# Copyright (c) 2023-2026 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Tests for anta.input_models.routing.generic.py."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
from pydantic import ValidationError

from anta.input_models.routing.generic import VRFRoutingTableSize
from anta.tests.routing.generic import VerifyIPv4RouteNextHops, VerifyIPv4RouteType

if TYPE_CHECKING:
    from anta.input_models.routing.generic import IPv4RouteEntry


class TestVRFRoutingTableSize:
    """Tests for anta.input_models.routing.generic.VRFRoutingTableSize."""

    @pytest.mark.parametrize(
        ("vrf", "minimum", "maximum"),
        [
            pytest.param("default", 2, 20, id="valid"),
            pytest.param("PROD", 100, 500, id="valid-equal"),
        ],
    )
    def test_valid(self, vrf: str, minimum: int, maximum: int) -> None:
        """Test VRFRoutingTableSize valid inputs."""
        entry = VRFRoutingTableSize(vrf=vrf, minimum=minimum, maximum=maximum)
        assert str(entry) == f"VRF: {vrf}"

    @pytest.mark.parametrize(
        ("vrf", "minimum", "maximum"),
        [
            pytest.param("default", 20, 2, id="invalid-min-greater-than-max"),
        ],
    )
    def test_invalid(self, vrf: str, minimum: int, maximum: int) -> None:
        """Test VRFRoutingTableSize invalid inputs."""
        with pytest.raises(ValidationError):
            VRFRoutingTableSize(vrf=vrf, minimum=minimum, maximum=maximum)


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
