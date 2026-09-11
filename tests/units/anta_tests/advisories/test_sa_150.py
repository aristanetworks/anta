# Copyright (c) 2026 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
# ruff: noqa: D102
# pylint: disable=duplicate-code, missing-function-docstring
"""Unit tests for Arista Security Advisory 150."""

from __future__ import annotations

import unittest
from typing import TYPE_CHECKING, Literal, TypeAlias

from anta._advisory.eos_versions import AffectedStatus, evaluate_version
from anta._advisory.facts.eos import EosVersionFact
from anta._advisory.facts.management import Dot1xControlledAuthenticatorFact
from anta._advisory.facts.models import (
    AvailableFact,
    CollectedFact,
    FactProblemKind,
    FactSource,
    FactSourceKind,
    FeatureName,
    FeatureState,
    FeatureValue,
    SubFeature,
)
from anta._advisory.facts.platform import PlatformIdentityFact
from anta._advisory.findings.models import ErrorResult, InconclusiveResult, NotAffectedResult
from anta._advisory.remediation import (
    AllOf,
    ChangeSoftwareVersion,
    ConditionalAction,
    FixedRelease,
    KnownFixedReleases,
    RemediationPlan,
    RunCommand,
    SoftwareTarget,
    software_version_plan,
)
from anta._eos.version import EOSVersion, parse_eos_version
from anta.result_manager.models import AntaTestStatus
from anta.tests.advisories.sa_150 import (
    ADVISORY,
    CVE_75943_AFFECTED_VERSIONS,
    CVE_75944_75945_AFFECTED_VERSIONS,
    CVE_77191_AFFECTED_VERSIONS,
    SA150,
    _assess_cve_75943,
    _assess_cve_75944,
    _assess_cve_75945,
    _assess_cve_77191,
)
from tests.units.anta_tests import build_eos_platform, build_eos_version, test

if TYPE_CHECKING:
    from anta._advisory.eos_versions import VersionRule
    from anta._eos.platform import PlatformIdentity
    from tests.units.anta_tests import AntaUnitTestData, AtomicResult, UnitTestResult

SOURCE = FactSource("unit test", FactSourceKind.DEVICE_METADATA)
ProductionStatus: TypeAlias = Literal[AntaTestStatus.SUCCESS, AntaTestStatus.FAILURE, AntaTestStatus.ERROR]
IssueExpectation: TypeAlias = tuple[ProductionStatus, str, RemediationPlan | None]
PHYSICAL_PLATFORM = "DCS-7050CX4-40D"
PLATFORM_INDICATION = f"platform '{PHYSICAL_PLATFORM}' is within the affected platform scope"
DOT1X_INDICATION = "the 802.1X controlled authenticator is enabled"
ACL_UNRESOLVED = "whether a static or dynamic ACL is assigned to the supplicant is external state"
EXPECTED_77191_RELEASES = (
    FixedRelease(EOSVersion(4, 35, 1, suffix="F")),
    FixedRelease(EOSVersion(4, 34, 6, suffix="M")),
    FixedRelease(EOSVersion(4, 33, 8, suffix="M")),
)
EXPECTED_75943_RELEASES = (
    FixedRelease(EOSVersion(4, 36, 2, suffix="F")),
    FixedRelease(EOSVersion(4, 35, 6, suffix="M")),
    FixedRelease(EOSVersion(4, 34, 8, suffix="M")),
    FixedRelease(EOSVersion(4, 33, 10, suffix="M")),
)
EXPECTED_75944_75945_RELEASES = (FixedRelease(EOSVersion(4, 36, 2, suffix="F")),)
EXPECTED_75945_REMEDIATION = RemediationPlan(
    AllOf(
        (
            ChangeSoftwareVersion(SoftwareTarget.EOS, EOSVersion(4, 36, 1, suffix="F"), KnownFixedReleases(EXPECTED_75944_75945_RELEASES)),
            ConditionalAction(
                "a supplicant remains authenticated after all 802.1X hosts are cleared",
                RunCommand(("clear dot1x host all",)),
            ),
        )
    )
)


