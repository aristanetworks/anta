# Copyright (c) 2023-2025 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Tests for anta.input_models.routing.generic.py."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
from pydantic import ValidationError

from anta.tests.routing.generic import VerifyIPv4RouteType

if TYPE_CHECKING:
    from anta.input_models.routing.generic import IPv4Routes


class TestVerifyIPv4RouteTypeInput:
    """Test anta.tests.routing.bgp.VerifyIPv4RouteType.Input."""

    @pytest.mark.parametrize(
        ("routes_entries"),
        [
            pytest.param([{"prefix": "192.168.0.0/24", "vrf": "default", "route_type": "eBGP"}], id="valid"),
        ],
    )
    def test_valid(self, routes_entries: list[IPv4Routes]) -> None:
        """Test VerifyIPv4RouteType.Input valid inputs."""
        VerifyIPv4RouteType.Input(routes_entries=routes_entries)

    @pytest.mark.parametrize(
        ("routes_entries"),
        [
            pytest.param([{"prefix": "192.168.0.0/24", "vrf": "default"}], id="invalid"),
        ],
    )
    def test_invalid(self, routes_entries: list[IPv4Routes]) -> None:
        """Test VerifyIPv4RouteType.Input invalid inputs."""
        with pytest.raises(ValidationError):
            VerifyIPv4RouteType.Input(routes_entries=routes_entries)
