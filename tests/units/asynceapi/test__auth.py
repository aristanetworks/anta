# Copyright (c) 2024-2026 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Unit tests for asynceapi._auth — pure functions and classes tested in isolation without Device."""

from __future__ import annotations

import json

import httpx
import pytest

from asynceapi._auth import (
    EapiSessionAuth,
    SessionState,
    build_cookie_header,
    build_login_payload,
    get_session_cookie,
    validate_login_status,
)
from asynceapi.errors import EapiAuthenticationError

# ---------------------------------------------------------------------------
# Shared constants
# ---------------------------------------------------------------------------

_HOST = "192.0.2.1"
_PORT = 443
_PROTO = "https"
_USERNAME = "admin"
_PASSWORD = "arista123"

_LOGIN_URL = f"{_PROTO}://{_HOST}:{_PORT}/login"
_COMMAND_URL = f"{_PROTO}://{_HOST}:{_PORT}/command-api"

_COOKIE_FIRST_LOGIN = "aabbccdd11223344"  # Cookie issued on initial login
_COOKIE_RELOGIN = "99887766aabbccdd"  # Cookie issued after mid-session 401 re-login

# ---------------------------------------------------------------------------
# Fixture
# ---------------------------------------------------------------------------


@pytest.fixture
def session_auth() -> EapiSessionAuth:
    """Return a fresh EapiSessionAuth with known credentials."""
    return EapiSessionAuth(username=_USERNAME, password=_PASSWORD, login_url=_LOGIN_URL, host=_HOST)


# ---------------------------------------------------------------------------
# Pure functions
# ---------------------------------------------------------------------------


class TestBuildLoginPayload:
    """Test cases for build_login_payload()."""

    def test_returns_dict_with_username_and_password(self) -> None:
        """Test that both keys are present in the returned dict with correct values."""
        assert build_login_payload(_USERNAME, _PASSWORD) == {"username": _USERNAME, "password": _PASSWORD}


class TestBuildCookieHeader:
    """Test cases for build_cookie_header()."""

    @pytest.mark.parametrize(
        ("session_cookie", "expected"),
        [
            (_COOKIE_FIRST_LOGIN, {"Cookie": f"Session={_COOKIE_FIRST_LOGIN}"}),
            (None, {}),
        ],
        ids=["with_cookie", "no_cookie"],
    )
    def test_returns_correct_header(self, session_cookie: str | None, expected: dict) -> None:
        """Test that a non-empty cookie produces a Cookie header and that None produces an empty dict."""
        assert build_cookie_header(session_cookie=session_cookie) == expected


class TestGetSessionCookie:
    """Test cases for get_session_cookie()."""

    @pytest.mark.parametrize(
        ("cookies", "expected"),
        [
            ({"Session": _COOKIE_FIRST_LOGIN}, _COOKIE_FIRST_LOGIN),
            ({}, None),
        ],
        ids=["key_present", "key_absent"],
    )
    def test_extracts_session_cookie(self, cookies: dict, expected: str | None) -> None:
        """Test that Session key is returned when present and None when absent."""
        assert get_session_cookie(cookies=cookies) == expected


class TestValidateLoginStatus:
    """Test cases for validate_login_status()."""

    @pytest.mark.parametrize("status_code", [200, 403], ids=["200_ok", "403_forbidden"])
    def test_does_not_raise_on_non_401(self, status_code: int) -> None:
        """Test that only 401 triggers EapiAuthenticationError — including auth-adjacent codes like 403."""
        assert validate_login_status(status_code, _HOST) is None

    def test_raises_on_401_with_correct_host(self) -> None:
        """Test that 401 raises EapiAuthenticationError carrying the device host."""
        with pytest.raises(EapiAuthenticationError) as exc_info:
            validate_login_status(401, _HOST)
        assert exc_info.value.host == _HOST


# ---------------------------------------------------------------------------
# SessionState
# ---------------------------------------------------------------------------


class TestSessionState:
    """Test cases for the SessionState class."""

    def test_initial_state(self) -> None:
        """Test that a fresh SessionState starts with logged_in=False and no cookie."""
        state = SessionState()
        assert state.logged_in is False
        assert state.session_cookie is None

    def test_reset_clears_state(self) -> None:
        """Test that reset() sets logged_in=False and clears session_cookie."""
        state = SessionState()
        state.logged_in = True
        state.session_cookie = _COOKIE_FIRST_LOGIN
        state.reset()
        assert state.logged_in is False
        assert state.session_cookie is None


# ---------------------------------------------------------------------------
# EapiSessionAuth — properties and non-async methods
# ---------------------------------------------------------------------------


