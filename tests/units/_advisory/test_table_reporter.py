# Copyright (c) 2026 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Unit tests for security advisory Rich table reporting."""

from __future__ import annotations

from typing import TYPE_CHECKING

from anta._advisory.reporter.reporting import SecurityAdvisoryReport
from anta._advisory.reporter.table_reporter import SecurityAdvisoryReportTable
from anta._advisory.results import _AdvisoryTestResult
from anta.result_manager import ResultManager
from anta.result_manager.models import AntaTestStatus
from tests.units._advisory.conftest import ADVISORY
from tests.units._advisory.reporting_data import build_security_advisory_result_manager

if TYPE_CHECKING:
    from rich.table import Table


def _cells(table: Table, row_index: int) -> list[str]:
    """Return plain text for a Rich table row."""
    return [str(column._cells[row_index]) for column in table.columns]


def test_security_advisory_summary_order_and_counts() -> None:
    """Order summary rows by severity and expose advisory-facing counts."""
    report = SecurityAdvisoryReport.from_result_manager(build_security_advisory_result_manager())

    table = SecurityAdvisoryReportTable().generate_summary(report)

    assert table.row_count == 3
    assert [_cells(table, index)[0] for index in range(table.row_count)] == ["🔴 Critical", "🟠 High", "🟡 Medium"]
    assert _cells(table, 0)[2:] == ["8", "4", "0", "2", "0", "1", "1", "0"]
    assert _cells(table, 1)[2:] == ["8", "1", "0", "5", "0", "1", "1", "0"]
    assert _cells(table, 2)[2:] == ["8", "2", "0", "4", "0", "1", "1", "0"]
    assert "SA0120: Example Management API Authentication Bypass" in _cells(table, 0)[1]
    assert "https://www.arista.com/en/support/advisories-notices/security-advisory/example-0120" in _cells(table, 0)[1]


def test_security_advisory_summary_mitigated_and_unset() -> None:
    """Represent mitigated and unset results without losing either state."""
    manager = ResultManager()
    manager.add(
        _AdvisoryTestResult(
            name="leaf1",
            test="VerifySA1",
            categories=["advisories"],
            description="Test advisory.",
            result=AntaTestStatus.SUCCESS,
            messages=["The device is affected but mitigated because the vulnerable service is disabled."],
            advisory=ADVISORY,
        )
    )
    manager.add(
        _AdvisoryTestResult(
            name="leaf2",
            test="VerifySA1",
            categories=["advisories"],
            description="Test advisory.",
            result=AntaTestStatus.UNSET,
            advisory=ADVISORY,
        )
    )

    table = SecurityAdvisoryReportTable().generate_summary(SecurityAdvisoryReport.from_result_manager(manager))

    assert _cells(table, 0)[2:] == ["2", "0", "1", "0", "0", "0", "0", "1"]


def test_security_advisory_device_findings_remediation_and_order() -> None:
    """Show actual remediation text and order urgent results first."""
    manager = ResultManager()
    manager.add(
        _AdvisoryTestResult(
            name="leaf2",
            test="VerifySA1",
            categories=["advisories"],
            description="Test advisory.",
            result=AntaTestStatus.SUCCESS,
            messages=["The device is not affected."],
            advisory=ADVISORY,
        )
    )
    manager.add(
        _AdvisoryTestResult(
            name="leaf1",
            test="VerifySA1",
            categories=["advisories"],
            description="Test advisory.",
            result=AntaTestStatus.FAILURE,
            messages=["The device is affected."],
            advisory=ADVISORY,
            remediations=["Upgrade EOS.", "Apply the configuration workaround."],
        )
    )

    table = SecurityAdvisoryReportTable().generate_device_findings(SecurityAdvisoryReport.from_result_manager(manager))

    assert table.row_count == 2
    assert _cells(table, 0) == [
        "🟠 High",
        "SA0001",
        "leaf1",
        "Affected",
        "The device is affected.",
        "Upgrade EOS.\nApply the configuration workaround.",
    ]
    assert _cells(table, 1)[-1] == "—"


def test_security_advisory_expanded_atomic_findings() -> None:
    """Render atomic evidence, associations, and remediation beneath the parent."""
    result = _AdvisoryTestResult(
        name="leaf1",
        test="VerifySA1",
        categories=["advisories"],
        description="Test advisory.",
        result=AntaTestStatus.FAILURE,
        messages=["Overall exposure detected."],
        advisory=ADVISORY,
        remediations=["Apply the advisory remediation."],
    )
    result.add(
        "Vulnerable service",
        AntaTestStatus.FAILURE,
        ["The service is exposed."],
        vulnerability_ids=("CVE-2026-0001",),
        remediations=["Disable the service."],
    )
    result.add("External condition", AntaTestStatus.INCONCLUSIVE, ["External evidence is unavailable."], remediations=["Collect external evidence."])
    manager = ResultManager()
    manager.add(result)

    table = SecurityAdvisoryReportTable().generate_device_findings(SecurityAdvisoryReport.from_result_manager(manager), expand_results=True)

    assert table.row_count == 3
    assert _cells(table, 0)[3:] == [
        "Overall advisory",
        "—",
        "Affected",
        "Overall exposure detected.\nVulnerable service - The service is exposed.\nExternal condition - External evidence is unavailable.",
        "Apply the advisory remediation.",
    ]
    assert _cells(table, 1)[3:] == ["├── Vulnerable service", "CVE-2026-0001", "Affected", "The service is exposed.", "Disable the service."]
    assert _cells(table, 2)[3:] == ["└── External condition", "—", "Inconclusive", "External evidence is unavailable.", "Collect external evidence."]
