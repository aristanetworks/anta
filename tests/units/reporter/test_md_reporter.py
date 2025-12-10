# Copyright (c) 2023-2025 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Test anta.reporter.md_reporter.py."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from io import StringIO
from pathlib import Path
from typing import TYPE_CHECKING, ClassVar

import pytest

from anta.reporter.md_reporter import MDReportBase, MDReportGenerator, TestResults
from anta.result_manager import ResultManager
from anta.result_manager.models import AntaTestStatus
from anta.tools import convert_categories

if TYPE_CHECKING:
    from collections.abc import Generator

    from tests.units.result_manager.conftest import ResultManagerFactoryProtocol

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
            messages = self.safe_markdown(result.messages[0]) if len(result.messages) == 1 else self.safe_markdown("<br>".join(result.messages))
            categories = ", ".join(sorted(convert_categories(result.categories)))
            yield (
                f"| {result.name or '-'} | {categories or '-'} | {result.test or '-'} "
                f"| {result.description or '-'} | {self.safe_markdown(result.custom_field) or '-'} | {result.result or '-'} | {messages or '-'} |\n"
            )

    def generate_section(self) -> None:
        """Generate the `## Failed Test Results Summary` section of the markdown report."""
        self.write_heading(heading_level=2)
        self.write_table(table_heading=self.TABLE_HEADING)


def test_md_report_generator_generate(tmp_path: Path, result_manager: ResultManager) -> None:
    """Test the MDReportGenerator.generate() class method."""
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


def test_md_report_generator_generate_with_extra_data(tmp_path: Path, result_manager: ResultManager) -> None:
    """Test the MDReportGenerator.generate() class method with extra_data."""
    md_filename = tmp_path / "test.md"
    expected_report = "test_md_report_extra_data.md"

    # Build the extra_data
    start_time = datetime(2025, 5, 20, 8, 30, 0, tzinfo=timezone.utc)
    end_time = datetime(2025, 5, 20, 8, 35, 30, 500000, tzinfo=timezone.utc)
    extra_data = {
        "anta_version": "v1.4.0",
        "test_execution_start_time": start_time,
        "test_execution_end_time": end_time,
        "total_duration": end_time - start_time,
        "total_devices_in_inventory": 4,
        "devices_unreachable_at_setup": ["s1-spine2"],
        "devices_filtered_at_setup": ["s1-leaf1", "s1-leaf2"],
        "filters_applied": {"tags": ["spine"]},
        "custom_metric": "Created by Arista",
    }

    # This special key must be exclude from the Run Overview section
    extra_data["_report_options"] = {"expand_results": True}

    # Generate the Markdown report with extra_data (providing extra_data will generate the Run Overview section)
    MDReportGenerator.generate(result_manager.sort(sort_by=["name", "categories", "test"]), md_filename, extra_data)
    assert md_filename.exists()

    # Load the existing Markdown report to compare with the generated one
    with (DATA_DIR / expected_report).open("r", encoding="utf-8") as f:
        expected_content = f.read()

    # Check the content of the Markdown file
    content = md_filename.read_text(encoding="utf-8")

    assert content == expected_content


def test_md_report_generator_generate_sections(tmp_path: Path, result_manager: ResultManager) -> None:
    """Test the MDReportGenerator.generate_sections() class method."""
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


def test_md_report_generator_generate_expand_results(tmp_path: Path, result_manager_factory: ResultManagerFactoryProtocol) -> None:
    """Test the MDReportGenerator.generate() class method with expand_results."""
    md_filename = tmp_path / "test.md"
    expected_report = "test_md_report_expand_results.md"

    result_manager = result_manager_factory(size=5, nb_atomic_results=3, distinct_tests=True, distinct_devices=True)

    # Generate the Markdown report with expand_results (this will generate atomic results)
    MDReportGenerator.generate(result_manager.sort(sort_by=["name", "categories", "test"]), md_filename, extra_data={"_report_options": {"expand_results": True}})
    assert md_filename.exists()

    # Load the existing Markdown report to compare with the generated one
    with (DATA_DIR / expected_report).open("r", encoding="utf-8") as f:
        expected_content = f.read()

    # Check the content of the Markdown file
    content = md_filename.read_text(encoding="utf-8")

    assert content == expected_content


