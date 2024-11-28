# Copyright (c) 2023-2024 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Module containing input models for services tests."""

from __future__ import annotations

from ipaddress import IPv4Address, IPv6Address

from pydantic import BaseModel, ConfigDict, Field


class DnsServer(BaseModel):
    """Model for a DNS server configuration."""

    model_config = ConfigDict(extra="forbid")
    server_address: IPv4Address | IPv6Address
    """The IPv4 or IPv6 address of the DNS server."""
    vrf: str = "default"
    """The VRF instance in which the DNS server resides. Defaults to 'default'."""
    priority: int = Field(ge=0, le=4)
    """The priority level of the DNS server, ranging from 0 to 4. Lower values indicate a higher priority, with 0 being the highest and 4 the lowest."""

    def __str__(self) -> str:
        """Return a human-readable string representation of the DnsServer for reporting.

        Examples
        --------
        Server 10.0.0.1 (VRF: default, Priority: 1)
        """
        return f"Server {self.server_address} (VRF: {self.vrf}, Priority: {self.priority})"
