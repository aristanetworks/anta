# Copyright (c) 2023-2025 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Tests for anta.input_models.routing.isis.py."""

from __future__ import annotations

from typing import TYPE_CHECKING, Literal

import pytest
from pydantic import ValidationError

from anta.input_models.routing.isis import ISISInstance, TunnelPath
from anta.tests.routing.isis import VerifyISISSegmentRoutingAdjacencySegments, VerifyISISSegmentRoutingDataplane

if TYPE_CHECKING:
    from ipaddress import IPv4Address

    from anta.custom_types import Interface


class TestVerifyISISSegmentRoutingAdjacencySegmentsInput:
    """Test anta.tests.routing.isis.VerifyISISSegmentRoutingAdjacencySegments.Input."""

    @pytest.mark.parametrize(
        ("instances"),
        [
            pytest.param(
                [{"name": "CORE-ISIS", "vrf": "default", "segments": [{"interface": "Ethernet2", "address": "10.0.1.3", "sid_origin": "dynamic"}]}], id="valid_vrf"
            ),
        ],
    )
    def test_valid(self, instances: list[ISISInstance]) -> None:
        """Test VerifyISISSegmentRoutingAdjacencySegments.Input valid inputs."""
        VerifyISISSegmentRoutingAdjacencySegments.Input(instances=instances)

    @pytest.mark.parametrize(
        ("instances"),
        [
            pytest.param(
                [{"name": "CORE-ISIS", "vrf": "PROD", "segments": [{"interface": "Ethernet2", "address": "10.0.1.3", "sid_origin": "dynamic"}]}], id="invalid_vrf"
            ),
        ],
    )
    def test_invalid(self, instances: list[ISISInstance]) -> None:
        """Test VerifyISISSegmentRoutingAdjacencySegments.Input invalid inputs."""
        with pytest.raises(ValidationError):
            VerifyISISSegmentRoutingAdjacencySegments.Input(instances=instances)


class TestVerifyISISSegmentRoutingDataplaneInput:
    """Test anta.tests.routing.isis.VerifyISISSegmentRoutingDataplane.Input."""

    @pytest.mark.parametrize(
        ("instances"),
        [
            pytest.param([{"name": "CORE-ISIS", "vrf": "default", "dataplane": "MPLS"}], id="valid_vrf"),
        ],
    )
    def test_valid(self, instances: list[ISISInstance]) -> None:
        """Test VerifyISISSegmentRoutingDataplane.Input valid inputs."""
        VerifyISISSegmentRoutingDataplane.Input(instances=instances)

    @pytest.mark.parametrize(
        ("instances"),
        [
            pytest.param([{"name": "CORE-ISIS", "vrf": "PROD", "dataplane": "MPLS"}], id="invalid_vrf"),
        ],
    )
    def test_invalid(self, instances: list[ISISInstance]) -> None:
        """Test VerifyISISSegmentRoutingDataplane.Input invalid inputs."""
        with pytest.raises(ValidationError):
            VerifyISISSegmentRoutingDataplane.Input(instances=instances)


class TestTunnelPath:
    """Test anta.input_models.routing.isis.TestTunnelPath."""

    # pylint: disable=too-few-public-methods

    @pytest.mark.parametrize(
        ("nexthop", "type", "interface", "tunnel_id", "expected"),
        [
            pytest.param("1.1.1.1", None, None, None, "Next-hop: 1.1.1.1", id="nexthop"),
            pytest.param(None, "ip", None, None, "Type: ip", id="type"),
            pytest.param(None, None, "Et1", None, "Interface: Ethernet1", id="interface"),
            pytest.param(None, None, None, "TI-LFA", "TunnelID: TI-LFA", id="tunnel_id"),
            pytest.param("1.1.1.1", "ip", "Et1", "TI-LFA", "Next-hop: 1.1.1.1 Type: ip Interface: Ethernet1 TunnelID: TI-LFA", id="all"),
            pytest.param(None, None, None, None, "", id="None"),
        ],
    )
    def test_valid__str__(
        self,
        nexthop: IPv4Address | None,
        type: Literal["ip", "tunnel"] | None,  # noqa: A002
        interface: Interface | None,
        tunnel_id: Literal["TI-LFA", "ti-lfa", "unset"] | None,
        expected: str,
    ) -> None:
        """Test TunnelPath __str__."""
        assert str(TunnelPath(nexthop=nexthop, type=type, interface=interface, tunnel_id=tunnel_id)) == expected