def test_md_report_generator_generate_no_custom_field(tmp_path: Path, result_manager_factory: ResultManagerFactoryProtocol) -> None:
    """Test the MDReportGenerator.generate() class method with no custom field."""
    md_filename = tmp_path / "test.md"
    expected_report = "test_md_report_no_custom_field.md"

    result_manager = result_manager_factory(size=5, nb_atomic_results=3, distinct_tests=True, distinct_devices=True)

    # Generate the Markdown report with no custom field
    MDReportGenerator.generate(
        result_manager.sort(sort_by=["name", "categories", "test"]), md_filename, extra_data={"_report_options": {"render_custom_field": False}}
    )
    assert md_filename.exists()

    # Load the existing Markdown report to compare with the generated one
    with (DATA_DIR / expected_report).open("r", encoding="utf-8") as f:
        expected_content = f.read()

    # Check the content of the Markdown file
    content = md_filename.read_text(encoding="utf-8")

    assert content == expected_content


def test_md_report_generator_generate_sections_expand_results(tmp_path: Path, result_manager_factory: ResultManagerFactoryProtocol) -> None:
    """Test the MDReportGenerator.generate_sections() class method with expand_results."""
    md_filename = tmp_path / "test.md"
    expected_report = "test_md_report_custom_sections_expand_results.md"

    result_manager = result_manager_factory(size=5, nb_atomic_results=3, distinct_tests=True, distinct_devices=True)

    sections: list[tuple[type[MDReportBase], ResultManager]] = [(TestResults, result_manager.sort(sort_by=["name", "categories", "test"]))]

    # Generate the Markdown report with the "Test Results" section only with expand_results (this will generate atomic results)
    MDReportGenerator.generate_sections(sections, md_filename, extra_data={"_report_options": {"expand_results": True}})
    assert md_filename.exists()

    # Load the existing Markdown report to compare with the generated one
    with (DATA_DIR / expected_report).open("r", encoding="utf-8") as f:
        expected_content = f.read()

    # Check the content of the Markdown file
    content = md_filename.read_text(encoding="utf-8")

    assert content == expected_content


def test_md_report_generator_generate_sections_no_custom_field(tmp_path: Path, result_manager_factory: ResultManagerFactoryProtocol) -> None:
    """Test the MDReportGenerator.generate_sections() class method with no custom field."""
    md_filename = tmp_path / "test.md"
    expected_report = "test_md_report_custom_sections_no_custom_field.md"

    result_manager = result_manager_factory(size=5, nb_atomic_results=3, distinct_tests=True, distinct_devices=True)

    sections: list[tuple[type[MDReportBase], ResultManager]] = [(TestResults, result_manager.sort(sort_by=["name", "categories", "test"]))]

    # Generate the Markdown report with the "Test Results" section only with no custom field
    MDReportGenerator.generate_sections(sections, md_filename, extra_data={"_report_options": {"render_custom_field": False}})
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


@pytest.mark.parametrize(
    ("value", "expected_output"),
    [
        pytest.param("hello_world", "Hello World", id="snake_to_title_case"),
        pytest.param("anta_version", "ANTA Version", id="anta_acronym_handling"),
        pytest.param("bgp_protocol", "BGP Protocol", id="bgp_acronym_handling"),
        pytest.param("", "", id="empty_string"),
        pytest.param("name", "Name", id="single_word"),
        pytest.param("this_is_a_test", "This Is A Test", id="multiple_underscores"),
        pytest.param("_leading_underscore", " Leading Underscore", id="leading_underscore"),
        pytest.param("mixed_CASE_string", "Mixed Case String", id="mixed_case_parts"),
    ],
)
def test_md_report_base_format_snake_case_to_title_case(value: str, expected_output: str) -> None:
    """Test the MDReportBase.format_snake_case_to_title_casey() method."""

    class FakeMDReportBase(MDReportBase):
        """Fake MDReportBase class."""

        def generate_section(self) -> None:
            pass

    results = ResultManager()

    with StringIO() as mock_file:
        report = FakeMDReportBase(mock_file, results)
        assert report.format_snake_case_to_title_case(value) == expected_output


