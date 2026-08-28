# Copyright (c) 2026 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Unit tests for security advisory Markdown reporting."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest

from anta._advisory.models import _AdvisoryVulnerability
from anta._advisory.reporter.md_reporter import SecurityAdvisoryDetails
from anta._advisory.reporter.reporting import SecurityAdvisoryReport, SecurityAdvisoryReportConfig, generate_security_advisory_md_report
from anta._advisory.results import _AdvisoryTestResult
from anta.result_manager import ResultManager
from anta.result_manager.models import AntaTestStatus
from anta.result_manager.models import TestResult as AntaTestResult
from tests.units._advisory.conftest import (
    ADVISORY,
    ADVISORY_ANTA_VERSION,
    ADVISORY_RUN_DEVICES_FILTERED,
    ADVISORY_RUN_DEVICES_UNREACHABLE,
    ADVISORY_RUN_DURATION_FORMATTED,
    ADVISORY_RUN_END_TIME_FORMATTED,
    ADVISORY_RUN_START_TIME_FORMATTED,
    DEFAULT_ADVISORY_REPORT_CONFIG,
    build_fleet_security_advisory_run_context,
    build_security_advisory_run_context,
)
from tests.units._advisory.reporting_data import EXAMPLE_HIGH_ADVISORY, build_security_advisory_result, build_security_advisory_result_manager


def test_security_advisory_markdown_report(tmp_path: Path) -> None:
    """Verify a realistic fleet report is clean, grouped, and deterministic."""
    report = SecurityAdvisoryReport.from_result_manager(build_security_advisory_result_manager())
    output = tmp_path / "advisories.md"

    generate_security_advisory_md_report(report, output, build_fleet_security_advisory_run_context(report), DEFAULT_ADVISORY_REPORT_CONFIG)

    expected = (Path(__file__).parents[2] / "data" / "test_security_advisory_md_report.md").read_text(encoding="utf-8")
    assert output.read_text(encoding="utf-8") == expected


def test_security_advisory_markdown_report_with_run_overview(tmp_path: Path) -> None:
    """Verify run context metadata is rendered in the security advisory run overview section."""
    report = SecurityAdvisoryReport.from_result_manager(build_security_advisory_result_manager())
    output = tmp_path / "advisories.md"
    run_context = build_fleet_security_advisory_run_context(report)

    generate_security_advisory_md_report(report, output, run_context, DEFAULT_ADVISORY_REPORT_CONFIG)

    content = output.read_text(encoding="utf-8")
    assert "  - [Security Advisory Run Overview](#security-advisory-run-overview)" in content
    assert '## 📋 Security Advisory Run Overview <a id="security-advisory-run-overview"></a>' in content
    assert f"**ANTA Version** | {ADVISORY_ANTA_VERSION}" in content
    assert f"**Test Execution Start Time** | {ADVISORY_RUN_START_TIME_FORMATTED}" in content
    assert f"**Test Execution End Time** | {ADVISORY_RUN_END_TIME_FORMATTED}" in content
    assert f"**Total Duration** | {ADVISORY_RUN_DURATION_FORMATTED}" in content
    assert "**Total Devices In Inventory** | 8" in content
    assert f"**Devices Unreachable At Setup** | {ADVISORY_RUN_DEVICES_UNREACHABLE[0]}" in content
    assert f"**Devices Filtered At Setup** | {'<br>'.join(ADVISORY_RUN_DEVICES_FILTERED)}" in content
    assert "**Filters Applied** | Tags: spine" in content
    assert "**Security Advisories Assessed** | 3" in content
    assert "**Devices Assessed** | 8" in content


def test_security_advisory_markdown_run_overview_ignores_hidden_results(tmp_path: Path) -> None:
    """Verify hidden results do not change the run-level assessment metrics."""
    manager = ResultManager()
    manager.add(build_security_advisory_result("leaf1", AntaTestStatus.SUCCESS, "No exposure detected.", ADVISORY))
    manager.add(build_security_advisory_result("leaf2", AntaTestStatus.FAILURE, "Exposure detected.", EXAMPLE_HIGH_ADVISORY))
    full_report = SecurityAdvisoryReport.from_result_manager(manager)
    visible_report = SecurityAdvisoryReport.from_result_manager(manager.filter({AntaTestStatus.SUCCESS}))
    output = tmp_path / "advisories.md"

    generate_security_advisory_md_report(
        visible_report,
        output,
        build_security_advisory_run_context(full_report, inventory_size=2),
        DEFAULT_ADVISORY_REPORT_CONFIG,
    )

    content = output.read_text(encoding="utf-8")
    assert "| leaf1 |" not in content
    assert "| leaf2 |" in content
    assert "**Security Advisories Assessed** | 2" in content
    assert "**Devices Assessed** | 2" in content


