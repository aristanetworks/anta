# Copyright (c) 2023-2025 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Test anta.reporter.junit_reporter.py."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from anta.reporter.junit_reporter import JUnitReporter

if TYPE_CHECKING:
    from anta.result_manager import ResultManager

DATA_DIR: Path = Path(__file__).parent.parent.parent.resolve() / "data"


def test_junit_reporter_generate(tmp_path: Path, result_manager: ResultManager) -> None:
    """Test the JUnitReporter.generate() class method."""
    junit_filename = tmp_path / "test.xml"
    expected_report = "test_junit_report.xml"

    # Generate the JUnit
    JUnitReporter.generate(results=result_manager, output_path=junit_filename)
    assert junit_filename.exists()

    # Load the existing Markdown report to compare with the generated one
    with (DATA_DIR / expected_report).open("r", encoding="utf-8") as f:
        expected_content = f.read()
    with (junit_filename).open("r", encoding="utf-8") as f, Path("/tmp/junit.xml").open("w", encoding="utf-8") as ff:
        ff.write(f.read())

    # Check the content of the JUnit file
    content = junit_filename.read_text(encoding="utf-8")

    assert content == expected_content
