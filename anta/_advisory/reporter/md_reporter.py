# Copyright (c) 2026 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Markdown reporting for ANTA security advisory results."""

from __future__ import annotations

from typing import TYPE_CHECKING, ClassVar

from anta._advisory.models import _ADVISORY_VULNERABILITY_SEVERITY_RANK, _AdvisoryVulnerabilitySeverity
from anta._advisory.remediation import render_remediation_markdown
from anta._advisory.reporter.reporting import SecurityAdvisoryRunOverviewData, _get_advisory_result
from anta._advisory.results import _AdvisoryAtomicTestResult, _get_atomic_vulnerability_ids
from anta.reporter.md_reporter import MDReportBase

if TYPE_CHECKING:
    from collections.abc import Generator
    from typing import TextIO

    from anta._advisory.models import _AdvisoryMetadata, _AdvisoryVulnerability
    from anta._advisory.reporter.reporting import AdvisoryResultGroup, SecurityAdvisoryReport
    from anta._runner import AntaRunContext
    from anta.result_manager.models import AtomicTestResult, TestResult

SEVERITY_ICONS = {
    _AdvisoryVulnerabilitySeverity.CRITICAL: "🔴",
    _AdvisoryVulnerabilitySeverity.HIGH: "🟠",
    _AdvisoryVulnerabilitySeverity.MEDIUM: "🟡",
    _AdvisoryVulnerabilitySeverity.LOW: "🔵",
    _AdvisoryVulnerabilitySeverity.NONE: "🟢",
    _AdvisoryVulnerabilitySeverity.UNKNOWN: "⚪",
}
"""Icons used to distinguish advisory severity without relying on color alone."""

ADVISORY_RESULT_ICONS = {
    "affected": "🛑",
    "inconclusive": "❓",
    "mitigated": "🛡️",
    "not affected": "✅",
    "error": "❗",
    "skipped": "⏭️",
    "unset": "-",
}
"""Icons used to distinguish advisory-facing results without relying on color alone."""

ADVISORY_RESULT_LABELS = {
    "not affected": "Not&nbsp;Affected",
}
"""Markdown labels that need a non-breaking space so column headers and cells do not wrap mid-phrase."""


class SecurityAdvisoryMDReportBase(MDReportBase):
    """Base class for security advisory markdown report sections."""

    def __init__(
        self,
        mdfile: TextIO,
        report: SecurityAdvisoryReport,
        run_context: AntaRunContext,
    ) -> None:
        """Initialize a section with pre-validated advisory report data."""
        self.report = report
        self.groups = report.groups
        self.run_context = run_context
        super().__init__(mdfile, report.source, extra_data=None)

    @staticmethod
    def format_advisory_result(result: TestResult | AtomicTestResult) -> str:
        """Format an ANTA result using advisory-facing terminology."""
        advisory_result = _get_advisory_result(result)
        label = ADVISORY_RESULT_LABELS.get(advisory_result, advisory_result.title())
        return f"{ADVISORY_RESULT_ICONS[advisory_result]}&nbsp;{label}"

    @staticmethod
    def format_severity(severity: _AdvisoryVulnerabilitySeverity) -> str:
        """Format a vulnerability severity with its identifying icon."""
        return f"{SEVERITY_ICONS[severity]}&nbsp;{severity.value.title()}"

    def format_remediations(self, result: AtomicTestResult) -> str:
        """Format structured remediation for a Markdown table cell."""
        if not isinstance(result, _AdvisoryAtomicTestResult) or result.remediation is None:
            return "-"
        return self.safe_markdown(render_remediation_markdown(result.remediation, result.remediation_guidance))


