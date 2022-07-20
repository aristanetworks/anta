#!/usr/bin/python
# coding: utf-8 -*-

"""
Report management for ANTA.
"""

from operator import itemgetter
from typing import List

from tabulate import tabulate

from .models import TestResult


# pylint: disable=R0903
class Colors:
    """Manage colors for output."""
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


class TableReport():
    """TableReport Generate a Table based on tabulate and TestResult."""

    # Default headers to use if not set by user.
    DEFAULT_HEADERS = ['Device', 'Test', 'Status', 'Message']

    def __init__(self, headers=None, colors: bool = True) -> None:
        """
        __init__ Class constructor

        Args:
            headers (list[str], optional): List of headers. Defaults to None.
        """
        self.report = tabulate([])
        self.content = []
        self._raw_content = []
        self.colors = colors
        self.headers = headers if headers is not None else self.DEFAULT_HEADERS

    def content_sorted_by_host(self, reverse: bool = False):
        """
        content_sorted_by_host Sort content by using host field

        Only valid for line using this structure:
        >>> [entry.host, entry.test, entry.result, entry.message]

        Args:
            reverse (bool, optional): Do reverse sorting. Defaults to False.

        Returns:
            List: List of result to print
        """
        return sorted(self.content, key=itemgetter(0), reverse=reverse)

    def content_sorted_by_test(self, reverse: bool = False):
        """
        content_sorted_by_test Sort content by using test field

        Only valid for line using this structure:
        >>> [entry.host, entry.test, entry.result, entry.message]

        Args:
            reverse (bool, optional): Do reverse sorting. Defaults to False.

        Returns:
            List: List of result to print
        """
        return sorted(self.content, key=itemgetter(1), reverse=reverse)

    def content_sorted_by_result(self, reverse: bool = False):
        """
        content_sorted_by_result Sort content by using result field

        Only valid for line using this structure:
        >>> [entry.host, entry.test, entry.result, entry.message]

        Args:
            reverse (bool, optional): Do reverse sorting. Defaults to False.

        Returns:
            List: List of result to print
        """
        return sorted(self.content, key=itemgetter(2), reverse=reverse)

    def content_sorted_by(self, key_index: int, reverse: bool = False) -> list:
        """
        content_sorted_by Sort content by using a user's defined key ID

        Key ID indicates which column in the inner list to use for sorting

        Args:
            key_index (int): innerkey to use to filter.
            reverse (bool, optional): Do reverse sorting. Defaults to False.

        Returns:
            List: List of result to print
        """
        return sorted(self.content, key=itemgetter(key_index), reverse=reverse)

    def get(self, table_format: str = 'pretty', sort_by: str = 'host',
            reverse: bool = False, enable_colors: bool = True):
        """
        get Expose report.

        Expose report with multiple rendering options:
        - Table style (from tabulate style support)
        - Column sorting
        - Reverse sorting

        Args:
            table_format (str, optional): Table format to use based on tabulate style. Defaults to 'pretty'.
            sort_by (str, optional): Column to sort tests. Defaults to 'host'.
            reverse (bool, optional): Revert sort. Defaults to False.
            enable_colors (bool, optional): Add color to report. Defaults to True.

        Returns:
            tabulate: A tabulate instance
        """
        self.colors = enable_colors
        content = self.build_content()

        if sort_by == 'test':
            content = self.content_sorted_by_test(reverse=reverse)
        elif sort_by == 'result':
            content = self.content_sorted_by_result(reverse=reverse)
        else:
            content = self.content_sorted_by_host(reverse=reverse)

        return tabulate(
            content,
            headers=self.headers,
            tablefmt=table_format,
            colalign=("left", "left", "left", "left")
        )

    def add_content(self, results: List[TestResult]):
        """
        add_content Add content to manage in the report.

        Args:
            results (list[TestResult]): A list of tests.
        """
        self._raw_content += results
        self.content = self.build_content()

    def build_content(self):
        """
        build_content Build output for the report.

        Returns:
            list: A list of tests.
        """
        content = []
        for entry in self._raw_content:
            self.content.append(
                self._table_build_line_result(
                    entry=entry)
            )
        return content

    def _table_build_line_result(self, entry: TestResult, colors: bool = True) -> list:
        """
        _table_build_line_result Add a test to the report.

        Add a test to the report and also do rendering.

        Args:
            entry (TestResult): A test to add to the report
            colors (bool, optional): Select if tests results are colored or not. Defaults to True.

        Returns:
            list: List of data for one line.
        """
        content = []
        if self.colors:
            if entry.result == 'failure':
                content = [entry.host, entry.test, f'{Colors.FAIL}{entry.result}{Colors.ENDC}', entry.message]
            elif entry.result == 'success':
                content = [entry.host, entry.test, f'{Colors.OKGREEN}{entry.result}{Colors.ENDC}', entry.message]
        else:
            content = [entry.host, entry.test,
                       f'{entry.result}', entry.message]
        return content
