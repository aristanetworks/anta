# Copyright (c) 2023-2025 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""ANTA Result Manager models unit tests."""

from __future__ import annotations

from typing import TYPE_CHECKING, Callable

import pytest

from anta.result_manager.models import AntaTestStatus
from tests.units.conftest import DEVICE_NAME

if TYPE_CHECKING:
    from _pytest.mark.structures import ParameterSet

    # Import as Result to avoid pytest collection
    from anta.result_manager.models import TestResult as Result

TEST_RESULT_SET_STATUS: list[ParameterSet] = [
    pytest.param(AntaTestStatus.SUCCESS, "test success message", id="set_success"),
    pytest.param(AntaTestStatus.ERROR, "test error message", id="set_error"),
    pytest.param(AntaTestStatus.FAILURE, "test failure message", id="set_failure"),
    pytest.param(AntaTestStatus.SKIPPED, "test skipped message", id="set_skipped"),
    pytest.param(AntaTestStatus.UNSET, "test unset message", id="set_unset"),
]


class TestTestResultModels:
    """Test components of anta.result_manager.models."""

    @pytest.mark.parametrize(("target", "message"), TEST_RESULT_SET_STATUS)
    def test__is_status_foo(self, test_result_factory: Callable[[int], Result], target: AntaTestStatus, message: str) -> None:
        """Test TestResult.is_foo methods."""
        testresult = test_result_factory(1)
        assert testresult.result == AntaTestStatus.UNSET
        assert len(testresult.messages) == 0
        if target == AntaTestStatus.SUCCESS:
            testresult.is_success(message)
            assert testresult.result == "success"
            assert message in testresult.messages
        if target == AntaTestStatus.FAILURE:
            testresult.is_failure(message)
            assert testresult.result == "failure"
            assert message in testresult.messages
        if target == AntaTestStatus.ERROR:
            testresult.is_error(message)
            assert testresult.result == "error"
            assert message in testresult.messages
        if target == AntaTestStatus.SKIPPED:
            testresult.is_skipped(message)
            assert testresult.result == "skipped"
            assert message in testresult.messages
        if target == AntaTestStatus.UNSET:
            # no helper for unset, testing _set_status
            testresult._set_status(AntaTestStatus.UNSET, message)
            assert testresult.result == "unset"
            assert message in testresult.messages

    @pytest.mark.parametrize(("target", "message"), TEST_RESULT_SET_STATUS)
    def test____str__(self, test_result_factory: Callable[[int], Result], target: AntaTestStatus, message: str) -> None:
        """Test TestResult.__str__."""
        testresult = test_result_factory(1)
        assert testresult.result == AntaTestStatus.UNSET
        assert len(testresult.messages) == 0
        testresult._set_status(target, message)
        assert testresult.result == target
        assert str(testresult) == f"Test 'VerifyTest1' (on '{DEVICE_NAME}'): Result '{target}'\nMessages: {[message]}"
