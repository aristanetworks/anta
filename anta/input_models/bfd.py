# Copyright (c) 2023-2025 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Module containing input models for BFD tests."""

from __future__ import annotations

from ipaddress import IPv4Address

from pydantic import BaseModel, ConfigDict

from anta.custom_types import BfdInterval, BfdMultiplier, BfdProtocol


class BFDPeer(BaseModel):
    """BFD (Bidirectional Forwarding Detection) model representing the peer details.

    Only IPv4 peers are supported for now.
    """

    model_config = ConfigDict(extra="forbid")
    peer_address: IPv4Address
    """IPv4 address of a BFD peer."""
    vrf: str = "default"
    """Optional VRF for the BFD peer. Defaults to `default`."""
    tx_interval: BfdInterval | None = None
    """Tx interval of BFD peer in milliseconds. Required field in the `VerifyBFDPeersIntervals` test."""
    rx_interval: BfdInterval | None = None
    """Rx interval of BFD peer in milliseconds. Required field in the `VerifyBFDPeersIntervals` test."""
    multiplier: BfdMultiplier | None = None
    """Multiplier of BFD peer. Required field in the `VerifyBFDPeersIntervals` test."""
    protocols: list[BfdProtocol] | None = None
    """List of protocols to be verified. Required field in the `VerifyBFDPeersRegProtocols` test."""

    def __str__(self) -> str:
        """Return a human-readable string representation of the BFDPeer for reporting."""
        return f"Peer: {self.peer_address} VRF: {self.vrf}"
