# Copyright (c) 2023-2025 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Module containing input models for routing ISIS tests."""

from __future__ import annotations

from ipaddress import IPv4Address
from typing import Literal

from pydantic import BaseModel, ConfigDict

from anta.custom_types import Interface


class ISISInstance(BaseModel):
    """Model for an IS-IS instance."""

    model_config = ConfigDict(extra="forbid")
    name: str
    """The name of the IS-IS instance."""
    vrf: str = "default"
    """VRF context where the IS-IS instance is configured. Defaults to `default`."""
    dataplane: Literal["MPLS", "mpls", "unset"] = "MPLS"
    """Configured dataplane for the IS-IS instance. Required field in the `VerifyISISSegmentRoutingDataplane` test."""
    segments: list[Segment] | None = None
    """A list of IS-IS segments associated with the instance. Required field in the `VerifyISISSegmentRoutingAdjacencySegments` test."""

    def __str__(self) -> str:
        """Return a human-readable string representation of the ISISInstance for reporting."""
        return f"Instance: {self.name} VRF: {self.vrf}"


class Segment(BaseModel):
    """Segment model definition."""

    model_config = ConfigDict(extra="forbid")
    interface: Interface
    """Interface name to check."""
    level: Literal[1, 2] = 2
    """IS-IS level configured for interface. Default is 2."""
    sid_origin: Literal["dynamic"] = "dynamic"
    "Specifies the origin of the Segment ID."
    address: IPv4Address
    """IP address of the remote end of the segment(segment endpoint)."""

    def __str__(self) -> str:
        """Return a human-readable string representation of the Segment for reporting."""
        return f"Interface: {self.interface} IP Addr: {self.address}"


class ISISInterface(BaseModel):
    """Model for a IS-IS Interface."""

    model_config = ConfigDict(extra="forbid")
    name: Interface
    """Interface name to check."""
    vrf: str = "default"
    """VRF name where IS-IS instance is configured."""
    level: Literal[1, 2] = 2
    """IS-IS level (1 or 2) configured for the interface. Default is 2."""
    count: int | None = None
    """The total number of IS-IS neighbors associated with interface."""
    mode: Literal["point-to-point", "broadcast", "passive"] | None = None
    """The configured IS-IS circuit type for this interface."""

    def __str__(self) -> str:
        """Return a human-readable string representation of the ISISInterface for reporting."""
        return f"Interface: {self.name} VRF: {self.vrf} Level: {self.level}"
