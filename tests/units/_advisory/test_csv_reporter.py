# Copyright (c) 2026 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Unit tests for security advisory CSV reporting."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

import pytest

from anta._advisory.models import AdvisoryMitigation
from anta._advisory.reporter.csv_reporter import SecurityAdvisoryReportCsv
from anta._advisory.reporter.reporting import SecurityAdvisoryReport, generate_security_advisory_csv_report
from anta._advisory.results import _AdvisoryTestResult
from anta.result_manager import ResultManager
from anta.result_manager.models import AntaTestStatus
from tests.units._advisory.conftest import ADVISORY
from tests.units._advisory.reporting_data import build_security_advisory_result_manager


def test_security_advisory_csv_report(tmp_path: Path) -> None:
    """Verify the CSV report renders the same realistic dataset as Markdown."""
    report = SecurityAdvisoryReport.from_result_manager(build_security_advisory_result_manager())
    output = tmp_path / "advisories.csv"

    generate_security_advisory_csv_report(report, output)

    expected = (Path(__file__).parents[2] / "data" / "test_security_advisory_csv_report.csv").read_text(encoding="utf-8")
    assert output.read_text(encoding="utf-8").splitlines() == expected.splitlines()


def test_security_advisory_csv_action_without_url() -> None:
    """Verify advisory guidance is emitted as structured JSON, including a null URL."""
    action = AdvisoryMitigation(name="Restrict access", details="Limit access to trusted operators.")

    assert json.loads(SecurityAdvisoryReportCsv._format_actions((action,))) == [
        {"name": "Restrict access", "details": "Limit access to trusted operators.", "url": None}
    ]


def test_security_advisory_csv_detailed_and_fallback_rows() -> None:
    """Verify detailed CVE findings, parent fallback, duplicate findings, and a non-CVE finding remain distinct."""
    result = _AdvisoryTestResult(
        name="leaf1",
        test="VerifyAdvisory",
        categories=["advisories"],
        description="Static advisory test metadata.",
        result=AntaTestStatus.SUCCESS,
        messages=["Parent assessment."],
        advisory=ADVISORY,
    )
    result.add("First issue", AntaTestStatus.SUCCESS, ["First CVE-specific conclusion."], cve_ids=("CVE-2026-0001",))
    result.add("Independent issue", AntaTestStatus.INCONCLUSIVE, ["Second CVE-specific conclusion."], cve_ids=("CVE-2026-0001",))
    result.add("Non-CVE issue", AntaTestStatus.FAILURE, ["Non-CVE conclusion."])

    rows = [dict(zip(SecurityAdvisoryReportCsv._advisory_headers(), row, strict=True)) for row in SecurityAdvisoryReportCsv._iter_result_rows(result, ADVISORY)]

    assert [row["CVE ID"] for row in rows] == ["CVE-2026-0001", "CVE-2026-0001", "CVE-2026-0002", ""]
    assert [row["Result"] for row in rows] == ["success", "inconclusive", "failure", "failure"]
    assert [row["Result Description"] for row in rows] == ["First issue", "Independent issue", "Static advisory test metadata.", "Non-CVE issue"]
    assert {row["Advisory Result"] for row in rows} == {"failure"}
    assert {row["Description"] for row in rows} == {"Static advisory test metadata."}
    assert {row["Advisory ID"] for row in rows} == {"SA0001"}
    assert json.loads(rows[0]["Result Message(s) JSON"]) == ["First CVE-specific conclusion."]
    assert json.loads(rows[0]["CVSS Scores JSON"]) == [
        {"version": "3.1", "score": 6.5, "vector": "CVSS:3.1/TEST"},
        {"version": "4.0", "score": 7.0, "vector": "CVSS:4.0/TEST"},
    ]
    assert json.loads(rows[2]["Result Message(s) JSON"]) == result.messages
    assert json.loads(rows[2]["CVSS Scores JSON"]) == []
    assert json.loads(rows[3]["Result Message(s) JSON"]) == ["Non-CVE conclusion."]
    assert json.loads(rows[3]["CVSS Scores JSON"]) == []


def test_security_advisory_csv_result_associated_with_multiple_cves() -> None:
    """Verify one detailed issue result associated with multiple CVEs is repeated once per CVE."""
    result = _AdvisoryTestResult(
        name="leaf1",
        test="VerifyAdvisory",
        categories=["advisories"],
        description="Static advisory test metadata.",
        advisory=ADVISORY,
    )
    result.add("Shared issue", AntaTestStatus.FAILURE, ["Shared issue conclusion."], cve_ids=("CVE-2026-0001", "CVE-2026-0002"))

    rows = [dict(zip(SecurityAdvisoryReportCsv._advisory_headers(), row, strict=True)) for row in SecurityAdvisoryReportCsv._iter_result_rows(result, ADVISORY)]

    assert [row["CVE ID"] for row in rows] == ["CVE-2026-0001", "CVE-2026-0002"]
    assert [row["Result Description"] for row in rows] == ["Shared issue", "Shared issue"]
    assert [json.loads(row["Result Message(s) JSON"]) for row in rows] == [["Shared issue conclusion."], ["Shared issue conclusion."]]


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
        messages=["Parent conclusion."],
        advisory=advisory,
    )
    if with_details:
        result.add("First issue", AntaTestStatus.SUCCESS, ["First conclusion."])
        result.add("Second issue", AntaTestStatus.FAILURE, ["Second conclusion."])

    rows = [dict(zip(SecurityAdvisoryReportCsv._advisory_headers(), row, strict=True)) for row in SecurityAdvisoryReportCsv._iter_result_rows(result, advisory)]

    assert len(rows) == (2 if with_details else 1)
    assert {row["CVE ID"] for row in rows} == {""}
    assert {row["CVE Severity"] for row in rows} == {""}
    assert all(json.loads(row["CVSS Scores JSON"]) == [] for row in rows)
    assert [row["Result"] for row in rows] == (["success", "failure"] if with_details else ["success"])
    assert [row["Result Description"] for row in rows] == (["First issue", "Second issue"] if with_details else ["Static advisory test metadata."])


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
