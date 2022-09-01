#!/usr/bin/python
# coding: utf-8 -*-

"""
Report management for ANTA.
"""

import logging
from typing import List, Any

from rich.table import Table
from anta.result_manager import ResultManager
from .models import ColorManager

logger = logging.getLogger(__name__)


# Source: https://rich.readthedocs.io/en/stable/appendix/colors.html
# pylint: disable=R0903
class RICH_COLOR_THEME:
    """Color code for text rendering."""
    FAILURE = "orange3"
    ERROR = "red3"
    SUCCESS = "green"
    SKIPPED = "orange4"
    HEADER = "cyan"


class ReportTable():
    """TableReport Generate a Table based on tabulate and TestResult."""

    def __init__(self) -> None:
        """
        __init__ Class constructor
        """
        self.colors = []
        self.colors.append(ColorManager(
            level='success', color=RICH_COLOR_THEME.SUCCESS))
        self.colors.append(ColorManager(
            level='failure', color=RICH_COLOR_THEME.FAILURE))
        self.colors.append(ColorManager(
            level='error', color=RICH_COLOR_THEME.ERROR))
        self.colors.append(ColorManager(
            level='skipped', color=RICH_COLOR_THEME.SKIPPED))

    def _split_list_to_txt_list(self, usr_list: List[str], delimiter: str = None) -> str:
        """
        Split list to multi-lines string

        Args:
            usr_list (List[str]): List of string to concatenate
            delimiter (str, optional): A delimiter to use to start string. Defaults to None.

        Returns:
            str: Multi-lines string
        """
        if delimiter is not None:
            return "\n".join(f"{delimiter} {line}" for line in usr_list)
        return "\n".join(f"{line}" for line in usr_list)

    def _build_headers(self, headers: List[str], table: Table) -> Table:
        """
        Create headers for a table.

        First key is considered as header and is colored using RICH_COLOR_THEME.HEADER

        Args:
            headers (List[str]): List of headers
            table (Table): A rich Table instance

        Returns:
            Table: A rich Table instance with headers
        """
        for idx, header in enumerate(headers):
            if idx == 0:
                table.add_column(header, justify="left", style=RICH_COLOR_THEME.HEADER, no_wrap=True)
            else:
                table.add_column(header, justify="left")
        return table

    def _color_result(self, status: str, output_type: str = 'Text') -> Any:
        """
        Helper to implement color based on test status.

        It gives output for either standard str or Text() colorized with Style()

        Args:
            status (str): status value to colorized
            output_type (str, optional): Which format to output code. Defaults to 'Text'.

        Returns:
            Any: Can be either str or Text with Style
        """
        if len([result for result in self.colors if str(result.level).upper() == status.upper()]) == 1:
            code: ColorManager = [result for result in self.colors if str(
                result.level).upper() == status.upper()][0]
            return code.style_rich() if output_type == 'Text' else code.string()
        return None

    def report_all(self, result_manager: ResultManager, host: str = None, testcase: str = None, title: str = 'All tests results') -> Table:
        """
        Create a table report with all tests for one or all devices.

        Create table with full output: Host / Test / Status / Message

        Args:
            result_manager (ResultManager): A manager with a list of tests.
            host (str, optional): IP Address of a host to search for. Defaults to None.
            testcase (str, optional): A test name to search for. Defaults to None.
            title (str, optional): Title for the report. Defaults to 'All tests results'.

        Returns:
            Table: A fully populated rich Table
        """
        table = Table(title=title)
        headers = ['Device IP', 'Test Name', 'Test Status', 'Message(s)']
        table = self._build_headers(headers=headers, table=table)

        for result in result_manager.get_results(output_format='list'):
            # pylint: disable=R0916
            if (host is None and testcase is None) \
                    or (host is not None and str(result.host) == host) \
                    or (testcase is not None and testcase == str(result.test)):
                logger.debug(f'adding new entry in table: {result.host} / {result.test} / {result.result}')
                state = self._color_result(status=str(
                    result.result), output_type='str')
                message = self._split_list_to_txt_list(
                    result.messages) if len(result.messages) > 0 else ''
                table.add_row(
                    str(result.host),
                    result.test,
                    state,
                    message
                )
        return table

    def report_summary_tests(self, result_manager: ResultManager, testcase: str = None, title: str = 'Summary per test case') -> Table:
        """
        Create a table report with result agregated per test.

        Create table with full output: Test / Number of success / Number of failure / Number of error / List of nodes in error or failure

        Args:
            result_manager (ResultManager): A manager with a list of tests.
            testcase (str, optional): A test name to search for. Defaults to None.
            title (str, optional): Title for the report. Defaults to 'All tests results'.

        Returns:
            Table: A fully populated rich Table
        """
        # sourcery skip: class-extract-method
        table = Table(title=title)
        headers = ['Test Case', '# of success', '# of failure', '# of errors', 'List of failed or error nodes']
        table = self._build_headers(headers=headers, table=table)
        for testcase_read in result_manager.get_testcases():
            if testcase is None or str(testcase_read) == testcase:
                results = result_manager.get_result_by_test(testcase_read)
                nb_failure = len(
                    [result for result in results if result.result == 'failure'])
                nb_error = len(
                    [result for result in results if result.result == 'error'])
                list_failure = [
                    str(result.host) for result in results if result.result in ['failure', 'error']]
                nb_success = len(
                    [result for result in results if result.result == 'success'])
                table.add_row(
                    testcase_read,
                    str(nb_success),
                    str(nb_failure),
                    str(nb_error),
                    str(list_failure)
                )
        return table

    def report_summary_hosts(self, result_manager: ResultManager, host: str = None, title: str = 'Summary per host') -> Table:
        """
        Create a table report with result agregated per host.

        Create table with full output: Host / Number of success / Number of failure / Number of error / List of nodes in error or failure

        Args:
            result_manager (ResultManager): A manager with a list of tests.
            host (str, optional): IP Address of a host to search for. Defaults to None.
            title (str, optional): Title for the report. Defaults to 'All tests results'.

        Returns:
            Table: A fully populated rich Table
        """
        table = Table(title=title)
        headers = ['Host IP', '# of success', '# of failure',
                   '# of errors', 'List of failed ortest case']
        table = self._build_headers(headers=headers, table=table)
        for host_read in result_manager.get_hosts():
            if host is None or str(host_read) == host:
                results = result_manager.get_result_by_host(host_read)
                logger.debug('data to use for computation')
                logger.debug(f'{host}: {results}')
                nb_failure = len(
                    [result for result in results if result.result == 'failure'])
                nb_error = len(
                    [result for result in results if result.result == 'error'])
                list_failure = [
                    str(result.test) for result in results if result.result in ['failure', 'error']]
                nb_success = len(
                    [result for result in results if result.result == 'success'])
                table.add_row(
                    str(host_read),
                    str(nb_success),
                    str(nb_failure),
                    str(nb_error),
                    str(list_failure)
                )
        return table
