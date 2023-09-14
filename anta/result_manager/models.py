# Copyright (c) 2023 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Models related to anta.result_manager module."""
from __future__ import annotations

from collections.abc import Iterator

# Need to keep List for pydantic in 3.8
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, RootModel

from anta.custom_types import TestStatus


class TestResult(BaseModel):
    """
    Describe the result of a test from a single device.

    Attributes:
        name: Device name where the test has run.
        test: Test name runs on the device.
        categories: List of categories the TestResult belongs to, by default the AntaTest categories.
        description: TestResult description, by default the AntaTest description.
        results: Result of the test. Can be one of ["unset", "success", "failure", "error", "skipped"].
        message: Message to report after the test if any.
        error: Exception object if the test result is "error" and an Exception occured
        custom_field: Custom field to store a string for flexibility in integrating with ANTA
    """

    # This is required if we want to keep an Exception object in the error field
    model_config = ConfigDict(arbitrary_types_allowed=True)

    name: str
    test: str
    categories: List[str]
    description: str
    result: TestStatus = "unset"
    messages: List[str] = []
    error: Optional[Exception] = None
    custom_field: Optional[str] = None

    def is_success(self, message: str | None = None) -> None:
        """
        Helper to set status to success

        Args:
            message: Optional message related to the test
        """
        self._set_status("success", message)

    def is_failure(self, message: str | None = None) -> None:
        """
        Helper to set status to failure

        Args:
            message: Optional message related to the test
        """
        self._set_status("failure", message)

    def is_skipped(self, message: str | None = None) -> None:
        """
        Helper to set status to skipped

        Args:
            message: Optional message related to the test
        """
        self._set_status("skipped", message)

    def is_error(self, message: str | None = None, exception: Exception | None = None) -> None:
        """
        Helper to set status to error

        Args:
            exception: Optional Exception objet related to the error
        """
        self._set_status("error", message)
        self.error = exception

    def _set_status(self, status: TestStatus, message: str | None = None) -> None:
        """
        Set status and insert optional message

        Args:
            status: status of the test
            message: optional message
        """
        self.result = status
        if message is not None:
            self.messages.append(message)

    def __str__(self) -> str:
        """
        Returns a human readable string of this TestResult
        """
        return f"Test {self.test} on device {self.name} has result {self.result}"


class ListResult(RootModel[List[TestResult]]):
    """
    list result for all tests on all devices.

    Attributes:
        __root__ (list[TestResult]): A list of TestResult objects.
    """

    root: List[TestResult] = []

    def extend(self, values: list[TestResult]) -> None:
        """Add support for extend method."""
        self.root.extend(values)

    def append(self, value: TestResult) -> None:
        """Add support for append method."""
        self.root.append(value)

    def __iter__(self) -> Iterator[TestResult]:  # type: ignore
        """Use custom iter method."""
        # TODO - mypy is not happy because we overwrite BaseModel.__iter__
        # return type and are breaking Liskov Substitution Principle.
        return iter(self.root)

    def __getitem__(self, item: int) -> TestResult:
        """Use custom getitem method."""
        return self.root[item]

    def __len__(self) -> int:
        """Support for length of __root__"""
        return len(self.root)
