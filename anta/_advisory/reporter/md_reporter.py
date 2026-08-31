# Copyright (c) 2026 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Markdown reporting for ANTA security advisory results."""

from __future__ import annotations

from typing import TYPE_CHECKING, ClassVar

from anta._advisory.models import _ADVISORY_VULNERABILITY_SEVERITY_RANK, _AdvisoryMetadata, _AdvisoryVulnerabilitySeverity
from anta._advisory.reporter.reporting import SecurityAdvisoryRunOverviewData, _get_advisory_result
from anta._advisory.results import _AdvisoryAtomicTestResult, _AdvisoryTestResult, _get_atomic_vulnerability_ids
from anta.reporter.md_reporter import MDReportBase
from anta.result_manager.models import AntaTestStatus

if TYPE_CHECKING:
    from collections.abc import Generator
    from typing import TextIO

    from anta._advisory.reporter.reporting import AdvisoryResultGroup, SecurityAdvisoryReport, SecurityAdvisoryReportConfig
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

RESULT_ICONS = {
    AntaTestStatus.SUCCESS: "✅",
    AntaTestStatus.INCONCLUSIVE: "❓",
    AntaTestStatus.FAILURE: "🛑",
    AntaTestStatus.ERROR: "❗",
    AntaTestStatus.SKIPPED: "⏭️",
    AntaTestStatus.UNSET: "-",
}
"""Icons used to distinguish advisory results without relying on color alone."""


class SecurityAdvisoryMDReportBase(MDReportBase):
    """Base class for security advisory markdown report sections."""

    def __init__(
        self,
        mdfile: TextIO,
        report: SecurityAdvisoryReport,
        config: SecurityAdvisoryReportConfig,
        run_context: AntaRunContext,
    ) -> None:
        """Initialize a section with pre-validated advisory report data."""
        self.report = report
        self.groups = report.groups
        self.config = config
        self.run_context = run_context
        super().__init__(mdfile, report.source, extra_data=None)

    @staticmethod
    def format_advisory_result(result: TestResult | AtomicTestResult) -> str:
        """Format an ANTA result using advisory-facing terminology."""
        return f"{RESULT_ICONS[result.result]}&nbsp;{_get_advisory_result(result).title()}"

    @staticmethod
    def format_severity(severity: _AdvisoryVulnerabilitySeverity) -> str:
        """Format a vulnerability severity with its identifying icon."""
        return f"{SEVERITY_ICONS[severity]}&nbsp;{severity.value.title()}"

    def format_remediations(self, result: TestResult | AtomicTestResult) -> str:
        """Format advisory remediation entries for a Markdown table cell."""
        if not isinstance(result, (_AdvisoryTestResult, _AdvisoryAtomicTestResult)):
            return "-"
        remediations = list(result.remediations)
        atomic_remediations: list[str] = []
        if isinstance(result, _AdvisoryTestResult):
            atomic_remediations = [
                remediation for atomic in result.atomic_results if isinstance(atomic, _AdvisoryAtomicTestResult) for remediation in atomic.remediations
            ]
            remediations.extend(atomic_remediations)
        unique_remediations = dict.fromkeys(remediations)
        formatted_remediations = []
        for remediation in unique_remediations:
            vulnerability_ids = self._remediation_vulnerability_ids(result, remediation)
            prefix = f"{', '.join(vulnerability_ids)}: " if vulnerability_ids else ""
            formatted_remediations.append(f"{prefix}{remediation}")
        if atomic_remediations:
            return "<br>".join(f"•&nbsp;{self.safe_markdown(remediation)}" for remediation in formatted_remediations)
        return self.safe_markdown("\n".join(formatted_remediations)) or "-"

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

    def format_findings(self, result: TestResult) -> str:
        """Format findings and label associated atomic findings with vulnerability IDs."""
        messages = list(result.messages)
        if isinstance(result, _AdvisoryTestResult):
            for atomic in result.atomic_results:
                vulnerability_ids = _get_atomic_vulnerability_ids(atomic)
                if not vulnerability_ids:
                    continue
                prefix = f"{', '.join(vulnerability_ids)}: "
                for message in atomic.messages:
                    inherited_message = f"{atomic.description} - {message}"
                    try:
                        index = messages.index(inherited_message)
                    except ValueError:
                        continue
                    messages[index] = f"{prefix}{message}"
        return self.safe_markdown("<br>".join(messages)) or "-"


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
        "✅&nbsp;Mitigated",
        "✅&nbsp;Not Affected",
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

    def _write_findings(self, group: AdvisoryResultGroup) -> None:
        """Write per-device findings for an advisory."""
        # TODO: When revisiting Markdown reports, fall back to atomic descriptions and messages if the parent result has no messages.
        self.mdfile.write("#### 🔎 Device Findings\n\n")
        if self.config.expand_results:
            self._write_expanded_findings(group)
            return

        heading = self.generate_table_heading(["Device", "Result", "Findings", "Remediations"])
        self.mdfile.write("\n".join(heading) + "\n")
        for result in group.results:
            findings = self.format_findings(result)
            remediation = self.format_remediations(result)
            self.mdfile.write(f"| {self.safe_markdown(result.name)} | {self.format_advisory_result(result)} | {findings} | {remediation} |\n")

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
        summaries = [f"{count}/{total}&nbsp;checks&nbsp;{label}" for advisory_result, label in labels.items() if (count := advisory_results.count(advisory_result))]
        return "; ".join(summaries) if summaries else f"All&nbsp;{total}&nbsp;checks&nbsp;not&nbsp;affected"

    def _write_expanded_findings(self, group: AdvisoryResultGroup) -> None:
        """Write parent advisory results followed by their actual detailed issue results."""
        heading = self.generate_table_heading(["Device", "Vulnerability ID(s)", "Result", "Findings", "Remediations"])
        self.mdfile.write("\n".join(heading) + "\n")
        vulnerability_by_id = {vulnerability.id: vulnerability for vulnerability in group.advisory.vulnerabilities}
        for result in group.results:
            has_details = bool(result.atomic_results)
            if has_details:
                findings = f"**Detailed findings:** {self._atomic_summary(result)}"
                if result.messages:
                    findings += f"<br>**Overall evidence:** {self.format_findings(result)}"
            else:
                findings = self.safe_markdown("<br>".join(result.messages)) or "-"
            remediation = self.format_remediations(result)
            self.mdfile.write(f"| {self.safe_markdown(result.name)} | - | {self.format_advisory_result(result)} | {findings} | {remediation} |\n")
            for index, atomic in enumerate(result.atomic_results):
                tree = "└──" if index == len(result.atomic_results) - 1 else "├──"
                vulnerability_ids = _get_atomic_vulnerability_ids(atomic)
                vulnerabilities = (
                    "<br>".join(
                        f"{SEVERITY_ICONS[vulnerability_by_id[vulnerability_id].severity]}&nbsp;{self.safe_markdown(vulnerability_id)}"
                        for vulnerability_id in vulnerability_ids
                    )
                    if vulnerability_ids
                    else "-"
                )
                atomic_findings = self.safe_markdown("<br>".join(atomic.messages)) or "-"
                remediation = self.format_remediations(atomic)
                self.mdfile.write(f"| &nbsp;&nbsp;{tree} | {vulnerabilities} | {self.format_advisory_result(atomic)} | {atomic_findings} | {remediation} |\n")

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
