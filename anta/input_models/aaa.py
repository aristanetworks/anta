# Copyright (c) 2023-2026 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Input models for AAA tests."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from anta.custom_types import AAAAuthMethod


class AAAMethodList(BaseModel):
    """Expected AAA authentication method list."""

    model_config = ConfigDict(extra="forbid")
    name: str
    """Authentication method-list name."""
    methods: list[AAAAuthMethod]
    """Authentication methods in the expected order."""


class AAAAuthentication(BaseModel):
    """AAA authentication types and their expected method lists."""

    model_config = ConfigDict(extra="forbid")
    auth_type: Literal["login", "enable", "dot1x"]
    """Authentication type using the expected method lists."""
    method_lists: list[AAAMethodList] = Field(min_length=1)
    """Expected authentication method lists."""
