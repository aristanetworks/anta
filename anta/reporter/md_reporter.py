# Copyright (c) 2023-2025 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Markdown report generator for ANTA test results."""

from __future__ import annotations

import logging
import re
from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from typing import TYPE_CHECKING, Any, ClassVar, TextIO

from anta.constants import ACRONYM_CATEGORIES, MD_REPORT_TOC, MD_REPORT_TOC_WITH_RUN_OVERVIEW
from anta.logger import anta_log_exception
from anta.result_manager.models import AntaTestStatus, TestResult
from anta.tools import convert_categories, convert_single_category_cached

if TYPE_CHECKING:
    from collections.abc import Generator
    from pathlib import Path

    from anta.result_manager import ResultManager


logger = logging.getLogger(__name__)

# Column names defined as constants to make Sonar happy.
CATEGORIES = "Categories"
CATEGORIES_FAILED = "Categories Failed"
CATEGORIES_SKIPPED = "Categories Skipped"
CUSTOM_FIELD = "Custom Field"
DESCRIPTION = "Description"
DEVICE = "Device"
MESSAGES = "Messages"
RESULT = "Result"
TEST = "Test"
TEST_CATEGORY = "Test Category"
TOTAL_TESTS = "Total Tests"

STATUS_MAP = {
    AntaTestStatus.SUCCESS: "✅&nbsp;Success",
    AntaTestStatus.FAILURE: "❌&nbsp;Failure",
    AntaTestStatus.ERROR: "❗&nbsp;Error",
    AntaTestStatus.SKIPPED: "⏭️&nbsp;Skipped",
    AntaTestStatus.UNSET: "Unset",
}
"""Mapping of `AntaTestStatus` to their string representation with icons and non-breaking spaces for Markdown."""


