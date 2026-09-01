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
from anta._advisory.reporter.reporting import _get_advisory_findings, _get_advisory_result, _get_advisory_severity
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
        value = _get_advisory_result(result)
        return Text(value.title(), style=cls._RESULT_STYLES[value])

    @staticmethod
    def _lines(values: list[str]) -> str:
        """Render a list as table-cell lines or an explicit empty marker."""
        return "\n".join(values) if values else "—"

    @staticmethod
    def _bullets(values: list[str]) -> str:
        """Render a list as bulleted table-cell lines or an explicit empty marker."""
        return "\n".join(f"• {value}" for value in values) if values else "—"

    @classmethod
    def _remediations(cls, result: TestResult | AtomicTestResult) -> list[str]:
        """Return stable, deduplicated remediation entries with parent vulnerability attribution."""
        if not isinstance(result, (_AdvisoryTestResult, _AdvisoryAtomicTestResult)):
            return []

        remediations = list(result.remediations)
        if isinstance(result, _AdvisoryTestResult):
            remediations.extend(
                remediation for atomic in result.atomic_results if isinstance(atomic, _AdvisoryAtomicTestResult) for remediation in atomic.remediations
            )
        formatted_remediations = []
        for remediation in dict.fromkeys(remediations):
            vulnerability_ids = cls._remediation_vulnerability_ids(result, remediation)
            prefix = f"{', '.join(vulnerability_ids)}: " if vulnerability_ids else ""
            formatted_remediations.append(f"{prefix}{remediation}")
        return formatted_remediations

    @staticmethod
    def _remediation_vulnerability_ids(result: TestResult | AtomicTestResult, remediation: str) -> tuple[str, ...]:
        """Return advisory-ordered vulnerability IDs sharing a parent remediation."""
        if not isinstance(result, _AdvisoryTestResult):
            return ()

        associated_ids: set[str] = set()
        for atomic in result.atomic_results:
            if not isinstance(atomic, _AdvisoryAtomicTestResult) or remediation not in atomic.remediations:
                continue
            if not atomic.vulnerability_ids:
                return ()
            associated_ids.update(atomic.vulnerability_ids)
        return tuple(vulnerability.id for vulnerability in result.advisory.vulnerabilities if vulnerability.id in associated_ids)

    @staticmethod
    def _atomic_summary(result: TestResult) -> str:
        """Summarize detailed findings using advisory-facing terminology."""
        total = len(result.atomic_results)
        labels = {
            "affected": "affected",
            "inconclusive": "inconclusive",
            "mitigated": "mitigated",
            "error": "errored",
            "skipped": "skipped",
            "unset": "unset",
        }
        advisory_results = [_get_advisory_result(atomic) for atomic in result.atomic_results]
        summaries = [f"{count}/{total} checks {label}" for advisory_result, label in labels.items() if (count := advisory_results.count(advisory_result))]
        return "; ".join(summaries) if summaries else f"All {total} checks not affected"

    @classmethod
    def _expanded_findings(cls, result: TestResult) -> str:
        """Return a detailed-result summary followed by the authoritative evidence."""
        if not result.atomic_results:
            return cls._findings(result)
        findings = f"Detailed findings: {cls._atomic_summary(result)}"
        if result.messages:
            findings += f"\nOverall evidence:\n{cls._findings(result)}"
        return findings

    @classmethod
    def _findings(cls, result: TestResult) -> str:
        """Return parent findings with associated atomic messages labelled by vulnerability ID."""
        return cls._lines(_get_advisory_findings(result))

    @staticmethod
    def _advisory_text(group: AdvisoryResultGroup) -> Text:
        """Return advisory identity and a visible, clickable source URL."""
        advisory = group.advisory
        text = Text(f"SA{advisory.sa_number}: {advisory.title}\n")
        text.append(advisory.url, style=Style(underline=True, link=advisory.url))
        return text

    @classmethod
    def _device_findings_title(cls, group: AdvisoryResultGroup) -> Text:
        """Return a per-advisory device findings title."""
        advisory = group.advisory
        text = Text("Device Findings — ")
        text.append(f"SA{advisory.sa_number}: ")
        text.append(advisory.title, style=Style(underline=True, link=advisory.url))
        text.append(" — ")
        text.append_text(cls._severity_text(_get_advisory_severity(advisory)))
        return text

    def generate_summary(self, report: SecurityAdvisoryReport) -> Table:
        """Generate the advisory exposure summary table."""
        table = Table(title="Security Advisory Summary", show_lines=True)
        table.add_column("Severity", no_wrap=True)
        table.add_column("Advisory", overflow="fold")
        table.add_column("Devices", justify="right", no_wrap=True)
        for column in ("Affected", "Inconclusive", "Mitigated", "Not affected", "Error", "Skipped", "Unset"):
            table.add_column(column, justify="right", no_wrap=True)

        for group in self._groups_by_severity(report):
            severity = _get_advisory_severity(group.advisory)
            counts = dict.fromkeys(self._RESULT_ORDER, 0)
            for result in group.results:
                counts[_get_advisory_result(result)] += 1
            table.add_row(
                self._severity_text(severity),
                self._advisory_text(group),
                str(len({result.name for result in group.results})),
                str(counts["affected"]),
                str(counts["inconclusive"]),
                str(counts["mitigated"]),
                str(counts["not affected"]),
                str(counts["error"]),
                str(counts["skipped"]),
                str(counts["unset"]),
            )
        return table

    def generate_device_findings(self, report: SecurityAdvisoryReport, *, expand_results: bool = False) -> list[Table]:
        """Generate one per-advisory device findings table, optionally with atomic results."""
        return [self._generate_advisory_device_findings(group, expand_results=expand_results) for group in self._groups_by_severity(report)]

    def _generate_advisory_device_findings(self, group: AdvisoryResultGroup, *, expand_results: bool) -> Table:
        """Generate the device findings table for one advisory."""
        table = Table(title=self._device_findings_title(group), expand=True)
        table.add_column("Device", width=18, overflow="fold")
        if expand_results:
            table.add_column("Vulnerability ID(s)", width=24, overflow="fold")
        table.add_column("Result", width=12, no_wrap=True)
        table.add_column("Findings", ratio=3)
        table.add_column("Remediations", ratio=2)

        vulnerability_by_id = {vulnerability.id: vulnerability for vulnerability in group.advisory.vulnerabilities}
        ordered_results = sorted(
            group.results,
            key=lambda result: (self._RESULT_ORDER[_get_advisory_result(result)], str(result.name), result.test),
        )
        for result in ordered_results:
            row: list[str | Text] = [str(result.name)]
            if expand_results:
                row.append("—")
            findings = self._expanded_findings(result) if expand_results else self._findings(result)
            row.extend([self._result_text(result), findings, self._bullets(self._remediations(result))])
            table.add_row(*row, end_section=not expand_results or not result.atomic_results)

            if not expand_results:
                continue
            for index, atomic in enumerate(result.atomic_results):
                tree = "└──" if index == len(result.atomic_results) - 1 else "├──"
                vulnerability_ids = _get_atomic_vulnerability_ids(atomic)
                vulnerabilities: str | Text = self._vulnerability_text(vulnerability_ids, vulnerability_by_id) if vulnerability_ids else "—"
                table.add_row(
                    f"  {tree}",
                    vulnerabilities,
                    self._result_text(atomic),
                    self._lines(atomic.messages),
                    self._bullets(self._remediations(atomic)),
                    end_section=index == len(result.atomic_results) - 1,
                )
        return table
