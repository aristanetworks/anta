# Copyright (c) 2026 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Markdown reporting for ANTA security advisory results."""

from __future__ import annotations

from typing import TYPE_CHECKING, ClassVar

from anta._advisory.models import _AdvisoryMetadata, _AdvisoryVulnerabilitySeverity
from anta._advisory.reporter.reporting import SecurityAdvisoryRunOverviewData, _get_advisory_result
from anta._advisory.results import _get_atomic_vulnerability_ids
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
    AntaTestStatus.FAILURE: "❌",
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


class ANTASecurityAdvisoryReport(SecurityAdvisoryMDReportBase):
    """Generate the title and table of contents for a security advisory report."""

    ICON = "🛡️"

    def generate_section(self) -> None:
        """Generate the security advisory report heading and table of contents."""
        self.write_heading(heading_level=1)
        toc = "**Table of Contents:**\n\n- [ANTA Security Advisory Report](#anta-security-advisory-report)\n"
        if self.groups:
            toc += "  - [Advisory Exposure Summary](#advisory-exposure-summary)\n  - [Security Advisory Details](#security-advisory-details)\n"
        toc += "  - [Security Advisory Run Overview](#security-advisory-run-overview)"
        self.mdfile.write(toc + "\n\n")


class AdvisoryExposureSummary(SecurityAdvisoryMDReportBase):
    """Generate a compact status summary grouped by security advisory."""

    ICON = "📊"
    _TABLE_COLUMNS: ClassVar[list[str]] = [
        "Security Advisory",
        "Severity",
        "Devices",
        "❌&nbsp;Affected",
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
            advisory_link = f"[SA{advisory.sa_number}: {self.safe_markdown(advisory.title)}](#sa-{advisory.sa_number.lower()})"
            advisory_severity = group.severity
            severity = f"{SEVERITY_ICONS[advisory_severity]}&nbsp;{advisory_severity.value.title()}"
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
        """Generate the advisory exposure summary section."""
        self.write_heading(heading_level=2)
        self.write_table(table_heading=self.TABLE_HEADING)


class SecurityAdvisoryDetails(SecurityAdvisoryMDReportBase):
    """Generate metadata and device findings grouped by security advisory."""

    ICON = "🔐"

    def _write_vulnerabilities(self, advisory: _AdvisoryMetadata) -> None:
        """Write vulnerability details for an advisory."""
        self.mdfile.write("#### Vulnerabilities\n\n")
        heading = self.generate_table_heading(["Vulnerability", "Description", "Severity"])
        self.mdfile.write("\n".join(heading) + "\n")
        for vulnerability in advisory.vulnerabilities:
            vulnerability_id = self.safe_markdown(vulnerability.id)
            description = self.safe_markdown(vulnerability.description)
            self.mdfile.write(f"| {vulnerability_id} | {description} | {vulnerability.severity.value.title()} |\n")
        self.mdfile.write("\n")

    def _write_findings(self, group: AdvisoryResultGroup) -> None:
        """Write per-device findings for an advisory."""
        # TODO: When revisiting Markdown reports, fall back to atomic descriptions and messages if the parent result has no messages.
        # TODO: Render parent and atomic remediation lists once the Markdown remediation presentation is defined.
        self.mdfile.write("#### 🔎 Device Findings\n\n")
        if self.config.expand_results:
            self._write_expanded_findings(group)
            return

        heading = self.generate_table_heading(["Device", "Test", "Result", "Messages"])
        self.mdfile.write("\n".join(heading) + "\n")
        for result in group.results:
            messages = self.safe_markdown("<br>".join(result.messages)) or "-"
            self.mdfile.write(f"| {self.safe_markdown(result.name)} | {self.safe_markdown(result.test)} | {self.format_advisory_result(result)} | {messages} |\n")

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
        heading = self.generate_table_heading(["Device", "Test", "Description", "Vulnerability ID(s)", "Result", "Messages"])
        self.mdfile.write("\n".join(heading) + "\n")
        for result in group.results:
            has_details = bool(result.atomic_results)
            if has_details:
                messages = f"**Detailed findings:** {self._atomic_summary(result)}"
                if result.messages:
                    messages += f"<br>**Overall evidence:** {self.safe_markdown('<br>'.join(result.messages))}"
            else:
                messages = self.safe_markdown("<br>".join(result.messages)) or "-"
            description = self.safe_markdown(result.description) or "-"
            self.mdfile.write(
                f"| {self.safe_markdown(result.name)} | {self.safe_markdown(result.test)} | {description} | - "
                f"| {self.format_advisory_result(result)} | {messages} |\n"
            )
            for index, atomic in enumerate(result.atomic_results):
                tree = "└──" if index == len(result.atomic_results) - 1 else "├──"
                atomic_description = self.safe_markdown(atomic.description) or "-"
                description = f"&nbsp;&nbsp;{tree}&nbsp;{atomic_description}"
                vulnerability_ids = _get_atomic_vulnerability_ids(atomic)
                vulnerabilities = self.safe_markdown(", ".join(vulnerability_ids)) if vulnerability_ids else "-"
                atomic_messages = self.safe_markdown("<br>".join(atomic.messages)) or "-"
                self.mdfile.write(f"| | | {description} | {vulnerabilities} | {self.format_advisory_result(atomic)} | {atomic_messages} |\n")

    def generate_section(self) -> None:
        """Generate detailed advisory metadata and findings."""
        self.write_heading(heading_level=2)
        for index, group in enumerate(self.groups):
            advisory = group.advisory
            anchor = f"sa-{advisory.sa_number.lower()}"
            title = self.safe_markdown(advisory.title)
            self.mdfile.write(f'### [SA{advisory.sa_number}: {title}]({advisory.url}) <a id="{anchor}"></a>\n\n')
            advisory_severity = group.severity
            severity = f"{SEVERITY_ICONS[advisory_severity]} **Severity:** {advisory_severity.value.title()}"
            self.mdfile.write(f"{severity}\n\n{self.safe_markdown(advisory.description)}\n\n")
            self._write_vulnerabilities(advisory)
            self._write_findings(group)
            if index < len(self.groups) - 1:
                self.mdfile.write("\n")
        self.mdfile.write("\n")


class SecurityAdvisoryRunOverview(SecurityAdvisoryMDReportBase):
    """Generate the Run Overview section for a security advisory report."""

    ICON = "📋"

    _TABLE_COLUMNS: ClassVar[list[str]] = ["⚙️ Run Metric", "📝 Details"]
    TABLE_HEADING: ClassVar[list[str]] = MDReportBase.generate_table_heading(columns=_TABLE_COLUMNS)

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

    def generate_rows(self) -> Generator[str, None, None]:
        """Generate the rows for the security advisory run overview table."""
        run_overview = SecurityAdvisoryRunOverviewData.from_context(self.run_context)
        for label, value in run_overview.iter_rows():
            row_value = self._format_row_value(value)
            yield f"| **{label}** | {row_value} |\n"

    def generate_section(self) -> None:
        """Generate the security advisory run overview section."""
        self.write_heading(heading_level=2)
        self.write_table(table_heading=self.TABLE_HEADING, last_table=True)
