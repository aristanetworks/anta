# Copyright (c) 2026 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Unit tests for security advisory Markdown reporting."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import TYPE_CHECKING, cast

import pytest

from anta._advisory.md_reporter import (
    AdvisoryExposureSummary,
    ANTASecurityAdvisoryReport,
    SecurityAdvisoryDetails,
    group_advisory_results,
)
from anta._advisory.models import AdvisoryCVE, AdvisoryCVSSScore, AdvisoryMetadata, AdvisoryMitigation, AdvisoryResolution, AdvisorySeverity
from anta.reporter.md_reporter import MDReportGenerator, RunOverview
from anta.result_manager import ResultManager
from anta.result_manager.models import AntaTestStatus
from anta.result_manager.models import TestResult as AntaTestResult
from anta.result_manager.models import TestResultMetadata as AntaTestResultMetadata
from anta.tests.advisories.sa_117 import VerifySA117
from tests.units._advisory.conftest import ADVISORY

if TYPE_CHECKING:
    from collections.abc import Iterable

SA117_ADVISORY = cast("AdvisoryMetadata", vars(VerifySA117)["advisory"])

EXAMPLE_CRITICAL_ADVISORY = AdvisoryMetadata(
    sa_number="0120",
    title="Example Management API Authentication Bypass",
    severity=AdvisorySeverity.CRITICAL,
    cves=(
        AdvisoryCVE(
            cve_id="CVE-2026-12001",
            severity=AdvisorySeverity.CRITICAL,
            cvss_scores=(
                AdvisoryCVSSScore(version="3.1", score=9.8, vector="CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H"),
                AdvisoryCVSSScore(version="4.0", score=9.3, vector="CVSS:4.0/AV:N/AC:L/AT:N/PR:N/UI:N/VC:H/VI:H/VA:H"),
            ),
        ),
        AdvisoryCVE(
            cve_id="CVE-2026-12002",
            severity=AdvisorySeverity.HIGH,
            cvss_scores=(AdvisoryCVSSScore(version="3.1", score=8.1, vector="CVSS:3.1/AV:N/AC:H/PR:N/UI:N/S:U/C:H/I:H/A:H"),),
        ),
    ),
    url="https://www.arista.com/en/support/advisories-notices/security-advisory/example-0120",
    description=(
        "An example vulnerability in an enabled management API could allow an unauthenticated remote actor to bypass authentication under specific configurations. "
        "This fictional advisory is used only to exercise realistic report rendering."
    ),
    resolutions=(
        AdvisoryResolution(
            name="Upgrade EOS",
            details="Upgrade every affected device to a fixed EOS release from the recommended release train.",
            url="https://www.arista.com/en/support/advisories-notices/security-advisory/example-0120",
        ),
        AdvisoryResolution(
            name="Rotate management credentials",
            details="Rotate credentials after upgrading if the vulnerable API was reachable from an untrusted network.",
        ),
    ),
    mitigations=(
        AdvisoryMitigation(
            name="Restrict management-plane access",
            details="Apply control-plane ACLs so the affected API is reachable only from trusted management subnets.",
        ),
    ),
)

EXAMPLE_HIGH_ADVISORY = AdvisoryMetadata(
    sa_number="0121",
    title="Example EOS Process Denial of Service",
    severity=AdvisorySeverity.HIGH,
    cves=(
        AdvisoryCVE(
            cve_id="CVE-2026-12101",
            severity=AdvisorySeverity.HIGH,
            cvss_scores=(AdvisoryCVSSScore(version="3.1", score=7.5, vector="CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:N/I:N/A:H"),),
        ),
    ),
    url="https://www.arista.com/en/support/advisories-notices/security-advisory/example-0121",
    description=(
        "An example malformed packet could restart an EOS process when received on an exposed service. "
        "This fictional advisory demonstrates a larger fleet with mixed findings and no published mitigation."
    ),
    resolutions=(
        AdvisoryResolution(
            name="Install a fixed release",
            details="Upgrade to a fixed EOS release and verify process stability after the maintenance window.",
            url="https://www.arista.com/en/support/advisories-notices/security-advisory/example-0121",
        ),
    ),
)


