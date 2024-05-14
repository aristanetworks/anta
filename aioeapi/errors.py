from __future__ import annotations

import httpx

from typing import Any


class EapiCommandError(RuntimeError):
    """
    Exception class for EAPI command errors

    Attributes
    ----------
    failed: str - the failed command
    errmsg: str - a description of the failure reason
    errors: list[str] - the command failure details
    passed: list[dict] - a list of command results of the commands that passed
    not_exec: list[str] - a list of commands that were not executed
    """

    def __init__(self, failed: str, errors: list[str], errmsg: str, passed: list[str | dict[str, Any]], not_exec: list[dict[str, Any]]):
        """Initializer for the EapiCommandError exception"""
        self.failed = failed
        self.errmsg = errmsg
        self.errors = errors
        self.passed = passed
        self.not_exec = not_exec
        super().__init__()

    def __str__(self) -> str:
        """returns the error message associated with the exception"""
        return self.errmsg


# alias for exception during sending-receiving
EapiTransportError = httpx.HTTPStatusError