class MDReportBase(ABC):
    """Base class for all sections subclasses.

    Every subclasses must implement the `generate_section` method that uses the `ResultManager` object
    to generate and write content to the provided markdown file.
    """

    ICON: str = ""
    """Optional icon to prepend to the section header."""

    def __init__(self, mdfile: TextIO, results: ResultManager, extra_data: dict[str, Any] | None = None) -> None:
        """Initialize the MDReportBase with an open markdown file object to write to and a ResultManager instance.

        Parameters
        ----------
        mdfile
            An open file object to write the markdown data into.
        results
            The ResultsManager instance containing all test results.
        extra_data
            Optional extra data dictionary. Can be used by subclasses to render additional data.
        """
        self.mdfile = mdfile
        self.results = results
        self.extra_data = extra_data

    @abstractmethod
    def generate_section(self) -> None:
        """Abstract method to generate a specific section of the markdown report.

        Must be implemented by subclasses.
        """
        msg = "Must be implemented by subclasses"
        raise NotImplementedError(msg)

    def generate_rows(self) -> Generator[str, None, None]:
        """Generate the rows of a markdown table for a specific report section.

        Subclasses can implement this method to generate the content of the table rows.
        """
        msg = "Subclasses should implement this method"
        raise NotImplementedError(msg)

    def generate_heading_name(self) -> str:
        """Generate a formatted heading name based on the class name.

        Returns
        -------
        str
            Formatted header name.

        Example
        -------
        - `ANTAReport` will become `ANTA Report`.
        - `TestResultsSummary` will become `Test Results Summary`.
        """
        class_name = self.__class__.__name__

        # Split the class name into words, keeping acronyms together
        words = re.findall(r"[A-Z]?[a-z]+|[A-Z]+(?=[A-Z][a-z]|\d|\W|$)|\d+", class_name)

        # Capitalize each word, but keep acronyms in all caps
        formatted_words = [word if word.isupper() else word.capitalize() for word in words]

        return " ".join(formatted_words)

    def write_table(self, table_heading: list[str], *, last_table: bool = False) -> None:
        """Write a markdown table with a table heading and multiple rows to the markdown file.

        Parameters
        ----------
        table_heading
            List of strings to join for the table heading.
        last_table
            Flag to determine if it's the last table of the markdown file to avoid unnecessary new line. Defaults to False.
        """
        self.mdfile.write("\n".join(table_heading) + "\n")
        for row in self.generate_rows():
            self.mdfile.write(row)
        if not last_table:
            self.mdfile.write("\n")

    def write_heading(self, heading_level: int) -> None:
        """Write a markdown heading to the markdown file.

        The heading name used is the class name.

        Handles adding the icon (if defined) and creating an explicit HTML anchor so TOC links
        work regardless of icons.

        Parameters
        ----------
        heading_level
            The level of the heading (1-6).

        Example
        -------
        `## [icon] Test Results Summary <a id="test-results-summary"></a>`
        """
        # Ensure the heading level is within the valid range of 1 to 6
        heading_level = max(1, min(heading_level, 6))
        heading_name = self.generate_heading_name()

        # Calculate the anchor ID expected by the TOC (kebab-case)
        anchor_id = heading_name.lower().replace(" ", "-")

        # Construct display name with icon
        display_name = f"{self.ICON} {heading_name}" if self.ICON else heading_name

        # Write header with explicit anchor
        heading = f'{"#" * heading_level} {display_name} <a id="{anchor_id}"></a>'

        self.mdfile.write(f"{heading}\n\n")

    def safe_markdown(self, text: str | None) -> str:
        """Escape markdown characters in the text to prevent markdown rendering issues.

        Parameters
        ----------
        text
            The text to escape markdown characters from.

        Returns
        -------
        str
            The text with escaped markdown characters.
        """
        # Custom field from a TestResult object can be None
        if text is None:
            return ""

        # Escape pipes so they don't break tables
        text = text.replace("|", r"\|")

        # Replace newlines with <br> to preserve line breaks in HTML
        return text.replace("\n", "<br>")

    def format_snake_case_to_title_case(self, value: str) -> str:
        """Format a snake_case string to a Title Cased string with spaces, handling known network protocol or feature acronyms.

        Parameters
        ----------
        value
            A string value to be formatted.

        Returns
        -------
        str
            The value formatted in Title Cased.

        Example
        -------
        - "hello_world" becomes "Hello World"
        - "anta_version" becomes "ANTA Version"
        """
        if not value:
            return ""

        parts = value.split("_")
        processed_parts = []
        for part in parts:
            if part.lower() in ACRONYM_CATEGORIES:
                processed_parts.append(part.upper())
            else:
                processed_parts.append(part.capitalize())

        return " ".join(processed_parts)

    # Value could be anything
    def format_value(self, value: Any) -> str:  # noqa: ANN401
        """Format different types of values for display in the report.

        Handles datetime, timedelta, lists, and other types by converting them to
        human-readable string representations.

        Handles only positive timedelta values.

        Parameters
        ----------
        value
            A value of any type to be formatted.

        Returns
        -------
        str
            The value formatted to a human-readable string.

        Example
        -------
        - datetime.now() becomes "YYYY-MM-DD HH:MM:SS.milliseconds"
        - timedelta(hours=1, minutes=5, seconds=30) becomes "1 hour, 5 minutes, 30 seconds"
        - ["item1", "item2"] becomes "item1, item2"
        - 123 becomes "123"
        """
        if isinstance(value, datetime):
            return value.isoformat(sep=" ", timespec="milliseconds")

        if isinstance(value, timedelta):
            return self.format_timedelta(value)

        if isinstance(value, list):
            return ", ".join(str(v_item) for v_item in value)

        return str(value)

    def format_timedelta(self, value: timedelta) -> str:
        """Format a timedelta object into a human-readable string.

        Handles positive timedelta values. Milliseconds are shown only
        if they are the sole component of a duration less than 1 second.
        Does not format "days"; 2 days will return 48 hours.

        Parameters
        ----------
        value
            The timedelta object to be formatted.

        Returns
        -------
        str
            The timedelta object formatted to a human-readable string.
        """
        total_seconds = int(value.total_seconds())

        if total_seconds < 0:
            return "Invalid duration"

        if total_seconds == 0 and value.microseconds == 0:
            return "0 seconds"

        parts = []

        hours = total_seconds // 3600
        if hours > 0:
            parts.append(f"{hours} hour{'s' if hours != 1 else ''}")
        minutes = (total_seconds % 3600) // 60
        if minutes > 0:
            parts.append(f"{minutes} minute{'s' if minutes != 1 else ''}")
        seconds = total_seconds % 60
        if seconds > 0:
            parts.append(f"{seconds} second{'s' if seconds != 1 else ''}")
        milliseconds = value.microseconds // 1000
        if milliseconds > 0 and not parts and total_seconds == 0:
            parts.append(f"{milliseconds} millisecond{'s' if milliseconds != 1 else ''}")

        return ", ".join(parts) if parts else "0 seconds"

    def format_status(self, status: AntaTestStatus) -> str:
        """Format result status with icon."""
        return STATUS_MAP.get(status, status.upper())

    @staticmethod
    def generate_table_heading(columns: list[str], align: str = ":-") -> list[str]:
        """Generate a list with the table header and its alignment row.

        Parameters
        ----------
        columns
            List of column names to build the table header.
        align
            Markdown alignment string (e.g., ':-', ':-:', '-:'). Defaults to left align.

        Returns
        -------
        list[str]
            A list with the table header and its alignment row.

        """
        header_row = f"| {' | '.join(columns)} |"
        alignment_row = f"| {' | '.join([align] * len(columns))} |"
        return [header_row, alignment_row]


