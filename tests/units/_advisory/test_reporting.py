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
from anta.result_manager.models import TestResult as AntaTestResult
from tests.units._advisory.conftest import (
    ADVISORY,
    ADVISORY_ANTA_VERSION,
    ADVISORY_RUN_END_TIME,
    ADVISORY_RUN_START_TIME,
    build_security_advisory_run_context,
)


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
    assert report.groups[0].results == [result]
    assert report.source is manager


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

    overview = SecurityAdvisoryRunOverviewData.from_context(report, build_security_advisory_run_context(report))

    assert overview.anta_version == ADVISORY_ANTA_VERSION
    assert overview.test_execution_start_time == ADVISORY_RUN_START_TIME
    assert overview.test_execution_end_time == ADVISORY_RUN_END_TIME
    assert overview.security_advisories_assessed == 1
    assert overview.devices_assessed == 1
