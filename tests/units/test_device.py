# Copyright (c) 2023 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""
test anta.device.py
"""

from __future__ import annotations

from typing import Any
from unittest.mock import patch

import pytest

from anta.aioeapi import EapiCommandError
from anta.device import AntaDevice, AsyncEOSDevice
from anta.models import AntaCommand
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
            "disable_cache": True,
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
        if device_data["device"].get("disable_cache") is True:
            assert device.cache is None
            assert device.cache_locks is None
        else:  # False or None
            assert device.cache is not None
            assert device.cache_locks is not None

    def test_supports(self) -> None:
        """
        Test if the supports() static method parses correctly the aioeapi.EapiCommandError exception
        """
        DATA: dict[str, Any] = {"host": "42.42.42.42", "username": "anta", "password": "anta"}
        kwargs: dict[str, Any] = {
            "name": "test.anta.ninja",
            "enable": False,
            "disable_cache": True,
            "insecure": False,
        }
        device = AsyncEOSDevice(DATA["host"], DATA["username"], DATA["password"], **kwargs)
        command = AntaCommand(
            command="show hardware counter drop",
            failed=EapiCommandError(
                passed=[],
                failed="show hardware counter drop",
                errors=["Unavailable command (not supported on this hardware platform) (at token 2: 'counter')"],
                errmsg="CLI command 1 of 1 'show hardware counter drop' failed: invalid command",
                not_exec=[],
            ),
        )
        assert device.supports(command) is False
        command = AntaCommand(command="show hardware counter drop")
        assert device.supports(command) is True


COLLECT_ANTADEVICE_DATA: list[dict[str, Any]] = [
    {
        "name": "device cache enabled, command cache enabled, no cache hit",
        "device": {
            "name": "42.42.42.42",
        },
        "command": {
            "command": "show version",
            "use_cache": True,
        },
        "cache_hit": False,
    },
    {
        "name": "device cache enabled, command cache enabled, cache hit",
        "device": {
            "name": "42.42.42.42",
        },
        "command": {
            "command": "show version",
            "use_cache": True,
        },
        "cache_hit": True,
    },
    {
        "name": "device cache disabled, command cache enabled",
        "device": {
            "name": "42.42.42.42",
            "disable_cache": True,
        },
        "command": {
            "command": "show version",
            "use_cache": True,
        },
        "cache_hit": "unused",
    },
    {
        "name": "device cache enabled, command cache disabled, cache has command",
        "device": {
            "name": "42.42.42.42",
            "disable_cache": False,
        },
        "command": {
            "command": "show version",
            "use_cache": False,
        },
        "cache_hit": True,
    },
    {
        "name": "device cache enabled, command cache disabled, cache does not have data",
        "device": {
            "name": "42.42.42.42",
            "disable_cache": False,
        },
        "command": {
            "command": "show version",
            "use_cache": False,
        },
        "cache_hit": False,
    },
    {
        "name": "device cache disabled, command cache disabled",
        "device": {
            "name": "42.42.42.42",
            "disable_cache": True,
        },
        "command": {
            "command": "show version",
            "use_cache": False,
        },
        "cache_hit": "unused",
    },
]


class TestAntaDevice:
    """
    Test for anta.device.AntaDevice Abstract class

    Leveraging:
        @patch("anta.device.AntaDevice.__abstractmethods__", set())
    to be able to instantiate the Abstract Class
    """

    # pylint: disable=abstract-class-instantiated

    @patch("anta.device.AntaDevice.__abstractmethods__", set())
    @pytest.mark.asyncio
    @pytest.mark.parametrize("device_data", COLLECT_ANTADEVICE_DATA, ids=generate_test_ids_list(COLLECT_ANTADEVICE_DATA))
    async def test_collect(self, device_data: dict[str, Any]) -> None:
        """
        Test AntaDevice.collect behavior
        """
        command = AntaCommand(command=device_data["command"]["command"], use_cache=device_data["command"]["use_cache"])
        device = AntaDevice(name=device_data["device"]["name"], disable_cache=device_data["device"].get("disable_cache"))  # type: ignore[abstract]

        # Dummy output for cache hit
        cached_output = "cached_value"
        retrieved_output = "retrieved"

        if device.cache is not None and device_data["cache_hit"] is True:
            await device.cache.set(command.uid, cached_output)  # pylint: disable=no-member

        def _patched__collect(command: AntaCommand) -> None:
            command.output = "retrieved"

        with patch("anta.device.AntaDevice._collect", side_effect=_patched__collect) as patched__collect:
            await device.collect(command)

        if device.cache is not None:  # device_cache is enabled
            current_cached_data = await device.cache.get(command.uid)  # pylint: disable=no-member
            if command.use_cache is True:  # command is allowed to use cache
                if device_data["cache_hit"] is True:
                    assert command.output == cached_output
                    assert current_cached_data == cached_output
                    assert device.cache.hit_miss_ratio["hits"] == 2  # pylint: disable=no-member
                else:
                    assert command.output == retrieved_output
                    assert current_cached_data == retrieved_output
                    assert device.cache.hit_miss_ratio["hits"] == 1  # pylint: disable=no-member
            else:  # command is not allowed to use cache
                patched__collect.assert_called_once_with(command=command)
                assert command.output == retrieved_output
                if device_data["cache_hit"] is True:
                    assert current_cached_data == cached_output
                else:
                    assert current_cached_data is None
        else:  # device is disabled
            assert device.cache is None
            patched__collect.assert_called_once_with(command=command)

    @patch("anta.device.AntaDevice.__abstractmethods__", set())
    @pytest.mark.asyncio
    async def test_cache_statistics(self) -> None:
        """
        Verify that when cache statistics attribute does not exist
        TODO add a test where cache has some value
        """
        device = AntaDevice(name="with_cache", disable_cache=False)  # type: ignore[abstract]
        assert device.cache_statistics == {"total_commands_sent": 0, "cache_hits": 0, "cache_hit_ratio": "0.00%"}

        device = AntaDevice(name="without_cache", disable_cache=True)  # type: ignore[abstract]
        assert device.cache_statistics is None
