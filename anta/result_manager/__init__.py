# Copyright (c) 2023-2024 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Result Manager module for ANTA."""

from __future__ import annotations

import json
import logging
from typing import TYPE_CHECKING

from pydantic import TypeAdapter

from anta.custom_types import TestStatus

if TYPE_CHECKING:
    from anta.result_manager.models import TestResult

logger = logging.getLogger(__name__)


class ResultManager:
    """Helper to manage Test Results and generate reports.

    Examples
    --------
        Create Inventory:

            inventory_anta = AntaInventory.parse(
                filename='examples/inventory.yml',
                username='ansible',
                password='ansible',
                timeout=0.5
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
                    host=IPv4Address('192.168.0.10'),
                    test='VerifyNTP',
                    result='failure',
                    message="device is not running NTP correctly"
                ),
                TestResult(
                    host=IPv4Address('192.168.0.10'),
                    test='VerifyEOSVersion',
                    result='success',
                    message=None
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
        for e in value:
            self.add(e)

    @property
    def json(self) -> str:
        """Get a JSON representation of the results."""
        return json.dumps([result.model_dump() for result in self._result_entries], indent=4)

    def _update_status(self, test_status: TestStatus) -> None:
        """Update ResultManager status based on the table above."""
        result_validator = TypeAdapter(TestStatus)
        result_validator.validate_python(test_status)
        if test_status == "error":
            self.error_status = True
            return
        if self.status == "unset" or self.status == "skipped" and test_status in {"success", "failure"}:
            self.status = test_status
        elif self.status == "success" and test_status == "failure":
            self.status = "failure"

    def add(self, result: TestResult) -> None:
        """Add a result to the report.

        Args:
        ----
            test: TestResult data to add to the report.

        """
        logger.debug(result)
        self._result_entries.append(result)
        self._update_status(result.result)

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

    def filter_by_test(self, tests: list[str]) -> ResultManager:
        """Get a filtered ResultManager that only contains specific tests.

        Args:
        ----
            tests: List of test names to filter the results.

        Returns
        -------
            A filtered `ResultManager`.
        """
        manager = ResultManager()
        manager.results = [result for result in self._result_entries if result.test in tests]
        return manager

    def filter_by_device(self, devices: list[str]) -> ResultManager:
        """Get a filtered ResultManager that only contains specific devices.

        Args:
        ----
            devices: List of device names to filter the results.

        Returns
        -------
            A filtered `ResultManager`.
        """
        manager = ResultManager()
        manager.results = [result for result in self._result_entries if result.name in devices]
        return manager

    def get_tests(self) -> set[str]:
        """Get the list of all the test names.

        Returns
        -------
            List of test names.

        """
        names = set()
        for result in self._result_entries:
            names.add(str(result.test))
        return names

    def get_devices(self) -> set[str]:
        """Get the list of all the device names.

        Returns
        -------
            List of device names.

        """
        names = set()
        for result in self._result_entries:
            names.add(str(result.name))
        return names
