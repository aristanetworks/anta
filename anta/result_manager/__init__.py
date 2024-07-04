# Copyright (c) 2023-2024 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Result Manager module for ANTA."""

from __future__ import annotations

import json
from collections import defaultdict
from itertools import chain
from typing import get_args

from pydantic import TypeAdapter

from anta.custom_types import TestStatus
from anta.result_manager.models import TestResult

from .constants import ACRONYM_CATEGORIES, STAT_MAPPING
from .models import CategoryStats, DeviceStats


class ResultManager:
    """Helper to manage Test Results and generate reports.

    Examples
    --------
        Create Inventory:

            inventory_anta = AntaInventory.parse(
                filename='examples/inventory.yml',
                username='ansible',
                password='ansible',
            )

        Create Result Manager:

            manager = ResultManager()

        Run tests for all connected devices:

            for device in inventory_anta.get_inventory().devices:
                manager.add(
                    VerifyNTP(device=device).test()
                )
                manager.add(
                    VerifyEOSVersion(device=device).test(version='4.28.3M')
                )

        Print result in native format:

            manager.results
            [
                TestResult(
                    name="pf1",
                    test="VerifyZeroTouch",
                    categories=["configuration"],
                    description="Verifies ZeroTouch is disabled",
                    result="success",
                    messages=[],
                    custom_field=None,
                ),
                TestResult(
                    name="pf1",
                    test='VerifyNTP',
                    categories=["software"],
                    categories=['system'],
                    description='Verifies if NTP is synchronised.',
                    result='failure',
                    messages=["The device is not synchronized with the configured NTP server(s): 'NTP is disabled.'"],
                    custom_field=None,
                ),
            ]
    """

    def __init__(self) -> None:
        """Class constructor.

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
        error_status is set to True.
        """
        self._results_by_status: dict[TestStatus, list[TestResult]] = defaultdict(list)
        self.status: TestStatus = "unset"
        self.error_status = False

        self.dut_stats: defaultdict[str, DeviceStats] = defaultdict(DeviceStats)
        self.category_stats: defaultdict[str, CategoryStats] = defaultdict(CategoryStats)

    def __len__(self) -> int:
        """Implement __len__ method to count the total number of results."""
        return self.get_total_results()

    @property
    def results(self) -> list[TestResult]:
        """Get the list of all results."""
        return self.get_results()

    @results.setter
    def results(self, value: list[TestResult]) -> None:
        """Set the list of all results."""
        self._results_by_status = defaultdict(list)
        self.status = "unset"
        self.error_status = False
        for result in value:
            self.add(result)

    @property
    def json(self) -> str:
        """Get a JSON representation of all results."""
        all_results = chain.from_iterable((result.model_dump() for result in results) for results in self._results_by_status.values())
        return json.dumps(list(all_results), indent=4)

    @property
    def sorted_category_stats(self) -> dict[str, CategoryStats]:
        """A property that returns the category_stats dictionary sorted by key name."""
        return dict(sorted(self.category_stats.items()))

    def _update_status(self, test_status: TestStatus) -> None:
        """Update the status of the ResultManager instance based on the test status.

        Parameters
        ----------
            test_status: TestStatus to update the ResultManager status.
        """
        result_validator: TypeAdapter[TestStatus] = TypeAdapter(TestStatus)
        result_validator.validate_python(test_status)
        if test_status == "error":
            self.error_status = True
            return
        if self.status == "unset" or self.status == "skipped" and test_status in {"success", "failure"}:
            self.status = test_status
        elif self.status == "success" and test_status == "failure":
            self.status = "failure"

    def _update_stats(self, result: TestResult) -> None:
        """Update the statistics based on the test result.

        Parameters
        ----------
            result: TestResult to update the statistics.
        """
        result.categories = [
            " ".join(word.upper() if word.lower() in ACRONYM_CATEGORIES else word.title() for word in category.split()) for category in result.categories
        ]

        stat_key = STAT_MAPPING[result.result]

        # Update DUT stats
        dut_stats = self.dut_stats[result.name]
        setattr(dut_stats, stat_key, getattr(dut_stats, stat_key) + 1)

        if result.result in ("failure", "error", "unset"):
            dut_stats.categories_failed.update(result.categories)
        elif result.result == "skipped":
            dut_stats.categories_skipped.update(result.categories)

        # Update category stats
        for category in result.categories:
            category_stats = self.category_stats[category]
            setattr(category_stats, stat_key, getattr(category_stats, stat_key) + 1)

    def add(self, result: TestResult) -> None:
        """Add a result to the ResultManager instance.

        The result is added to the internal list of results per status and the overall status
        of the ResultManager instance is updated based on the added test status.

        Parameters
        ----------
            result: TestResult to add to the ResultManager instance.

        Raises
        ------
            TypeError: If the added test result is not a TestResult instance.
        """
        if not isinstance(result, TestResult):
            msg = f"Added test result '{result}' must be a TestResult instance, got {type(result).__name__}."
            raise TypeError(msg)

        self._results_by_status[result.result].append(result)
        # TODO: Validate if get_total_tests() is not too expensive to get the id
        result.id = self.get_total_results() + 1
        self._update_status(result.result)
        self._update_stats(result)

    def get_results(self, status: set[TestStatus] | TestStatus | None = None) -> list[TestResult]:
        """Get the results, optionally filtered by status.

        If no status is provided, all results are returned.

        Parameters
        ----------
            status: TestStatus or set of TestStatus literals to filter the results.

        Returns
        -------
            List of TestResult.
        """
        if status is None:
            # Return all results
            return list(chain.from_iterable(self._results_by_status.values()))

        if isinstance(status, set):
            # Return results for multiple statuses
            return list(chain.from_iterable(self._results_by_status.get(s, []) for s in status))

        # Return results for a single status
        return self._results_by_status.get(status, [])

    def get_total_results(self, status: set[TestStatus] | TestStatus | None = None) -> int:
        """Get the total number of results, optionally filtered by status.

        If no status is provided, the total number of results is returned.

        Parameters
        ----------
            status: TestStatus or set of TestStatus literals to filter the results.

        Returns
        -------
            Total number of results.
        """
        if status is None:
            # Return the total number of results
            return sum(len(results) for results in self._results_by_status.values())

        if isinstance(status, set):
            # Return the total number of results for multiple statuses
            return sum(len(self._results_by_status.get(s, [])) for s in status)

        # Return the total number of results for a single status
        return len(self._results_by_status.get(status, []))

    def get_status(self, *, ignore_error: bool = False) -> str:
        """Return the current status including error_status if ignore_error is False."""
        return "error" if self.error_status and not ignore_error else self.status

    def filter(self, hide: set[TestStatus]) -> ResultManager:
        """Get a filtered ResultManager based on test status.

        Parameters
        ----------
            hide: set of TestStatus literals to select tests to hide based on their status.

        Returns
        -------
            A filtered `ResultManager`.
        """
        possible_statuses = set(get_args(TestStatus))
        manager = ResultManager()
        manager.results = self.get_results(possible_statuses - hide)
        return manager

    def filter_by_tests(self, tests: set[str]) -> ResultManager:
        """Get a filtered ResultManager that only contains specific tests.

        Parameters
        ----------
            tests: Set of test names to filter the results.

        Returns
        -------
            A filtered `ResultManager`.
        """
        manager = ResultManager()
        manager.results = [result for result in self.get_results() if result.test in tests]
        return manager

    def filter_by_devices(self, devices: set[str]) -> ResultManager:
        """Get a filtered ResultManager that only contains specific devices.

        Parameters
        ----------
            devices: Set of device names to filter the results.

        Returns
        -------
            A filtered `ResultManager`.
        """
        manager = ResultManager()
        manager.results = [result for result in self.get_results() if result.name in devices]
        return manager

    def get_tests(self) -> set[str]:
        """Get the set of all the test names.

        Returns
        -------
            Set of test names.
        """
        return {str(result.test) for result in self.get_results()}

    def get_devices(self) -> set[str]:
        """Get the set of all the device names.

        Returns
        -------
            Set of device names.
        """
        return {str(result.name) for result in self.get_results()}
