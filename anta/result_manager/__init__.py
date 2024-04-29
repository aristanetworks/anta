# Copyright (c) 2023-2024 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Result Manager module for ANTA."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING

from pydantic import TypeAdapter

from anta.custom_types import TestStatus

if TYPE_CHECKING:
    from anta.result_manager.models import TestResult


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
        self._result_entries: list[TestResult] = []
        self.status: TestStatus = "unset"
        self.error_status = False

    def __len__(self) -> int:
        """Implement __len__ method to count number of results."""
        return len(self._result_entries)

    @property
    def results(self) -> list[TestResult]:
        """Get the list of TestResult."""
        return self._result_entries

    @results.setter
    def results(self, value: list[TestResult]) -> None:
        self._result_entries = []
        self.status = "unset"
        self.error_status = False
        for e in value:
            self.add(e)

    @property
    def json(self) -> str:
        """Get a JSON representation of the results."""
        return json.dumps([result.model_dump() for result in self._result_entries], indent=4)

    def add(self, result: TestResult) -> None:
        """Add a result to the ResultManager instance.

        Args:
        ----
            result: TestResult to add to the ResultManager instance.
        """

        def _update_status(test_status: TestStatus) -> None:
            result_validator = TypeAdapter(TestStatus)
            result_validator.validate_python(test_status)
            if test_status == "error":
                self.error_status = True
                return
            if self.status == "unset" or self.status == "skipped" and test_status in {"success", "failure"}:
                self.status = test_status
            elif self.status == "success" and test_status == "failure":
                self.status = "failure"

        self._result_entries.append(result)
        _update_status(result.result)

    def get_status(self, *, ignore_error: bool = False) -> str:
        """Return the current status including error_status if ignore_error is False."""
        return "error" if self.error_status and not ignore_error else self.status

    def filter(self, hide: set[TestStatus]) -> ResultManager:
        """Get a filtered ResultManager based on test status.

        Args:
        ----
            hide: set of TestStatus literals to select tests to hide based on their status.

        Returns
        -------
            A filtered `ResultManager`.
        """
        manager = ResultManager()
        manager.results = [test for test in self._result_entries if test.result not in hide]
        return manager

    def filter_by_tests(self, tests: set[str]) -> ResultManager:
        """Get a filtered ResultManager that only contains specific tests.

        Args:
        ----
            tests: Set of test names to filter the results.

        Returns
        -------
            A filtered `ResultManager`.
        """
        manager = ResultManager()
        manager.results = [result for result in self._result_entries if result.test in tests]
        return manager

    def filter_by_devices(self, devices: set[str]) -> ResultManager:
        """Get a filtered ResultManager that only contains specific devices.

        Args:
        ----
            devices: Set of device names to filter the results.

        Returns
        -------
            A filtered `ResultManager`.
        """
        manager = ResultManager()
        manager.results = [result for result in self._result_entries if result.name in devices]
        return manager

    def get_tests(self) -> set[str]:
        """Get the set of all the test names.

        Returns
        -------
            Set of test names.
        """
        return {str(result.test) for result in self._result_entries}

    def get_devices(self) -> set[str]:
        """Get the set of all the device names.

        Returns
        -------
            Set of device names.
        """
        return {str(result.name) for result in self._result_entries}
