# Copyright (c) 2023-2024 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Markdown report generator for ANTA test results."""

from __future__ import annotations

import logging
import re
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, ClassVar

from anta.constants import MD_REPORT_TOC
from anta.logger import anta_log_exception
from anta.result_manager.models import AntaTestStatus
from anta.tools import convert_categories

if TYPE_CHECKING:
    from collections.abc import Generator
    from io import TextIOWrapper
    from pathlib import Path

    from anta.result_manager import ResultManager

logger = logging.getLogger(__name__)


# pylint: disable=too-few-public-methods
class MDReportGenerator:
    """Class responsible for generating a Markdown report based on the provided `ResultManager` object.

    It aggregates different report sections, each represented by a subclass of `MDReportBase`,
    and sequentially generates their content into a markdown file.

    The `generate` class method will loop over all the section subclasses and call their `generate_section` method.
    The final report will be generated in the same order as the `sections` list of the method.
    """

    @classmethod
    def generate(cls, results: ResultManager, md_filename: Path) -> None:
        """Generate and write the various sections of the markdown report.

        Parameters
        ----------
        results
            The ResultsManager instance containing all test results.
        md_filename
            The path to the markdown file to write the report into.
        """
        try:
            with md_filename.open("w", encoding="utf-8") as mdfile:
                sections: list[MDReportBase] = [
                    ANTAReport(mdfile, results),
                    TestResultsSummary(mdfile, results),
                    SummaryTotals(mdfile, results),
                    SummaryTotalsDeviceUnderTest(mdfile, results),
                    SummaryTotalsPerCategory(mdfile, results),
                    TestResults(mdfile, results),
                ]
                for section in sections:
                    section.generate_section()
        except OSError as exc:
            message = f"OSError caught while writing the Markdown file '{md_filename.resolve()}'."
            anta_log_exception(exc, message, logger)
            raise


class MDReportBase(ABC):
    """Base class for all sections subclasses.

    Every subclasses must implement the `generate_section` method that uses the `ResultManager` object
    to generate and write content to the provided markdown file.
    """

    def __init__(self, mdfile: TextIOWrapper, results: ResultManager) -> None:
        """Initialize the MDReportBase with an open markdown file object to write to and a ResultManager instance.

        Parameters
        ----------
        mdfile
            An open file object to write the markdown data into.
        results
            The ResultsManager instance containing all test results.
        """
        self.mdfile = mdfile
        self.results = results

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

        Parameters
        ----------
        heading_level
            The level of the heading (1-6).

        Example
        -------
        `## Test Results Summary`
        """
        # Ensure the heading level is within the valid range of 1 to 6
        heading_level = max(1, min(heading_level, 6))
        heading_name = self.generate_heading_name()
        heading = "#" * heading_level + " " + heading_name
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

        # Replace newlines with spaces to keep content on one line
        text = text.replace("\n", " ")

        # Replace backticks with single quotes
        return text.replace("`", "'")


class ANTAReport(MDReportBase):
    """Generate the `# ANTA Report` section of the markdown report."""

    def generate_section(self) -> None:
        """Generate the `# ANTA Report` section of the markdown report."""
        self.write_heading(heading_level=1)
        toc = MD_REPORT_TOC
        self.mdfile.write(toc + "\n\n")


class TestResultsSummary(MDReportBase):
    """Generate the `## Test Results Summary` section of the markdown report."""

    def generate_section(self) -> None:
        """Generate the `## Test Results Summary` section of the markdown report."""
        self.write_heading(heading_level=2)


class SummaryTotals(MDReportBase):
    """Generate the `### Summary Totals` section of the markdown report."""

    TABLE_HEADING: ClassVar[list[str]] = [
        "| Total Tests | Total Tests Success | Total Tests Skipped | Total Tests Failure | Total Tests Error |",
        "| ----------- | ------------------- | ------------------- | ------------------- | ------------------|",
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

    TABLE_HEADING: ClassVar[list[str]] = [
        "| Device Under Test | Total Tests | Tests Success | Tests Skipped | Tests Failure | Tests Error | Categories Skipped | Categories Failed |",
        "| ------------------| ----------- | ------------- | ------------- | ------------- | ----------- | -------------------| ------------------|",
    ]

    def generate_rows(self) -> Generator[str, None, None]:
        """Generate the rows of the summary totals device under test table."""
        for device, stat in self.results.device_stats.items():
            total_tests = stat.tests_success_count + stat.tests_skipped_count + stat.tests_failure_count + stat.tests_error_count
            categories_skipped = ", ".join(sorted(convert_categories(list(stat.categories_skipped))))
            categories_failed = ", ".join(sorted(convert_categories(list(stat.categories_failed))))
            yield (
                f"| {device} | {total_tests} | {stat.tests_success_count} | {stat.tests_skipped_count} | {stat.tests_failure_count} | {stat.tests_error_count} "
                f"| {categories_skipped or '-'} | {categories_failed or '-'} |\n"
            )

    def generate_section(self) -> None:
        """Generate the `### Summary Totals Devices Under Tests` section of the markdown report."""
        self.write_heading(heading_level=3)
        self.write_table(table_heading=self.TABLE_HEADING)


class SummaryTotalsPerCategory(MDReportBase):
    """Generate the `### Summary Totals Per Category` section of the markdown report."""

    TABLE_HEADING: ClassVar[list[str]] = [
        "| Test Category | Total Tests | Tests Success | Tests Skipped | Tests Failure | Tests Error |",
        "| ------------- | ----------- | ------------- | ------------- | ------------- | ----------- |",
    ]

    def generate_rows(self) -> Generator[str, None, None]:
        """Generate the rows of the summary totals per category table."""
        for category, stat in self.results.sorted_category_stats.items():
            total_tests = stat.tests_success_count + stat.tests_skipped_count + stat.tests_failure_count + stat.tests_error_count
            yield (
                f"| {category} | {total_tests} | {stat.tests_success_count} | {stat.tests_skipped_count} | {stat.tests_failure_count} "
                f"| {stat.tests_error_count} |\n"
            )

    def generate_section(self) -> None:
        """Generate the `### Summary Totals Per Category` section of the markdown report."""
        self.write_heading(heading_level=3)
        self.write_table(table_heading=self.TABLE_HEADING)


class TestResults(MDReportBase):
    """Generates the `## Test Results` section of the markdown report."""

    TABLE_HEADING: ClassVar[list[str]] = [
        "| Device Under Test | Categories | Test | Description | Custom Field | Result | Messages |",
        "| ----------------- | ---------- | ---- | ----------- | ------------ | ------ | -------- |",
    ]

    def generate_rows(self) -> Generator[str, None, None]:
        """Generate the rows of the all test results table."""
        for result in self.results.get_results(sort_by=["name", "test"]):
            messages = self.safe_markdown(", ".join(result.messages))
            categories = ", ".join(convert_categories(result.categories))
            yield (
                f"| {result.name or '-'} | {categories or '-'} | {result.test or '-'} "
                f"| {result.description or '-'} | {self.safe_markdown(result.custom_field) or '-'} | {result.result or '-'} | {messages or '-'} |\n"
            )

    def generate_section(self) -> None:
        """Generate the `## Test Results` section of the markdown report."""
        self.write_heading(heading_level=2)
        self.write_table(table_heading=self.TABLE_HEADING, last_table=True)
