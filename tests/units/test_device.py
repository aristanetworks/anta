# Copyright (c) 2023-2024 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""test anta.device.py."""

from __future__ import annotations

import asyncio
from pathlib import Path
from typing import TYPE_CHECKING, Any
from unittest.mock import patch

import httpx
import pytest
from asyncssh import SSHClientConnection, SSHClientConnectionOptions
from rich import print as rprint

import aioeapi
from anta.device import AntaDevice, AsyncEOSDevice
from anta.models import AntaCommand
from tests.lib.fixture import COMMAND_OUTPUT
from tests.lib.utils import generate_test_ids_list

if TYPE_CHECKING:
    from _pytest.mark.structures import ParameterSet

INIT_DATA: list[dict[str, Any]] = [
    {
        "name": "no name, no port",
        "device": {
            "host": "42.42.42.42",
            "username": "anta",
            "password": "anta",
        },
        "expected": {"name": "42.42.42.42"},
    },
    {
        "name": "no name, port",
        "device": {
            "host": "42.42.42.42",
            "username": "anta",
            "password": "anta",
            "port": 666,
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
            "disable_cache": True,
        },
        "expected": {"name": "test.anta.ninja"},
    },
    {
        "name": "insecure",
        "device": {
            "host": "42.42.42.42",
            "username": "anta",
            "password": "anta",
            "name": "test.anta.ninja",
            "insecure": True,
        },
        "expected": {"name": "test.anta.ninja"},
    },
]
EQUALITY_DATA: list[dict[str, Any]] = [
    {
        "name": "equal",
        "device1": {
            "host": "42.42.42.42",
            "username": "anta",
            "password": "anta",
        },
        "device2": {
            "host": "42.42.42.42",
            "username": "anta",
            "password": "blah",
        },
        "expected": True,
    },
    {
        "name": "equals-name",
        "device1": {
            "host": "42.42.42.42",
            "username": "anta",
            "password": "anta",
            "name": "device1",
        },
        "device2": {
            "host": "42.42.42.42",
            "username": "plop",
            "password": "anta",
            "name": "device2",
        },
        "expected": True,
    },
    {
        "name": "not-equal-port",
        "device1": {
            "host": "42.42.42.42",
            "username": "anta",
            "password": "anta",
        },
        "device2": {
            "host": "42.42.42.42",
            "username": "anta",
            "password": "anta",
            "port": 666,
        },
        "expected": False,
    },
    {
        "name": "not-equal-host",
        "device1": {
            "host": "42.42.42.41",
            "username": "anta",
            "password": "anta",
        },
        "device2": {
            "host": "42.42.42.42",
            "username": "anta",
            "password": "anta",
        },
        "expected": False,
    },
]
AIOEAPI_COLLECT_DATA: list[dict[str, Any]] = [
    {
        "name": "command",
        "device": {},
        "command": {
            "command": "show version",
            "patch_kwargs": {
                "return_value": [
                    {
                        "mfgName": "Arista",
                        "modelName": "DCS-7280CR3-32P4-F",
                        "hardwareRevision": "11.00",
                        "serialNumber": "JPE19500066",
                        "systemMacAddress": "fc:bd:67:3d:13:c5",
                        "hwMacAddress": "fc:bd:67:3d:13:c5",
                        "configMacAddress": "00:00:00:00:00:00",
                        "version": "4.31.1F-34361447.fraserrel (engineering build)",
                        "architecture": "x86_64",
                        "internalVersion": "4.31.1F-34361447.fraserrel",
                        "internalBuildId": "4940d112-a2fc-4970-8b5a-a16cd03fd08c",
                        "imageFormatVersion": "3.0",
                        "imageOptimization": "Default",
                        "bootupTimestamp": 1700729434.5892005,
                        "uptime": 20666.78,
                        "memTotal": 8099732,
                        "memFree": 4989568,
                        "isIntlVersion": False,
                    },
                ],
            },
        },
        "expected": {
            "output": {
                "mfgName": "Arista",
                "modelName": "DCS-7280CR3-32P4-F",
                "hardwareRevision": "11.00",
                "serialNumber": "JPE19500066",
                "systemMacAddress": "fc:bd:67:3d:13:c5",
                "hwMacAddress": "fc:bd:67:3d:13:c5",
                "configMacAddress": "00:00:00:00:00:00",
                "version": "4.31.1F-34361447.fraserrel (engineering build)",
                "architecture": "x86_64",
                "internalVersion": "4.31.1F-34361447.fraserrel",
                "internalBuildId": "4940d112-a2fc-4970-8b5a-a16cd03fd08c",
                "imageFormatVersion": "3.0",
                "imageOptimization": "Default",
                "bootupTimestamp": 1700729434.5892005,
                "uptime": 20666.78,
                "memTotal": 8099732,
                "memFree": 4989568,
                "isIntlVersion": False,
            },
            "errors": [],
        },
    },
    {
        "name": "enable",
        "device": {"enable": True},
        "command": {
            "command": "show version",
            "patch_kwargs": {
                "return_value": [
                    {},
                    {
                        "mfgName": "Arista",
                        "modelName": "DCS-7280CR3-32P4-F",
                        "hardwareRevision": "11.00",
                        "serialNumber": "JPE19500066",
                        "systemMacAddress": "fc:bd:67:3d:13:c5",
                        "hwMacAddress": "fc:bd:67:3d:13:c5",
                        "configMacAddress": "00:00:00:00:00:00",
                        "version": "4.31.1F-34361447.fraserrel (engineering build)",
                        "architecture": "x86_64",
                        "internalVersion": "4.31.1F-34361447.fraserrel",
                        "internalBuildId": "4940d112-a2fc-4970-8b5a-a16cd03fd08c",
                        "imageFormatVersion": "3.0",
                        "imageOptimization": "Default",
                        "bootupTimestamp": 1700729434.5892005,
                        "uptime": 20666.78,
                        "memTotal": 8099732,
                        "memFree": 4989568,
                        "isIntlVersion": False,
                    },
                ],
            },
        },
        "expected": {
            "output": {
                "mfgName": "Arista",
                "modelName": "DCS-7280CR3-32P4-F",
                "hardwareRevision": "11.00",
                "serialNumber": "JPE19500066",
                "systemMacAddress": "fc:bd:67:3d:13:c5",
                "hwMacAddress": "fc:bd:67:3d:13:c5",
                "configMacAddress": "00:00:00:00:00:00",
                "version": "4.31.1F-34361447.fraserrel (engineering build)",
                "architecture": "x86_64",
                "internalVersion": "4.31.1F-34361447.fraserrel",
                "internalBuildId": "4940d112-a2fc-4970-8b5a-a16cd03fd08c",
                "imageFormatVersion": "3.0",
                "imageOptimization": "Default",
                "bootupTimestamp": 1700729434.5892005,
                "uptime": 20666.78,
                "memTotal": 8099732,
                "memFree": 4989568,
                "isIntlVersion": False,
            },
            "errors": [],
        },
    },
    {
        "name": "enable password",
        "device": {"enable": True, "enable_password": "anta"},
        "command": {
            "command": "show version",
            "patch_kwargs": {
                "return_value": [
                    {},
                    {
                        "mfgName": "Arista",
                        "modelName": "DCS-7280CR3-32P4-F",
                        "hardwareRevision": "11.00",
                        "serialNumber": "JPE19500066",
                        "systemMacAddress": "fc:bd:67:3d:13:c5",
                        "hwMacAddress": "fc:bd:67:3d:13:c5",
                        "configMacAddress": "00:00:00:00:00:00",
                        "version": "4.31.1F-34361447.fraserrel (engineering build)",
                        "architecture": "x86_64",
                        "internalVersion": "4.31.1F-34361447.fraserrel",
                        "internalBuildId": "4940d112-a2fc-4970-8b5a-a16cd03fd08c",
                        "imageFormatVersion": "3.0",
                        "imageOptimization": "Default",
                        "bootupTimestamp": 1700729434.5892005,
                        "uptime": 20666.78,
                        "memTotal": 8099732,
                        "memFree": 4989568,
                        "isIntlVersion": False,
                    },
                ],
            },
        },
        "expected": {
            "output": {
                "mfgName": "Arista",
                "modelName": "DCS-7280CR3-32P4-F",
                "hardwareRevision": "11.00",
                "serialNumber": "JPE19500066",
                "systemMacAddress": "fc:bd:67:3d:13:c5",
                "hwMacAddress": "fc:bd:67:3d:13:c5",
                "configMacAddress": "00:00:00:00:00:00",
                "version": "4.31.1F-34361447.fraserrel (engineering build)",
                "architecture": "x86_64",
                "internalVersion": "4.31.1F-34361447.fraserrel",
                "internalBuildId": "4940d112-a2fc-4970-8b5a-a16cd03fd08c",
                "imageFormatVersion": "3.0",
                "imageOptimization": "Default",
                "bootupTimestamp": 1700729434.5892005,
                "uptime": 20666.78,
                "memTotal": 8099732,
                "memFree": 4989568,
                "isIntlVersion": False,
            },
            "errors": [],
        },
    },
    {
        "name": "revision",
        "device": {},
        "command": {
            "command": "show version",
            "revision": 3,
            "patch_kwargs": {
                "return_value": [
                    {},
                    {
                        "mfgName": "Arista",
                        "modelName": "DCS-7280CR3-32P4-F",
                        "hardwareRevision": "11.00",
                        "serialNumber": "JPE19500066",
                        "systemMacAddress": "fc:bd:67:3d:13:c5",
                        "hwMacAddress": "fc:bd:67:3d:13:c5",
                        "configMacAddress": "00:00:00:00:00:00",
                        "version": "4.31.1F-34361447.fraserrel (engineering build)",
                        "architecture": "x86_64",
                        "internalVersion": "4.31.1F-34361447.fraserrel",
                        "internalBuildId": "4940d112-a2fc-4970-8b5a-a16cd03fd08c",
                        "imageFormatVersion": "3.0",
                        "imageOptimization": "Default",
                        "bootupTimestamp": 1700729434.5892005,
                        "uptime": 20666.78,
                        "memTotal": 8099732,
                        "memFree": 4989568,
                        "isIntlVersion": False,
                    },
                ],
            },
        },
        "expected": {
            "output": {
                "mfgName": "Arista",
                "modelName": "DCS-7280CR3-32P4-F",
                "hardwareRevision": "11.00",
                "serialNumber": "JPE19500066",
                "systemMacAddress": "fc:bd:67:3d:13:c5",
                "hwMacAddress": "fc:bd:67:3d:13:c5",
                "configMacAddress": "00:00:00:00:00:00",
                "version": "4.31.1F-34361447.fraserrel (engineering build)",
                "architecture": "x86_64",
                "internalVersion": "4.31.1F-34361447.fraserrel",
                "internalBuildId": "4940d112-a2fc-4970-8b5a-a16cd03fd08c",
                "imageFormatVersion": "3.0",
                "imageOptimization": "Default",
                "bootupTimestamp": 1700729434.5892005,
                "uptime": 20666.78,
                "memTotal": 8099732,
                "memFree": 4989568,
                "isIntlVersion": False,
            },
            "errors": [],
        },
    },
    {
        "name": "aioeapi.EapiCommandError",
        "device": {},
        "command": {
            "command": "show version",
            "patch_kwargs": {
                "side_effect": aioeapi.EapiCommandError(
                    passed=[],
                    failed="show version",
                    errors=["Authorization denied for command 'show version'"],
                    errmsg="Invalid command",
                    not_exec=[],
                ),
            },
        },
        "expected": {"output": None, "errors": ["Authorization denied for command 'show version'"]},
    },
    {
        "name": "httpx.HTTPError",
        "device": {},
        "command": {
            "command": "show version",
            "patch_kwargs": {"side_effect": httpx.HTTPError(message="404")},
        },
        "expected": {"output": None, "errors": ["HTTPError: 404"]},
    },
    {
        "name": "httpx.ConnectError",
        "device": {},
        "command": {
            "command": "show version",
            "patch_kwargs": {"side_effect": httpx.ConnectError(message="Cannot open port")},
        },
        "expected": {"output": None, "errors": ["ConnectError: Cannot open port"]},
    },
]
AIOEAPI_COPY_DATA: list[dict[str, Any]] = [
    {
        "name": "from",
        "device": {},
        "copy": {
            "sources": [Path("/mnt/flash"), Path("/var/log/agents")],
            "destination": Path(),
            "direction": "from",
        },
    },
    {
        "name": "to",
        "device": {},
        "copy": {
            "sources": [Path("/mnt/flash"), Path("/var/log/agents")],
            "destination": Path(),
            "direction": "to",
        },
    },
    {
        "name": "wrong",
        "device": {},
        "copy": {
            "sources": [Path("/mnt/flash"), Path("/var/log/agents")],
            "destination": Path(),
            "direction": "wrong",
        },
    },
]
REFRESH_DATA: list[dict[str, Any]] = [
    {
        "name": "established",
        "device": {},
        "patch_kwargs": (
            {"return_value": True},
            {
                "return_value": [
                    {
                        "mfgName": "Arista",
                        "modelName": "DCS-7280CR3-32P4-F",
                        "hardwareRevision": "11.00",
                        "serialNumber": "JPE19500066",
                        "systemMacAddress": "fc:bd:67:3d:13:c5",
                        "hwMacAddress": "fc:bd:67:3d:13:c5",
                        "configMacAddress": "00:00:00:00:00:00",
                        "version": "4.31.1F-34361447.fraserrel (engineering build)",
                        "architecture": "x86_64",
                        "internalVersion": "4.31.1F-34361447.fraserrel",
                        "internalBuildId": "4940d112-a2fc-4970-8b5a-a16cd03fd08c",
                        "imageFormatVersion": "3.0",
                        "imageOptimization": "Default",
                        "bootupTimestamp": 1700729434.5892005,
                        "uptime": 20666.78,
                        "memTotal": 8099732,
                        "memFree": 4989568,
                        "isIntlVersion": False,
                    }
                ],
            },
        ),
        "expected": {"is_online": True, "established": True, "hw_model": "DCS-7280CR3-32P4-F"},
    },
    {
        "name": "is not online",
        "device": {},
        "patch_kwargs": (
            {"return_value": False},
            {
                "return_value": {
                    "mfgName": "Arista",
                    "modelName": "DCS-7280CR3-32P4-F",
                    "hardwareRevision": "11.00",
                    "serialNumber": "JPE19500066",
                    "systemMacAddress": "fc:bd:67:3d:13:c5",
                    "hwMacAddress": "fc:bd:67:3d:13:c5",
                    "configMacAddress": "00:00:00:00:00:00",
                    "version": "4.31.1F-34361447.fraserrel (engineering build)",
                    "architecture": "x86_64",
                    "internalVersion": "4.31.1F-34361447.fraserrel",
                    "internalBuildId": "4940d112-a2fc-4970-8b5a-a16cd03fd08c",
                    "imageFormatVersion": "3.0",
                    "imageOptimization": "Default",
                    "bootupTimestamp": 1700729434.5892005,
                    "uptime": 20666.78,
                    "memTotal": 8099732,
                    "memFree": 4989568,
                    "isIntlVersion": False,
                },
            },
        ),
        "expected": {"is_online": False, "established": False, "hw_model": None},
    },
    {
        "name": "cannot parse command",
        "device": {},
        "patch_kwargs": (
            {"return_value": True},
            {
                "return_value": [
                    {
                        "mfgName": "Arista",
                        "hardwareRevision": "11.00",
                        "serialNumber": "JPE19500066",
                        "systemMacAddress": "fc:bd:67:3d:13:c5",
                        "hwMacAddress": "fc:bd:67:3d:13:c5",
                        "configMacAddress": "00:00:00:00:00:00",
                        "version": "4.31.1F-34361447.fraserrel (engineering build)",
                        "architecture": "x86_64",
                        "internalVersion": "4.31.1F-34361447.fraserrel",
                        "internalBuildId": "4940d112-a2fc-4970-8b5a-a16cd03fd08c",
                        "imageFormatVersion": "3.0",
                        "imageOptimization": "Default",
                        "bootupTimestamp": 1700729434.5892005,
                        "uptime": 20666.78,
                        "memTotal": 8099732,
                        "memFree": 4989568,
                        "isIntlVersion": False,
                    }
                ],
            },
        ),
        "expected": {"is_online": True, "established": False, "hw_model": None},
    },
    {
        "name": "aioeapi.EapiCommandError",
        "device": {},
        "patch_kwargs": (
            {"return_value": True},
            {
                "side_effect": aioeapi.EapiCommandError(
                    passed=[],
                    failed="show version",
                    errors=["Authorization denied for command 'show version'"],
                    errmsg="Invalid command",
                    not_exec=[],
                ),
            },
        ),
        "expected": {"is_online": True, "established": False, "hw_model": None},
    },
    {
        "name": "httpx.HTTPError",
        "device": {},
        "patch_kwargs": (
            {"return_value": True},
            {"side_effect": httpx.HTTPError(message="404")},
        ),
        "expected": {"is_online": True, "established": False, "hw_model": None},
    },
    {
        "name": "httpx.ConnectError",
        "device": {},
        "patch_kwargs": (
            {"return_value": True},
            {"side_effect": httpx.ConnectError(message="Cannot open port")},
        ),
        "expected": {"is_online": True, "established": False, "hw_model": None},
    },
]
COLLECT_DATA: list[dict[str, Any]] = [
    {
        "name": "device cache enabled, command cache enabled, no cache hit",
        "device": {"disable_cache": False},
        "command": {
            "command": "show version",
            "use_cache": True,
        },
        "expected": {"cache_hit": False},
    },
    {
        "name": "device cache enabled, command cache enabled, cache hit",
        "device": {"disable_cache": False},
        "command": {
            "command": "show version",
            "use_cache": True,
        },
        "expected": {"cache_hit": True},
    },
    {
        "name": "device cache disabled, command cache enabled",
        "device": {"disable_cache": True},
        "command": {
            "command": "show version",
            "use_cache": True,
        },
        "expected": {},
    },
    {
        "name": "device cache enabled, command cache disabled, cache has command",
        "device": {"disable_cache": False},
        "command": {
            "command": "show version",
            "use_cache": False,
        },
        "expected": {"cache_hit": True},
    },
    {
        "name": "device cache enabled, command cache disabled, cache does not have data",
        "device": {
            "disable_cache": False,
        },
        "command": {
            "command": "show version",
            "use_cache": False,
        },
        "expected": {"cache_hit": False},
    },
    {
        "name": "device cache disabled, command cache disabled",
        "device": {
            "disable_cache": True,
        },
        "command": {
            "command": "show version",
            "use_cache": False,
        },
        "expected": {},
    },
]
CACHE_STATS_DATA: list[ParameterSet] = [
    pytest.param({"disable_cache": False}, {"total_commands_sent": 0, "cache_hits": 0, "cache_hit_ratio": "0.00%"}, id="with_cache"),
    pytest.param({"disable_cache": True}, None, id="without_cache"),
]


