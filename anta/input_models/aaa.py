# Copyright (c) 2026 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Input models for AAA tests."""

from __future__ import annotations

import re
from typing import TYPE_CHECKING

from pydantic import BaseModel, ConfigDict, Field, model_validator

from anta.custom_types import AAAAccountingType, AAAAuthMethod

if TYPE_CHECKING:
    import sys

    if sys.version_info >= (3, 11):
        from typing import Self
    else:
        from typing_extensions import Self

PRIVILEGE_LEVEL_RANGE_PATTERN = re.compile(r"^(?P<start>\d|1[0-5])(?:-(?P<end>\d|1[0-5]))?$")
MAX_PRIVILEGE_LEVEL = 15


def _normalize_privilege_method_list_name(name: str) -> str:
    """Return the canonical EOS JSON key for a commands accounting method-list name."""
    if name == "all":
        return "privilege0-15"

    match = PRIVILEGE_LEVEL_RANGE_PATTERN.fullmatch(name)
    if not match:
        msg = f"Invalid privilege method-list name: {name!r}. Expected 'all', 'N', or 'N-M' where N is 0-15"
        raise ValueError(msg)

    # Reject ranges where the start level exceeds the end level
    start, end = int(match.group("start")), match.group("end")
    if end is not None and start > int(end):
        msg = f"Invalid privilege range {name!r}: start level must not exceed end level"
        raise ValueError(msg)

    return f"privilege{name}"


class AAAAccountingMethods(BaseModel):
    """Expected AAA accounting method lists for a single EOS accounting section."""

    model_config = ConfigDict(extra="forbid")
    name: str | int
    """Accounting method-list name."""
    default_methods: list[AAAAuthMethod] | None = Field(default=None, min_length=1)
    """Expected default accounting methods."""
    console_methods: list[AAAAuthMethod] | None = Field(default=None, min_length=1)
    """Expected console accounting methods."""

    @model_validator(mode="after")
    def validate_methods(self) -> Self:
        """Require at least one accounting context to be provided."""
        if self.default_methods is None and self.console_methods is None:
            msg = "At least one of 'default_methods' or 'console_methods' must be provided"
            raise ValueError(msg)
        return self


class AAAAccounting(BaseModel):
    """AAA accounting types and their expected default or console method lists."""

    model_config = ConfigDict(extra="forbid")
    acct_type: AAAAccountingType
    """Accounting type using the expected method lists."""
    method_configs: list[AAAAccountingMethods] = Field(min_length=1)
    """Expected accounting method list configurations."""

    @model_validator(mode="after")
    def validate_method_lists(self) -> Self:
        """Validate method-list names and contexts supported by the selected accounting type."""
        if self.acct_type == "commands":
            # Normalize each privilege method-list name to its canonical EOS form
            for entry in self.method_configs:
                entry.name = _normalize_privilege_method_list_name(str(entry.name))

        # Ensure all names are unique (applies to all accounting types)
        method_names = [str(entry.name) for entry in self.method_configs]
        if len(method_names) != len(set(method_names)):
            msg = "AAA accounting method-list names must be unique"
            raise ValueError(msg)

        if self.acct_type == "commands":
            return self

        # For exec, system, and dot1x, EOS only allows one fixed method-list name matching the type
        expected_name = self.acct_type
        if invalid_names := set(method_names).difference({expected_name}):
            msg = f"Invalid AAA accounting method-list name(s): {', '.join(sorted(invalid_names))}. Expected: {expected_name}"
            raise ValueError(msg)

        # Console accounting is not supported for system and dot1x types
        if self.acct_type in {"system", "dot1x"} and any(entry.console_methods is not None for entry in self.method_configs):
            msg = f"Console accounting methods are not supported for accounting type '{self.acct_type}'"
            raise ValueError(msg)
        return self
