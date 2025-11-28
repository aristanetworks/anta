# Copyright (c) 2023-2025 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Module containing input models for connectivity tests."""

from __future__ import annotations

from ipaddress import IPv4Address, IPv6Address
from typing import Any
from warnings import warn

from pydantic import BaseModel, ConfigDict

from anta.custom_types import Interface


class Host(BaseModel):
    """Model for a remote host to ping."""

    model_config = ConfigDict(extra="forbid")
    destination: IPv4Address | IPv6Address
    """Destination address to ping."""
    source: IPv4Address | IPv6Address | Interface | None = None
    """Source address IP or egress interface to use. Can be provided in the `VerifyReachability` test."""
    description: str | None = None
    """Description of the remote destination."""
    vrf: str = "default"
    """VRF context."""
    repeat: int = 2
    """Number of ping repetition."""
    size: int = 100
    """Specify datagram size."""
    df_bit: bool = False
    """Enable do not fragment bit in IP header."""
    reachable: bool = True
    """Indicates whether the destination should be reachable."""

    def __str__(self) -> str:
        """Return a human-readable string representation of the Host for reporting."""
        return (
            f"Destination {self.destination}"
            f"{f' ({self.description})' if self.description is not None else ''}"
            f"{f' from {self.source}' if self.source is not None else ''}"
            f" in VRF {self.vrf}"
        )


class LLDPNeighbor(BaseModel):
    """LLDP (Link Layer Discovery Protocol) model representing the port details and neighbor information."""

    model_config = ConfigDict(extra="forbid")
    port: Interface
    """The LLDP port for the local device."""
    neighbor_device: str
    """The system name of the LLDP neighbor device."""
    neighbor_port: str
    """The LLDP port on the neighboring device."""

    def __str__(self) -> str:
        """Return a human-readable string representation of the LLDPNeighbor for reporting.

        Examples
        --------
        Port: Ethernet1 Neighbor: DC1-SPINE2 Neighbor Port: Ethernet2

        """
        return f"Port: {self.port} Neighbor: {self.neighbor_device} Neighbor Port: {self.neighbor_port}"


class Neighbor(LLDPNeighbor):  # pragma: no cover
    """Alias for the LLDPNeighbor model to maintain backward compatibility.

    When initialized, it will emit a deprecation warning and call the LLDPNeighbor model.

    TODO: Remove this class in ANTA v2.0.0.
    """

    def __init__(self, **data: Any) -> None:  # noqa: ANN401
        """Initialize the LLDPNeighbor class, emitting a depreciation warning."""
        warn(
            message="Neighbor model is deprecated and will be removed in ANTA v2.0.0. Use the LLDPNeighbor model instead.",
            category=DeprecationWarning,
            stacklevel=2,
        )
        super().__init__(**data)
