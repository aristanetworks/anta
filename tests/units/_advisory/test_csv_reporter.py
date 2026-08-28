# Copyright (c) 2026 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Unit tests for security advisory CSV reporting."""

from __future__ import annotations

import csv
from pathlib import Path
from unittest.mock import patch

import pytest

from anta._advisory.reporter.csv_reporter import SecurityAdvisoryReportCsv
from anta._advisory.reporter.reporting import SecurityAdvisoryReport, generate_security_advisory_csv_report
from anta._advisory.results import _AdvisoryTestResult
from anta.result_manager import ResultManager
from anta.result_manager.models import AntaTestStatus
from tests.units._advisory.conftest import ADVISORY
from tests.units._advisory.reporting_data import build_security_advisory_result_manager

EXPECTED_HEADERS = [
    "Device",
    "Test Name",
    "Advisory Result",
    "Advisory Result Messages",
    "CVE Result",
    "CVE Description",
    "CVE Result Messages",
    "CVE Remediation",
    "Remediation",
    "Advisory ID",
    "Advisory Title",
    "Advisory Severity",
    "Advisory URL",
    "Advisory Description",
    "CVE ID",
    "CVE Severity",
]


def test_security_advisory_csv_report(tmp_path: Path) -> None:
    """Verify the CSV report renders the same realistic dataset as Markdown."""
    report = SecurityAdvisoryReport.from_result_manager(build_security_advisory_result_manager())
    output = tmp_path / "advisories.csv"

    generate_security_advisory_csv_report(report, output)

    expected = (Path(__file__).parents[2] / "data" / "test_security_advisory_csv_report.csv").read_text(encoding="utf-8")
    assert output.read_text(encoding="utf-8") == expected


def test_security_advisory_csv_headers() -> None:
    """Verify the security advisory CSV uses the documented column order."""
    assert SecurityAdvisoryReportCsv._advisory_headers() == EXPECTED_HEADERS
    assert all("JSON" not in header for header in EXPECTED_HEADERS)


@pytest.mark.parametrize(
    ("status", "messages", "expected"),
    [
        pytest.param(AntaTestStatus.SUCCESS, ["The device is not affected because the fixed release is installed."], "not affected", id="not-affected"),
        pytest.param(
            AntaTestStatus.SUCCESS,
            ["CVE-2026-0001 - The device is affected but mitigated because the vulnerable service is disabled."],
            "mitigated",
            id="mitigated",
        ),
        pytest.param(AntaTestStatus.INCONCLUSIVE, [], "inconclusive", id="inconclusive"),
        pytest.param(AntaTestStatus.FAILURE, [], "affected", id="affected"),
        pytest.param(AntaTestStatus.ERROR, [], "error", id="error"),
        pytest.param(AntaTestStatus.SKIPPED, [], "skipped", id="skipped"),
        pytest.param(AntaTestStatus.UNSET, [], "unset", id="unset"),
    ],
)
def test_security_advisory_csv_result_wording(status: AntaTestStatus, messages: list[str], expected: str) -> None:
    """Verify ANTA statuses use advisory-facing result wording."""
    result = _AdvisoryTestResult(
        name="leaf1",
        test="VerifyAdvisory",
        categories=["advisories"],
        description="Test advisory metadata.",
        result=status,
        messages=messages,
        advisory=ADVISORY,
    )

    assert SecurityAdvisoryReportCsv._format_result(result) == expected


def test_security_advisory_csv_detailed_and_fallback_rows() -> None:
    """Verify detailed CVE findings, parent fallback, duplicate findings, and a non-CVE finding remain distinct."""
    result = _AdvisoryTestResult(
        name="leaf1",
        test="VerifyAdvisory",
        categories=["advisories"],
        description="Test advisory (CVE-2026-0001, CVE-2026-0002): issue details at https://example.com/advisory.",
        result=AntaTestStatus.FAILURE,
        messages=["The device is affected because parent evidence proves exposure.", "Additional parent evidence."],
        advisory=ADVISORY,
    )
    result.add(
        "CVE-2026-0001 vulnerable service",
        AntaTestStatus.SUCCESS,
        ["The device is not affected because the service is disabled."],
        cve_ids=("CVE-2026-0001",),
    )
    result.add(
        "CVE-2026-0001 external condition",
        AntaTestStatus.INCONCLUSIVE,
        ["The assessment is inconclusive and the device may be affected because external evidence is unavailable."],
        cve_ids=("CVE-2026-0001",),
    )
    result.add("Non-CVE issue", AntaTestStatus.FAILURE, ["The device is affected because a non-CVE issue is present."])

    rows = [dict(zip(SecurityAdvisoryReportCsv._advisory_headers(), row, strict=True)) for row in SecurityAdvisoryReportCsv._iter_result_rows(result, ADVISORY)]

    assert [row["CVE ID"] for row in rows] == ["CVE-2026-0001", "CVE-2026-0001", "CVE-2026-0002", ""]
    assert [row["CVE Result"] for row in rows] == ["not affected", "inconclusive", "affected", "affected"]
    assert [row["CVE Description"] for row in rows] == [
        "CVE-2026-0001 vulnerable service",
        "CVE-2026-0001 external condition",
        result.description,
        "Non-CVE issue",
    ]
    assert {row["Advisory Result"] for row in rows} == {"affected"}
    assert {row["Advisory Result Messages"] for row in rows} == {"\n".join(result.messages)}
    assert rows[0]["CVE Result Messages"] == "The device is not affected because the service is disabled."
    assert rows[2]["CVE Result Messages"] == "\n".join(result.messages)
    assert rows[3]["CVE Result Messages"] == "The device is affected because a non-CVE issue is present."
    assert {row["Advisory Severity"] for row in rows} == {"high"}
    assert {row["CVE Remediation"] for row in rows} == {""}
    assert {row["Remediation"] for row in rows} == {""}


