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
from tests.units._advisory.reporting_data import EXAMPLE_HIGH_ADVISORY, build_security_advisory_md_result_manager, build_security_advisory_result


def test_security_advisory_markdown_report(tmp_path: Path) -> None:
    """Verify a realistic fleet report is clean, grouped, and deterministic."""
    report = SecurityAdvisoryReport.from_result_manager(build_security_advisory_md_result_manager())
    output = tmp_path / "advisories.md"

    generate_security_advisory_md_report(report, output, build_fleet_security_advisory_run_context(report), DEFAULT_ADVISORY_REPORT_CONFIG)

    expected = (Path(__file__).parents[2] / "data" / "test_security_advisory_md_report.md").read_text(encoding="utf-8")
    assert output.read_text(encoding="utf-8") == expected


def test_security_advisory_markdown_report_with_run_overview(tmp_path: Path) -> None:
    """Verify run context metadata is rendered in the Run Overview section."""
    report = SecurityAdvisoryReport.from_result_manager(build_security_advisory_md_result_manager())
    output = tmp_path / "advisories.md"
    run_context = build_fleet_security_advisory_run_context(report)

    generate_security_advisory_md_report(report, output, run_context, DEFAULT_ADVISORY_REPORT_CONFIG)

    content = output.read_text(encoding="utf-8")
    assert '<h1 id="anta-security-advisory-report" align="center">🛡️ ANTA Security Advisory Report 🛡️</h1>' in content
    assert "- [ANTA Security Advisory Report](#anta-security-advisory-report)" not in content
    assert "- [Run Overview](#run-overview)" in content
    assert "  - [Example Management API Authentication Bypass](#sa-0120)" in content
    assert "  - [Example EOS Process Denial of Service](#sa-0121)" in content
    assert "  - [Security Advisory 0117](#sa-0117)" in content
    assert '## 📋 Run Overview <a id="run-overview"></a>' in content
    assert f"| **ANTA Version** | {ADVISORY_ANTA_VERSION} |" in content
    assert f"| **Duration** | {ADVISORY_RUN_DURATION_FORMATTED} ({ADVISORY_RUN_START_TIME_FORMATTED} → {ADVISORY_RUN_END_TIME_FORMATTED}) |" in content
    assert "| **Security Advisories Tested** | 3 |" in content
    assert "### Security Advisories" not in content
    assert "### Devices" not in content
    assert "| Device Metric | Details |" not in content
    assert "| **Total Devices In Inventory** | 8 |" in content
    assert "| **Devices Assessed** | 8 |" in content
    assert f"| **Devices Unreachable At Setup** | {ADVISORY_RUN_DEVICES_UNREACHABLE[0]} |" in content
    assert f"| **Devices Filtered At Setup** | {'<br>'.join(ADVISORY_RUN_DEVICES_FILTERED)} |" in content
    assert "| **Filters Applied** | Tags: spine |" in content


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
    assert "| **Total Devices In Inventory** | 2 |" in content
    assert "| **Devices Assessed** | 2 |" in content


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
    report = SecurityAdvisoryReport.from_result_manager(build_security_advisory_md_result_manager())
    output = tmp_path / "advisories.md"

    generate_security_advisory_md_report(report, output, build_fleet_security_advisory_run_context(report), SecurityAdvisoryReportConfig(expand_results=True))

    expected = (Path(__file__).parents[2] / "data" / "test_security_advisory_md_report_expanded.md").read_text(encoding="utf-8")
    content = output.read_text(encoding="utf-8")
    assert content == expected
    assert "CVE-2025-0936" in content
    assert "🟡&nbsp;CVE-2025-0936" in content
    assert "🔵&nbsp;CVE-2026-12102" in content
    assert "⚪&nbsp;CVE-2026-12103" in content
    assert "Upgrade to a fixed EOS release when one is published, then rerun the test." in content
    assert "GTI-EXAMPLE-12101" in content
    assert "Disable or restrict the exposed service and upgrade to a fixed EOS release." in content


