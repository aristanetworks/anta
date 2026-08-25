# Copyright (c) 2023-2026 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Input models for AAA tests."""

from __future__ import annotations

from typing import TYPE_CHECKING, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from anta.custom_types import AAAAuthMethod

if TYPE_CHECKING:
    import sys

    if sys.version_info >= (3, 11):
        from typing import Self
    else:
        from typing_extensions import Self


def _validate_method_list_names(method_lists: list[AAAMethodList], expected_names: set[str]) -> None:
    """Validate that method-list names are unique and optionally belong to a fixed set."""
    names = [method_list.name for method_list in method_lists]
    if len(names) != len(set(names)):
        msg = "AAA method-list names must be unique"
        raise ValueError(msg)

    if invalid_names := set(names).difference(expected_names):
        msg = f"Invalid AAA method-list name(s): {', '.join(sorted(map(str, invalid_names)))}. Expected one of: {', '.join(sorted(expected_names))}"
        raise ValueError(msg)


class AAAMethodList(BaseModel):
    """Expected AAA authentication method list."""

    model_config = ConfigDict(extra="forbid")
    name: str | int
    """Method-list name."""
    methods: list[AAAAuthMethod]
    """Methods in the expected order."""


class AAAAuthentication(BaseModel):
    """AAA authentication types and their expected method lists."""

    model_config = ConfigDict(extra="forbid")
    auth_type: Literal["login", "enable", "dot1x"]
    """Authentication type using the expected method lists."""
    method_lists: list[AAAMethodList] = Field(min_length=1)
    """Expected authentication method lists."""

    @model_validator(mode="after")
    def validate_method_lists(self) -> Self:
        """Validate method-list names supported by the selected authentication type."""
        expected_names = {
            "login": {"default", "console", "login", "command-api"},
            "enable": {"default", "console"},
            "dot1x": {"default"},
        }[self.auth_type]
        _validate_method_list_names(self.method_lists, expected_names)
        return self
