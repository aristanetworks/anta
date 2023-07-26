"""
Result Manager Module for ANTA.
"""

import json
import logging
from typing import Any, List

from anta.result_manager.models import RESULT_OPTIONS, ListResult, TestResult
from anta.tools.pydantic import pydantic_to_dict

logger = logging.getLogger(__name__)


class ResultManager:
    """
    Helper to manage Test Results and generate reports.

    Examples:

        Create Inventory:

            inventory_anta = AntaInventory.parse(
                inventory_file='examples/inventory.yml',
                username='ansible',
                password='ansible',
                timeout=0.5
            )

        Create Result Manager:

            manager = ResultManager()

        Run tests for all connected devices:

            for device in inventory_anta.get_inventory():
                manager.add_test_result(
                    VerifyNTP(device=device).test()
                )
                manager.add_test_result(
                    VerifyEOSVersion(device=device).test(version='4.28.3M')
                )

        Print result in native format:

            manager.get_results()
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
        """
        Class constructor.

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
        logger.debug("Instantiate result-manager")
        self._result_entries = ListResult()
        # Initialize status
        self.status = "unset"
        self.error_status = False

    def __len__(self) -> int:
        """
        Implement __len__ method to count number of results.
        """
        return len(self._result_entries)

    def _update_status(self, test_status: str) -> None:
        """
        Update ResultManager status based on the table above.
        """
        if test_status not in RESULT_OPTIONS:
            raise ValueError("{test_status} is not a valid result option")
        if test_status == "error":
            self.error_status = True
            return

        if self.status == "unset":
            self.status = test_status
        elif self.status == "skipped" and test_status in {"success", "failure"}:
            self.status = test_status
        elif self.status == "success" and test_status == "failure":
            self.status = "failure"

    def add_test_result(self, entry: TestResult) -> None:
        """Add a result to the list

        Args:
            entry (TestResult): TestResult data to add to the report
        """
        logger.debug(entry)
        self._result_entries.append(entry)
        self._update_status(entry.result)

    def add_test_results(self, entries: List[TestResult]) -> None:
        """Add a list of results to the list

        Args:
            entries (List[TestResult]): list of TestResult data to add to the report
        """
        for e in entries:
            self.add_test_result(e)

    def get_status(self, ignore_error: bool = False) -> str:
        """
        Returns the current status including error_status if ignore_error is False
        """
        return "error" if self.error_status and not ignore_error else self.status

    def get_results(self, output_format: str = "native") -> Any:
        """
        Expose list of all test results in different format

        Support multiple format:
          - native: ListResults format
          - list: a list of TestResult
          - json: a native JSON format

        Args:
            output_format (str, optional): format selector. Can be either native/list/json. Defaults to 'native'.

        Returns:
            any: List of results.
        """
        if output_format == "list":
            return list(self._result_entries)

        if output_format == "json":
            return json.dumps(pydantic_to_dict(self._result_entries), indent=4)

        if output_format == "native":
            # Default return for native format.
            return self._result_entries
        raise ValueError(f"{output_format} is not a valid value ['list', 'json', 'native']")

    def get_result_by_test(self, test_name: str, output_format: str = "native") -> Any:
        """
        Get list of test result for a given test.

        Args:
            test_name (str): Test name to use to filter results
            output_format (str, optional): format selector. Can be either native/list. Defaults to 'native'.

        Returns:
            list[TestResult]: List of results related to the test.
        """
        if output_format == "list":
            return [result for result in self._result_entries if str(result.test) == test_name]

        result_manager_filtered = ListResult()
        for result in self._result_entries:
            if result.test == test_name:
                result_manager_filtered.append(result)
        return result_manager_filtered

    def get_result_by_host(self, host_ip: str, output_format: str = "native") -> Any:
        """
        Get list of test result for a given host.

        Args:
            host_ip (str): IP Address of the host to use to filter results.
            output_format (str, optional): format selector. Can be either native/list. Defaults to 'native'.

        Returns:
            Any: List of results related to the host.
        """
        if output_format == "list":
            return [result for result in self._result_entries if str(result.name) == host_ip]

        result_manager_filtered = ListResult()
        for result in self._result_entries:
            if str(result.name) == host_ip:
                result_manager_filtered.append(result)
        return result_manager_filtered

    def get_testcases(self) -> List[str]:
        """
        Get list of name of all test cases in current manager.

        Returns:
            List[str]: List of names for all tests.
        """
        result_list = []
        for testcase in self._result_entries:
            if str(testcase.test) not in result_list:
                result_list.append(str(testcase.test))
        return result_list

    def get_hosts(self) -> List[str]:
        """
        Get list of IP addresses in current manager.

        Returns:
            List[str]: List of IP addresses.
        """
        result_list = []
        for testcase in self._result_entries:
            if str(testcase.name) not in result_list:
                result_list.append(str(testcase.name))
        return result_list
