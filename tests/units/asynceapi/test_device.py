# Copyright (c) 2023-2025 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Unit tests the asynceapi.device module."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import pytest
from httpx import HTTPStatusError

from asynceapi import Device, EapiCommandError

from .test_data import ERROR_EAPI_RESPONSE, JSONRPC_REQUEST_TEMPLATE, SUCCESS_EAPI_RESPONSE

if TYPE_CHECKING:
    from pytest_httpx import HTTPXMock


@pytest.mark.parametrize(
    "cmds",
    [
        (["show version", "show clock"]),
        ([{"cmd": "show version"}, {"cmd": "show clock"}]),
        ([{"cmd": "show version"}, "show clock"]),
    ],
    ids=["simple_commands", "complex_commands", "mixed_commands"],
)
async def test_jsonrpc_exec_success(
    asynceapi_device: Device,
    httpx_mock: HTTPXMock,
    cmds: list[str | dict[str, Any]],
) -> None:
    """Test the Device.jsonrpc_exec method with a successful response. Simple and complex commands are tested."""
    jsonrpc_request: dict[str, Any] = JSONRPC_REQUEST_TEMPLATE.copy()
    jsonrpc_request["params"]["cmds"] = cmds

    httpx_mock.add_response(json=SUCCESS_EAPI_RESPONSE)

    result = await asynceapi_device.jsonrpc_exec(jsonrpc=jsonrpc_request)

    assert result == SUCCESS_EAPI_RESPONSE["result"]


@pytest.mark.parametrize(
    "cmds",
    [
        (["show version", "bad command", "show clock"]),
        ([{"cmd": "show version"}, {"cmd": "bad command"}, {"cmd": "show clock"}]),
        ([{"cmd": "show version"}, {"cmd": "bad command"}, "show clock"]),
    ],
    ids=["simple_commands", "complex_commands", "mixed_commands"],
)
async def test_jsonrpc_exec_eapi_command_error(
    asynceapi_device: Device,
    httpx_mock: HTTPXMock,
    cmds: list[str | dict[str, Any]],
) -> None:
    """Test the Device.jsonrpc_exec method with an error response. Simple and complex commands are tested."""
    jsonrpc_request: dict[str, Any] = JSONRPC_REQUEST_TEMPLATE.copy()
    jsonrpc_request["params"]["cmds"] = cmds

    error_eapi_response: dict[str, Any] = ERROR_EAPI_RESPONSE.copy()
    httpx_mock.add_response(json=error_eapi_response)

    with pytest.raises(EapiCommandError) as exc_info:
        await asynceapi_device.jsonrpc_exec(jsonrpc=jsonrpc_request)

    assert exc_info.value.passed == [error_eapi_response["error"]["data"][0]]
    assert exc_info.value.failed == "bad command"
    assert exc_info.value.errors == ["Invalid input (at token 1: 'bad')"]
    assert exc_info.value.errmsg == "CLI command 2 of 3 'bad command' failed: invalid command"
    assert exc_info.value.not_exec == [jsonrpc_request["params"]["cmds"][2]]


async def test_jsonrpc_exec_http_status_error(asynceapi_device: Device, httpx_mock: HTTPXMock) -> None:
    """Test the Device.jsonrpc_exec method with an HTTPStatusError."""
    jsonrpc_request: dict[str, Any] = JSONRPC_REQUEST_TEMPLATE.copy()
    jsonrpc_request["params"]["cmds"] = ["show version"]

    httpx_mock.add_response(status_code=500, text="Internal Server Error")

    with pytest.raises(HTTPStatusError):
        await asynceapi_device.jsonrpc_exec(jsonrpc=jsonrpc_request)
