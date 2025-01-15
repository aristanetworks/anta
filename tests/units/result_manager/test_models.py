# Copyright (c) 2023-2025 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""ANTA Result Manager models unit tests."""

from __future__ import annotations

from typing import TYPE_CHECKING, Callable

import pytest

from anta.result_manager.models import AntaTestStatus, AtomicTestResult
from tests.units.conftest import DEVICE_NAME
from tests.units.result_manager.conftest import FAKE_TEST

if TYPE_CHECKING:
    from _pytest.mark.structures import ParameterSet

    # Import as Result to avoid pytest collection
    from anta.result_manager.models import TestResult as Result

TEST_RESULTS: list[ParameterSet] = [
    pytest.param(AntaTestStatus.SUCCESS, [], f"Test {FAKE_TEST.name} (on {DEVICE_NAME}): success\nMessages:\nsuccess message", id="success"),
    pytest.param(
        AntaTestStatus.SUCCESS,
        [AntaTestStatus.SUCCESS, AntaTestStatus.SUCCESS],
        f"Test {FAKE_TEST.name} (on {DEVICE_NAME}): success [success,success]\nMessages:\natomic success message\natomic success message",
        id="success-atomic",
    ),
    pytest.param(AntaTestStatus.FAILURE, [], f"Test {FAKE_TEST.name} (on {DEVICE_NAME}): failure\nMessages:\nfailure message", id="failure"),
    pytest.param(
        AntaTestStatus.FAILURE,
        [AntaTestStatus.SUCCESS, AntaTestStatus.FAILURE],
        f"Test {FAKE_TEST.name} (on {DEVICE_NAME}): failure [success,failure]\nMessages:\natomic success message\natomic failure message",
        id="failure-atomic",
    ),
    pytest.param(AntaTestStatus.SKIPPED, [], f"Test {FAKE_TEST.name} (on {DEVICE_NAME}): skipped\nMessages:\nskipped message", id="skipped"),
    pytest.param(
        AntaTestStatus.UNSET,
        [AntaTestStatus.SKIPPED, AntaTestStatus.SKIPPED],
        f"Test {FAKE_TEST.name} (on {DEVICE_NAME}): unset [skipped,skipped]\nMessages:\natomic skipped message\natomic skipped message",
        id="skipped-atomic",
    ),
    pytest.param(
        AntaTestStatus.SUCCESS,
        [AntaTestStatus.SKIPPED, AntaTestStatus.SUCCESS],
        f"Test {FAKE_TEST.name} (on {DEVICE_NAME}): success [skipped,success]\nMessages:\natomic skipped message\natomic success message",
        id="skipped-success-atomic",
    ),
    pytest.param(AntaTestStatus.FAILURE, [], f"Test {FAKE_TEST.name} (on {DEVICE_NAME}): failure\nMessages:\nfailure message", id="failure"),
    pytest.param(
        AntaTestStatus.FAILURE,
        [AntaTestStatus.SUCCESS, AntaTestStatus.FAILURE],
        f"Test {FAKE_TEST.name} (on {DEVICE_NAME}): failure [success,failure]\nMessages:\natomic success message\natomic failure message",
        id="failure-atomic",
    ),
    pytest.param(AntaTestStatus.ERROR, [], f"Test {FAKE_TEST.name} (on {DEVICE_NAME}): error\nMessages:\nerror message", id="error"),
    pytest.param(
        AntaTestStatus.ERROR,
        [AntaTestStatus.SUCCESS, AntaTestStatus.ERROR],
        f"Test {FAKE_TEST.name} (on {DEVICE_NAME}): error [success,error]\nMessages:\natomic success message\natomic error message",
        id="error-atomic",
    ),
]


def _set_result(result: Result | AtomicTestResult, status: AntaTestStatus) -> None:
    message = f"atomic {status} message" if isinstance(result, AtomicTestResult) else f"{status} message"
    if status == AntaTestStatus.SUCCESS:
        result.is_success(message)
    if status == AntaTestStatus.FAILURE:
        result.is_failure(message)
    if status == AntaTestStatus.ERROR:
        result.is_error(message)
    if status == AntaTestStatus.SKIPPED:
        result.is_skipped(message)


class TestTestResult:
    """Test TestResult."""

    @pytest.mark.parametrize(("status", "atomic", "expected"), TEST_RESULTS)
    def test_is_status_foo(self, test_result_factory: Callable[[int], Result], status: AntaTestStatus, atomic: list[AntaTestStatus], expected: str) -> None:
        """Test TestResult.is_foo methods."""
        result = test_result_factory(1)
        assert result.result == AntaTestStatus.UNSET
        assert len(result.messages) == 0
        if atomic:
            for i, s in enumerate(atomic):
                a_result = result.add(f"Atomic Result {i}")
                _set_result(a_result, s)
        else:
            _set_result(result, status)
        assert result.result == status
        if atomic:
            assert len(result.messages) == len(atomic)
        else:
            assert len(result.messages) == 1

    @pytest.mark.parametrize(("status", "atomic", "expected"), TEST_RESULTS)
    def test____str__(self, test_result_factory: Callable[[int], Result], status: AntaTestStatus, atomic: list[AntaTestStatus], expected: str) -> None:
        """Test TestResult.__str__()."""
        result = test_result_factory(1)
        assert str(result) == f"Test {FAKE_TEST.name} (on {DEVICE_NAME}): {AntaTestStatus.UNSET}"
        if atomic:
            for i, s in enumerate(atomic):
                a_result = result.add(f"Atomic Result {i}")
                _set_result(a_result, s)
        else:
            _set_result(result, status)
        assert str(result) == expected
