# Copyright (c) 2023-2025 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Module containing input models for routing ISIS tests."""

from __future__ import annotations

from ipaddress import IPv4Address, IPv4Network
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


class SRTunnelEntry(BaseModel):
    """Model for a IS-IS SR tunnel."""

    model_config = ConfigDict(extra="forbid")
    endpoint: IPv4Network
    """Endpoint of the tunnel."""
    vias: list[TunnelPath] | None = None
    """Optional list of path to reach endpoint."""

    def __str__(self) -> str:
        """Return a human-readable string representation of the SRTunnelEntry for reporting."""
        return f"Endpoint: {self.endpoint}"


class TunnelPath(BaseModel):
    """Model for a IS-IS tunnel path."""

    model_config = ConfigDict(extra="forbid")
    nexthop: IPv4Address | None = None
    """Nexthop of the tunnel."""
    type: Literal["ip", "tunnel"] | None = None
    """Type of the tunnel."""
    interface: Interface | None = None
    """Interface of the tunnel."""
    tunnel_id: Literal["TI-LFA", "ti-lfa", "unset"] | None = None
    """Computation method of the tunnel."""

    def __str__(self) -> str:
        """Return a human-readable string representation of the TunnelPath for reporting."""
        base_string = ""
        if self.nexthop:
            base_string += f" Next-hop: {self.nexthop}"
        if self.type:
            base_string += f" Type: {self.type}"
        if self.interface:
            base_string += f" Interface: {self.interface}"
        if self.tunnel_id:
            base_string += f" TunnelID: {self.tunnel_id}"

        return base_string.lstrip()
