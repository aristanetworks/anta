#!/usr/bin/python
# coding: utf-8 -*-

"""
Result Manager Module for ANTA.
"""

import json
from typing import List

from tabulate import tabulate

from .models import ListResult, TestResult
from .report import TableReport


class ResultManager():
    """ResultManager Helper to manage Test Results and generate reports."""

    def __init__(self) -> None:
        """__init__ Class constructor."""
        self._result_entries = ListResult()

    def add_test_result(self, entry: TestResult) -> None:
        """
        add_test_result Add a result to the list

        Args:
            entry (TestResult): TestResult data to add to the report
        """
        self._result_entries.append(entry)

    def get_results(self, output_format: str = 'native') -> any:
        """
        get_results Expose list of all test results in different format

        Support multiple format:
        - native: ListResults format
        - list: a list of TestResult
        - json: a native JSON format

        Args:
            output_format (str, optional): format selector. Can be either native/list/json. Defaults to 'native'.

        Returns:
            any: List of results.
        """
        if output_format == 'list':
            return list(self._result_entries)

        if output_format == 'json':
            return json.loads([result.json() for result in self._result_entries])

        # Default return for native format.
        return self._result_entries

    def get_result_by_test(self, test_name: str) -> List[TestResult]:
        """
        get_result_by_test Get list of test result for a given test.

        Args:
            test_name (str): Test name to use to filter results

        Returns:
            list[TestResult]: List of results related to the test.
        """
        return [result for result in self._result_entries if str(result.test) == test_name]

    def get_result_by_host(self, host_ip: str) -> List[TestResult]:
        """
        get_result_by_test Get list of test result for a given host.

        Args:
            host_ip (str): IP Address of the host to use to filter results.

        Returns:
            list[TestResult]: List of results related to the host.
        """
        return [result for result in self._result_entries if str(result.host) == host_ip]

    def table_report(self, sort_by: str = 'host', reverse: bool = False, colors: bool = True) -> tabulate:
        """
        table_report Build a table report of all tests

        Args:
            sort_by (str, optional): Key to use to filter result. Can be either host/test/result. Defaults to 'host'.
            reverse (bool, optional): Enable reverse sorting. Defaults to False.
            colors (bool, optional): Select if tests results are colored or not. Defaults to True.

        Returns:
            tabulate: A Tabulate str that can be printed.
        """
        report = TableReport()
        report.add_content(
            results=self.get_results(output_format='list'),
        )
        return report.get(sort_by=sort_by, reverse=reverse, enable_colors=colors)
