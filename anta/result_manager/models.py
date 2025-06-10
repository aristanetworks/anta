# Copyright (c) 2023-2025 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Models related to anta.result_manager module."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from pydantic import BaseModel, FieldSerializationInfo, field_serializer, field_validator


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
    evidence : dict[str, Any] | None
        Optional evidence attached to the result.
        If provided, the dictionary must follow this structure: `{"inputs": AntaTest.Input, "commands": list[AntaCommand]}`.

    """

    name: str
    test: str
    categories: list[str]
    description: str
    result: AntaTestStatus = AntaTestStatus.UNSET
    messages: list[str] = []
    custom_field: str | None = None

    # Using Any to prevent a circular import from anta.models (AntaCommand, AntaTest.Input)
    # TODO: Replace with a stricter type (TypedDict or dataclass) once module refactoring in ANTA v2.0.0 resolves the circular import from anta.models
    evidence: dict[str, Any] | None = None

    @field_serializer("evidence")
    def serialize_evidence(self, evidence: dict[str, Any] | None, _info: FieldSerializationInfo) -> dict[str, Any] | None:
        """Serialize the evidence field if present."""
        if evidence is None:
            return None

        inputs = evidence["inputs"].model_dump(mode="json", exclude_unset=True)
        commands = [command.model_dump(mode="json", exclude={"template", "params", "use_cache"}) for command in evidence["commands"]]
        return {"inputs": inputs, "commands": commands}

    # TODO: Remove this validator when a stricter type will be associated to evidence
    @field_validator("evidence", mode="after")
    @classmethod
    def validate_evidence(cls, evidence: dict[str, Any] | None) -> dict[str, Any] | None:
        """Validate the evidence field if present."""
        if evidence is None:
            return None

        errors: list[str] = []
        expected_keys = {"inputs", "commands"}
        actual_keys = set(evidence.keys())

        # Check for missing required keys
        if missing_keys := expected_keys - actual_keys:
            errors.append(f"evidence is missing required key(s): {sorted(missing_keys)}")

        # Check for unexpected extra keys
        if extra_keys := actual_keys - expected_keys:
            errors.append(f"evidence has unexpected key(s): {sorted(extra_keys)}")

        # Check if 'commands' value is a list (only if the key is present)
        if "commands" in actual_keys and not isinstance(evidence["commands"], list):
            errors.append(f"'commands' must be a list, but got '{type(evidence['commands']).__name__}'")

        # If any errors were collected, raise a single exception
        if errors:
            raise ValueError("\n".join(errors))

        return evidence

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
