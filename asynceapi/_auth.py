# Copyright (c) 2024-2026 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""asynceapi session-based (cookie) authentication."""

from __future__ import annotations

import asyncio
from http import HTTPStatus
from logging import getLogger
from typing import TYPE_CHECKING

import httpx

from .errors import EapiAuthenticationError

if TYPE_CHECKING:
    from collections.abc import AsyncGenerator, Mapping

LOGGER = getLogger(__name__)


class SessionState:  # pylint: disable=too-few-public-methods
    """Mutable session state for eAPI cookie-based authentication.

    Attributes
    ----------
    logged_in : bool
        True when a valid session cookie is held.
    session_cookie : str | None
        The active session cookie value, or None if not logged in.
    """

    def __init__(self) -> None:
        self.logged_in: bool = False
        self.session_cookie: str | None = None

    def reset(self) -> None:
        """Set ``logged_in`` to False and clear ``session_cookie``."""
        self.logged_in = False
        self.session_cookie = None


# Library-agnostic utilities (no httpx dependency)


def build_login_payload(username: str, password: str) -> dict[str, str]:
    """Build the JSON body for the EOS POST /login endpoint.

    Parameters
    ----------
    username
        The login username.
    password
        The login password.

    Returns
    -------
    dict[str, str]
        JSON-serializable body expected by EOS POST /login.
    """
    return {"username": username, "password": password}


def build_cookie_header(session_cookie: str | None) -> dict[str, str]:
    """Build an HTTP Cookie header dict for the given session cookie value.

    Parameters
    ----------
    session_cookie
        The session cookie value returned by EOS after a successful login,
        or None if no session is active.

    Returns
    -------
    dict[str, str]
        ``{"Cookie": "Session=<value>"}`` when a cookie is present, empty dict otherwise.
    """
    return {"Cookie": f"Session={session_cookie}"} if session_cookie else {}


def get_session_cookie(cookies: Mapping[str, str]) -> str | None:
    """Extract the Session cookie value from an httpx response cookie mapping.

    Parameters
    ----------
    cookies
        The response cookie mapping (e.g. ``response.cookies``).

    Returns
    -------
    str | None
        The Session cookie value, or None if the cookie is absent.
    """
    return cookies.get("Session")


def validate_login_status(status_code: int, host: str) -> None:
    """Raise EapiAuthenticationError if the login response returned HTTP 401.

    Parameters
    ----------
    status_code
        The HTTP status code from the /login response.
    host
        The target device hostname, used in the exception message.

    Raises
    ------
    EapiAuthenticationError
        When ``status_code`` is 401 Unauthorized.
    """
    if status_code == HTTPStatus.UNAUTHORIZED:
        raise EapiAuthenticationError(host)


