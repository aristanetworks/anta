# Copyright (c) 2023-2026 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""test anta.device.py."""

from __future__ import annotations

import asyncio
import logging
from contextlib import AbstractContextManager
from contextlib import nullcontext as does_not_raise
from pathlib import Path
from typing import TYPE_CHECKING, Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from asyncssh import SSHClientConnection, SSHClientConnectionOptions
from httpx import ConnectError, ConnectTimeout, HTTPError, TimeoutException
from rich import print as rprint

from anta.device import AntaDevice, AntaDeviceCapabilities, AsyncEOSDevice
from anta.models import AntaCommand
from asynceapi import EapiCommandError
from asynceapi._models import EAPIClientConnectionOptions
from asynceapi.errors import EapiAuthenticationError
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
        pytest.raises(ValueError, match=r"'host' is required to create an AsyncEOSDevice"),
        id="host is None",
    ),
    pytest.param(
        {"host": "42.42.42.42", "username": None, "password": "anta", "name": "test.anta.ninja"},
        None,
        pytest.raises(ValueError, match=r"'username' is required to instantiate device 'test.anta.ninja'"),
        id="username is None",
    ),
    pytest.param(
        {"host": "42.42.42.42", "username": "anta", "password": None, "name": "test.anta.ninja"},
        None,
        pytest.raises(ValueError, match=r"'password' is required to instantiate device 'test.anta.ninja'"),
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
        {
            "command": "session peer-supervisor show file systems",
            "patch_kwargs": {
                "side_effect": EapiCommandError(
                    passed=[],
                    failed="session peer-supervisor show file systems",
                    errors=[""],
                    errmsg="CLI command 2 of 2 'session peer-supervisor show file systems' failed: could not run command",
                    not_exec=[],
                )
            },
        },
        {"output": None, "errors": ["could not run command"]},
        id="asynceapi.EapiCommandError - empty error list",
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
    pytest.param(
        {},
        {"command": "show version", "patch_kwargs": {"side_effect": EapiAuthenticationError("42.42.42.42")}},
        {"output": None, "errors": ["EapiAuthenticationError: Authentication failed for '42.42.42.42' (HTTP 401)."]},
        id="asynceapi.EapiAuthenticationError",
    ),
    pytest.param(
        {},
        {"command": "show version", "patch_kwargs": {"side_effect": EapiAuthenticationError("42.42.42.42", session_expired=True)}},
        {
            "output": None,
            "errors": ["EapiAuthenticationError: Session cookie expired. Consider increasing 'session timeout' under 'management api http-commands' on the device."],
        },
        id="asynceapi.EapiAuthenticationError.session_expired",
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
        id="is not online - HTTPError",
    ),
    pytest.param(
        {},
        (
            {"side_effect": EapiAuthenticationError("42.42.42.42", response_text="Bad username/password combination")},
            {},
        ),
        {"is_online": False, "established": False, "hw_model": None},
        id="is not online - EapiAuthenticationError",
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

    def test_max_connections(self, device: AntaDevice) -> None:
        """Test max_connections property."""
        assert device.max_connections is None

    def test_capabilities_default(self, device: AntaDevice) -> None:
        """Verify the base AntaDevice capabilities default to all-False."""
        assert device.capabilities == AntaDeviceCapabilities()
        assert device.capabilities.supports_session_auth is False


# pylint: disable=too-many-public-methods
class TestAsyncEOSDevice:
    """Test for anta.device.AsyncEOSDevice."""

    def test_capabilities(self) -> None:
        """Verify AsyncEOSDevice advertises session auth support."""
        assert AsyncEOSDevice.capabilities.supports_session_auth is True

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

    def test__init__stores_eapi_client_connection_options(self) -> None:
        """Test the AsyncEOSDevice eAPI client connection options."""
        dev = AsyncEOSDevice(host="42.42.42.42", username="anta", password="anta", port=8443, timeout=12.0, proto="https")

        assert dev._eapi_opts == EAPIClientConnectionOptions(
            host="42.42.42.42",
            username="anta",
            password="anta",
            port=8443,
            proto="https",
            timeout=12.0,
        )

    def test__rich_repr_debug_sanitizes_client_details(self, async_device: AsyncEOSDevice) -> None:
        """Test the debug Rich repr does not expose internal client state."""
        with patch("anta.device.__DEBUG__", new=True):
            rich_repr = dict(async_device.__rich_repr__())

        assert rich_repr["_client"] == {
            "host": async_device._client.host,
            "port": async_device._client.port,
            "base_url": str(async_device._client.base_url),
            "is_closed": async_device._client.is_closed,
        }
        assert "auth" not in rich_repr["_client"]
        assert "_auth" not in rich_repr["_client"]

    @pytest.mark.parametrize(("device1", "device2", "expected"), EQUALITY_PARAMS)
    def test__eq(self, device1: dict[str, Any], device2: dict[str, Any], expected: bool) -> None:
        """Test the AsyncEOSDevice equality."""
        dev1 = AsyncEOSDevice(**device1)
        dev2 = AsyncEOSDevice(**device2)
        if expected:
            assert dev1 == dev2
        else:
            assert dev1 != dev2

    def test_max_connections(self, async_device: AsyncEOSDevice) -> None:
        """Test max_connections property."""
        # HTTPX uses a max_connections of 100 by default
        assert async_device.max_connections == 100

    def test_max_connections_none(self, async_device: AsyncEOSDevice) -> None:
        """Test max_connections property when not available in the session object."""
        with patch.object(async_device, "_client", None):
            assert async_device.max_connections is None

    @pytest.mark.parametrize(
        ("async_device", "patch_kwargs", "expected"),
        REFRESH_PARAMS,
        indirect=["async_device"],
    )
    async def test_refresh(self, async_device: AsyncEOSDevice, patch_kwargs: list[dict[str, Any]], expected: dict[str, Any]) -> None:
        """Test AsyncEOSDevice.refresh()."""
        with patch.object(async_device._client, "check_api_endpoint", **patch_kwargs[0]), patch.object(async_device._client, "cli", **patch_kwargs[1]):
            await async_device.refresh()
            async_device._client.check_api_endpoint.assert_called_once()  # type: ignore[attr-defined] # asynceapi.Device.check_api_endpoint is patched
            if expected["is_online"]:
                async_device._client.cli.assert_called_once()  # type: ignore[attr-defined] # asynceapi.Device.cli is patched
            assert async_device.is_online == expected["is_online"]
            assert async_device.established == expected["established"]
            assert async_device.hw_model == expected["hw_model"]

    async def test_refresh_timeout_without_message_in_exception(self, async_device: AsyncEOSDevice, caplog: pytest.LogCaptureFixture) -> None:
        """Test when a timeout occurs in AsyncEOSDevice.refresh() without a message in the HTTPX exception."""
        caplog.set_level(logging.WARNING)

        # Simulating a low-level asyncio timeout created without additional context
        with patch.object(async_device._client, "check_api_endpoint", side_effect=ConnectTimeout(message=str(asyncio.TimeoutError()))):
            await async_device.refresh()

            assert not async_device.is_online
            assert not async_device.established
            assert "An error occurred while attempting to connect to device pytest: ConnectTimeout" in caplog.messages

    async def test_refresh_timeout_with_message_in_exception(self, async_device: AsyncEOSDevice, caplog: pytest.LogCaptureFixture) -> None:
        """Test when a timeout occurs in AsyncEOSDevice.refresh() with a message in the HTTPX exception."""
        caplog.set_level(logging.WARNING)

        with patch.object(async_device._client, "check_api_endpoint", side_effect=ConnectTimeout(message="Timeout!")):
            await async_device.refresh()

            assert not async_device.is_online
            assert not async_device.established
            assert "An error occurred while attempting to connect to device pytest: ConnectTimeout: Timeout!" in caplog.messages

    @pytest.mark.parametrize(
        ("async_device", "command", "expected"),
        ASYNCEAPI_COLLECT_PARAMS,
        indirect=["async_device"],
    )
    async def test__collect(self, async_device: AsyncEOSDevice, command: dict[str, Any], expected: dict[str, Any]) -> None:
        """Test AsyncEOSDevice._collect()."""
        cmd = AntaCommand(command=command["command"], revision=command["revision"]) if "revision" in command else AntaCommand(command=command["command"])
        with patch.object(async_device._client, "cli", **command["patch_kwargs"]):
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
            async_device._client.cli.assert_called_once_with(commands=commands, ofmt=cmd.ofmt, version=cmd.version, req_id=f"ANTA-{collection_id}-{id(cmd)}")  # type: ignore[attr-defined] # asynceapi.Device.cli is patched
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

    async def test_disconnect(self, async_device: AsyncEOSDevice) -> None:
        """Test that disconnect() closes the underlying httpx client."""
        assert not async_device._client.is_closed
        await async_device.disconnect()
        assert async_device._client.is_closed
        assert async_device.is_online is False
        assert async_device.established is False
        await async_device.disconnect()
        assert async_device._client.is_closed

    async def test_disconnect_with_session_calls_logout(self) -> None:
        """Test that disconnect() triggers logout() before aclose() when use_session_auth=True."""
        device = AsyncEOSDevice(host="42.42.42.42", username="anta", password="anta", use_session_auth=True)
        assert device._client._session_auth is not None

        logout_mock = AsyncMock()
        with patch.object(device._client, "logout", logout_mock):
            await device.disconnect()

        logout_mock.assert_awaited_once()
        assert device._client.is_closed
        assert device.is_online is False
        assert device.established is False

    async def test_refresh_recreate(self, async_device: AsyncEOSDevice) -> None:
        """Test that refresh() recreates the httpx client when it has been closed."""
        await async_device.disconnect()
        assert async_device._client.is_closed

        mock_client = MagicMock()
        mock_client.is_closed = False
        mock_client.check_api_endpoint = AsyncMock(return_value=True)
        mock_client.cli = AsyncMock(return_value=[{"modelName": "DCS-72"}])

        with patch.object(async_device, "_create_client", return_value=mock_client) as mock_create:
            await async_device.refresh()
            mock_create.assert_called_once()
            assert async_device._client is mock_client
            assert async_device.is_online is True
            assert async_device.established is True
            assert async_device.hw_model == "DCS-72"

    async def test__collect_raises_when_client_closed(self, async_device: AsyncEOSDevice) -> None:
        """Test that _collect() raises RuntimeError when the httpx client is closed."""
        await async_device.disconnect()
        assert async_device._client.is_closed
        cmd = AntaCommand(command="show version")
        with pytest.raises(RuntimeError, match="httpx client is closed"):
            await async_device._collect(cmd)

    def test_tags_set_not_mutated(self) -> None:
        """Verify that passing a tags set does not mutate the original set."""
        shared_tags = {"tag1", "tag2"}
        original_tags = shared_tags.copy()

        AsyncEOSDevice(
            host="42.42.42.42",
            username="anta",
            password="anta",
            name="device1",
            tags=shared_tags,
        )

        assert shared_tags == original_tags, "Original tags set should not be mutated"

    def test_tags_isolation_multiple_devices(self) -> None:
        """Verify that multiple devices from the same tags set do not inherit each other's names."""
        shared_tags = {"shared_tag"}

        device1 = AsyncEOSDevice(
            host="10.0.0.1",
            username="anta",
            password="anta",
            name="device1",
            tags=shared_tags,
        )

        device2 = AsyncEOSDevice(
            host="10.0.0.2",
            username="anta",
            password="anta",
            name="device2",
            tags=shared_tags,
        )

        assert "device1" in device1.tags
        assert "device2" in device2.tags
        assert "device2" not in device1.tags, "device1 should not have device2's name in tags"
        assert "device1" not in device2.tags, "device2 should not have device1's name in tags"
        assert "shared_tag" in device1.tags
        assert "shared_tag" in device2.tags

    def test_tags_none_initializes_with_device_name(self) -> None:
        """Verify that passing tags=None initializes with only device name."""
        device = AsyncEOSDevice(
            host="42.42.42.42",
            username="anta",
            password="anta",
            name="device1",
            tags=None,
        )

        assert "device1" in device.tags
        assert len(device.tags) == 1

    def test_tags_device_name_always_included(self) -> None:
        """Verify that device name is included in tags even if pre-existing."""
        tags = {"device1", "tag1"}
        device = AsyncEOSDevice(
            host="42.42.42.42",
            username="anta",
            password="anta",
            name="device1",
            tags=tags,
        )

        assert "device1" in device.tags
        assert "tag1" in device.tags
        assert len(device.tags) == 2