def test_security_advisory_csv_multiline_messages(tmp_path: Path) -> None:
    """Verify message lists are flattened with real newlines and remain valid CSV cells."""
    advisory = ADVISORY.model_copy(update={"cves": ()})
    result = _AdvisoryTestResult(
        name="leaf1",
        test="VerifyAdvisory",
        categories=["advisories"],
        description="Test advisory metadata.",
        result=AntaTestStatus.FAILURE,
        messages=["First conclusion line.", "Second conclusion line."],
        advisory=advisory,
    )
    manager = ResultManager()
    manager.add(result)
    output = tmp_path / "advisories.csv"

    generate_security_advisory_csv_report(SecurityAdvisoryReport.from_result_manager(manager), output)

    with output.open(encoding="utf-8", newline="") as csv_file:
        row = next(csv.DictReader(csv_file))
    expected_messages = "First conclusion line.\nSecond conclusion line."
    assert row["Advisory Result Messages"] == expected_messages
    assert row["CVE Result Messages"] == expected_messages


def test_security_advisory_csv_result_associated_with_multiple_cves() -> None:
    """Verify one detailed issue result associated with multiple CVEs is repeated once per CVE."""
    result = _AdvisoryTestResult(
        name="leaf1",
        test="VerifyAdvisory",
        categories=["advisories"],
        description="Static advisory test metadata.",
        advisory=ADVISORY,
    )
    result.add(
        "Shared issue",
        AntaTestStatus.FAILURE,
        ["The device is affected because shared evidence proves exposure."],
        cve_ids=("CVE-2026-0001", "CVE-2026-0002"),
    )

    rows = [dict(zip(SecurityAdvisoryReportCsv._advisory_headers(), row, strict=True)) for row in SecurityAdvisoryReportCsv._iter_result_rows(result, ADVISORY)]

    assert [row["CVE ID"] for row in rows] == ["CVE-2026-0001", "CVE-2026-0002"]
    assert [row["CVE Description"] for row in rows] == ["Shared issue", "Shared issue"]
    assert [row["CVE Result Messages"] for row in rows] == [
        "The device is affected because shared evidence proves exposure.",
        "The device is affected because shared evidence proves exposure.",
    ]


@pytest.mark.parametrize("with_details", [False, True])
def test_security_advisory_csv_without_cves(*, with_details: bool) -> None:
    """Verify advisories without CVEs emit either one parent row or their detailed non-CVE rows."""
    advisory = ADVISORY.model_copy(update={"cves": ()})
    result = _AdvisoryTestResult(
        name="leaf1",
        test="VerifyAdvisory",
        categories=["advisories"],
        description="Static advisory test metadata.",
        result=AntaTestStatus.SUCCESS,
        messages=["The device is not affected because no issue applies."],
        advisory=advisory,
    )
    if with_details:
        result.add("First issue", AntaTestStatus.SUCCESS, ["The device is not affected because the issue does not apply."])
        result.add("Second issue", AntaTestStatus.FAILURE, ["The device is affected because the issue applies."])

    rows = [dict(zip(SecurityAdvisoryReportCsv._advisory_headers(), row, strict=True)) for row in SecurityAdvisoryReportCsv._iter_result_rows(result, advisory)]

    assert len(rows) == (2 if with_details else 1)
    assert {row["CVE ID"] for row in rows} == {""}
    assert {row["CVE Severity"] for row in rows} == {""}
    assert {row["Advisory Severity"] for row in rows} == {"unknown"}
    assert [row["CVE Result"] for row in rows] == (["not affected", "affected"] if with_details else ["not affected"])
    assert [row["CVE Description"] for row in rows] == (["First issue", "Second issue"] if with_details else ["Static advisory test metadata."])


def test_security_advisory_csv_report_os_error(tmp_path: Path) -> None:
    """Verify CSV filesystem errors are propagated."""
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

    with patch("pathlib.Path.open", side_effect=OSError("write failed")), pytest.raises(OSError, match="write failed"):
        generate_security_advisory_csv_report(report, tmp_path / "advisories.csv")
