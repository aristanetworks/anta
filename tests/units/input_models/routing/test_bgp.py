# Copyright (c) 2023-2025 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Tests for anta.input_models.routing.bgp.py."""

# pylint: disable=C0302
from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
from pydantic import ValidationError

from anta.input_models.routing.bgp import BgpAddressFamily, BgpPeer, BgpRoute
from anta.tests.routing.bgp import (
    VerifyBGPExchangedRoutes,
    VerifyBGPNlriAcceptance,
    VerifyBGPPeerCount,
    VerifyBGPPeerGroup,
    VerifyBGPPeerMPCaps,
    VerifyBGPPeerRouteLimit,
    VerifyBGPPeerTtlMultiHops,
    VerifyBGPRouteECMP,
    VerifyBgpRouteMaps,
    VerifyBGPRoutePaths,
    VerifyBGPSpecificPeers,
    VerifyBGPTimers,
)

if TYPE_CHECKING:
    from anta.custom_types import Afi, Safi


class TestBgpAddressFamily:
    """Test anta.input_models.routing.bgp.BgpAddressFamily."""

    @pytest.mark.parametrize(
        ("afi", "safi", "vrf"),
        [
            pytest.param("ipv4", "unicast", "MGMT", id="afi"),
            pytest.param("evpn", None, "default", id="safi"),
            pytest.param("ipv4", "unicast", "default", id="vrf"),
        ],
    )
    def test_valid(self, afi: Afi, safi: Safi, vrf: str) -> None:
        """Test BgpAddressFamily valid inputs."""
        BgpAddressFamily(afi=afi, safi=safi, vrf=vrf)

    @pytest.mark.parametrize(
        ("afi", "safi", "vrf"),
        [
            pytest.param("ipv4", None, "default", id="afi"),
            pytest.param("evpn", "multicast", "default", id="safi"),
            pytest.param("evpn", None, "MGMT", id="vrf"),
        ],
    )
    def test_invalid(self, afi: Afi, safi: Safi, vrf: str) -> None:
        """Test BgpAddressFamily invalid inputs."""
        with pytest.raises(ValidationError):
            BgpAddressFamily(afi=afi, safi=safi, vrf=vrf)


class TestVerifyBGPPeerCountInput:
    """Test anta.tests.routing.bgp.VerifyBGPPeerCount.Input."""

    @pytest.mark.parametrize(
        ("address_families"),
        [
            pytest.param([{"afi": "evpn", "num_peers": 2}], id="valid"),
        ],
    )
    def test_valid(self, address_families: list[BgpAddressFamily]) -> None:
        """Test VerifyBGPPeerCount.Input valid inputs."""
        VerifyBGPPeerCount.Input(address_families=address_families)

    @pytest.mark.parametrize(
        ("address_families"),
        [
            pytest.param([{"afi": "evpn", "num_peers": 0}], id="zero-peer"),
            pytest.param([{"afi": "evpn"}], id="None"),
        ],
    )
    def test_invalid(self, address_families: list[BgpAddressFamily]) -> None:
        """Test VerifyBGPPeerCount.Input invalid inputs."""
        with pytest.raises(ValidationError):
            VerifyBGPPeerCount.Input(address_families=address_families)


class TestVerifyBGPSpecificPeersInput:
    """Test anta.tests.routing.bgp.VerifyBGPSpecificPeers.Input."""

    @pytest.mark.parametrize(
        ("address_families"),
        [
            pytest.param([{"afi": "evpn", "peers": ["10.1.0.1", "10.1.0.2"]}], id="valid"),
        ],
    )
    def test_valid(self, address_families: list[BgpAddressFamily]) -> None:
        """Test VerifyBGPSpecificPeers.Input valid inputs."""
        VerifyBGPSpecificPeers.Input(address_families=address_families)

    @pytest.mark.parametrize(
        ("address_families"),
        [
            pytest.param([{"afi": "evpn"}], id="None"),
        ],
    )
    def test_invalid(self, address_families: list[BgpAddressFamily]) -> None:
        """Test VerifyBGPSpecificPeers.Input invalid inputs."""
        with pytest.raises(ValidationError):
            VerifyBGPSpecificPeers.Input(address_families=address_families)


