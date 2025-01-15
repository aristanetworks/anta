# Copyright (c) 2023-2025 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Tests for anta.input_models.bfd.py."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
from pydantic import ValidationError

from anta.tests.bfd import VerifyBFDPeersIntervals, VerifyBFDPeersRegProtocols

if TYPE_CHECKING:
    from anta.input_models.bfd import BFDPeer


class TestVerifyBFDPeersIntervalsInput:
    """Test anta.tests.bfd.VerifyBFDPeersIntervals.Input."""

    @pytest.mark.parametrize(
        ("bfd_peers"),
        [
            pytest.param([{"peer_address": "10.0.0.1", "vrf": "default", "tx_interval": 1200, "rx_interval": 1200, "multiplier": 3}], id="valid"),
        ],
    )
    def test_valid(self, bfd_peers: list[BFDPeer]) -> None:
        """Test VerifyBFDPeersIntervals.Input valid inputs."""
        VerifyBFDPeersIntervals.Input(bfd_peers=bfd_peers)

    @pytest.mark.parametrize(
        ("bfd_peers"),
        [
            pytest.param([{"peer_address": "10.0.0.1", "vrf": "default", "tx_interval": 1200}], id="invalid-tx-interval"),
            pytest.param([{"peer_address": "10.0.0.1", "vrf": "default", "rx_interval": 1200}], id="invalid-rx-interval"),
            pytest.param([{"peer_address": "10.0.0.1", "vrf": "default", "tx_interval": 1200, "rx_interval": 1200}], id="invalid-multiplier"),
        ],
    )
    def test_invalid(self, bfd_peers: list[BFDPeer]) -> None:
        """Test VerifyBFDPeersIntervals.Input invalid inputs."""
        with pytest.raises(ValidationError):
            VerifyBFDPeersIntervals.Input(bfd_peers=bfd_peers)


class TestVerifyBFDPeersRegProtocolsInput:
    """Test anta.tests.bfd.VerifyBFDPeersRegProtocols.Input."""

    @pytest.mark.parametrize(
        ("bfd_peers"),
        [
            pytest.param([{"peer_address": "10.0.0.1", "vrf": "default", "protocols": ["bgp"]}], id="valid"),
        ],
    )
    def test_valid(self, bfd_peers: list[BFDPeer]) -> None:
        """Test VerifyBFDPeersRegProtocols.Input valid inputs."""
        VerifyBFDPeersRegProtocols.Input(bfd_peers=bfd_peers)

    @pytest.mark.parametrize(
        ("bfd_peers"),
        [
            pytest.param([{"peer_address": "10.0.0.1", "vrf": "default"}], id="invalid"),
        ],
    )
    def test_invalid(self, bfd_peers: list[BFDPeer]) -> None:
        """Test VerifyBFDPeersRegProtocols.Input invalid inputs."""
        with pytest.raises(ValidationError):
            VerifyBFDPeersRegProtocols.Input(bfd_peers=bfd_peers)
