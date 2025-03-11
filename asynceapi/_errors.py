# Copyright (c) 2024-2025 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Exceptions for the asynceapi package."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from asynceapi._models import EapiResponse


class EapiReponseError(Exception):
    """Exception raised when an eAPI response contains errors.

    Attributes
    ----------
    response : EapiResponse
        The eAPI response that contains the error.
    """

    def __init__(self, response: EapiResponse) -> None:
        """Initialize the EapiReponseError exception."""
        self.response = response

        # Build a descriptive error message
        message = "Error in eAPI response"

        if response.error_code is not None:
            message += f" (code: {response.error_code})"

        if response.error_message is not None:
            message += f": {response.error_message}"

        super().__init__(message)
