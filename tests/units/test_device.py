# Copyright (c) 2023-2025 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""test anta.device.py."""

from __future__ import annotations

import asyncio
from contextlib import AbstractContextManager
from contextlib import nullcontext as does_not_raise
from pathlib import Path
from typing import TYPE_CHECKING, Any
from unittest.mock import patch

import pytest
from asyncssh import SSHClientConnection, SSHClientConnectionOptions
from httpx import ConnectError, HTTPError, TimeoutException
from rich import print as rprint

from anta.device import AntaDevice, AsyncEOSDevice
from anta.models import AntaCommand
from asynceapi import EapiCommandError
from tests.units.conftest import COMMAND_OUTPUT

if TYPE_CHECKING:
    from _pytest.mark.structures import ParameterSet

INIT_PARAMS: list[ParameterSet] = [
    pytest.param({"host": "42.42.42.42", "username": "anta", "password": "anta"}, {"name": "42.42.42.42"}, does_not_raise(), id="no name, no port"),
    pytest.param({"host": "42.42.42.42", "username": "anta", "password": "anta", "port": 666}, {"name": "42.42.42.42:666"}, does_not_raise(), id="no name, port"),
    pytest.param(
        {"host": "42.42.42.42", "username": "anta", "password": "anta", "name": "test.anta.ninja", "disable_cache": True},
        {"name": "test.anta.ninja"},
        does_not_raise(),
        id="name",
    ),
    pytest.param(
        {"host": "42.42.42.42", "username": "anta", "password": "anta", "name": "test.anta.ninja", "insecure": True},
        {"name": "test.anta.ninja"},
        does_not_raise(),
        id="insecure",
    ),
    pytest.param(
        {"host": None, "username": "anta", "password": "anta", "name": "test.anta.ninja"},
        None,
        pytest.raises(ValueError, match="'host' is required to create an AsyncEOSDevice"),
        id="host is None",
    ),
    pytest.param(
        {"host": "42.42.42.42", "username": None, "password": "anta", "name": "test.anta.ninja"},
        None,
        pytest.raises(ValueError, match="'username' is required to instantiate device 'test.anta.ninja'"),
        id="username is None",
    ),
    pytest.param(
        {"host": "42.42.42.42", "username": "anta", "password": None, "name": "test.anta.ninja"},
        None,
        pytest.raises(ValueError, match="'password' is required to instantiate device 'test.anta.ninja'"),
        id="password is None",
    ),
]
EQUALITY_PARAMS: list[ParameterSet] = [
    pytest.param({"host": "42.42.42.42", "username": "anta", "password": "anta"}, {"host": "42.42.42.42", "username": "anta", "password": "blah"}, True, id="equal"),
    pytest.param(
        {"host": "42.42.42.42", "username": "anta", "password": "anta", "name": "device1"},
        {"host": "42.42.42.42", "username": "plop", "password": "anta", "name": "device2"},
        True,
        id="equals-name",
    ),
    pytest.param(
        {"host": "42.42.42.42", "username": "anta", "password": "anta"},
        {"host": "42.42.42.42", "username": "anta", "password": "anta", "port": 666},
        False,
        id="not-equal-port",
    ),
    pytest.param(
        {"host": "42.42.42.41", "username": "anta", "password": "anta"},
        {"host": "42.42.42.42", "username": "anta", "password": "anta"},
        False,
        id="not-equal-host",
    ),
]
ASYNCEAPI_COLLECT_PARAMS: list[ParameterSet] = [
    pytest.param(
        {},
        {
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
                    }
                ]
            },
        },
        {
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
        id="command",
    ),
    pytest.param(
        {"enable": True},
        {
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
                ]
            },
        },
        {
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
        id="enable",
    ),
    pytest.param(
        {"enable": True, "enable_password": "anta"},
        {
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
                ]
            },
        },
        {
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
        id="enable password",
    ),
    pytest.param(
        {},
        {
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
                ]
            },
        },
        {
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
        id="revision",
    ),
    pytest.param(
        {},
        {
            "command": "show version",
            "patch_kwargs": {
                "side_effect": EapiCommandError(
                    passed=[],
                    failed="show version",
                    errors=["Authorization denied for command 'show version'"],
                    errmsg="Invalid command",
                    not_exec=[],
                )
            },
        },
        {"output": None, "errors": ["Authorization denied for command 'show version'"]},
        id="asynceapi.EapiCommandError - Authorization denied",
    ),
    pytest.param(
        {},
        {
            "command": "show version",
            "patch_kwargs": {
                "side_effect": EapiCommandError(
                    passed=[],
                    failed="show version",
                    errors=["not supported on this hardware platform"],
                    errmsg="Invalid command",
                    not_exec=[],
                )
            },
        },
        {"output": None, "errors": ["not supported on this hardware platform"]},
        id="asynceapi.EapiCommandError - not supported",
    ),
    pytest.param(
        {},
        {
            "command": "show version",
            "patch_kwargs": {
                "side_effect": EapiCommandError(
                    passed=[],
                    failed="show version",
                    errors=["BGP inactive"],
                    errmsg="Invalid command",
                    not_exec=[],
                )
            },
        },
        {"output": None, "errors": ["BGP inactive"]},
        id="asynceapi.EapiCommandError - known EOS error",
    ),
    pytest.param(
        {},
        {
            "command": "show version",
            "patch_kwargs": {
                "side_effect": EapiCommandError(
                    passed=[],
                    failed="show version",
                    errors=["Invalid input (privileged mode required)"],
                    errmsg="Invalid command",
                    not_exec=[],
                )
            },
        },
        {"output": None, "errors": ["Invalid input (privileged mode required)"]},
        id="asynceapi.EapiCommandError - requires privileges",
    ),
    pytest.param(
        {},
        {"command": "show version", "patch_kwargs": {"side_effect": HTTPError("404")}},
        {"output": None, "errors": ["HTTPError: 404"]},
        id="httpx.HTTPError",
    ),
    pytest.param(
        {},
        {"command": "show version", "patch_kwargs": {"side_effect": ConnectError("Cannot open port")}},
        {"output": None, "errors": ["ConnectError: Cannot open port"]},
        id="httpx.ConnectError",
    ),
    pytest.param(
        {},
        {"command": "show version", "patch_kwargs": {"side_effect": TimeoutException("Test")}},
        {"output": None, "errors": ["TimeoutException: Test"]},
        id="httpx.TimeoutException",
    ),
]
ASYNCEAPI_COPY_PARAMS: list[ParameterSet] = [
    pytest.param({}, {"sources": [Path("/mnt/flash"), Path("/var/log/agents")], "destination": Path(), "direction": "from"}, id="from"),
    pytest.param({}, {"sources": [Path("/mnt/flash"), Path("/var/log/agents")], "destination": Path(), "direction": "to"}, id="to"),
    pytest.param({}, {"sources": [Path("/mnt/flash"), Path("/var/log/agents")], "destination": Path(), "direction": "wrong"}, id="wrong"),
]
REFRESH_PARAMS: list[ParameterSet] = [
    pytest.param(
        {},
        (
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
                ]
            },
        ),
        {"is_online": True, "established": True, "hw_model": "DCS-7280CR3-32P4-F"},
        id="established",
    ),
    pytest.param(
        {},
        (
            {"side_effect": HTTPError(message="Unauthorized")},
            {},
        ),
        {"is_online": False, "established": False, "hw_model": None},
        id="is not online",
    ),
    pytest.param(
        {},
        (
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
                ]
            },
        ),
        {"is_online": True, "established": False, "hw_model": None},
        id="cannot parse command",
    ),
    pytest.param(
        {},
        (
            {"return_value": True},
            {
                "side_effect": EapiCommandError(
                    passed=[],
                    failed="show version",
                    errors=["Authorization denied for command 'show version'"],
                    errmsg="Invalid command",
                    not_exec=[],
                )
            },
        ),
        {"is_online": True, "established": False, "hw_model": None},
        id="asynceapi.EapiCommandError",
    ),
    pytest.param(
        {},
        ({"return_value": True}, {"side_effect": HTTPError("404")}),
        {"is_online": True, "established": False, "hw_model": None},
        id="httpx.HTTPError",
    ),
    pytest.param(
        {},
        ({"return_value": True}, {"side_effect": ConnectError("Cannot open port")}),
        {"is_online": True, "established": False, "hw_model": None},
        id="httpx.ConnectError",
    ),
    pytest.param(
        {},
        (
            {"return_value": True},
            {
                "return_value": [
                    {
                        "mfgName": "Arista",
                        "modelName": "",
                    }
                ]
            },
        ),
        {"is_online": True, "established": False, "hw_model": ""},
        id="modelName empty string",
    ),
]
COLLECT_PARAMS: list[ParameterSet] = [
    pytest.param(
        {"disable_cache": False},
        {"command": "show version", "use_cache": True},
        {"cache_hit": False},
        id="device cache enabled, command cache enabled, no cache hit",
    ),
    pytest.param(
        {"disable_cache": False},
        {"command": "show version", "use_cache": True},
        {"cache_hit": True},
        id="device cache enabled, command cache enabled, cache hit",
    ),
    pytest.param({"disable_cache": True}, {"command": "show version", "use_cache": True}, {}, id="device cache disabled, command cache enabled"),
    pytest.param(
        {"disable_cache": False},
        {"command": "show version", "use_cache": False},
        {"cache_hit": True},
        id="device cache enabled, command cache disabled, cache has command",
    ),
    pytest.param(
        {"disable_cache": False},
        {"command": "show version", "use_cache": False},
        {"cache_hit": False},
        id="device cache enabled, command cache disabled, cache does not have data",
    ),
    pytest.param({"disable_cache": True}, {"command": "show version", "use_cache": False}, {}, id="device cache disabled, command cache disabled"),
]
CACHE_STATS_PARAMS: list[ParameterSet] = [
    pytest.param({"disable_cache": False}, {"total_commands_sent": 0, "cache_hits": 0, "cache_hit_ratio": "0.00%"}, id="with_cache"),
    pytest.param({"disable_cache": True}, None, id="without_cache"),
]


