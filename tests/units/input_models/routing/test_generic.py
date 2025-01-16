# Copyright (c) 2023-2025 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Tests for anta.input_models.routing.generic.py."""

# pylint: disable=C0302
from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
from pydantic import ValidationError

from anta.tests.routing.generic import VerifyRouteEntry

if TYPE_CHECKING:
    from anta.input_models.routing.generic import IPv4Routes


class TestVerifyRouteEntryInput:
    """Test anta.tests.routing.generic.VerifyRouteEntry.Input."""

    @pytest.mark.parametrize(
        ("route_entries"),
        [
            pytest.param([{"prefix": "10.10.0.1/32", "vrf": "default", "nexthops": ["10.100.0.8", "10.100.0.10"]}], id="valid"),
        ],
    )
    def test_valid(self, route_entries: list[IPv4Routes]) -> None:
        """Test VerifyRouteEntry.Input valid inputs."""
        VerifyRouteEntry.Input(route_entries=route_entries)

    @pytest.mark.parametrize(
        ("route_entries"),
        [
            pytest.param([{"prefix": "10.10.0.1/32", "vrf": "default"}], id="invalid"),
        ],
    )
    def test_invalid(self, route_entries: list[IPv4Routes]) -> None:
        """Test VerifyRouteEntry.Input invalid inputs."""
        with pytest.raises(ValidationError):
            VerifyRouteEntry.Input(route_entries=route_entries)