def expected_remediation(releases: tuple[FixedRelease, ...], version: str) -> RemediationPlan:
    """Build an expected SA150 remediation independently from production constants."""
    return software_version_plan(releases, current_version=parse_eos_version(version).unwrap())


def expected_result(status: ProductionStatus, issues: tuple[IssueExpectation, ...]) -> UnitTestResult:
    """Build parent and per-vulnerability expectations."""
    parent_remediations = list(dict.fromkeys(remediation for _, _, remediation in issues if remediation is not None))
    atomic_results: list[AtomicResult] = []
    for vulnerability, (issue_status, message, remediation) in zip(ADVISORY.vulnerabilities, issues, strict=True):
        atomic_result: AtomicResult = {
            "description": f"Verify {vulnerability.id}.",
            "result": issue_status,
            "messages": [message],
        }
        if remediation is not None:
            atomic_result["remediation"] = remediation
        atomic_results.append(atomic_result)
    return {
        "result": status,
        "messages": [message for _, message, _ in issues],
        "remediations": parent_remediations,
        "atomic_results": atomic_results,
    }


def not_affected_version(version: str) -> str:
    """Return the standard outside-scope message."""
    return f"The device is not affected because EOS version '{version}' is outside the affected releases"


def inconclusive(version: str, unresolved: str = ACL_UNRESOLVED) -> str:
    """Return the expected shared SA150 inconclusive message."""
    return (
        "The assessment is inconclusive and the device may be affected. "
        f"Indications: EOS version '{version}' is affected, {PLATFORM_INDICATION}, and {DOT1X_INDICATION}. Unresolved: {unresolved}"
    )


def dot1x(*, controlled: bool) -> dict[str, object]:
    """Return effective 802.1X state."""
    return {"systemAuthControl": True, "interfaces": {"Ethernet1": {"portControl": "controlled" if controlled else "forceAuth"}}}


