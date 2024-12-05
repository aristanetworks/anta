# Copyright (c) 2023-2024 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Module containing input models for routing ISIS tests."""

from __future__ import annotations

from ipaddress import IPv4Address, IPv6Address
from typing import TYPE_CHECKING, Any, Literal
from warnings import warn

from pydantic import BaseModel, ConfigDict, PositiveInt, model_validator

from anta.custom_types import Interface


class ISISInstance(BaseModel):
    """"""
    model_config = ConfigDict(extra="forbid")
    name: str
    """ISIS instance name."""
    vrf: str = "default"
    """VRF name where ISIS instance is configured."""
    dataplane: Literal["MPLS", "mpls", "unset"] = "MPLS"
    """Configured dataplane for the instance."""
    interfaces: list[ISISInterface] | None = None
    """"""

    def __str__(self) -> str:
        """Return a human-readable string representation of the ISISInstance for reporting."""
        return f"Instance: {self.name} VRF: {self.vrf}"


class ISISInterface(BaseModel):
    """Model for a ISIS Interface."""

    model_config = ConfigDict(extra="forbid")
    name: Interface
    """Interface name to check."""
    # Should have support for is-type level-1-2 ================================================== Added 0 for this, Need to verify that can be neigbor and passive true/false is same or not
    level: Literal[1, 2, 0] = 2
    """ISIS level (1 or 2) configured for the interface. Default is 2."""
    neighbor_count: int
    """The total number of IS-IS neighbors associated with interface."""
    mode: Literal["point-to-point", "broadcast", "passive"] | None = None
    """The operational mode of the IS-IS interface."""
    segment: Segment | None = None
    """"""

    def __str__(self) -> str:
        """Return a human-readable string representation of the ISISInterface for reporting."""
        return f"Interface: {self.name} Level: {self.level if self.level else 'IS Type(1-2)'}"


class Segment(BaseModel):
    """Segment model definition for ISIS"""

    model_config = ConfigDict(extra="forbid")
    sid_origin: Literal["dynamic"] = "dynamic"
    "Specifies the origin of the Segment ID."
    address: IPv4Address
    """IP address of the remote end of the segment(segment endpoint)."""

    def __str__(self) -> str:
        """Return a human-readable string representation of the Segment for reporting."""
        return f"Interface: {self.interface} Level: {self.level} Origin: {self.sid_origin} Endpoint: {self.address}"

class InterfaceCount(ISISInterface):
    pass