class TestVerifyBGPExchangedRoutesInput:
    """Test anta.tests.routing.bgp.VerifyBGPExchangedRoutes.Input."""

    @pytest.mark.parametrize(
        ("bgp_peers"),
        [
            pytest.param(
                [{"peer_address": "172.30.255.5", "vrf": "default", "advertised_routes": ["192.0.254.5/32"], "received_routes": ["192.0.255.4/32"]}],
                id="valid_both_received_advertised",
            ),
            pytest.param([{"peer_address": "172.30.255.5", "vrf": "default", "advertised_routes": ["192.0.254.5/32"]}], id="valid_advertised_routes"),
        ],
    )
    def test_valid(self, bgp_peers: list[BgpPeer]) -> None:
        """Test VerifyBGPExchangedRoutes.Input valid inputs."""
        VerifyBGPExchangedRoutes.Input(bgp_peers=bgp_peers)

    @pytest.mark.parametrize(
        ("bgp_peers"),
        [
            pytest.param([{"peer_address": "172.30.255.5", "vrf": "default"}], id="invalid"),
        ],
    )
    def test_invalid(self, bgp_peers: list[BgpPeer]) -> None:
        """Test VerifyBGPExchangedRoutes.Input invalid inputs."""
        with pytest.raises(ValidationError):
            VerifyBGPExchangedRoutes.Input(bgp_peers=bgp_peers)


class TestVerifyBGPPeerMPCapsInput:
    """Test anta.tests.routing.bgp.VerifyBGPPeerMPCaps.Input."""

    @pytest.mark.parametrize(
        ("bgp_peers"),
        [
            pytest.param([{"peer_address": "172.30.255.5", "vrf": "default", "capabilities": ["ipv4Unicast"]}], id="valid"),
        ],
    )
    def test_valid(self, bgp_peers: list[BgpPeer]) -> None:
        """Test VerifyBGPPeerMPCaps.Input valid inputs."""
        VerifyBGPPeerMPCaps.Input(bgp_peers=bgp_peers)

    @pytest.mark.parametrize(
        ("bgp_peers"),
        [
            pytest.param([{"peer_address": "172.30.255.5", "vrf": "default"}], id="invalid"),
        ],
    )
    def test_invalid(self, bgp_peers: list[BgpPeer]) -> None:
        """Test VerifyBGPPeerMPCaps.Input invalid inputs."""
        with pytest.raises(ValidationError):
            VerifyBGPPeerMPCaps.Input(bgp_peers=bgp_peers)


class TestVerifyBGPTimersInput:
    """Test anta.tests.routing.bgp.VerifyBGPTimers.Input."""

    @pytest.mark.parametrize(
        ("bgp_peers"),
        [
            pytest.param([{"peer_address": "172.30.255.5", "vrf": "default", "hold_time": 180, "keep_alive_time": 60}], id="valid"),
        ],
    )
    def test_valid(self, bgp_peers: list[BgpPeer]) -> None:
        """Test VerifyBGPTimers.Input valid inputs."""
        VerifyBGPTimers.Input(bgp_peers=bgp_peers)

    @pytest.mark.parametrize(
        ("bgp_peers"),
        [
            pytest.param([{"peer_address": "172.30.255.5", "vrf": "default"}], id="invalid"),
            pytest.param([{"peer_address": "172.30.255.5", "vrf": "default", "hold_time": 180}], id="invalid_keep_alive"),
            pytest.param([{"peer_address": "172.30.255.5", "vrf": "default", "keep_alive_time": 180}], id="invalid_hold_time"),
        ],
    )
    def test_invalid(self, bgp_peers: list[BgpPeer]) -> None:
        """Test VerifyBGPTimers.Input invalid inputs."""
        with pytest.raises(ValidationError):
            VerifyBGPTimers.Input(bgp_peers=bgp_peers)


