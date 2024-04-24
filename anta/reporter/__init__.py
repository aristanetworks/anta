# Copyright (c) 2023-2024 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Report management for ANTA."""

# pylint: disable = too-few-public-methods
from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

from jinja2 import Template
from rich.table import Table

from anta import RICH_COLOR_PALETTE, RICH_COLOR_THEME

if TYPE_CHECKING:
    import pathlib

    from anta.custom_types import TestStatus
    from anta.result_manager import ResultManager
    from anta.result_manager.models import TestResult

logger = logging.getLogger(__name__)


class ReportTable:
    """TableReport Generate a Table based on TestResult."""

    def _split_list_to_txt_list(self, usr_list: list[str], delimiter: str | None = None) -> str:
        """Split list to multi-lines string.

        Args:
        ----
            usr_list (list[str]): List of string to concatenate
            delimiter (str, optional): A delimiter to use to start string. Defaults to None.

        Returns
        -------
            str: Multi-lines string

        """
        if delimiter is not None:
            return "\n".join(f"{delimiter} {line}" for line in usr_list)
        return "\n".join(f"{line}" for line in usr_list)

    def _build_headers(self, headers: list[str], table: Table) -> Table:
        """Create headers for a table.

        First key is considered as header and is colored using RICH_COLOR_PALETTE.HEADER

        Args:
        ----
            headers: List of headers.
            table: A rich Table instance.

        Returns
        -------
            A rich `Table` instance with headers.

        """
        for idx, header in enumerate(headers):
            if idx == 0:
                table.add_column(header, justify="left", style=RICH_COLOR_PALETTE.HEADER, no_wrap=True)
            elif header == "Test Name":
                # We always want the full test name
                table.add_column(header, justify="left", no_wrap=True)
            else:
                table.add_column(header, justify="left")
        return table

    def _color_result(self, status: TestStatus) -> str:
        """Return a colored string based on the status value.

        Args:
        ----
            status (TestStatus): status value to color.

        Returns
        -------
        str: the colored string

        """
        color = RICH_COLOR_THEME.get(status, "")
        return f"[{color}]{status}" if color != "" else str(status)

    def report_all(self, manager: ResultManager, title: str = "All tests results") -> Table:
        """Create a table report with all tests for one or all devices.

        Create table with full output: Host / Test / Status / Message

        Args:
        ----
            manager: A ResultManager instance.
            title: Title for the report. Defaults to 'All tests results'.

        Returns
        -------
            A fully populated rich `Table`

        """
        table = Table(title=title, show_lines=True)
        headers = ["Device", "Test Name", "Test Status", "Message(s)", "Test description", "Test category"]
        table = self._build_headers(headers=headers, table=table)

        def add_line(result: TestResult) -> None:
            state = self._color_result(result.result)
            message = self._split_list_to_txt_list(result.messages) if len(result.messages) > 0 else ""
            categories = ", ".join(result.categories)
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

        Create table with full output: Test | Number of success | Number of failure | Number of error | List of nodes in error or failure

        Args:
        ----
            manager: A ResultManager instance.
            tests: List of test names to include. None to select all tests.
            title: Title of the report.

        Returns
        -------
            A fully populated rich `Table`.
        """
        table = Table(title=title, show_lines=True)
        headers = [
            "Test Case",
            "# of success",
            "# of skipped",
            "# of failure",
            "# of errors",
            "List of failed or error nodes",
        ]
        table = self._build_headers(headers=headers, table=table)
        for test in manager.get_tests():
            if tests is None or test in tests:
                results = manager.filter_by_tests({test}).results
                nb_failure = len([result for result in results if result.result == "failure"])
                nb_error = len([result for result in results if result.result == "error"])
                list_failure = [result.name for result in results if result.result in ["failure", "error"]]
                nb_success = len([result for result in results if result.result == "success"])
                nb_skipped = len([result for result in results if result.result == "skipped"])
                table.add_row(
                    test,
                    str(nb_success),
                    str(nb_skipped),
                    str(nb_failure),
                    str(nb_error),
                    str(list_failure),
                )
        return table

    def report_summary_devices(
        self,
        manager: ResultManager,
        devices: list[str] | None = None,
        title: str = "Summary per device",
    ) -> Table:
        """Create a table report with result aggregated per device.

        Create table with full output: Host | Number of success | Number of failure | Number of error | List of nodes in error or failure

        Args:
        ----
            manager: A ResultManager instance.
            devices: List of device names to include. None to select all devices.
            title: Title of the report.

        Returns
        -------
            A fully populated rich `Table`.
        """
        table = Table(title=title, show_lines=True)
        headers = [
            "Device",
            "# of success",
            "# of skipped",
            "# of failure",
            "# of errors",
            "List of failed or error test cases",
        ]
        table = self._build_headers(headers=headers, table=table)
        for device in manager.get_devices():
            if devices is None or device in devices:
                results = manager.filter_by_devices({device}).results
                nb_failure = len([result for result in results if result.result == "failure"])
                nb_error = len([result for result in results if result.result == "error"])
                list_failure = [result.test for result in results if result.result in ["failure", "error"]]
                nb_success = len([result for result in results if result.result == "success"])
                nb_skipped = len([result for result in results if result.result == "skipped"])
                table.add_row(
                    device,
                    str(nb_success),
                    str(nb_skipped),
                    str(nb_failure),
                    str(nb_error),
                    str(list_failure),
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

        Args:
        ----
            data: List of results from ResultManager.results
            trim_blocks: enable trim_blocks for J2 rendering.
            lstrip_blocks: enable lstrip_blocks for J2 rendering.

        Returns
        -------
            Rendered template

        """
        with self.template_path.open(encoding="utf-8") as file_:
            template = Template(file_.read(), trim_blocks=trim_blocks, lstrip_blocks=lstrip_blocks)

        return template.render({"data": data})