_DATA: AntaUnitTestData = {
    (SA150, "inconclusive-all-ural-issues"): {
        "version": build_eos_version("4.36.1F"),
        "platform": build_eos_platform(PHYSICAL_PLATFORM),
        "eos_data": [dot1x(controlled=True)],
        "expected": expected_result(
            AntaTestStatus.FAILURE,
            (
                (AntaTestStatus.SUCCESS, not_affected_version("4.36.1F"), None),
                (AntaTestStatus.FAILURE, inconclusive("4.36.1F"), expected_remediation(EXPECTED_75943_RELEASES, "4.36.1F")),
                (
                    AntaTestStatus.FAILURE,
                    inconclusive(
                        "4.36.1F",
                        f"{ACL_UNRESOLVED} and whether a stale ACL entry remains after supplicant re-authentication is device state not exposed",
                    ),
                    expected_remediation(EXPECTED_75944_75945_RELEASES, "4.36.1F"),
                ),
                (
                    AntaTestStatus.FAILURE,
                    inconclusive("4.36.1F"),
                    EXPECTED_75945_REMEDIATION,
                ),
            ),
        ),
    },
    (SA150, "inconclusive-older-two-issues"): {
        "version": build_eos_version("4.35.0.3F"),
        "platform": build_eos_platform(PHYSICAL_PLATFORM),
        "eos_data": [dot1x(controlled=True)],
        "expected": expected_result(
            AntaTestStatus.FAILURE,
            (
                (AntaTestStatus.FAILURE, inconclusive("4.35.0.3F"), expected_remediation(EXPECTED_77191_RELEASES, "4.35.0.3F")),
                (AntaTestStatus.FAILURE, inconclusive("4.35.0.3F"), expected_remediation(EXPECTED_75943_RELEASES, "4.35.0.3F")),
                (AntaTestStatus.SUCCESS, not_affected_version("4.35.0.3F"), None),
                (AntaTestStatus.SUCCESS, not_affected_version("4.35.0.3F"), None),
            ),
        ),
    },
    (SA150, "success-no-controlled-authenticator"): {
        "version": None,
        "platform": None,
        "eos_data": [dot1x(controlled=False)],
        "expected": expected_result(
            AntaTestStatus.SUCCESS,
            tuple((AntaTestStatus.SUCCESS, "The device is not affected because the 802.1X controlled authenticator is disabled", None) for _ in range(4)),
        ),
    },
    (SA150, "success-fixed-version"): {
        "version": build_eos_version("4.36.2F"),
        "platform": None,
        "eos_data": [{}],
        "expected": expected_result(
            AntaTestStatus.SUCCESS,
            tuple((AntaTestStatus.SUCCESS, not_affected_version("4.36.2F"), None) for _ in range(4)),
        ),
    },
    (SA150, "success-excluded-platform"): {
        "version": build_eos_version("4.36.1F"),
        "platform": build_eos_platform("vEOS"),
        "eos_data": [dot1x(controlled=True)],
        "expected": expected_result(
            AntaTestStatus.SUCCESS,
            (
                (AntaTestStatus.SUCCESS, not_affected_version("4.36.1F"), None),
                *tuple(
                    (AntaTestStatus.SUCCESS, "The device is not affected because platform 'vEOS' is outside the affected platform scope", None) for _ in range(3)
                ),
            ),
        ),
    },
    (SA150, "error-missing-version"): {
        "version": None,
        "platform": build_eos_platform(PHYSICAL_PLATFORM),
        "eos_data": [dot1x(controlled=True)],
        "expected": expected_result(
            AntaTestStatus.ERROR,
            tuple(
                (
                    AntaTestStatus.ERROR,
                    "The test could not determine the EOS version because it is missing from device metadata",
                    None,
                )
                for _ in range(4)
            ),
        ),
    },
    (SA150, "error-missing-platform-for-applicable-issues"): {
        "version": build_eos_version("4.36.1F"),
        "platform": None,
        "eos_data": [dot1x(controlled=True)],
        "expected": expected_result(
            AntaTestStatus.ERROR,
            (
                (AntaTestStatus.SUCCESS, not_affected_version("4.36.1F"), None),
                *tuple(
                    (
                        AntaTestStatus.ERROR,
                        "The test could not determine the platform identity because it is missing from device metadata",
                        None,
                    )
                    for _ in range(3)
                ),
            ),
        ),
    },
}


def version_fact(value: str) -> CollectedFact[EOSVersion]:
    """Build an EOS version fact."""
    parsed = parse_eos_version(value).unwrap()
    return EosVersionFact.available(parsed, SOURCE)


def platform_fact(value: str) -> AvailableFact[PlatformIdentity]:
    """Build a platform fact."""
    platform = build_eos_platform(value)
    assert platform is not None
    return PlatformIdentityFact.available(platform, SOURCE)


def dot1x_fact(state: FeatureState) -> AvailableFact[FeatureValue]:
    """Build an 802.1X fact."""
    return Dot1xControlledAuthenticatorFact.available(FeatureValue(SubFeature(FeatureName.DOT1X, "controlled authenticator"), state), SOURCE)


