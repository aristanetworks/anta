# Copyright (c) 2023-2024 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Test anta.report.csv_reporter.py."""

# pylint: disable=too-few-public-methods

import csv
import pathlib
from typing import Any, Callable

from anta.reporter.csv_reporter import ReportCsv
from anta.result_manager import ResultManager

# To avoid such error:
# pytest.PytestCollectionWarning: cannot collect test class 'TestResult' because it has a __init__ constructor


class TestReportCsv:
    """Tester for ReportCsv class."""

    def compare_csv_and_result(self, rows: list[Any], index: int, result_manager: ResultManager) -> None:
        """Compare CSV and TestResult."""
        assert rows[index + 1][0] == result_manager.results[index].name
        assert rows[index + 1][1] == result_manager.results[index].test
        assert rows[index + 1][2] == result_manager.results[index].result
        assert rows[index + 1][3] == ReportCsv().split_list_to_txt_list(result_manager.results[index].messages)
        assert rows[index + 1][4] == result_manager.results[index].description
        assert rows[index + 1][5] == ReportCsv().split_list_to_txt_list(result_manager.results[index].categories)

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
        result_manager.results[0].messages = ["Message 1", "Message 2"]
        result_manager.results[1].messages = ["Cat 1", "Cat 2"]

        # Generate the CSV report
        ReportCsv.generate(result_manager, csv_filename)

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
        for index in [0, max_test_entries - 1]:
            self.compare_csv_and_result(rows, index, result_manager)

        # Assert number of lines
        assert len(rows) == len(result_manager.results) + 1
