# Copyright (c) 2023-2024 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Models related to anta.result_manager module."""

from __future__ import annotations

from pydantic import BaseModel

from anta.custom_types import TestStatus


class TestResult(BaseModel):
    """Describe the result of a test from a single device.

    Attributes
    ----------
        name: Device name where the test has run.
        test: Test name runs on the device.
        categories: List of categories the TestResult belongs to, by default the AntaTest categories.
        description: TestResult description, by default the AntaTest description.
        result: Result of the test. Can be one of "unset", "success", "failure", "error" or "skipped".
        messages: Message to report after the test if any.
        custom_field: Custom field to store a string for flexibility in integrating with ANTA

    """

    name: str
    test: str
    categories: list[str]
    description: str
    result: TestStatus = "unset"
    messages: list[str] = []
    custom_field: str | None = None

    def is_success(self, message: str | None = None) -> None:
        """Set status to success.

        Args:
        ----
            message: Optional message related to the test

        """
        self._set_status("success", message)

    def is_failure(self, message: str | None = None) -> None:
        """Set status to failure.

        Args:
        ----
            message: Optional message related to the test

        """
        self._set_status("failure", message)

    def is_skipped(self, message: str | None = None) -> None:
        """Set status to skipped.

        Args:
        ----
            message: Optional message related to the test

        """
        self._set_status("skipped", message)

    def is_error(self, message: str | None = None) -> None:
        """Set status to error.

        Args:
        ----
            message: Optional message related to the test

        """
        self._set_status("error", message)

    def _set_status(self, status: TestStatus, message: str | None = None) -> None:
        """Set status and insert optional message.

        Args:
        ----
            status: status of the test
            message: optional message

        """
        self.result = status
        if message is not None:
            self.messages.append(message)

    def __str__(self) -> str:
        """Return a human readable string of this TestResult."""
        return f"Test '{self.test}' (on '{self.name}'): Result '{self.result}'\nMessages: {self.messages}"
