# Copyright (c) 2023-2024 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Models related to anta.result_manager module."""

from __future__ import annotations

from abc import ABC
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from pydantic import BaseModel, InstanceOf


class AntaTestStatus(str, Enum):
    """Test status Enum for the TestResult.

    NOTE: This could be updated to StrEnum when Python 3.11 is the minimum supported version in ANTA.
    """

    UNSET = "unset"
    SUCCESS = "success"
    FAILURE = "failure"
    ERROR = "error"
    SKIPPED = "skipped"

    def __str__(self) -> str:
        """Override the __str__ method to return the value of the Enum, mimicking the behavior of StrEnum."""
        return self.value


class BaseTestResult(BaseModel, ABC):
    """Base model for test results.

    Attributes
    ----------
    result : AntaTestStatus
        Result of the test.
    messages : list[str]
        Messages reported by the test.
    """

    result: AntaTestStatus = AntaTestStatus.UNSET
    messages: list[str] = []

    def is_success(self, message: str | None = None) -> None:
        """Set status to success.

        Parameters
        ----------
        message
            Optional message related to the test.

        """
        self._set_status(AntaTestStatus.SUCCESS, message)

    def is_failure(self, message: str | None = None) -> None:
        """Set status to failure.

        Parameters
        ----------
        message
            Optional message related to the test.

        """
        self._set_status(AntaTestStatus.FAILURE, message)

    def is_skipped(self, message: str | None = None) -> None:
        """Set status to skipped.

        Parameters
        ----------
        message
            Optional message related to the test.

        """
        self._set_status(AntaTestStatus.SKIPPED, message)

    def is_error(self, message: str | None = None) -> None:
        """Set status to error.

        Parameters
        ----------
        message
            Optional message related to the test.

        """
        self._set_status(AntaTestStatus.ERROR, message)

    def _set_status(self, status: AntaTestStatus, message: str | None = None) -> None:
        """Set status and insert optional message.

        Parameters
        ----------
        status
            Status of the test.
        message
            Optional message.
        """
        self.result = status
        if message is not None:
            self.messages.append(message)


class AtomicTestResult(BaseTestResult):
    """Describe the result of an atomic test part of a larger test related to a TestResult instance.

    Attributes
    ----------
    description : str | None
        Description of the AtomicTestResult.
    inputs: BaseModel | None
        If this AtomicTestResult is related to a specific parent test input, this field must be set.
    result : AntaTestStatus
        Result of the atomic test.
    messages : list[str]
        Messages reported by the test.
    """

    _parent: TestResult
    description: str | None = None
    inputs: InstanceOf[BaseModel] | None = None

    def __init__(self, **data: Any) -> None:  # noqa: ANN401
        """Instantiate the parent TestResult private attribute."""
        parent = data.pop("parent")
        super().__init__(**data)
        self._parent = parent

    def _set_status(self, status: AntaTestStatus, message: str | None = None) -> None:
        """Set status and insert optional message.

        Parameters
        ----------
        status
            Status of the test.
        message
            Optional message.
        """
        self.result = status
        if (self._parent.result == AntaTestStatus.UNSET and status == AntaTestStatus.SUCCESS) or status in [AntaTestStatus.FAILURE, AntaTestStatus.ERROR]:
            self._parent.result = status
        if message is not None:
            self.messages.append(message)
            self._parent.messages.append(message)


class TestResult(BaseTestResult):
    """Describe the result of a test from a single device.

    Attributes
    ----------
    name : str
        Name of the device on which the test was run.
    test : str
        Name of the AntaTest subclass.
    inputs:  BaseModel | None
        Inputs of the AntaTest instance.
    categories : list[str]
        List of categories the TestResult belongs to. Defaults to the AntaTest subclass categories.
    description : str
        Description of the TestResult. Defaults to the AntaTest subclass description.
    result : AntaTestStatus
        Result of the test.
    messages : list[str]
        Messages reported by the test.
    custom_field : str | None
        Custom field to store a string for flexibility in integrating with ANTA.
    atomic_results: list[AtomicTestResult]
        A list of AtomicTestResult instances which can be used to store atomic results during the test execution.
        It can then be leveraged in the report to render atomic results over the test global TestResult.
    """

    name: str
    test: str
    description: str
    inputs: InstanceOf[BaseModel] | None = None
    categories: list[str]
    custom_field: str | None = None
    atomic_results: list[AtomicTestResult] = []

    def __str__(self) -> str:
        """Return a human readable string of this TestResult."""
        return f"Test '{self.test}' (on '{self.name}'): Result '{self.result}'\nMessages: {self.messages}"

    def add(self, description: str | None = None, inputs: BaseModel | None = None) -> AtomicTestResult:
        """Create and add a new AtomicTestResult to this TestResult instance.

        Parameters
        ----------
        description : str | None
            Description of the AtomicTestResult.
        inputs: BaseModel | None
            If this AtomicTestResult is related to a specific parent test input, this field must be set.
        """
        res = AtomicTestResult(description=description, inputs=inputs, parent=self)
        self.atomic_results.append(res)
        return res


# Pylint does not treat dataclasses differently: https://github.com/pylint-dev/pylint/issues/9058
# pylint: disable=too-many-instance-attributes
@dataclass
class DeviceStats:
    """Device statistics for a run of tests."""

    tests_success_count: int = 0
    tests_skipped_count: int = 0
    tests_failure_count: int = 0
    tests_error_count: int = 0
    tests_unset_count: int = 0
    tests_failure: set[str] = field(default_factory=set)
    categories_failed: set[str] = field(default_factory=set)
    categories_skipped: set[str] = field(default_factory=set)


@dataclass
class CategoryStats:
    """Category statistics for a run of tests."""

    tests_success_count: int = 0
    tests_skipped_count: int = 0
    tests_failure_count: int = 0
    tests_error_count: int = 0
    tests_unset_count: int = 0


@dataclass
class TestStats:
    """Test statistics for a run of tests."""

    devices_success_count: int = 0
    devices_skipped_count: int = 0
    devices_failure_count: int = 0
    devices_error_count: int = 0
    devices_unset_count: int = 0
    devices_failure: set[str] = field(default_factory=set)
