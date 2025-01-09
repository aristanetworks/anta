# Copyright (c) 2023-2025 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Module containing input models for SNMP tests."""

from __future__ import annotations

from ipaddress import IPv4Address

from pydantic import BaseModel, ConfigDict

from anta.custom_types import Hostname


class SNMPHost(BaseModel):
    """Model for a SNMP Host."""

    model_config = ConfigDict(extra="forbid")
    hostname: IPv4Address | Hostname
    """IPv4 address of the SNMP notification host."""
    vrf: str = "default"
    """Optional VRF for SNMP Hosts. If not provided, it defaults to `default`."""

    def __str__(self) -> str:
        """Return a human-readable string representation of the Host for reporting.

        Examples
        --------
         - Host: 192.168.1.100  VRF: default
        """
        return f"Host: {self.hostname} VRF: {self.vrf}"
