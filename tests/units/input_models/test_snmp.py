# Copyright (c) 2023-2025 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Tests for anta.input_models.snmp.py."""

# pylint: disable=C0302
from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
from pydantic import ValidationError

from anta.tests.snmp import VerifySnmpNotificationHost

if TYPE_CHECKING:
    from anta.input_models.snmp import SnmpHost


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