def test_security_advisory_markdown_report_flattened_atomic_results(tmp_path: Path) -> None:
    """Verify default output retains issue attribution without exposing child rows."""
    report = SecurityAdvisoryReport.from_result_manager(build_security_advisory_md_result_manager())
    output = tmp_path / "advisories.md"

    generate_security_advisory_md_report(report, output, build_fleet_security_advisory_run_context(report), DEFAULT_ADVISORY_REPORT_CONFIG)

    content = output.read_text(encoding="utf-8")
    assert "| Device | Result | Findings | Remediations |" in content
    assert "> | Vulnerability | Severity | Description |" in content
    assert "#### Vulnerabilities" not in content
    assert (
        "> **Severity:** 🔴 Critical\\\n> **URL:** <https://www.arista.com/en/support/advisories-notices/security-advisory/example-0120>\n>\n"
        "> An example vulnerability in an enabled management API could allow an unauthenticated remote actor to bypass authentication under specific "
        "configurations. This fictional advisory is used only to exercise realistic report rendering."
    ) in content
    assert "> | CVE-2026-12001 | 🔴&nbsp;Critical | Authentication bypass in an enabled management API. |" in content
    assert "> | GHSA-2345-6789-cfgh | 🟠&nbsp;High | Authorization flaw affecting management API access controls. |\n>\n\n#### 🔎 Device Findings" in content
    assert "CVE-2026-12001: Vulnerable management API - The device is affected because the vulnerable management API is enabled." in content
    assert "GHSA-2345-6789-cfgh: Authorization controls - The device is not affected by this issue because" in content
    assert "Upgrade to a fixed EOS release when one is published, then rerun the test." in content
    assert "Collect valid EOS version evidence and rerun the test." in content
    assert "Restore device reachability and rerun the test." in content
    assert "├──" not in content
    assert "└──" not in content


def test_security_advisory_markdown_report_flattened_remediation(tmp_path: Path) -> None:
    """Render aggregated test-level remediation when atomic rows are hidden."""
    result = build_security_advisory_result(
        "leaf1",
        AntaTestStatus.FAILURE,
        "The device is affected.",
        ADVISORY,
        remediations=["First remediation.", "Second remediation."],
    )
    result.add(
        "Affected issue.",
        AntaTestStatus.FAILURE,
        ["Affected finding."],
        vulnerability_ids=("CVE-2026-0001",),
        remediations=["First remediation.", "Atomic remediation."],
    )
    manager = ResultManager()
    manager.add(result)
    report = SecurityAdvisoryReport.from_result_manager(manager)
    output = tmp_path / "advisories.md"

    generate_security_advisory_md_report(report, output, build_security_advisory_run_context(report), DEFAULT_ADVISORY_REPORT_CONFIG)

    content = output.read_text(encoding="utf-8")
    assert (
        "| leaf1 | 🛑&nbsp;Affected | The device is affected.<br>CVE-2026-0001: Affected issue. - Affected finding. "
        "| •&nbsp;CVE-2026-0001: First remediation.<br>•&nbsp;Second remediation.<br>•&nbsp;CVE-2026-0001: Atomic remediation. |"
    ) in content


def test_security_advisory_markdown_report_groups_shared_remediation_vulnerability_ids(tmp_path: Path) -> None:
    """Render one shared remediation with every associated vulnerability ID."""
    result = build_security_advisory_result("leaf1", AntaTestStatus.FAILURE, "The device is affected.", ADVISORY)
    for vulnerability in ADVISORY.vulnerabilities:
        result.add(
            vulnerability.description,
            AntaTestStatus.FAILURE,
            ["The device is affected because shared evidence proves exposure."],
            vulnerability_ids=(vulnerability.id,),
            remediations=["Apply the shared remediation."],
        )
    manager = ResultManager()
    manager.add(result)
    report = SecurityAdvisoryReport.from_result_manager(manager)
    output = tmp_path / "advisories.md"

    generate_security_advisory_md_report(report, output, build_security_advisory_run_context(report), DEFAULT_ADVISORY_REPORT_CONFIG)

    content = output.read_text(encoding="utf-8")
    assert "•&nbsp;CVE-2026-0001, CVE-2026-0002: Apply the shared remediation." in content
    assert content.count("Apply the shared remediation.") == 1


