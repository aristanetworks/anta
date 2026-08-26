# Copyright (c) 2026 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""CSV reporting for ANTA security advisory results."""

from __future__ import annotations

import csv
import logging
import os
from dataclasses import dataclass
from typing import TYPE_CHECKING

from anta._advisory.reporting import validate_advisory_results
from anta.logger import anta_log_exception
from anta.reporter.csv_reporter import ReportCsv
from anta.tools import convert_categories

if TYPE_CHECKING:
    import pathlib

    from anta._advisory.models import AdvisoryMetadata, AdvisoryMitigation, AdvisoryResolution
    from anta.result_manager import ResultManager
    from anta.result_manager.models import TestResult

logger = logging.getLogger(__name__)


class SecurityAdvisoryReportCsv(ReportCsv):
    """Build a detailed CSV report from security advisory test results."""

    @dataclass
    class Headers(ReportCsv.Headers):
        """Headers for the security advisory CSV report."""

        sa_number: str = "SA Number"
        sa_title: str = "SA Title"
        sa_severity: str = "SA Severity"
        cves: str = "CVE(s)"
        cvss_scores: str = "CVSS Score(s)"
        advisory_url: str = "Advisory URL"
        advisory_description: str = "Advisory Description"
        mitigations: str = "Mitigation(s)"
        resolutions: str = "Resolution(s)"

    @staticmethod
    def _format_actions(actions: tuple[AdvisoryMitigation, ...] | tuple[AdvisoryResolution, ...]) -> str:
        """Format advisory mitigations or resolutions for a CSV cell."""
        return SecurityAdvisoryReportCsv.split_list_to_txt_list([f"{action.name}: {action.details}{f' ({action.url})' if action.url else ''}" for action in actions])

    @classmethod
    def _convert_to_list(cls, result: TestResult, advisory: AdvisoryMetadata) -> list[str]:
        """Convert an advisory test result into a detailed CSV row."""
        messages = cls.split_list_to_txt_list(result.messages) if result.messages else ""
        categories = cls.split_list_to_txt_list(convert_categories(result.categories)) if result.categories else "None"
        cves = cls.split_list_to_txt_list([f"{cve.cve_id} ({cve.severity.value})" for cve in advisory.cves])
        cvss_scores = cls.split_list_to_txt_list(
            [f"{cve.cve_id}: CVSS {score.version}: {score.score:g} ({score.vector})" for cve in advisory.cves for score in cve.cvss_scores]
        )

        return [
            str(result.name),
            result.test,
            result.result,
            messages,
            result.description,
            categories,
            advisory.sa_number,
            advisory.title,
            advisory.severity.value,
            cves,
            cvss_scores,
            advisory.url,
            advisory.description,
            cls._format_actions(advisory.mitigations),
            cls._format_actions(advisory.resolutions),
        ]

    @classmethod
    def generate(cls, results: ResultManager, csv_filename: pathlib.Path) -> None:
        """Build a detailed CSV report from advisory-only results."""
        advisory_results = validate_advisory_results(results.results)
        headers = [
            cls.Headers.device,
            cls.Headers.test_name,
            cls.Headers.test_status,
            cls.Headers.messages,
            cls.Headers.description,
            cls.Headers.categories,
            cls.Headers.sa_number,
            cls.Headers.sa_title,
            cls.Headers.sa_severity,
            cls.Headers.cves,
            cls.Headers.cvss_scores,
            cls.Headers.advisory_url,
            cls.Headers.advisory_description,
            cls.Headers.mitigations,
            cls.Headers.resolutions,
        ]

        try:
            with csv_filename.open(mode="w", encoding="utf-8", newline="") as csvfile:
                csvwriter = csv.writer(csvfile, delimiter=",", lineterminator=os.linesep)
                csvwriter.writerow(headers)
                for result, advisory in advisory_results:
                    csvwriter.writerow(cls._convert_to_list(result, advisory))
        except OSError as exc:
            message = f"OSError caught while writing the security advisory CSV file '{csv_filename.resolve()}'."
            anta_log_exception(exc, message, logger)
            raise
