# Copyright (c) 2023-2026 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Unit tests for the asynceapi.device module."""

from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING
from unittest.mock import AsyncMock, patch

import pytest
import respx
from httpx import HTTPStatusError, Response

from asynceapi import Device, EapiAuthenticationError, EapiCommandError
from asynceapi._constants import EapiCommandFormat

from .test_data import ERROR_EAPI_RESPONSE, JSONRPC_REQUEST_TEMPLATE, SUCCESS_EAPI_RESPONSE

_HOST = "192.0.2.1"
_PASSWORD = "test1234"
_SESSION_COOKIE = "aabbccdd11223344"
_BASE_URL = f"https://{_HOST}"


if TYPE_CHECKING:
    from pytest_httpx import HTTPXMock

    from asynceapi._types import EapiComplexCommand, EapiSimpleCommand, JsonRpc


def _jsonrpc_request() -> JsonRpc:
    """Return a fresh JSON-RPC request for session-auth tests."""
    return {
        "jsonrpc": "2.0",
        "method": "runCmds",
        "params": {"version": 1, "cmds": ["show version"], "format": EapiCommandFormat.JSON},
        "id": "EapiExplorer-1",
    }


def _jsonrpc_response() -> dict[str, object]:
    """Return a JSON-RPC response for session-auth tests."""
    return {
        "jsonrpc": "2.0",
        "id": "EapiExplorer-1",
        "result": [{"modelName": "pytest"}],
    }


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
    cmds: list[EapiSimpleCommand | EapiComplexCommand],
) -> None:
    """Test the Device.jsonrpc_exec method with a successful response. Simple and complex commands are tested."""
    jsonrpc_request = JSONRPC_REQUEST_TEMPLATE.copy()
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
    cmds: list[EapiSimpleCommand | EapiComplexCommand],
) -> None:
    """Test the Device.jsonrpc_exec method with an error response. Simple and complex commands are tested."""
    jsonrpc_request = JSONRPC_REQUEST_TEMPLATE.copy()
    jsonrpc_request["params"]["cmds"] = cmds

    httpx_mock.add_response(json=ERROR_EAPI_RESPONSE)

    with pytest.raises(EapiCommandError) as exc_info:
        await asynceapi_device.jsonrpc_exec(jsonrpc=jsonrpc_request)

    assert exc_info.value.passed == [ERROR_EAPI_RESPONSE["error"]["data"][0]]
    assert exc_info.value.failed == "bad command"
    assert exc_info.value.errors == ["Invalid input (at token 1: 'bad')"]
    assert exc_info.value.errmsg == "CLI command 2 of 3 'bad command' failed: invalid command"
    assert exc_info.value.not_exec == [jsonrpc_request["params"]["cmds"][2]]


async def test_jsonrpc_exec_http_status_error(asynceapi_device: Device, httpx_mock: HTTPXMock) -> None:
    """Test the Device.jsonrpc_exec method with an HTTPStatusError."""
    jsonrpc_request = JSONRPC_REQUEST_TEMPLATE.copy()
    jsonrpc_request["params"]["cmds"] = ["show version"]

    httpx_mock.add_response(status_code=500, text="Internal Server Error")

    with pytest.raises(HTTPStatusError):
        await asynceapi_device.jsonrpc_exec(jsonrpc=jsonrpc_request)


async def test_jsonrpc_exec_session_auth_concurrent_first_use_single_login() -> None:
    """Test concurrent session-auth requests share a single login and cookie."""
    with respx.mock as respx_mock:
        login_route = respx_mock.post(f"{_BASE_URL}/login").respond(status_code=200, headers={"Set-Cookie": f"Session={_SESSION_COOKIE}; Path=/"})
        command_route = respx_mock.post(f"{_BASE_URL}/command-api").respond(json=_jsonrpc_response())
        logout_route = respx_mock.post(f"{_BASE_URL}/logout").respond(status_code=200)

        device = Device(host=_HOST, username="admin", password=_PASSWORD, use_session=True)
        try:
            await asyncio.gather(*(device.jsonrpc_exec(jsonrpc=_jsonrpc_request()) for _ in range(5)))
        finally:
            await device.aclose()

        assert login_route.call_count == 1
        assert command_route.call_count == 5
        assert logout_route.call_count == 1
        assert all(call.request.headers.get("cookie") == f"Session={_SESSION_COOKIE}" for call in command_route.calls)


async def test_jsonrpc_exec_session_auth_command_401_does_not_relogin() -> None:
    """Test an expired session cookie raises and does not trigger a second login."""
    with respx.mock(assert_all_called=False) as respx_mock:
        login_route = respx_mock.post(f"{_BASE_URL}/login").respond(status_code=200, headers={"Set-Cookie": f"Session={_SESSION_COOKIE}; Path=/"})
        command_route = respx_mock.post(f"{_BASE_URL}/command-api").mock(side_effect=[Response(200, json=_jsonrpc_response()), Response(401)])
        logout_route = respx_mock.post(f"{_BASE_URL}/logout").respond(status_code=200)

        device = Device(host=_HOST, username="admin", password=_PASSWORD, use_session=True)
        try:
            await device.jsonrpc_exec(jsonrpc=_jsonrpc_request())
            with pytest.raises(EapiAuthenticationError):
                await device.jsonrpc_exec(jsonrpc=_jsonrpc_request())
        finally:
            await device.aclose()

        assert login_route.call_count == 1
        assert command_route.call_count == 2
        assert logout_route.call_count == 1


async def test_aclose_calls_logout_when_session_enabled() -> None:
    """Test that aclose() calls logout() exactly once when use_session=True."""
    device = Device(host="localhost", username="admin", password=_PASSWORD, use_session=True)
    with patch.object(device, "logout", new_callable=AsyncMock) as mock_logout:
        await device.aclose()
    mock_logout.assert_called_once()


async def test_aclose_skips_logout_when_session_disabled() -> None:
    """Test that aclose() never calls logout() when use_session=False."""
    device = Device(host="localhost", username="admin", password=_PASSWORD, use_session=False)
    with patch.object(device, "logout", new_callable=AsyncMock) as mock_logout:
        await device.aclose()
    mock_logout.assert_not_called()
