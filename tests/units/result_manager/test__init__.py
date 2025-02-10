# Copyright (c) 2023-2025 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Test anta.result_manager.__init__.py."""

from __future__ import annotations

import json
import logging
import re
from contextlib import AbstractContextManager, nullcontext
from typing import TYPE_CHECKING, Callable

import pytest

from anta.result_manager import ResultManager, models
from anta.result_manager.models import AntaTestStatus

if TYPE_CHECKING:
    from anta.result_manager.models import TestResult


# pylint: disable=too-many-public-methods
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
            test.result = AntaTestStatus.SUCCESS
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

    def test_category_stats(self, list_result_factory: Callable[[int], list[TestResult]]) -> None:
        """Test ResultManager.category_stats."""
        result_manager = ResultManager()
        results = list_result_factory(4)

        # Modify the categories to have a mix of different acronym categories
        results[0].categories = ["ospf"]
        results[1].categories = ["bgp"]
        results[2].categories = ["vxlan"]
        results[3].categories = ["system"]

        result_manager.results = results

        # Check that category_stats returns sorted order by default
        expected_order = ["bgp", "ospf", "system", "vxlan"]
        assert list(result_manager.category_stats.keys()) == expected_order

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
            pytest.param("unset", "unknown", None, pytest.raises(ValueError, match="'unknown' is not a valid AntaTestStatus"), id="wrong status"),
        ],
    )
    def test_add(
        self,
        test_result_factory: Callable[[], TestResult],
        starting_status: str,
        test_status: str,
        expected_status: str,
        expected_raise: AbstractContextManager[Exception],
    ) -> None:
        """Test ResultManager_update_status."""
        result_manager = ResultManager()
        result_manager.status = AntaTestStatus(starting_status)
        assert result_manager.error_status is False
        assert len(result_manager) == 0

        test = test_result_factory()
        with expected_raise:
            test.result = AntaTestStatus(test_status)
            result_manager.add(test)
            if test_status == "error":
                assert result_manager.error_status is True
            else:
                assert result_manager.status == expected_status
            assert len(result_manager) == 1

    def test_add_clear_cache(self, result_manager: ResultManager, test_result_factory: Callable[[], TestResult]) -> None:
        """Test ResultManager.add and make sure the cache is reset after adding a new test."""
        # Check the cache is empty
        assert "results_by_status" not in result_manager.__dict__

        # Access the cache
        assert result_manager.get_total_results() == 30

        # Check the cache is filled with the correct results count
        assert "results_by_status" in result_manager.__dict__
        assert sum(len(v) for v in result_manager.__dict__["results_by_status"].values()) == 30

        # Add a new test
        result_manager.add(result=test_result_factory())

        # Check the cache has been reset
        assert "results_by_status" not in result_manager.__dict__

        # Access the cache again
        assert result_manager.get_total_results() == 31

        # Check the cache is filled again with the correct results count
        assert "results_by_status" in result_manager.__dict__
        assert sum(len(v) for v in result_manager.__dict__["results_by_status"].values()) == 31

    def test_get_results(self, result_manager: ResultManager) -> None:
        """Test ResultManager.get_results."""
        # Check for single status
        success_results = result_manager.get_results(status={AntaTestStatus.SUCCESS})
        assert len(success_results) == 7
        assert all(r.result == "success" for r in success_results)

        # Check for multiple statuses
        failure_results = result_manager.get_results(status={AntaTestStatus.FAILURE, AntaTestStatus.ERROR})
        assert len(failure_results) == 21
        assert all(r.result in {"failure", "error"} for r in failure_results)

        # Check all results
        all_results = result_manager.get_results()
        assert len(all_results) == 30

    def test_get_results_sort_by(self, result_manager: ResultManager) -> None:
        """Test ResultManager.get_results with sort_by."""
        # Check all results with sort_by result
        all_results = result_manager.get_results(sort_by=["result"])
        assert len(all_results) == 30
        assert [r.result for r in all_results] == ["error"] * 2 + ["failure"] * 19 + ["skipped"] * 2 + ["success"] * 7

        # Check all results with sort_by device (name)
        all_results = result_manager.get_results(sort_by=["name"])
        assert len(all_results) == 30
        assert all_results[0].name == "DC1-LEAF1A"
        assert all_results[-1].name == "DC1-SPINE1"

        # Check multiple statuses with sort_by categories
        success_skipped_results = result_manager.get_results(status={AntaTestStatus.SUCCESS, AntaTestStatus.SKIPPED}, sort_by=["categories"])
        assert len(success_skipped_results) == 9
        assert success_skipped_results[0].categories == ["Interfaces"]
        assert success_skipped_results[-1].categories == ["VXLAN"]

        # Check all results with bad sort_by
        with pytest.raises(
            ValueError,
            match=re.escape(
                "Invalid sort_by fields: ['bad_field']. Accepted fields are: ['name', 'test', 'categories', 'description', 'result', 'messages', 'custom_field']",
            ),
        ):
            all_results = result_manager.get_results(sort_by=["bad_field"])

    def test_get_total_results(self, result_manager: ResultManager) -> None:
        """Test ResultManager.get_total_results."""
        # Test all results
        assert result_manager.get_total_results() == 30

        # Test single status
        assert result_manager.get_total_results(status={AntaTestStatus.SUCCESS}) == 7
        assert result_manager.get_total_results(status={AntaTestStatus.FAILURE}) == 19
        assert result_manager.get_total_results(status={AntaTestStatus.ERROR}) == 2
        assert result_manager.get_total_results(status={AntaTestStatus.SKIPPED}) == 2

        # Test multiple statuses
        assert result_manager.get_total_results(status={AntaTestStatus.SUCCESS, AntaTestStatus.FAILURE}) == 26
        assert result_manager.get_total_results(status={AntaTestStatus.SUCCESS, AntaTestStatus.FAILURE, AntaTestStatus.ERROR}) == 28
        assert result_manager.get_total_results(status={AntaTestStatus.SUCCESS, AntaTestStatus.FAILURE, AntaTestStatus.ERROR, AntaTestStatus.SKIPPED}) == 30

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
        status: AntaTestStatus,
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
            test.result = AntaTestStatus.SUCCESS
        result_manager.results = success_list

        test = test_result_factory()
        test.result = AntaTestStatus.FAILURE
        result_manager.add(test)

        test = test_result_factory()
        test.result = AntaTestStatus.ERROR
        result_manager.add(test)

        test = test_result_factory()
        test.result = AntaTestStatus.SKIPPED
        result_manager.add(test)

        assert len(result_manager) == 6
        assert len(result_manager.filter({AntaTestStatus.FAILURE})) == 5
        assert len(result_manager.filter({AntaTestStatus.ERROR})) == 5
        assert len(result_manager.filter({AntaTestStatus.SKIPPED})) == 5
        assert len(result_manager.filter({AntaTestStatus.FAILURE, AntaTestStatus.ERROR})) == 4
        assert len(result_manager.filter({AntaTestStatus.FAILURE, AntaTestStatus.ERROR, AntaTestStatus.SKIPPED})) == 3
        assert len(result_manager.filter({AntaTestStatus.SUCCESS, AntaTestStatus.FAILURE, AntaTestStatus.ERROR, AntaTestStatus.SKIPPED})) == 0

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

    def test_stats_computation_methods(self, test_result_factory: Callable[[], TestResult], caplog: pytest.LogCaptureFixture) -> None:
        """Test ResultManager internal stats computation methods."""
        result_manager = ResultManager()

        # Initially stats should be unsynced
        assert result_manager._stats_in_sync is False

        # Test _reset_stats
        result_manager._reset_stats()
        assert result_manager._stats_in_sync is False
        assert len(result_manager._device_stats) == 0
        assert len(result_manager._category_stats) == 0
        assert len(result_manager._test_stats) == 0

        # Add some test results
        test1 = test_result_factory()
        test1.name = "device1"
        test1.result = AntaTestStatus.SUCCESS
        test1.categories = ["system"]
        test1.test = "test1"

        test2 = test_result_factory()
        test2.name = "device2"
        test2.result = AntaTestStatus.FAILURE
        test2.categories = ["interfaces"]
        test2.test = "test2"

        result_manager.add(test1)
        result_manager.add(test2)

        # Stats should still be unsynced after adding results
        assert result_manager._stats_in_sync is False

        # Test _compute_stats directly
        with caplog.at_level(logging.INFO):
            result_manager._compute_stats()
        assert "Computing statistics for all results" in caplog.text
        assert result_manager._stats_in_sync is True

        # Verify stats content
        assert len(result_manager._device_stats) == 2
        assert len(result_manager._category_stats) == 2
        assert len(result_manager._test_stats) == 2
        assert result_manager._device_stats["device1"].tests_success_count == 1
        assert result_manager._device_stats["device2"].tests_failure_count == 1
        assert result_manager._category_stats["system"].tests_success_count == 1
        assert result_manager._category_stats["interfaces"].tests_failure_count == 1
        assert result_manager._test_stats["test1"].devices_success_count == 1
        assert result_manager._test_stats["test2"].devices_failure_count == 1

    def test_stats_property_computation(self, test_result_factory: Callable[[], TestResult], caplog: pytest.LogCaptureFixture) -> None:
        """Test that stats are computed only once when accessed via properties."""
        result_manager = ResultManager()

        # Add some test results
        test1 = test_result_factory()
        test1.name = "device1"
        test1.result = AntaTestStatus.SUCCESS
        test1.categories = ["system"]
        result_manager.add(test1)

        test2 = test_result_factory()
        test2.name = "device2"
        test2.result = AntaTestStatus.FAILURE
        test2.categories = ["interfaces"]
        result_manager.add(test2)

        # Stats should be unsynced after adding results
        assert result_manager._stats_in_sync is False
        assert "Computing statistics" not in caplog.text

        # Access device_stats property - should trigger computation
        with caplog.at_level(logging.INFO):
            _ = result_manager.device_stats
        assert "Computing statistics for all results" in caplog.text
        assert result_manager._stats_in_sync is True

        # Clear the log
        caplog.clear()

        # Access other stats properties - should not trigger computation again
        with caplog.at_level(logging.INFO):
            _ = result_manager.category_stats
            _ = result_manager.test_stats
        assert "Computing statistics" not in caplog.text

        # Add another result - should mark stats as unsynced
        test3 = test_result_factory()
        test3.name = "device3"
        test3.result = "error"
        result_manager.add(test3)
        assert result_manager._stats_in_sync is False

        # Access stats again - should trigger recomputation
        with caplog.at_level(logging.INFO):
            _ = result_manager.device_stats
        assert "Computing statistics for all results" in caplog.text
        assert result_manager._stats_in_sync is True

    def test_sort_by_result(self, test_result_factory: Callable[[], TestResult]) -> None:
        """Test sorting by result."""
        result_manager = ResultManager()
        test1 = test_result_factory()
        test1.result = AntaTestStatus.SUCCESS
        test2 = test_result_factory()
        test2.result = AntaTestStatus.FAILURE
        test3 = test_result_factory()
        test3.result = AntaTestStatus.ERROR

        result_manager.results = [test1, test2, test3]
        sorted_manager = result_manager.sort(["result"])
        assert [r.result for r in sorted_manager.results] == ["error", "failure", "success"]

    def test_sort_by_name(self, test_result_factory: Callable[[], TestResult]) -> None:
        """Test sorting by name."""
        result_manager = ResultManager()
        test1 = test_result_factory()
        test1.name = "Device3"
        test2 = test_result_factory()
        test2.name = "Device1"
        test3 = test_result_factory()
        test3.name = "Device2"

        result_manager.results = [test1, test2, test3]
        sorted_manager = result_manager.sort(["name"])
        assert [r.name for r in sorted_manager.results] == ["Device1", "Device2", "Device3"]

    def test_sort_by_categories(self, test_result_factory: Callable[[], TestResult]) -> None:
        """Test sorting by categories."""
        result_manager = ResultManager()
        test1 = test_result_factory()
        test1.categories = ["VXLAN", "networking"]
        test2 = test_result_factory()
        test2.categories = ["BGP", "routing"]
        test3 = test_result_factory()
        test3.categories = ["system", "hardware"]

        result_manager.results = [test1, test2, test3]
        sorted_manager = result_manager.sort(["categories"])
        results = sorted_manager.results

        assert results[0].categories == ["BGP", "routing"]
        assert results[1].categories == ["VXLAN", "networking"]
        assert results[2].categories == ["system", "hardware"]

    def test_sort_multiple_fields(self, test_result_factory: Callable[[], TestResult]) -> None:
        """Test sorting by multiple fields."""
        result_manager = ResultManager()
        test1 = test_result_factory()
        test1.result = AntaTestStatus.ERROR
        test1.test = "Test3"
        test2 = test_result_factory()
        test2.result = AntaTestStatus.ERROR
        test2.test = "Test1"
        test3 = test_result_factory()
        test3.result = AntaTestStatus.FAILURE
        test3.test = "Test2"

        result_manager.results = [test1, test2, test3]
        sorted_manager = result_manager.sort(["result", "test"])
        results = sorted_manager.results

        assert results[0].result == "error"
        assert results[0].test == "Test1"
        assert results[1].result == "error"
        assert results[1].test == "Test3"
        assert results[2].result == "failure"
        assert results[2].test == "Test2"

    def test_sort_invalid_field(self) -> None:
        """Test that sort method raises ValueError for invalid sort_by fields."""
        result_manager = ResultManager()
        with pytest.raises(
            ValueError,
            match=re.escape(
                "Invalid sort_by fields: ['bad_field']. Accepted fields are: ['name', 'test', 'categories', 'description', 'result', 'messages', 'custom_field']",
            ),
        ):
            result_manager.sort(["bad_field"])

    def test_sort_is_chainable(self) -> None:
        """Test that the sort method is chainable."""
        result_manager = ResultManager()
        assert isinstance(result_manager.sort(["name"]), ResultManager)
