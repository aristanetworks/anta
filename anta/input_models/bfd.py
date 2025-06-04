# Copyright (c) 2023-2025 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Module containing input models for BFD tests."""

from __future__ import annotations

from ipaddress import IPv4Address, IPv6Address

from pydantic import BaseModel, ConfigDict

from anta.custom_types import BfdInterval, BfdMultiplier, BfdProtocol, Interface


class BFDPeer(BaseModel):
    """Model for a BFD peer."""

    model_config = ConfigDict(extra="forbid")
    peer_address: IPv4Address | IPv6Address
    """IPv4 or IPv6 address of the BFD peer."""
    vrf: str = "default"
    """VRF of the BFD peer."""
    interface: Interface | None = None
    """Single-hop transport interface. Use `None` for multi-hop sessions."""
    protocols: list[BfdProtocol] | None = None
    """List of protocols using BFD with this peer. Required field in the `VerifyBFDPeersRegProtocols` test."""
    tx_interval: BfdInterval | None = None
    """Operational transmit interval of the BFD session in milliseconds. Required field in the `VerifyBFDPeersIntervals` test."""
    rx_interval: BfdInterval | None = None
    """Operational minimum receive interval of the BFD session in milliseconds. Required field in the `VerifyBFDPeersIntervals` test."""
    multiplier: BfdMultiplier | None = None
    """Multiplier of the BFD session. Required field in the `VerifyBFDPeersIntervals` test."""
    detection_time: int | None = None
    """Detection time of the BFD session in milliseconds. Defines how long it takes for BFD to detect connection failure.

    Optional field in the `VerifyBFDPeersIntervals` test."""

    def __str__(self) -> str:
        """Return a human-readable string representation of the BFDPeer for reporting."""
        base = f"Peer: {self.peer_address} VRF: {self.vrf}"
        if self.interface is not None:
            base += f" Interface: {self.interface}"
        return base