class ANTASecurityAdvisoryReport(SecurityAdvisoryMDReportBase):
    """Generate the title and table of contents for a security advisory report."""

    ICON = "🛡️"

    def generate_section(self) -> None:
        """Generate the security advisory report heading and table of contents."""
        self.mdfile.write('<h1 id="anta-security-advisory-report" align="center">🛡️ ANTA Security Advisory Report 🛡️</h1>\n\n')
        toc = "**Table of Contents:**\n\n"
        if self.groups:
            toc += "- [Advisory Assessment Summary](#advisory-assessment-summary)\n- [Security Advisory Details](#security-advisory-details)\n"
            for group in self.groups:
                advisory = group.advisory
                toc += f"  - [{self.safe_markdown(advisory.title)}](#sa-{advisory.sa_number.lower()})\n"
        toc += "- [Run Overview](#run-overview)"
        self.mdfile.write(toc + "\n\n")


class AdvisoryAssessmentSummary(SecurityAdvisoryMDReportBase):
    """Generate a compact status summary grouped by security advisory."""

    ICON = "📊"
    _TABLE_COLUMNS: ClassVar[list[str]] = [
        "Security Advisory",
        "Severity",
        "Devices",
        "🛑&nbsp;Affected",
        "❓&nbsp;Inconclusive",
        "🛡️&nbsp;Mitigated",
        "✅&nbsp;Not&nbsp;Affected",
        "❗&nbsp;Error",
        "⏭️&nbsp;Skipped",
    ]
    TABLE_HEADING: ClassVar[list[str]] = MDReportBase.generate_table_heading(columns=_TABLE_COLUMNS)

    @staticmethod
    def _count(group: AdvisoryResultGroup, advisory_result: str) -> int:
        """Count results with a specific advisory-facing result."""
        return sum(_get_advisory_result(result) == advisory_result for result in group.results)

    def generate_rows(self) -> Generator[str, None, None]:
        """Generate one summary row per security advisory."""
        for group in self.groups:
            advisory = group.advisory
            advisory_link = f"[{self.safe_markdown(advisory.title)}](#sa-{advisory.sa_number.lower()})"
            severity = self.format_severity(group.severity)
            devices = len({result.name for result in group.results})
            yield (
                f"| {advisory_link} | {severity} | {devices} "
                f"| {self._count(group, 'affected')} "
                f"| {self._count(group, 'inconclusive')} "
                f"| {self._count(group, 'mitigated')} "
                f"| {self._count(group, 'not affected')} "
                f"| {self._count(group, 'error')} "
                f"| {self._count(group, 'skipped')} |\n"
            )

    def generate_section(self) -> None:
        """Generate the advisory assessment summary section."""
        self.write_heading(heading_level=2)
        self.write_table(table_heading=self.TABLE_HEADING)


