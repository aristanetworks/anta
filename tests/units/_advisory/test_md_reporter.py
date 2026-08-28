# Copyright (c) 2026 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Unit tests for security advisory Markdown reporting."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest

from anta._advisory.reporter.md_reporter import SecurityAdvisoryDetails
from anta._advisory.reporter.reporting import SecurityAdvisoryReport, generate_security_advisory_md_report
from anta._advisory.results import _AdvisoryTestResult
from anta.result_manager import ResultManager
from anta.result_manager.models import AntaTestStatus
from tests.units._advisory.conftest import ADVISORY
from tests.units._advisory.reporting_data import build_security_advisory_result, build_security_advisory_result_manager


def _build_atomic_result_manager() -> ResultManager:
    """Build one AR003/AR004-compliant advisory result with varied issue associations."""
    result = _AdvisoryTestResult(
        name="leaf1",
        test="VerifySA1",
        categories=["advisories"],
        description=("Test advisory (CVE-2026-0001, CVE-2026-0002): Verify exposure to the issues described at https://example.com/advisory."),
        advisory=ADVISORY,
    )
    result.add(
        "CVE-2026-0001 vulnerable service",
        AntaTestStatus.FAILURE,
        ["The device is affected because EOS 4.31.1F enables the vulnerable service."],
        cve_ids=("CVE-2026-0001",),
    )
    result.add(
        "CVE-2026-0001 and CVE-2026-0002 platform applicability",
        AntaTestStatus.SUCCESS,
        ["The device is not affected because platform DCS-7050SX3 is outside the affected family."],
        cve_ids=("CVE-2026-0001", "CVE-2026-0002"),
    )
    result.add(
        "External trust condition",
        AntaTestStatus.INCONCLUSIVE,
        ["The assessment is inconclusive and the device may be affected because external trust configuration could not be verified."],
    )
    result.result = AntaTestStatus.FAILURE
    manager = ResultManager()
    manager.add(result)
    return manager


def test_security_advisory_markdown_report(tmp_path: Path) -> None:
    """Verify a realistic fleet report is clean, grouped, and deterministic."""
    report = SecurityAdvisoryReport.from_result_manager(build_security_advisory_result_manager())
    output = tmp_path / "advisories.md"

    generate_security_advisory_md_report(report, output)

    expected = (Path(__file__).parents[2] / "data" / "test_security_advisory_md_report.md").read_text(encoding="utf-8")
    assert output.read_text(encoding="utf-8") == expected


def test_security_advisory_markdown_report_expanded(tmp_path: Path) -> None:
    """Verify expanded Markdown renders real issue assessments using the regular ANTA parent/child layout."""
    report = SecurityAdvisoryReport.from_result_manager(_build_atomic_result_manager())
    output = tmp_path / "advisories.md"

    generate_security_advisory_md_report(report, output, expand_results=True)

    expected = (Path(__file__).parents[2] / "data" / "test_security_advisory_md_report_expanded.md").read_text(encoding="utf-8")
    assert output.read_text(encoding="utf-8") == expected


def test_security_advisory_markdown_report_flattened_atomic_results(tmp_path: Path) -> None:
    """Verify default output retains issue attribution without exposing child rows."""
    report = SecurityAdvisoryReport.from_result_manager(_build_atomic_result_manager())
    output = tmp_path / "advisories.md"

    generate_security_advisory_md_report(report, output)

    content = output.read_text(encoding="utf-8")
    assert "| Device | Test | Result | Messages |" in content
    assert "CVE-2026-0001 vulnerable service - The device is affected because EOS 4.31.1F enables the vulnerable service." in content
    assert "CVE-2026-0001 and CVE-2026-0002 platform applicability - The device is not affected because" in content
    assert "├──" not in content
    assert "└──" not in content


def test_security_advisory_markdown_report_expanded_without_atomic_results(tmp_path: Path) -> None:
    """Verify expanded mode keeps a normal parent row when no detailed issue assessment exists."""
    manager = ResultManager()
    manager.add(build_security_advisory_result("leaf1", AntaTestStatus.SUCCESS, "The device is not affected because EOS 4.40.1F contains the fix.", ADVISORY))
    report = SecurityAdvisoryReport.from_result_manager(manager)
    output = tmp_path / "advisories.md"

    generate_security_advisory_md_report(report, output, expand_results=True)

    content = output.read_text(encoding="utf-8")
    assert "| Device | Test | Description | CVE(s) | Result | Messages |" in content
    assert (
        "| leaf1 | VerifySA1 | Verify that the device is not exposed to Arista Security Advisory 0001. | - | ✅&nbsp;Success "
        "| The device is not affected because EOS 4.40.1F contains the fix. |"
    ) in content
    assert "├──" not in content
    assert "└──" not in content


