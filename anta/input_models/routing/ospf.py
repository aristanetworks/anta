# Copyright (c) 2025 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Module containing input models for routing OSPF tests."""

from __future__ import annotations

from ipaddress import IPv4Address
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from anta.custom_types import Interface


class OSPFNeighbor(BaseModel):
    """Model for an OSPF neighbor."""

    model_config = ConfigDict(extra="forbid")
    instance: int = Field(ge=1, le=65535)
    """OSPF instance."""
    vrf: str = "default"
    """VRF context of the OSPF instance."""
    ip_address: IPv4Address
    """Neighbor interface IP address."""
    local_interface: Interface
    """Local interface establishing the adjacency."""
    state: Literal["full", "2Ways"] = "full"
    """Expected adjacency state."""
    area_id: IPv4Address | Annotated[int, Field(ge=0, le=4294967295)]
    """OSPF area-id in decimal or IP address format."""

    @field_validator("area_id", mode="after")
    @classmethod
    def convert_area_id(cls, area_id: IPv4Address | int) -> IPv4Address:
        """Convert a decimal OSPF area-id to an IP address format if needed."""
        return IPv4Address(area_id) if isinstance(area_id, int) else area_id

    def __str__(self) -> str:
        """Return a human-readable string representation of the OSPFNeighbor for reporting."""
        return f"Instance: {self.instance} VRF: {self.vrf} Neighbor IP: {self.ip_address} Area: {self.area_id}"
