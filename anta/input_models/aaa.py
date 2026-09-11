# Copyright (c) 2026 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Input models for AAA tests."""

from __future__ import annotations

import re
from typing import TYPE_CHECKING, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from anta.custom_types import AAAAuthMethod

if TYPE_CHECKING:
    import sys

    if sys.version_info >= (3, 11):
        from typing import Self
    else:
        from typing_extensions import Self


PRIVILEGE_METHOD_LIST_PATTERN = re.compile(r"^privilege(?P<start>[0-9]|1[0-5])(?:-(?P<end>[0-9]|1[0-5]))?$")
MAX_PRIVILEGE_LEVEL = 15


def _validate_method_list_names(method_lists: list[AAAMethodList], expected_names: set[str] | None = None) -> None:
    """Validate that method-list names are unique and optionally belong to a fixed set."""
    names = [method_list.name for method_list in method_lists]
    if len(names) != len(set(names)):
        msg = "AAA method-list names must be unique"
        raise ValueError(msg)

    if expected_names is not None and (invalid_names := set(names).difference(expected_names)):
        msg = f"Invalid AAA method-list name(s): {', '.join(sorted(map(str, invalid_names)))}. Expected one of: {', '.join(sorted(expected_names))}"
        raise ValueError(msg)


def _normalize_privilege_method_list_name(name: str | int) -> str:
    """Normalize and validate an EOS privilege method-list name."""
    if isinstance(name, int):
        if 0 <= name <= MAX_PRIVILEGE_LEVEL:
            return f"privilege{name}"
        msg = f"Invalid AAA privilege level: {name}. Expected an integer between 0 and 15"
        raise ValueError(msg)

    if name == "all":
        return "privilege0-15"

    if (match := PRIVILEGE_METHOD_LIST_PATTERN.fullmatch(name)) is None:
        msg = (
            f"Invalid AAA privilege method-list name: {name}. Expected an integer between 0 and 15, 'all', "
            "'privilegeN', or 'privilegeN-M', where levels are between 0 and 15"
        )
        raise ValueError(msg)

    if (end := match.group("end")) is not None and int(match.group("start")) > int(end):
        msg = f"Invalid AAA privilege method-list range: {name}. The first privilege level must not exceed the last"
        raise ValueError(msg)
    return name


class AAAMethodList(BaseModel):
    """Expected AAA authentication or authorization method list."""

    model_config = ConfigDict(extra="forbid")
    name: str | int
    """Authentication method-list name."""
    methods: list[AAAAuthMethod]
    """Authentication methods in the expected order."""


class AAAAuthorization(BaseModel):
    """AAA authorization types and their expected method lists."""

    model_config = ConfigDict(extra="forbid")
    authz_type: Literal["commands", "exec"]
    """Authorization type using the expected method lists."""
    method_lists: list[AAAMethodList] = Field(min_length=1)
    """Expected authorization method lists."""

    @model_validator(mode="after")
    def validate_method_lists(self) -> Self:
        """Validate method-list names supported by the selected authorization type."""
        if self.authz_type == "commands":
            for method_list in self.method_lists:
                method_list.name = _normalize_privilege_method_list_name(method_list.name)
            _validate_method_list_names(self.method_lists)
        else:
            _validate_method_list_names(self.method_lists, {"exec"})
        return self
