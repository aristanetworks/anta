# Copyright (c) 2026 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Unit tests for the asynceapi.errors module."""

from __future__ import annotations

import httpx
import pytest

from asynceapi.errors import EapiAuthenticationError, EapiCommandError, EapiTransportError


def test_eapi_authentication_error_host_and_message() -> None:
    """Test that EapiAuthenticationError stores host and includes it with HTTP 401 context in the message."""
    exc = EapiAuthenticationError("192.0.2.1")
    assert exc.host == "192.0.2.1"
    message = str(exc)
    assert "192.0.2.1" in message
    assert "HTTP 401" in message


def test_eapi_authentication_error_is_runtime_error() -> None:
    """Test that EapiAuthenticationError is a subclass of RuntimeError."""
    assert isinstance(EapiAuthenticationError("192.0.2.1"), RuntimeError)


@pytest.mark.parametrize(
    ("failed", "errors", "errmsg", "passed", "not_exec"),
    [
        (
            "show bad-command",
            ["Invalid input (at token 1: 'bad-command')"],
            "CLI command 2 of 3 'show bad-command' failed: invalid command",
            [{"hostname": "switch1"}],
            ["show clock"],
        ),
        (
            "show version",
            ["err1", "err2", "err3"],
            "CLI command 1 of 1 failed",
            [],
            [],
        ),
    ],
    ids=["mid_sequence_failure", "first_cmd_fails_multiple_errors"],
)
def test_eapi_command_error_attributes_and_str(
    failed: str,
    errors: list[str],
    errmsg: str,
    passed: list,
    not_exec: list,
) -> None:
    """Test that EapiCommandError stores all constructor attributes and str() returns errmsg."""
    exc = EapiCommandError(failed=failed, errors=errors, errmsg=errmsg, passed=passed, not_exec=not_exec)
    assert exc.failed == failed
    assert exc.errors == errors
    assert exc.errmsg == errmsg
    assert exc.passed == passed
    assert exc.not_exec == not_exec
    assert str(exc) == errmsg


def test_eapi_command_error_is_runtime_error() -> None:
    """Test that EapiCommandError is a subclass of RuntimeError."""
    exc = EapiCommandError(failed="cmd", errors=["err"], errmsg="msg", passed=[], not_exec=[])
    assert isinstance(exc, RuntimeError)


def test_eapi_transport_error_is_alias_for_httpx_http_status_error() -> None:
    """Test that EapiTransportError is the same class as httpx.HTTPStatusError."""
    assert EapiTransportError is httpx.HTTPStatusError
