# Copyright (c) 2023-2024 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Test anta.reporter.md_reporter.py."""

from __future__ import annotations

import json
from io import StringIO
from pathlib import Path

import pytest

from anta.reporter.md_reporter import MDReportBase, MDReportGenerator
from anta.result_manager import ResultManager
from anta.result_manager.models import TestResult as FakeTestResult

DATA_DIR: Path = Path(__file__).parent.parent.parent.resolve() / "data"


@pytest.mark.parametrize(
    ("only_failed_tests", "expected_report_name"),
    [
        pytest.param(True, "test_md_report_only_failed_tests.md", id="only_failed_tests"),
        pytest.param(False, "test_md_report_all_tests.md", id="all_tests"),
    ],
)
def test_md_report_generate(tmp_path: Path, expected_report_name: str, *, only_failed_tests: bool) -> None:
    """Test the MDReportGenerator class."""
    # Create a temporary Markdown file
    md_filename = tmp_path / "test.md"

    manager = ResultManager()

    # Load JSON results into the manager
    with (DATA_DIR / "test_md_report_results.json").open("r", encoding="utf-8") as f:
        results = json.load(f)

    for result in results:
        manager.add(FakeTestResult(**result))

    # Generate the Markdown report
    MDReportGenerator.generate(manager, md_filename, only_failed_tests=only_failed_tests)
    assert md_filename.exists()

    # Load the existing Markdown report to compare with the generated one
    with (DATA_DIR / expected_report_name).open("r", encoding="utf-8") as f:
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