class TestSA150VersionMatrices(unittest.TestCase):
    """Validate every source-published version boundary independently."""

    def test_version_boundaries(self) -> None:
        matrices: tuple[tuple[tuple[VersionRule, ...], tuple[tuple[str, AffectedStatus], ...]], ...] = (
            (
                CVE_77191_AFFECTED_VERSIONS,
                (
                    ("4.35.0.3F", AffectedStatus.AFFECTED),
                    ("4.35.0.99F", AffectedStatus.AFFECTED),
                    ("4.35.1F", AffectedStatus.NOT_AFFECTED),
                    ("4.34.5M", AffectedStatus.AFFECTED),
                    ("4.34.6M", AffectedStatus.NOT_AFFECTED),
                    ("4.33.7.1M", AffectedStatus.AFFECTED),
                    ("4.33.7.99M", AffectedStatus.AFFECTED),
                    ("4.33.8M", AffectedStatus.NOT_AFFECTED),
                    ("4.32.99M", AffectedStatus.AFFECTED),
                ),
            ),
            (
                CVE_75943_AFFECTED_VERSIONS,
                (
                    ("4.36.1F", AffectedStatus.AFFECTED),
                    ("4.36.2F", AffectedStatus.NOT_AFFECTED),
                    ("4.35.5M", AffectedStatus.AFFECTED),
                    ("4.35.6M", AffectedStatus.NOT_AFFECTED),
                    ("4.34.7.1M", AffectedStatus.AFFECTED),
                    ("4.34.7.99M", AffectedStatus.AFFECTED),
                    ("4.34.8M", AffectedStatus.NOT_AFFECTED),
                    ("4.33.9M", AffectedStatus.AFFECTED),
                    ("4.33.10M", AffectedStatus.NOT_AFFECTED),
                    ("4.32.99M", AffectedStatus.AFFECTED),
                ),
            ),
            (
                CVE_75944_75945_AFFECTED_VERSIONS,
                (
                    ("4.36.0F", AffectedStatus.NOT_AFFECTED),
                    ("4.36.1F", AffectedStatus.AFFECTED),
                    ("4.36.1.99F", AffectedStatus.AFFECTED),
                    ("4.36.2F", AffectedStatus.NOT_AFFECTED),
                    ("4.35.99M", AffectedStatus.NOT_AFFECTED),
                ),
            ),
        )
        for matrix, cases in matrices:
            for version, expected in cases:
                with self.subTest(matrix=matrix, version=version):
                    parsed = parse_eos_version(version).unwrap()
                    assert evaluate_version(parsed, matrix).affected_status is expected


class TestSA150Assessment(unittest.TestCase):
    """Validate shared and vulnerability-specific assessment branches."""

    def test_applicable_vulnerabilities_are_inconclusive(self) -> None:
        version = version_fact("4.36.1F")
        platform = platform_fact(PHYSICAL_PLATFORM)
        enabled = dot1x_fact(FeatureState.ENABLED)

        assert isinstance(_assess_cve_77191(version, platform, enabled), NotAffectedResult)
        assert isinstance(_assess_cve_75943(version, platform, enabled), InconclusiveResult)
        assert isinstance(_assess_cve_75944(version, platform, enabled), InconclusiveResult)
        cve_75945 = _assess_cve_75945(version, platform, enabled)
        assert isinstance(cve_75945, InconclusiveResult)
        assert cve_75945.remediation == EXPECTED_75945_REMEDIATION

    def test_unaffected_platforms(self) -> None:
        version = version_fact("4.36.1F")
        enabled = dot1x_fact(FeatureState.ENABLED)
        for platform in ("AWE-5310", "AWE-7210R", "CloudEOS", "cEOSLab", "vEOS"):
            with self.subTest(platform=platform):
                assert isinstance(_assess_cve_75943(version, platform_fact(platform), enabled), NotAffectedResult)

    def test_unknown_platform_is_error(self) -> None:
        version = version_fact("4.36.1F")
        enabled = dot1x_fact(FeatureState.ENABLED)

        assert isinstance(_assess_cve_75943(version, platform_fact("DCS-UNRECOGNIZED"), enabled), ErrorResult)

    def test_disabled_and_unavailable_dot1x(self) -> None:
        version = version_fact("4.36.1F")
        platform = platform_fact(PHYSICAL_PLATFORM)
        disabled = dot1x_fact(FeatureState.DISABLED)
        unavailable = Dot1xControlledAuthenticatorFact.unavailable(FactProblemKind.MALFORMED, SOURCE)

        assert isinstance(_assess_cve_75943(version, platform, disabled), NotAffectedResult)
        assert isinstance(_assess_cve_75943(version, platform, unavailable), ErrorResult)
