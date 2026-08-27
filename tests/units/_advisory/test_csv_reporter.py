# Copyright (c) 2026 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Unit tests for security advisory CSV reporting."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest

from anta._advisory.models import AdvisoryMitigation
from anta._advisory.reporter.csv_reporter import SecurityAdvisoryReportCsv
from anta._advisory.reporter.reporting import SecurityAdvisoryReport, generate_security_advisory_csv_report
from anta._advisory.results import _AdvisoryTestResult
from anta.result_manager import ResultManager
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
    """Verify advisory guidance without a URL is formatted cleanly."""
    action = AdvisoryMitigation(name="Restrict access", details="Limit access to trusted operators.")

    assert SecurityAdvisoryReportCsv._format_actions((action,)) == "Restrict access: Limit access to trusted operators."


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