def test_security_advisory_markdown_validates_unfiltered_results_before_writing(tmp_path: Path) -> None:
    """Verify hidden non-advisory results fail validation without leaving a partial report."""
    manager = ResultManager()
    manager.add(build_security_advisory_result("leaf1", AntaTestStatus.FAILURE, "Exposure detected.", ADVISORY))
    report = SecurityAdvisoryReport.from_result_manager(manager)
    manager.add(
        AntaTestResult(
            name="leaf2",
            test="VerifyNTP",
            categories=["ntp"],
            description="Verify NTP.",
            result=AntaTestStatus.SUCCESS,
        )
    )
    output = tmp_path / "advisories.md"

    with pytest.raises(ValueError, match="leaf2/VerifyNTP"):
        generate_security_advisory_md_report(report, output, build_security_advisory_run_context(report), DEFAULT_ADVISORY_REPORT_CONFIG)

    assert not output.exists()


def test_security_advisory_markdown_report_expanded(tmp_path: Path) -> None:
    """Verify expanded Markdown renders real issue assessments using the regular ANTA parent/child layout."""
    report = SecurityAdvisoryReport.from_result_manager(build_security_advisory_result_manager())
    output = tmp_path / "advisories.md"

    generate_security_advisory_md_report(report, output, build_fleet_security_advisory_run_context(report), SecurityAdvisoryReportConfig(expand_results=True))

    expected = (Path(__file__).parents[2] / "data" / "test_security_advisory_md_report_expanded.md").read_text(encoding="utf-8")
    assert output.read_text(encoding="utf-8") == expected


def test_security_advisory_markdown_report_flattened_atomic_results(tmp_path: Path) -> None:
    """Verify default output retains issue attribution without exposing child rows."""
    report = SecurityAdvisoryReport.from_result_manager(build_security_advisory_result_manager())
    output = tmp_path / "advisories.md"

    generate_security_advisory_md_report(report, output, build_fleet_security_advisory_run_context(report), DEFAULT_ADVISORY_REPORT_CONFIG)

    content = output.read_text(encoding="utf-8")
    assert "| Device | Test | Result | Messages |" in content
    assert "| Vulnerability | Description | Severity |" in content
    assert "| CVE-2026-12001 | CVE-2026-12001 Authentication bypass in an enabled management API." in content
    assert "CVE-2026-12001 vulnerable management API - The device is affected because the vulnerable management API is enabled." in content
    assert "GHSA-2345-6789-cfgh authorization controls - The device is not affected by this issue because" in content
    assert "├──" not in content
    assert "└──" not in content


def test_security_advisory_markdown_report_expanded_without_atomic_results(tmp_path: Path) -> None:
    """Verify expanded mode keeps a normal parent row when no detailed issue assessment exists."""
    manager = ResultManager()
    manager.add(build_security_advisory_result("leaf1", AntaTestStatus.SUCCESS, "The device is not affected because EOS 4.40.1F contains the fix.", ADVISORY))
    report = SecurityAdvisoryReport.from_result_manager(manager)
    output = tmp_path / "advisories.md"

    generate_security_advisory_md_report(report, output, build_security_advisory_run_context(report), SecurityAdvisoryReportConfig(expand_results=True))

    content = output.read_text(encoding="utf-8")
    assert "| Device | Test | Description | Vulnerability ID(s) | Result | Messages |" in content
    assert (
        "| leaf1 | VerifySA1 | Verify that the device is not exposed to Arista Security Advisory 0001. | - | ✅&nbsp;Not Affected "
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
        vulnerability_ids=("CVE-2026-0001",),
    )
    manager = ResultManager()
    manager.add(result)
    report = SecurityAdvisoryReport.from_result_manager(manager)
    output = tmp_path / "advisories.md"

    generate_security_advisory_md_report(report, output, build_security_advisory_run_context(report), SecurityAdvisoryReportConfig(expand_results=True))

    content = output.read_text(encoding="utf-8")
    assert "**Detailed findings:** All&nbsp;1&nbsp;checks&nbsp;not&nbsp;affected" in content
    assert "**Overall evidence:** The device is affected because parent-specific evidence proves exposure." in content
    assert "CVE-2026-0001 platform applicability - The device is not affected because this individual platform check passed." in content
    assert "The device is not affected because this individual platform check passed." in content