class TestAntaDevice:
    """Test for anta.device.AntaDevice Abstract class."""

    @pytest.mark.parametrize(("device", "command", "expected"), COLLECT_PARAMS, indirect=["device"])
    async def test_collect(self, device: AntaDevice, command: dict[str, Any], expected: dict[str, Any]) -> None:
        """Test AntaDevice.collect behavior."""
        cmd = AntaCommand(command=command["command"], use_cache=command["use_cache"])

        # Dummy output for cache hit
        cached_output = "cached_value"

        if device.cache is not None and expected["cache_hit"] is True:
            await device.cache.set(cmd.uid, cached_output)

        await device.collect(cmd)

        if device.cache is not None:  # device_cache is enabled
            current_cached_data = await device.cache.get(cmd.uid)
            if cmd.use_cache is True:  # command is allowed to use cache
                if expected["cache_hit"] is True:
                    assert cmd.output == cached_output
                    assert current_cached_data == cached_output
                    assert device.cache.stats["hits"] == 2
                else:
                    assert cmd.output == COMMAND_OUTPUT
                    assert current_cached_data == COMMAND_OUTPUT
                    assert device.cache.stats["hits"] == 1
            else:  # command is not allowed to use cache
                device._collect.assert_called_once_with(command=cmd, collection_id=None)  # type: ignore[attr-defined]
                assert cmd.output == COMMAND_OUTPUT
                if expected["cache_hit"] is True:
                    assert current_cached_data == cached_output
                else:
                    assert current_cached_data is None
        else:  # device is disabled
            assert device.cache is None
            device._collect.assert_called_once_with(command=cmd, collection_id=None)  # type: ignore[attr-defined]

    @pytest.mark.parametrize(("device", "expected"), CACHE_STATS_PARAMS, indirect=["device"])
    def test_cache_statistics(self, device: AntaDevice, expected: dict[str, Any] | None) -> None:
        """Verify that when cache statistics attribute does not exist.

        TODO add a test where cache has some value.
        """
        assert device.cache_statistics == expected


