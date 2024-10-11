# Copyright (c) 2023-2024 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Report management for ANTA."""

# pylint: disable = too-few-public-methods
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from jinja2 import Template
from rich.table import Table

from anta import RICH_COLOR_PALETTE, RICH_COLOR_THEME
from anta.tools import convert_categories

if TYPE_CHECKING:
    import pathlib

    from anta.result_manager import ResultManager
    from anta.result_manager.models import AntaTestStatus, TestResult

logger = logging.getLogger(__name__)


class ReportTable:
    """TableReport Generate a Table based on TestResult."""

    @dataclass()
    class Headers:  # pylint: disable=too-many-instance-attributes
        """Headers for the table report."""

        device: str = "Device"
        test_case: str = "Test Name"
        number_of_success: str = "# of success"
        number_of_failure: str = "# of failure"
        number_of_skipped: str = "# of skipped"
        number_of_errors: str = "# of errors"
        list_of_error_nodes: str = "List of failed or error nodes"
        list_of_error_tests: str = "List of failed or error test cases"

    def _split_list_to_txt_list(self, usr_list: list[str], delimiter: str | None = None) -> str:
        """Split list to multi-lines string.

        Parameters
        ----------
        usr_list : list[str]
            List of string to concatenate.
        delimiter : str, optional
            A delimiter to use to start string. Defaults to None.

        Returns
        -------
        str
            Multi-lines string.

        """
        if delimiter is not None:
            return "\n".join(f"{delimiter} {line}" for line in usr_list)
        return "\n".join(f"{line}" for line in usr_list)

    def _build_headers(self, headers: list[str], table: Table) -> Table:
        """Create headers for a table.

        First key is considered as header and is colored using RICH_COLOR_PALETTE.HEADER

        Parameters
        ----------
        headers
            List of headers.
        table
            A rich Table instance.

        Returns
        -------
        Table
            A rich `Table` instance with headers.

        """
        for idx, header in enumerate(headers):
            if idx == 0:
                table.add_column(header, justify="left", style=RICH_COLOR_PALETTE.HEADER, no_wrap=True)
            else:
                table.add_column(header, justify="left")
        return table

    def _color_result(self, status: AntaTestStatus) -> str:
        """Return a colored string based on an AntaTestStatus.

        Parameters
        ----------
        status
            AntaTestStatus enum to color.

        Returns
        -------
        str
            The colored string.
        """
        color = RICH_COLOR_THEME.get(str(status), "")
        return f"[{color}]{status}" if color != "" else str(status)

    def report_all(self, manager: ResultManager, title: str = "All tests results") -> Table:
        """Create a table report with all tests for one or all devices.

        Create table with full output: Device | Test Name | Test Status | Message(s) | Test description | Test category

        Parameters
        ----------
        manager
            A ResultManager instance.
        title
            Title for the report. Defaults to 'All tests results'.

        Returns
        -------
        Table
            A fully populated rich `Table`.
        """
        table = Table(title=title, show_lines=True)
        headers = ["Device", "Test Name", "Test Status", "Message(s)", "Test description", "Test category"]
        table = self._build_headers(headers=headers, table=table)

        def add_line(result: TestResult) -> None:
            state = self._color_result(result.result)
            message = self._split_list_to_txt_list(result.messages) if len(result.messages) > 0 else ""
            categories = ", ".join(convert_categories(result.categories))
            table.add_row(str(result.name), result.test, state, message, result.description, categories)

        for result in manager.results:
            add_line(result)
        return table

    def report_summary_tests(
        self,
        manager: ResultManager,
        tests: list[str] | None = None,
        title: str = "Summary per test",
    ) -> Table:
        """Create a table report with result aggregated per test.

        Create table with full output:
        Test Name | # of success | # of skipped | # of failure | # of errors | List of failed or error nodes

        Parameters
        ----------
        manager
            A ResultManager instance.
        tests
            List of test names to include. None to select all tests.
        title
            Title of the report.

        Returns
        -------
        Table
            A fully populated rich `Table`.
        """
        table = Table(title=title, show_lines=True)
        headers = [
            self.Headers.test_case,
            self.Headers.number_of_success,
            self.Headers.number_of_skipped,
            self.Headers.number_of_failure,
            self.Headers.number_of_errors,
            self.Headers.list_of_error_nodes,
        ]
        table = self._build_headers(headers=headers, table=table)
        for test, stats in sorted(manager.test_stats.items()):
            if tests is None or test in tests:
                table.add_row(
                    test,
                    str(stats.devices_success_count),
                    str(stats.devices_skipped_count),
                    str(stats.devices_failure_count),
                    str(stats.devices_error_count),
                    ", ".join(stats.devices_failure),
                )
        return table

    def report_summary_devices(
        self,
        manager: ResultManager,
        devices: list[str] | None = None,
        title: str = "Summary per device",
    ) -> Table:
        """Create a table report with result aggregated per device.

        Create table with full output: Device | # of success | # of skipped | # of failure | # of errors | List of failed or error test cases

        Parameters
        ----------
        manager
            A ResultManager instance.
        devices
            List of device names to include. None to select all devices.
        title
            Title of the report.

        Returns
        -------
        Table
            A fully populated rich `Table`.
        """
        table = Table(title=title, show_lines=True)
        headers = [
            self.Headers.device,
            self.Headers.number_of_success,
            self.Headers.number_of_skipped,
            self.Headers.number_of_failure,
            self.Headers.number_of_errors,
            self.Headers.list_of_error_tests,
        ]
        table = self._build_headers(headers=headers, table=table)
        for device, stats in sorted(manager.device_stats.items()):
            if devices is None or device in devices:
                table.add_row(
                    device,
                    str(stats.tests_success_count),
                    str(stats.tests_skipped_count),
                    str(stats.tests_failure_count),
                    str(stats.tests_error_count),
                    ", ".join(stats.tests_failure),
                )
        return table


class ReportJinja:
    """Report builder based on a Jinja2 template."""

    def __init__(self, template_path: pathlib.Path) -> None:
        """Create a ReportJinja instance."""
        if not template_path.is_file():
            msg = f"template file is not found: {template_path}"
            raise FileNotFoundError(msg)

        self.template_path = template_path

    def render(self, data: list[dict[str, Any]], *, trim_blocks: bool = True, lstrip_blocks: bool = True) -> str:
        """Build a report based on a Jinja2 template.

        Report is built based on a J2 template provided by user.
        Data structure sent to template is:

        Example
        -------
        ```
        >>> print(ResultManager.json)
        [
            {
                name: ...,
                test: ...,
                result: ...,
                messages: [...]
                categories: ...,
                description: ...,
            }
        ]
        ```

        Parameters
        ----------
        data
            List of results from `ResultManager.results`.
        trim_blocks
            enable trim_blocks for J2 rendering.
        lstrip_blocks
            enable lstrip_blocks for J2 rendering.

        Returns
        -------
        str
            Rendered template

        """
        with self.template_path.open(encoding="utf-8") as file_:
            template = Template(file_.read(), trim_blocks=trim_blocks, lstrip_blocks=lstrip_blocks)

        return template.render({"data": data})
