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
from rich import print as rprint

from anta.device import AntaDevice, AsyncEOSDevice
from anta.models import AntaCommand
from tests.lib.fixture import COMMAND_OUTPUT
from tests.lib.utils import generate_test_ids_list

DEVICE_DATA: list[dict[str, Any]] = [
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

DEVICE_EQ_DATA = [
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
COLLECT_ASYNCEOSDEVICE_DATA: list[dict[str, Any]] = [
    {
        "name": "command",
        "device": {},
        "command": {
            "command": "show version",
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
        "expected": {
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
    {
        "name": "enable",
        "device": {"enable": True},
        "command": {
            "command": "show version",
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
        "expected": {
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
]

REFRESH_DATA: list[dict[str, Any]] = [
    {
        "name": "established",
        "device": {},
        "return_value": (
            True,
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
        ),
        "expected": {"is_online": True, "established": True, "hw_model": "DCS-7280CR3-32P4-F"},
    },
    {
        "name": "is not online",
        "device": {},
        "return_value": (
            False,
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
        ),
        "expected": {"is_online": False, "established": False, "hw_model": None},
    },
    {
        "name": "cannot parse command",
        "device": {},
        "return_value": (
            True,
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
            },
        ),
        "expected": {"is_online": True, "established": False, "hw_model": None},
    },
]


class Test_AsyncEOSDevice:
    """
    Test for anta.device.AsyncEOSDevice
    """

    @pytest.mark.parametrize("data", DEVICE_DATA, ids=generate_test_ids_list(DEVICE_DATA))
    def test__init__(self, data: dict[str, Any]) -> None:
        """Test the AsyncEOSDevice constructor"""
        device = AsyncEOSDevice(**data["device"])

        assert device.name == data["expected"]["name"]
        if data["device"].get("disable_cache") is True:
            assert device.cache is None
            assert device.cache_locks is None
        else:  # False or None
            assert device.cache is not None
            assert device.cache_locks is not None
        hash(device)

        with patch("anta.__DEBUG__", new=True):  # TODO does not work
            rprint(device)

    @pytest.mark.parametrize("data", DEVICE_EQ_DATA, ids=generate_test_ids_list(DEVICE_EQ_DATA))
    def test__eq(self, data: dict[str, Any]) -> None:
        """Test the AsyncEOSDevice equality"""
        device1 = AsyncEOSDevice(**data["device1"])
        device2 = AsyncEOSDevice(**data["device2"])
        if data["expected"]:
            assert device1 == device2
        else:
            assert device1 != device2

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "async_device, return_value, expected",
        map(lambda d: (d["device"], d["return_value"], d["expected"]), REFRESH_DATA),
        ids=generate_test_ids_list(REFRESH_DATA),
        indirect=["async_device"],
    )
    async def test_refresh(self, async_device: AsyncEOSDevice, return_value: list[dict[str, Any]], expected: dict[str, Any]) -> None:
        # pylint: disable=protected-access
        """Test AsyncEOSDevice.refresh()"""
        with patch.object(async_device._session, "check_connection", return_value=return_value[0]):
            with patch.object(async_device._session, "cli", return_value=return_value[1]):
                await async_device.refresh()
                async_device._session.check_connection.assert_called_once()
                if expected["is_online"]:
                    async_device._session.cli.assert_called_once()
                assert async_device.is_online == expected["is_online"]
                assert async_device.established == expected["established"]
                assert async_device.hw_model == expected["hw_model"]

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "async_device, command, expected",
        map(lambda d: (d["device"], d["command"], d["expected"]), COLLECT_ASYNCEOSDEVICE_DATA),
        ids=generate_test_ids_list(COLLECT_ASYNCEOSDEVICE_DATA),
        indirect=["async_device"],
    )
    async def test__collect(self, async_device: AsyncEOSDevice, command: dict[str, Any], expected: dict[str, Any]) -> None:
        # pylint: disable=protected-access
        """Test AsyncEOSDevice._collect()"""
        cmd = AntaCommand(command=command["command"])
        with patch.object(async_device._session, "cli", return_value=command["return_value"]):
            await async_device.collect(cmd)
            async_device._session.cli.assert_called_once()
            assert cmd.output == expected


COLLECT_ANTADEVICE_DATA: list[dict[str, Any]] = [
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

CACHE_STATS_DATA = [
    pytest.param({"disable_cache": False}, {"total_commands_sent": 0, "cache_hits": 0, "cache_hit_ratio": "0.00%"}, id="with_cache"),
    pytest.param({"disable_cache": True}, None, id="without_cache"),
]


class TestAntaDevice:
    """
    Test for anta.device.AntaDevice Abstract class
    """

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "device, command_data, expected_data",
        map(lambda d: (d["device"], d["command"], d["expected"]), COLLECT_ANTADEVICE_DATA),
        indirect=["device"],
        ids=generate_test_ids_list(COLLECT_ANTADEVICE_DATA),
    )
    async def test_collect(self, device: AntaDevice, command_data: dict[str, Any], expected_data: dict[str, Any]) -> None:
        """
        Test AntaDevice.collect behavior
        """
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

    @pytest.mark.parametrize("device, expected", CACHE_STATS_DATA, indirect=["device"])
    def test_cache_statistics(self, device: AntaDevice, expected: dict[str, Any] | None) -> None:
        """
        Verify that when cache statistics attribute does not exist
        TODO add a test where cache has some value
        """
        assert device.cache_statistics == expected

    def test_supports(self, device: AntaDevice) -> None:
        """
        Test if the supports() method
        """
        command = AntaCommand(command="show hardware counter drop", errors=["Unavailable command (not supported on this hardware platform) (at token 2: 'counter')"])
        assert device.supports(command) is False
        command = AntaCommand(command="show hardware counter drop")
        assert device.supports(command) is True
