# Copyright (c) 2023-2025 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Module containing input models for EVPN tests."""

from __future__ import annotations

from ipaddress import IPv4Interface, IPv6Interface
from typing import Literal

from pydantic import BaseModel, ConfigDict

from anta.custom_types import Vni


class EVPNType5Prefix(BaseModel):
    """Model for an EVPN Type-5 prefix."""

    model_config = ConfigDict(extra="forbid")
    address: IPv4Interface | IPv6Interface
    """IPv4 or IPv6 prefix address to verify."""
    vni: Vni
    """VNI associated with the prefix."""
    routes: list[EVPNRoute] | None = None
    """Specific EVPN routes to verify for this prefix."""

    def __str__(self) -> str:
        """Return a human-readable string representation of the EVPNType5Prefix for reporting."""
        return f"Prefix: {self.address} VNI: {self.vni}"


class EVPNRoute(BaseModel):
    """Model for an EVPN Type-5 route for a prefix."""

    model_config = ConfigDict(extra="forbid")
    rd: str
    """Expected route distinguisher `<admin>:<local assignment>` of the route."""
    domain: Literal["local", "remote"] = "local"
    """EVPN domain. Can be remote on gateway nodes in a multi-domain EVPN VXLAN fabric."""
    paths: list[EVPNPath] | None = None
    """Specific paths to verify for this route."""

    def __str__(self) -> str:
        """Return a human-readable string representation of the EVPNRoute for reporting."""
        value = f"RD: {self.rd}"
        if self.domain == "remote":
            value += " Domain: remote"
        return value


class EVPNPath(BaseModel):
    """Model for an EVPN Type-5 path for a route."""

    model_config = ConfigDict(extra="forbid")
    nexthop: str
    """Expected next-hop IPv4 or IPv6 address. Can be an empty string for local paths."""
    route_targets: list[str] | None = None
    """List of expected RTs following the `ASN(asplain):nn` or `ASN(asdot):nn` or `IP-address:nn` format."""

    def __str__(self) -> str:
        """Return a human-readable string representation of the EVPNPath for reporting."""
        value = f"Nexthop: {self.nexthop}"
        if self.route_targets:
            value += f" RTs: {', '.join(self.route_targets)}"
        return value