class TestVerifyBgpRouteMapsInput:
    """Test anta.tests.routing.bgp.VerifyBgpRouteMaps.Input."""

    @pytest.mark.parametrize(
        ("bgp_peers"),
        [
            pytest.param([{"peer_address": "172.30.255.5", "vrf": "default", "inbound_route_map": "Test", "outbound_route_map": "Test"}], id="valid"),
        ],
    )
    def test_valid(self, bgp_peers: list[BgpPeer]) -> None:
        """Test VerifyBgpRouteMaps.Input valid inputs."""
        VerifyBgpRouteMaps.Input(bgp_peers=bgp_peers)

    @pytest.mark.parametrize(
        ("bgp_peers"),
        [
            pytest.param([{"peer_address": "172.30.255.5", "vrf": "default"}], id="invalid"),
        ],
    )
    def test_invalid(self, bgp_peers: list[BgpPeer]) -> None:
        """Test VerifyBgpRouteMaps.Input invalid inputs."""
        with pytest.raises(ValidationError):
            VerifyBgpRouteMaps.Input(bgp_peers=bgp_peers)


class TestVerifyBGPPeerRouteLimitInput:
    """Test anta.tests.routing.bgp.VerifyBGPPeerRouteLimit.Input."""

    @pytest.mark.parametrize(
        ("bgp_peers"),
        [
            pytest.param([{"peer_address": "172.30.255.5", "vrf": "default", "maximum_routes": 10000}], id="valid"),
        ],
    )
    def test_valid(self, bgp_peers: list[BgpPeer]) -> None:
        """Test VerifyBGPPeerRouteLimit.Input valid inputs."""
        VerifyBGPPeerRouteLimit.Input(bgp_peers=bgp_peers)

    @pytest.mark.parametrize(
        ("bgp_peers"),
        [
            pytest.param([{"peer_address": "172.30.255.5", "vrf": "default"}], id="invalid"),
        ],
    )
    def test_invalid(self, bgp_peers: list[BgpPeer]) -> None:
        """Test VerifyBGPPeerRouteLimit.Input invalid inputs."""
        with pytest.raises(ValidationError):
            VerifyBGPPeerRouteLimit.Input(bgp_peers=bgp_peers)


class TestVerifyBGPPeerGroupInput:
    """Test anta.tests.routing.bgp.VerifyBGPPeerGroup.Input."""

    @pytest.mark.parametrize(
        ("bgp_peers"),
        [
            pytest.param([{"peer_address": "172.30.255.5", "vrf": "default", "peer_group": "IPv4-UNDERLAY-PEERS"}], id="valid"),
        ],
    )
    def test_valid(self, bgp_peers: list[BgpPeer]) -> None:
        """Test VerifyBGPPeerGroup.Input valid inputs."""
        VerifyBGPPeerGroup.Input(bgp_peers=bgp_peers)

    @pytest.mark.parametrize(
        ("bgp_peers"),
        [
            pytest.param([{"peer_address": "172.30.255.5", "vrf": "default"}], id="invalid"),
        ],
    )
    def test_invalid(self, bgp_peers: list[BgpPeer]) -> None:
        """Test VerifyBGPPeerGroup.Input invalid inputs."""
        with pytest.raises(ValidationError):
            VerifyBGPPeerGroup.Input(bgp_peers=bgp_peers)


class TestVerifyBGPNlriAcceptanceInput:
    """Test anta.tests.routing.bgp.VerifyBGPNlriAcceptance.Input."""

    @pytest.mark.parametrize(
        ("bgp_peers"),
        [
            pytest.param([{"peer_address": "172.30.255.5", "vrf": "default", "capabilities": ["ipv4Unicast"]}], id="valid"),
        ],
    )
    def test_valid(self, bgp_peers: list[BgpPeer]) -> None:
        """Test VerifyBGPNlriAcceptance.Input valid inputs."""
        VerifyBGPNlriAcceptance.Input(bgp_peers=bgp_peers)

    @pytest.mark.parametrize(
        ("bgp_peers"),
        [
            pytest.param([{"peer_address": "172.30.255.5", "vrf": "default"}], id="invalid"),
        ],
    )
    def test_invalid(self, bgp_peers: list[BgpPeer]) -> None:
        """Test VerifyBGPNlriAcceptance.Input invalid inputs."""
        with pytest.raises(ValidationError):
            VerifyBGPNlriAcceptance.Input(bgp_peers=bgp_peers)