def test_security_advisory_markdown_report_expanded_preserves_parent_messages(tmp_path: Path) -> None:
    """Verify expansion renders every parent message alongside the detailed summary."""
    result = _AdvisoryTestResult(
        name="leaf1",
        test="VerifySA1",
        categories=["advisories"],
        description="Test advisory (CVE-2026-0001): Verify exposure described at https://example.com/advisory.",
        result=AntaTestStatus.FAILURE,
        messages=["The device is affected because parent-specific evidence proves exposure."],
        advisory=ADVISORY,
    )
    result.add(
        "CVE-2026-0001 platform applicability",
        AntaTestStatus.SUCCESS,
        ["The device is not affected because this individual platform check passed."],
        cve_ids=("CVE-2026-0001",),
    )
    manager = ResultManager()
    manager.add(result)
    report = SecurityAdvisoryReport.from_result_manager(manager)
    output = tmp_path / "advisories.md"

    generate_security_advisory_md_report(report, output, expand_results=True)

    content = output.read_text(encoding="utf-8")
    assert "**Detailed findings:** All&nbsp;1&nbsp;checks&nbsp;passed" in content
    assert "**Overall evidence:** The device is affected because parent-specific evidence proves exposure." in content
    assert "CVE-2026-0001 platform applicability - The device is not affected because this individual platform check passed." in content
    assert "The device is not affected because this individual platform check passed." in content


def test_security_advisory_markdown_report_os_error(tmp_path: Path) -> None:
    """Verify Markdown filesystem errors are propagated."""
    manager = ResultManager()
    manager.add(build_security_advisory_result("leaf1", AntaTestStatus.SUCCESS, "No exposure detected.", ADVISORY))
    report = SecurityAdvisoryReport.from_result_manager(manager)

    with patch("pathlib.Path.open", side_effect=OSError("write failed")), pytest.raises(OSError, match="write failed"):
        generate_security_advisory_md_report(report, tmp_path / "advisories.md")


def test_security_advisory_markdown_summary_includes_inconclusive_but_not_unset(tmp_path: Path) -> None:
    """Verify the summary represents terminal inconclusive results without exposing non-terminal unset state."""
    manager = ResultManager()
    manager.add(
        build_security_advisory_result(
            "leaf1",
            AntaTestStatus.INCONCLUSIVE,
            "The assessment is inconclusive and the device may be affected because required evidence is unavailable.",
            ADVISORY,
        )
    )
    report = SecurityAdvisoryReport.from_result_manager(manager)
    output = tmp_path / "advisories.md"

    generate_security_advisory_md_report(report, output)

    content = output.read_text(encoding="utf-8")
    assert "| Security Advisory | Severity | Devices | ✅&nbsp;Success | ❓&nbsp;Inconclusive | ❌&nbsp;Failure | ❗&nbsp;Error | ⏭️&nbsp;Skipped |" in content
    assert "| [SA0001: Test advisory](#sa-0001) | 🟠&nbsp;High | 1 | 0 | 1 | 0 | 0 | 0 |" in content
    assert "Unset" not in content


@pytest.mark.parametrize(
    ("statuses", "expected"),
    [
        pytest.param([AntaTestStatus.SUCCESS, AntaTestStatus.SUCCESS], "All&nbsp;2&nbsp;checks&nbsp;passed", id="all-passed"),
        pytest.param([AntaTestStatus.SUCCESS, AntaTestStatus.FAILURE], "1/2&nbsp;checks&nbsp;failed", id="failure"),
        pytest.param([AntaTestStatus.SUCCESS, AntaTestStatus.INCONCLUSIVE], "1/2&nbsp;checks&nbsp;inconclusive", id="inconclusive"),
        pytest.param(
            [AntaTestStatus.FAILURE, AntaTestStatus.INCONCLUSIVE],
            "1/2&nbsp;checks&nbsp;failed; 1/2&nbsp;checks&nbsp;inconclusive",
            id="failure-and-inconclusive",
        ),
    ],
)
def test_security_advisory_markdown_atomic_summary(statuses: list[AntaTestStatus], expected: str) -> None:
    """Verify expanded parent summaries match the regular ANTA Markdown convention."""
    result = _AdvisoryTestResult(
        name="leaf1",
        test="VerifySA1",
        categories=["advisories"],
        description="Test advisory metadata.",
        advisory=ADVISORY,
    )
    for index, status in enumerate(statuses):
        result.add(f"Issue {index}", status)

    assert SecurityAdvisoryDetails._atomic_summary(result) == expected


def test_security_advisory_report_rejects_conflicting_metadata() -> None:
    """Verify one advisory number cannot be rendered with conflicting metadata."""
    manager = ResultManager()
    manager.add(build_security_advisory_result("leaf1", AntaTestStatus.SUCCESS, "No exposure detected.", ADVISORY))
    manager.add(
        build_security_advisory_result(
            "leaf2",
            AntaTestStatus.FAILURE,
            "Exposure detected.",
            advisory=ADVISORY.model_copy(update={"title": "Conflicting title"}),
        )
    )

    with pytest.raises(ValueError, match="Conflicting metadata"):
        SecurityAdvisoryReport.from_result_manager(manager)


def test_security_advisory_markdown_without_cves(tmp_path: Path) -> None:
    """Verify an advisory without CVEs uses unknown severity and renders no removed metadata."""
    advisory = ADVISORY.model_copy(update={"sa_number": "0002", "cves": ()})
    manager = ResultManager()
    manager.add(build_security_advisory_result("leaf1", AntaTestStatus.SUCCESS, "No exposure detected.", advisory))
    report = SecurityAdvisoryReport.from_result_manager(manager)
    output = tmp_path / "advisories.md"

    generate_security_advisory_md_report(report, output)

    content = output.read_text(encoding="utf-8")
    assert "[SA0002: Test advisory](#sa-0002) | ⚪&nbsp;Unknown" in content
    assert "⚪ **Severity:** Unknown" in content
    assert "| CVE | Severity |" in content
    assert "CVSS" not in content
    assert "Mitigations" not in content
    assert "Resolutions" not in content
