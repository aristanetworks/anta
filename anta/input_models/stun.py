# Copyright (c) 2023-2025 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Module containing input models for services tests."""

from __future__ import annotations

from ipaddress import IPv4Address

from pydantic import BaseModel, ConfigDict

from anta.custom_types import Port


class StunClientTranslation(BaseModel):
    """STUN (Session Traversal Utilities for NAT) model represents the configuration of an IPv4-based client translations."""

    model_config = ConfigDict(extra="forbid")
    source_address: IPv4Address
    """The IPv4 address of the STUN client"""
    source_port: Port = 4500
    """The port number used by the STUN client for communication. Defaults to 4500."""
    public_address: IPv4Address | None = None
    """The public-facing IPv4 address of the STUN client, discovered via the STUN server."""
    public_port: Port | None = None
    """The public-facing port number of the STUN client, discovered via the STUN server."""

    def __str__(self) -> str:
        """Return a human-readable string representation of the StunClientTranslation for reporting.

        Examples
        --------
        Client 10.0.0.1 Port: 4500
        """
        return f"Client {self.source_address} Port: {self.source_port}"
