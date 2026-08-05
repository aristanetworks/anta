# Copyright (c) 2023-2026 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Tests for anta.input_models.routing.generic.py."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
from pydantic import ValidationError

from anta.input_models.routing.generic import RoutingTableSizeRouteSource, RoutingTableSizeVRF
from anta.tests.routing.generic import VerifyIPv4RouteNextHops, VerifyIPv4RouteType

if TYPE_CHECKING:
    from anta.input_models.routing.generic import IPv4RouteEntry


class TestRoutingTableSizeRouteSource:
    """Tests for anta.input_models.routing.generic.RoutingTableSizeRouteSource."""

    def test_default_source_is_total(self) -> None:
        """`source` defaults to `total`."""
        rs = RoutingTableSizeRouteSource(minimum=1, maximum=10)
        assert rs.source == "total_routes"

    def test_valid_bounds(self) -> None:
        """Both bounds provided is valid."""
        rs = RoutingTableSizeRouteSource(source="bgp", minimum=10, maximum=100)
        assert rs.minimum == 10
        assert rs.maximum == 100

    def test_invalid_min_greater_than_max(self) -> None:
        """`minimum > maximum` is rejected."""
        with pytest.raises(ValidationError):
            RoutingTableSizeRouteSource(source="bgp", minimum=100, maximum=10)

    def test_invalid_unknown_source(self) -> None:
        """Unknown `source` literals are rejected."""
        with pytest.raises(ValidationError):
            RoutingTableSizeRouteSource(source="unknown", minimum=1, maximum=10)  # pyright: ignore[reportArgumentType]


class TestRoutingTableSizeVRF:
    """Tests for anta.input_models.routing.generic.RoutingTableSizeVRF."""

    def test_valid_defaults(self) -> None:
        """A VRF entry with defaults has vrf='default'."""
        v = RoutingTableSizeVRF(route_sources=[RoutingTableSizeRouteSource(source="total_routes", minimum=1, maximum=10)])
        assert str(v) == "VRF: default"
        assert len(v.route_sources) == 1
        assert v.route_sources[0].source == "total_routes"

    def test_valid_with_route_sources(self) -> None:
        """A VRF entry with explicit route sources is valid."""
        RoutingTableSizeVRF(vrf="PROD", route_sources=[RoutingTableSizeRouteSource(source="bgp", minimum=1, maximum=10)])

    def test_invalid_duplicate_route_sources(self) -> None:
        """Duplicate route sources within the same VRF are rejected."""
        with pytest.raises(ValidationError):
            RoutingTableSizeVRF(
                vrf="PROD",
                route_sources=[
                    RoutingTableSizeRouteSource(source="bgp", minimum=1, maximum=10),
                    RoutingTableSizeRouteSource(source="bgp", minimum=1, maximum=10),
                ],
            )


class TestVerifyRouteEntryInput:
    """Test anta.tests.routing.generic.VerifyIPv4RouteNextHops.Input."""

    @pytest.mark.parametrize(
        ("route_entries"),
        [
            pytest.param([{"prefix": "10.10.0.1/32", "vrf": "default", "strict": True, "nexthops": ["10.100.0.8", "10.100.0.10"]}], id="valid"),
        ],
    )
    def test_valid(self, route_entries: list[IPv4RouteEntry]) -> None:
        """Test VerifyIPv4RouteNextHops.Input valid inputs."""
        VerifyIPv4RouteNextHops.Input(route_entries=route_entries)

    @pytest.mark.parametrize(
        ("route_entries"),
        [
            pytest.param([{"prefix": "10.10.0.1/32", "vrf": "default"}], id="invalid"),
        ],
    )
    def test_invalid(self, route_entries: list[IPv4RouteEntry]) -> None:
        """Test VerifyIPv4RouteNextHops.Input invalid inputs."""
        with pytest.raises(ValidationError):
            VerifyIPv4RouteNextHops.Input(route_entries=route_entries)


class TestVerifyIPv4RouteTypeInput:
    """Test anta.tests.routing.bgp.VerifyIPv4RouteType.Input."""

    @pytest.mark.parametrize(
        ("routes_entries"),
        [
            pytest.param([{"prefix": "192.168.0.0/24", "vrf": "default", "route_type": "eBGP"}], id="valid"),
        ],
    )
    def test_valid(self, routes_entries: list[IPv4RouteEntry]) -> None:
        """Test VerifyIPv4RouteType.Input valid inputs."""
        VerifyIPv4RouteType.Input(routes_entries=routes_entries)

    @pytest.mark.parametrize(
        ("routes_entries"),
        [
            pytest.param([{"prefix": "192.168.0.0/24", "vrf": "default"}], id="invalid"),
        ],
    )
    def test_invalid(self, routes_entries: list[IPv4RouteEntry]) -> None:
        """Test VerifyIPv4RouteType.Input invalid inputs."""
        with pytest.raises(ValidationError):
            VerifyIPv4RouteType.Input(routes_entries=routes_entries)
