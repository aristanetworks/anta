# Copyright (c) 2026 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Rich table reporting for ANTA security advisory results."""

from __future__ import annotations

from typing import TYPE_CHECKING, ClassVar

from rich.style import Style
from rich.table import Table
from rich.text import Text

from anta import RICH_COLOR_PALETTE
from anta._advisory.models import _ADVISORY_VULNERABILITY_SEVERITY_RANK, _AdvisoryVulnerabilitySeverity
from anta._advisory.reporter.reporting import _format_advisory_result, _get_advisory_severity
from anta._advisory.results import _AdvisoryAtomicTestResult, _AdvisoryTestResult, _get_atomic_vulnerability_ids

if TYPE_CHECKING:
    from anta._advisory.models import _AdvisoryVulnerability
    from anta._advisory.reporter.reporting import AdvisoryResultGroup, SecurityAdvisoryReport
    from anta.result_manager.models import AtomicTestResult, TestResult


SEVERITY_STYLES = {
    _AdvisoryVulnerabilitySeverity.CRITICAL: "red",
    _AdvisoryVulnerabilitySeverity.HIGH: "orange3",
    _AdvisoryVulnerabilitySeverity.MEDIUM: "yellow3",
    _AdvisoryVulnerabilitySeverity.LOW: "blue",
    _AdvisoryVulnerabilitySeverity.NONE: "green4",
    _AdvisoryVulnerabilitySeverity.UNKNOWN: "grey74",
}


