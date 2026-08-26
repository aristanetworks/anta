# Copyright (c) 2026 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Unit tests for security advisory CSV reporting."""

from __future__ import annotations

import csv
from typing import TYPE_CHECKING
from unittest.mock import patch

import pytest

from anta._advisory.csv_reporter import SecurityAdvisoryReportCsv
from anta._advisory.models import AdvisoryMitigation
from anta.result_manager import ResultManager
from anta.result_manager.models import AntaTestStatus
from anta.result_manager.models import TestResult as AntaTestResult
from anta.result_manager.models import TestResultMetadata as AntaTestResultMetadata
from tests.units._advisory.conftest import ADVISORY

if TYPE_CHECKING:
    from pathlib import Path


def test_security_advisory_csv_report(tmp_path: Path) -> None:
    """Verify the specialized CSV report includes complete flattened metadata."""
    result = AntaTestResult(
        name="leaf1",
        test="VerifyAdvisory",
        categories=["advisories"],
        description="Verify an advisory.",
        result=AntaTestStatus.FAILURE,
        messages=["Exposure detected."],
        metadata=AntaTestResultMetadata(security_advisory=ADVISORY),
    )
    manager = ResultManager()
    manager.add(result)
    output = tmp_path / "advisories.csv"

    SecurityAdvisoryReportCsv.generate(manager, output)

    with output.open(encoding="utf-8", newline="") as csvfile:
        rows = list(csv.reader(csvfile))

    assert rows[0] == [
        "Device",
        "Test Name",
        "Test Status",
        "Message(s)",
        "Test description",
        "Test category",
        "SA Number",
        "SA Title",
        "SA Severity",
        "CVE(s)",
        "CVSS Score(s)",
        "Advisory URL",
        "Advisory Description",
        "Mitigation(s)",
        "Resolution(s)",
    ]
    assert rows[1] == [
        "leaf1",
        "VerifyAdvisory",
        "failure",
        "Exposure detected.",
        "Verify an advisory.",
        "Advisories",
        "0001",
        "Test advisory",
        "high",
        "CVE-2026-0001 (medium)",
        "CVE-2026-0001: CVSS 3.1: 6.5 (CVSS:3.1/TEST) - CVE-2026-0001: CVSS 4.0: 7 (CVSS:4.0/TEST)",
        "https://example.com/advisory",
        "Test advisory description.",
        "Workaround: Apply the temporary workaround. (https://example.com/mitigation)",
        "Upgrade: Upgrade to a fixed release. (https://example.com/resolution)",
    ]


def test_security_advisory_csv_action_without_url() -> None:
    """Verify advisory guidance without a URL is formatted cleanly."""
    action = AdvisoryMitigation(name="Restrict access", details="Limit access to trusted operators.")

    assert SecurityAdvisoryReportCsv._format_actions((action,)) == "Restrict access: Limit access to trusted operators."


def test_security_advisory_csv_report_os_error(tmp_path: Path) -> None:
    """Verify CSV filesystem errors are propagated."""
    result = AntaTestResult(
        name="leaf1",
        test="VerifyAdvisory",
        categories=["advisories"],
        description="Verify an advisory.",
        metadata=AntaTestResultMetadata(security_advisory=ADVISORY),
    )
    manager = ResultManager()
    manager.add(result)

    with patch("pathlib.Path.open", side_effect=OSError("write failed")), pytest.raises(OSError, match="write failed"):
        SecurityAdvisoryReportCsv.generate(manager, tmp_path / "advisories.csv")
