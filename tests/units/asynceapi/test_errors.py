# Copyright (c) 2024-2026 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Unit tests for the asynceapi.errors module."""

from __future__ import annotations

import httpx
import pytest

from asynceapi.errors import EapiAuthenticationError, EapiCommandError, EapiTransportError


class TestEapiAuthenticationError:
    """Test cases for the EapiAuthenticationError exception class."""

    def test_host_stored_and_message_format(self) -> None:
        """Test that .host is stored verbatim and str(exc) contains the host, HTTP 401 status, and credentials hint."""
        exc = EapiAuthenticationError("192.0.2.1")
        assert exc.host == "192.0.2.1"
        message = str(exc)
        assert "192.0.2.1" in message
        assert "HTTP 401" in message
        assert "credentials" in message

    def test_is_runtime_error(self) -> None:
        """Test that EapiAuthenticationError is a RuntimeError subclass."""
        assert isinstance(EapiAuthenticationError("192.0.2.1"), RuntimeError)


class TestEapiCommandError:
    """Test cases for the EapiCommandError exception class."""

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
    def test_all_attributes_and_str(
        self,
        failed: str,
        errors: list[str],
        errmsg: str,
        passed: list,
        not_exec: list,
    ) -> None:
        """Test that all attributes are stored correctly and str(exc) returns errmsg."""
        exc = EapiCommandError(
            failed=failed,
            errors=errors,
            errmsg=errmsg,
            passed=passed,
            not_exec=not_exec,
        )
        assert exc.failed == failed
        assert exc.errors == errors
        assert exc.errmsg == errmsg
        assert exc.passed == passed
        assert exc.not_exec == not_exec
        assert str(exc) == errmsg

    def test_is_runtime_error(self) -> None:
        """Test that EapiCommandError is a RuntimeError subclass."""
        exc = EapiCommandError(failed="cmd", errors=["err"], errmsg="msg", passed=[], not_exec=[])
        assert isinstance(exc, RuntimeError)


class TestEapiTransportError:  # pylint: disable=too-few-public-methods
    """Test cases for the EapiTransportError alias."""

    def test_is_alias_for_httpx_http_status_error(self) -> None:
        """Test that EapiTransportError is exactly httpx.HTTPStatusError, not a subclass or copy."""
        assert EapiTransportError is httpx.HTTPStatusError