@pytest.mark.parametrize(
    ("value", "expected_output"),
    [
        # Datetime tests
        pytest.param(datetime(2023, 1, 15, 10, 30, 45, 123456, tzinfo=timezone.utc), "2023-01-15 10:30:45.123+00:00", id="datetime_with_milliseconds"),
        pytest.param(datetime(2024, 7, 20, 14, 0, 0, tzinfo=timezone.utc), "2024-07-20 14:00:00.000+00:00", id="datetime_without_milliseconds"),
        # Timedelta tests
        pytest.param(timedelta(hours=1, minutes=5, seconds=30, milliseconds=500), "1 hour, 5 minutes, 30 seconds", id="timedelta_full"),
        pytest.param(timedelta(days=2), "48 hours", id="timedelta_only_days"),
        pytest.param(timedelta(hours=2), "2 hours", id="timedelta_only_hours"),
        pytest.param(timedelta(minutes=1), "1 minute", id="timedelta_only_minute"),
        pytest.param(timedelta(seconds=45), "45 seconds", id="timedelta_only_seconds"),
        pytest.param(timedelta(milliseconds=100), "100 milliseconds", id="timedelta_only_milliseconds"),
        pytest.param(timedelta(microseconds=100000), "100 milliseconds", id="timedelta_only_microseconds"),
        pytest.param(timedelta(microseconds=999), "0 seconds", id="timedelta_sub_milliseconds"),
        pytest.param(timedelta(0), "0 seconds", id="timedelta_zero"),
        pytest.param(timedelta(seconds=-10), "Invalid duration", id="timedelta_negative"),
        pytest.param(timedelta(days=1, hours=3, minutes=20), "27 hours, 20 minutes", id="timedelta_days_to_hours"),
        # List tests
        pytest.param(["apple", "banana", "cherry"], "apple, banana, cherry", id="list_of_strings"),
        pytest.param([1, 2, 3], "1, 2, 3", id="list_of_integers"),
        pytest.param(["text", 123, True], "text, 123, True", id="list_of_mixed_types"),
        pytest.param([], "", id="empty_list"),
        # Other types (default str conversion)
        pytest.param("simple string", "simple string", id="string_value"),
        pytest.param(123, "123", id="integer_value"),
        pytest.param(3.14, "3.14", id="float_value"),
        pytest.param(True, "True", id="boolean_value"),
        pytest.param(None, "None", id="none_value"),
    ],
)
def test_md_report_base_format_value(value: str, expected_output: str) -> None:
    """Test the MDReportBase.format_value() method."""

    class FakeMDReportBase(MDReportBase):
        """Fake MDReportBase class."""

        def generate_section(self) -> None:
            pass

    results = ResultManager()

    with StringIO() as mock_file:
        report = FakeMDReportBase(mock_file, results)
        assert report.format_value(value) == expected_output


def test_md_report_error(result_manager: ResultManager) -> None:
    """Test the MDReportGenerator class to OSError to be raised."""
    md_filename = Path("non_existent_directory/non_existent_file.md")
    rm = result_manager.sort(sort_by=["name", "categories", "test"])

    sections = [(section, rm) for section in MDReportGenerator.DEFAULT_SECTIONS]

    with pytest.raises(OSError, match="No such file or directory"):
        MDReportGenerator.generate_sections(sections, md_filename)

    with pytest.raises(OSError, match="No such file or directory"):
        MDReportGenerator.generate(result_manager, md_filename)
