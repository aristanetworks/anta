# Copyright (c) 2023-2025 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Tests for anta.input_models.routing.bgp.py."""

# pylint: disable=C0302
from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
from pydantic import ValidationError

from anta.input_models.routing.bgp import BgpAddressFamily
from anta.tests.routing.bgp import VerifyBGPPeerCount, VerifyBGPSpecificPeers

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
