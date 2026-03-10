# Copyright (c) 2023-2026 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Module containing input models for generic routing tests."""

from __future__ import annotations

from ipaddress import IPv4Address, IPv4Network
from typing import Any
from warnings import warn

from pydantic import BaseModel, ConfigDict

from anta.custom_types import IPv4RouteType


class IPv4RouteEntry(BaseModel):
    """Model for a list of IPV4 prefixes."""

    model_config = ConfigDict(extra="forbid")
    prefix: IPv4Network
    """IPv4 prefix in CIDR notation."""
    vrf: str = "default"
    """VRF context."""
    description: str | None = None
    """Optional metadata describing the BGP peer or RFC5549 interface. Used for reporting."""
    route_type: IPv4RouteType | None = None
    """Expected route type. Required field in the `VerifyIPv4RouteType` test."""
    nexthops: list[IPv4Address] | None = None
    """A list of the next-hop IP addresses for the route. Required field in the `VerifyIPv4RouteNextHops` test."""
    strict: bool = False
    """If True, requires exact matching of provided nexthop(s).

    Can be enabled in `VerifyIPv4RouteNextHops` test."""

    def __str__(self) -> str:
        """Return a human-readable string representation of the IPv4Routes for reporting."""
        identifier = f"Prefix: {self.prefix}"
        description = f" ({self.description})" if self.description else ""
        return f"{identifier}{description} VRF: {self.vrf}"


class IPv4Routes(IPv4RouteEntry):  # pragma: no cover
    """Alias for the IPv4RouteEntry model to maintain backward compatibility.

    When initialized, it will emit a deprecation warning and call the IPv4RouteEntry model.

    TODO: Remove this class in ANTA v2.0.0.
    """

    def __init__(self, **data: Any) -> None:  # noqa: ANN401
        """Initialize the IPv4Routes class, emitting a deprecation warning."""
        warn(
            message="IPv4Routes model is deprecated and will be removed in ANTA v2.0.0. Use the IPv4RouteEntry model instead.",
            category=DeprecationWarning,
            stacklevel=2,
        )
        super().__init__(**data)
