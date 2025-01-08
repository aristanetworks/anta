# Copyright (c) 2023-2025 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Test anta.report.csv_reporter.py."""

# pylint: disable=too-few-public-methods

import csv
import pathlib
from typing import Any, Callable
from unittest.mock import patch

import pytest

from anta.reporter.csv_reporter import ReportCsv
from anta.result_manager import ResultManager
from anta.tools import convert_categories


class TestReportCsv:
    """Tester for ReportCsv class."""

    def compare_csv_and_result(self, rows: list[Any], index: int, result_manager: ResultManager) -> None:
        """Compare CSV and TestResult."""
        assert rows[index + 1][0] == result_manager.results[index].name
        assert rows[index + 1][1] == result_manager.results[index].test
        assert rows[index + 1][2] == result_manager.results[index].result
        assert rows[index + 1][3] == ReportCsv().split_list_to_txt_list(result_manager.results[index].messages)
        assert rows[index + 1][4] == result_manager.results[index].description
        assert rows[index + 1][5] == ReportCsv().split_list_to_txt_list(convert_categories(result_manager.results[index].categories))

    def test_report_csv_generate(
        self,
        result_manager_factory: Callable[[int], ResultManager],
        tmp_path: pathlib.Path,
    ) -> None:
        """Test CSV reporter."""
        max_test_entries = 10

        # Create a temporary CSV file path
        csv_filename = tmp_path / "test.csv"

        # Create a ResultManager instance with dummy test results
        result_manager = result_manager_factory(max_test_entries)
        # Test usecase with list of messages
        result_manager.results[0].messages = ["Message 1", "Message 2"]
        # Test usecase with list of categories
        result_manager.results[1].messages = ["Cat 1", "Cat 2"]

        # Generate the CSV report
        ReportCsv.generate(result_manager, csv_filename)

        # Read the generated CSV file - newline required on Windows..
        with pathlib.Path.open(csv_filename, encoding="utf-8", newline="") as csvfile:
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
        for index in [0, max_test_entries - 1]:
            self.compare_csv_and_result(rows, index, result_manager)

        # Assert number of lines: Number of TestResults + CSV Headers
        assert len(rows) == len(result_manager.results) + 1

    def test_report_csv_generate_os_error(
        self,
        result_manager_factory: Callable[[int], ResultManager],
        tmp_path: pathlib.Path,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        """Test CSV reporter OSError."""
        # Create a ResultManager instance with dummy test results
        max_test_entries = 10
        result_manager = result_manager_factory(max_test_entries)

        csv_filename = tmp_path / "read_only.csv"

        with patch("pathlib.Path.open", side_effect=OSError("Any OSError")), pytest.raises(OSError, match="Any OSError"):
            # Generate the CSV report
            ReportCsv.generate(result_manager, csv_filename)

        assert len(caplog.record_tuples) == 1
        assert "OSError caught while writing the CSV file" in caplog.text
