# Copyright (c) 2023 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""ANTA Result Manager models unit tests."""
from __future__ import annotations

from typing import Any, Callable

import pytest

from anta.result_manager.models import TestResult
from tests.data.json_data import TEST_RESULT_SET_STATUS
from tests.lib.utils import generate_test_ids_dict

# pytest.skip(reason="Not yet ready for CI", allow_module_level=True)


class TestTestResultModels:
    """Test components of anta.result_manager.models."""

    @pytest.mark.parametrize("data", TEST_RESULT_SET_STATUS, ids=generate_test_ids_dict)
    def test__is_status_foo(self, test_result_factory: Callable[[int], TestResult], data: dict[str, Any]) -> None:
        """Test TestResult.is_foo methods."""
        testresult = test_result_factory(1)
        assert testresult.result == "unset"
        assert len(testresult.messages) == 0
        if data["target"] == "success":
            testresult.is_success(data["message"])
            assert testresult.result == data["target"]
            assert data["message"] in testresult.messages
        if data["target"] == "failure":
            testresult.is_failure(data["message"])
            assert testresult.result == data["target"]
            assert data["message"] in testresult.messages
        if data["target"] == "error":
            testresult.is_error(data["message"])
            assert testresult.result == data["target"]
            assert data["message"] in testresult.messages
        if data["target"] == "skipped":
            testresult.is_skipped(data["message"])
            assert testresult.result == data["target"]
            assert data["message"] in testresult.messages
        # no helper for unset, testing _set_status
        if data["target"] == "unset":
            testresult._set_status("unset", data["message"])  # pylint: disable=W0212
            assert testresult.result == data["target"]
            assert data["message"] in testresult.messages

    @pytest.mark.parametrize("data", TEST_RESULT_SET_STATUS, ids=generate_test_ids_dict)
    def test____str__(self, test_result_factory: Callable[[int], TestResult], data: dict[str, Any]) -> None:
        """Test TestResult.__str__."""
        testresult = test_result_factory(1)
        assert testresult.result == "unset"
        assert len(testresult.messages) == 0
        testresult._set_status(data["target"], data["message"])  # pylint: disable=W0212
        assert testresult.result == data["target"]
        assert str(testresult) == f"Test VerifyTest1 on device testdevice has result {data['target']}"
