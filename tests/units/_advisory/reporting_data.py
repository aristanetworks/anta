# Copyright (c) 2026 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Shared realistic data for security advisory reporter tests."""

from __future__ import annotations

from datetime import date
from typing import TYPE_CHECKING, cast

from anta._advisory.models import (
    _AdvisoryMetadata,
    _AdvisoryVulnerability,
    _AdvisoryVulnerabilitySeverity,
)
from anta._advisory.results import _AdvisoryTestResult
from anta.result_manager import ResultManager
from anta.result_manager.models import AntaTestStatus
from anta.tests.advisories.sa_117 import VerifySA117

if TYPE_CHECKING:
    from collections.abc import Iterable

SA117_ADVISORY = cast("_AdvisoryMetadata", vars(VerifySA117)["advisory"])

EXAMPLE_CRITICAL_ADVISORY = _AdvisoryMetadata(
    sa_number="0120",
    title="Example Management API Authentication Bypass",
    last_updated=date(2026, 1, 1),
    vulnerabilities=(
        _AdvisoryVulnerability(
            id="CVE-2026-12001",
            severity=_AdvisoryVulnerabilitySeverity.CRITICAL,
            description="Authentication bypass in an enabled management API.",
        ),
        _AdvisoryVulnerability(
            id="GHSA-2345-6789-cfgh",
            severity=_AdvisoryVulnerabilitySeverity.HIGH,
            description="Authorization flaw affecting management API access controls.",
        ),
    ),
    url="https://www.arista.com/en/support/advisories-notices/security-advisory/example-0120",
    description=(
        "An example vulnerability in an enabled management API could allow an unauthenticated remote actor to bypass authentication under specific configurations. "
        "This fictional advisory is used only to exercise realistic report rendering."
    ),
)

EXAMPLE_HIGH_ADVISORY = _AdvisoryMetadata(
    sa_number="0121",
    title="Example EOS Process Denial of Service",
    last_updated=date(2026, 1, 1),
    vulnerabilities=(
        _AdvisoryVulnerability(
            id="GTI-EXAMPLE-12101",
            severity=_AdvisoryVulnerabilitySeverity.HIGH,
            description="Malformed packet may restart an exposed EOS process.",
        ),
    ),
    url="https://www.arista.com/en/support/advisories-notices/security-advisory/example-0121",
    description=(
        "An example malformed packet could restart an EOS process when received on an exposed service. "
        "This fictional advisory demonstrates a larger fleet with mixed findings and no published mitigation."
    ),
)


def build_security_advisory_result(
    name: str,
    status: AntaTestStatus,
    message: str,
    advisory: _AdvisoryMetadata,
    *,
    remediations: list[str] | None = None,
) -> _AdvisoryTestResult:
    """Create a security advisory result for reporter tests."""
    return _AdvisoryTestResult(
        name=name,
        test=f"VerifySA{int(advisory.sa_number)}",
        categories=["advisories"],
        description=f"Verify that the device is not exposed to Arista Security Advisory {advisory.sa_number}.",
        result=status,
        messages=[message],
        advisory=advisory,
        remediations=remediations or [],
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
    """Build the shared 3-advisory, 8-device reporter dataset."""
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
    critical_results = _add_findings(
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
    critical_results[0].add(
        "Verify CVE-2026-12001.",
        AntaTestStatus.FAILURE,
        ["The device is affected because the vulnerable management API is enabled."],
        vulnerability_ids=("CVE-2026-12001",),
    )
    critical_results[0].add(
        "External network reachability",
        AntaTestStatus.INCONCLUSIVE,
        ["The assessment is inconclusive because external reachability could not be verified."],
    )
    critical_results[0].add(
        "Verify GHSA-2345-6789-cfgh.",
        AntaTestStatus.SUCCESS,
        ["The device is not affected by this issue because authorization controls are enabled."],
        vulnerability_ids=("GHSA-2345-6789-cfgh",),
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
    return manager


def build_security_advisory_md_result_manager() -> ResultManager:
    """Build the shared reporter dataset with Markdown-only SA117 remediation examples."""
    manager = build_security_advisory_result_manager()
    sa121_markdown_advisory = EXAMPLE_HIGH_ADVISORY.model_copy(
        update={
            "vulnerabilities": (
                *EXAMPLE_HIGH_ADVISORY.vulnerabilities,
                _AdvisoryVulnerability(
                    id="CVE-2026-12102",
                    severity=_AdvisoryVulnerabilitySeverity.LOW,
                    description="Low-impact information disclosure in process diagnostics.",
                ),
                _AdvisoryVulnerability(
                    id="CVE-2026-12103",
                    severity=_AdvisoryVulnerabilitySeverity.UNKNOWN,
                    description="Process behavior with severity pending assessment.",
                ),
            )
        }
    )
    remediations = {
        AntaTestStatus.INCONCLUSIVE: ["Upgrade to a fixed EOS release when one is published, then rerun the test."],
        AntaTestStatus.ERROR: ["Collect valid EOS version evidence and rerun the test."],
        AntaTestStatus.SKIPPED: ["Restore device reachability and rerun the test."],
    }
    for result in manager.results:
        if isinstance(result, _AdvisoryTestResult) and result.advisory.sa_number == "0117":
            result.remediations = remediations.get(result.result, [])
            if result.name == "DC1-LEAF1":
                vulnerability = result.advisory.vulnerabilities[0]
                result.add(
                    f"Verify {vulnerability.id}.",
                    AntaTestStatus.INCONCLUSIVE,
                    ["The assessment is inconclusive because required gNOI File and gNSI Authz evidence is unavailable."],
                    vulnerability_ids=(vulnerability.id,),
                    remediations=remediations[AntaTestStatus.INCONCLUSIVE],
                )
        if isinstance(result, _AdvisoryTestResult) and result.advisory.sa_number == "0121":
            result.advisory = sa121_markdown_advisory
        if isinstance(result, _AdvisoryTestResult) and result.advisory.sa_number == "0121" and result.name == "DC1-SPINE1":
            high_vulnerability, low_vulnerability, unknown_vulnerability = result.advisory.vulnerabilities
            remediation = "Disable or restrict the exposed service and upgrade to a fixed EOS release."
            result.remediations = [remediation]
            result.add(
                f"Verify {high_vulnerability.id}.",
                AntaTestStatus.FAILURE,
                ["The device is affected because an affected EOS release and exposed service were detected."],
                vulnerability_ids=(high_vulnerability.id,),
                remediations=[remediation],
            )
            result.add(
                f"Verify {low_vulnerability.id}.",
                AntaTestStatus.SUCCESS,
                ["The device is not affected by the low-severity issue because process diagnostics are restricted."],
                vulnerability_ids=(low_vulnerability.id,),
                remediations=["Keep process diagnostics restricted to trusted operators."],
            )
            result.add(
                f"Verify {unknown_vulnerability.id}.",
                AntaTestStatus.INCONCLUSIVE,
                ["The assessment is inconclusive because the severity and affected conditions are still being investigated."],
                vulnerability_ids=(unknown_vulnerability.id,),
                remediations=["Monitor the advisory for updated severity and remediation guidance."],
            )
    return manager