class TestAsyncEOSDevice:
    """Test for anta.device.AsyncEOSDevice."""

    @pytest.mark.parametrize(("device", "expected", "expected_raise"), INIT_PARAMS)
    def test__init__(self, device: dict[str, Any], expected: dict[str, Any] | None, expected_raise: AbstractContextManager[Exception]) -> None:
        """Test the AsyncEOSDevice constructor."""
        with expected_raise:
            dev = AsyncEOSDevice(**device)

            assert expected is not None
            assert dev.name == expected["name"]
            if device.get("disable_cache") is True:
                assert dev.cache is None
                assert dev.cache_locks is None
            else:  # False or None
                assert dev.cache is not None
                assert dev.cache_locks is not None
            hash(dev)

            with patch("anta.device.__DEBUG__", new=True):
                rprint(dev)

    @pytest.mark.parametrize(("device1", "device2", "expected"), EQUALITY_PARAMS)
    def test__eq(self, device1: dict[str, Any], device2: dict[str, Any], expected: bool) -> None:
        """Test the AsyncEOSDevice equality."""
        dev1 = AsyncEOSDevice(**device1)
        dev2 = AsyncEOSDevice(**device2)
        if expected:
            assert dev1 == dev2
        else:
            assert dev1 != dev2

    @pytest.mark.parametrize(
        ("async_device", "patch_kwargs", "expected"),
        REFRESH_PARAMS,
        indirect=["async_device"],
    )
    async def test_refresh(self, async_device: AsyncEOSDevice, patch_kwargs: list[dict[str, Any]], expected: dict[str, Any]) -> None:
        """Test AsyncEOSDevice.refresh()."""
        with patch.object(async_device._session, "check_connection", **patch_kwargs[0]), patch.object(async_device._session, "cli", **patch_kwargs[1]):
            await async_device.refresh()
            async_device._session.check_connection.assert_called_once()  # type: ignore[attr-defined] # asynceapi.Device.check_connection is patched
            if expected["is_online"]:
                async_device._session.cli.assert_called_once()  # type: ignore[attr-defined] # asynceapi.Device.cli is patched
            assert async_device.is_online == expected["is_online"]
            assert async_device.established == expected["established"]
            assert async_device.hw_model == expected["hw_model"]

    @pytest.mark.parametrize(
        ("async_device", "command", "expected"),
        ASYNCEAPI_COLLECT_PARAMS,
        indirect=["async_device"],
    )
    async def test__collect(self, async_device: AsyncEOSDevice, command: dict[str, Any], expected: dict[str, Any]) -> None:
        """Test AsyncEOSDevice._collect()."""
        cmd = AntaCommand(command=command["command"], revision=command["revision"]) if "revision" in command else AntaCommand(command=command["command"])
        with patch.object(async_device._session, "cli", **command["patch_kwargs"]):
            collection_id = "pytest"
            await async_device.collect(cmd, collection_id=collection_id)
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
            async_device._session.cli.assert_called_once_with(commands=commands, ofmt=cmd.ofmt, version=cmd.version, req_id=f"ANTA-{collection_id}-{id(cmd)}")  # type: ignore[attr-defined] # asynceapi.Device.cli is patched
            assert cmd.output == expected["output"]
            assert cmd.errors == expected["errors"]

    @pytest.mark.parametrize(
        ("async_device", "copy"),
        ASYNCEAPI_COPY_PARAMS,
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
