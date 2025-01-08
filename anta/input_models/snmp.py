# Copyright (c) 2023-2025 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Module containing input models for SNMP tests."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict

from anta.custom_types import HashingAlgorithm, SnmpEncryptionAlgorithm, SnmpVersion


class SnmpUser(BaseModel):
    """Model for a SNMP User."""

    model_config = ConfigDict(extra="forbid")
    username: str
    """SNMP user name."""
    group_name: str | None = None
    """SNMP group for the user. Required field in the `VerifySnmpUser` test."""
    version: SnmpVersion | None = None
    """SNMP protocol version. Required field in the `VerifySnmpUser` test."""
    auth_type: HashingAlgorithm | None = None
    """User authentication algorithm. Can be provided in the `VerifySnmpUser` test."""
    priv_type: SnmpEncryptionAlgorithm | None = None
    """User privacy algorithm. Can be provided in the `VerifySnmpUser` test."""

    def __str__(self) -> str:
        """Return a human-readable string representation of the SnmpUser for reporting.

        Examples
        --------
        - User: Test
        - User: Test Group: Test_Group
        - User: Test Group: Test_Group Version: v2c
        """
        base_string = f"User: {self.username}"
        if self.group_name:
            base_string += f" Group: {self.group_name}"
        if self.version:
            base_string += f" Version: {self.version}"
        return base_string
