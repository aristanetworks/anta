# Copyright (c) 2026 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Shared realistic data for security advisory reporter tests.

Regenerate the checked-in reports with ``uv run python -m tests.units._advisory.generate_report_fixtures``.
"""

from __future__ import annotations

from datetime import date
from typing import TYPE_CHECKING, cast

from anta._advisory.models import _AdvisoryMetadata, _AdvisoryVulnerability, _AdvisoryVulnerabilitySeverity
from anta._advisory.remediation import OperationalAction, RemediationGuidance, RemediationPlan, software_version_plan
from anta._advisory.results import _AdvisoryTestResult
from anta._eos.version import EOSVersion
from anta.result_manager import ResultManager
from anta.result_manager.models import AntaTestStatus
from anta.tests.advisories.sa_117 import FIXED_RELEASES as SA117_FIXED_RELEASES
from anta.tests.advisories.sa_117 import VerifySA117
from anta.tests.advisories.sa_146 import EOS_FIXED_RELEASES as SA146_EOS_FIXED_RELEASES
from anta.tests.advisories.sa_146 import VerifySA146
from anta.tests.advisories.sa_147 import VerifySA147

if TYPE_CHECKING:
    from collections.abc import Iterable

SA117_ADVISORY = cast("_AdvisoryMetadata", vars(VerifySA117)["advisory"])
SA146_ADVISORY = cast("_AdvisoryMetadata", vars(VerifySA146)["advisory"])
SA147_ADVISORY = cast("_AdvisoryMetadata", vars(VerifySA147)["advisory"])
RENDERING_COVERAGE_ADVISORY = _AdvisoryMetadata(
    sa_number="9999",
    title="Reporter Rendering Coverage Advisory",
    last_updated=date(2026, 1, 1),
    vulnerabilities=(
        _AdvisoryVulnerability(
            id="TEST-LOW-SEVERITY",
            severity=_AdvisoryVulnerabilitySeverity.LOW,
            description="Synthetic low-severity vulnerability used to verify report rendering.",
        ),
        _AdvisoryVulnerability(
            id="TEST-UNKNOWN-SEVERITY",
            severity=_AdvisoryVulnerabilitySeverity.UNKNOWN,
            description="Synthetic unknown-severity vulnerability used to verify report rendering.",
        ),
    ),
    url="https://example.com/security-advisory-rendering-coverage",
    description=(
        "This fictional advisory exists only to exercise low and unknown severity report rendering, which published ANTA advisory tests do not currently use."
    ),
)
_PUBLISHED_TEST_METADATA = {
    SA117_ADVISORY.sa_number: (VerifySA117.__name__, VerifySA117.description),
    SA146_ADVISORY.sa_number: (VerifySA146.__name__, VerifySA146.description),
    SA147_ADVISORY.sa_number: (VerifySA147.__name__, VerifySA147.description),
}


def build_security_advisory_result(
    name: str,
    status: AntaTestStatus,
    message: str,
    advisory: _AdvisoryMetadata,
) -> _AdvisoryTestResult:
    """Create a security advisory result for reporter tests."""
    test_name, description = _PUBLISHED_TEST_METADATA.get(
        advisory.sa_number,
        (f"VerifySA{int(advisory.sa_number)}", f"Verify that the device is not exposed to Arista Security Advisory {advisory.sa_number}."),
    )
    return _AdvisoryTestResult(
        name=name,
        test=test_name,
        categories=["advisories"],
        description=description,
        result=status,
        messages=[message],
        advisory=advisory,
    )


def _add_findings(
    manager: ResultManager,
    advisory: _AdvisoryMetadata,
    findings: Iterable[tuple[str, AntaTestStatus, str]],
) -> list[_AdvisoryTestResult]:
    """Add realistic per-device findings for one advisory."""
    results = []
    for device, status, message in findings:
        result = build_security_advisory_result(device, status, message, advisory)
        manager.add(result)
        results.append(result)
    return results


def build_security_advisory_result_manager() -> ResultManager:
    """Build the shared 3-published-advisory, 8-device reporter dataset with one rendering-only advisory."""
    manager = ResultManager()
    _add_findings(
        manager,
        SA117_ADVISORY,
        [
            (
                "DC1-LEAF1",
                AntaTestStatus.INCONCLUSIVE,
                (
                    "The assessment is inconclusive and the device may be affected because EOS version '4.32.4M' has an enabled gNMI transport "
                    "with accounting enabled, but the gNOI File and effective gNSI Authz controls cannot be determined."
                ),
            ),
            ("DC1-LEAF2", AntaTestStatus.SUCCESS, "EOS 4.32.5M is not affected by this advisory."),
            ("DC1-LEAF3", AntaTestStatus.ERROR, "The EOS version could not be determined from the available command output."),
            ("DC1-LEAF4", AntaTestStatus.SKIPPED, "Device was unreachable during test execution."),
            ("DC1-SPINE1", AntaTestStatus.SUCCESS, "EOS 4.33.2F is not affected by this advisory."),
            (
                "DC1-SPINE2",
                AntaTestStatus.INCONCLUSIVE,
                (
                    "The assessment is inconclusive and the device may be affected because EOS version '4.31.6M' has an enabled gNMI transport and OpenConfig "
                    "tracing includes a selector identified by the advisory, but the gNOI File and effective gNSI Authz controls cannot be determined."
                ),
            ),
            ("DC2-LEAF1", AntaTestStatus.SUCCESS, "The device configuration is not affected by this advisory."),
            ("DC2-LEAF2", AntaTestStatus.SUCCESS, "EOS 4.30.10M is not affected by this advisory."),
        ],
    )
    sa147_results = _add_findings(
        manager,
        SA147_ADVISORY,
        [
            ("DC1-LEAF1", AntaTestStatus.FAILURE, "The device is affected because openssh-server '9.9p1' is affected and SSH accepts connections."),
            ("DC1-LEAF2", AntaTestStatus.SUCCESS, "The device is not affected because its EOS version is outside the published affected range."),
            ("DC1-LEAF3", AntaTestStatus.FAILURE, "The device is affected because openssh-server '9.8p1' is affected and SSH accepts connections."),
            ("DC1-LEAF4", AntaTestStatus.SKIPPED, "Device was unreachable during test execution."),
            ("DC1-SPINE1", AntaTestStatus.SUCCESS, "The device is not affected because openssh-clients and openssh-server '10.4p1' are fixed."),
            ("DC1-SPINE2", AntaTestStatus.FAILURE, "The device is affected because openssh-server '9.9p2' is affected and SSH accepts connections."),
            ("DC2-LEAF1", AntaTestStatus.ERROR, "The openssh-clients package version could not be determined from 'show version detail'."),
            ("DC2-LEAF2", AntaTestStatus.FAILURE, "The device is affected because openssh-server '9.7p1' is affected and SSH accepts connections."),
        ],
    )
    sa147_results[0].add(
        "Verify CVE-2026-59995.",
        AntaTestStatus.INCONCLUSIVE,
        [
            (
                "The assessment is inconclusive and the device may be affected because openssh-clients '9.9p1' is affected, "
                "but operator-initiated SFTP use with an untrusted server cannot be determined."
            )
        ],
        vulnerability_ids=("CVE-2026-59995",),
    )
    sa147_results[0].add(
        "Verify CVE-2026-59996.",
        AntaTestStatus.INCONCLUSIVE,
        [
            (
                "The assessment is inconclusive and the device may be affected because openssh-clients '9.9p1' is affected, "
                "but operator-initiated SCP remote-to-remote use with an untrusted server cannot be determined."
            )
        ],
        vulnerability_ids=("CVE-2026-59996",),
    )
    sa147_results[0].add(
        "Verify CVE-2026-60001.",
        AntaTestStatus.FAILURE,
        ["The device is affected because openssh-server '9.9p1' is affected and SSH accepts connections."],
        vulnerability_ids=("CVE-2026-60001",),
    )
    sa147_results[0].add(
        "Verify CVE-2026-60002.",
        AntaTestStatus.INCONCLUSIVE,
        ["The device is affected but mitigated because openssh-clients '9.9p1' uses strict host-key checking."],
        vulnerability_ids=("CVE-2026-60002",),
    )
    _add_findings(
        manager,
        SA146_ADVISORY,
        [
            ("DC1-LEAF1", AntaTestStatus.SUCCESS, "The device is not affected because no enabled gRPC server is on an affected software version."),
            ("DC1-LEAF2", AntaTestStatus.SUCCESS, "The device is not affected because no enabled gRPC server is on an affected software version."),
            ("DC1-LEAF3", AntaTestStatus.SUCCESS, "The device is not affected because no enabled gRPC server is on an affected software version."),
            ("DC1-LEAF4", AntaTestStatus.SKIPPED, "Device was unreachable during test execution."),
            ("DC1-SPINE1", AntaTestStatus.FAILURE, "The device is affected because vulnerable gRPC server path(s) are enabled without complete mTLS: gNMI."),
            ("DC1-SPINE2", AntaTestStatus.SUCCESS, "The device is not affected because no enabled gRPC server is on an affected software version."),
            ("DC2-LEAF1", AntaTestStatus.ERROR, "The following required evidence is unavailable or invalid: gRIBI enabled state."),
            ("DC2-LEAF2", AntaTestStatus.SUCCESS, "The device is not affected because no enabled gRPC server is on an affected software version."),
        ],
    )
    rendering_results = _add_findings(
        manager,
        RENDERING_COVERAGE_ADVISORY,
        [("DC1-LEAF1", AntaTestStatus.INCONCLUSIVE, "Synthetic result used only to verify low and unknown severity report rendering.")],
    )
    rendering_results[0].add(
        "Verify low-severity rendering.",
        AntaTestStatus.SUCCESS,
        ["Synthetic low-severity rendering check passed."],
        vulnerability_ids=("TEST-LOW-SEVERITY",),
    )
    rendering_results[0].add(
        "Verify unknown-severity rendering.",
        AntaTestStatus.INCONCLUSIVE,
        ["Synthetic unknown-severity rendering check is inconclusive."],
        vulnerability_ids=("TEST-UNKNOWN-SEVERITY",),
    )
    return manager


def build_security_advisory_md_result_manager() -> ResultManager:
    """Build the shared reporter dataset with Markdown-only SA117 remediation examples."""
    manager = build_security_advisory_result_manager()
    sa117_remediations = {
        "DC1-LEAF1": software_version_plan(SA117_FIXED_RELEASES, current_version=EOSVersion(4, 32, 4, suffix="M")),
        "DC1-SPINE2": software_version_plan(SA117_FIXED_RELEASES, current_version=EOSVersion(4, 31, 6, suffix="M")),
    }
    inconclusive_guidance = frozenset(
        {
            RemediationGuidance.NEW_RELEASES,
            RemediationGuidance.CURRENT_MITIGATIONS,
            RemediationGuidance.UNRESOLVED_CONDITIONS,
        }
    )
    for result in manager.results:
        if not isinstance(result, _AdvisoryTestResult):
            continue
        advisory_result = cast("_AdvisoryTestResult", result)
        if advisory_result.advisory.sa_number == "0117":
            if advisory_result.name in sa117_remediations:
                vulnerability = advisory_result.advisory.vulnerabilities[0]
                advisory_result.add(
                    f"Verify {vulnerability.id}.",
                    AntaTestStatus.INCONCLUSIVE,
                    ["The assessment is inconclusive because required gNOI File and gNSI Authz evidence is unavailable."],
                    vulnerability_ids=(vulnerability.id,),
                    remediation=sa117_remediations[advisory_result.name],
                    remediation_guidance=inconclusive_guidance,
                )
            elif advisory_result.result is AntaTestStatus.ERROR:
                advisory_result.add(
                    "Collect valid device evidence.",
                    AntaTestStatus.ERROR,
                    remediation=RemediationPlan(OperationalAction("Collect or correct valid refreshed device EOS version metadata and rerun the test.")),
                )
            elif advisory_result.result is AntaTestStatus.SKIPPED:
                advisory_result.add(
                    "Restore device reachability.",
                    AntaTestStatus.SKIPPED,
                    remediation=RemediationPlan(OperationalAction("Restore device reachability and rerun the test.")),
                )
        if advisory_result.advisory.sa_number == "0146" and advisory_result.name == "DC1-SPINE1":
            vulnerability = advisory_result.advisory.vulnerabilities[0]
            remediation = software_version_plan(SA146_EOS_FIXED_RELEASES, current_version=EOSVersion(4, 35, 1, suffix="F"))
            advisory_result.add(
                f"Verify {vulnerability.id}.",
                AntaTestStatus.FAILURE,
                ["The device is affected because vulnerable gRPC server path(s) are enabled without complete mTLS: gNMI."],
                vulnerability_ids=(vulnerability.id,),
                remediation=remediation,
                remediation_guidance=frozenset({RemediationGuidance.NEW_RELEASES, RemediationGuidance.CURRENT_MITIGATIONS}),
            )
    return manager
