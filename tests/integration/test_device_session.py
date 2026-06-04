# Copyright (c) 2026 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Integration tests for the asynceapi Device session-auth lifecycle."""

from __future__ import annotations

from typing import TYPE_CHECKING

import respx

from asynceapi import Device
from asynceapi._constants import EapiCommandFormat

if TYPE_CHECKING:
    from asynceapi._types import JsonRpc

_HOST = "192.0.2.1"
_PORT = 443
_PROTO = "https"
_USERNAME = "admin"
_PASSWORD = "test1234"  # noqa: S105
_SESSION_COOKIE = "aabbccdd11223344"

_JSONRPC_REQUEST: JsonRpc = {
    "jsonrpc": "2.0",
    "method": "runCmds",
    "params": {"version": 1, "cmds": ["show version"], "format": EapiCommandFormat.JSON},
    "id": "EapiExplorer-1",
}

_COMMAND_RESPONSE = {
    "jsonrpc": "2.0",
    "id": "EapiExplorer-1",
    "result": [{"modelName": "pytest"}],
}


async def test_device_session_logout_sends_cookie_and_resets_state() -> None:
    """Test that logout() POSTs /logout with the session cookie and resets session state."""
    with respx.mock:
        respx.post(path="/login").respond(status_code=200, headers={"Set-Cookie": f"Session={_SESSION_COOKIE}; Path=/"})
        respx.post(path="/command-api").respond(json=_COMMAND_RESPONSE)
        logout_route = respx.post(path="/logout").respond(status_code=200)

        device = Device(host=_HOST, username=_USERNAME, password=_PASSWORD, proto=_PROTO, port=_PORT, use_session=True)
        await device.jsonrpc_exec(jsonrpc=_JSONRPC_REQUEST)

        assert device._session_auth.logged_in is True  # type: ignore[union-attr]

        await device.aclose()

        assert logout_route.called
        assert logout_route.calls[0].request.headers.get("cookie") == f"Session={_SESSION_COOKIE}"
        assert device._session_auth.logged_in is False  # type: ignore[union-attr]
        assert device._session_auth.session_cookie is None  # type: ignore[union-attr]


async def test_device_session_context_manager_exit_triggers_logout() -> None:
    """Test that context-manager exit triggers logout and resets session state."""
    with respx.mock:
        respx.post(path="/login").respond(status_code=200, headers={"Set-Cookie": f"Session={_SESSION_COOKIE}; Path=/"})
        respx.post(path="/command-api").respond(json=_COMMAND_RESPONSE)
        logout_route = respx.post(path="/logout").respond(status_code=200)

        async with Device(host=_HOST, username=_USERNAME, password=_PASSWORD, proto=_PROTO, port=_PORT, use_session=True) as device:
            await device.jsonrpc_exec(jsonrpc=_JSONRPC_REQUEST)

        assert logout_route.called
        assert logout_route.calls[0].request.headers.get("cookie") == f"Session={_SESSION_COOKIE}"
        assert device._session_auth.logged_in is False  # type: ignore[union-attr]
        assert device._session_auth.session_cookie is None  # type: ignore[union-attr]
