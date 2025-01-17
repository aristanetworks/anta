# Copyright (c) 2023-2025 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Module containing input models for SNMP tests."""

from __future__ import annotations

from ipaddress import IPv4Address
from typing import Literal

from pydantic import BaseModel, ConfigDict

from anta.custom_types import Hostname, SnmpEncryptionAlgorithm, SnmpHashingAlgorithm, SnmpVersion


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


class SnmpGroup(BaseModel):
    """Model for a SNMP group."""

    group_name: str
    """SNMP group for the user."""
    version: SnmpVersion
    """SNMP protocol version."""
    read_view: str | None = None
    """Optional field, View to restrict read access."""
    write_view: str | None = None
    """Optional field, View to restrict write access."""
    notify_view: str | None = None
    """Optional field, View to restrict notifications."""
    authentication: Literal["v3Auth", "v3Priv", "v3NoAuth"] | None = None
    """Advanced authentication in v3 SNMP version. Defaults to None.
    - v3Auth: Group using authentication but not privacy
    - v3Priv: Group using both authentication and privacy
    - v3NoAuth: Group using neither authentication nor privacy
    """

    def __str__(self) -> str:
        """Return a human-readable string representation of the SnmpGroup for reporting.

        Examples
        --------
        - Group: Test_Group Version: v2c
        """
        return f"Group: {self.group_name}, Version: {self.version}"