class TestAntaDevice:
    """Test for anta.device.AntaDevice Abstract class."""

    @pytest.mark.asyncio()
    @pytest.mark.parametrize(
        ("device", "command_data", "expected_data"),
        ((d["device"], d["command"], d["expected"]) for d in COLLECT_DATA),
        indirect=["device"],
        ids=generate_test_ids_list(COLLECT_DATA),
    )
    async def test_collect(self, device: AntaDevice, command_data: dict[str, Any], expected_data: dict[str, Any]) -> None:
        """Test AntaDevice.collect behavior."""
        command = AntaCommand(command=command_data["command"], use_cache=command_data["use_cache"])

        # Dummy output for cache hit
        cached_output = "cached_value"

        if device.cache is not None and expected_data["cache_hit"] is True:
            await device.cache.set(command.uid, cached_output)

        await device.collect(command)

        if device.cache is not None:  # device_cache is enabled
            current_cached_data = await device.cache.get(command.uid)
            if command.use_cache is True:  # command is allowed to use cache
                if expected_data["cache_hit"] is True:
                    assert command.output == cached_output
                    assert current_cached_data == cached_output
                    assert device.cache.hit_miss_ratio["hits"] == 2
                else:
                    assert command.output == COMMAND_OUTPUT
                    assert current_cached_data == COMMAND_OUTPUT
                    assert device.cache.hit_miss_ratio["hits"] == 1
            else:  # command is not allowed to use cache
                device._collect.assert_called_once_with(command=command)  # type: ignore[attr-defined]  # pylint: disable=protected-access
                assert command.output == COMMAND_OUTPUT
                if expected_data["cache_hit"] is True:
                    assert current_cached_data == cached_output
                else:
                    assert current_cached_data is None
        else:  # device is disabled
            assert device.cache is None
            device._collect.assert_called_once_with(command=command)  # type: ignore[attr-defined]  # pylint: disable=protected-access

    @pytest.mark.parametrize(("device", "expected"), CACHE_STATS_DATA, indirect=["device"])
    def test_cache_statistics(self, device: AntaDevice, expected: dict[str, Any] | None) -> None:
        """Verify that when cache statistics attribute does not exist.

        TODO add a test where cache has some value.
        """
        assert device.cache_statistics == expected


