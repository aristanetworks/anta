# Copyright (c) 2026 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Unit tests for security advisory Markdown reporting."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest

from anta._advisory.models import _AdvisoryVulnerability
from anta._advisory.remediation import OperationalAction, RemediationPlan
from anta._advisory.reporter.reporting import SecurityAdvisoryReport, generate_security_advisory_md_report
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
    build_fleet_security_advisory_run_context,
    build_security_advisory_run_context,
)
from tests.units._advisory.reporting_data import SA146_ADVISORY, build_security_advisory_md_result_manager, build_security_advisory_result, ensure_atomic_results


def test_security_advisory_markdown_report(tmp_path: Path) -> None:
    """Verify a realistic fleet report is clean, grouped, and deterministic."""
    report = SecurityAdvisoryReport.from_result_manager(build_security_advisory_md_result_manager())
    output = tmp_path / "advisories.md"

    generate_security_advisory_md_report(report, output, build_fleet_security_advisory_run_context(report))

    expected = (Path(__file__).parents[2] / "data" / "test_security_advisory_md_report.md").read_text(encoding="utf-8")
    assert output.read_text(encoding="utf-8") == expected


def test_security_advisory_markdown_report_with_run_overview(tmp_path: Path) -> None:
    """Verify run context metadata is rendered in the Run Overview section."""
    report = SecurityAdvisoryReport.from_result_manager(build_security_advisory_md_result_manager())
    output = tmp_path / "advisories.md"
    run_context = build_fleet_security_advisory_run_context(report)

    generate_security_advisory_md_report(report, output, run_context)

    content = output.read_text(encoding="utf-8")
    assert '<h1 id="anta-security-advisory-report" align="center">🛡️ ANTA Security Advisory Report 🛡️</h1>' in content
    assert "- [ANTA Security Advisory Report](#anta-security-advisory-report)" not in content
    assert "- [Run Overview](#run-overview)" in content
    assert "  - [Security Advisory 0147](#sa-0147)" in content
    assert "  - [Security Advisory 0146](#sa-0146)" in content
    assert "  - [Security Advisory 0117](#sa-0117)" in content
    assert "  - [Reporter Rendering Coverage Advisory](#sa-9999)" in content
    assert '## 📋 Run Overview <a id="run-overview"></a>' in content
    assert f"| **ANTA Version** | {ADVISORY_ANTA_VERSION} |" in content
    assert f"| **Duration** | {ADVISORY_RUN_DURATION_FORMATTED} ({ADVISORY_RUN_START_TIME_FORMATTED} → {ADVISORY_RUN_END_TIME_FORMATTED}) |" in content
    assert "| **Security Advisories Tested** | 4 |" in content
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
    manager.add(ensure_atomic_results(build_security_advisory_result("leaf1", AntaTestStatus.SUCCESS, "No exposure detected.", ADVISORY)))
    manager.add(ensure_atomic_results(build_security_advisory_result("leaf2", AntaTestStatus.FAILURE, "Exposure detected.", SA146_ADVISORY)))
    full_report = SecurityAdvisoryReport.from_result_manager(manager)
    visible_report = SecurityAdvisoryReport.from_result_manager(manager.filter({AntaTestStatus.SUCCESS}))
    output = tmp_path / "advisories.md"

    generate_security_advisory_md_report(visible_report, output, build_security_advisory_run_context(full_report, inventory_size=2))

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
        generate_security_advisory_md_report(report, output, build_security_advisory_run_context(report))

    assert not output.exists()


def test_security_advisory_markdown_device_findings_use_atomic_results(tmp_path: Path) -> None:
    """Verify device findings render one atomic row per vulnerability without parent aggregation."""
    report = SecurityAdvisoryReport.from_result_manager(build_security_advisory_md_result_manager())
    output = tmp_path / "advisories.md"

    generate_security_advisory_md_report(report, output, build_fleet_security_advisory_run_context(report))

    content = output.read_text(encoding="utf-8")
    assert "| Device | Vulnerability | Result | Findings | Remediations |" in content
    assert "> | Vulnerability | Severity | Description |" in content
    assert "#### Vulnerabilities" not in content
    assert (
        "> **Severity:** 🔴 Critical\\\n> **URL:** <https://www.arista.com/en/support/advisories-notices/security-advisory/24515-security-advisory-0147>\n>\n"
        "> Multiple vulnerabilities have been discovered in OpenSSH before version 10.4, which is shipped with multiple Arista products."
    ) in content
    assert "> | CVE-2026-60002 | 🔴&nbsp;Critical | SSH client issue when connecting to a malicious or compromised server. |" in content
    assert "> | CVE-2026-60001 | 🟡&nbsp;Medium | OpenSSH server issue affecting accepted SSH connections. |\n>\n\n#### 🔎 Device Findings" in content
    assert "| DC1-LEAF1 | 🟡&nbsp;CVE-2026-60001 | 🛑&nbsp;Affected |" in content
    assert "| DC1-LEAF1 | 🟡&nbsp;CVE-2026-59995 | ❓&nbsp;Inconclusive |" in content
    assert "| DC1-LEAF1 | 🔴&nbsp;CVE-2026-60002 | ❓&nbsp;Inconclusive |" in content
    assert "The device is affected because openssh-server '9.9p1' is affected and SSH accepts connections." in content
    assert "The assessment is inconclusive and the device may be affected because openssh-clients '9.9p1' is affected" in content
    assert "The device is affected but mitigated because openssh-clients '9.9p1' uses strict host-key checking." in content
    assert "CVE-2026-60001: The device is affected" not in content
    assert "**Detailed findings:**" not in content
    assert "**Overall evidence:**" not in content
    assert "├──" not in content
    assert "└──" not in content
    assert "Refer to the advisory to determine whether the unresolved condition applies" in content
    assert "Collect or correct valid refreshed device EOS version metadata and rerun the test." in content
    assert "Restore device reachability and rerun the test." in content
    assert "🟡&nbsp;CVE-2025-0936" in content
    assert "🟠&nbsp;GHSA-hrxh-6v49-42gf" in content
    assert "Upgrade to EOS 4.36.2F or later in the 4.36 train" in content
    assert "🔵&nbsp;TEST-LOW-SEVERITY" in content
    assert "⚪&nbsp;TEST-UNKNOWN-SEVERITY" in content


