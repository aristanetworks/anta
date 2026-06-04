# Copyright (c) 2026 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Unit tests for the asynceapi._auth module."""

from __future__ import annotations

import asyncio
import json

import httpx
import pytest

from asynceapi._auth import EapiSessionAuth, SessionState
from asynceapi.errors import EapiAsyncOnlyError, EapiAuthenticationError

_HOST = "192.0.2.1"
_USERNAME = "admin"
_PASSWORD = "test1234"

_LOGIN_URL = f"https://{_HOST}:443/login"
_COMMAND_URL = f"https://{_HOST}:443/command-api"

_SESSION_COOKIE = "aabbccdd11223344"


@pytest.fixture(name="session_auth")
def _session_auth_fixture() -> EapiSessionAuth:
    """Return a fresh EapiSessionAuth with known credentials."""
    return EapiSessionAuth(username=_USERNAME, password=_PASSWORD, login_url=_LOGIN_URL, host=_HOST)


def test_session_state_initial_state() -> None:
    """Test that fresh SessionState starts logged out with no cookie."""
    state = SessionState()
    assert state.logged_in is False
    assert state.session_cookie is None


def test_session_state_reset_clears_state() -> None:
    """Test that reset() clears logged_in and session_cookie to their defaults."""
    state = SessionState()
    state.logged_in = True
    state.session_cookie = _SESSION_COOKIE
    state.reset()
    assert state.logged_in is False
    assert state.session_cookie is None


def test_eapi_session_auth_repr_masks_credentials(session_auth: EapiSessionAuth) -> None:
    """Test that repr includes the host but masks username and password."""
    auth_repr = repr(session_auth)
    assert _HOST in auth_repr
    assert _USERNAME not in auth_repr
    assert _PASSWORD not in auth_repr


@pytest.mark.parametrize(
    ("logged_in", "cookie", "expected_header"),
    [
        (True, _SESSION_COOKIE, {"Cookie": f"Session={_SESSION_COOKIE}"}),
        (False, None, {}),
    ],
    ids=["logged_in", "logged_out"],
)
def test_eapi_session_auth_properties_reflect_state(
    session_auth: EapiSessionAuth,
    logged_in: bool,
    cookie: str | None,
    expected_header: dict[str, str],
) -> None:
    """Test that logged_in, session_cookie, and cookie_header reflect the underlying SessionState."""
    session_auth._state.logged_in = logged_in  # type: ignore[protected-access]
    session_auth._state.session_cookie = cookie  # type: ignore[protected-access]
    assert session_auth.logged_in is logged_in
    assert session_auth.session_cookie == cookie
    assert session_auth.cookie_header == expected_header


def test_eapi_session_auth_build_login_request(session_auth: EapiSessionAuth) -> None:
    """Test that _build_login_request() produces a POST to the login URL with credentials in the body."""
    req = session_auth._build_login_request()  # type: ignore[protected-access]
    assert req.method == "POST"
    assert req.url.path == "/login"
    assert json.loads(req.content) == {"username": _USERNAME, "password": _PASSWORD}


def test_eapi_session_auth_handle_login_response_success(session_auth: EapiSessionAuth) -> None:
    """Test that a 200 with a Session cookie sets logged_in and stores the cookie."""
    login_req = httpx.Request("POST", _LOGIN_URL)
    response = httpx.Response(200, headers={"Set-Cookie": f"Session={_SESSION_COOKIE}; Path=/"}, request=login_req)
    session_auth._handle_login_response(response=response)  # type: ignore[protected-access]
    assert session_auth.logged_in is True
    assert session_auth.session_cookie == _SESSION_COOKIE


@pytest.mark.parametrize(
    ("status_code", "expected_exc"),
    [
        (401, EapiAuthenticationError),
        (500, httpx.HTTPStatusError),
    ],
    ids=["401_auth_error", "500_http_error"],
)
def test_eapi_session_auth_handle_login_response_error_raises(
    session_auth: EapiSessionAuth,
    status_code: int,
    expected_exc: type[Exception],
) -> None:
    """Test that a failed login raises the correct exception and leaves state clean."""
    login_req = httpx.Request("POST", _LOGIN_URL)
    with pytest.raises(expected_exc):
        session_auth._handle_login_response(httpx.Response(status_code, request=login_req))  # type: ignore[protected-access]
    assert session_auth.logged_in is False
    assert session_auth.session_cookie is None


