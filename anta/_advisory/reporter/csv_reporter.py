# Copyright (c) 2026 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""CSV reporting for ANTA security advisory results."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from anta._advisory.reporter.reporting import _get_advisory_severity
from anta._advisory.results import _AdvisoryAtomicTestResult, _AdvisoryTestResult, _get_atomic_vulnerability_ids
from anta.reporter.csv_reporter import ReportCsv
from anta.result_manager.models import AntaTestStatus

if TYPE_CHECKING:
    import pathlib
    from collections.abc import Iterator, Sequence

    from anta._advisory.models import _AdvisoryMetadata, _AdvisoryVulnerability
    from anta._advisory.reporter.reporting import SecurityAdvisoryReport
    from anta.result_manager.models import AtomicTestResult, TestResult


class SecurityAdvisoryReportCsv(ReportCsv):
    """Build a detailed CSV report from security advisory test results."""

    _REPORT_NAME = "security advisory CSV"

    @dataclass
    class Headers(ReportCsv.Headers):  # pylint: disable=too-many-instance-attributes
        """Headers for the security advisory CSV report."""

        advisory_result: str = "Advisory Result"
        advisory_result_messages: str = "Advisory Result Messages"
        vulnerability_result: str = "Vulnerability Result"
        vulnerability_result_messages: str = "Vulnerability Result Messages"
        vulnerability_remediation: str = "Vulnerability Remediation"
        advisory_remediation: str = "Advisory Remediation"
        advisory_id: str = "Advisory ID"
        advisory_title: str = "Advisory Title"
        advisory_severity: str = "Advisory Severity"
        advisory_url: str = "Advisory URL"
        advisory_description: str = "Advisory Description"
        vulnerability_id: str = "Vulnerability ID"
        vulnerability_description: str = "Vulnerability Description"
        vulnerability_severity: str = "Vulnerability Severity"

    @staticmethod
    def _format_result(result: TestResult | AtomicTestResult) -> str:
        """Translate an ANTA status to advisory-facing result wording."""
        if result.result is AntaTestStatus.SUCCESS:
            mitigated_opening = "The device is affected but mitigated because "
            return "mitigated" if any(mitigated_opening in message for message in result.messages) else "not affected"
        return {
            AntaTestStatus.UNSET: "unset",
            AntaTestStatus.INCONCLUSIVE: "inconclusive",
            AntaTestStatus.FAILURE: "affected",
            AntaTestStatus.ERROR: "error",
            AntaTestStatus.SKIPPED: "skipped",
        }[result.result]

    @staticmethod
    def _format_remediations(result: TestResult | AtomicTestResult) -> str:
        """Flatten advisory remediation entries into a plain-text CSV cell."""
        if isinstance(result, (_AdvisoryTestResult, _AdvisoryAtomicTestResult)):
            return "\n".join(result.remediations)
        return ""

    @classmethod
    def _convert_to_list(
        cls,
        result: TestResult,
        row_result: TestResult | AtomicTestResult,
        advisory: _AdvisoryMetadata,
        vulnerability: _AdvisoryVulnerability | None,
    ) -> list[str]:
        """Convert one parent or detailed advisory result into a CSV row."""
        return [
            str(result.name),
            result.test,
            cls._format_result(result),
            "\n".join(result.messages),
            cls._format_result(row_result),
            "\n".join(row_result.messages),
            cls._format_remediations(row_result),
            cls._format_remediations(result),
            f"SA{advisory.sa_number}",
            advisory.title,
            _get_advisory_severity(advisory).value,
            advisory.url,
            advisory.description,
            vulnerability.id if vulnerability is not None else "",
            vulnerability.description if vulnerability is not None else "",
            vulnerability.severity.value if vulnerability is not None else "",
        ]

    @classmethod
    def _iter_result_rows(cls, result: TestResult, advisory: _AdvisoryMetadata) -> Iterator[list[str]]:
        """Yield vulnerability-oriented rows, using detailed results when associated and the parent result otherwise."""
        associated_results: dict[str, list[AtomicTestResult]] = {}
        unassociated_results: list[AtomicTestResult] = []
        for atomic_result in result.atomic_results:
            if vulnerability_ids := _get_atomic_vulnerability_ids(atomic_result):
                for vulnerability_id in vulnerability_ids:
                    associated_results.setdefault(vulnerability_id, []).append(atomic_result)
            else:
                unassociated_results.append(atomic_result)

        for vulnerability in advisory.vulnerabilities:
            row_results: Sequence[TestResult | AtomicTestResult] = detailed_results if (detailed_results := associated_results.get(vulnerability.id)) else (result,)
            for row_result in row_results:
                yield cls._convert_to_list(result, row_result, advisory, vulnerability)

        for row_result in unassociated_results:
            yield cls._convert_to_list(result, row_result, advisory, None)

        if not advisory.vulnerabilities and not unassociated_results:
            yield cls._convert_to_list(result, result, advisory, None)

    @classmethod
    def _advisory_headers(cls) -> list[str]:
        """Return the security advisory CSV column headers."""
        return [
            cls.Headers.device,
            cls.Headers.test_name,
            cls.Headers.advisory_result,
            cls.Headers.advisory_result_messages,
            cls.Headers.vulnerability_result,
            cls.Headers.vulnerability_result_messages,
            cls.Headers.vulnerability_remediation,
            cls.Headers.advisory_remediation,
            cls.Headers.advisory_id,
            cls.Headers.advisory_title,
            cls.Headers.advisory_severity,
            cls.Headers.advisory_url,
            cls.Headers.advisory_description,
            cls.Headers.vulnerability_id,
            cls.Headers.vulnerability_description,
            cls.Headers.vulnerability_severity,
        ]

    @classmethod
    def _iter_advisory_rows(cls, report: SecurityAdvisoryReport) -> Iterator[list[str]]:
        """Yield CSV rows for the provided security advisory report."""
        for group in report.groups:
            for result in group.results:
                yield from cls._iter_result_rows(result, group.advisory)

    @classmethod
    def write_report(cls, report: SecurityAdvisoryReport, csv_filename: pathlib.Path) -> None:
        """Build a detailed CSV report from a validated security advisory report."""
        cls._write_rows(csv_filename, cls._advisory_headers(), cls._iter_advisory_rows(report))