class SecurityAdvisoryDetails(SecurityAdvisoryMDReportBase):
    """Generate metadata and device findings grouped by security advisory."""

    ICON = "🔐"

    def _write_vulnerabilities(self, advisory: _AdvisoryMetadata) -> None:
        """Write vulnerability details for an advisory."""
        # NOTE: Nested tables are not supported consistently by every Markdown renderer. Prefix every table line and pad it with quoted blank lines to maximize
        # compatibility across renderers that support Markdown tables.
        heading = self.generate_table_heading(["Vulnerability", "Severity", "Description"])
        self.mdfile.write("\n".join(f"> {line}" for line in heading) + "\n")
        vulnerabilities = sorted(
            advisory.vulnerabilities,
            key=lambda vulnerability: (-_ADVISORY_VULNERABILITY_SEVERITY_RANK[vulnerability.severity], vulnerability.id.casefold()),
        )
        for vulnerability in vulnerabilities:
            vulnerability_id = self.safe_markdown(vulnerability.id)
            description = self.safe_markdown(vulnerability.description)
            self.mdfile.write(f"> | {vulnerability_id} | {self.format_severity(vulnerability.severity)} | {description} |\n")
        self.mdfile.write(">\n\n")

    def _format_vulnerability(self, vulnerability_id: str, vulnerability_by_id: dict[str, _AdvisoryVulnerability]) -> str:
        """Format a vulnerability identifier with its severity icon."""
        vulnerability = vulnerability_by_id[vulnerability_id]
        return f"{SEVERITY_ICONS[vulnerability.severity]}&nbsp;{self.safe_markdown(vulnerability_id)}"

    def _write_findings(self, group: AdvisoryResultGroup) -> None:
        """Write one device finding row per vulnerability assessment."""
        self.mdfile.write("#### 🔎 Device Findings\n\n")
        heading = self.generate_table_heading(["Device", "Vulnerability", "Result", "Findings", "Remediations"])
        self.mdfile.write("\n".join(heading) + "\n")
        vulnerability_by_id = {vulnerability.id: vulnerability for vulnerability in group.advisory.vulnerabilities}
        for result in group.results:
            for atomic in result.atomic_results:
                findings = self.safe_markdown("<br>".join(atomic.messages)) or "-"
                remediation = self.format_remediations(atomic)
                vulnerability_ids = _get_atomic_vulnerability_ids(atomic) or (None,)
                for vulnerability_id in vulnerability_ids:
                    vulnerability = "-" if vulnerability_id is None else self._format_vulnerability(vulnerability_id, vulnerability_by_id)
                    self.mdfile.write(
                        f"| {self.safe_markdown(result.name)} | {vulnerability} | {self.format_advisory_result(atomic)} | {findings} | {remediation} |\n"
                    )

    def generate_section(self) -> None:
        """Generate detailed advisory metadata and findings."""
        self.write_heading(heading_level=2)
        for index, group in enumerate(self.groups):
            advisory = group.advisory
            anchor = f"sa-{advisory.sa_number.lower()}"
            title = self.safe_markdown(advisory.title)
            self.mdfile.write(f'### {title} <a id="{anchor}"></a>\n\n')
            advisory_severity = group.severity
            severity = f"**Severity:** {SEVERITY_ICONS[advisory_severity]} {advisory_severity.value.title()}"
            description = self.safe_markdown(advisory.description)
            self.mdfile.write(f"> {severity}\\\n> **URL:** <{advisory.url}>\n>\n> {description}\n>\n")
            self._write_vulnerabilities(advisory)
            self._write_findings(group)
            if index < len(self.groups) - 1:
                self.mdfile.write("\n")
        self.mdfile.write("\n")


class RunOverview(SecurityAdvisoryMDReportBase):
    """Generate the Run Overview section for a security advisory report."""

    ICON = "📋"

    def _format_row_value(self, value: object) -> str:
        """Format one run overview value for Markdown table rendering."""
        if isinstance(value, list | tuple):
            if not value:
                return "None"
            return "<br>".join(self.safe_markdown(str(item)) for item in value)
        if isinstance(value, dict):
            if not value:
                return "None"
            items = []
            for sub_key, sub_value in value.items():
                sub_label = self.format_snake_case_to_title_case(sub_key)
                items.append(f"{self.safe_markdown(sub_label)}: {self.safe_markdown(self.format_value(sub_value))}")
            return "<br>".join(items)
        return self.safe_markdown(self.format_value(value))

    def generate_section(self) -> None:
        """Generate the Run Overview section."""
        self.write_heading(heading_level=2)
        run_overview = SecurityAdvisoryRunOverviewData.from_context(self.run_context)
        start_time = self._format_row_value(run_overview.test_execution_start_time)
        end_time = self._format_row_value(run_overview.test_execution_end_time)
        duration = self._format_row_value(run_overview.total_duration)
        overview_metrics: list[tuple[str, object]] = [
            ("ANTA Version", run_overview.anta_version),
            ("Duration", f"{duration} ({start_time} → {end_time})"),
            ("Security Advisories Tested", run_overview.security_advisories_assessed),
            ("Total Devices In Inventory", run_overview.total_devices_in_inventory),
            ("Devices Assessed", run_overview.devices_assessed),
            ("Devices Unreachable At Setup", run_overview.devices_unreachable_at_setup),
            ("Devices Filtered At Setup", run_overview.devices_filtered_at_setup),
            ("Filters Applied", run_overview.filters_applied),
        ]
        if run_overview.warnings_at_setup:
            overview_metrics.append(("Warnings At Setup", run_overview.warnings_at_setup))
        self.mdfile.write("| | |\n| :- | :- |\n")
        for label, value in overview_metrics:
            self.mdfile.write(f"| **{label}** | {self._format_row_value(value)} |\n")
