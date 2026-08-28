# Copyright (c) 2026 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Shared helpers for security advisory reports."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

from anta._advisory.models import _ADVISORY_VULNERABILITY_SEVERITY_RANK, _AdvisoryVulnerabilitySeverity
from anta._advisory.results import _get_advisory_metadata
from anta.logger import anta_log_exception

if TYPE_CHECKING:
    from collections.abc import Generator, Sequence
    from datetime import datetime, timedelta
    from pathlib import Path

    from anta._advisory.models import _AdvisoryMetadata
    from anta._runner import AntaRunContext
    from anta.result_manager import ResultManager
    from anta.result_manager.models import TestResult

logger = logging.getLogger(__name__)


@dataclass
class AdvisoryResultGroup:
    """Results and shared metadata for one security advisory."""

    advisory: _AdvisoryMetadata
    results: list[TestResult] = field(default_factory=list)


@dataclass(frozen=True)
class SecurityAdvisoryRunOverviewData:
    """Run metadata rendered in the security advisory Markdown report."""

    anta_version: str
    test_execution_start_time: datetime | None
    test_execution_end_time: datetime | None
    total_duration: timedelta | None
    total_devices_in_inventory: int
    devices_unreachable_at_setup: tuple[str, ...]
    devices_filtered_at_setup: tuple[str, ...]
    filters_applied: dict[str, list[str]] | None
    security_advisories_assessed: int
    devices_assessed: int
    warnings_at_setup: tuple[str, ...] = ()

    @classmethod
    def from_context(cls, report: SecurityAdvisoryReport, run_context: AntaRunContext) -> SecurityAdvisoryRunOverviewData:
        """Build run overview data from an ANTA run context and advisory report."""
        from anta import __version__ as anta_version  # noqa: PLC0415

        active_filters_dict: dict[str, list[str]] = {}
        if run_context.filters.tags:
            active_filters_dict["tags"] = sorted(run_context.filters.tags)
        if run_context.filters.tests:
            active_filters_dict["tests"] = sorted(run_context.filters.tests)
        if run_context.filters.devices:
            active_filters_dict["devices"] = sorted(run_context.filters.devices)

        return cls(
            anta_version=anta_version,
            test_execution_start_time=run_context.start_time,
            test_execution_end_time=run_context.end_time,
            total_duration=run_context.duration,
            total_devices_in_inventory=run_context.total_devices_in_inventory,
            devices_unreachable_at_setup=tuple(run_context.devices_unreachable_at_setup),
            devices_filtered_at_setup=tuple(run_context.devices_filtered_at_setup),
            filters_applied=active_filters_dict or None,
            security_advisories_assessed=len(report.groups),
            devices_assessed=len({result.name for group in report.groups for result in group.results}),
            warnings_at_setup=tuple(run_context.warnings_at_setup),
        )

    def iter_rows(self) -> Generator[tuple[str, Any], None, None]:
        """Yield display rows as ``(label, value)`` pairs in report order."""
        yield "ANTA Version", self.anta_version
        yield "Test Execution Start Time", self.test_execution_start_time
        yield "Test Execution End Time", self.test_execution_end_time
        yield "Total Duration", self.total_duration
        yield "Total Devices In Inventory", self.total_devices_in_inventory
        yield "Devices Unreachable At Setup", self.devices_unreachable_at_setup
        yield "Devices Filtered At Setup", self.devices_filtered_at_setup
        yield "Filters Applied", self.filters_applied
        yield "Security Advisories Assessed", self.security_advisories_assessed
        yield "Devices Assessed", self.devices_assessed
        if self.warnings_at_setup:
            yield "Warnings At Setup", self.warnings_at_setup


@dataclass(frozen=True)
class SecurityAdvisoryReportConfig:
    """User-facing options for security advisory report generation."""

    expand_results: bool = False


def _get_advisory_severity(advisory: _AdvisoryMetadata) -> _AdvisoryVulnerabilitySeverity:
    """Return the highest normalized severity among an advisory's vulnerabilities."""
    return max(
        (vulnerability.severity for vulnerability in advisory.vulnerabilities),
        key=_ADVISORY_VULNERABILITY_SEVERITY_RANK.__getitem__,
        default=_AdvisoryVulnerabilitySeverity.UNKNOWN,
    )


def validate_advisory_results(results: Sequence[TestResult]) -> list[tuple[TestResult, _AdvisoryMetadata]]:
    """Return results paired with metadata, rejecting empty or mixed result sets."""
    if not results:
        msg = "Security advisory reports require at least one test result."
        raise ValueError(msg)

    advisory_results: list[tuple[TestResult, _AdvisoryMetadata]] = []
    non_advisory_results: list[str] = []
    for result in results:
        advisory = _get_advisory_metadata(result)
        if advisory is None:
            non_advisory_results.append(f"{result.name}/{result.test}")
        else:
            advisory_results.append((result, advisory))

    if non_advisory_results:
        msg = f"Security advisory reports only support advisory test results. Found non-advisory results: {', '.join(non_advisory_results)}."
        raise ValueError(msg)

    return advisory_results


def group_advisory_results(results: Sequence[TestResult]) -> list[AdvisoryResultGroup]:
    """Validate and group flat results by security advisory number."""
    groups: dict[str, AdvisoryResultGroup] = {}
    for result, advisory in validate_advisory_results(results):
        if advisory.sa_number in groups:
            group = groups[advisory.sa_number]
            if group.advisory != advisory:
                msg = f"Conflicting metadata found for security advisory {advisory.sa_number}."
                raise ValueError(msg)
        else:
            group = groups[advisory.sa_number] = AdvisoryResultGroup(advisory=advisory)
        group.results.append(result)

    for group in groups.values():
        group.results.sort(key=lambda result: (result.name, result.test))
    return [groups[sa_number] for sa_number in sorted(groups)]


@dataclass
class SecurityAdvisoryReport:
    """Validated, grouped security advisory results ready for report generation."""

    groups: list[AdvisoryResultGroup]
    source: ResultManager = field(repr=False, compare=False)

    @classmethod
    def from_result_manager(cls, manager: ResultManager) -> SecurityAdvisoryReport:
        """Build a report model from a result manager."""
        return cls(groups=group_advisory_results(manager.results), source=manager)


def generate_security_advisory_md_report(
    report: SecurityAdvisoryReport,
    md_filename: Path,
    run_context: AntaRunContext,
    config: SecurityAdvisoryReportConfig,
) -> None:
    """Generate the default security advisory markdown report."""
    from anta._advisory.reporter.md_reporter import (  # noqa: PLC0415
        AdvisoryExposureSummary,
        ANTASecurityAdvisoryReport,
        SecurityAdvisoryDetails,
        SecurityAdvisoryRunOverview,
    )

    sections = (
        ANTASecurityAdvisoryReport,
        AdvisoryExposureSummary,
        SecurityAdvisoryDetails,
        SecurityAdvisoryRunOverview,
    )
    try:
        with md_filename.open("w", encoding="utf-8") as mdfile:
            for section in sections:
                section(mdfile, report, config, run_context).generate_section()
    except OSError as exc:
        message = f"OSError caught while writing the Markdown file '{md_filename.resolve()}'."
        anta_log_exception(exc, message, logger)
        raise


def generate_security_advisory_csv_report(report: SecurityAdvisoryReport, csv_filename: Path) -> None:
    """Generate the default security advisory CSV report."""
    from anta._advisory.reporter.csv_reporter import SecurityAdvisoryReportCsv  # noqa: PLC0415

    SecurityAdvisoryReportCsv.write_report(report, csv_filename)
