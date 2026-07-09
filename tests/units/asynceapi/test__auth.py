# Copyright (c) 2026 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Unit tests for the asynceapi._auth module."""

from __future__ import annotations

import asyncio
import logging

import httpx
import pytest

from asynceapi._auth import EapiSessionAuth, _cookie_fingerprint
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
    return EapiSessionAuth(host=_HOST, username=_USERNAME, password=_PASSWORD, login_url=_LOGIN_URL)


def test_eapi_session_auth_initial_state(session_auth: EapiSessionAuth) -> None:
    """Test that fresh EapiSessionAuth starts logged out with no cookie."""
    assert session_auth.logged_in is False
    assert session_auth.session_cookie is None


def test_eapi_session_auth_repr_masks_credentials(session_auth: EapiSessionAuth) -> None:
    """Test that repr includes the host but masks username and password."""
    auth_repr = repr(session_auth)
    assert _HOST in auth_repr
    assert _USERNAME not in auth_repr
    assert _PASSWORD not in auth_repr


def test_eapi_session_auth_sync_auth_flow_raises(session_auth: EapiSessionAuth) -> None:
    """Test that sync_auth_flow raises EapiAsyncOnlyError."""
    with pytest.raises(EapiAsyncOnlyError):
        session_auth.sync_auth_flow(httpx.Request("POST", _COMMAND_URL))


async def test_eapi_session_auth_reset_clears_state(session_auth: EapiSessionAuth) -> None:
    """Test that reset() clears logged_in and session_cookie."""
    session_auth.session_cookie = _SESSION_COOKIE
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


async def test_auth_flow_login_success(session_auth: EapiSessionAuth) -> None:
    """Test that a successful login routes through /login, attaches the cookie on the command request, and updates internal state."""
    gen = session_auth.async_auth_flow(request=httpx.Request("POST", _COMMAND_URL))

    login_req = await anext(gen)
    assert login_req.url.path == "/login"

    login_response = httpx.Response(200, headers={"Set-Cookie": f"Session={_SESSION_COOKIE}; Path=/"}, request=login_req)
    cmd_req = await gen.asend(login_response)
    assert cmd_req.url.path == "/command-api"
    assert cmd_req.headers.get("Cookie") == f"Session={_SESSION_COOKIE}"
    assert session_auth.logged_in is True
    assert session_auth.session_cookie == _SESSION_COOKIE
    await gen.aclose()


async def test_auth_flow_login_success_logs_cookie_fingerprint(session_auth: EapiSessionAuth, caplog: pytest.LogCaptureFixture) -> None:
    """Test that a successful login logs the cookie fingerprint."""
    caplog.set_level(logging.DEBUG, logger="asynceapi._auth")
    gen = session_auth.async_auth_flow(request=httpx.Request("POST", _COMMAND_URL))

    login_req = await anext(gen)
    await gen.asend(httpx.Response(200, headers={"Set-Cookie": f"Session={_SESSION_COOKIE}; Path=/"}, request=login_req))

    assert _cookie_fingerprint(_SESSION_COOKIE) in caplog.text
    await gen.aclose()


async def test_auth_flow_skips_login_when_already_logged_in(session_auth: EapiSessionAuth) -> None:
    """Test that an already-logged-in session skips login and attaches the cookie directly."""
    session_auth.session_cookie = _SESSION_COOKIE

    gen = session_auth.async_auth_flow(request=httpx.Request("POST", _COMMAND_URL))
    cmd_req = await anext(gen)
    assert cmd_req.url.path == "/command-api"
    assert cmd_req.headers.get("Cookie") == f"Session={_SESSION_COOKIE}"

    with pytest.raises(StopAsyncIteration):
        await gen.asend(httpx.Response(200, request=cmd_req))


async def test_auth_flow_waiting_request_skips_login_after_concurrent_login(session_auth: EapiSessionAuth) -> None:
    """Test that a request waiting on login skips its own login after the first login completes."""
    first_gen = session_auth.async_auth_flow(request=httpx.Request("POST", _COMMAND_URL))
    # Start the first auth flow and pause it at the yielded login request.
    first_login_req = await anext(first_gen)
    assert first_login_req.url.path == "/login"

    second_gen = session_auth.async_auth_flow(request=httpx.Request("POST", _COMMAND_URL))
    # Start a second auth flow while the first one still holds the login lock.
    second_request_task = asyncio.create_task(anext(second_gen))
    await asyncio.sleep(0)

    # Resume the first flow with a successful login response; the second flow should then skip its own login.
    first_cmd_req = await first_gen.asend(httpx.Response(200, headers={"Set-Cookie": f"Session={_SESSION_COOKIE}; Path=/"}, request=first_login_req))
    second_cmd_req = await second_request_task

    assert first_cmd_req.url.path == "/command-api"
    assert second_cmd_req.url.path == "/command-api"
    assert first_cmd_req.headers.get("Cookie") == f"Session={_SESSION_COOKIE}"
    assert second_cmd_req.headers.get("Cookie") == f"Session={_SESSION_COOKIE}"

    await first_gen.aclose()
    await second_gen.aclose()