class TestEapiSessionAuth:
    """Test cases for EapiSessionAuth properties and non-async methods."""

    def test_repr_masks_credentials(self, session_auth: EapiSessionAuth) -> None:
        """Test that repr shows the host but never exposes username or password."""
        auth_repr = repr(session_auth)
        assert _USERNAME not in auth_repr
        assert _PASSWORD not in auth_repr
        assert _HOST in auth_repr

    def test_properties_reflect_state(self, session_auth: EapiSessionAuth) -> None:
        """Test that logged_in, session_cookie, and cookie_header all read live from internal state."""
        session_auth._state.logged_in = True  # type: ignore[protected-access]
        session_auth._state.session_cookie = _COOKIE_FIRST_LOGIN  # type: ignore[protected-access]
        assert session_auth.logged_in is True
        assert session_auth.session_cookie == _COOKIE_FIRST_LOGIN
        assert session_auth.cookie_header == {"Cookie": f"Session={_COOKIE_FIRST_LOGIN}"}

    def test_build_login_request(self, session_auth: EapiSessionAuth) -> None:
        """Test that _build_login_request() returns POST to the login URL with credentials in the body."""
        req = session_auth._build_login_request()  # type: ignore[protected-access]
        assert req.method == "POST"
        assert req.url.path == "/login"
        assert json.loads(req.content) == {"username": _USERNAME, "password": _PASSWORD}

    def test_handle_login_response_200_with_cookie_sets_state(self, session_auth: EapiSessionAuth) -> None:
        """Test that a 200 login response with a Session cookie sets logged_in=True and stores the cookie."""
        # httpx requires every Response to carry its originating Request
        login_req = httpx.Request("POST", _LOGIN_URL)
        response = httpx.Response(200, headers={"Set-Cookie": f"Session={_COOKIE_FIRST_LOGIN}; Path=/"}, request=login_req)
        session_auth._handle_login_response(response=response)  # type: ignore[protected-access]
        assert session_auth.logged_in is True
        assert session_auth.session_cookie == _COOKIE_FIRST_LOGIN

    @pytest.mark.parametrize(
        ("status_code", "expected_exc"),
        [
            (401, EapiAuthenticationError),
            (500, httpx.HTTPStatusError),
        ],
        ids=["401_auth_error", "500_http_error"],
    )
    def test_handle_login_error_response_raises_and_leaves_state_clean(
        self,
        session_auth: EapiSessionAuth,
        status_code: int,
        expected_exc: type[Exception],
    ) -> None:
        """Test that a failed login response raises the correct exception and leaves state clean."""
        login_req = httpx.Request("POST", _LOGIN_URL)  # httpx requires every Response to carry its Request
        with pytest.raises(expected_exc):
            session_auth._handle_login_response(httpx.Response(status_code, request=login_req))  # type: ignore[protected-access]
        assert session_auth.logged_in is False
        assert session_auth.session_cookie is None

    def test_handle_login_response_200_without_cookie_raises(self, session_auth: EapiSessionAuth) -> None:
        """Test that a 2xx response with no Session cookie raises RuntimeError and leaves state clean."""
        login_req = httpx.Request("POST", _LOGIN_URL)
        with pytest.raises(RuntimeError, match="no Session cookie"):
            session_auth._handle_login_response(httpx.Response(200, request=login_req))  # type: ignore[protected-access]
        assert session_auth.logged_in is False
        assert session_auth.session_cookie is None

    @pytest.mark.parametrize(
        ("cookie", "expected_cookie_header"),
        [
            (_COOKIE_FIRST_LOGIN, f"Session={_COOKIE_FIRST_LOGIN}"),
            (None, None),
        ],
        ids=["cookie_attached", "no_cookie_no_header"],
    )
    def test_attach_cookie(self, session_auth: EapiSessionAuth, cookie: str | None, expected_cookie_header: str | None) -> None:
        """Test that _attach_cookie() sets Cookie header when cookie is present and skips when absent."""
        session_auth._state.session_cookie = cookie  # type: ignore[protected-access]
        request = httpx.Request("POST", _COMMAND_URL)
        session_auth._attach_cookie(request=request)  # type: ignore[protected-access]
        assert request.headers.get("Cookie") == expected_cookie_header


# ---------------------------------------------------------------------------
# EapiSessionAuth — async_auth_flow generator
# ---------------------------------------------------------------------------


