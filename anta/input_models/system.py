# Copyright (c) 2023-2025 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Module containing input models for system tests."""

from __future__ import annotations

from ipaddress import IPv4Address

from pydantic import BaseModel, ConfigDict

from anta.custom_types import Hostname, NTPStratumLevel


class NTPServer(BaseModel):
    """Model for a NTP server."""

    model_config = ConfigDict(extra="forbid")
    server_address: Hostname | IPv4Address
    """The NTP server address as an IPv4 address or hostname. The NTP server name defined in the running configuration
    of the device may change during DNS resolution, which is not handled in ANTA. Please provide the DNS-resolved server name.
    For example, 'ntp.example.com' in the configuration might resolve to 'ntp3.example.com' in the device output."""
    preferred: bool = False
    """Optional preferred for NTP server. If not provided, it defaults to `False`."""
    stratum: NTPStratumLevel
    """NTP stratum level (0 to 15) where 0 is the reference clock and 16 indicates unsynchronized.
    Values should be between 0 and 15 for valid synchronization and 16 represents an out-of-sync state."""

    def __str__(self) -> str:
        """Representation of the NTPServer model."""
        return f"NTP Server: {self.server_address} Preferred: {self.preferred} Stratum: {self.stratum}"


class NTPPool(BaseModel):
    """Model for a NTP server pool."""

    model_config = ConfigDict(extra="forbid")
    server_addresses: list[Hostname | IPv4Address]
    """The list of NTP server addresses as an IPv4 addresses or hostnames."""
    preferred_stratum_range: list[NTPStratumLevel]
    """Preferred NTP stratum range for the NTP server pool. If the expected stratum range is 1 to 3 then preferred_stratum_range should be `[1,3]`."""
