# Copyright (c) 2023-2025 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Module containing input models for SNMP tests."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict

from anta.custom_types import EncryptionAlgorithms, HashingAlgorithms, SnmpVersion


class SnmpUser(BaseModel):
    """Model for a SNMP User."""

    model_config = ConfigDict(extra="forbid")
    username: str
    """SNMP user name."""
    group_name: str | None = None
    """SNMP group for the user. Required field in the `VerifySnmpUser` test."""
    security_model: SnmpVersion | None = None
    """SNMP protocol version. Required field in the `VerifySnmpUser` test."""
    authentication_type: HashingAlgorithms | None = None
    """User authentication settings. Can be provided in the `VerifySnmpUser` test."""
    encryption: EncryptionAlgorithms | None = None
    """User privacy settings. Can be provided in the `VerifySnmpUser` test."""

    def __str__(self) -> str:
        """Return a human-readable string representation of the SnmpUser for reporting.

        Examples
        --------
        User: Test Group: Test_Group Version: v2c
        """
        return f"User: {self.username} Version: {self.security_model}"
