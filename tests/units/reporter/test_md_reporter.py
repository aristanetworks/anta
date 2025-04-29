# Copyright (c) 2023-2025 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Test anta.reporter.md_reporter.py."""

from __future__ import annotations

from io import StringIO
from pathlib import Path
from typing import TYPE_CHECKING, ClassVar

import pytest

from anta.reporter.md_reporter import MDReportBase, MDReportGenerator
from anta.result_manager import ResultManager
from anta.result_manager.models import AntaTestStatus
from anta.tools import convert_categories

if TYPE_CHECKING:
    from collections.abc import Generator

DATA_DIR: Path = Path(__file__).parent.parent.parent.resolve() / "data"


class FailedTestResultsSummary(MDReportBase):
    """Test-only class used for simulating behavior in unit tests.

    Generates the `## Failed Test Results Summary` section of the markdown report.
    """

    TABLE_HEADING: ClassVar[list[str]] = [
        "| Device Under Test | Categories | Test | Description | Custom Field | Result | Messages |",
        "| ----------------- | ---------- | ---- | ----------- | ------------ | ------ | -------- |",
    ]

    def generate_rows(self) -> Generator[str, None, None]:
        """Generate the rows of the all test results table."""
        for result in self.results.results:
            messages = self.safe_markdown_messages(result.messages[0]) if len(result.messages) == 1 else self.safe_markdown_messages("<br>".join(result.messages))
            categories = ", ".join(sorted(convert_categories(result.categories)))
            yield (
                f"| {result.name or '-'} | {categories or '-'} | {result.test or '-'} "
                f"| {result.description or '-'} | {self.safe_markdown(result.custom_field) or '-'} | {result.result or '-'} | {messages or '-'} |\n"
            )

    def generate_section(self) -> None:
        """Generate the `## Failed Test Results Summary` section of the markdown report."""
        self.write_heading(heading_level=2)
        self.write_table(table_heading=self.TABLE_HEADING)


def test_md_report_generate(tmp_path: Path, result_manager: ResultManager) -> None:
    """Test the MDReportGenerator class."""
    md_filename = tmp_path / "test.md"
    expected_report = "test_md_report.md"

    # Generate the Markdown report
    MDReportGenerator.generate(result_manager.sort(sort_by=["name", "categories", "test"]), md_filename)
    assert md_filename.exists()

    # Load the existing Markdown report to compare with the generated one
    with (DATA_DIR / expected_report).open("r", encoding="utf-8") as f:
        expected_content = f.read()

    # Check the content of the Markdown file
    content = md_filename.read_text(encoding="utf-8")

    assert content == expected_content


def test_md_report_generate_sections(tmp_path: Path, result_manager: ResultManager) -> None:
    """Test the MDReportGenerator class."""
    md_filename = tmp_path / "test.md"
    expected_report = "test_md_report_custom_sections.md"
    rm = result_manager.sort(sort_by=["name", "categories", "test"])

    sections = [(section, rm) for section in MDReportGenerator.DEFAULT_SECTIONS]
    # Adding custom section
    failed_section = (FailedTestResultsSummary, rm.filter({AntaTestStatus.SUCCESS, AntaTestStatus.ERROR, AntaTestStatus.SKIPPED, AntaTestStatus.UNSET}))
    sections.insert(-1, failed_section)

    # Generate the Markdown report
    MDReportGenerator.generate_sections(sections, md_filename)
    assert md_filename.exists()

    # Load the existing Markdown report to compare with the generated one
    with (DATA_DIR / expected_report).open("r", encoding="utf-8") as f:
        expected_content = f.read()

    # Check the content of the Markdown file
    content = md_filename.read_text(encoding="utf-8")

    assert content == expected_content


def test_md_report_base() -> None:
    """Test the MDReportBase class."""

    class FakeMDReportBase(MDReportBase):
        """Fake MDReportBase class."""

        def generate_section(self) -> None:
            pass

    results = ResultManager()

    with StringIO() as mock_file:
        report = FakeMDReportBase(mock_file, results)
        assert report.generate_heading_name() == "Fake MD Report Base"

        with pytest.raises(NotImplementedError, match="Subclasses should implement this method"):
            report.generate_rows()


def test_md_report_error(result_manager: ResultManager) -> None:
    """Test the MDReportGenerator class to OSError to be raised."""
    md_filename = Path("non_existent_directory/non_existent_file.md")
    rm = result_manager.sort(sort_by=["name", "categories", "test"])

    sections = [(section, rm) for section in MDReportGenerator.DEFAULT_SECTIONS]

    with pytest.raises(OSError, match="No such file or directory"):
        MDReportGenerator.generate_sections(sections, md_filename)

    with pytest.raises(OSError, match="No such file or directory"):
        MDReportGenerator.generate(result_manager, md_filename)
