# Copyright (c) 2023-2026 Arista Networks, Inc.
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

PRIVILEGE_METHOD_LIST_PATTERN = re.compile(r"^privilege(?P<start>[0-9]|1[0-5])(?:-(?P<end>[0-9]|1[0-5]))?$")
MAX_PRIVILEGE_LEVEL = 15


def _normalize_privilege_method_list_name(name: str | int) -> str:
    """Normalize and validate an EOS privilege method-list name."""
    # Handle integer input: convert to "privilegeN" EOS format
    if isinstance(name, int):
        if 0 <= name <= MAX_PRIVILEGE_LEVEL:
            return f"privilege{name}"
        msg = f"Invalid AAA privilege level: {name}. Expected an integer between 0 and 15"
        raise ValueError(msg)

    # Expand the "all" shorthand to the full EOS privilege range
    if name == "all":
        return "privilege0-15"

    # Validate the string matches the expected "privilegeN" or "privilegeN-M" pattern
    if (match := PRIVILEGE_METHOD_LIST_PATTERN.fullmatch(name)) is None:
        msg = (
            f"Invalid AAA privilege method-list name: {name}. Expected an integer between 0 and 15, 'all', "
            "'privilegeN', or 'privilegeN-M', where levels are between 0 and 15"
        )
        raise ValueError(msg)

    # Reject ranges where the start level exceeds the end level
    if (end := match.group("end")) is not None and int(match.group("start")) > int(end):
        msg = f"Invalid AAA privilege method-list range: {name}. The first privilege level must not exceed the last"
        raise ValueError(msg)
    return name


class AAAAccountingMethods(BaseModel):
    """Expected AAA accounting method lists for a single EOS accounting section."""

    model_config = ConfigDict(extra="forbid")
    name: str | int
    """Accounting method-list name."""
    default_methods: list[AAAAuthMethod] | None = None
    """Expected default accounting methods in order."""
    console_methods: list[AAAAuthMethod] | None = None
    """Expected console accounting methods in order."""

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
                entry.name = _normalize_privilege_method_list_name(entry.name)

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
