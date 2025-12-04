# Copyright (c) 2023-2025 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Report management for ANTA."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from jinja2 import Template
from rich.table import Table
from typing_extensions import deprecated

from anta import RICH_COLOR_PALETTE, RICH_COLOR_THEME
from anta.result_manager.models import AtomicTestResult, TestResult
from anta.tools import convert_categories

if TYPE_CHECKING:
    import pathlib

    from anta.result_manager import ResultManager
    from anta.result_manager.models import AntaTestStatus

logger = logging.getLogger(__name__)


class ReportTable:
    """Create a `rich.Table` instance based on an `anta.result_manager.ResultManager` instance.

    Attributes
    ----------
    title
        Title used when creating the `rich.Table` instance. See `ReportTable.Title` for the default values.
    columns
        Column names used when creating the `rich.Table` instance. See `ReportTable.Columns` for the default values.
    """

    @dataclass
    class Title:
        """Titles for the table report."""

        all: str = "All tests results"
        tests: str = "Summary per test"
        device: str = "Summary per device"

    @dataclass
    class Columns:  # pylint: disable=too-many-instance-attributes
        """Column names for the table report."""

        device: str = "Device"
        test: str = "Test"
        category: str = "Category"
        status: str = "Status"
        messages: str = "Message(s)"
        description: str = "Description"
        number_of_success: str = "# of success"
        number_of_failure: str = "# of failure"
        number_of_skipped: str = "# of skipped"
        number_of_errors: str = "# of errors"
        failed_devices: str = "List of devices with failed or errored tests"
        failed_tests: str = "List of failed or errored tests"

    def __init__(self) -> None:
        """Initialize a ReportTable instance."""
        self.title = ReportTable.Title()
        self.columns = ReportTable.Columns()

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

    @staticmethod
    def _build_table(title: str, columns: list[str]) -> Table:
        """Create an empty Rich table from a title and column names.

        All the rows in the first column are colored using RICH_COLOR_PALETTE.HEADER.

        Parameters
        ----------
        title
            Title of the table.
        columns
            List of the column names.

        Returns
        -------
            A rich `Table` instance.
        """
        table = Table(title=title, show_lines=True)
        if columns:
            table.add_column(columns[0], justify="left", style=RICH_COLOR_PALETTE.HEADER, no_wrap=True)
            for column in columns[1:]:
                table.add_column(column, justify="left")
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

    def generate(self, manager: ResultManager) -> Table:
        """Create a table report with all tests.

        Attributes used to build the table are:

            Table title: `title.all`
            Table columns:
                - `columns.category`
                - `columns.device`
                - `columns.test`
                - `columns.description`
                - `columns.status`
                - `columns.messages`

        Parameters
        ----------
        manager
            A ResultManager instance.

        Returns
        -------
            A fully populated rich `Table`.
        """
        columns = [self.columns.category, self.columns.device, self.columns.test, self.columns.description, self.columns.status, self.columns.messages]

        table = ReportTable._build_table(title=self.title.all, columns=columns)

        for result in manager.results:
            state = self._color_result(result.result)
            message = self._split_list_to_txt_list(result.messages) if len(result.messages) > 0 else ""
            categories = ", ".join(convert_categories(result.categories))
            renderables: list[str | None] = [categories, str(result.name), result.test, result.description, state, message]
            table.add_row(*renderables)
        return table

    def generate_expanded(self, manager: ResultManager) -> Table:
        """Create a table report with all tests, expanded atomic results, test descriptions.

        Attributes used to build the table are:

            Table title: `title.all`
            Table columns:
                - `columns.category`
                - `columns.device`
                - `columns.test`
                - `columns.description`
                - `columns.status`
                - `columns.messages`

        Parameters
        ----------
        manager
            A ResultManager instance.

        Returns
        -------
        Table
            A fully populated rich `Table`.
        """
        columns = [
            self.columns.category,
            self.columns.device,
            self.columns.test,
            self.columns.description,
            self.columns.status,
            self.columns.messages,
        ]

        table = ReportTable._build_table(title=self.title.all, columns=columns)

        def add_line(result: TestResult | AtomicTestResult, suffix: str | None = None) -> None:
            categories = device = test = None

            if isinstance(result, TestResult):
                categories = ", ".join(convert_categories(result.categories))
                device = str(result.name)
                test = result.test
            else:  # AtomicTestResult
                if suffix is None:  # pragma: no cover
                    # This should never happen
                    msg = "Cannot generate a report line for AtomicTestResult without a suffix"
                    raise ValueError(msg)
                test = f"{result.parent.test} {suffix}"

            state = self._color_result(result.result)
            message = self._split_list_to_txt_list(result.messages) if len(result.messages) > 0 else ""
            renderables = [categories, test, device, result.description, state, message]
            table.add_row(*renderables)

        for result in manager.results:
            add_line(result)
            for index, atomic_res in enumerate(result.atomic_results):
                add_line(atomic_res, f"{index + 1}/{len(result.atomic_results)}")
        return table

    def generate_summary_by_test(self, manager: ResultManager, *, tests: set[str] | None = None) -> Table:
        """Create a table report with results aggregated per test.

        Attributes used to build the table are:

            Table title: `title.tests`
            Table columns:
                - `columns.test`
                - `columns.number_of_success`
                - `columns.number_of_skipped`
                - `columns.number_of_failure`
                - `columns.number_of_errors`
                - `columns.failed_devices`

        Parameters
        ----------
        manager
            A ResultManager instance.
        tests
            List of test names to include. None to select all tests.

        Returns
        -------
            A fully populated rich `Table`.
        """
        columns = [
            self.columns.test,
            self.columns.number_of_success,
            self.columns.number_of_skipped,
            self.columns.number_of_failure,
            self.columns.number_of_errors,
            self.columns.failed_devices,
        ]
        table = ReportTable._build_table(title=self.title.tests, columns=columns)

        for test, stats in manager.test_stats.items():
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

    def generate_summary_by_device(
        self,
        manager: ResultManager,
        *,
        devices: set[str] | None = None,
    ) -> Table:
        """Create a table report with results aggregated per device.

        Attributes used to build the table are:

            Table title: `title.device`
            Table columns:
                - `columns.device`
                - `columns.number_of_success`
                - `columns.number_of_skipped`
                - `columns.number_of_failure`
                - `columns.number_of_errors`
                - `columns.failed_tests`

        Parameters
        ----------
        manager
            A ResultManager instance.
        devices
            List of device names to include. None to select all devices.

        Returns
        -------
            A fully populated rich `Table`.
        """
        columns = [
            self.columns.device,
            self.columns.number_of_success,
            self.columns.number_of_skipped,
            self.columns.number_of_failure,
            self.columns.number_of_errors,
            self.columns.failed_tests,
        ]
        table = ReportTable._build_table(title=self.title.device, columns=columns)
        for device, stats in manager.device_stats.items():
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

    @deprecated("This method is deprecated, use `generate` instead. This will be removed in ANTA v2.0.0.", category=DeprecationWarning)
    def report_all(self, manager: ResultManager, title: str = "All tests results") -> Table:
        """Create a table report with all tests for one or all devices.

        Create table with full output: Device | Test Name | Test Status | Message(s) | Test description | Test category

        Warnings
        --------
        * This method sets the `report.title.all` value which impacts future calls to generate_* methods.

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
        self.title.all = title
        return self.generate(manager)

    @deprecated("This method is deprecated, use `generate_summary_tests` instead. This will be removed in ANTA v2.0.0.", category=DeprecationWarning)
    def report_summary_tests(
        self,
        manager: ResultManager,
        tests: list[str] | None = None,
        title: str = "Summary per test",
    ) -> Table:
        """Create a table report with result aggregated per test.

        Create table with full output:
        Test Name | # of success | # of skipped | # of failure | # of errors | List of failed or error nodes

        Warnings
        --------
        * This method sets the `report.title.all` value which impacts future calls to generate_* methods.

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
        self.title.tests = title
        return self.generate_summary_by_test(manager, tests=set(tests) if tests is not None else None)

    @deprecated("This method is deprecated, use `generate_summary_devices` instead. This will be removed in ANTA v2.0.0.", category=DeprecationWarning)
    def report_summary_devices(
        self,
        manager: ResultManager,
        devices: list[str] | None = None,
        title: str = "Summary per device",
    ) -> Table:
        """Create a table report with result aggregated per device.

        Create table with full output: Device | # of success | # of skipped | # of failure | # of errors | List of failed or error test cases

        Warnings
        --------
        * This method sets the `report.title.all` value which impacts future calls to generate_* methods.

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
        self.title.device = title
        return self.generate_summary_by_device(manager, devices=set(devices) if devices is not None else None)


class ReportJinja:  # pylint: disable=too-few-public-methods
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
