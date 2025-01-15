# Copyright (c) 2023-2025 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Module containing input models for SNMP tests."""

from __future__ import annotations

from ipaddress import IPv4Address
from typing import Literal

from pydantic import BaseModel, ConfigDict

from anta.custom_types import Hostname, Port, SnmpEncryptionAlgorithm, SnmpHashingAlgorithm, SnmpVersion


class SnmpHost(BaseModel):
    """Model for a SNMP host."""

    model_config = ConfigDict(extra="forbid")
    hostname: IPv4Address | Hostname
    """IPv4 address or Hostname of the SNMP notification host."""
    vrf: str = "default"
    """Optional VRF for SNMP Hosts. If not provided, it defaults to `default`."""
    notification_type: Literal["trap", "inform"] = "trap"
    """Type of SNMP notification (trap or inform), it defaults to trap."""
    version: SnmpVersion | None = None
    """SNMP protocol version. Required field in the `VerifySnmpNotificationHost` test."""
    udp_port: Port | int = 162
    """UDP port for SNMP. If not provided then defaults to 162."""
    community_string: str | None = None
    """Optional SNMP community string for authentication,required for SNMP version is v1 or v2c. Can be provided in the `VerifySnmpNotificationHost` test."""
    user: str | None = None
    """Optional SNMP user for authentication, required for SNMP version v3. Can be provided in the `VerifySnmpNotificationHost` test."""

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
