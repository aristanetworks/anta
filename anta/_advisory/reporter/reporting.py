# Copyright (c) 2026 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Shared helpers for security advisory reports."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from anta._advisory.results import get_advisory_metadata
from anta.logger import anta_log_exception

if TYPE_CHECKING:
    from collections.abc import Sequence
    from pathlib import Path

    from anta._advisory.models import AdvisoryMetadata
    from anta.result_manager import ResultManager
    from anta.result_manager.models import TestResult

logger = logging.getLogger(__name__)


@dataclass
class AdvisoryResultGroup:
    """Results and shared metadata for one security advisory."""

    advisory: AdvisoryMetadata
    results: list[TestResult] = field(default_factory=list)


def validate_advisory_results(results: Sequence[TestResult]) -> list[tuple[TestResult, AdvisoryMetadata]]:
    """Return results paired with metadata, rejecting empty or mixed result sets."""
    if not results:
        msg = "Security advisory reports require at least one test result."
        raise ValueError(msg)

    advisory_results: list[tuple[TestResult, AdvisoryMetadata]] = []
    non_advisory_results: list[str] = []
    for result in results:
        advisory = get_advisory_metadata(result)
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


def generate_security_advisory_md_report(report: SecurityAdvisoryReport, md_filename: Path) -> None:
    """Generate the default security advisory markdown report."""
    from anta._advisory.reporter.md_reporter import (  # noqa: PLC0415
        AdvisoryExposureSummary,
        ANTASecurityAdvisoryReport,
        SecurityAdvisoryDetails,
    )

    sections = (
        ANTASecurityAdvisoryReport,
        AdvisoryExposureSummary,
        SecurityAdvisoryDetails,
    )
    try:
        with md_filename.open("w", encoding="utf-8") as mdfile:
            for section in sections:
                section(mdfile, report).generate_section()
    except OSError as exc:
        message = f"OSError caught while writing the Markdown file '{md_filename.resolve()}'."
        anta_log_exception(exc, message, logger)
        raise


def generate_security_advisory_csv_report(report: SecurityAdvisoryReport, csv_filename: Path) -> None:
    """Generate the default security advisory CSV report."""
    from anta._advisory.reporter.csv_reporter import SecurityAdvisoryReportCsv  # noqa: PLC0415

    SecurityAdvisoryReportCsv.write_report(report, csv_filename)
