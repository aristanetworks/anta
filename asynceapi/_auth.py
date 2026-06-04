# Copyright (c) 2026 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""asynceapi session-based (cookie) authentication."""

from __future__ import annotations

import asyncio
from http import HTTPStatus
from logging import getLogger
from typing import TYPE_CHECKING

import httpx

from .errors import EapiAsyncOnlyError, EapiAuthenticationError

if TYPE_CHECKING:
    from collections.abc import AsyncGenerator, Generator

LOGGER = getLogger(__name__)


class SessionState:  # pylint: disable=too-few-public-methods
    """Mutable session state shared across coroutines."""

    def __init__(self) -> None:
        self.logged_in: bool = False
        self.session_cookie: str | None = None

    def reset(self) -> None:
        """Clear session state."""
        self.logged_in = False
        self.session_cookie = None


class EapiSessionAuth(httpx.Auth):
    """httpx.Auth implementation for eAPI cookie-session authentication.

    Performs a single login on the first request and attaches the session cookie thereafter.
    A 401 on any request raises EapiAuthenticationError immediately — re-login is not supported.
    """

    def __init__(self, username: str, password: str, login_url: str, host: str) -> None:
        self._username = username
        self._password = password
        self._login_url = login_url
        self._host = host
        self._state = SessionState()
        self._lock = asyncio.Lock()

    def __repr__(self) -> str:
        return f"EapiSessionAuth(host={self._host!r}, logged_in={self._state.logged_in})"

    @property
    def logged_in(self) -> bool:
        """True if a session cookie is currently held."""
        return self._state.logged_in

    @property
    def session_cookie(self) -> str | None:
        """Active session cookie value, or None."""
        return self._state.session_cookie

    @property
    def cookie_header(self) -> dict[str, str]:
        """Cookie header dict for the current session, or empty dict."""
        return {"Cookie": f"Session={self._state.session_cookie}"} if self._state.session_cookie else {}

    async def reset(self) -> None:
        """Invalidate the current session, waiting for any in-progress login to complete first."""
        async with self._lock:
            self._state.reset()

    def _build_login_request(self) -> httpx.Request:
        """Build the POST /login request with credentials in the JSON body."""
        return httpx.Request("POST", self._login_url, json={"username": self._username, "password": self._password})

    def _handle_login_response(self, response: httpx.Response) -> None:
        """Parse the login response, update session state, and raise on failure."""
        if response.status_code == HTTPStatus.UNAUTHORIZED:
            raise EapiAuthenticationError(self._host)
        response.raise_for_status()
        cookie = response.cookies.get("Session")
        if not cookie:
            msg = f"Login to {self._host!r} succeeded (HTTP {response.status_code}) but the response contained no Session cookie."
            raise RuntimeError(msg)
        self._state.session_cookie = cookie
        self._state.logged_in = True

    def sync_auth_flow(self, request: httpx.Request) -> Generator[httpx.Request, httpx.Response, None]:  # noqa: ARG002
        """Not supported — this auth class requires an async httpx client."""
        raise EapiAsyncOnlyError

    def _attach_cookie(self, request: httpx.Request) -> None:
        """Attach the session cookie header to the outgoing request."""
        if self._state.session_cookie:
            request.headers["Cookie"] = f"Session={self._state.session_cookie}"

    async def async_auth_flow(
        self,
        request: httpx.Request,
    ) -> AsyncGenerator[httpx.Request, httpx.Response]:
        """Login lazily, attach the session cookie, then dispatch the request."""
        # Lazy login with double-checked locking
        if not self._state.logged_in:
            async with self._lock:
                LOGGER.debug("[AUTH] acquiring lock and logging in")
                if not self._state.logged_in:
                    login_response = yield self._build_login_request()
                    self._handle_login_response(login_response)
                    LOGGER.debug("[AUTH] login OK — cookie=%s...", (self._state.session_cookie or "")[:8])

        # Attach session cookie and dispatch the real request
        self._attach_cookie(request)
        response = yield request

        # Surface session expiry as a clear error — retry with re-login is not yet implemented
        if response.status_code == HTTPStatus.UNAUTHORIZED:
            raise EapiAuthenticationError(self._host)