async def test_auth_flow_waiting_request_logs_existing_cookie_fingerprint(session_auth: EapiSessionAuth, caplog: pytest.LogCaptureFixture) -> None:
    """Test that a request waiting on another login logs the existing cookie fingerprint."""
    caplog.set_level(logging.DEBUG, logger="asynceapi._auth")
    first_gen = session_auth.async_auth_flow(request=httpx.Request("POST", _COMMAND_URL))
    first_login_req = await anext(first_gen)

    second_gen = session_auth.async_auth_flow(request=httpx.Request("POST", _COMMAND_URL))
    second_request_task = asyncio.create_task(anext(second_gen))
    await asyncio.sleep(0)

    await first_gen.asend(httpx.Response(200, headers={"Set-Cookie": f"Session={_SESSION_COOKIE}; Path=/"}, request=first_login_req))
    await second_request_task

    assert _cookie_fingerprint(_SESSION_COOKIE) in caplog.text
    await first_gen.aclose()
    await second_gen.aclose()


@pytest.mark.parametrize(
    ("status_code", "expected_exc"),
    [
        (401, EapiAuthenticationError),
        (500, httpx.HTTPStatusError),
        (200, RuntimeError),
    ],
    ids=["401_auth_error", "500_http_error", "200_no_cookie"],
)
async def test_auth_flow_login_failure_raises(
    session_auth: EapiSessionAuth,
    status_code: int,
    expected_exc: type[Exception],
) -> None:
    """Test that a failed login raises the correct exception and leaves state clean."""
    gen = session_auth.async_auth_flow(request=httpx.Request("POST", _COMMAND_URL))
    login_req = await anext(gen)

    with pytest.raises(expected_exc):
        await gen.asend(httpx.Response(status_code, request=login_req))
    assert session_auth.logged_in is False
    assert session_auth.session_cookie is None


async def test_auth_flow_401_clears_matching_cookie(session_auth: EapiSessionAuth) -> None:
    """Test that a 401 on the command request clears the cookie when it matches the one used."""
    session_auth.session_cookie = _SESSION_COOKIE

    gen = session_auth.async_auth_flow(request=httpx.Request("POST", _COMMAND_URL))
    cmd_req = await anext(gen)

    with pytest.raises(EapiAuthenticationError):
        await gen.asend(httpx.Response(401, request=cmd_req))

    assert session_auth.logged_in is False
    assert session_auth.session_cookie is None


async def test_auth_flow_401_preserves_new_cookie(session_auth: EapiSessionAuth) -> None:
    """Test that a 401 does not clear a cookie that was replaced by a concurrent re-login."""
    session_auth.session_cookie = _SESSION_COOKIE

    gen = session_auth.async_auth_flow(request=httpx.Request("POST", _COMMAND_URL))
    cmd_req = await anext(gen)

    new_cookie = "freshcookie99887766"
    session_auth.session_cookie = new_cookie

    with pytest.raises(EapiAuthenticationError):
        await gen.asend(httpx.Response(401, request=cmd_req))

    assert session_auth.session_cookie == new_cookie


async def test_auth_flow_login_401_includes_response_text(session_auth: EapiSessionAuth) -> None:
    """Test that a 401 on login includes the response body in the exception."""
    gen = session_auth.async_auth_flow(request=httpx.Request("POST", _COMMAND_URL))
    login_req = await anext(gen)

    with pytest.raises(EapiAuthenticationError) as exc_info:
        await gen.asend(httpx.Response(401, text="Unauthorized", request=login_req))

    assert exc_info.value.response_text == "Unauthorized"


async def test_auth_flow_session_expired_includes_response_text(session_auth: EapiSessionAuth) -> None:
    """Test that a 401 on the command request includes the response body in the exception."""
    session_auth.session_cookie = _SESSION_COOKIE

    gen = session_auth.async_auth_flow(request=httpx.Request("POST", _COMMAND_URL))
    cmd_req = await anext(gen)

    with pytest.raises(EapiAuthenticationError) as exc_info:
        await gen.asend(httpx.Response(401, text="Session expired", request=cmd_req))

    assert exc_info.value.response_text == "Session expired"
