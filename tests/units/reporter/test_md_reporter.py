# Copyright (c) 2023-2024 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Test anta.reporter.md_reporter.py."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from anta.reporter.md_reporter import MDReportGenerator
from anta.result_manager import ResultManager
from anta.result_manager.models import TestResult as FakeTestResult

DATA_DIR: Path = Path(__file__).parent.parent.parent.resolve() / "data"


# pylint: disable=too-few-public-methods
class TestMDReportGenerator:
    """Test MDReportGenerator class."""

    @pytest.mark.parametrize(
        ("only_failed_tests"),
        [
            pytest.param(True, id="only_failed_tests"),
            pytest.param(False, id="all_tests"),
        ],
    )
    def test_generate(self, tmp_path: Path, *, only_failed_tests: bool) -> None:
        """Test the generate class method."""
        # Create a temporary Markdown file
        md_filename = tmp_path / "test_md_report.md"

        manager = ResultManager()

        # Load JSON results into the manager
        with (DATA_DIR / "test_results.json").open("r", encoding="utf-8") as f:
            results = json.load(f)

        for result in results:
            manager.add(FakeTestResult(**result))

        # Generate the Markdown report
        MDReportGenerator.generate(manager, md_filename, only_failed_tests=only_failed_tests)
        assert md_filename.exists()

        # Check the content of the Markdown file
        content = md_filename.read_text(encoding="utf-8")

        sections = [
            "# ANTA Report",
            "## Test Results Summary",
            "### Summary Totals",
            "### Summary Totals Device Under Test",
            "### Summary Totals Per Category",
            "## Failed Test Results Summary",
        ]

        for section in sections:
            assert section in content
            if not only_failed_tests:
                assert "## All Test Results" in content
