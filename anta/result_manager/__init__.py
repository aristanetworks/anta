# Copyright (c) 2023-2025 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Result Manager module for ANTA."""

from __future__ import annotations

import logging
from collections import defaultdict
from functools import cached_property
from itertools import chain
from typing import Any

from pydantic import TypeAdapter
from typing_extensions import deprecated

from anta.result_manager.models import AntaTestStatus, TestResult

from .models import CategoryStats, DeviceStats, TestStats

logger = logging.getLogger(__name__)


# The TypeAdapter is used to conveniently be able to dump the ResultManager later.
# https://docs.pydantic.dev/latest/api/type_adapter/
ResultManagerTypeAdapter = TypeAdapter(list[TestResult])


class ResultManager:
    """Manager of ANTA Results.

    The status of the class is initialized to "unset"

    Then when adding a test with a status that is NOT 'error' the following
    table shows the updated status:

    | Current Status |         Added test Status       | Updated Status |
    | -------------- | ------------------------------- | -------------- |
    |      unset     |              Any                |       Any      |
    |     skipped    |         unset, skipped          |     skipped    |
    |     skipped    |            success              |     success    |
    |     skipped    |            failure              |     failure    |
    |     success    |     unset, skipped, success     |     success    |
    |     success    |            failure              |     failure    |
    |     failure    | unset, skipped success, failure |     failure    |

    If the status of the added test is error, the status is untouched and the
    `error_status` attribute is set to True.

    Attributes
    ----------
    results
    dump
    status
        Status rerpesenting all the results.
    error_status
        Will be `True` if a test returned an error.
    results_by_status
    dump
    json
    device_stats
    category_stats
    test_stats
    """

    # TODO: Remove the following pylint disable once deprecated methods are removed.
    # pylint: disable=too-many-public-methods

    _results: list[TestResult]
    status: AntaTestStatus
    error_status: bool

    _device_stats: defaultdict[str, DeviceStats]
    _category_stats: defaultdict[str, CategoryStats]
    _test_stats: defaultdict[str, TestStats]
    _stats_in_sync: bool

    def __init__(self) -> None:
        """Initialize a ResultManager instance."""
        self.reset()

    def reset(self) -> None:
        """Create or reset the attributes of the ResultManager instance."""
        self._results = []
        self.status = AntaTestStatus.UNSET
        self.error_status = False

        # Initialize the statistics attributes
        self._reset_stats()

    def __len__(self) -> int:
        """Implement __len__ method to count number of results."""
        return len(self._results)

    @property
    def results(self) -> list[TestResult]:
        """Get the list of TestResult."""
        return self._results

    @results.setter
    def results(self, value: list[TestResult]) -> None:
        """Set the list of TestResult."""
        # When setting the results, we need to reset the state of the current instance
        self.reset()

        for result in value:
            self.add(result)

    @property
    def dump(self) -> list[dict[str, Any]]:
        """Get a list of dictionary of the results."""
        return ResultManagerTypeAdapter.dump_python(self._results)

    @property
    def json(self) -> str:
        """Get a JSON representation of the results."""
        return ResultManagerTypeAdapter.dump_json(self._results, indent=4).decode()

    @property
    def device_stats(self) -> dict[str, DeviceStats]:
        """Get the device statistics."""
        self._ensure_stats_in_sync()
        return dict(sorted(self._device_stats.items()))

    @property
    def category_stats(self) -> dict[str, CategoryStats]:
        """Get the category statistics."""
        self._ensure_stats_in_sync()
        return dict(sorted(self._category_stats.items()))

    @property
    def test_stats(self) -> dict[str, TestStats]:
        """Get the test statistics."""
        self._ensure_stats_in_sync()
        return dict(sorted(self._test_stats.items()))

    @property
    @deprecated("This property is deprecated, use `category_stats` instead. This will be removed in ANTA v2.0.0.", category=DeprecationWarning)
    def sorted_category_stats(self) -> dict[str, CategoryStats]:
        """A property that returns the category_stats dictionary sorted by key name."""
        return self.category_stats

    @cached_property
    def results_by_status(self) -> dict[AntaTestStatus, list[TestResult]]:
        """A cached property that returns the results grouped by status."""
        return {status: [result for result in self._results if result.result == status] for status in AntaTestStatus}

    @cached_property
    def results_by_category(self) -> list[TestResult]:
        """A cached property that returns the list of results sorted by categories."""
        return sorted(self._results, key=lambda res: res.categories)

    def _update_status(self, test_status: AntaTestStatus) -> None:
        """Update the status of the ResultManager instance based on the test status.

        Parameters
        ----------
        test_status
            AntaTestStatus to update the ResultManager status.
        """
        if test_status == "error":
            self.error_status = True
            return
        if self.status == "unset" or (self.status == "skipped" and test_status in {"success", "failure"}):
            self.status = test_status
        elif self.status == "success" and test_status == "failure":
            self.status = AntaTestStatus.FAILURE

    def _reset_stats(self) -> None:
        """Create or reset the statistics attributes."""
        self._device_stats = defaultdict(DeviceStats)
        self._category_stats = defaultdict(CategoryStats)
        self._test_stats = defaultdict(TestStats)
        self._stats_in_sync = False

    def _update_stats(self, result: TestResult) -> None:
        """Update the statistics based on the test result.

        Parameters
        ----------
        result
            TestResult to update the statistics.
        """
        count_attr = f"tests_{result.result}_count"

        # Update device stats
        device_stats: DeviceStats = self._device_stats[result.name]
        setattr(device_stats, count_attr, getattr(device_stats, count_attr) + 1)
        if result.result in ("failure", "error"):
            device_stats.tests_failure.add(result.test)
            device_stats.categories_failed.update(result.categories)
        elif result.result == "skipped":
            device_stats.categories_skipped.update(result.categories)

        # Update category stats
        for category in result.categories:
            category_stats: CategoryStats = self._category_stats[category]
            setattr(category_stats, count_attr, getattr(category_stats, count_attr) + 1)

        # Update test stats
        count_attr = f"devices_{result.result}_count"
        test_stats: TestStats = self._test_stats[result.test]
        setattr(test_stats, count_attr, getattr(test_stats, count_attr) + 1)
        if result.result in ("failure", "error"):
            test_stats.devices_failure.add(result.name)

    def _compute_stats(self) -> None:
        """Compute all statistics from the current results."""
        logger.info("Computing statistics for all results.")

        # Reset all stats
        self._reset_stats()

        # Recompute stats for all results
        for result in self._results:
            self._update_stats(result)

        self._stats_in_sync = True

    def _ensure_stats_in_sync(self) -> None:
        """Ensure statistics are in sync with current results."""
        if not self._stats_in_sync:
            self._compute_stats()

    def add(self, result: TestResult) -> None:
        """Add a result to the ResultManager instance.

        The result is added to the internal list of results and the overall status
        of the ResultManager instance is updated based on the added test status.

        Parameters
        ----------
        result
            TestResult to add to the ResultManager instance.
        """
        self._results.append(result)
        self._update_status(result.result)
        self._stats_in_sync = False

        # Every time a new result is added, we need to clear the cached properties
        for name in ["results_by_status", "results_by_category"]:
            self.__dict__.pop(name, None)

    def get_results(self, status: set[AntaTestStatus] | None = None, sort_by: list[str] | None = None) -> list[TestResult]:
        """Get the results, optionally filtered by status and sorted by TestResult fields.

        If no status is provided, all results are returned.

        Parameters
        ----------
        status
            Optional set of AntaTestStatus enum members to filter the results.
        sort_by
            Optional list of TestResult fields to sort the results.

        Returns
        -------
        list[TestResult]
            List of results.
        """
        # Return all results if no status is provided, otherwise return results for multiple statuses
        results = self._results if status is None else list(chain.from_iterable(self.results_by_status.get(status, []) for status in status))

        if sort_by:
            accepted_fields = TestResult.model_fields.keys()
            if not set(sort_by).issubset(set(accepted_fields)):
                msg = f"Invalid sort_by fields: {sort_by}. Accepted fields are: {list(accepted_fields)}"
                raise ValueError(msg)
            results = sorted(results, key=lambda result: [getattr(result, field) or "" for field in sort_by])

        return results

    def get_total_results(self, status: set[AntaTestStatus] | None = None) -> int:
        """Get the total number of results, optionally filtered by status.

        If no status is provided, the total number of results is returned.

        Parameters
        ----------
        status
            Optional set of AntaTestStatus enum members to filter the results.

        Returns
        -------
        int
            Total number of results.
        """
        if status is None:
            # Return the total number of results
            return sum(len(results) for results in self.results_by_status.values())

        # Return the total number of results for multiple statuses
        return sum(len(self.results_by_status.get(status, [])) for status in status)

    def get_status(self, *, ignore_error: bool = False) -> str:
        """Return the current status including error_status if ignore_error is False."""
        return "error" if self.error_status and not ignore_error else self.status

    def sort(self, sort_by: list[str]) -> ResultManager:
        """Sort the ResultManager results based on TestResult fields.

        Parameters
        ----------
        sort_by
            List of TestResult fields to sort the results.
        """
        accepted_fields = TestResult.model_fields.keys()
        if not set(sort_by).issubset(set(accepted_fields)):
            msg = f"Invalid sort_by fields: {sort_by}. Accepted fields are: {list(accepted_fields)}"
            raise ValueError(msg)
        self._results.sort(key=lambda result: [getattr(result, field) or "" for field in sort_by])
        return self

    def filter(self, hide: set[AntaTestStatus]) -> ResultManager:
        """Get a filtered ResultManager based on test status.

        Parameters
        ----------
        hide
            Set of AntaTestStatus enum members to select tests to hide based on their status.

        Returns
        -------
        ResultManager
            A filtered `ResultManager`.
        """
        possible_statuses = set(AntaTestStatus)
        manager = ResultManager()
        manager.results = self.get_results(possible_statuses - hide)
        return manager

    @classmethod
    def merge_results(cls, results_managers: list[ResultManager]) -> ResultManager:
        """Merge multiple ResultManager instances.

        Parameters
        ----------
        results_managers
            A list of ResultManager instances to merge.

        Returns
        -------
        ResultManager
            A new ResultManager instance containing the results of all the input ResultManagers.
        """
        combined_results = list(chain(*(rm.results for rm in results_managers)))
        merged_manager = cls()
        merged_manager.results = combined_results
        return merged_manager

    @deprecated("This method is deprecated. This will be removed in ANTA v2.0.0.", category=DeprecationWarning)
    def filter_by_tests(self, tests: set[str]) -> ResultManager:
        """Get a filtered ResultManager that only contains specific tests.

        Parameters
        ----------
        tests
            Set of test names to filter the results.

        Returns
        -------
        ResultManager
            A filtered `ResultManager`.
        """
        manager = ResultManager()
        manager.results = [result for result in self._results if result.test in tests]
        return manager

    @deprecated("This method is deprecated. This will be removed in ANTA v2.0.0.", category=DeprecationWarning)
    def filter_by_devices(self, devices: set[str]) -> ResultManager:
        """Get a filtered ResultManager that only contains specific devices.

        Parameters
        ----------
        devices
            Set of device names to filter the results.

        Returns
        -------
        ResultManager
            A filtered `ResultManager`.
        """
        manager = ResultManager()
        manager.results = [result for result in self._results if result.name in devices]
        return manager

    @deprecated("This method is deprecated. This will be removed in ANTA v2.0.0.", category=DeprecationWarning)
    def get_tests(self) -> set[str]:
        """Get the set of all the test names.

        Returns
        -------
        set[str]
            Set of test names.
        """
        return {str(result.test) for result in self._results}

    @deprecated("This method is deprecated. This will be removed in ANTA v2.0.0.", category=DeprecationWarning)
    def get_devices(self) -> set[str]:
        """Get the set of all the device names.

        Returns
        -------
        set[str]
            Set of device names.
        """
        return {str(result.name) for result in self._results}
