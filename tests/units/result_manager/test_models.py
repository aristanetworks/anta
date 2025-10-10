# Copyright (c) 2023-2025 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""ANTA Result Manager models unit tests."""

from __future__ import annotations

from typing import TYPE_CHECKING, Callable

import pytest

from anta.result_manager.models import AntaTestStatus
from tests.units.conftest import DEVICE_NAME
from tests.units.result_manager.conftest import FAKE_TEST

if TYPE_CHECKING:
    from _pytest.mark.structures import ParameterSet

    # Import as Result to avoid pytest collection
    from anta.result_manager.models import TestResult as Result

TEST_RESULTS: list[ParameterSet] = [
    pytest.param(AntaTestStatus.SUCCESS, f"Test {FAKE_TEST.name} (on {DEVICE_NAME}): success\nMessages:\nsuccess message", id="success"),
    pytest.param(AntaTestStatus.SKIPPED, f"Test {FAKE_TEST.name} (on {DEVICE_NAME}): skipped\nMessages:\nskipped message", id="skipped"),
    pytest.param(AntaTestStatus.FAILURE, f"Test {FAKE_TEST.name} (on {DEVICE_NAME}): failure\nMessages:\nfailure message", id="failure"),
    pytest.param(AntaTestStatus.ERROR, f"Test {FAKE_TEST.name} (on {DEVICE_NAME}): error\nMessages:\nerror message", id="error"),
]


def _set_result(result: Result, status: AntaTestStatus) -> None:
    message = f"{status} message"
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

    @pytest.mark.parametrize(("status", "expected"), TEST_RESULTS)
    def test_is_status_foo(self, test_result_factory: Callable[[int], Result], status: AntaTestStatus, expected: str) -> None:
        """Test TestResult.is_foo methods."""
        result = test_result_factory(1)
        assert result.result == AntaTestStatus.UNSET
        assert len(result.messages) == 0
        _set_result(result, status)
        assert result.result == status
        assert len(result.messages) == 1
        assert str(result) == expected

    @pytest.mark.parametrize(("status", "expected"), TEST_RESULTS)
    def test____str__(self, test_result_factory: Callable[[int], Result], status: AntaTestStatus, expected: str) -> None:
        """Test TestResult.__str__()."""
        result = test_result_factory(1)
        assert str(result) == f"Test {FAKE_TEST.name} (on {DEVICE_NAME}): {AntaTestStatus.UNSET}"
        _set_result(result, status)
        assert str(result) == expected
