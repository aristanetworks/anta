# Copyright (c) 2023-2025 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Module containing input models for generic routing tests."""

from __future__ import annotations

from ipaddress import IPv4Network

from pydantic import BaseModel, ConfigDict

from anta.custom_types import IPv4RouteType


class IPv4Routes(BaseModel):
    """Model for a list of IPV4 route entries."""

    model_config = ConfigDict(extra="forbid")
    prefix: IPv4Network
    """The IPV4 network to validate the route type."""
    vrf: str = "default"
    """VRF context. Defaults to `default` VRF."""
    route_type: IPv4RouteType
    """List of IPV4 Route type to validate the valid rout type."""

    def __str__(self) -> str:
        """Return a human-readable string representation of the IPv4RouteType for reporting."""
        return f"Prefix: {self.prefix} VRF: {self.vrf}"
