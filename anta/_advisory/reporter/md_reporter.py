# Copyright (c) 2026 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Markdown reporting for ANTA security advisory results."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, ClassVar

from anta._advisory.models import AdvisoryMetadata, AdvisoryMitigation, AdvisoryResolution, AdvisorySeverity
from anta._advisory.results import get_atomic_cve_ids
from anta.reporter.md_reporter import MDReportBase
from anta.result_manager.models import AntaTestStatus

if TYPE_CHECKING:
    from collections.abc import Generator
    from typing import TextIO

    from anta._advisory.reporter.reporting import AdvisoryResultGroup, SecurityAdvisoryReport
    from anta.result_manager.models import TestResult

SEVERITY_ICONS = {
    AdvisorySeverity.CRITICAL: "🔴",
    AdvisorySeverity.HIGH: "🟠",
    AdvisorySeverity.MEDIUM: "🟡",
    AdvisorySeverity.LOW: "🔵",
    AdvisorySeverity.UNKNOWN: "⚪",
}
"""Icons used to distinguish advisory severity without relying on color alone."""


class SecurityAdvisoryMDReportBase(MDReportBase):
    """Base class for security advisory markdown report sections."""

    def __init__(self, mdfile: TextIO, report: SecurityAdvisoryReport, extra_data: dict[str, Any] | None = None) -> None:
        """Initialize a section with pre-validated advisory report data."""
        self.report = report
        self.groups = report.groups
        super().__init__(mdfile, report.source, extra_data)


class ANTASecurityAdvisoryReport(SecurityAdvisoryMDReportBase):
    """Generate the title and table of contents for a security advisory report."""

    ICON = "🛡️"

    def generate_section(self) -> None:
        """Generate the security advisory report heading and table of contents."""
        self.write_heading(heading_level=1)
        toc = (
            "**Table of Contents:**\n\n"
            "- [ANTA Security Advisory Report](#anta-security-advisory-report)\n"
            "  - [Advisory Exposure Summary](#advisory-exposure-summary)\n"
            "  - [Security Advisory Details](#security-advisory-details)"
        )
        self.mdfile.write(toc + "\n\n")


class AdvisoryExposureSummary(SecurityAdvisoryMDReportBase):
    """Generate a compact status summary grouped by security advisory."""

    ICON = "📊"
    _TABLE_COLUMNS: ClassVar[list[str]] = [
        "Security Advisory",
        "Severity",
        "Devices",
        "✅&nbsp;Success",
        "❓&nbsp;Inconclusive",
        "❌&nbsp;Failure",
        "❗&nbsp;Error",
        "⏭️&nbsp;Skipped",
    ]
    TABLE_HEADING: ClassVar[list[str]] = MDReportBase.generate_table_heading(columns=_TABLE_COLUMNS)

    @staticmethod
    def _count(group: AdvisoryResultGroup, status: AntaTestStatus) -> int:
        """Count results with a specific status."""
        return sum(result.result is status for result in group.results)

    def generate_rows(self) -> Generator[str, None, None]:
        """Generate one summary row per security advisory."""
        for group in self.groups:
            advisory = group.advisory
            advisory_link = f"[SA{advisory.sa_number}: {self.safe_markdown(advisory.title)}](#sa-{advisory.sa_number.lower()})"
            severity = f"{SEVERITY_ICONS[advisory.severity]}&nbsp;{advisory.severity.value.title()}"
            devices = len({result.name for result in group.results})
            yield (
                f"| {advisory_link} | {severity} | {devices} "
                f"| {self._count(group, AntaTestStatus.SUCCESS)} "
                f"| {self._count(group, AntaTestStatus.INCONCLUSIVE)} "
                f"| {self._count(group, AntaTestStatus.FAILURE)} "
                f"| {self._count(group, AntaTestStatus.ERROR)} "
                f"| {self._count(group, AntaTestStatus.SKIPPED)} |\n"
            )

    def generate_section(self) -> None:
        """Generate the advisory exposure summary section."""
        self.write_heading(heading_level=2)
        self.write_table(table_heading=self.TABLE_HEADING)


