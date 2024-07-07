# Copyright (c) 2023-2024 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Test anta.report.csv_reporter.py."""

# pylint: disable=too-few-public-methods

import csv
import pathlib

from anta.reporter.csv_reporter import ReportCsv
from anta.result_manager import ResultManager

# To avoid succh error:
# pytest.PytestCollectionWarning: cannot collect test class 'TestResult' because it has a __init__ constructor
from anta.result_manager.models import TestResult as FakeResult


class TestReportCsv:
    """Tester for ReportCsv class."""

    def test_report_csv_generate(self, tmp_path: pathlib.Path) -> None:
        """Test CSV reporter."""
        # Create a temporary CSV file path
        csv_filename = tmp_path / "test.csv"

        # Create a ResultManager instance with dummy test results
        results = ResultManager()
        results.results = [
            FakeResult(
                name="dummy",
                test="VerifyEOSVersion",
                result="success",
                messages=["Test passed"],
                description="Verify EOS version",
                categories=["category1", "category2"],
            ),
            FakeResult(
                name="dummy",
                test="VerifyHardwareStatus",
                result="failure",
                messages=["Test failed"],
                description="Verify hardware status",
                categories=["category1"],
            ),
        ]

        # Generate the CSV report
        ReportCsv.generate(results, csv_filename)

        # Read the generated CSV file
        with pathlib.Path.open(csv_filename, encoding="utf-8") as csvfile:
            reader = csv.reader(csvfile, delimiter=",")
            rows = list(reader)

        # Assert the headers
        assert rows[0] == [
            ReportCsv.Headers.device,
            ReportCsv.Headers.test_name,
            ReportCsv.Headers.test_status,
            ReportCsv.Headers.messages,
            ReportCsv.Headers.description,
            ReportCsv.Headers.categories,
        ]

        # Assert the test result rows
        assert rows[1] == [
            "dummy",
            "VerifyEOSVersion",
            "success",
            "Test passed",
            "Verify EOS version",
            "category1, category2",
        ]
        assert rows[2] == [
            "dummy",
            "VerifyHardwareStatus",
            "failure",
            "Test failed",
            "Verify hardware status",
            "category1",
        ]
