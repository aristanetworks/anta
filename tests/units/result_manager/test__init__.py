# Copyright (c) 2023-2024 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Test anta.result_manager.__init__.py."""

from __future__ import annotations

import json
import re
from contextlib import AbstractContextManager, nullcontext
from typing import TYPE_CHECKING, Callable

import pytest

from anta.result_manager import ResultManager, models

if TYPE_CHECKING:
    from anta.custom_types import TestStatus
    from anta.result_manager.models import TestResult


class TestResultManager:
    """Test ResultManager class."""

    # not testing __init__ as nothing is going on there

    def test__len__(self, list_result_factory: Callable[[int], list[TestResult]]) -> None:
        """Test __len__."""
        list_result = list_result_factory(3)
        result_manager = ResultManager()
        assert len(result_manager) == 0
        for i in range(3):
            result_manager.add(list_result[i])
            assert len(result_manager) == i + 1

    def test_results_getter(self, result_manager_factory: Callable[[int], ResultManager]) -> None:
        """Test ResultManager.results property getter."""
        result_manager = result_manager_factory(3)
        res = result_manager.results
        assert len(res) == 3
        assert isinstance(res, list)
        for e in res:
            assert isinstance(e, models.TestResult)

    def test_results_setter(self, list_result_factory: Callable[[int], list[TestResult]], result_manager_factory: Callable[[int], ResultManager]) -> None:
        """Test ResultManager.results property setter."""
        result_manager = result_manager_factory(3)
        assert len(result_manager) == 3
        tests = list_result_factory(5)
        result_manager.results = tests
        assert len(result_manager) == 5

    def test_json(self, list_result_factory: Callable[[int], list[TestResult]]) -> None:
        """Test ResultManager.json property."""
        result_manager = ResultManager()

        success_list = list_result_factory(3)
        for test in success_list:
            test.result = "success"
        result_manager.results = success_list

        json_res = result_manager.json
        assert isinstance(json_res, str)

        # Verifies it can be deserialized back to a list of dict with the correct values types
        res = json.loads(json_res)
        for test in res:
            assert isinstance(test, dict)
            assert isinstance(test.get("test"), str)
            assert isinstance(test.get("categories"), list)
            assert isinstance(test.get("description"), str)
            assert test.get("custom_field") is None
            assert test.get("result") == "success"

    def test_sorted_category_stats(self, list_result_factory: Callable[[int], list[TestResult]]) -> None:
        """Test ResultManager.sorted_category_stats."""
        result_manager = ResultManager()
        results = list_result_factory(4)

        # Modify the categories to have a mix of different acronym categories
        results[0].categories = ["ospf"]
        results[1].categories = ["bgp"]
        results[2].categories = ["vxlan"]
        results[3].categories = ["system"]

        result_manager.results = results

        # Check the current categories order and name format
        expected_order = ["OSPF", "BGP", "VXLAN", "System"]
        assert list(result_manager.category_stats.keys()) == expected_order

        # Check the sorted categories order and name format
        expected_order = ["BGP", "OSPF", "System", "VXLAN"]
        assert list(result_manager.sorted_category_stats.keys()) == expected_order

    @pytest.mark.parametrize(
        ("starting_status", "test_status", "expected_status", "expected_raise"),
        [
            pytest.param("unset", "unset", "unset", nullcontext(), id="unset->unset"),
            pytest.param("unset", "success", "success", nullcontext(), id="unset->success"),
            pytest.param("unset", "error", "unset", nullcontext(), id="set error"),
            pytest.param("skipped", "skipped", "skipped", nullcontext(), id="skipped->skipped"),
            pytest.param("skipped", "unset", "skipped", nullcontext(), id="skipped, add unset"),
            pytest.param(
                "skipped",
                "success",
                "success",
                nullcontext(),
                id="skipped, add success",
            ),
            pytest.param(
                "skipped",
                "failure",
                "failure",
                nullcontext(),
                id="skipped, add failure",
            ),
            pytest.param("success", "unset", "success", nullcontext(), id="success, add unset"),
            pytest.param(
                "success",
                "skipped",
                "success",
                nullcontext(),
                id="success, add skipped",
            ),
            pytest.param("success", "success", "success", nullcontext(), id="success->success"),
            pytest.param("success", "failure", "failure", nullcontext(), id="success->failure"),
            pytest.param("failure", "unset", "failure", nullcontext(), id="failure->failure"),
            pytest.param("failure", "skipped", "failure", nullcontext(), id="failure, add unset"),
            pytest.param(
                "failure",
                "success",
                "failure",
                nullcontext(),
                id="failure, add skipped",
            ),
            pytest.param(
                "failure",
                "failure",
                "failure",
                nullcontext(),
                id="failure, add success",
            ),
            pytest.param(
                "unset", "unknown", None, pytest.raises(ValueError, match="Input should be 'unset', 'success', 'failure', 'error' or 'skipped'"), id="wrong status"
            ),
        ],
    )
    def test_add(
        self,
        test_result_factory: Callable[[], TestResult],
        starting_status: TestStatus,
        test_status: TestStatus,
        expected_status: str,
        expected_raise: AbstractContextManager[Exception],
    ) -> None:
        # pylint: disable=too-many-arguments
        """Test ResultManager_update_status."""
        result_manager = ResultManager()
        result_manager.status = starting_status
        assert result_manager.error_status is False
        assert len(result_manager) == 0

        test = test_result_factory()
        test.result = test_status
        with expected_raise:
            result_manager.add(test)
            if test_status == "error":
                assert result_manager.error_status is True
            else:
                assert result_manager.status == expected_status
            assert len(result_manager) == 1

    def test_add_type_error(self) -> None:
        """Test ResultManager.add with wrong object type."""
        result_manager = ResultManager()
        with pytest.raises(TypeError, match="Added test result 'test' must be a TestResult instance, got str."):
            result_manager.add("test")  # type: ignore[arg-type]

    def test_get_results(self, test_result_factory: Callable[[], TestResult]) -> None:
        """Test ResultManager.get_results."""
        result_manager = ResultManager()
        assert result_manager.get_results() == []

        success_result = test_result_factory()
        success_result.result = "success"
        success_result.categories = ["ospf"]
        result_manager.add(success_result)

        failure_result = test_result_factory()
        failure_result.result = "failure"
        failure_result.categories = ["bgp"]
        result_manager.add(failure_result)

        skipped_result = test_result_factory()
        skipped_result.result = "skipped"
        result_manager.add(skipped_result)

        error_result = test_result_factory()
        error_result.result = "error"
        result_manager.add(error_result)

        # Check for single status
        success_results = result_manager.get_results(status="success")
        assert len(success_results) == 1
        assert success_results[0].result == "success"

        # Check for multiple statuses
        success_failure_results = result_manager.get_results(status={"success", "failure"})
        assert len(success_failure_results) == 2
        assert all(r.result in {"success", "failure"} for r in success_failure_results)

        # Check all results
        all_results = result_manager.get_results()
        assert len(all_results) == 4
        assert [r.result for r in all_results] == ["success", "failure", "skipped", "error"]

        # Check all results with sort_by result
        all_results = result_manager.get_results(sort_by=["result"])
        assert len(all_results) == 4
        assert [r.result for r in all_results] == ["error", "failure", "skipped", "success"]

        # Check multiple statuses with sort_by categories
        success_failure_results = result_manager.get_results(status={"success", "failure"}, sort_by=["categories"])
        assert len(success_failure_results) == 2
        assert success_failure_results[0] == failure_result
        assert success_failure_results[1] == success_result

        # Check all results with bad sort_by
        with pytest.raises(
            ValueError,
            match=re.escape(
                "Invalid sort_by fields: ['bad_field']. Accepted fields are: ['name', 'test', 'categories', 'description', 'result', 'messages', 'custom_field']",
            ),
        ):
            all_results = result_manager.get_results(sort_by=["bad_field"])

    def test_get_total_results(self, test_result_factory: Callable[[], TestResult]) -> None:
        """Test ResultManager.get_total_results."""
        result_manager = ResultManager()
        assert result_manager.get_total_results() == 0

        success_result = test_result_factory()
        success_result.result = "success"
        result_manager.add(success_result)

        failure_result = test_result_factory()
        failure_result.result = "failure"
        result_manager.add(failure_result)

        skipped_result = test_result_factory()
        skipped_result.result = "skipped"
        result_manager.add(skipped_result)

        error_result = test_result_factory()
        error_result.result = "error"
        result_manager.add(error_result)

        assert result_manager.get_total_results(status="success") == 1
        assert result_manager.get_total_results(status={"success", "failure"}) == 2
        assert result_manager.get_total_results() == 4

    @pytest.mark.parametrize(
        ("status", "error_status", "ignore_error", "expected_status"),
        [
            pytest.param("success", False, True, "success", id="no error"),
            pytest.param("success", True, True, "success", id="error, ignore error"),
            pytest.param("success", True, False, "error", id="error, do not ignore error"),
        ],
    )
    def test_get_status(
        self,
        status: TestStatus,
        error_status: bool,
        ignore_error: bool,
        expected_status: str,
    ) -> None:
        """Test ResultManager.get_status."""
        result_manager = ResultManager()
        result_manager.status = status
        result_manager.error_status = error_status

        assert result_manager.get_status(ignore_error=ignore_error) == expected_status

    def test_filter(self, test_result_factory: Callable[[], TestResult], list_result_factory: Callable[[int], list[TestResult]]) -> None:
        """Test ResultManager.filter."""
        result_manager = ResultManager()

        success_list = list_result_factory(3)
        for test in success_list:
            test.result = "success"
        result_manager.results = success_list

        test = test_result_factory()
        test.result = "failure"
        result_manager.add(test)

        test = test_result_factory()
        test.result = "error"
        result_manager.add(test)

        test = test_result_factory()
        test.result = "skipped"
        result_manager.add(test)

        assert len(result_manager) == 6
        assert len(result_manager.filter({"failure"})) == 5
        assert len(result_manager.filter({"error"})) == 5
        assert len(result_manager.filter({"skipped"})) == 5
        assert len(result_manager.filter({"failure", "error"})) == 4
        assert len(result_manager.filter({"failure", "error", "skipped"})) == 3
        assert len(result_manager.filter({"success", "failure", "error", "skipped"})) == 0

    def test_get_by_tests(self, test_result_factory: Callable[[], TestResult], result_manager_factory: Callable[[int], ResultManager]) -> None:
        """Test ResultManager.get_by_tests."""
        result_manager = result_manager_factory(3)

        test = test_result_factory()
        test.test = "Test1"
        result_manager.add(test)

        test = test_result_factory()
        test.test = "Test2"
        result_manager.add(test)

        test = test_result_factory()
        test.test = "Test2"
        result_manager.add(test)

        assert len(result_manager) == 6
        assert len(result_manager.filter_by_tests({"Test1"})) == 1
        rm = result_manager.filter_by_tests({"Test1", "Test2"})
        assert len(rm) == 3
        assert len(rm.filter_by_tests({"Test1"})) == 1

    def test_get_by_devices(self, test_result_factory: Callable[[], TestResult], result_manager_factory: Callable[[int], ResultManager]) -> None:
        """Test ResultManager.get_by_devices."""
        result_manager = result_manager_factory(3)

        test = test_result_factory()
        test.name = "Device1"
        result_manager.add(test)

        test = test_result_factory()
        test.name = "Device2"
        result_manager.add(test)

        test = test_result_factory()
        test.name = "Device2"
        result_manager.add(test)

        assert len(result_manager) == 6
        assert len(result_manager.filter_by_devices({"Device1"})) == 1
        rm = result_manager.filter_by_devices({"Device1", "Device2"})
        assert len(rm) == 3
        assert len(rm.filter_by_devices({"Device1"})) == 1

    def test_get_tests(self, test_result_factory: Callable[[], TestResult], list_result_factory: Callable[[int], list[TestResult]]) -> None:
        """Test ResultManager.get_tests."""
        result_manager = ResultManager()

        tests = list_result_factory(3)
        for test in tests:
            test.test = "Test1"
        result_manager.results = tests

        test = test_result_factory()
        test.test = "Test2"
        result_manager.add(test)

        assert len(result_manager.get_tests()) == 2
        assert all(t in result_manager.get_tests() for t in ["Test1", "Test2"])

    def test_get_devices(self, test_result_factory: Callable[[], TestResult], list_result_factory: Callable[[int], list[TestResult]]) -> None:
        """Test ResultManager.get_tests."""
        result_manager = ResultManager()

        tests = list_result_factory(3)
        for test in tests:
            test.name = "Device1"
        result_manager.results = tests

        test = test_result_factory()
        test.name = "Device2"
        result_manager.add(test)

        assert len(result_manager.get_devices()) == 2
        assert all(t in result_manager.get_devices() for t in ["Device1", "Device2"])