class TestEapiSessionAuthFlow:
    """Test cases for EapiSessionAuth.async_auth_flow() generator."""

    async def test_not_logged_in_yields_login_then_attaches_cookie(self, session_auth: EapiSessionAuth) -> None:
        """Test full initial login flow: first yield is POST /login, second yield carries the first-login cookie."""
        # async_auth_flow is an async generator — each yield sends a request through httpx transport and
        # receives the response back. __anext__() starts the generator and returns the first yielded request;
        # asend(response) resumes it with that response and advances to the next yield.
        request = httpx.Request("POST", _COMMAND_URL)
        gen = session_auth.async_auth_flow(request=request)

        # Phase 1: not logged in — generator must yield a login request before the real one
        login_req = await gen.__anext__()
        assert login_req.url.path == "/login"

        # Phase 2: send login response back into the generator — next yield must be the real request with cookie
        # login_req is attached to the response because httpx requires every Response to reference its Request
        login_response = httpx.Response(200, headers={"Set-Cookie": f"Session={_COOKIE_FIRST_LOGIN}; Path=/"}, request=login_req)
        cmd_req = await gen.asend(login_response)
        assert cmd_req.url.path == "/command-api"
        assert cmd_req.headers.get("Cookie") == f"Session={_COOKIE_FIRST_LOGIN}"
        await gen.aclose()  # release generator resources

    async def test_already_logged_in_skips_login(self, session_auth: EapiSessionAuth) -> None:
        """Test that if already logged in, the first yield is the real request — no login request sent.

        Also verifies that a non-401 command response does not trigger re-login (generator finishes cleanly).
        """
        session_auth._state.logged_in = True  # type: ignore[protected-access]
        session_auth._state.session_cookie = _COOKIE_FIRST_LOGIN  # type: ignore[protected-access]

        request = httpx.Request("POST", _COMMAND_URL)
        gen = session_auth.async_auth_flow(request=request)
        cmd_req = await gen.__anext__()  # skips login — first yield is the real command request

        assert cmd_req.url.path == "/command-api"
        assert cmd_req.headers.get("Cookie") == f"Session={_COOKIE_FIRST_LOGIN}"

        # Send a non-401 response — generator must finish with no further yields (no re-login attempt).
        # StopAsyncIteration means the generator is exhausted, which is the correct behavior.
        with pytest.raises(StopAsyncIteration):
            await gen.asend(httpx.Response(200, request=cmd_req))

    async def test_mid_session_401_triggers_relogin_with_fresh_cookie(self, session_auth: EapiSessionAuth) -> None:
        """Test that a 401 on the real request triggers re-login and the retry carries the relogin cookie."""
        session_auth._state.logged_in = True  # type: ignore[protected-access]
        session_auth._state.session_cookie = _COOKIE_FIRST_LOGIN  # type: ignore[protected-access]

        request = httpx.Request("POST", _COMMAND_URL)
        gen = session_auth.async_auth_flow(request=request)

        # Phase 1: generator skips login (already logged in) and yields the command request
        cmd_req = await gen.__anext__()

        # Phase 2: simulate server rejecting the command with 401 (session expired)
        # generator must respond by yielding a fresh login request, not giving up
        relogin_req = await gen.asend(httpx.Response(401, request=cmd_req))
        assert relogin_req.url.path == "/login"  # confirms generator decided to re-login

        # Phase 3: simulate successful re-login returning a new cookie
        relogin_response = httpx.Response(
            200,
            headers={"Set-Cookie": f"Session={_COOKIE_RELOGIN}; Path=/"},
            request=relogin_req,
        )
        # generator must yield the original command again — correct endpoint and fresh cookie
        retry_req = await gen.asend(relogin_response)
        assert retry_req.url.path == "/command-api"  # retries the original request, not a new login
        assert retry_req.headers.get("Cookie") == f"Session={_COOKIE_RELOGIN}"  # stale cookie must not be used
        await gen.aclose()

    @pytest.mark.parametrize(
        ("status_code", "expected_exc"),
        [
            (401, EapiAuthenticationError),
            (200, RuntimeError),  # 200 but no Session cookie in response
        ],
        ids=["login_401", "login_200_no_cookie"],
    )
    async def test_auth_flow_initial_login_failure_propagates(
        self,
        session_auth: EapiSessionAuth,
        status_code: int,
        expected_exc: type[Exception],
    ) -> None:
        """Test that login failures during initial login propagate the correct exception and leave state clean."""
        request = httpx.Request("POST", _COMMAND_URL)
        gen = session_auth.async_auth_flow(request=request)

        # Phase 1: get the login request from the generator
        login_req = await gen.__anext__()

        # Phase 2: send back the bad login response — exception must propagate out of the generator
        with pytest.raises(expected_exc):
            await gen.asend(httpx.Response(status_code, request=login_req))
        assert session_auth.logged_in is False
        assert session_auth.session_cookie is None

    async def test_auth_flow_relogin_401_propagates(self, session_auth: EapiSessionAuth) -> None:
        """Test that a 401 during re-login propagates EapiAuthenticationError and leaves state clean."""
        session_auth._state.logged_in = True  # type: ignore[protected-access]
        session_auth._state.session_cookie = _COOKIE_FIRST_LOGIN  # type: ignore[protected-access]

        request = httpx.Request("POST", _COMMAND_URL)
        gen = session_auth.async_auth_flow(request=request)

        # Phase 1: generator skips login (already logged in), yields the command request
        cmd_req = await gen.__anext__()

        # Phase 2: command gets 401 — generator resets state and yields a re-login request
        relogin_req = await gen.asend(httpx.Response(401, request=cmd_req))
        assert relogin_req.url.path == "/login"

        # Phase 3: re-login also gets 401 — EapiAuthenticationError must propagate out
        with pytest.raises(EapiAuthenticationError):
            await gen.asend(httpx.Response(401, request=relogin_req))
        assert session_auth.logged_in is False
        assert session_auth.session_cookie is None
