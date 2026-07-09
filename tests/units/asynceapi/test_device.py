# Copyright (c) 2023-2026 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Unit tests for the asynceapi.device module."""

from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING
from unittest.mock import ANY, AsyncMock, patch

import pytest
import respx
from httpx import ConnectError, HTTPStatusError, Response

from asynceapi import Device, EapiCommandError
from asynceapi._constants import EapiCommandFormat
from asynceapi.errors import EapiAuthenticationError

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

        device = Device(host=_HOST, username="admin", password=_PASSWORD, use_session_auth=True)
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

        device = Device(host=_HOST, username="admin", password=_PASSWORD, use_session_auth=True)
        try:
            await device.jsonrpc_exec(jsonrpc=_jsonrpc_request())
            with pytest.raises(EapiAuthenticationError):
                await device.jsonrpc_exec(jsonrpc=_jsonrpc_request())
        finally:
            await device.aclose()

        assert login_route.call_count == 1
        assert command_route.call_count == 2
        # The 401 clears session_cookie → logged_in is False → So logout() is a no-op
        assert logout_route.call_count == 0


async def test_aclose_calls_logout_when_session_enabled() -> None:
    """Test that aclose() calls logout() exactly once when use_session_auth=True."""
    device = Device(host="localhost", username="admin", password=_PASSWORD, use_session_auth=True)
    with patch.object(device, "logout", new_callable=AsyncMock) as mock_logout:
        await device.aclose()
    mock_logout.assert_called_once()


async def test_aclose_skips_logout_when_session_disabled() -> None:
    """Test that aclose() never calls logout() when use_session_auth=False."""
    device = Device(host="localhost", username="admin", password=_PASSWORD, use_session_auth=False)
    with patch.object(device, "logout", new_callable=AsyncMock) as mock_logout:
        await device.aclose()
    mock_logout.assert_not_called()


async def test_device_session_logout_sends_cookie_and_resets_state() -> None:
    """Test that logout() POSTs /logout with the session cookie and resets session state."""
    with respx.mock as respx_mock:
        respx_mock.post(f"{_BASE_URL}/login").respond(status_code=200, headers={"Set-Cookie": f"Session={_SESSION_COOKIE}; Path=/"})
        respx_mock.post(f"{_BASE_URL}/command-api").respond(json=_jsonrpc_response())
        logout_route = respx_mock.post(f"{_BASE_URL}/logout").respond(status_code=200)

        device = Device(host=_HOST, username="admin", password=_PASSWORD, use_session_auth=True)
        await device.jsonrpc_exec(jsonrpc=_jsonrpc_request())

        assert device._session_auth is not None
        assert device._session_auth.logged_in is True

        await device.aclose()

        assert logout_route.called
        assert logout_route.calls[0].request.headers.get("cookie") == f"Session={_SESSION_COOKIE}"
        assert device._session_auth.logged_in is False
        assert device._session_auth.session_cookie is None


async def test_device_session_context_manager_exit_triggers_logout() -> None:
    """Test that context-manager exit triggers logout and resets session state."""
    with respx.mock as respx_mock:
        respx_mock.post(f"{_BASE_URL}/login").respond(status_code=200, headers={"Set-Cookie": f"Session={_SESSION_COOKIE}; Path=/"})
        respx_mock.post(f"{_BASE_URL}/command-api").respond(json=_jsonrpc_response())
        logout_route = respx_mock.post(f"{_BASE_URL}/logout").respond(status_code=200)

        async with Device(host=_HOST, username="admin", password=_PASSWORD, use_session_auth=True) as device:
            await device.jsonrpc_exec(jsonrpc=_jsonrpc_request())

        assert logout_route.called
        assert logout_route.calls[0].request.headers.get("cookie") == f"Session={_SESSION_COOKIE}"
        assert device._session_auth is not None
        assert device._session_auth.logged_in is False
        assert device._session_auth.session_cookie is None


@pytest.mark.parametrize(
    ("username", "password"),
    [
        (None, None),
        ("admin", None),
        (None, _PASSWORD),
    ],
    ids=["no_credentials", "username_only", "password_only"],
)
def test_device_init_session_raises_without_credentials(username: str | None, password: str | None) -> None:
    """Test that Device raises ValueError when use_session_auth=True but credentials are incomplete."""
    with pytest.raises(ValueError, match="username and password are required"):
        Device(host=_HOST, username=username, password=password, use_session_auth=True)


def test_device_init_session_raises_without_host() -> None:
    """Test that Device raises ValueError when use_session_auth=True but host is not provided."""
    with pytest.raises(ValueError, match="host is required"):
        Device(host=None, username="admin", password=_PASSWORD, use_session_auth=True)


async def test_logout_noop_when_session_auth_is_none() -> None:
    """Test that logout() is a no-op when the device is not using session auth."""
    device = Device(host=_HOST, username="admin", password=_PASSWORD, use_session_auth=False)
    await device.logout()
    assert device._session_auth is None


async def test_logout_noop_when_not_logged_in() -> None:
    """Test that logout() is a no-op when session auth exists but no login has occurred yet."""
    device = Device(host=_HOST, username="admin", password=_PASSWORD, use_session_auth=True)
    assert device._session_auth is not None
    await device.logout()
    assert device._session_auth.logged_in is False


async def test_logout_warns_on_http_error() -> None:
    """Test that logout() logs a warning and still resets state when the POST raises an HTTPError."""
    with respx.mock as respx_mock:
        respx_mock.post(f"{_BASE_URL}/login").respond(status_code=200, headers={"Set-Cookie": f"Session={_SESSION_COOKIE}; Path=/"})
        respx_mock.post(f"{_BASE_URL}/command-api").respond(json=_jsonrpc_response())
        respx_mock.post(f"{_BASE_URL}/logout").mock(side_effect=ConnectError("connection refused"))

        device = Device(host=_HOST, username="admin", password=_PASSWORD, use_session_auth=True)
        await device.jsonrpc_exec(jsonrpc=_jsonrpc_request())

        with patch("asynceapi.device.LOGGER.warning") as mock_warn:
            await device.logout()

    mock_warn.assert_called_once_with("Logout HTTP error for %s: %s", _HOST, ANY)
    assert device._session_auth is not None
    assert device._session_auth.logged_in is False


async def test_logout_resets_state_on_non_success_response() -> None:
    """Test that logout() silently resets state when the server returns a non-2xx status."""
    with respx.mock as respx_mock:
        respx_mock.post(f"{_BASE_URL}/login").respond(status_code=200, headers={"Set-Cookie": f"Session={_SESSION_COOKIE}; Path=/"})
        respx_mock.post(f"{_BASE_URL}/command-api").respond(json=_jsonrpc_response())
        respx_mock.post(f"{_BASE_URL}/logout").respond(status_code=503, text="Service Unavailable")

        device = Device(host=_HOST, username="admin", password=_PASSWORD, use_session_auth=True)
        await device.jsonrpc_exec(jsonrpc=_jsonrpc_request())
        await device.logout()

    assert device._session_auth is not None
    assert device._session_auth.logged_in is False
