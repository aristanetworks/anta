# Copyright (c) 2023-2026 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Module containing input models for generic routing tests."""

from __future__ import annotations

from ipaddress import IPv4Address, IPv4Network
from typing import TYPE_CHECKING, Any, ClassVar, Literal
from warnings import warn

from pydantic import BaseModel, ConfigDict, model_validator

from anta.custom_types import IPv4RouteType, PositiveInteger

if TYPE_CHECKING:
    import sys

    if sys.version_info >= (3, 11):
        from typing import Self
    else:
        from typing_extensions import Self


class RoutingTableSizeRouteSource(BaseModel):
    """Model for a route source entry used in the `VerifyRoutingTableSize` test.

    When used through `VerifyRoutingTableSize`, `minimum` and `maximum` are inherited from the test-level
    global values if not explicitly provided.
    """

    model_config = ConfigDict(extra="forbid")

    source: Literal["total_routes", "bgp", "ospf", "ospfv3", "isis", "static", "connected"] = "total_routes"
    """Route source to verify."""
    minimum: PositiveInteger
    """Expected minimum number of routes."""
    maximum: PositiveInteger
    """Expected maximum number of routes."""

    _DISPLAY_NAMES: ClassVar[dict[str, str]] = {
        "total_routes": "Total Routes",
        "connected": "Connected",
        "static": "Static",
        "bgp": "BGP",
        "ospf": "OSPF",
        "ospfv3": "OSPFv3",
        "isis": "ISIS",
    }

    @model_validator(mode="after")
    def check_min_max(self) -> Self:
        """Validate that minimum is not greater than maximum."""
        if self.minimum > self.maximum:
            msg = f"Minimum {self.minimum} is greater than maximum {self.maximum}"
            raise ValueError(msg)
        return self

    def __str__(self) -> str:
        """Return a human-readable string representation of the RoutingTableSizeRouteSource for reporting."""
        return f"Route Source: {self._DISPLAY_NAMES[self.source]}"


class RoutingTableSizeVRF(BaseModel):
    """Model for a VRF entry used in the `VerifyRoutingTableSize` test.

    When used through `VerifyRoutingTableSize`, `route_sources` defaults to a single `total_routes` check
    if not explicitly provided.
    """

    model_config = ConfigDict(extra="forbid")

    vrf: str = "default"
    """VRF name."""
    route_sources: list[RoutingTableSizeRouteSource]
    """List of route sources to verify."""

    @model_validator(mode="after")
    def validate_unique_route_sources(self) -> Self:
        """Validate that no duplicate route sources are defined within the same VRF."""
        seen = set()
        duplicates = set()

        for rs in self.route_sources:
            source = rs.source
            if source in seen:
                duplicates.add(source)
            else:
                seen.add(source)

        if duplicates:
            msg = f"Duplicate route sources found in VRF '{self.vrf}': {', '.join(sorted(duplicates))}"
            raise ValueError(msg)

        return self

    def __str__(self) -> str:
        """Return a human-readable string representation of the RoutingTableSizeVRF for reporting."""
        return f"VRF: {self.vrf}"


class IPv4RouteEntry(BaseModel):
    """Model for an IPv4 route entry."""

    model_config = ConfigDict(extra="forbid")
    prefix: IPv4Network
    """IPv4 prefix in CIDR notation."""
    vrf: str = "default"
    """VRF context."""
    description: str | None = None
    """Optional metadata describing the IPv4 route entry. Used for reporting."""
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
