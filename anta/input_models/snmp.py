# Copyright (c) 2023-2025 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Module containing input models for SNMP tests."""

from __future__ import annotations

from ipaddress import IPv4Address

from pydantic import BaseModel, ConfigDict

from anta.custom_types import Hostname, Interface, SnmpEncryptionAlgorithm, SnmpHashingAlgorithm, SnmpVersion


class SnmpHost(BaseModel):
    """Model for a SNMP host."""

    model_config = ConfigDict(extra="forbid")
    hostname: IPv4Address | Hostname
    """IPv4 address or hostname of the SNMP notification host."""
    vrf: str = "default"
    """Optional VRF for SNMP hosts. If not provided, it defaults to `default`."""

    def __str__(self) -> str:
        """Return a human-readable string representation of the SnmpHost for reporting.

        Examples
        --------
         - Host: 192.168.1.100  VRF: default
        """
        return f"Host: {self.hostname} VRF: {self.vrf}"


class SnmpUser(BaseModel):
    """Model for a SNMP User."""

    model_config = ConfigDict(extra="forbid")
    username: str
    """SNMP user name."""
    group_name: str
    """SNMP group for the user."""
    version: SnmpVersion
    """SNMP protocol version."""
    auth_type: SnmpHashingAlgorithm | None = None
    """User authentication algorithm. Can be provided in the `VerifySnmpUser` test."""
    priv_type: SnmpEncryptionAlgorithm | None = None
    """User privacy algorithm. Can be provided in the `VerifySnmpUser` test."""

    def __str__(self) -> str:
        """Return a human-readable string representation of the SnmpUser for reporting.

        Examples
        --------
        - User: Test Group: Test_Group Version: v2c
        """
        return f"User: {self.username} Group: {self.group_name} Version: {self.version}"


class SnmpSourceInterface(BaseModel):
    """Model for a SNMP source-interface."""

    interface: Interface
    """Source-interface to use as source IP address of log messages."""
    vrf: str = "default"
    """The VRF name to verify the SNMP agent in. Defaults to `default`."""

    def __str__(self) -> str:
        """Return a human-readable string representation of the SnmpSourceInterface for reporting.

        Examples
        --------
        - VRF: default, Source Interface: Ethernet1
        """
        return f"VRF: {self.vrf}, Source Interface: {self.interface}"