def test_security_advisory_markdown_report_expanded_without_atomic_results(tmp_path: Path) -> None:
    """Verify expanded mode keeps a normal parent row when no detailed issue assessment exists."""
    manager = ResultManager()
    result = build_security_advisory_result(
        "leaf1",
        AntaTestStatus.SUCCESS,
        "The device is not affected because EOS 4.40.1F contains the fix.",
        ADVISORY,
        remediations=["Maintain EOS 4.40.1F or later."],
    )
    manager.add(result)
    report = SecurityAdvisoryReport.from_result_manager(manager)
    output = tmp_path / "advisories.md"

    generate_security_advisory_md_report(report, output, build_security_advisory_run_context(report), SecurityAdvisoryReportConfig(expand_results=True))

    content = output.read_text(encoding="utf-8")
    assert "| Device | Description | Vulnerability ID(s) | Result | Findings | Remediations |" in content
    assert (
        "| leaf1 | Verify that the device is not exposed to Arista Security Advisory 0001. | - | ✅&nbsp;Not Affected "
        "| The device is not affected because EOS 4.40.1F contains the fix. | Maintain EOS 4.40.1F or later. |"
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
        "Platform applicability",
        AntaTestStatus.SUCCESS,
        ["The device is not affected because this individual platform check passed."],
        vulnerability_ids=("CVE-2026-0001",),
        remediations=["Maintain the current platform configuration."],
    )
    manager = ResultManager()
    manager.add(result)
    report = SecurityAdvisoryReport.from_result_manager(manager)
    output = tmp_path / "advisories.md"

    generate_security_advisory_md_report(report, output, build_security_advisory_run_context(report), SecurityAdvisoryReportConfig(expand_results=True))

    content = output.read_text(encoding="utf-8")
    assert "**Detailed findings:** All&nbsp;1&nbsp;checks&nbsp;not&nbsp;affected" in content
    assert "**Overall evidence:** The device is affected because parent-specific evidence proves exposure." in content
    assert "Test vulnerability affecting the management API." in content
    assert "The device is not affected because this individual platform check passed." in content
    assert "Maintain the current platform configuration." in content


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
    expected_header = (
        "| Security Advisory | Severity | Devices | 🛑&nbsp;Affected | ❓&nbsp;Inconclusive "
        "| ✅&nbsp;Mitigated | ✅&nbsp;Not Affected | ❗&nbsp;Error | ⏭️&nbsp;Skipped |"
    )
    assert expected_header in content
    assert "| [Test advisory](#sa-0001) | 🟠&nbsp;High | 1 | 0 | 1 | 0 | 0 | 0 | 0 |" in content
    assert "Unset" not in content


def test_security_advisory_markdown_summary_distinguishes_mitigated_results(tmp_path: Path) -> None:
    """Verify mitigated devices are not counted as unaffected in the summary."""
    manager = ResultManager()
    manager.add(build_security_advisory_result("leaf1", AntaTestStatus.SUCCESS, "The device is affected but mitigated because the service is disabled.", ADVISORY))
    manager.add(build_security_advisory_result("leaf2", AntaTestStatus.SUCCESS, "The device is not affected because the fixed release is installed.", ADVISORY))
    report = SecurityAdvisoryReport.from_result_manager(manager)
    output = tmp_path / "advisories.md"

    generate_security_advisory_md_report(report, output, build_security_advisory_run_context(report, inventory_size=2), DEFAULT_ADVISORY_REPORT_CONFIG)

    content = output.read_text(encoding="utf-8")
    assert "| [Test advisory](#sa-0001) | 🟠&nbsp;High | 2 | 0 | 0 | 1 | 1 | 0 | 0 |" in content
    assert "| leaf1 | ✅&nbsp;Mitigated |" in content


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


