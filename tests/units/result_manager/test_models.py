# Copyright (c) 2023-2024 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""ANTA Result Manager models unit tests."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Callable

import pytest

from anta.result_manager import ResultManager
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

    def test_register_manager(self, test_result_factory: Callable[[], Result], caplog: pytest.LogCaptureFixture) -> None:
        """Test TestResult.register_manager."""
        test_result = test_result_factory()
        manager1 = ResultManager()
        manager2 = ResultManager()

        # Initial registration
        assert test_result._manager is None
        test_result.register_manager(manager1)
        assert test_result._manager is manager1

        # Re-register to same manager (no warning)
        with caplog.at_level(logging.WARNING):
            test_result.register_manager(manager1)
        assert len(caplog.records) == 0
        assert test_result._manager is manager1

        # Register to different manager (should log warning)
        with caplog.at_level(logging.WARNING):
            test_result.register_manager(manager2)

        # Verify warning was logged
        assert len(caplog.records) == 1
        assert "is being re-registered to a different ResultManager" in caplog.records[0].message
        assert test_result._manager is manager2

    def test_add_message(self, test_result_factory: Callable[[], Result]) -> None:
        """Test TestResult.add_message."""
        test_result = test_result_factory()
        assert len(test_result.messages) == 0

        # Test adding None message (shouldn't add)
        test_result.add_message(None)
        assert len(test_result.messages) == 0

        # Test adding first message
        test_result.add_message("First message")
        assert len(test_result.messages) == 1
        assert test_result.messages == ["First message"]

        # Test adding second message
        test_result.add_message("Second message")
        assert len(test_result.messages) == 2
        assert test_result.messages == ["First message", "Second message"]

    def test_status_updates_with_manager(self, test_result_factory: Callable[[], Result]) -> None:
        """Test status updates with and without manager."""
        test_result = test_result_factory()
        manager = ResultManager()

        # Before adding to manager, status updates are direct
        test_result.is_success("Direct update")
        assert test_result.result == AntaTestStatus.SUCCESS
        assert test_result not in manager.results

        # Add to manager (this also registers the manager)
        manager.add(test_result)
        assert test_result._manager is manager
        assert test_result in manager.results

        # Now status updates should go through manager
        test_result.is_failure("Through manager")
        assert test_result.result == AntaTestStatus.FAILURE
        assert len(manager.get_results(status={AntaTestStatus.FAILURE})) == 1

        # Verify message was added
        assert "Through manager" in test_result.messages
