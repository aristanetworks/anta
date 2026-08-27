# Copyright (c) 2026 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""CSV reporting for ANTA security advisory results."""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import TYPE_CHECKING

from anta._advisory.results import get_atomic_cve_ids
from anta.reporter.csv_reporter import ReportCsv

if TYPE_CHECKING:
    import pathlib
    from collections.abc import Iterator, Sequence

    from anta._advisory.models import AdvisoryCVE, AdvisoryMetadata, AdvisoryMitigation, AdvisoryResolution
    from anta._advisory.reporter.reporting import SecurityAdvisoryReport
    from anta.result_manager.models import AtomicTestResult, TestResult


class SecurityAdvisoryReportCsv(ReportCsv):
    """Build a detailed CSV report from security advisory test results."""

    _REPORT_NAME = "security advisory CSV"

    @dataclass
    class Headers(ReportCsv.Headers):
        """Headers for the security advisory CSV report."""

        description: str = "Description"
        advisory_result: str = "Advisory Result"
        result: str = "Result"
        result_description: str = "Result Description"
        result_messages: str = "Result Message(s) JSON"
        advisory_id: str = "Advisory ID"
        advisory_title: str = "Advisory Title"
        advisory_severity: str = "Advisory Severity"
        advisory_url: str = "Advisory URL"
        advisory_description: str = "Advisory Description"
        cve_id: str = "CVE ID"
        cve_severity: str = "CVE Severity"
        cvss_scores: str = "CVSS Scores JSON"
        mitigations: str = "Published Mitigations JSON"
        resolutions: str = "Published Resolutions JSON"

    @staticmethod
    def _format_actions(actions: tuple[AdvisoryMitigation, ...] | tuple[AdvisoryResolution, ...]) -> str:
        """Serialize advisory mitigations or resolutions as a JSON array."""
        return SecurityAdvisoryReportCsv._to_json([{"name": action.name, "details": action.details, "url": action.url} for action in actions])

    @staticmethod
    def _to_json(value: object) -> str:
        """Serialize a value for a structured CSV cell."""
        return json.dumps(value, ensure_ascii=False, separators=(",", ":"))

    @classmethod
    def _format_cvss_scores(cls, cve: AdvisoryCVE | None) -> str:
        """Serialize the selected CVE's CVSS scores as a JSON array."""
        if cve is None:
            return cls._to_json([])
        return cls._to_json([{"version": score.version, "score": score.score, "vector": score.vector} for score in cve.cvss_scores])

    @classmethod
    def _convert_to_list(cls, result: TestResult, row_result: TestResult | AtomicTestResult, advisory: AdvisoryMetadata, cve: AdvisoryCVE | None) -> list[str]:
        """Convert one parent or detailed advisory result into a CSV row."""
        return [
            str(result.name),
            result.test,
            result.description,
            str(result.result),
            str(row_result.result),
            row_result.description,
            cls._to_json(row_result.messages),
            f"SA{advisory.sa_number}",
            advisory.title,
            advisory.severity.value,
            advisory.url,
            advisory.description,
            cve.cve_id if cve is not None else "",
            cve.severity.value if cve is not None else "",
            cls._format_cvss_scores(cve),
            cls._format_actions(advisory.mitigations),
            cls._format_actions(advisory.resolutions),
        ]

    @classmethod
    def _iter_result_rows(cls, result: TestResult, advisory: AdvisoryMetadata) -> Iterator[list[str]]:
        """Yield CVE-oriented rows, using detailed results when associated and the parent result otherwise."""
        associated_results: dict[str, list[AtomicTestResult]] = {}
        unassociated_results: list[AtomicTestResult] = []
        for atomic_result in result.atomic_results:
            if cve_ids := get_atomic_cve_ids(atomic_result):
                for cve_id in cve_ids:
                    associated_results.setdefault(cve_id, []).append(atomic_result)
            else:
                unassociated_results.append(atomic_result)

        for cve in advisory.cves:
            row_results: Sequence[TestResult | AtomicTestResult] = detailed_results if (detailed_results := associated_results.get(cve.cve_id)) else (result,)
            for row_result in row_results:
                yield cls._convert_to_list(result, row_result, advisory, cve)

        for row_result in unassociated_results:
            yield cls._convert_to_list(result, row_result, advisory, None)

        if not advisory.cves and not unassociated_results:
            yield cls._convert_to_list(result, result, advisory, None)

    @classmethod
    def _advisory_headers(cls) -> list[str]:
        """Return the security advisory CSV column headers."""
        return [
            cls.Headers.device,
            cls.Headers.test_name,
            cls.Headers.description,
            cls.Headers.advisory_result,
            cls.Headers.result,
            cls.Headers.result_description,
            cls.Headers.result_messages,
            cls.Headers.advisory_id,
            cls.Headers.advisory_title,
            cls.Headers.advisory_severity,
            cls.Headers.advisory_url,
            cls.Headers.advisory_description,
            cls.Headers.cve_id,
            cls.Headers.cve_severity,
            cls.Headers.cvss_scores,
            cls.Headers.mitigations,
            cls.Headers.resolutions,
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
