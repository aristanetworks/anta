# Copyright (c) 2023 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""
test anta.device.py
"""

from __future__ import annotations

from typing import Any

import pytest

from anta.device import AsyncEOSDevice
from tests.lib.utils import generate_test_ids_list

INIT_DEVICE_DATA: list[dict[str, Any]] = [
    {
        "name": "no name, no port",
        "device": {
            "host": "42.42.42.42",
            "username": "anta",
            "password": "anta",
            "name": None,
            "enable": False,
            "enable_password": None,
            "port": None,
            "ssh_port": None,
            "tags": None,
            "timeout": None,
            "insecure": False,
            "proto": None,
        },
        "expected": {"name": "42.42.42.42"},
    },
    {
        "name": "no name, port",
        "device": {
            "host": "42.42.42.42",
            "username": "anta",
            "password": "anta",
            "name": None,
            "enable": False,
            "enable_password": None,
            "port": 666,
            "ssh_port": None,
            "tags": None,
            "timeout": None,
            "insecure": False,
            "proto": None,
        },
        "expected": {"name": "42.42.42.42:666"},
    },
    {
        "name": "name",
        "device": {
            "host": "42.42.42.42",
            "username": "anta",
            "password": "anta",
            "name": "test.anta.ninja",
            "enable": False,
            "enable_password": None,
            "port": None,
            "ssh_port": None,
            "tags": None,
            "timeout": None,
            "insecure": False,
            "proto": None,
        },
        "expected": {"name": "test.anta.ninja"},
    },
]


# TODO remove this pylint later
# pylint: disable=too-few-public-methods
class Test_AsyncEOSDevice:
    """
    Test for anta.device.AsyncEOSDevice
    """

    @pytest.mark.parametrize("device_data", INIT_DEVICE_DATA, ids=generate_test_ids_list(INIT_DEVICE_DATA))
    def test__init__(self, device_data: dict[str, Any]) -> None:
        """
        Checking name only for now
        """
        host = device_data["device"]["host"]
        username = device_data["device"]["username"]
        password = device_data["device"]["password"]
        kwargs = {k: v for k, v in device_data["device"].items() if v is not None and k not in ["host", "username", "password"]}

        device = AsyncEOSDevice(host, username, password, **kwargs)

        assert device.name == device_data["expected"]["name"]