class TestVerifyBGPRouteECMPInput:
    """Test anta.tests.routing.bgp.VerifyBGPRouteECMP.Input."""

    @pytest.mark.parametrize(
        ("bgp_routes"),
        [
            pytest.param([{"prefix": "10.100.0.128/31", "vrf": "default", "ecmp_count": 2}], id="valid"),
        ],
    )
    def test_valid(self, bgp_routes: list[BgpRoute]) -> None:
        """Test VerifyBGPRouteECMP.Input valid inputs."""
        VerifyBGPRouteECMP.Input(route_entries=bgp_routes)

    @pytest.mark.parametrize(
        ("bgp_routes"),
        [
            pytest.param([{"prefix": "10.100.0.128/31", "vrf": "default"}], id="invalid"),
        ],
    )
    def test_invalid(self, bgp_routes: list[BgpRoute]) -> None:
        """Test VerifyBGPRouteECMP.Input invalid inputs."""
        with pytest.raises(ValidationError):
            VerifyBGPRouteECMP.Input(route_entries=bgp_routes)


class TestVerifyBGPRoutePathsInput:
    """Test anta.tests.routing.bgp.VerifyBGPRoutePaths.Input."""

    @pytest.mark.parametrize(
        ("route_entries"),
        [
            pytest.param(
                [
                    {
                        "prefix": "10.100.0.128/31",
                        "vrf": "default",
                        "paths": [{"nexthop": "10.100.0.10", "origin": "Igp"}, {"nexthop": "10.100.4.5", "origin": "Incomplete"}],
                    }
                ],
                id="valid",
            ),
        ],
    )
    def test_valid(self, route_entries: list[BgpRoute]) -> None:
        """Test VerifyBGPRoutePaths.Input valid inputs."""
        VerifyBGPRoutePaths.Input(route_entries=route_entries)

    @pytest.mark.parametrize(
        ("route_entries"),
        [
            pytest.param([{"prefix": "10.100.0.128/31", "vrf": "default"}], id="invalid"),
        ],
    )
    def test_invalid(self, route_entries: list[BgpRoute]) -> None:
        """Test VerifyBGPRoutePaths.Input invalid inputs."""
        with pytest.raises(ValidationError):
            VerifyBGPRoutePaths.Input(route_entries=route_entries)


class TestVerifyBGPPeerTtlMultiHopsInput:
    """Test anta.tests.routing.bgp.VerifyBGPPeerTtlMultiHops.Input."""

    @pytest.mark.parametrize(
        ("bgp_peers"),
        [
            pytest.param([{"peer_address": "172.30.255.5", "vrf": "default", "ttl_duration": 3, "max_ttl_hops": 3}], id="valid"),
        ],
    )
    def test_valid(self, bgp_peers: list[BgpPeer]) -> None:
        """Test VerifyBGPPeerTtlMultiHops.Input valid inputs."""
        VerifyBGPPeerTtlMultiHops.Input(bgp_peers=bgp_peers)

    @pytest.mark.parametrize(
        ("bgp_peers"),
        [
            pytest.param([{"peer_address": "172.30.255.5", "vrf": "default", "ttl_duration": None, "max_ttl_hops": 3}], id="invalid-ttl-time"),
            pytest.param([{"peer_address": "172.30.255.6", "vrf": "default", "ttl_duration": 3, "max_ttl_hops": None}], id="invalid-max-ttl-hops"),
        ],
    )
    def test_invalid(self, bgp_peers: list[BgpPeer]) -> None:
        """Test VerifyBGPPeerTtlMultiHops.Input invalid inputs."""
        with pytest.raises(ValidationError):
            VerifyBGPPeerTtlMultiHops.Input(bgp_peers=bgp_peers)
