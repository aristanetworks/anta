# Copyright (c) 2023-2025 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Tests for anta.input_models.routing.isis.py."""

from __future__ import annotations

from typing import TYPE_CHECKING, Literal

import pytest
from pydantic import ValidationError

from anta.input_models.routing.isis import ISISInstance, TunnelPath
from anta.tests.routing.isis import VerifyISISInterfaceAuthMode, VerifyISISSegmentRoutingAdjacencySegments, VerifyISISSegmentRoutingDataplane

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
            pytest.param(None, None, None, "TI-LFA", "Tunnel ID: TI-LFA", id="tunnel_id"),
            pytest.param("1.1.1.1", "ip", "Et1", "TI-LFA", "Next-hop: 1.1.1.1 Type: ip Interface: Ethernet1 Tunnel ID: TI-LFA", id="all"),
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


class TestVerifyISISInterfaceAuthModeInput:
    """Test anta.tests.routing.isis.TestVerifyISISInterfaceAuthModeInput.Input."""

    @pytest.mark.parametrize(
        ("instances"),
        [
            pytest.param(
                [{"name": "CORE-ISIS", "vrf": "default", "interfaces": [{"name": "Ethernet1", "level": 2, "authentication_mode": "Text"}]}],
                id="valid_auth_mode_text",
            ),
            pytest.param(
                [{"name": "CORE-ISIS-1", "vrf": "default", "interfaces": [{"name": "Ethernet2", "level": 2, "authentication_mode": "MD5"}]}],
                id="valid_auth_mode_md5",
            ),
            pytest.param(
                [{"name": "CORE-ISIS-2", "vrf": "default", "interfaces": [{"name": "Ethernet3", "level": 2, "authentication_mode": "SHA", "auth_key_id": 10}]}],
                id="valid_auth_mode_sha",
            ),
            pytest.param(
                [
                    {
                        "name": "CORE-ISIS-3",
                        "vrf": "default",
                        "interfaces": [{"name": "Ethernet4", "level": 2, "authentication_mode": "shared-secret", "shared_secret_key_profile": "Secret"}],
                    }
                ],
                id="valid_auth_mode_shared_secret",
            ),
        ],
    )
    def test_valid(self, instances: list[ISISInstance]) -> None:
        """Test VerifyISISInterfaceAuthMode.Input valid inputs."""
        VerifyISISInterfaceAuthMode.Input(instances=instances)

    @pytest.mark.parametrize(
        ("instances"),
        [
            pytest.param(
                [{"name": "CORE-ISIS", "vrf": "default", "interfaces": [{"name": "Ethernet1", "level": 2, "authentication_mode": "Text2"}]}], id="invalid_auth_mode"
            ),
            pytest.param([{"name": "CORE-ISIS", "vrf": "default"}], id="interfaces_details_not_found"),
            pytest.param([{"name": "CORE-ISIS-2", "vrf": "default", "interfaces": [{"name": "Ethernet3", "level": 2}]}], id="auth_mode_not_found"),
            pytest.param(
                [{"name": "CORE-ISIS-2", "vrf": "default", "interfaces": [{"name": "Ethernet4", "level": 2, "authentication_mode": "SHA", "auth_key_id": None}]}],
                id="invalid_auth_key_id",
            ),
            pytest.param(
                [{"name": "CORE-ISIS-3", "vrf": "default", "interfaces": [{"name": "Ethernet5", "level": 2, "authentication_mode": "shared-secret"}]}],
                id="invalid_shared_secret_profile",
            ),
        ],
    )
    def test_invalid(self, instances: list[ISISInstance]) -> None:
        """Test VerifyISISInterfaceAuthMode.Input invalid inputs."""
        with pytest.raises(ValidationError):
            VerifyISISInterfaceAuthMode.Input(instances=instances)