def test_security_advisory_markdown_atomic_summary_includes_mitigated_results() -> None:
    """Verify expanded summaries distinguish mitigated checks from unaffected checks."""
    result = _AdvisoryTestResult(
        name="leaf1",
        test="VerifySA1",
        categories=["advisories"],
        description="Test advisory metadata.",
        advisory=ADVISORY,
    )
    result.add("Mitigated issue", AntaTestStatus.SUCCESS, ["The device is affected but mitigated because the service is disabled."])
    result.add("Unaffected issue", AntaTestStatus.SUCCESS, ["The device is not affected because the fixed release is installed."])

    assert SecurityAdvisoryDetails._atomic_summary(result) == "1/2&nbsp;checks&nbsp;mitigated"


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
    assert "[Test advisory](#sa-0002) | ⚪&nbsp;Unknown" in content
    assert "**Severity:** ⚪ Unknown" in content
    assert "> | Vulnerability | Severity | Description |" in content
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
    assert "| PROVIDER-0001 | ⚪&nbsp;Unknown | Provider vulnerability. |" in content
    assert "[PROVIDER-0001]" not in content


def test_security_advisory_markdown_sorts_vulnerabilities_by_severity(tmp_path: Path) -> None:
    """Order vulnerability metadata from highest to lowest severity."""
    manager = ResultManager()
    manager.add(build_security_advisory_result("leaf1", AntaTestStatus.SUCCESS, "No exposure detected.", ADVISORY))
    report = SecurityAdvisoryReport.from_result_manager(manager)
    output = tmp_path / "advisories.md"

    generate_security_advisory_md_report(report, output, build_security_advisory_run_context(report), DEFAULT_ADVISORY_REPORT_CONFIG)

    content = output.read_text(encoding="utf-8")
    high_vulnerability = "| CVE-2026-0002 | 🟠&nbsp;High | Test vulnerability affecting access controls. |"
    medium_vulnerability = "| CVE-2026-0001 | 🟡&nbsp;Medium | Test vulnerability affecting the management API. |"
    assert content.index(high_vulnerability) < content.index(medium_vulnerability)


def test_security_advisory_markdown_atomic_metadata_and_remediation(tmp_path: Path) -> None:
    """Use vulnerability metadata and atomic remediation in expanded findings."""
    result = _AdvisoryTestResult(
        name="leaf1",
        test="VerifySA1",
        categories=["advisories"],
        description="Test advisory metadata.",
        result=AntaTestStatus.FAILURE,
        messages=["The device is affected."],
        advisory=ADVISORY,
        remediations=["Parent aggregate remediation."],
    )
    result.add(
        "Shared atomic description.",
        AntaTestStatus.FAILURE,
        ["Shared finding."],
        vulnerability_ids=("CVE-2026-0001", "CVE-2026-0002"),
        remediations=["Shared vulnerability remediation."],
    )
    result.add("Unassociated atomic description.", AntaTestStatus.INCONCLUSIVE, ["Unassociated finding."], remediations=["Unassociated remediation."])
    manager = ResultManager()
    manager.add(result)
    report = SecurityAdvisoryReport.from_result_manager(manager)
    output = tmp_path / "advisories.md"

    generate_security_advisory_md_report(report, output, build_security_advisory_run_context(report), SecurityAdvisoryReportConfig(expand_results=True))

    content = output.read_text(encoding="utf-8")
    assert "Test vulnerability affecting the management API.<br>Test vulnerability affecting access controls." in content
    assert "Unassociated atomic description." in content
    assert "Shared vulnerability remediation." in content
    assert "Unassociated remediation." in content
    assert (
        "•&nbsp;Parent aggregate remediation.<br>•&nbsp;CVE-2026-0001, CVE-2026-0002: Shared vulnerability remediation.<br>•&nbsp;Unassociated remediation."
    ) in content
