# Copyright (c) 2023-2025 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""ANTA Result Manager models unit tests."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from anta.result_manager.models import AntaTestStatus
from tests.units.conftest import DEVICE_NAME
from tests.units.result_manager.conftest import FAKE_TEST

if TYPE_CHECKING:
    from _pytest.mark.structures import ParameterSet

    # Import as Result to avoid pytest collection
    from .conftest import TestResultFactoryProtocol

TEST_RESULTS: list[ParameterSet] = [
    pytest.param(AntaTestStatus.SUCCESS, [], f"Test {FAKE_TEST.name} (on {DEVICE_NAME}): success\nMessages:\nsuccess message", id="success"),
    pytest.param(
        AntaTestStatus.SUCCESS,
        [AntaTestStatus.SUCCESS, AntaTestStatus.SUCCESS],
        (
            f"Test {FAKE_TEST.name} (on {DEVICE_NAME}): success [success,success]\nMessages:\n"
            f"FakeTestWithInput1AtomicTestResult0 - atomic success message\n"
            f"FakeTestWithInput1AtomicTestResult1 - atomic success message"
        ),
        id="success-atomic",
    ),
    pytest.param(AntaTestStatus.FAILURE, [], f"Test {FAKE_TEST.name} (on {DEVICE_NAME}): failure\nMessages:\nfailure message", id="failure"),
    pytest.param(
        AntaTestStatus.FAILURE,
        [AntaTestStatus.SUCCESS, AntaTestStatus.FAILURE],
        (
            f"Test {FAKE_TEST.name} (on {DEVICE_NAME}): failure [success,failure]\nMessages:\n"
            f"FakeTestWithInput1AtomicTestResult0 - atomic success message\n"
            f"FakeTestWithInput1AtomicTestResult1 - atomic failure message"
        ),
        id="failure-atomic",
    ),
    pytest.param(AntaTestStatus.SKIPPED, [], f"Test {FAKE_TEST.name} (on {DEVICE_NAME}): skipped\nMessages:\nskipped message", id="skipped"),
    pytest.param(
        AntaTestStatus.UNSET,
        [AntaTestStatus.SKIPPED, AntaTestStatus.SKIPPED],
        (
            f"Test {FAKE_TEST.name} (on {DEVICE_NAME}): unset [skipped,skipped]\nMessages:\n"
            f"FakeTestWithInput1AtomicTestResult0 - atomic skipped message\n"
            f"FakeTestWithInput1AtomicTestResult1 - atomic skipped message"
        ),
        id="skipped-atomic",
    ),
    pytest.param(
        AntaTestStatus.SUCCESS,
        [AntaTestStatus.SKIPPED, AntaTestStatus.SUCCESS],
        (
            f"Test {FAKE_TEST.name} (on {DEVICE_NAME}): success [skipped,success]\nMessages:\n"
            f"FakeTestWithInput1AtomicTestResult0 - atomic skipped message\n"
            f"FakeTestWithInput1AtomicTestResult1 - atomic success message"
        ),
        id="skipped-success-atomic",
    ),
    pytest.param(AntaTestStatus.ERROR, [], f"Test {FAKE_TEST.name} (on {DEVICE_NAME}): error\nMessages:\nerror message", id="error"),
    pytest.param(
        AntaTestStatus.ERROR,
        [AntaTestStatus.SUCCESS, AntaTestStatus.ERROR],
        (
            f"Test {FAKE_TEST.name} (on {DEVICE_NAME}): error [success,error]\nMessages:\n"
            f"FakeTestWithInput1AtomicTestResult0 - atomic success message\n"
            f"FakeTestWithInput1AtomicTestResult1 - atomic error message"
        ),
        id="error-atomic",
    ),
    # TODO: failure + error atomic
]


class TestTestResult:
    """Test TestResult."""

    @pytest.mark.parametrize(("status", "atomic", "expected"), TEST_RESULTS)
    def test_is_status_foo(self, test_result_factory: TestResultFactoryProtocol, status: AntaTestStatus, atomic: list[AntaTestStatus], expected: str) -> None:
        """Test TestResult.is_foo methods."""
        result = test_result_factory(1, atomic)
        if len(atomic) == 0:
            result._set_status(status, message=f"{status} message")

        assert result.result == status

        if atomic:
            assert len(result.messages) == len(atomic)
        else:
            assert len(result.messages) == 1

    @pytest.mark.parametrize(("status", "atomic", "expected"), TEST_RESULTS)
    def test____str__(self, test_result_factory: TestResultFactoryProtocol, status: AntaTestStatus, atomic: list[AntaTestStatus], expected: str) -> None:
        """Test TestResult.__str__()."""
        result = test_result_factory(1, atomic)
        if len(atomic) == 0:
            result._set_status(status, message=f"{status} message")
        assert str(result) == expected

    def test_add(self, test_result_factory: TestResultFactoryProtocol) -> None:
        """Test TestResult.add."""
        result = test_result_factory(1, None)
        assert len(result.atomic_results) == 0
        assert len(result.messages) == 0

        # Add one atomic result with default status
        result.add("Atomic result default status")
        assert len(result.atomic_results) == 1
        assert result.atomic_results[0].result == AntaTestStatus.UNSET
        assert result.result == AntaTestStatus.UNSET
        assert result.atomic_results[0].description == "Atomic result default status"
        assert len(result.messages) == 0

        # Add one atomic result with status success
        result.add("Atomic result status==success", status=AntaTestStatus.SUCCESS)
        assert len(result.atomic_results) == 2
        assert result.atomic_results[1].result == AntaTestStatus.SUCCESS
        assert result.result == AntaTestStatus.SUCCESS  # TODO: but should it be really given that [0] is unset
        assert result.atomic_results[1].description == "Atomic result status==success"
        assert len(result.messages) == 0

        # Add one atomic result with status failure
        result.add("Atomic result status==failure", status=AntaTestStatus.FAILURE)
        assert len(result.atomic_results) == 3
        assert result.atomic_results[2].result == AntaTestStatus.FAILURE
        assert result.result == AntaTestStatus.FAILURE
        assert result.atomic_results[2].description == "Atomic result status==failure"
        assert len(result.messages) == 0

        # Add one atomic result with multiple messages
        result.add("Multiple messages", status=AntaTestStatus.FAILURE, messages=["message 1", "message 2"])
        assert len(result.atomic_results) == 4
        assert result.atomic_results[3].result == AntaTestStatus.FAILURE
        assert result.result == AntaTestStatus.FAILURE
        assert result.atomic_results[3].description == "Multiple messages"
        assert len(result.messages) == 2
