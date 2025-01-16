# Copyright (c) 2023-2025 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Tests for anta.input_models.snmp.py."""

# pylint: disable=C0302
from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
from pydantic import ValidationError

from anta.tests.snmp import VerifySnmpGroup, VerifySnmpUser

if TYPE_CHECKING:
    from anta.input_models.snmp import SnmpGroup, SnmpUser


class TestVerifySnmpUserInput:
    """Test anta.tests.snmp.VerifySnmpUser.Input."""

    @pytest.mark.parametrize(
        ("snmp_users"),
        [
            pytest.param([{"username": "test", "group_name": "abc", "version": "v1", "auth_type": None, "priv_type": None}], id="valid-v1"),
            pytest.param([{"username": "test", "group_name": "abc", "version": "v2c", "auth_type": None, "priv_type": None}], id="valid-v2c"),
            pytest.param([{"username": "test", "group_name": "abc", "version": "v3", "auth_type": "SHA", "priv_type": "AES-128"}], id="valid-v3"),
        ],
    )
    def test_valid(self, snmp_users: list[SnmpUser]) -> None:
        """Test VerifySnmpUser.Input valid inputs."""
        VerifySnmpUser.Input(snmp_users=snmp_users)

    @pytest.mark.parametrize(
        ("snmp_users"),
        [
            pytest.param([{"username": "test", "group_name": "abc", "version": "v3", "auth_type": None, "priv_type": None}], id="invalid-v3"),
        ],
    )
    def test_invalid(self, snmp_users: list[SnmpUser]) -> None:
        """Test VerifySnmpUser.Input invalid inputs."""
        with pytest.raises(ValidationError):
            VerifySnmpUser.Input(snmp_users=snmp_users)


class TestVerifySnmpGroupInput:
    """Test anta.tests.snmp.VerifySnmpGroup.Input."""

    @pytest.mark.parametrize(
        ("snmp_groups"),
        [
            pytest.param(
                [{"group_name": "abc", "version": "v1", "read_view": "group_read_1", "write_view": "group_write_1", "notify_view": "group_notify_1"}], id="valid-v1"
            ),
            pytest.param(
                [
                    {
                        "group_name": "abc",
                        "version": "v3",
                        "read_view": "group_read_1",
                        "write_view": "group_write_1",
                        "notify_view": "group_notify_1",
                        "authentication": "v3Auth",
                    }
                ],
                id="valid-v3",
            ),
        ],
    )
    def test_valid(self, snmp_groups: list[SnmpGroup]) -> None:
        """Test VerifySnmpGroup.Input valid inputs."""
        VerifySnmpGroup.Input(snmp_groups=snmp_groups)

    @pytest.mark.parametrize(
        ("snmp_groups"),
        [
            pytest.param(
                [
                    {
                        "group_name": "abc",
                        "version": "v3",
                        "read_view": "group_read_1",
                        "write_view": "group_write_1",
                        "notify_view": "group_notify_1",
                        "authentication": None,
                    }
                ],
                id="invalid-v3",
            ),
        ],
    )
    def test_invalid(self, snmp_groups: list[SnmpGroup]) -> None:
        """Test VerifySnmpGroup.Input invalid inputs."""
        with pytest.raises(ValidationError):
            VerifySnmpGroup.Input(snmp_groups=snmp_groups)