class ANTAReport(MDReportBase):
    """Generate the `# ANTA Report` section of the markdown report."""

    ICON = "📊"

    def __init__(self, mdfile: TextIO, results: ResultManager, extra_data: dict[str, Any] | None = None) -> None:
        """Initialize the `# ANTA Report` section.

        Set the proper TOC to the `toc` attribute depending if `extra_data` is provided.
        """
        super().__init__(mdfile, results, extra_data)

        # Check it there are keys remaining after ignoring _report_options
        has_run_data = False
        if self.extra_data:
            data_keys = set(self.extra_data.keys()) - {"_report_options"}
            has_run_data = len(data_keys) > 0

        self.toc = MD_REPORT_TOC_WITH_RUN_OVERVIEW if has_run_data else MD_REPORT_TOC

    def generate_section(self) -> None:
        """Generate the `# ANTA Report` section of the markdown report."""
        self.write_heading(heading_level=1)
        self.mdfile.write(self.toc + "\n\n")


class RunOverview(MDReportBase):
    """Generate the `## Run Overview` section of the markdown report.

    The `extra_data` dictionary containing the desired run information
    must be provided to the initializer to generate this section.

    NOTE: If present, the `_report_options` key is ignored from the `extra_data`
    dictionary as it is used for other sections.
    """

    ICON = "📋"

    _TABLE_COLUMNS: ClassVar[list[str]] = ["⚙️ Run Metric", "📝 Details"]

    TABLE_HEADING: list[str] = MDReportBase.generate_table_heading(columns=_TABLE_COLUMNS)

    def __init__(self, mdfile: TextIO, results: ResultManager, extra_data: dict[str, Any] | None = None) -> None:
        """Initialize the `## Run Overview` section.

        Configure the `section_data` attribute using `extra_data` if available.
        """
        super().__init__(mdfile, results, extra_data)

        data = self.extra_data or {}

        # Storing everything from extra_data except _report_options which is used in other sections
        self.section_data = {key: value for key, value in data.items() if key not in {"_report_options"}}

    def generate_rows(self) -> Generator[str, None, None]:
        """Generate the rows for the run overview table."""
        for key, value in self.section_data.items():
            label = self.format_snake_case_to_title_case(key)
            row_key = f"**{label}**"

            if isinstance(value, list):
                row_value = "<br>".join([str(item) for item in value]) if value else "None"
            elif isinstance(value, dict):
                items = []
                for k, v in value.items():
                    sub_label = self.format_snake_case_to_title_case(k)
                    sub_val = self.format_value(v)
                    items.append(f"{sub_label}: {sub_val}")
                row_value = "<br>".join(items) if items else "None"
            else:
                row_value = self.format_value(value)

            yield f"| {row_key} | {row_value} |\n"

    def generate_section(self) -> None:
        """Generate the `## Run Overview` section of the markdown report."""
        if not self.section_data:
            return

        self.write_heading(heading_level=2)
        self.write_table(table_heading=self.TABLE_HEADING)