def test_eapi_session_auth_handle_login_response_no_cookie_raises(session_auth: EapiSessionAuth) -> None:
    """Test that a 2xx without a Session cookie raises RuntimeError and leaves state clean."""
    login_req = httpx.Request("POST", _LOGIN_URL)
    with pytest.raises(RuntimeError, match="no Session cookie"):
        session_auth._handle_login_response(httpx.Response(200, request=login_req))  # type: ignore[protected-access]
    assert session_auth.logged_in is False
    assert session_auth.session_cookie is None


def test_eapi_session_auth_attach_cookie(session_auth: EapiSessionAuth) -> None:
    """Test that _attach_cookie() sets the Cookie header when a session cookie is held."""
    session_auth._state.session_cookie = _SESSION_COOKIE  # type: ignore[protected-access]
    request = httpx.Request("POST", _COMMAND_URL)
    session_auth._attach_cookie(request=request)  # type: ignore[protected-access]
    assert request.headers.get("Cookie") == f"Session={_SESSION_COOKIE}"


def test_eapi_session_auth_sync_auth_flow_raises(session_auth: EapiSessionAuth) -> None:
    """Test that sync_auth_flow raises EapiAsyncOnlyError."""
    with pytest.raises(EapiAsyncOnlyError):
        session_auth.sync_auth_flow(httpx.Request("POST", _COMMAND_URL))


async def test_eapi_session_auth_reset_clears_state(session_auth: EapiSessionAuth) -> None:
    """Test that reset() clears logged_in and session_cookie."""
    session_auth._state.logged_in = True  # type: ignore[protected-access]
    session_auth._state.session_cookie = _SESSION_COOKIE  # type: ignore[protected-access]
    await session_auth.reset()
    assert session_auth.logged_in is False
    assert session_auth.session_cookie is None


async def test_eapi_session_auth_reset_serialized_with_login(session_auth: EapiSessionAuth) -> None:
    """Test that reset() waits for an in-progress login to finish before clearing state."""
    gen = session_auth.async_auth_flow(request=httpx.Request("POST", _COMMAND_URL))
    login_req = await anext(gen)

    reset_task = asyncio.create_task(session_auth.reset())
    await asyncio.sleep(0)  # give reset_task a chance to attempt the lock — it should block

    login_response = httpx.Response(200, headers={"Set-Cookie": f"Session={_SESSION_COOKIE}; Path=/"}, request=login_req)
    await gen.asend(login_response)
    await reset_task

    assert session_auth.logged_in is False
    assert session_auth.session_cookie is None
    await gen.aclose()


async def test_auth_flow_initial_login(session_auth: EapiSessionAuth) -> None:
    """Test that the first request triggers login and the command request carries the session cookie."""
    gen = session_auth.async_auth_flow(request=httpx.Request("POST", _COMMAND_URL))

    login_req = await anext(gen)
    assert login_req.url.path == "/login"

    login_response = httpx.Response(200, headers={"Set-Cookie": f"Session={_SESSION_COOKIE}; Path=/"}, request=login_req)
    cmd_req = await gen.asend(login_response)
    assert cmd_req.url.path == "/command-api"
    assert cmd_req.headers.get("Cookie") == f"Session={_SESSION_COOKIE}"
    await gen.aclose()


async def test_auth_flow_skips_login_when_already_logged_in(session_auth: EapiSessionAuth) -> None:
    """Test that an already-logged-in session skips login and attaches the cookie directly."""
    session_auth._state.logged_in = True  # type: ignore[protected-access]
    session_auth._state.session_cookie = _SESSION_COOKIE  # type: ignore[protected-access]

    gen = session_auth.async_auth_flow(request=httpx.Request("POST", _COMMAND_URL))
    cmd_req = await anext(gen)
    assert cmd_req.url.path == "/command-api"
    assert cmd_req.headers.get("Cookie") == f"Session={_SESSION_COOKIE}"

    with pytest.raises(StopAsyncIteration):
        await gen.asend(httpx.Response(200, request=cmd_req))


async def test_auth_flow_401_raises(session_auth: EapiSessionAuth) -> None:
    """Test that a 401 on the command request raises EapiAuthenticationError."""
    session_auth._state.logged_in = True  # type: ignore[protected-access]
    session_auth._state.session_cookie = _SESSION_COOKIE  # type: ignore[protected-access]

    gen = session_auth.async_auth_flow(request=httpx.Request("POST", _COMMAND_URL))
    cmd_req = await anext(gen)

    with pytest.raises(EapiAuthenticationError):
        await gen.asend(httpx.Response(401, request=cmd_req))
