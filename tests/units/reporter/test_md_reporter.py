# Copyright (c) 2023-2024 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Test anta.reporter.md_reporter.py."""

from __future__ import annotations

from io import BytesIO, TextIOWrapper
from pathlib import Path

import pytest

from anta.reporter.md_reporter import MDReportBase, MDReportGenerator
from anta.result_manager import ResultManager

DATA_DIR: Path = Path(__file__).parent.parent.parent.resolve() / "data"


def test_md_report_generate(tmp_path: Path, result_manager: ResultManager) -> None:
    """Test the MDReportGenerator class."""
    md_filename = tmp_path / "test.md"
    expected_report = "test_md_report.md"

    # Generate the Markdown report
    MDReportGenerator.generate(result_manager, md_filename)
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

    with TextIOWrapper(BytesIO(b"1 2 3")) as mock_file:
        report = FakeMDReportBase(mock_file, results)
        assert report.generate_heading_name() == "Fake MD Report Base"

        with pytest.raises(NotImplementedError, match="Subclasses should implement this method"):
            report.generate_rows()
