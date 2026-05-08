# Copyright (c) 2023-2026 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Tests for anta.input_models.routing.generic.py."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
from pydantic import ValidationError

from anta.input_models.routing.generic import RoutingTableSizeCheck, RoutingTableSizeVRFFilter
from anta.tests.routing.generic import VerifyIPv4RouteNextHops, VerifyIPv4RouteType

if TYPE_CHECKING:
    from anta.input_models.routing.generic import IPv4RouteEntry


class TestRoutingTableSizeCheck:
    """Tests for anta.input_models.routing.generic.RoutingTableSizeCheck."""

    def test_default_metric_is_total(self) -> None:
        """`metric` defaults to `total` and bounds are optional."""
        check = RoutingTableSizeCheck()
        assert check.metric == "total"
        assert check.minimum is None
        assert check.maximum is None

    def test_valid_partial_bounds(self) -> None:
        """Either bound may be omitted independently."""
        RoutingTableSizeCheck(metric="bgp", minimum=10)
        RoutingTableSizeCheck(metric="bgp", maximum=100)

    def test_invalid_min_greater_than_max(self) -> None:
        """`minimum > maximum` is rejected when both are set."""
        with pytest.raises(ValidationError):
            RoutingTableSizeCheck(metric="bgp", minimum=100, maximum=10)

    def test_invalid_unknown_metric(self) -> None:
        """Unknown `metric` literals are rejected."""
        with pytest.raises(ValidationError):
            RoutingTableSizeCheck(metric="unknown")  # pyright: ignore[reportArgumentType]


class TestRoutingTableSizeVRFFilter:
    """Tests for anta.input_models.routing.generic.RoutingTableSizeVRFFilter."""

    def test_valid_no_checks(self) -> None:
        """A VRF filter without `checks` is valid."""
        f = RoutingTableSizeVRFFilter(vrf="PROD")
        assert str(f) == "VRF: PROD"

    def test_valid_with_checks(self) -> None:
        """A VRF filter with `checks` is valid."""
        RoutingTableSizeVRFFilter(vrf="PROD", checks=[RoutingTableSizeCheck(metric="bgp", minimum=1, maximum=10)])


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
