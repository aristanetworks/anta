# Copyright (c) 2026 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""asynceapi session-based (cookie) authentication."""

from __future__ import annotations

import asyncio
from http import HTTPStatus
from typing import TYPE_CHECKING

import httpx

from .errors import EapiAsyncOnlyError, EapiAuthenticationError

if TYPE_CHECKING:
    from collections.abc import AsyncGenerator, Generator


class EapiSessionAuth(httpx.Auth):
    """httpx.Auth implementation for eAPI cookie-session authentication.

    Performs a single login on the first request and attaches the session cookie thereafter.
    A 401 on any request raises EapiAuthenticationError immediately.
    """

    def __init__(self, host: str, username: str, password: str, login_url: str) -> None:
        """Initialize EapiSessionAuth with credentials and connection details."""
        self._host = host
        self._username = username
        self._password = password
        self._login_url = login_url
        self.session_cookie: str | None = None
        self._lock = asyncio.Lock()

    @property
    def logged_in(self) -> bool:
        """Return whether session authentication currently has a cookie."""
        return self.session_cookie is not None

    def __repr__(self) -> str:
        return f"EapiSessionAuth(host={self._host!r}, logged_in={self.logged_in})"

    async def reset(self) -> None:
        """Invalidate the current session, waiting for any in-progress login to complete first."""
        async with self._lock:
            self.session_cookie = None

    def sync_auth_flow(self, request: httpx.Request) -> Generator[httpx.Request, httpx.Response, None]:
        """Not supported — this auth class requires an async httpx client."""
        _ = request
        raise EapiAsyncOnlyError

    async def async_auth_flow(
        self,
        request: httpx.Request,
    ) -> AsyncGenerator[httpx.Request, httpx.Response]:
        """Authenticate if needed, attach the session cookie, and dispatch the request."""
        # Login on first use with double-checked locking
        if not self.logged_in:
            async with self._lock:
                if not self.logged_in:
                    # Send login request
                    login_request = httpx.Request("POST", self._login_url, json={"username": self._username, "password": self._password})
                    login_response = yield login_request

                    # Validate response
                    if login_response.status_code == HTTPStatus.UNAUTHORIZED:
                        raise EapiAuthenticationError(self._host)  # bad credentials
                    login_response.raise_for_status()

                    # Extract session cookie
                    cookie = login_response.cookies.get("Session")
                    if not cookie:
                        msg = f"Login to {self._host!r} succeeded (HTTP {login_response.status_code}) but the response contained no Session cookie."
                        raise RuntimeError(msg)  # device bug or misconfiguration

                    # Update state
                    self.session_cookie = cookie

        # Attach session cookie and dispatch the real request
        request.headers["Cookie"] = f"Session={self.session_cookie}"
        response = yield request

        if response.status_code == HTTPStatus.UNAUTHORIZED:
            raise EapiAuthenticationError(self._host)  # session expired
