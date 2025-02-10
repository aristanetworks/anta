# Copyright (c) 2024-2025 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
# Initially written by Jeremy Schulman at https://github.com/jeremyschulman/aio-eapi
"""asynceapi module exceptions."""

from __future__ import annotations

from typing import TYPE_CHECKING

import httpx

if TYPE_CHECKING:
    from ._types import EapiComplexCommand, EapiJsonOutput, EapiSimpleCommand, EapiTextOutput


class EapiCommandError(RuntimeError):
    """Exception class for eAPI command errors.

    Attributes
    ----------
        failed: the failed command
        errmsg: a description of the failure reason
        errors: the command failure details
        passed: a list of command results of the commands that passed
        not_exec: a list of commands that were not executed
    """

    def __init__(
        self,
        failed: str,
        errors: list[str],
        errmsg: str,
        passed: list[EapiJsonOutput] | list[EapiTextOutput],
        not_exec: list[EapiSimpleCommand | EapiComplexCommand],
    ) -> None:
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