def _result(name: str, status: AntaTestStatus, message: str, advisory: AdvisoryMetadata = ADVISORY) -> AntaTestResult:
    """Create a security advisory result for report tests."""
    return AntaTestResult(
        name=name,
        test=f"VerifySA{int(advisory.sa_number)}",
        categories=["advisories"],
        description=f"Verify that the device is not exposed to Arista Security Advisory {advisory.sa_number}.",
        result=status,
        messages=[message],
        metadata=AntaTestResultMetadata(security_advisory=advisory),
    )


def _add_findings(
    manager: ResultManager,
    advisory: AdvisoryMetadata,
    findings: Iterable[tuple[str, AntaTestStatus, str]],
) -> None:
    """Add realistic per-device findings for one advisory."""
    for device, status, message in findings:
        manager.add(_result(device, status, message, advisory))


def test_security_advisory_markdown_report(tmp_path: Path) -> None:
    """Verify a realistic fleet report is clean, grouped, and deterministic."""
    manager = ResultManager()
    _add_findings(
        manager,
        SA117_ADVISORY,
        [
            ("DC1-LEAF1", AntaTestStatus.FAILURE, "EOS 4.32.4M is affected. OpenConfig gNMI has accounting requests enabled."),
            ("DC1-LEAF2", AntaTestStatus.SUCCESS, "EOS 4.32.5M is not affected by this advisory."),
            ("DC1-LEAF3", AntaTestStatus.ERROR, "The EOS version could not be determined from the available command output."),
            ("DC1-LEAF4", AntaTestStatus.SKIPPED, "Device was unreachable during test execution."),
            ("DC1-SPINE1", AntaTestStatus.SUCCESS, "EOS 4.33.2F is not affected by this advisory."),
            ("DC1-SPINE2", AntaTestStatus.FAILURE, "EOS 4.31.6M is affected. OpenConfig tracing includes a risky selector."),
            ("DC2-LEAF1", AntaTestStatus.SUCCESS, "The device configuration is not affected by this advisory."),
            ("DC2-LEAF2", AntaTestStatus.SUCCESS, "EOS 4.30.10M is not affected by this advisory."),
        ],
    )
    _add_findings(
        manager,
        EXAMPLE_CRITICAL_ADVISORY,
        [
            ("DC1-LEAF1", AntaTestStatus.FAILURE, "Affected API is enabled and reachable from an untrusted network."),
            ("DC1-LEAF2", AntaTestStatus.SUCCESS, "The management API is restricted to the trusted management VRF."),
            ("DC1-LEAF3", AntaTestStatus.FAILURE, "Affected API is enabled without a control-plane ACL."),
            ("DC1-LEAF4", AntaTestStatus.SKIPPED, "Device was unreachable during test execution."),
            ("DC1-SPINE1", AntaTestStatus.SUCCESS, "Installed EOS release contains the security fix."),
            ("DC1-SPINE2", AntaTestStatus.FAILURE, "Affected release detected; management API exposure requires remediation."),
            ("DC2-LEAF1", AntaTestStatus.ERROR, "Management API configuration could not be parsed."),
            ("DC2-LEAF2", AntaTestStatus.FAILURE, "Affected API is exposed through the default VRF."),
        ],
    )
    _add_findings(
        manager,
        EXAMPLE_HIGH_ADVISORY,
        [
            ("DC1-LEAF1", AntaTestStatus.SUCCESS, "The affected service is disabled."),
            ("DC1-LEAF2", AntaTestStatus.SUCCESS, "Installed EOS release contains the security fix."),
            ("DC1-LEAF3", AntaTestStatus.SUCCESS, "The service is limited to a trusted interface."),
            ("DC1-LEAF4", AntaTestStatus.SKIPPED, "Device was unreachable during test execution."),
            ("DC1-SPINE1", AntaTestStatus.FAILURE, "Affected EOS release and exposed service detected."),
            ("DC1-SPINE2", AntaTestStatus.SUCCESS, "Installed EOS release contains the security fix."),
            ("DC2-LEAF1", AntaTestStatus.ERROR, "Service state could not be determined."),
            ("DC2-LEAF2", AntaTestStatus.SUCCESS, "The affected service is disabled."),
        ],
    )
    output = tmp_path / "advisories.md"
    sections = [
        (ANTASecurityAdvisoryReport, manager),
        (RunOverview, manager),
        (AdvisoryExposureSummary, manager),
        (SecurityAdvisoryDetails, manager),
    ]
    extra_data = {
        "anta_version": "2.0.0",
        "test_execution_start_time": datetime(2026, 8, 26, 14, 30, tzinfo=timezone.utc),
        "test_execution_end_time": datetime(2026, 8, 26, 14, 31, 12, 450000, tzinfo=timezone.utc),
        "total_duration": timedelta(minutes=1, seconds=12, milliseconds=450),
        "total_devices_in_inventory": 8,
        "devices_unreachable_at_setup": ["DC1-LEAF4"],
        "devices_filtered_at_setup": [],
        "filters_applied": {"tags": ["fabric", "security-advisory"], "tests": ["VerifySA117", "VerifySA120", "VerifySA121"]},
    }

    MDReportGenerator.generate_sections(sections, output, extra_data=extra_data)

    expected = (Path(__file__).parents[2] / "data" / "test_security_advisory_md_report.md").read_text(encoding="utf-8")
    assert output.read_text(encoding="utf-8") == expected


