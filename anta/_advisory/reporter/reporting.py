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
from anta.result_manager.models import AntaTestStatus

if TYPE_CHECKING:
    from collections.abc import Generator, Sequence
    from datetime import datetime, timedelta
    from pathlib import Path

    from anta._advisory.models import _AdvisoryMetadata
    from anta._runner import AntaRunContext
    from anta.result_manager import ResultManager
    from anta.result_manager.models import AtomicTestResult, TestResult

logger = logging.getLogger(__name__)

_ADVISORY_RESULT_RANK = {
    AntaTestStatus.FAILURE: 0,
    AntaTestStatus.INCONCLUSIVE: 1,
    AntaTestStatus.SUCCESS: 2,
    AntaTestStatus.ERROR: 3,
    AntaTestStatus.SKIPPED: 4,
    AntaTestStatus.UNSET: 5,
}


def _get_advisory_result(result: TestResult | AtomicTestResult) -> str:
    """Translate an ANTA status to advisory-facing result wording."""
    # MITIGATED is projected to native INCONCLUSIVE until the semantic state is retained on the atomic
    # result. Reporters follow that native status and do not recover mitigation from inconclusive
    # message text. SUCCESS remains accepted for results that used the earlier success-based encoding.
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


@dataclass
class AdvisoryResultGroup:
    """Pre-sorted results and metadata for one security advisory."""

    advisory: _AdvisoryMetadata
    results: tuple[TestResult, ...]
    severity: _AdvisoryVulnerabilitySeverity = field(init=False)

    def __post_init__(self) -> None:
        """Compute stable derived data while finalizing the group."""
        self.severity = _get_advisory_severity(self.advisory)


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
    def from_context(cls, run_context: AntaRunContext) -> SecurityAdvisoryRunOverviewData:
        """Build run overview data from an ANTA run context."""
        from anta import __version__ as anta_version  # noqa: PLC0415

        advisory_results = validate_advisory_results(run_context.manager.results)
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
            security_advisories_assessed=len({advisory.sa_number for _, advisory in advisory_results}),
            devices_assessed=len({result.name for result, _ in advisory_results}),
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


def group_advisory_results(results: Sequence[TestResult]) -> tuple[AdvisoryResultGroup, ...]:
    """Validate, group, and sort flat results into an immutable report snapshot."""
    groups: dict[str, tuple[_AdvisoryMetadata, list[TestResult]]] = {}
    for result, advisory in validate_advisory_results(results):
        if advisory.sa_number in groups:
            group_advisory, group_results = groups[advisory.sa_number]
            if group_advisory != advisory:
                msg = f"Conflicting metadata found for security advisory {advisory.sa_number}."
                raise ValueError(msg)
        else:
            group_results = []
            groups[advisory.sa_number] = (advisory, group_results)
        sorted_result = result.model_copy(update={"atomic_results": sorted(result.atomic_results, key=lambda atomic: _ADVISORY_RESULT_RANK[atomic.result])})
        group_results.append(sorted_result)

    result_groups = (
        AdvisoryResultGroup(
            advisory=advisory,
            results=tuple(
                sorted(
                    group_results,
                    key=lambda result: (_ADVISORY_RESULT_RANK[result.result], result.name.casefold(), result.test.casefold()),
                )
            ),
        )
        for advisory, group_results in groups.values()
    )
    return tuple(
        sorted(
            result_groups,
            key=lambda group: (-_ADVISORY_VULNERABILITY_SEVERITY_RANK[group.severity], group.advisory.sa_number),
        )
    )


@dataclass
class SecurityAdvisoryReport:
    """Validated and pre-sorted security advisory report data."""

    groups: tuple[AdvisoryResultGroup, ...]
    source: ResultManager = field(repr=False, compare=False)

    @classmethod
    def from_result_manager(cls, manager: ResultManager, *, allow_empty: bool = False) -> SecurityAdvisoryReport:
        """Build a report model from a result manager."""
        groups = () if allow_empty and not manager.results else group_advisory_results(manager.results)
        return cls(groups=groups, source=manager)


def generate_security_advisory_md_report(
    report: SecurityAdvisoryReport,
    md_filename: Path,
    run_context: AntaRunContext,
) -> None:
    """Generate the default security advisory markdown report."""
    validate_advisory_results(run_context.manager.results)

    from anta._advisory.reporter.md_reporter import (  # noqa: PLC0415
        AdvisoryAssessmentSummary,
        ANTASecurityAdvisoryReport,
        RunOverview,
        SecurityAdvisoryDetails,
    )

    try:
        with md_filename.open("w", encoding="utf-8") as mdfile:
            ANTASecurityAdvisoryReport(mdfile, report, run_context).generate_section()
            if report.groups:
                AdvisoryAssessmentSummary(mdfile, report, run_context).generate_section()
                SecurityAdvisoryDetails(mdfile, report, run_context).generate_section()
            RunOverview(mdfile, report, run_context).generate_section()
    except OSError as exc:
        message = f"OSError caught while writing the Markdown file '{md_filename.resolve()}'."
        anta_log_exception(exc, message, logger)
        raise


def generate_security_advisory_csv_report(report: SecurityAdvisoryReport, csv_filename: Path) -> None:
    """Generate the default security advisory CSV report."""
    from anta._advisory.reporter.csv_reporter import SecurityAdvisoryReportCsv  # noqa: PLC0415

    SecurityAdvisoryReportCsv.write_report(report, csv_filename)