def test_security_advisory_markdown_report_os_error(tmp_path: Path) -> None:
    """Verify Markdown filesystem errors are propagated."""
    manager = ResultManager()
    manager.add(build_security_advisory_result("leaf1", AntaTestStatus.SUCCESS, "No exposure detected.", ADVISORY))
    report = SecurityAdvisoryReport.from_result_manager(manager)
    run_context = build_security_advisory_run_context(report)
    output = tmp_path / "advisories.md"

    with patch("pathlib.Path.open", side_effect=OSError("write failed")), pytest.raises(OSError, match="write failed"):
        generate_security_advisory_md_report(report, output, run_context, DEFAULT_ADVISORY_REPORT_CONFIG)


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

    generate_security_advisory_md_report(report, output, build_security_advisory_run_context(report), DEFAULT_ADVISORY_REPORT_CONFIG)

    content = output.read_text(encoding="utf-8")
    assert "| Security Advisory | Severity | Devices | ❌&nbsp;Affected | ❓&nbsp;Inconclusive | ✅&nbsp;Not Affected | ❗&nbsp;Error | ⏭️&nbsp;Skipped |" in content
    assert "| [SA0001: Test advisory](#sa-0001) | 🟠&nbsp;High | 1 | 0 | 1 | 0 | 0 | 0 |" in content
    assert "Unset" not in content


@pytest.mark.parametrize(
    ("statuses", "expected"),
    [
        pytest.param([AntaTestStatus.SUCCESS, AntaTestStatus.SUCCESS], "All&nbsp;2&nbsp;checks&nbsp;not&nbsp;affected", id="all-not-affected"),
        pytest.param([AntaTestStatus.SUCCESS, AntaTestStatus.FAILURE], "1/2&nbsp;checks&nbsp;affected", id="affected"),
        pytest.param([AntaTestStatus.SUCCESS, AntaTestStatus.INCONCLUSIVE], "1/2&nbsp;checks&nbsp;inconclusive", id="inconclusive"),
        pytest.param(
            [AntaTestStatus.FAILURE, AntaTestStatus.INCONCLUSIVE],
            "1/2&nbsp;checks&nbsp;affected; 1/2&nbsp;checks&nbsp;inconclusive",
            id="affected-and-inconclusive",
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


def test_security_advisory_markdown_without_vulnerabilities(tmp_path: Path) -> None:
    """Verify an advisory without vulnerabilities uses unknown severity and renders an empty metadata table."""
    advisory = ADVISORY.model_copy(update={"sa_number": "0002", "vulnerabilities": ()})
    manager = ResultManager()
    manager.add(build_security_advisory_result("leaf1", AntaTestStatus.SUCCESS, "No exposure detected.", advisory))
    report = SecurityAdvisoryReport.from_result_manager(manager)
    output = tmp_path / "advisories.md"

    generate_security_advisory_md_report(report, output, build_security_advisory_run_context(report), DEFAULT_ADVISORY_REPORT_CONFIG)

    content = output.read_text(encoding="utf-8")
    assert "[SA0002: Test advisory](#sa-0002) | ⚪&nbsp;Unknown" in content
    assert "⚪ **Severity:** Unknown" in content
    assert "| Vulnerability | Description | Severity |" in content
    assert "CVSS" not in content
    assert "Mitigations" not in content
    assert "Resolutions" not in content


def test_security_advisory_markdown_vulnerability_defaults(tmp_path: Path) -> None:
    """Verify a vulnerability with default severity renders as expected."""
    vulnerability = _AdvisoryVulnerability(id="PROVIDER-0001", description="Provider vulnerability.")
    advisory = ADVISORY.model_copy(update={"vulnerabilities": (vulnerability,)})
    manager = ResultManager()
    manager.add(build_security_advisory_result("leaf1", AntaTestStatus.SUCCESS, "No exposure detected.", advisory))
    report = SecurityAdvisoryReport.from_result_manager(manager)
    output = tmp_path / "advisories.md"

    generate_security_advisory_md_report(report, output, build_security_advisory_run_context(report), DEFAULT_ADVISORY_REPORT_CONFIG)

    content = output.read_text(encoding="utf-8")
    assert "| PROVIDER-0001 | Provider vulnerability. | Unknown |" in content
    assert "[PROVIDER-0001]" not in content
