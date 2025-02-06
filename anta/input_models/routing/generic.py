# Copyright (c) 2023-2025 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Module containing input models for generic routing tests."""

from __future__ import annotations

from ipaddress import IPv4Address, IPv4Network

from pydantic import BaseModel, ConfigDict

from anta.custom_types import IPv4RouteType


class IPv4Routes(BaseModel):
    """Model for a list of IPV4 route entries."""

    model_config = ConfigDict(extra="forbid")
    prefix: IPv4Network
    """IPv4 prefix in CIDR notation."""
    vrf: str = "default"
    """VRF context. Defaults to `default` VRF."""
    route_type: IPv4RouteType | None = None
    """Expected route type. Required field in the `VerifyIPv4RouteType` test."""
    nexthops: list[IPv4Address] | None = None
    """A list of the next-hop IP addresses for the route. Required field in the `VerifyIPv4RouteNextHops` test."""
    strict: bool = False
    """If True, requires exact matching of provided nexthop(s).

    Can be enabled in `VerifyIPv4RouteNextHops` test."""

    def __str__(self) -> str:
        """Return a human-readable string representation of the IPv4Routes for reporting."""
        return f"Prefix: {self.prefix} VRF: {self.vrf}"