class SecurityAdvisoryDetails(SecurityAdvisoryMDReportBase):
    """Generate metadata and device findings grouped by security advisory."""

    ICON = "🔐"

    def __init__(self, mdfile: TextIO, report: SecurityAdvisoryReport, extra_data: dict[str, Any] | None = None) -> None:
        """Initialize advisory details and configure detailed result expansion."""
        super().__init__(mdfile, report, extra_data)
        report_options = (self.extra_data or {}).get("_report_options", {})
        self.expand_results = report_options.get("expand_results", False)

    def _write_cves(self, advisory: AdvisoryMetadata) -> None:
        """Write CVE and CVSS details for an advisory."""
        self.mdfile.write("#### CVEs\n\n")
        heading = self.generate_table_heading(["CVE", "Severity", "CVSS Version", "Base Score", "Vector"])
        self.mdfile.write("\n".join(heading) + "\n")
        for cve in advisory.cves:
            if not cve.cvss_scores:
                self.mdfile.write(f"| {cve.cve_id} | {cve.severity.value.title()} | - | - | - |\n")
                continue
            for score in cve.cvss_scores:
                self.mdfile.write(f"| {cve.cve_id} | {cve.severity.value.title()} | {score.version} | {score.score:g} | `{self.safe_markdown(score.vector)}` |\n")
        self.mdfile.write("\n")

    def _write_findings(self, group: AdvisoryResultGroup) -> None:
        """Write per-device findings for an advisory."""
        self.mdfile.write("#### 🔎 Device Findings\n\n")
        if self.expand_results:
            self._write_expanded_findings(group)
            return

        heading = self.generate_table_heading(["Device", "Test", "Result", "Messages"])
        self.mdfile.write("\n".join(heading) + "\n")
        for result in group.results:
            messages = self.safe_markdown("<br>".join(result.messages)) or "-"
            self.mdfile.write(f"| {self.safe_markdown(result.name)} | {self.safe_markdown(result.test)} | {self.format_status(result.result)} | {messages} |\n")
        self.mdfile.write("\n")

    @staticmethod
    def _atomic_summary(result: TestResult) -> str:
        """Summarize detailed findings using the regular Markdown reporter convention."""
        total = len(result.atomic_results)
        inconclusive = sum(atomic.result is AntaTestStatus.INCONCLUSIVE for atomic in result.atomic_results)
        failed = sum(atomic.result not in {AntaTestStatus.SUCCESS, AntaTestStatus.INCONCLUSIVE} for atomic in result.atomic_results)
        if failed and inconclusive:
            return f"{failed}/{total}&nbsp;checks&nbsp;failed; {inconclusive}/{total}&nbsp;checks&nbsp;inconclusive"
        if failed:
            return f"{failed}/{total}&nbsp;checks&nbsp;failed"
        if inconclusive:
            return f"{inconclusive}/{total}&nbsp;checks&nbsp;inconclusive"
        return f"All&nbsp;{total}&nbsp;checks&nbsp;passed"

    def _write_expanded_findings(self, group: AdvisoryResultGroup) -> None:
        """Write parent advisory results followed by their actual detailed issue results."""
        heading = self.generate_table_heading(["Device", "Test", "Description", "CVE(s)", "Result", "Messages"])
        self.mdfile.write("\n".join(heading) + "\n")
        for result in group.results:
            has_details = bool(result.atomic_results)
            messages = self._atomic_summary(result) if has_details else self.safe_markdown("<br>".join(result.messages)) or "-"
            description = self.safe_markdown(result.description) or "-"
            self.mdfile.write(
                f"| {self.safe_markdown(result.name)} | {self.safe_markdown(result.test)} | {description} | - | {self.format_status(result.result)} | {messages} |\n"
            )
            for index, atomic in enumerate(result.atomic_results):
                tree = "└──" if index == len(result.atomic_results) - 1 else "├──"
                atomic_description = self.safe_markdown(atomic.description) or "-"
                description = f"&nbsp;&nbsp;{tree}&nbsp;{atomic_description}"
                cve_ids = get_atomic_cve_ids(atomic)
                cves = self.safe_markdown(", ".join(cve_ids)) if cve_ids else "-"
                atomic_messages = self.safe_markdown("<br>".join(atomic.messages)) or "-"
                self.mdfile.write(f"| | | {description} | {cves} | {self.format_status(atomic.result)} | {atomic_messages} |\n")
        self.mdfile.write("\n")

    def _write_actions(
        self,
        heading: str,
        icon: str,
        actions: tuple[AdvisoryMitigation, ...] | tuple[AdvisoryResolution, ...],
        *,
        trailing_separator: bool = True,
    ) -> None:
        """Write mitigation or resolution guidance."""
        self.mdfile.write(f"#### {icon} {heading}\n\n")
        if not actions:
            ending = "\n\n" if trailing_separator else "\n"
            self.mdfile.write(f"*No {heading.lower()} are published for this advisory.*{ending}")
            return

        for action in actions:
            name = self.safe_markdown(action.name)
            details = self.safe_markdown(action.details)
            reference = f" ([Reference]({action.url}))" if action.url else ""
            self.mdfile.write(f"- **{name}:** {details}{reference}\n")
        if trailing_separator:
            self.mdfile.write("\n")

    def generate_section(self) -> None:
        """Generate detailed advisory metadata and findings."""
        self.write_heading(heading_level=2)
        for index, group in enumerate(self.groups):
            advisory = group.advisory
            anchor = f"sa-{advisory.sa_number.lower()}"
            title = self.safe_markdown(advisory.title)
            self.mdfile.write(f'### [SA{advisory.sa_number}: {title}]({advisory.url}) <a id="{anchor}"></a>\n\n')
            severity = f"{SEVERITY_ICONS[advisory.severity]} **Severity:** {advisory.severity.value.title()}"
            self.mdfile.write(f"{severity}\n\n{self.safe_markdown(advisory.description)}\n\n")
            self._write_cves(advisory)
            self._write_findings(group)
            self._write_actions("Mitigations", "🛠️", advisory.mitigations)
            self._write_actions("Resolutions", "✅", advisory.resolutions, trailing_separator=index < len(self.groups) - 1)
