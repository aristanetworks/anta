# Copyright (c) 2023-2025 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Tests for anta.input_models.snmp.py."""

# pylint: disable=C0302
from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
from pydantic import ValidationError

from anta.tests.snmp import VerifySnmpUser

if TYPE_CHECKING:
    from anta.input_models.snmp import SnmpUser


class TestVerifySnmpUserInput:
    """Test anta.tests.snmp.VerifySnmpUser.Input."""

    @pytest.mark.parametrize(
        ("snmp_users"),
        [
            pytest.param([{"username": "test", "group_name": "abc", "security_model": "v1", "authentication_type": None, "encryption": None}], id="valid-v1"),
            pytest.param([{"username": "test", "group_name": "abc", "security_model": "v2c", "authentication_type": None, "encryption": None}], id="valid-v2c"),
            pytest.param([{"username": "test", "group_name": "abc", "security_model": "v3", "authentication_type": "SHA", "encryption": "AES-128"}], id="valid-v3"),
        ],
    )
    def test_valid(self, snmp_users: list[SnmpUser]) -> None:
        """Test VerifySnmpUser.Input valid inputs."""
        VerifySnmpUser.Input(snmp_users=snmp_users)

    @pytest.mark.parametrize(
        ("snmp_users"),
        [
            pytest.param([{"username": "test", "group_name": None, "security_model": "v1", "authentication_type": None, "encryption": None}], id="invalid-group"),
            pytest.param([{"username": "test", "group_name": "abc", "security_model": None, "authentication_type": None, "encryption": None}], id="invalid-version"),
            pytest.param([{"username": "test", "group_name": "abc", "security_model": "v3", "authentication_type": None, "encryption": None}], id="invalid-v3"),
        ],
    )
    def test_invalid(self, snmp_users: list[SnmpUser]) -> None:
        """Test VerifySnmpUser.Input invalid inputs."""
        with pytest.raises(ValidationError):
            VerifySnmpUser.Input(snmp_users=snmp_users)
