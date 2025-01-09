# Copyright (c) 2023-2025 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Module containing input models for security tests."""

from __future__ import annotations

from ipaddress import IPv4Address
from typing import Any
from warnings import warn

from pydantic import BaseModel, ConfigDict


class IPSecPeer(BaseModel):
    """IPSec (Internet Protocol Security) model represents the details of an IPv4 security peer."""

    model_config = ConfigDict(extra="forbid")
    peer: IPv4Address
    """The IPv4 address of the security peer."""
    vrf: str = "default"
    """VRF context. Defaults to `default`."""
    connections: list[IPSecConn] | None = None
    """A list of IPv4 security connections associated with the peer. Defaults to None."""

    def __str__(self) -> str:
        """Return a string representation of the IPSecPeer model. Used in failure messages.

        Examples
        --------
        - Peer: 1.1.1.1 VRF: default
        """
        return f"Peer: {self.peer} VRF: {self.vrf}"


class IPSecConn(BaseModel):
    """Details of an IPv4 security connection for a peer."""

    model_config = ConfigDict(extra="forbid")
    source_address: IPv4Address
    """The IPv4 address of the source in the security connection."""
    destination_address: IPv4Address
    """The IPv4 address of the destination in the security connection."""


class IPSecPeers(IPSecPeer):  # pragma: no cover
    """Alias for the IPSecPeers model to maintain backward compatibility.

    When initialized, it will emit a deprecation warning and call the IPSecPeer model.

    TODO: Remove this class in ANTA v2.0.0.
    """

    def __init__(self, **data: Any) -> None:  # noqa: ANN401
        """Initialize the IPSecPeer class, emitting a deprecation warning."""
        warn(
            message="IPSecPeers model is deprecated and will be removed in ANTA v2.0.0. Use the IPSecPeer model instead.",
            category=DeprecationWarning,
            stacklevel=2,
        )
        super().__init__(**data)
