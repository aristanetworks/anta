# Copyright (c) 2026 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Unit tests for security advisory reporting helpers."""

from __future__ import annotations

import pytest

from anta._advisory.models import _AdvisoryVulnerability, _AdvisoryVulnerabilitySeverity
from anta._advisory.reporter.reporting import (
    SecurityAdvisoryReport,
    SecurityAdvisoryRunOverviewData,
    _get_advisory_severity,
    validate_advisory_results,
)
from anta._advisory.results import _AdvisoryTestResult
from anta.result_manager import ResultManager
from anta.result_manager.models import AntaTestStatus
from anta.result_manager.models import TestResult as AntaTestResult
from tests.units._advisory.conftest import (
    ADVISORY,
    ADVISORY_ANTA_VERSION,
    ADVISORY_RUN_END_TIME,
    ADVISORY_RUN_START_TIME,
    build_security_advisory_run_context,
)
from tests.units._advisory.reporting_data import build_security_advisory_result_manager


def test_validate_advisory_results() -> None:
    """Verify advisory results are returned with their typed metadata."""
    result = _AdvisoryTestResult(
        name="leaf1",
        test="VerifyAdvisory",
        categories=["advisories"],
        description="Verify an advisory.",
        advisory=ADVISORY,
    )

    assert validate_advisory_results([result]) == [(result, ADVISORY)]


def test_security_advisory_report_from_result_manager() -> None:
    """Verify grouped advisory report data is built once from a result manager."""
    result = _AdvisoryTestResult(
        name="leaf1",
        test="VerifyAdvisory",
        categories=["advisories"],
        description="Verify an advisory.",
        advisory=ADVISORY,
    )
    manager = ResultManager()
    manager.add(result)

    report = SecurityAdvisoryReport.from_result_manager(manager)

    assert len(report.groups) == 1
    assert report.groups[0].advisory is ADVISORY
    assert report.groups[0].results == (result,)
    assert report.source is manager


def test_security_advisory_report_sorting() -> None:
    """Verify advisory groups and their findings expose security-prioritized ordering."""
    report = SecurityAdvisoryReport.from_result_manager(build_security_advisory_result_manager())

    assert isinstance(report.groups, tuple)
    assert [group.advisory.sa_number for group in report.groups] == ["0120", "0121", "0117"]
    critical_findings = report.groups[0].results
    assert critical_findings
    assert isinstance(critical_findings, tuple)
    assert report.groups[0].severity is _AdvisoryVulnerabilitySeverity.CRITICAL
    assert [result.result for result in critical_findings] == [
        AntaTestStatus.FAILURE,
        AntaTestStatus.FAILURE,
        AntaTestStatus.FAILURE,
        AntaTestStatus.FAILURE,
        AntaTestStatus.SUCCESS,
        AntaTestStatus.SUCCESS,
        AntaTestStatus.ERROR,
        AntaTestStatus.SKIPPED,
    ]
    assert [result.name for result in critical_findings[:4]] == ["DC1-LEAF1", "DC1-LEAF3", "DC1-SPINE2", "DC2-LEAF2"]


def test_security_advisory_report_sorts_atomic_results() -> None:
    """Verify atomic findings are sorted without mutating the source result manager."""
    result = _AdvisoryTestResult(
        name="leaf1",
        test="VerifyAdvisory",
        categories=["advisories"],
        description="Verify an advisory.",
        advisory=ADVISORY,
    )
    for status in (
        AntaTestStatus.SKIPPED,
        AntaTestStatus.ERROR,
        AntaTestStatus.SUCCESS,
        AntaTestStatus.INCONCLUSIVE,
        AntaTestStatus.FAILURE,
    ):
        result.add(status.value, status)
    manager = ResultManager()
    manager.add(result)
    source_atomic_results = tuple(result.atomic_results)

    report = SecurityAdvisoryReport.from_result_manager(manager)

    assert tuple(manager.results[0].atomic_results) == source_atomic_results
    assert [atomic.result for atomic in manager.results[0].atomic_results] == [
        AntaTestStatus.SKIPPED,
        AntaTestStatus.ERROR,
        AntaTestStatus.SUCCESS,
        AntaTestStatus.INCONCLUSIVE,
        AntaTestStatus.FAILURE,
    ]
    assert [atomic.result for atomic in report.groups[0].results[0].atomic_results] == [
        AntaTestStatus.FAILURE,
        AntaTestStatus.INCONCLUSIVE,
        AntaTestStatus.SUCCESS,
        AntaTestStatus.ERROR,
        AntaTestStatus.SKIPPED,
    ]


def test_get_advisory_severity() -> None:
    """Verify advisory severity is the highest known vulnerability severity."""
    assert _get_advisory_severity(ADVISORY) is _AdvisoryVulnerabilitySeverity.HIGH
    assert _get_advisory_severity(ADVISORY.model_copy(update={"vulnerabilities": ()})) is _AdvisoryVulnerabilitySeverity.UNKNOWN

    vulnerabilities = (
        _AdvisoryVulnerability(id="UNKNOWN", description="Unknown severity."),
        _AdvisoryVulnerability(id="NONE", description="No severity.", severity=_AdvisoryVulnerabilitySeverity.NONE),
    )
    assert _get_advisory_severity(ADVISORY.model_copy(update={"vulnerabilities": vulnerabilities})) is _AdvisoryVulnerabilitySeverity.NONE


def test_validate_advisory_results_rejects_empty_results() -> None:
    """Verify an advisory report cannot be generated without results."""
    with pytest.raises(ValueError, match="at least one test result"):
        validate_advisory_results([])


def test_validate_advisory_results_rejects_mixed_results() -> None:
    """Verify ordinary results cannot be included in an advisory report."""
    result = AntaTestResult(name="leaf1", test="VerifyNTP", categories=["ntp"], description="Verify NTP.")

    with pytest.raises(ValueError, match="leaf1/VerifyNTP"):
        validate_advisory_results([result])


def test_security_advisory_run_overview_data_from_context() -> None:
    """Verify run overview data combines run context with advisory report metrics."""
    result = _AdvisoryTestResult(
        name="leaf1",
        test="VerifyAdvisory",
        categories=["advisories"],
        description="Verify an advisory.",
        advisory=ADVISORY,
    )
    manager = ResultManager()
    manager.add(result)
    report = SecurityAdvisoryReport.from_result_manager(manager)

    overview = SecurityAdvisoryRunOverviewData.from_context(build_security_advisory_run_context(report))

    assert overview.anta_version == ADVISORY_ANTA_VERSION
    assert overview.test_execution_start_time == ADVISORY_RUN_START_TIME
    assert overview.test_execution_end_time == ADVISORY_RUN_END_TIME
    assert overview.security_advisories_assessed == 1
    assert overview.devices_assessed == 1