def test_security_advisory_markdown_report_atomic_remediation(tmp_path: Path) -> None:
    """Render remediation on the atomic vulnerability row that owns the plan."""
    result = build_security_advisory_result("leaf1", AntaTestStatus.FAILURE, "The device is affected.", ADVISORY)
    result.add(
        "Verify CVE-2026-0001.",
        AntaTestStatus.FAILURE,
        ["Affected finding."],
        vulnerability_ids=("CVE-2026-0001",),
        remediation=RemediationPlan(OperationalAction("First remediation.")),
    )
    result.add(
        "Verify CVE-2026-0002.",
        AntaTestStatus.FAILURE,
        ["Second finding."],
        vulnerability_ids=("CVE-2026-0002",),
        remediation=RemediationPlan(OperationalAction("Second remediation.")),
    )
    manager = ResultManager()
    manager.add(result)
    report = SecurityAdvisoryReport.from_result_manager(manager)
    output = tmp_path / "advisories.md"

    generate_security_advisory_md_report(report, output, build_security_advisory_run_context(report))

    content = output.read_text(encoding="utf-8")
    assert "| leaf1 | 🟡&nbsp;CVE-2026-0001 | 🛑&nbsp;Affected | Affected finding. | First remediation. |" in content
    assert "| leaf1 | 🟠&nbsp;CVE-2026-0002 | 🛑&nbsp;Affected | Second finding. | Second remediation. |" in content
    assert "•&nbsp;" not in content


def test_security_advisory_markdown_report_repeats_shared_remediation_per_vulnerability(tmp_path: Path) -> None:
    """Render the same atomic remediation independently on each associated vulnerability row."""
    result = build_security_advisory_result("leaf1", AntaTestStatus.FAILURE, "The device is affected.", ADVISORY)
    for vulnerability in ADVISORY.vulnerabilities:
        result.add(
            f"Verify {vulnerability.id}.",
            AntaTestStatus.FAILURE,
            ["The device is affected because shared evidence proves exposure."],
            vulnerability_ids=(vulnerability.id,),
            remediation=RemediationPlan(OperationalAction("Apply the shared remediation.")),
        )
    manager = ResultManager()
    manager.add(result)
    report = SecurityAdvisoryReport.from_result_manager(manager)
    output = tmp_path / "advisories.md"

    generate_security_advisory_md_report(report, output, build_security_advisory_run_context(report))

    content = output.read_text(encoding="utf-8")
    assert content.count("Apply the shared remediation.") == 2
    assert "CVE-2026-0001, CVE-2026-0002: Apply the shared remediation." not in content


def test_security_advisory_markdown_report_os_error(tmp_path: Path) -> None:
    """Verify Markdown filesystem errors are propagated."""
    manager = ResultManager()
    manager.add(build_security_advisory_result("leaf1", AntaTestStatus.SUCCESS, "No exposure detected.", ADVISORY))
    report = SecurityAdvisoryReport.from_result_manager(manager)
    run_context = build_security_advisory_run_context(report)
    output = tmp_path / "advisories.md"

    with patch("pathlib.Path.open", side_effect=OSError("write failed")), pytest.raises(OSError, match="write failed"):
        generate_security_advisory_md_report(report, output, run_context)


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

    generate_security_advisory_md_report(report, output, build_security_advisory_run_context(report))

    content = output.read_text(encoding="utf-8")
    expected_header = (
        "| Security Advisory | Severity | Devices | 🛑&nbsp;Affected | ❓&nbsp;Inconclusive "
        "| 🛡️&nbsp;Mitigated | ✅&nbsp;Not&nbsp;Affected | ❗&nbsp;Error | ⏭️&nbsp;Skipped |"
    )
    assert expected_header in content
    assert "| [Test advisory](#sa-0001) | 🟠&nbsp;High | 1 | 0 | 1 | 0 | 0 | 0 | 0 |" in content
    assert "Unset" not in content