class TestResultsSummary(MDReportBase):
    """Generate the `## Test Results Summary` section of the markdown report."""

    ICON = "📉"

    def generate_section(self) -> None:
        """Generate the `## Test Results Summary` section of the markdown report."""
        self.write_heading(heading_level=2)

        data = self.extra_data or {}
        report_options = data.get("_report_options", {})

        # Only display the note if results are actually expanded, as that is when the discrepancy is visible.
        if report_options.get("expand_results", False):
            note = (
                ">💡 **Note:** This report was generated with **Expanded Results** enabled. "
                "The summary sections below aggregate results at the test level, "
                "so individual checks (atomic results) are not counted in these totals.\n\n"
            )
            self.mdfile.write(note)


class SummaryTotals(MDReportBase):
    """Generate the `### Summary Totals` section of the markdown report."""

    ICON = "🔢"

    _TABLE_COLUMNS: ClassVar[list[str]] = [
        TOTAL_TESTS,
        STATUS_MAP[AntaTestStatus.SUCCESS],
        STATUS_MAP[AntaTestStatus.SKIPPED],
        STATUS_MAP[AntaTestStatus.FAILURE],
        STATUS_MAP[AntaTestStatus.ERROR],
    ]

    TABLE_HEADING: list[str] = MDReportBase.generate_table_heading(columns=_TABLE_COLUMNS)

    def generate_rows(self) -> Generator[str, None, None]:
        """Generate the rows of the summary totals table."""
        yield (
            f"| {self.results.get_total_results()} "
            f"| {self.results.get_total_results({AntaTestStatus.SUCCESS})} "
            f"| {self.results.get_total_results({AntaTestStatus.SKIPPED})} "
            f"| {self.results.get_total_results({AntaTestStatus.FAILURE})} "
            f"| {self.results.get_total_results({AntaTestStatus.ERROR})} |\n"
        )

    def generate_section(self) -> None:
        """Generate the `### Summary Totals` section of the markdown report."""
        self.write_heading(heading_level=3)
        self.write_table(table_heading=self.TABLE_HEADING)


class SummaryTotalsDeviceUnderTest(MDReportBase):
    """Generate the `### Summary Totals Devices Under Tests` section of the markdown report."""

    ICON = "🔌"

    _TABLE_COLUMNS: ClassVar[list[str]] = [
        DEVICE,
        TOTAL_TESTS,
        STATUS_MAP[AntaTestStatus.SUCCESS],
        STATUS_MAP[AntaTestStatus.SKIPPED],
        STATUS_MAP[AntaTestStatus.FAILURE],
        STATUS_MAP[AntaTestStatus.ERROR],
        CATEGORIES_SKIPPED,
        CATEGORIES_FAILED,
    ]

    TABLE_HEADING: list[str] = MDReportBase.generate_table_heading(columns=_TABLE_COLUMNS)

    def generate_rows(self) -> Generator[str, None, None]:
        """Generate the rows of the summary totals device under test table."""
        for device, stat in self.results.device_stats.items():
            total_tests = stat.tests_success_count + stat.tests_skipped_count + stat.tests_failure_count + stat.tests_error_count + stat.tests_unset_count
            categories_skipped = ", ".join(convert_categories(list(stat.categories_skipped), sort=True))
            categories_failed = ", ".join(convert_categories(list(stat.categories_failed), sort=True))
            yield (
                f"| **{device}** | {total_tests} | {stat.tests_success_count} | {stat.tests_skipped_count} | {stat.tests_failure_count} | {stat.tests_error_count} "
                f"| {categories_skipped or '-'} | {categories_failed or '-'} |\n"
            )

    def generate_section(self) -> None:
        """Generate the `### Summary Totals Devices Under Tests` section of the markdown report."""
        self.write_heading(heading_level=3)
        self.write_table(table_heading=self.TABLE_HEADING)


