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
from anta.tools import convert_categories

if TYPE_CHECKING:
    from collections.abc import Generator
    from pathlib import Path

    from anta.result_manager import ResultManager


logger = logging.getLogger(__name__)


class MDReportBase(ABC):
    """Base class for all sections subclasses.

    Every subclasses must implement the `generate_section` method that uses the `ResultManager` object
    to generate and write content to the provided markdown file.
    """

    ICON: ClassVar[str] = ""
    """Optional icon to prepend to the section header."""

    STATUS_MAP: ClassVar[dict[AntaTestStatus, str]] = {
        AntaTestStatus.SUCCESS: "✅&nbsp;SUCCESS",
        AntaTestStatus.FAILURE: "❌&nbsp;FAILURE",
        AntaTestStatus.ERROR: "❗&nbsp;ERROR",
        AntaTestStatus.SKIPPED: "⏭️&nbsp;SKIPPED",
        AntaTestStatus.UNSET: "UNSET",
    }
    """Mapping of `AntaTestStatus` to their string representation with icons."""

    def __init__(self, mdfile: TextIO, results: ResultManager, extra_data: dict[str, Any] | None = None, *, expand_results: bool = False) -> None:
        """Initialize the MDReportBase with an open markdown file object to write to and a ResultManager instance.

        Parameters
        ----------
        mdfile
            An open file object to write the markdown data into.
        results
            The ResultsManager instance containing all test results.
        extra_data
            Optional extra data dictionary. Can be used by subclasses to render additional data.
        expand_results
            Expand atomic results for supported tests.
        """
        self.mdfile = mdfile
        self.results = results
        self.extra_data = extra_data
        self.expand_results = expand_results

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
        return self.STATUS_MAP.get(status, status.upper())


class ANTAReport(MDReportBase):
    """Generate the `# ANTA Report` section of the markdown report."""

    ICON = "📊"

    def generate_section(self) -> None:
        """Generate the `# ANTA Report` section of the markdown report."""
        self.write_heading(heading_level=1)
        toc = MD_REPORT_TOC_WITH_RUN_OVERVIEW if self.extra_data else MD_REPORT_TOC
        self.mdfile.write(toc + "\n\n")


class RunOverview(MDReportBase):
    """Generate the `## Run Overview` section of the markdown report.

    The `extra_data` dictionary containing the desired run information
    must be provided to the initializer to generate this section.
    """

    ICON = "📋"

    TABLE_HEADING: ClassVar[list[str]] = [
        "| ⚙️ Run Metric | 📝 Details |",
        "| :--- | :--- |",
    ]

    def generate_rows(self) -> Generator[str, None, None]:
        """Generate the rows for the run overview table."""
        for key, value in (self.extra_data or {}).items():
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
        if not self.extra_data:
            return

        self.write_heading(heading_level=2)
        self.write_table(table_heading=self.TABLE_HEADING)


class TestResultsSummary(MDReportBase):
    """Generate the `## Test Results Summary` section of the markdown report."""

    ICON = "📉"

    def generate_section(self) -> None:
        """Generate the `## Test Results Summary` section of the markdown report."""
        self.write_heading(heading_level=2)