def test_group_advisory_results_rejects_conflicting_metadata() -> None:
    """Verify one advisory number cannot be rendered with conflicting metadata."""
    manager = ResultManager()
    manager.add(_result("leaf1", AntaTestStatus.SUCCESS, "No exposure detected."))
    manager.add(
        _result(
            "leaf2",
            AntaTestStatus.FAILURE,
            "Exposure detected.",
            advisory=ADVISORY.model_copy(update={"title": "Conflicting title"}),
        )
    )

    with pytest.raises(ValueError, match="Conflicting metadata"):
        group_advisory_results(manager)


def test_security_advisory_markdown_optional_content(tmp_path: Path) -> None:
    """Verify the report handles advisories without scores or published guidance."""
    advisory = ADVISORY.model_copy(
        update={
            "sa_number": "0002",
            "cves": (ADVISORY.cves[0].model_copy(update={"cvss_scores": ()}),),
            "mitigations": (ADVISORY.mitigations[0].model_copy(update={"url": None}),),
            "resolutions": (),
        }
    )
    manager = ResultManager()
    manager.add(_result("leaf1", AntaTestStatus.SUCCESS, "No exposure detected.", advisory))
    manager.add(_result("leaf2", AntaTestStatus.SUCCESS, "No exposure detected.", advisory.model_copy(update={"sa_number": "0001"})))
    output = tmp_path / "advisories.md"

    MDReportGenerator.generate_sections(
        [
            (ANTASecurityAdvisoryReport, manager),
            (SecurityAdvisoryDetails, manager),
        ],
        output,
        extra_data={"started_at": "2026-08-26"},
    )

    content = output.read_text(encoding="utf-8")
    assert "  - [Run Overview](#run-overview)" in content
    assert "| CVE-2026-0001 | Medium | - | - | - |" in content
    assert "- **Workaround:** Apply the temporary workaround." in content
    assert "[Reference]" not in content
    assert "*No resolutions are published for this advisory.*" in content

    standalone_output = tmp_path / "standalone-summary.md"
    MDReportGenerator.generate_sections([(AdvisoryExposureSummary, manager)], standalone_output)
    assert "[SA0001: Test advisory](#sa-0001)" in standalone_output.read_text(encoding="utf-8")
