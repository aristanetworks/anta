# Copyright (c) 2023-2024 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""CSV Report management for ANTA."""

# pylint: disable = too-few-public-methods
from __future__ import annotations

import csv
import logging
import pathlib
from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from anta.result_manager import ResultManager
    from anta.result_manager.models import TestResult

logger = logging.getLogger(__name__)


class ReportCsv:
    """Build a CSV report."""

    @dataclass()
    class Headers:
        """Headers for the CSV report."""

        device: str = "Device"
        test_name: str = "Test Name"
        test_status: str = "Test Status"
        messages: str = "Message(s)"
        description: str = "Test description"
        categories: str = "Test category"

    @classmethod
    def split_list_to_txt_list(cls, usr_list: list[str], delimiter: str = " - ") -> str:
        """Split list to multi-lines string.

        Parameters
        ----------
            usr_list: List of string to concatenate
            delimiter: A delimiter to use to start string. Defaults to None.

        Returns
        -------
            str: Multi-lines string

        """
        return f"{delimiter}".join(f"{line}" for line in usr_list)

    @classmethod
    def convert_to_list(cls, result: TestResult) -> list[str]:
        """
        Convert a TestResult into a list of string for creating file content.

        Args:
        ----
            results: A TestResult to convert into list.
        """
        message = cls.split_list_to_txt_list(result.messages) if len(result.messages) > 0 else ""
        categories = cls.split_list_to_txt_list(result.categories) if len(result.categories) > 0 else "None"
        return [
            str(result.name),
            result.test,
            result.result,
            message,
            result.description,
            categories,
        ]

    @classmethod
    def generate(cls, results: ResultManager, csv_filename: pathlib.Path) -> None:
        """Build CSV flle with tests results.

        Args:
        ----
            results: A ResultManager instance.
            csv_filename: File path where to save CSV data.
        """
        headers = [
            cls.Headers.device,
            cls.Headers.test_name,
            cls.Headers.test_status,
            cls.Headers.messages,
            cls.Headers.description,
            cls.Headers.categories,
        ]

        with pathlib.Path.open(csv_filename, "w", encoding="utf-8") as csvfile:
            csvwriter = csv.writer(
                csvfile,
                delimiter=",",
            )
            csvwriter.writerow(headers)
            for entry in results.results:
                csvwriter.writerow(cls.convert_to_list(entry))