class SummaryTotalsPerCategory(MDReportBase):
    """Generate the `### Summary Totals Per Category` section of the markdown report."""

    ICON = "🗂️"

    _TABLE_COLUMNS: ClassVar[list[str]] = [
        TEST_CATEGORY,
        TOTAL_TESTS,
        STATUS_MAP[AntaTestStatus.SUCCESS],
        STATUS_MAP[AntaTestStatus.SKIPPED],
        STATUS_MAP[AntaTestStatus.FAILURE],
        STATUS_MAP[AntaTestStatus.ERROR],
    ]

    TABLE_HEADING: list[str] = MDReportBase.generate_table_heading(columns=_TABLE_COLUMNS)

    def generate_rows(self) -> Generator[str, None, None]:
        """Generate the rows of the summary totals per category table."""
        for category, stat in self.results.category_stats.items():
            converted_category = convert_single_category_cached(category)
            total_tests = stat.tests_success_count + stat.tests_skipped_count + stat.tests_failure_count + stat.tests_error_count + stat.tests_unset_count
            yield (
                f"| **{converted_category}** | {total_tests} | {stat.tests_success_count} | {stat.tests_skipped_count} | {stat.tests_failure_count} "
                f"| {stat.tests_error_count} |\n"
            )

    def generate_section(self) -> None:
        """Generate the `### Summary Totals Per Category` section of the markdown report."""
        self.write_heading(heading_level=3)
        self.write_table(table_heading=self.TABLE_HEADING)


class TestResults(MDReportBase):
    """Generates the `## Test Results` section of the markdown report."""

    ICON = "🧪"

    _TABLE_COLUMNS: ClassVar[list[str]] = [DEVICE, CATEGORIES, TEST, DESCRIPTION, CUSTOM_FIELD, RESULT, MESSAGES]

    TABLE_HEADING: list[str] = MDReportBase.generate_table_heading(columns=_TABLE_COLUMNS)

    def __init__(self, mdfile: TextIO, results: ResultManager, extra_data: dict[str, Any] | None = None) -> None:
        """Initialize the `## Test Results` section.

        Configure the section behavior using `_report_options` from `extra_data` if available.
        """
        super().__init__(mdfile, results, extra_data)

        data = self.extra_data or {}
        report_options = data.get("_report_options", {})

        # Set configuration flags
        self.render_custom_field = report_options.get("render_custom_field", True)
        self.expand_results = report_options.get("expand_results", False)

        if not self.render_custom_field:
            # Override the class variable to remove the "Custom Field" column
            columns = list(self._TABLE_COLUMNS)
            if CUSTOM_FIELD in columns:
                columns.remove(CUSTOM_FIELD)
            self.TABLE_HEADING = self.generate_table_heading(columns=columns)

    def generate_rows(self) -> Generator[str, None, None]:
        """Generate the rows of the all test results table."""
        for result in self.results.results:
            # Check if we should render this as an expanded atomic result
            is_expanded = self.expand_results and bool(result.atomic_results)

            # Generate parent row
            yield self._format_parent_row(result, is_expanded=is_expanded)

            # Generate atomic rows (if expanded)
            if is_expanded:
                yield from self.generate_atomic_rows(result)

    def generate_atomic_rows(self, result: TestResult) -> Generator[str, None, None]:
        """Generate the rows for atomic results."""
        total_atomic = len(result.atomic_results)

        for idx, atomic in enumerate(result.atomic_results):
            is_last = idx == total_atomic - 1
            tree_char = "└──" if is_last else "├──"

            description = self.safe_markdown(atomic.description) if atomic.description else "-"
            atomic_description_str = f"&nbsp;&nbsp;{tree_char}&nbsp;{description}"

            atomic_messages_str = self.safe_markdown("<br>".join(atomic.messages)) or "-"
            atomic_result_str = self.format_status(atomic.result) or "-"

            if self.render_custom_field:
                yield f"| | | | {atomic_description_str} | | {atomic_result_str} | {atomic_messages_str} |\n"
            else:
                yield f"| | | | {atomic_description_str} | {atomic_result_str} | {atomic_messages_str} |\n"

    def generate_section(self) -> None:
        """Generate the `## Test Results` section of the markdown report."""
        self.write_heading(heading_level=2)
        self.write_table(table_heading=self.TABLE_HEADING, last_table=True)

    def _format_parent_row(self, result: TestResult, *, is_expanded: bool = False) -> str:
        """Format a single parent row string."""
        categories_str = ", ".join(convert_categories(result.categories, sort=True)) or "-"
        result_str = self.format_status(result.result) or "-"

        # Format the messages
        if is_expanded:
            total = len(result.atomic_results)
            failed = len([res for res in result.atomic_results if res.result != AntaTestStatus.SUCCESS])
            messages_str = f"{failed}/{total}&nbsp;checks&nbsp;failed" if failed > 0 else f"All&nbsp;{total}&nbsp;checks&nbsp;passed"
        else:
            messages_str = self.safe_markdown("<br>".join(result.messages)) or "-"

        # Build the row parts
        row_parts = [result.name or "-", categories_str, result.test or "-", result.description or "-"]

        # Conditionally add the custom field
        if self.render_custom_field:
            custom_field_str = self.safe_markdown(result.custom_field) or "-"
            row_parts.append(custom_field_str)

        row_parts.extend([result_str, messages_str])

        return f"| {' | '.join(row_parts)} |\n"


