# Copyright (c) 2023-2025 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Tests for anta.input_models.snmp.py."""

# pylint: disable=C0302
from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
from pydantic import ValidationError

from anta.tests.snmp import VerifySnmpNotificationHost, VerifySnmpUser

if TYPE_CHECKING:
    from anta.input_models.snmp import SnmpHost, SnmpUser


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


class TestSnmpHost:
    """Test anta.input_models.snmp.SnmpHost."""

    @pytest.mark.parametrize(
        ("notification_hosts"),
        [
            pytest.param(
                [
                    {
                        "hostname": "192.168.1.100",
                        "vrf": "test",
                        "notification_type": "trap",
                        "version": "v1",
                        "udp_port": 162,
                        "community_string": "public",
                        "user": None,
                    }
                ],
                id="valid-v1",
            ),
            pytest.param(
                [
                    {
                        "hostname": "192.168.1.100",
                        "vrf": "test",
                        "notification_type": "trap",
                        "version": "v2c",
                        "udp_port": 162,
                        "community_string": "public",
                        "user": None,
                    }
                ],
                id="valid-v2c",
            ),
            pytest.param(
                [
                    {
                        "hostname": "192.168.1.100",
                        "vrf": "test",
                        "notification_type": "trap",
                        "version": "v3",
                        "udp_port": 162,
                        "community_string": None,
                        "user": "public",
                    }
                ],
                id="valid-v3",
            ),
        ],
    )
    def test_valid(self, notification_hosts: list[SnmpHost]) -> None:
        """Test VerifySnmpNotificationHost.Input valid inputs."""
        VerifySnmpNotificationHost.Input(notification_hosts=notification_hosts)

    @pytest.mark.parametrize(
        ("notification_hosts"),
        [
            pytest.param(
                [
                    {
                        "hostname": "192.168.1.100",
                        "vrf": "test",
                        "notification_type": "trap",
                        "version": None,
                        "udp_port": 162,
                        "community_string": None,
                        "user": None,
                    }
                ],
                id="invalid-version",
            ),
            pytest.param(
                [
                    {
                        "hostname": "192.168.1.100",
                        "vrf": "test",
                        "notification_type": "trap",
                        "version": "v1",
                        "udp_port": 162,
                        "community_string": None,
                        "user": None,
                    }
                ],
                id="invalid-community-string-version-v1",
            ),
            pytest.param(
                [
                    {
                        "hostname": "192.168.1.100",
                        "vrf": "test",
                        "notification_type": "trap",
                        "version": "v2c",
                        "udp_port": 162,
                        "community_string": None,
                        "user": None,
                    }
                ],
                id="invalid-community-string-version-v2c",
            ),
            pytest.param(
                [
                    {
                        "hostname": "192.168.1.100",
                        "vrf": "test",
                        "notification_type": "trap",
                        "version": "v3",
                        "udp_port": 162,
                        "community_string": None,
                        "user": None,
                    }
                ],
                id="invalid-user-version-v3",
            ),
        ],
    )
    def test_invalid(self, notification_hosts: list[SnmpHost]) -> None:
        """Test VerifySnmpNotificationHost.Input invalid inputs."""
        with pytest.raises(ValidationError):
            VerifySnmpNotificationHost.Input(notification_hosts=notification_hosts)
