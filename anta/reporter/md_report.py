# Copyright (c) 2023-2024 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Markdown report generator for ANTA test results."""

from __future__ import annotations

import re
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, ClassVar

if TYPE_CHECKING:
    from collections.abc import Generator
    from io import TextIOWrapper

    from anta.result_manager import ResultManager


# pylint: disable=too-few-public-methods
class MDReportFactory:
    """Factory class responsible for generating a Markdown report based on the provided `ResultManager` object.

    It aggregates different report sections, each represented by a subclass of `MDReportBase`,
    and sequentially generates their content into a markdown file.

    The `generate_report` method will loop over all the section subclasses and call their `generate_section` method.
    The final report will be generated in the same order as the `sections` list of the method.

    The factory method also accepts an optional `only_failed_tests` flag to generate a report with only failed tests.

    By default, the report will include all test results.
    """

    @classmethod
    def generate_report(cls, mdfile: TextIOWrapper, manager: ResultManager, *, only_failed_tests: bool = False) -> None:
        """Generate and write the various sections of the markdown report."""
        sections: list[MDReportBase] = [
            ANTAReport(mdfile, manager),
            TestResultsSummary(mdfile, manager),
            SummaryTotals(mdfile, manager),
            SummaryTotalsDeviceUnderTest(mdfile, manager),
            SummaryTotalsPerCategory(mdfile, manager),
            FailedTestResultsSummary(mdfile, manager),
            AllTestResults(mdfile, manager),
        ]

        if only_failed_tests:
            sections.pop()

        for section in sections:
            section.generate_section()


class MDReportBase(ABC):
    """Base class for all sections subclasses.

    Every subclasses must implement the `generate_section` method that uses the `ResultManager` object
    to generate and write content to the provided markdown file.
    """

    def __init__(self, mdfile: TextIOWrapper, manager: ResultManager) -> None:
        """Initialize the MDReportBase with an open markdown file object to write to and a ResultManager instance.

        Args:
        ----
            mdfile (TextIOWrapper): An open file object to write the markdown data into.
            results (ResultManager): The ResultsManager instance containing all test results.
        """
        self.mdfile = mdfile
        self.manager = manager

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
            str: Formatted header name.

        Example:
        -------
            - `ANTAReport` will become ANTA Report.
            - `TestResultsSummary` will become Test Results Summary.
        """
        class_name = self.__class__.__name__

        # Split the class name into words, keeping acronyms together
        words = re.findall(r"([A-Z]+(?=[A-Z][a-z]|\d|\W|$|\s)|[A-Z]?[a-z]+|\d+)", class_name)

        # Capitalize each word, but keep acronyms in all caps
        formatted_words = [word if word.isupper() else word.capitalize() for word in words]

        return " ".join(formatted_words)

    def write_table(self, table_heading: list[str], *, last_table: bool = False) -> None:
        """Write a markdown table with a table heading and multiple rows to the markdown file.

        Args:
        ----
            table_heading (list[str]): List of strings to join for the table heading.
            last_table (bool): Flag to determine if it's the last table of the markdown file to avoid unnecessary new line.
                                Defaults to False.
        """
        self.mdfile.write("\n".join(table_heading) + "\n")
        for row in self.generate_rows():
            self.mdfile.write(row)
        if not last_table:
            self.mdfile.write("\n")

    def write_heading(self, heading_level: int) -> None:
        """Write a markdown heading to the markdown file.

        The heading name used is the class name.

        Args:
        ----
            heading_level (int): The level of the heading (1-6).

        Example:
        -------
            ## Test Results Summary
        """
        # Ensure the heading level is within the valid range of 1 to 6
        heading_level = max(1, min(heading_level, 6))
        heading_name = self.generate_heading_name()
        heading = "#" * heading_level + " " + heading_name
        self.mdfile.write(f"{heading}\n\n")

    def safe_markdown(self, text: str | None) -> str:
        """Escape markdown characters in the text to prevent markdown rendering issues."""
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
        self.mdfile.write(
            """**Table of Contents:**