class TestAsyncEOSDevice:
    """Test for anta.device.AsyncEOSDevice."""

    @pytest.mark.parametrize("data", INIT_DATA, ids=generate_test_ids_list(INIT_DATA))
    def test__init__(self, data: dict[str, Any]) -> None:
        """Test the AsyncEOSDevice constructor."""
        device = AsyncEOSDevice(**data["device"])

        assert device.name == data["expected"]["name"]
        if data["device"].get("disable_cache") is True:
            assert device.cache is None
            assert device.cache_locks is None
        else:  # False or None
            assert device.cache is not None
            assert device.cache_locks is not None
        hash(device)

        with patch("anta.device.__DEBUG__", new=True):
            rprint(device)

    @pytest.mark.parametrize("data", EQUALITY_DATA, ids=generate_test_ids_list(EQUALITY_DATA))
    def test__eq(self, data: dict[str, Any]) -> None:
        """Test the AsyncEOSDevice equality."""
        device1 = AsyncEOSDevice(**data["device1"])
        device2 = AsyncEOSDevice(**data["device2"])
        if data["expected"]:
            assert device1 == device2
        else:
            assert device1 != device2

    @pytest.mark.asyncio()
    @pytest.mark.parametrize(
        ("async_device", "patch_kwargs", "expected"),
        ((d["device"], d["patch_kwargs"], d["expected"]) for d in REFRESH_DATA),
        ids=generate_test_ids_list(REFRESH_DATA),
        indirect=["async_device"],
    )
    async def test_refresh(self, async_device: AsyncEOSDevice, patch_kwargs: list[dict[str, Any]], expected: dict[str, Any]) -> None:
        # pylint: disable=protected-access
        """Test AsyncEOSDevice.refresh()."""
        with patch.object(async_device._session, "check_connection", **patch_kwargs[0]), patch.object(async_device._session, "cli", **patch_kwargs[1]):
            await async_device.refresh()
            async_device._session.check_connection.assert_called_once()  # type: ignore[attr-defined] # aioeapi.Device.check_connection is patched
            if expected["is_online"]:
                async_device._session.cli.assert_called_once()  # type: ignore[attr-defined] # aioeapi.Device.cli is patched
            assert async_device.is_online == expected["is_online"]
            assert async_device.established == expected["established"]
            assert async_device.hw_model == expected["hw_model"]

    @pytest.mark.asyncio()
    @pytest.mark.parametrize(
        ("async_device", "command", "expected"),
        ((d["device"], d["command"], d["expected"]) for d in AIOEAPI_COLLECT_DATA),
        ids=generate_test_ids_list(AIOEAPI_COLLECT_DATA),
        indirect=["async_device"],
    )
    async def test__collect(self, async_device: AsyncEOSDevice, command: dict[str, Any], expected: dict[str, Any]) -> None:
        # pylint: disable=protected-access
        """Test AsyncEOSDevice._collect()."""
        cmd = AntaCommand(command=command["command"], revision=command["revision"]) if "revision" in command else AntaCommand(command=command["command"])
        with patch.object(async_device._session, "cli", **command["patch_kwargs"]):
            await async_device.collect(cmd)
            commands: list[dict[str, Any]] = []
            if async_device.enable and async_device._enable_password is not None:
                commands.append(
                    {
                        "cmd": "enable",
                        "input": str(async_device._enable_password),
                    },
                )
            elif async_device.enable:
                # No password
                commands.append({"cmd": "enable"})
            if cmd.revision:
                commands.append({"cmd": cmd.command, "revision": cmd.revision})
            else:
                commands.append({"cmd": cmd.command})
            async_device._session.cli.assert_called_once_with(commands=commands, ofmt=cmd.ofmt, version=cmd.version)  # type: ignore[attr-defined] # aioeapi.Device.cli is patched # pylint: disable=line-too-long
            assert cmd.output == expected["output"]
            assert cmd.errors == expected["errors"]

    @pytest.mark.asyncio()
    @pytest.mark.parametrize(
        ("async_device", "copy"),
        ((d["device"], d["copy"]) for d in AIOEAPI_COPY_DATA),
        ids=generate_test_ids_list(AIOEAPI_COPY_DATA),
        indirect=["async_device"],
    )
    async def test_copy(self, async_device: AsyncEOSDevice, copy: dict[str, Any]) -> None:
        """Test AsyncEOSDevice.copy()."""
        conn = SSHClientConnection(asyncio.get_event_loop(), SSHClientConnectionOptions())
        with patch("asyncssh.connect") as connect_mock:
            connect_mock.return_value.__aenter__.return_value = conn
            with patch("asyncssh.scp") as scp_mock:
                await async_device.copy(copy["sources"], copy["destination"], copy["direction"])
                if copy["direction"] == "from":
                    src = [(conn, file) for file in copy["sources"]]
                    dst = copy["destination"]
                elif copy["direction"] == "to":
                    src = copy["sources"]
                    dst = conn, copy["destination"]
                else:
                    scp_mock.assert_not_awaited()
                    return
                scp_mock.assert_awaited_once_with(src, dst)
