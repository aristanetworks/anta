# Copyright (c) 2023-2025 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Module containing input models for VLAN tests."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict

from anta.custom_types import VlanId


class Vlan(BaseModel):
    """Model for a VLAN."""

    model_config = ConfigDict(extra="forbid")
    vlan_id: VlanId
    """The VLAN ID."""
    status: Literal["active", "suspended", "inactive"]
    """The VLAN administrative status."""

    def __str__(self) -> str:
        """Representation of the VLAN model."""
        return f"VLAN: Vlan{self.vlan_id}"