- [ANTA Report](#anta-report)
  - [Test Results Summary](#test-results-summary)
  - [Failed Test Results Summary](#failed-test-results-summary)
  - [All Test Results](#all-test-results)

""",
        )


class TestResultsSummary(MDReportBase):
    """Generate the `## Test Results Summary` section of the markdown report."""

    def generate_section(self) -> None:
        """Generate the `## Test Results Summary` section of the markdown report."""
        self.write_heading(heading_level=2)


class SummaryTotals(MDReportBase):
    """Generate the `### Summary Totals` section of the markdown report."""

    TABLE_HEADING: ClassVar[list[str]] = [
        "| Total Tests | Total Tests Passed | Total Tests Failed | Total Tests Skipped |",
        "| ----------- | ------------------ | ------------------ | ------------------- |",
    ]

    def generate_rows(self) -> Generator[str, None, None]:
        """Generate the rows of the summary totals table."""
        yield (
            f"| {self.manager.get_total_results()} "
            f"| {self.manager.get_total_results('success')} "
            f"| {self.manager.get_total_results({'failure', 'error', 'unset'})} "
            f"| {self.manager.get_total_results('skipped')} |\n"
        )

    def generate_section(self) -> None:
        """Generate the `### Summary Totals` section of the markdown report."""
        self.write_heading(heading_level=3)
        self.write_table(table_heading=self.TABLE_HEADING)


class SummaryTotalsDeviceUnderTest(MDReportBase):
    """Generate the `### Summary Totals Devices Under Tests` section of the markdown report."""

    TABLE_HEADING: ClassVar[list[str]] = [
        "| Device Under Test | Total Tests | Tests Passed | Tests Failed | Tests Skipped | Categories Failed | Categories Skipped |",
        "| ------------------| ----------- | ------------ | ------------ | ------------- | ----------------- | ------------------ |",
    ]

    def generate_rows(self) -> Generator[str, None, None]:
        """Generate the rows of the summary totals dut table."""
        for dut, stat in self.manager.dut_stats.items():
            total_tests = stat.tests_passed + stat.tests_failed + stat.tests_skipped
            categories_failed = ", ".join(sorted(stat.categories_failed))
            categories_skipped = ", ".join(sorted(stat.categories_skipped))
            yield (
                f"| {dut} | {total_tests} | {stat.tests_passed} | {stat.tests_failed} | {stat.tests_skipped} | {categories_failed or '-'} "
                f"| {categories_skipped or '-'} |\n"
            )

    def generate_section(self) -> None:
        """Generate the `### Summary Totals Devices Under Tests` section of the markdown report."""
        self.write_heading(heading_level=3)
        self.write_table(table_heading=self.TABLE_HEADING)


class SummaryTotalsPerCategory(MDReportBase):
    """Generate the `### Summary Totals Per Category` section of the markdown report."""

    TABLE_HEADING: ClassVar[list[str]] = [
        "| Test Category | Total Tests | Tests Passed | Tests Failed | Tests Skipped |",
        "| ------------- | ----------- | ------------ | ------------ | ------------- |",
    ]

    def generate_rows(self) -> Generator[str, None, None]:
        """Generate the rows of the summary totals per category table."""
        for category, stat in self.manager.sorted_category_stats.items():
            total_tests = stat.tests_passed + stat.tests_failed + stat.tests_skipped
            yield f"| {category} | {total_tests} | {stat.tests_passed} | {stat.tests_failed} | {stat.tests_skipped} |\n"

    def generate_section(self) -> None:
        """Generate the `### Summary Totals Per Category` section of the markdown report."""
        self.write_heading(heading_level=3)
        self.write_table(table_heading=self.TABLE_HEADING)


class FailedTestResultsSummary(MDReportBase):
    """Generate the `## Failed Test Results Summary` section of the markdown report."""

    TABLE_HEADING: ClassVar[list[str]] = [
        "| ID | Device Under Test | Categories | Test | Description | Custom Field | Result | Messages |",
        "| -- | ----------------- | ---------- | ---- | ----------- | ------------ | -------| -------- |",
    ]

    def generate_rows(self) -> Generator[str, None, None]:
        """Generate the rows of the failed test results table."""
        for result in self.manager.get_results({"failure", "error", "unset"}):
            messages = self.safe_markdown(", ".join(result.messages))
            categories = ", ".join(result.categories)
            yield (
                f"| {result.id or '-'} | {result.name or '-'} | {categories or '-'} | {result.test or '-'} "
                f"| {result.description or '-'} | {self.safe_markdown(result.custom_field) or '-'} | {result.result or '-'} | {messages or '-'} |\n"
            )

    def generate_section(self) -> None:
        """Generate the `## Failed Test Results Summary` section of the markdown report."""
        self.write_heading(heading_level=2)
        self.write_table(table_heading=self.TABLE_HEADING)


class AllTestResults(MDReportBase):
    """Generates the `## All Test Results` section of the markdown report.

    This section is generated only if the report includes all results.
    """

    TABLE_HEADING: ClassVar[list[str]] = [
        "| ID | Device Under Test | Categories | Test | Description | Custom Field | Result | Messages |",
        "| -- | ----------------- | ---------- | ---- | ----------- | ------------ | -------| -------- |",
    ]

    def generate_rows(self) -> Generator[str, None, None]:
        """Generate the rows of the all test results table."""
        for result in self.manager.results:
            messages = self.safe_markdown(", ".join(result.messages))
            categories = ", ".join(result.categories)
            yield (
                f"| {result.id or '-'} | {result.name or '-'} | {categories or '-'} | {result.test or '-'} "
                f"| {result.description or '-'} | {self.safe_markdown(result.custom_field) or '-'} | {result.result or '-'} | {messages or '-'} |\n"
            )

    def generate_section(self) -> None:
        """Generate the `## All Test Results` section of the markdown report.

        This section is generated only if the report includes all results.
        """
        self.write_heading(heading_level=2)
        self.write_table(table_heading=self.TABLE_HEADING, last_table=True)