class SecurityAdvisoryReportTable:
    """Generate summary and per-device Rich tables for security advisory results."""

    _RESULT_ORDER: ClassVar[dict[str, int]] = {
        "affected": 0,
        "error": 1,
        "inconclusive": 2,
        "mitigated": 3,
        "not affected": 4,
        "skipped": 5,
        "unset": 6,
    }
    _RESULT_STYLES: ClassVar[dict[str, str]] = {
        "affected": RICH_COLOR_PALETTE.FAILURE,
        "error": RICH_COLOR_PALETTE.ERROR,
        "inconclusive": RICH_COLOR_PALETTE.INCONCLUSIVE,
        "mitigated": RICH_COLOR_PALETTE.SUCCESS,
        "not affected": RICH_COLOR_PALETTE.SUCCESS,
        "skipped": RICH_COLOR_PALETTE.SKIPPED,
        "unset": RICH_COLOR_PALETTE.UNSET,
    }

    @staticmethod
    def _groups_by_severity(report: SecurityAdvisoryReport) -> list[AdvisoryResultGroup]:
        """Return advisory groups ordered by descending severity and advisory number."""
        return sorted(
            report.groups,
            key=lambda group: (-_ADVISORY_VULNERABILITY_SEVERITY_RANK[_get_advisory_severity(group.advisory)], group.advisory.sa_number),
        )

    @staticmethod
    def _severity_text(severity: _AdvisoryVulnerabilitySeverity) -> Text:
        """Return a severity label that does not rely on color alone."""
        text = Text()
        text.append("●", style=SEVERITY_STYLES[severity])
        text.append(f" {severity.value.title()}")
        return text

    @staticmethod
    def _vulnerability_text(vulnerability_ids: tuple[str, ...], vulnerability_by_id: dict[str, _AdvisoryVulnerability]) -> Text:
        """Return vulnerability IDs colored by severity."""
        text = Text()
        for index, vulnerability_id in enumerate(vulnerability_ids):
            if index:
                text.append("\n")
            vulnerability = vulnerability_by_id[vulnerability_id]
            text.append("●", style=SEVERITY_STYLES[vulnerability.severity])
            text.append(f" {vulnerability_id}")
        return text

    @classmethod
    def _result_text(cls, result: TestResult | AtomicTestResult) -> Text:
        """Return an advisory-facing result label with the ANTA status color."""
        value = _format_advisory_result(result)
        return Text(value.title(), style=cls._RESULT_STYLES[value])

    @staticmethod
    def _lines(values: list[str]) -> str:
        """Render a list as table-cell lines or an explicit empty marker."""
        return "\n".join(values) if values else "—"

    @staticmethod
    def _bullets(values: list[str]) -> str:
        """Render a list as bulleted table-cell lines or an explicit empty marker."""
        return "\n".join(f"• {value}" for value in values) if values else "—"

    @staticmethod
    def _remediations(result: TestResult | AtomicTestResult) -> list[str]:
        """Return stable, deduplicated remediation entries for an advisory result."""
        if not isinstance(result, (_AdvisoryTestResult, _AdvisoryAtomicTestResult)):
            return []

        remediations = list(result.remediations)
        if isinstance(result, _AdvisoryTestResult):
            remediations.extend(
                remediation for atomic in result.atomic_results if isinstance(atomic, _AdvisoryAtomicTestResult) for remediation in atomic.remediations
            )
        return list(dict.fromkeys(remediations))

    @staticmethod
    def _advisory_text(group: AdvisoryResultGroup) -> Text:
        """Return advisory identity and a visible, clickable source URL."""
        advisory = group.advisory
        text = Text(f"SA{advisory.sa_number}: {advisory.title}\n")
        text.append(advisory.url, style=Style(underline=True, link=advisory.url))
        return text

    def generate_summary(self, report: SecurityAdvisoryReport) -> Table:
        """Generate the advisory exposure summary table."""
        table = Table(title="Security Advisory Summary", show_lines=True)
        table.add_column("Severity", no_wrap=True)
        table.add_column("Advisory", overflow="fold")
        table.add_column("Devices", justify="right", no_wrap=True)
        for column in ("Affected", "Mitigated", "Not affected", "Inconclusive", "Error", "Skipped", "Unset"):
            table.add_column(column, justify="right", no_wrap=True)

        for group in self._groups_by_severity(report):
            severity = _get_advisory_severity(group.advisory)
            counts = dict.fromkeys(self._RESULT_ORDER, 0)
            for result in group.results:
                counts[_format_advisory_result(result)] += 1
            table.add_row(
                self._severity_text(severity),
                self._advisory_text(group),
                str(len({result.name for result in group.results})),
                str(counts["affected"]),
                str(counts["mitigated"]),
                str(counts["not affected"]),
                str(counts["inconclusive"]),
                str(counts["error"]),
                str(counts["skipped"]),
                str(counts["unset"]),
            )
        return table

    def generate_device_findings(self, report: SecurityAdvisoryReport, *, expand_results: bool = False) -> Table:
        """Generate per-device advisory findings, optionally with atomic results."""
        table = Table(title="Security Advisory Device Findings", show_lines=True)
        table.add_column("Severity", no_wrap=True)
        table.add_column("Advisory", no_wrap=True)
        table.add_column("Device", no_wrap=True)
        if expand_results:
            table.add_column("Description")
            table.add_column("Vulnerability ID(s)")
        table.add_column("Result", no_wrap=True)
        table.add_column("Findings")
        table.add_column("Remediations")

        for group in self._groups_by_severity(report):
            severity = _get_advisory_severity(group.advisory)
            vulnerability_by_id = {vulnerability.id: vulnerability for vulnerability in group.advisory.vulnerabilities}
            ordered_results = sorted(
                group.results,
                key=lambda result: (self._RESULT_ORDER[_format_advisory_result(result)], str(result.name), result.test),
            )
            for result in ordered_results:
                row: list[str | Text] = [
                    self._severity_text(severity),
                    f"SA{group.advisory.sa_number}",
                    str(result.name),
                ]
                if expand_results:
                    row.extend(["Overall advisory", "—"])
                row.extend([self._result_text(result), self._lines(result.messages), self._bullets(self._remediations(result))])
                table.add_row(*row)

                if not expand_results:
                    continue
                for index, atomic in enumerate(result.atomic_results):
                    tree = "└──" if index == len(result.atomic_results) - 1 else "├──"
                    vulnerability_ids = _get_atomic_vulnerability_ids(atomic)
                    if vulnerability_ids:
                        description = "\n".join(vulnerability_by_id[vulnerability_id].description for vulnerability_id in vulnerability_ids)
                        vulnerabilities = self._vulnerability_text(vulnerability_ids, vulnerability_by_id)
                    else:
                        description = atomic.description
                        vulnerabilities = "—"
                    table.add_row(
                        "",
                        "",
                        "",
                        f"{tree} {description}",
                        vulnerabilities,
                        self._result_text(atomic),
                        self._lines(atomic.messages),
                        self._bullets(self._remediations(atomic)),
                    )
        return table
