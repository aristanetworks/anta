"""aioeapi module exceptions."""

from __future__ import annotations

from typing import Any

import httpx


class EapiCommandError(RuntimeError):
    """
    Exception class for EAPI command errors.

    Attributes
    ----------
        failed: the failed command
        errmsg: a description of the failure reason
        errors: the command failure details
        passed: a list of command results of the commands that passed
        not_exec: a list of commands that were not executed
    """

    def __init__(self, failed: str, errors: list[str], errmsg: str, passed: list[str | dict[str, Any]], not_exec: list[dict[str, Any]]) -> None:  # noqa: PLR0913
        """Initialize for the EapiCommandError exception."""
        self.failed = failed
        self.errmsg = errmsg
        self.errors = errors
        self.passed = passed
        self.not_exec = not_exec
        super().__init__()

    def __str__(self) -> str:
        """Return the error message associated with the exception."""
        return self.errmsg


# alias for exception during sending-receiving
EapiTransportError = httpx.HTTPStatusError