class SummaryTotals(MDReportBase):
    """Generate the `### Summary Totals` section of the markdown report."""

    ICON = "🔢"

    TABLE_HEADING: ClassVar[list[str]] = [
        "| Total Tests | ✅&nbsp;Success | ⏭️&nbsp;Skipped | ❌&nbsp;Failure | ❗&nbsp;Error |",
        "| :--- | :--- | :--- | :--- | :--- |",
    ]

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

    TABLE_HEADING: ClassVar[list[str]] = [
        "| Device&nbsp;Under&nbsp;Test | Total Tests ",
        "| ✅&nbsp;Success | ⏭️&nbsp;Skipped | ❌&nbsp;Failure | ❗&nbsp;Error | Categories Skipped | Categories Failed |",
        "| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |",
    ]

    def generate_rows(self) -> Generator[str, None, None]:
        """Generate the rows of the summary totals device under test table."""
        for device, stat in self.results.device_stats.items():
            total_tests = stat.tests_success_count + stat.tests_skipped_count + stat.tests_failure_count + stat.tests_error_count + stat.tests_unset_count
            categories_skipped = ", ".join(sorted(convert_categories(list(stat.categories_skipped))))
            categories_failed = ", ".join(sorted(convert_categories(list(stat.categories_failed))))
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

    TABLE_HEADING: ClassVar[list[str]] = [
        "| Test Category | Total Tests | ✅&nbsp;Success | ⏭️&nbsp;Skipped | ❌&nbsp;Failure | ❗&nbsp;Error |",
        "| :--- | :--- | :--- | :--- | :--- | :--- |",
    ]

    def generate_rows(self) -> Generator[str, None, None]:
        """Generate the rows of the summary totals per category table."""
        for category, stat in self.results.category_stats.items():
            converted_category = convert_categories([category])[0]
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
    """Generates the `## Test Results` section of the markdown report.

    Honors the `expand_results` attribute provided to the initializer to generate
    atomic results for tests that support them.
    """

    ICON = "🧪"

    TABLE_HEADING: ClassVar[list[str]] = [
        "| Device&nbsp;Under&nbsp;Test | Categories | Test | Description | Custom Field | Result | Messages |",
        "| :--- | :--- | :--- | :--- | :--- | :--- | :--- |",
    ]

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
        """Generate the indented rows for atomic results."""
        total_atomic = len(result.atomic_results)

        for idx, atomic in enumerate(result.atomic_results):
            is_last = idx == total_atomic - 1
            tree_char = "└──" if is_last else "├──"

            description = self.safe_markdown(atomic.description) if atomic.description else "-"
            atomic_description_str = f"&nbsp;&nbsp;{tree_char}&nbsp;{description}"

            atomic_messages_str = self.safe_markdown("<br>".join(atomic.messages)) or "-"
            atomic_result_str = self.format_status(atomic.result)

            yield f"| | | | {atomic_description_str} | | {atomic_result_str} | {atomic_messages_str} |\n"

    def generate_section(self) -> None:
        """Generate the `## Test Results` section of the markdown report."""
        self.write_heading(heading_level=2)
        self.write_table(table_heading=self.TABLE_HEADING, last_table=True)

    def _format_parent_row(self, result: TestResult, *, is_expanded: bool = False) -> str:
        """Format a single parent row string."""
        categories_str = ", ".join(sorted(convert_categories(result.categories))) or "-"
        custom_field_str = self.safe_markdown(result.custom_field) or "-"
        result_str = self.format_status(result.result) or "-"

        # Format the messages
        if is_expanded:
            total = len(result.atomic_results)
            failed = len([res for res in result.atomic_results if res.result != AntaTestStatus.SUCCESS])
            messages_str = f"{failed}/{total} checks failed" if failed > 0 else f"All {total} checks passed"
        else:
            messages_str = self.safe_markdown("<br>".join(result.messages)) or "-"

        return (
            f"| {result.name or '-'} | {categories_str} | {result.test or '-'} "
            f"| {result.description or '-'} | {custom_field_str} | {result_str} | {messages_str} |\n"
        )


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
    def generate(cls, results: ResultManager, md_filename: Path, extra_data: dict[str, Any] | None = None, *, expand_results: bool = False) -> None:
        """Generate the sections of the markdown report defined in DEFAULT_SECTIONS using a single result manager instance for all sections.

        Parameters
        ----------
        results
            The ResultsManager instance containing all test results.
        md_filename
            The path to the markdown file to write the report into.
        extra_data
            Optional extra data dictionary that can be used by the section generators to render additional data.
        expand_results
            Expand atomic results for supported tests.
        """
        try:
            with md_filename.open("w", encoding="utf-8") as mdfile:
                for section in cls.DEFAULT_SECTIONS:
                    section(mdfile, results, extra_data, expand_results=expand_results).generate_section()
        except OSError as exc:
            message = f"OSError caught while writing the Markdown file '{md_filename.resolve()}'."
            anta_log_exception(exc, message, logger)
            raise

    @classmethod
    def generate_sections(
        cls,
        sections: list[tuple[type[MDReportBase], ResultManager]],
        md_filename: Path,
        extra_data: dict[str, Any] | None = None,
        *,
        expand_results: bool = False,
    ) -> None:
        """Generate the different sections of the markdown report provided in the sections argument with each section using its own result manager instance.

        Parameters
        ----------
        sections
            A sequence of tuples, where each tuple contains a subclass of `MDReportBase` and an instance of `ResultManager`.
        md_filename
            The path to the markdown file to write the report into.
        extra_data
            Optional extra data dictionary that can be used by the section generators to render additional data.
        expand_results
            Expand atomic results for supported tests.
        """
        try:
            with md_filename.open("w", encoding="utf-8") as md_file:
                for section, rm in sections:
                    section(md_file, rm, extra_data, expand_results=expand_results).generate_section()
        except OSError as exc:
            message = f"OSError caught while writing the Markdown file '{md_filename.resolve()}'."
            anta_log_exception(exc, message, logger)
            raise
