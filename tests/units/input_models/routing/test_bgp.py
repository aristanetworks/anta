# Copyright (c) 2023-2025 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Tests for anta.input_models.routing.bgp.py."""

# pylint: disable=C0302
from __future__ import annotations

from typing import TYPE_CHECKING, Any

import pytest
from pydantic import ValidationError

from anta.input_models.routing.bgp import AddressFamilyConfig, BgpAddressFamily, BgpPeer, BgpRoute, RedistributedRouteConfig
from anta.tests.routing.bgp import (
    VerifyBGPExchangedRoutes,
    VerifyBGPNlriAcceptance,
    VerifyBGPPeerCount,
    VerifyBGPPeerGroup,
    VerifyBGPPeerMPCaps,
    VerifyBGPPeerRouteLimit,
    VerifyBGPRouteECMP,
    VerifyBgpRouteMaps,
    VerifyBGPRoutePaths,
    VerifyBGPSpecificPeers,
    VerifyBGPTimers,
)

if TYPE_CHECKING:
    from anta.custom_types import Afi, RedistributedAfiSafi, RedistributedProtocol, Safi


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


class TestVerifyBGPRedistributedRoute:
    """Test anta.input_models.routing.bgp.RedistributedRouteConfig."""

    @pytest.mark.parametrize(
        ("proto", "include_leaked"),
        [
            pytest.param("Connected", True, id="proto-valid"),
            pytest.param("Static", False, id="proto-valid-leaked-false"),
            pytest.param("User", False, id="proto-User"),
        ],
    )
    def test_validate_inputs(self, proto: RedistributedProtocol, include_leaked: bool) -> None:
        """Test RedistributedRouteConfig valid inputs."""
        RedistributedRouteConfig(proto=proto, include_leaked=include_leaked)

    @pytest.mark.parametrize(
        ("proto", "include_leaked"),
        [
            pytest.param("Dynamic", True, id="proto-valid"),
            pytest.param("User", True, id="proto-valid-leaked-false"),
        ],
    )
    def test_invalid(self, proto: RedistributedProtocol, include_leaked: bool) -> None:
        """Test RedistributedRouteConfig invalid inputs."""
        with pytest.raises(ValidationError):
            RedistributedRouteConfig(proto=proto, include_leaked=include_leaked)

    @pytest.mark.parametrize(
        ("proto", "include_leaked", "route_map", "expected"),
        [
            pytest.param("Connected", True, "RM-CONN-2-BGP", "Proto: Connected, Include Leaked: present, Route Map: RM-CONN-2-BGP", id="check-all-params"),
            pytest.param("Static", False, None, "Proto: Static", id="check-proto-include_leaked"),
            pytest.param("User", False, "RM-CONN-2-BGP", "Proto: EOS SDK, Route Map: RM-CONN-2-BGP", id="check-proto-route_map"),
            pytest.param("Dynamic", False, None, "Proto: Dynamic", id="check-proto-only"),
        ],
    )
    def test_valid_str(self, proto: RedistributedProtocol, include_leaked: bool, route_map: str | None, expected: str) -> None:
        """Test RedistributedRouteConfig __str__."""
        assert str(RedistributedRouteConfig(proto=proto, include_leaked=include_leaked, route_map=route_map)) == expected


class TestVerifyBGPAddressFamilyConfig:
    """Test anta.input_models.routing.bgp.AddressFamilyConfig."""

    @pytest.mark.parametrize(
        ("afi_safi", "redistributed_routes"),
        [
            pytest.param("ipv4Unicast", [{"proto": "OSPFv3 External", "include_leaked": True, "route_map": "RM-CONN-2-BGP"}], id="afisafi-ipv4-unicast"),
            pytest.param("ipv6 Multicast", [{"proto": "OSPF Internal", "include_leaked": True, "route_map": "RM-CONN-2-BGP"}], id="afisafi-ipv6-multicast"),
            pytest.param("ipv4-Multicast", [{"proto": "IS-IS", "include_leaked": False, "route_map": "RM-CONN-2-BGP"}], id="afisafi-ipv4-multicast"),
            pytest.param("ipv6_Unicast", [{"proto": "AttachedHost", "route_map": "RM-CONN-2-BGP"}], id="afisafi-ipv6-unicast"),
        ],
    )
    def test_valid(self, afi_safi: RedistributedAfiSafi, redistributed_routes: list[Any]) -> None:
        """Test AddressFamilyConfig valid inputs."""
        AddressFamilyConfig(afi_safi=afi_safi, redistributed_routes=redistributed_routes)

    @pytest.mark.parametrize(
        ("afi_safi", "redistributed_routes"),
        [
            pytest.param("evpn", [{"proto": "OSPFv3 Nssa-External", "include_leaked": True, "route_map": "RM-CONN-2-BGP"}], id="invalid-address-family"),
            pytest.param("ipv6 sr-te", [{"proto": "RIP", "route_map": "RM-CONN-2-BGP"}], id="ipv6-invalid-address-family"),
            pytest.param("iipv6_Unicast", [{"proto": "Bgp", "include_leaked": True, "route_map": "RM-CONN-2-BGP"}], id="ipv6-unicast-invalid-address-family"),
            pytest.param("ipv6_Unicastt", [{"proto": "Static", "include_leaked": True, "route_map": "RM-CONN-2-BGP"}], id="ipv6-unicast-invalid-address-family"),
        ],
    )
    def test_invalid(self, afi_safi: RedistributedAfiSafi, redistributed_routes: list[Any]) -> None:
        """Test AddressFamilyConfig invalid inputs."""
        with pytest.raises(ValidationError):
            AddressFamilyConfig(afi_safi=afi_safi, redistributed_routes=redistributed_routes)

    @pytest.mark.parametrize(
        ("afi_safi", "redistributed_routes", "expected"),
        [
            pytest.param(
                "v4u", [{"proto": "OSPFv3 Nssa-External", "include_leaked": True, "route_map": "RM-CONN-2-BGP"}], "AFI-SAFI: IPv4 Unicast", id="valid-ipv4-unicast"
            ),
            pytest.param("v4m", [{"proto": "RIP", "route_map": "RM-CONN-2-BGP"}], "AFI-SAFI: IPv4 Multicast", id="valid-ipv4-multicast"),
            pytest.param("v6u", [{"proto": "Bgp", "include_leaked": True, "route_map": "RM-CONN-2-BGP"}], "AFI-SAFI: IPv6 Unicast", id="valid-ipv6-unicast"),
            pytest.param("v6m", [{"proto": "Static", "include_leaked": True, "route_map": "RM-CONN-2-BGP"}], "AFI-SAFI: IPv6 Multicast", id="valid-ipv6-multicast"),
        ],
    )
    def test_valid_str(self, afi_safi: RedistributedAfiSafi, redistributed_routes: list[Any], expected: str) -> None:
        """Test AddressFamilyConfig __str__."""
        assert str(AddressFamilyConfig(afi_safi=afi_safi, redistributed_routes=redistributed_routes)) == expected