def test_security_advisory_markdown_summary_distinguishes_mitigated_results(tmp_path: Path) -> None:
    """Verify mitigated devices are not counted as unaffected in the summary."""
    manager = ResultManager()
    manager.add(
        ensure_atomic_results(
            build_security_advisory_result("leaf1", AntaTestStatus.SUCCESS, "The device is affected but mitigated because the service is disabled.", ADVISORY)
        )
    )
    manager.add(
        ensure_atomic_results(
            build_security_advisory_result("leaf2", AntaTestStatus.SUCCESS, "The device is not affected because the fixed release is installed.", ADVISORY)
        )
    )
    report = SecurityAdvisoryReport.from_result_manager(manager)
    output = tmp_path / "advisories.md"

    generate_security_advisory_md_report(report, output, build_security_advisory_run_context(report, inventory_size=2))

    content = output.read_text(encoding="utf-8")
    assert "| [Test advisory](#sa-0001) | 🟠&nbsp;High | 2 | 0 | 0 | 1 | 1 | 0 | 0 |" in content
    assert "| leaf1 | 🟡&nbsp;CVE-2026-0001 | 🛡️&nbsp;Mitigated |" in content


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
    manager.add(ensure_atomic_results(build_security_advisory_result("leaf1", AntaTestStatus.SUCCESS, "No exposure detected.", advisory)))
    report = SecurityAdvisoryReport.from_result_manager(manager)
    output = tmp_path / "advisories.md"

    generate_security_advisory_md_report(report, output, build_security_advisory_run_context(report))

    content = output.read_text(encoding="utf-8")
    assert "[Test advisory](#sa-0002) | ⚪&nbsp;Unknown" in content
    assert "**Severity:** ⚪ Unknown" in content
    assert "> | Vulnerability | Severity | Description |" in content
    assert "| leaf1 | - | ✅&nbsp;Not&nbsp;Affected | No exposure detected. | - |" in content
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

    generate_security_advisory_md_report(report, output, build_security_advisory_run_context(report))

    content = output.read_text(encoding="utf-8")
    assert "| PROVIDER-0001 | ⚪&nbsp;Unknown | Provider vulnerability. |" in content
    assert "[PROVIDER-0001]" not in content


def test_security_advisory_markdown_sorts_vulnerabilities_by_severity(tmp_path: Path) -> None:
    """Order vulnerability metadata from highest to lowest severity."""
    manager = ResultManager()
    manager.add(build_security_advisory_result("leaf1", AntaTestStatus.SUCCESS, "No exposure detected.", ADVISORY))
    report = SecurityAdvisoryReport.from_result_manager(manager)
    output = tmp_path / "advisories.md"

    generate_security_advisory_md_report(report, output, build_security_advisory_run_context(report))

    content = output.read_text(encoding="utf-8")
    high_vulnerability = "| CVE-2026-0002 | 🟠&nbsp;High | Test vulnerability affecting access controls. |"
    medium_vulnerability = "| CVE-2026-0001 | 🟡&nbsp;Medium | Test vulnerability affecting the management API. |"
    assert content.index(high_vulnerability) < content.index(medium_vulnerability)


def test_security_advisory_markdown_atomic_metadata_and_remediation(tmp_path: Path) -> None:
    """Render one device finding row per vulnerability, repeating a shared atomic result."""
    result = _AdvisoryTestResult(
        name="leaf1",
        test="VerifySA1",
        categories=["advisories"],
        description="Test advisory metadata.",
        result=AntaTestStatus.FAILURE,
        messages=["The device is affected."],
        advisory=ADVISORY,
    )
    result.add(
        "Verify CVE-2026-0001 and CVE-2026-0002.",
        AntaTestStatus.FAILURE,
        ["Shared finding."],
        vulnerability_ids=("CVE-2026-0001", "CVE-2026-0002"),
        remediation=RemediationPlan(OperationalAction("Shared vulnerability remediation.")),
    )
    result.add(
        "Unassociated atomic description.",
        AntaTestStatus.INCONCLUSIVE,
        ["Unassociated finding."],
        remediation=RemediationPlan(OperationalAction("Unassociated remediation.")),
    )
    manager = ResultManager()
    manager.add(result)
    report = SecurityAdvisoryReport.from_result_manager(manager)
    output = tmp_path / "advisories.md"

    generate_security_advisory_md_report(report, output, build_security_advisory_run_context(report))

    content = output.read_text(encoding="utf-8")
    assert "| Device | Vulnerability | Result | Findings | Remediations |" in content
    assert "| leaf1 | 🟡&nbsp;CVE-2026-0001 | 🛑&nbsp;Affected | Shared finding. | Shared vulnerability remediation. |" in content
    assert "| leaf1 | 🟠&nbsp;CVE-2026-0002 | 🛑&nbsp;Affected | Shared finding. | Shared vulnerability remediation. |" in content
    assert "| leaf1 | - | ❓&nbsp;Inconclusive | Unassociated finding. | Unassociated remediation. |" in content
    assert "Verify CVE-2026-0001 and CVE-2026-0002." not in content
    assert "Unassociated atomic description." not in content
    assert "•&nbsp;" not in content
