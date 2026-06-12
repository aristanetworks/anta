# Copyright (c) 2023-2026 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Module containing input models for generic routing tests."""

from __future__ import annotations

from ipaddress import IPv4Address, IPv4Network
from typing import TYPE_CHECKING, Any, Literal
from warnings import warn

from pydantic import BaseModel, ConfigDict, Field, model_validator

from anta.custom_types import IPv4RouteType, PositiveInteger

RoutingTableMetric = Literal["total", "bgp", "ospf", "ospfv3", "isis", "static", "connected"]

if TYPE_CHECKING:
    import sys

    if sys.version_info >= (3, 11):
        from typing import Self
    else:
        from typing_extensions import Self


class RoutingTableSizeRouteSource(BaseModel):
    """Model for a single per-source routing table size check used in `VerifyRoutingTableSize`."""

    model_config = ConfigDict(extra="forbid")

    source: RoutingTableMetric = "total"
    """Route source to check. One of `total`, `bgp`, `ospf`, `ospfv3`, `isis`, `static`, `connected`. Defaults to `total`."""
    minimum: PositiveInteger | None = None
    """Optional minimum value for this check. If unset, falls back to the test's global `minimum`."""
    maximum: PositiveInteger | None = None
    """Optional maximum value for this check. If unset, falls back to the test's global `maximum`."""

    @model_validator(mode="after")
    def check_min_max(self) -> Self:
        """Validate that minimum is not greater than maximum when both are set."""
        if self.minimum is not None and self.maximum is not None and self.minimum > self.maximum:
            msg = f"Minimum {self.minimum} is greater than maximum {self.maximum}"
            raise ValueError(msg)
        return self


class RoutingTableSizeVRF(BaseModel):
    """Model for a per-VRF entry used in `VerifyRoutingTableSize`."""

    model_config = ConfigDict(extra="forbid")

    vrf: str = "default"
    """VRF name. Defaults to `default`."""
    route_sources: list[RoutingTableSizeRouteSource] = Field(default_factory=lambda: [RoutingTableSizeRouteSource(source="total")])
    """List of per-source checks. Defaults to a single `total` check."""

    @model_validator(mode="after")
    def validate_unique_route_sources(self) -> Self:
        """Validate that no duplicate route sources are defined within the same VRF."""
        sources = [rs.source for rs in self.route_sources]
        if len(sources) != len(set(sources)):
            msg = f"Duplicate route sources found in VRF '{self.vrf}': {', '.join(s for s in sources if sources.count(s) > 1)}"
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
