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
    _get_advisory_result,
    _get_advisory_severity,
    iter_advisory_report_rows,
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
from tests.units._advisory.reporting_data import _add_vulnerability_atomic, _FindingKind, build_security_advisory_result_manager


def test_validate_advisory_results() -> None:
    """Verify advisory results are returned with their typed metadata."""
    result = _AdvisoryTestResult(
        name="leaf1",
        test="VerifyAdvisory",
        categories=["advisories"],
        description="Verify an advisory.",
        advisory=ADVISORY,
    )
    _add_vulnerability_atomic(result, "CVE-2026-0001", AntaTestStatus.SUCCESS, "not affected")

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
    _add_vulnerability_atomic(result, "CVE-2026-0001", AntaTestStatus.SUCCESS, "not affected")
    manager = ResultManager()
    manager.add(result)

    report = SecurityAdvisoryReport.from_result_manager(manager)

    assert len(report.groups) == 1
    assert report.groups[0].advisory is ADVISORY
    assert report.groups[0].results == (result,)
    assert report.source is manager


def test_security_advisory_report_sorting() -> None:
    """Verify advisory groups are severity ordered and results are device ordered."""
    report = SecurityAdvisoryReport.from_result_manager(build_security_advisory_result_manager())

    assert isinstance(report.groups, tuple)
    assert [group.advisory.sa_number for group in report.groups] == ["0147", "0146", "0117"]
    critical_findings = report.groups[0].results
    assert critical_findings
    assert isinstance(critical_findings, tuple)
    assert report.groups[0].severity is _AdvisoryVulnerabilitySeverity.CRITICAL
    assert [result.name for result in critical_findings] == [
        "DC1-LEAF1",
        "DC1-LEAF2",
        "DC1-LEAF3",
        "DC1-LEAF4",
        "DC1-SPINE1",
        "DC1-SPINE2",
        "DC2-LEAF1",
        "DC2-LEAF2",
    ]
    assert [_get_advisory_result(result) for result in critical_findings] == [
        "affected",
        "not affected",
        "affected",
        "skipped",
        "not affected",
        "affected",
        "error",
        "affected",
    ]


def test_security_advisory_report_preserves_atomic_result_order() -> None:
    """Verify reporting preserves the test's atomic emission order."""
    result = _AdvisoryTestResult(
        name="leaf1",
        test="VerifyAdvisory",
        categories=["advisories"],
        description="Verify an advisory.",
        advisory=ADVISORY,
    )
    _add_vulnerability_atomic(result, "CVE-2026-0002", AntaTestStatus.ERROR, "error", finding_kind="error")
    _add_vulnerability_atomic(result, "CVE-2026-0001", AntaTestStatus.SUCCESS, "not affected")
    manager = ResultManager()
    manager.add(result)
    source_atomic_results = tuple(result.atomic_results)

    report = SecurityAdvisoryReport.from_result_manager(manager)

    assert tuple(manager.results[0].atomic_results) == source_atomic_results
    assert [atomic.result for atomic in manager.results[0].atomic_results] == [
        AntaTestStatus.ERROR,
        AntaTestStatus.SUCCESS,
    ]
    assert [_get_advisory_result(atomic) for atomic in report.groups[0].results[0].atomic_results] == [
        "error",
        "not affected",
    ]


@pytest.mark.parametrize(
    ("higher_status", "higher_kind", "expected"),
    [
        pytest.param(AntaTestStatus.SUCCESS, "mitigated", "mitigated", id="mitigated"),
        pytest.param(AntaTestStatus.FAILURE, "inconclusive", "inconclusive", id="inconclusive"),
        pytest.param(AntaTestStatus.FAILURE, "affected", "affected", id="affected"),
        pytest.param(AntaTestStatus.ERROR, "error", "error", id="error"),
    ],
)
def test_advisory_result_precedence_comes_from_atomic_findings(higher_status: AntaTestStatus, higher_kind: _FindingKind, expected: str) -> None:
    """Use finding objects, not the generic parent status or messages, for advisory conclusions."""
    result = _AdvisoryTestResult(
        name="leaf1",
        test="VerifyAdvisory",
        categories=["advisories"],
        description="Verify an advisory.",
        advisory=ADVISORY,
    )
    _add_vulnerability_atomic(result, "CVE-2026-0001", AntaTestStatus.SUCCESS, "ambiguous text")
    _add_vulnerability_atomic(result, "CVE-2026-0002", higher_status, "ambiguous text", finding_kind=higher_kind)

    assert _get_advisory_result(result) == expected


@pytest.mark.parametrize("status", [AntaTestStatus.SKIPPED, AntaTestStatus.ERROR])
def test_lifecycle_results_are_expanded_only_for_reporting(status: AntaTestStatus) -> None:
    """Expand parent-only lifecycle outcomes into one report row per published vulnerability."""
    result = _AdvisoryTestResult(
        name="leaf1",
        test="VerifyAdvisory",
        categories=["advisories"],
        description="Verify an advisory.",
        advisory=ADVISORY,
    )
    result._set_status(status, "Framework lifecycle message.")

    assert validate_advisory_results([result]) == [(result, ADVISORY)]
    assert _get_advisory_result(result) == status.value
    assert not result.atomic_results

    rows = tuple(iter_advisory_report_rows(result, ADVISORY))
    assert [row.vulnerability_id for row in rows] == ["CVE-2026-0001", "CVE-2026-0002"]
    assert all(row.result is result for row in rows)


