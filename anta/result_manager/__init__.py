"""
Result Manager Module for ANTA.
"""

import json
import logging
from typing import Any, List

from anta.result_manager.models import ListResult, TestResult
from anta.tools import pydantic_to_dict

logger = logging.getLogger(__name__)


class ResultManager:
    """
    Helper to manage Test Results and generate reports.

    Examples:

        Create Inventory:

            inventory_anta = AntaInventory(
                inventory_file='examples/inventory.yml',
                username='ansible',
                password='ansible',
                timeout=0.5,
                auto_connect=True
            )

        Create Result Manager:

            manager = ResultManager()

        Run tests for all connected devices:

            for device in inventory_anta.get_inventory():
                manager.add_test_result(
                    verify_eos_version(
                        device=device, versions=['4.28.0F']
                    )
                )
                manager.add_test_result(
                    verify_uptime(
                        device=device, minimum=1
                    )
                )

        Print result in native format:

            manager.get_results()
            [
                TestResult(
                    host=IPv4Address('192.168.0.10'),
                    test='verify_eos_version',
                    result='failure',
                    message="device is running version 4.27.3F-26379303.4273F (engineering build) and test expect ['4.28.0F']"
                ),
                TestResult(
                    host=IPv4Address('192.168.0.10'),
                    test='verify_eos_version',
                    result='success',
                    message=None
                ),
            ]
    """

    def __init__(self) -> None:
        """ Class constructor."""
        logger.debug('Instantiate result-manager')
        self._result_entries = ListResult()

    def __len__(self) -> int:
        """
        Implement __len__ method to count number of results.
        """
        return len(self._result_entries)

    def add_test_result(self, entry: TestResult) -> None:
        """Add a result to the list

        Args:
            entry (TestResult): TestResult data to add to the report
        """
        logger.info(f'add new test result to manager: {entry}')
        self._result_entries.append(entry)

    def add_test_results(self, entries: List[TestResult]) -> None:
        """Add a list of results to the list

        Args:
            entries (List[TestResult]): list of TestResult data to add to the report
        """
        logger.info(f'add new list of results to manager: {[str(r) for r in entries]}')
        self._result_entries.extend(entries)

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
        logger.info(f'retrieve list of result using output_format {output_format}')
        if output_format == 'list':
            return list(self._result_entries)

        if output_format == "json":
            return json.dumps(pydantic_to_dict(self._result_entries), indent=4)

        # Default return for native format.
        return self._result_entries

    def get_result_by_test(self, test_name: str, output_format: str = "native") -> Any:
        """
        Get list of test result for a given test.

        Args:
            test_name (str): Test name to use to filter results
            output_format (str, optional): format selector. Can be either native/list. Defaults to 'native'.

        Returns:
            list[TestResult]: List of results related to the test.
        """
        logger.info(
            f'retrieve list of result using output_format {output_format} for test {test_name}')
        if output_format == "list":
            return [
                result
                for result in self._result_entries
                if str(result.test) == test_name
            ]

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
        logger.info(
            f'retrieve list of result using output_format {output_format} for host {host_ip}')
        if output_format == "list":
            return [
                result for result in self._result_entries if str(result.name) == host_ip
            ]

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
        logger.info('build list of testcases registered in result-manager')
        result_list = []
        for testcase in self._result_entries:
            if str(testcase.test) not in result_list:
                result_list.append(str(testcase.test))
        logger.debug(f'list of tests name: {result_list}')
        return result_list

    def get_hosts(self) -> List[str]:
        """
        Get list of IP addresses in current manager.

        Returns:
            List[str]: List of IP addresses.
        """
        logger.info('build list of host ip registered in result-manager')
        result_list = []
        for testcase in self._result_entries:
            if str(testcase.name) not in result_list:
                result_list.append(str(testcase.name))
        logger.debug(f'list of tests name: {result_list}')
        return result_list
