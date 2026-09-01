# Copyright (c) 2026 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Unit tests for security advisory Rich table reporting."""

from __future__ import annotations

from typing import TYPE_CHECKING, cast

from anta._advisory.reporter.reporting import SecurityAdvisoryReport
from anta._advisory.reporter.table_reporter import SecurityAdvisoryReportTable
from anta._advisory.results import _AdvisoryTestResult
from anta.result_manager import ResultManager
from anta.result_manager.models import AntaTestStatus
from tests.units._advisory.conftest import ADVISORY
from tests.units._advisory.reporting_data import build_security_advisory_result_manager

if TYPE_CHECKING:
    from rich.table import Table
    from rich.text import Text


def _cells(table: Table, row_index: int) -> list[str]:
    """Return plain text for a Rich table row."""
    return [str(column._cells[row_index]) for column in table.columns]


def test_security_advisory_summary_order_and_counts() -> None:
    """Order summary rows by severity and expose advisory-facing counts."""
    report = SecurityAdvisoryReport.from_result_manager(build_security_advisory_result_manager())

    table = SecurityAdvisoryReportTable().generate_summary(report)

    assert table.row_count == 3
    assert [_cells(table, index)[0] for index in range(table.row_count)] == ["● Critical", "● High", "● Medium"]
    assert [str(cast("Text", table.columns[0]._cells[index]).spans[0].style) for index in range(table.row_count)] == ["red", "orange3", "yellow3"]
    assert _cells(table, 0)[2:] == ["8", "4", "0", "0", "2", "1", "1", "0"]
    assert _cells(table, 1)[2:] == ["8", "1", "0", "0", "5", "1", "1", "0"]
    assert _cells(table, 2)[2:] == ["8", "0", "2", "0", "4", "1", "1", "0"]
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

    assert _cells(table, 0)[2:] == ["2", "0", "0", "1", "0", "0", "0", "1"]


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

    tables = SecurityAdvisoryReportTable().generate_device_findings(SecurityAdvisoryReport.from_result_manager(manager))

    assert len(tables) == 1
    table = tables[0]
    assert table.row_count == 2
    assert "Device Findings — SA0001: Test advisory" in str(table.title)
    assert [str(column.header) for column in table.columns] == ["Device", "Result", "Findings", "Remediations"]
    assert _cells(table, 0) == [
        "leaf1",
        "Affected",
        "The device is affected.",
        "• Upgrade EOS.\n• Apply the configuration workaround.",
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
        remediations=["Apply the advisory remediation.", "Disable the service."],
    )
    result.add("External condition", AntaTestStatus.INCONCLUSIVE, ["External evidence is unavailable."], remediations=["Collect external evidence."])
    manager = ResultManager()
    manager.add(result)

    tables = SecurityAdvisoryReportTable().generate_device_findings(SecurityAdvisoryReport.from_result_manager(manager), expand_results=True)

    assert len(tables) == 1
    table = tables[0]
    assert table.row_count == 3
    assert [row.end_section for row in table.rows] == [False, False, True]
    assert [str(column.header) for column in table.columns] == [
        "Device",
        "Vulnerability ID(s)",
        "Result",
        "Findings",
        "Remediations",
    ]
    assert _cells(table, 0) == [
        "leaf1",
        "—",
        "Affected",
        (
            "Detailed findings: 1/2 checks affected; 1/2 checks inconclusive\n"
            "Overall evidence:\n"
            "Overall exposure detected.\n"
            "CVE-2026-0001: The service is exposed.\n"
            "External condition - External evidence is unavailable."
        ),
        "• CVE-2026-0001: Apply the advisory remediation.\n• CVE-2026-0001: Disable the service.\n• Collect external evidence.",
    ]
    assert _cells(table, 1) == [
        "  ├──",
        "● CVE-2026-0001",
        "Affected",
        "The service is exposed.",
        "• Apply the advisory remediation.\n• Disable the service.",
    ]
    assert str(cast("Text", table.columns[1]._cells[1]).spans[0].style) == "yellow3"
    assert _cells(table, 2) == ["  └──", "—", "Inconclusive", "External evidence is unavailable.", "• Collect external evidence."]


def test_security_advisory_device_findings_use_consistent_layout() -> None:
    """Use the same full-width column layout for every advisory table."""
    report = SecurityAdvisoryReport.from_result_manager(build_security_advisory_result_manager())

    tables = SecurityAdvisoryReportTable().generate_device_findings(report, expand_results=True)

    assert len(tables) == 3
    assert all(table.expand for table in tables)
    layouts = [[(column.width, column.ratio) for column in table.columns] for table in tables]
    assert layouts == [[(18, None), (24, None), (12, None), (None, 3), (None, 2)]] * 3