def test_structured_error_finding_remains_an_evaluated_atomic() -> None:
    """Distinguish an evaluated ErrorResult from a parent-only framework error."""
    result = _AdvisoryTestResult(
        name="leaf1",
        test="VerifyAdvisory",
        categories=["advisories"],
        description="Verify an advisory.",
        advisory=ADVISORY,
    )
    _add_vulnerability_atomic(result, "CVE-2026-0001", AntaTestStatus.ERROR, "Required evidence is unavailable.", finding_kind="error")

    assert validate_advisory_results([result]) == [(result, ADVISORY)]
    rows = tuple(iter_advisory_report_rows(result, ADVISORY))
    assert len(rows) == 1
    assert rows[0].result is result.atomic_results[0]
    assert rows[0].vulnerability_id == "CVE-2026-0001"


@pytest.mark.parametrize("status", [AntaTestStatus.SKIPPED, AntaTestStatus.ERROR])
def test_lifecycle_result_without_published_vulnerabilities_expands_to_one_report_row(status: AntaTestStatus) -> None:
    """Keep a whole-advisory row when lifecycle reporting has no vulnerability metadata."""
    advisory = ADVISORY.model_copy(update={"vulnerabilities": ()})
    result = _AdvisoryTestResult(
        name="leaf1",
        test="VerifyAdvisory",
        categories=["advisories"],
        description="Verify an advisory.",
        advisory=advisory,
    )
    result._set_status(status, "Framework lifecycle message.")

    rows = tuple(iter_advisory_report_rows(result, advisory))

    assert len(rows) == 1
    assert rows[0].result is result
    assert rows[0].vulnerability_id is None


def test_validate_advisory_results_rejects_unset_atomics() -> None:
    """Reject unset states because dry-run never reaches advisory reporting."""
    result = _AdvisoryTestResult(
        name="leaf1",
        test="VerifyAdvisory",
        categories=["advisories"],
        description="Verify an advisory.",
        advisory=ADVISORY,
    )
    for vulnerability in ADVISORY.vulnerabilities:
        result.add(f"Verify {vulnerability.id}.", vulnerability_id=vulnerability.id)

    with pytest.raises(ValueError, match="do not accept unset"):
        validate_advisory_results([result])


def test_validate_advisory_results_rejects_evaluated_result_without_atomics() -> None:
    """Reject an evaluated advisory result without structured findings."""
    result = _AdvisoryTestResult(
        name="leaf1",
        test="VerifyAdvisory",
        categories=["advisories"],
        description="Verify an advisory.",
        result=AntaTestStatus.SUCCESS,
        advisory=ADVISORY,
    )

    with pytest.raises(ValueError, match="requires structured findings"):
        validate_advisory_results([result])


def test_validate_advisory_results_rejects_missing_finding_when_parent_is_error() -> None:
    """Reject an evaluated atomic without a finding even when a later error changes the parent status."""
    result = _AdvisoryTestResult(
        name="leaf1",
        test="VerifyAdvisory",
        categories=["advisories"],
        description="Verify an advisory.",
        advisory=ADVISORY,
    )
    result.add("Evaluated without a finding", AntaTestStatus.SUCCESS, vulnerability_id="CVE-2026-0001")
    result.is_error("Later framework error.")

    with pytest.raises(ValueError, match="structured finding on every atomic"):
        validate_advisory_results([result])


@pytest.mark.parametrize("status", [AntaTestStatus.SUCCESS, AntaTestStatus.FAILURE])
def test_validate_advisory_results_rejects_evaluated_state_without_findings(status: AntaTestStatus) -> None:
    """Require every completed advisory assessment to carry structured atomic findings."""
    result = _AdvisoryTestResult(
        name="leaf1",
        test="VerifyAdvisory",
        categories=["advisories"],
        description="Verify an advisory.",
        advisory=ADVISORY,
    )
    result.add("Evaluated without a finding", status, vulnerability_id="CVE-2026-0001")

    with pytest.raises(ValueError, match="structured finding on every atomic"):
        validate_advisory_results([result])


@pytest.mark.parametrize("status", [AntaTestStatus.SKIPPED, AntaTestStatus.ERROR])
def test_validate_advisory_results_rejects_lifecycle_atomics(status: AntaTestStatus) -> None:
    """Reserve atomic results for structured assessments instead of lifecycle expansion."""
    result = _AdvisoryTestResult(
        name="leaf1",
        test="VerifyAdvisory",
        categories=["advisories"],
        description="Verify an advisory.",
        advisory=ADVISORY,
    )
    result.add("Lifecycle atomic", status, ["Framework lifecycle message."], vulnerability_id="CVE-2026-0001")
    result._set_status(status)

    with pytest.raises(ValueError, match="structured finding on every atomic"):
        validate_advisory_results([result])


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
    _add_vulnerability_atomic(result, "CVE-2026-0001", AntaTestStatus.SUCCESS, "not affected")
    manager = ResultManager()
    manager.add(result)
    report = SecurityAdvisoryReport.from_result_manager(manager)

    overview = SecurityAdvisoryRunOverviewData.from_context(build_security_advisory_run_context(report))

    assert overview.anta_version == ADVISORY_ANTA_VERSION
    assert overview.test_execution_start_time == ADVISORY_RUN_START_TIME
    assert overview.test_execution_end_time == ADVISORY_RUN_END_TIME
    assert overview.security_advisories_assessed == 1
    assert overview.devices_assessed == 1
