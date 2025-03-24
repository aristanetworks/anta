# Copyright (c) 2023-2025 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Models related to anta.result_manager module."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import TYPE_CHECKING, Any

from pydantic import BaseModel

if TYPE_CHECKING:
    from anta.models import AntaCommand, AntaTest


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


@dataclass(frozen=True)
class TestEvidence:
    """Container for additional evidence related to a TestResult.

    Attributes
    ----------
    inputs : AntaTest.Input | None
        Inputs used for the test. Can be None in case of inputs validation error.
    commands : list[AntaCommand]
        List of commands executed during the test.
    """

    inputs: AntaTest.Input | None
    commands: list[AntaCommand]

    def dump(self) -> dict[str, Any]:
        """Dump the evidence to a JSON serializable dictionary."""
        return {
            "inputs": self.inputs.model_dump(mode="json", exclude={"filters", "result_overwrite"}) if self.inputs else None,
            "commands": [command.model_dump(mode="json", exclude={"template", "params", "use_cache"}) for command in self.commands],
        }


class TestResult(BaseModel):
    """Describe the result of a test from a single device.

    Attributes
    ----------
    name : str
        Name of the device where the test was run.
    test : str
        Name of the test run on the device.
    categories : list[str]
        List of categories the TestResult belongs to. Defaults to the AntaTest categories.
    description : str
        Description of the TestResult. Defaults to the AntaTest description.
    result : AntaTestStatus
        Result of the test. Must be one of the AntaTestStatus Enum values: unset, success, failure, error or skipped.
    messages : list[str]
        Messages to report after the test, if any.
    custom_field : str | None
        Custom field to store a string for flexibility in integrating with ANTA.
    _evidence : TestEvidence | None
        Optional evidence attached to the result. Can be set and retrieved using the evidence property.

    """

    name: str
    test: str
    categories: list[str]
    description: str
    result: AntaTestStatus = AntaTestStatus.UNSET
    messages: list[str] = []
    custom_field: str | None = None

    # Optional evidence attached to the result
    _evidence: TestEvidence | None = None

    @property
    def has_evidence(self) -> bool:
        """Check if this result has attached evidence."""
        return self._evidence is not None

    @property
    def evidence(self) -> TestEvidence:
        """Return the evidence attached to this result."""
        if self._evidence is None:
            msg = "No evidence attached to this result"
            raise ValueError(msg)
        return self._evidence

    @evidence.setter
    def evidence(self, evidence: TestEvidence) -> None:
        """Set the evidence attached to this result."""
        self._evidence = evidence

    def dump(self, *, with_evidence: bool = False) -> dict[str, Any]:
        """Dump the TestResult to a JSON serializable dictionary."""
        data = self.model_dump(mode="json")
        if with_evidence and self.has_evidence:
            data["evidence"] = self.evidence.dump()
        return data

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

    def __str__(self) -> str:
        """Return a human readable string of this TestResult."""
        return f"Test '{self.test}' (on '{self.name}'): Result '{self.result}'\nMessages: {self.messages}"


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