# pylint: disable=too-few-public-methods
class MDReportGenerator:
    """Class responsible for generating a Markdown report based on the provided `ResultManager` object.

    It aggregates different report sections, each represented by a subclass of `MDReportBase`,
    and sequentially generates their content into a markdown file.

    This class provides two methods for generating the report:

    - `generate`: Uses a single result manager instance to generate all sections defined in the `DEFAULT_SECTIONS` class variable list.

    - `generate_sections`: A custom list of sections is provided. Each section uses its own dedicated result manager instance,
    allowing greater flexibility or isolation between section generations.
    """

    DEFAULT_SECTIONS: ClassVar[list[type[MDReportBase]]] = [
        ANTAReport,
        RunOverview,
        TestResultsSummary,
        SummaryTotals,
        SummaryTotalsDeviceUnderTest,
        SummaryTotalsPerCategory,
        TestResults,
    ]

    @classmethod
    def generate(cls, results: ResultManager, md_filename: Path, extra_data: dict[str, Any] | None = None) -> None:
        """Generate the sections of the markdown report defined in DEFAULT_SECTIONS using a single result manager instance for all sections.

        Parameters
        ----------
        results
            The ResultsManager instance containing all test results.
        md_filename
            The path to the markdown file to write the report into.
        extra_data
            Optional extra data dictionary that can be used by the section generators to render additional data.
        """
        try:
            with md_filename.open("w", encoding="utf-8") as mdfile:
                for section in cls.DEFAULT_SECTIONS:
                    section(mdfile, results, extra_data).generate_section()
        except OSError as exc:
            message = f"OSError caught while writing the Markdown file '{md_filename.resolve()}'."
            anta_log_exception(exc, message, logger)
            raise

    @classmethod
    def generate_sections(cls, sections: list[tuple[type[MDReportBase], ResultManager]], md_filename: Path, extra_data: dict[str, Any] | None = None) -> None:
        """Generate the different sections of the markdown report provided in the sections argument with each section using its own result manager instance.

        Parameters
        ----------
        sections
            A list of tuples, where each tuple contains a subclass of `MDReportBase` and an instance of `ResultManager`.
        md_filename
            The path to the markdown file to write the report into.
        extra_data
            Optional extra data dictionary that can be used by the section generators to render additional data.
        """
        try:
            with md_filename.open("w", encoding="utf-8") as md_file:
                for section, rm in sections:
                    section(md_file, rm, extra_data).generate_section()
        except OSError as exc:
            message = f"OSError caught while writing the Markdown file '{md_filename.resolve()}'."
            anta_log_exception(exc, message, logger)
            raise