class EapiSessionAuth(httpx.Auth):
    """httpx.Auth that drives eAPI cookie-session authentication.

    Credentials are stored here, not on the device, so they never appear in
    device repr(), logs, or tracebacks.
    Login (POST /login) is performed lazily before the first request.
    An asyncio.Lock with double-checked locking prevents concurrent login stampedes
    when multiple coroutines share the same auth instance.
    A mid-session 401 triggers one re-login attempt inside async_auth_flow.

    Attributes
    ----------
    logged_in : bool
        True when a valid session cookie is held.
    session_cookie : str | None
        The active session cookie value, or None if not logged in.
    cookie_header : dict[str, str]
        Cookie header dict ready to attach to an outgoing request.
    """

    def __init__(self, username: str, password: str, login_url: str, host: str) -> None:
        """Initialize EapiSessionAuth with credentials and the absolute login URL.

        Parameters
        ----------
        username
            The login username.
        password
            The login password.
        login_url
            Absolute URL for the EOS /login endpoint (e.g. ``https://host:443/login``).
        host
            The device hostname; used in error messages and repr.
        """
        self._username = username
        self._password = password
        self._login_url = login_url
        self._host = host
        self._state = SessionState()
        self._lock = asyncio.Lock()

    def __repr__(self) -> str:
        """Mask credentials — safe to log or repr."""
        return f"EapiSessionAuth(host={self._host!r}, logged_in={self._state.logged_in})"

    @property
    def logged_in(self) -> bool:
        """Return True if a session cookie is currently held."""
        return self._state.logged_in

    @property
    def session_cookie(self) -> str | None:
        """Return the active session cookie value, or None if not logged in."""
        return self._state.session_cookie

    @property
    def cookie_header(self) -> dict[str, str]:
        """Return a Cookie header dict for the current session, or empty dict."""
        return build_cookie_header(self._state.session_cookie)

    def reset(self) -> None:
        """Invalidate the current session.

        Called by Device.logout() and on mid-session 401 before re-login.
        Delegates to SessionState.reset() so state management stays co-located.
        """
        self._state.reset()

    def _build_login_request(self) -> httpx.Request:
        """Construct the POST /login request with credentials as a JSON body.

        Returns
        -------
        httpx.Request
            A POST request to the login URL with username and password as JSON.
        """
        return httpx.Request("POST", self._login_url, json=build_login_payload(self._username, self._password))

    def _handle_login_response(self, response: httpx.Response) -> None:
        """Validate the login response and store the session cookie.

        Parameters
        ----------
        response
            The HTTP response from the POST /login endpoint.

        Raises
        ------
        EapiAuthenticationError
            If the response status code is 401 Unauthorized.
        httpx.HTTPStatusError
            If the response status code is any other non-2xx value.
        RuntimeError
            If the login response is 2xx but contains no Session cookie.
        """
        validate_login_status(response.status_code, self._host)
        response.raise_for_status()
        cookie = get_session_cookie(response.cookies)
        if not cookie:
            msg = f"Login to {self._host!r} succeeded (HTTP {response.status_code}) but the response contained no Session cookie."
            raise RuntimeError(msg)
        self._state.session_cookie = cookie
        self._state.logged_in = True

    def _attach_cookie(self, request: httpx.Request) -> None:
        """Attach the active session cookie to an outgoing request header in place."""
        if self._state.session_cookie:
            request.headers["Cookie"] = f"Session={self._state.session_cookie}"

    async def async_auth_flow(
        self,
        request: httpx.Request,
    ) -> AsyncGenerator[httpx.Request, httpx.Response]:
        """Drive the full login → request → 401-retry flow.

        httpx calls this generator for every outgoing request. Each ``yield``
        sends a request through the transport and receives the response back,
        allowing auth sub-requests (e.g. POST /login) to be interleaved without
        breaking httpx's transport machinery.

        Because httpx does not merge cookies from auth-flow sub-requests into
        the client cookie jar, the Session cookie is extracted manually and
        attached explicitly to every real request via the ``Cookie`` header.

        Parameters
        ----------
        request
            The outgoing request that triggered the auth flow.
        """
        # Phase 1: lazy login with double-checked locking
        if not self._state.logged_in:
            async with self._lock:
                LOGGER.debug("[AUTH] acquiring lock and logging in")
                if not self._state.logged_in:
                    login_response = yield self._build_login_request()
                    self._handle_login_response(login_response)
                    LOGGER.debug("[AUTH] login OK — cookie=%s...", (self._state.session_cookie or "")[:8])

        # Phase 2: attach session cookie and dispatch the real request
        self._attach_cookie(request)
        response = yield request

        # Phase 3: mid-session 401 — re-login once and retry
        if response.status_code == HTTPStatus.UNAUTHORIZED:
            LOGGER.debug("[AUTH] got 401 — resetting session, will re-login")
            self.reset()
            async with self._lock:
                if not self._state.logged_in:
                    login_response = yield self._build_login_request()
                    self._handle_login_response(login_response)
                    LOGGER.debug("[AUTH] re-login OK — retrying original request")
            self._attach_cookie(request)
            yield request
