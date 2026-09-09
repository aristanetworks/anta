# Copyright (c) 2026 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Unit tests for Arista Security Advisory 160."""

from __future__ import annotations

from typing import TYPE_CHECKING, Literal, TypeAlias

from anta._advisory.eos_versions import AffectedStatus
from anta._advisory.facts.eos import EosVersionFact
from anta._advisory.facts.models import AvailableFact, FeatureName, FeatureState, FeatureValue, SubFeature
from anta._advisory.facts.routing import IsisConfiguredFact, IsisNonPassiveBroadcastInterfaceFact
from anta._advisory.findings.models import AffectedResult, ErrorResult, InconclusiveResult, NotAffectedResult
from anta._advisory.remediation import FixedRelease, RemediationPlan, software_version_plan
from anta._eos.version import EOSVersion
from anta.result_manager.models import AntaTestStatus
from anta.tests.advisories.sa_160 import (
    ADVISORY,
    BROADCAST_AFFECTED_VERSIONS,
    LSP_AND_GRACEFUL_RESTART_AFFECTED_VERSIONS,
    LSP_AND_GRACEFUL_RESTART_FIXED_RELEASES,
    SA160,
    _assess_broadcast_issue,
    _assess_isis_issue,
)
from tests.units.anta_tests import build_eos_version, test
from tests.units.anta_tests.advisories.fact_builders import assert_version_statuses, available_fact, eos_version_fact, unavailable_fact

if TYPE_CHECKING:
    from tests.units.anta_tests import AntaUnitTestData, AtomicResult, UnitTestResult

Status: TypeAlias = Literal[AntaTestStatus.SUCCESS, AntaTestStatus.FAILURE, AntaTestStatus.ERROR]
Issue: TypeAlias = tuple[Status, str, RemediationPlan | None]
BROADCAST_RELEASES = (
    FixedRelease(EOSVersion(4, 36, 2, suffix="F")),
    FixedRelease(EOSVersion(4, 35, 6, suffix="M")),
    FixedRelease(EOSVersion(4, 34, 8, suffix="M")),
    FixedRelease(EOSVersion(4, 33, 10, suffix="M")),
)
LSP_AND_GRACEFUL_RESTART_RELEASES = (FixedRelease(EOSVersion(4, 36, 2, suffix="F")),)
BROADCAST_REMEDIATION = software_version_plan(BROADCAST_RELEASES, current_version=EOSVersion(4, 36, 1, suffix="F"))
LSP_AND_GRACEFUL_RESTART_REMEDIATION = software_version_plan(
    LSP_AND_GRACEFUL_RESTART_RELEASES,
    current_version=EOSVersion(4, 36, 1, suffix="F"),
)
OLD_BROADCAST_REMEDIATION = software_version_plan(BROADCAST_RELEASES, current_version=EOSVersion(4, 35, 5, suffix="M"))


def isis_fact(state: FeatureState) -> AvailableFact[FeatureValue]:
    """Build normalized IS-IS configuration state for direct assessment tests."""
    return available_fact(IsisConfiguredFact, FeatureValue(FeatureName.ISIS, state))


def isis_interface_fact(state: FeatureState) -> AvailableFact[FeatureValue]:
    """Build normalized modeled IS-IS broadcast-interface state."""
    return available_fact(
        IsisNonPassiveBroadcastInterfaceFact,
        FeatureValue(SubFeature(FeatureName.ISIS, "non-passive broadcast interface"), state),
    )


def test_sa160_assessment_contract() -> None:
    """Apply the issue-specific prerequisite and version matrix to typed facts."""
    vulnerability_id = "CVE-2026-73459"
    assert isinstance(
        _assess_isis_issue(
            vulnerability_id,
            unavailable_fact(EosVersionFact),
            isis_fact(FeatureState.DISABLED),
            LSP_AND_GRACEFUL_RESTART_AFFECTED_VERSIONS,
            LSP_AND_GRACEFUL_RESTART_FIXED_RELEASES,
        ),
        NotAffectedResult,
    )
    assert isinstance(
        _assess_isis_issue(
            vulnerability_id,
            eos_version_fact("4.36.1F"),
            isis_fact(FeatureState.ENABLED),
            LSP_AND_GRACEFUL_RESTART_AFFECTED_VERSIONS,
            LSP_AND_GRACEFUL_RESTART_FIXED_RELEASES,
        ),
        AffectedResult,
    )
    assert isinstance(
        _assess_isis_issue(
            vulnerability_id,
            eos_version_fact("4.36.2F"),
            isis_fact(FeatureState.ENABLED),
            LSP_AND_GRACEFUL_RESTART_AFFECTED_VERSIONS,
            LSP_AND_GRACEFUL_RESTART_FIXED_RELEASES,
        ),
        NotAffectedResult,
    )
    assert isinstance(
        _assess_isis_issue(
            vulnerability_id,
            unavailable_fact(EosVersionFact),
            isis_fact(FeatureState.ENABLED),
            LSP_AND_GRACEFUL_RESTART_AFFECTED_VERSIONS,
            LSP_AND_GRACEFUL_RESTART_FIXED_RELEASES,
        ),
        ErrorResult,
    )


def test_sa160_broadcast_assessment_contract() -> None:
    """Apply confirmed, absent, unresolved, fixed-release, and unavailable broadcast evidence."""
    assert isinstance(
        _assess_broadcast_issue(
            eos_version_fact("4.35.5M"),
            isis_interface_fact(FeatureState.ENABLED),
            isis_fact(FeatureState.ENABLED),
        ),
        AffectedResult,
    )
    assert isinstance(
        _assess_broadcast_issue(
            unavailable_fact(EosVersionFact),
            isis_interface_fact(FeatureState.DISABLED),
            isis_fact(FeatureState.DISABLED),
        ),
        NotAffectedResult,
    )
    assert isinstance(
        _assess_broadcast_issue(
            eos_version_fact("4.35.5M"),
            isis_interface_fact(FeatureState.DISABLED),
            isis_fact(FeatureState.ENABLED),
        ),
        InconclusiveResult,
    )
    assert isinstance(
        _assess_broadcast_issue(
            eos_version_fact("4.35.6M"),
            isis_interface_fact(FeatureState.DISABLED),
            isis_fact(FeatureState.ENABLED),
        ),
        NotAffectedResult,
    )
    assert isinstance(
        _assess_broadcast_issue(
            eos_version_fact("4.35.5M"),
            unavailable_fact(IsisNonPassiveBroadcastInterfaceFact),
            isis_fact(FeatureState.ENABLED),
        ),
        ErrorResult,
    )
    assert isinstance(
        _assess_broadcast_issue(
            eos_version_fact("4.35.5M"),
            isis_interface_fact(FeatureState.DISABLED),
            unavailable_fact(IsisConfiguredFact),
        ),
        ErrorResult,
    )


def test_sa160_version_boundaries() -> None:
    """Cover the independent source boundaries for the broadcast and newer issues."""
    assert_version_statuses(
        BROADCAST_AFFECTED_VERSIONS,
        (
            ("4.36.1F", AffectedStatus.AFFECTED),
            ("4.36.2F", AffectedStatus.NOT_AFFECTED),
            ("4.35.5M", AffectedStatus.AFFECTED),
            ("4.35.6M", AffectedStatus.NOT_AFFECTED),
            ("4.34.7.1M", AffectedStatus.AFFECTED),
            ("4.34.7.99M", AffectedStatus.AFFECTED),
            ("4.33.9M", AffectedStatus.AFFECTED),
            ("4.33.10M", AffectedStatus.NOT_AFFECTED),
            ("4.31.99M", AffectedStatus.AFFECTED),
            ("4.30.99M", AffectedStatus.NOT_AFFECTED),
        ),
    )
    assert_version_statuses(
        LSP_AND_GRACEFUL_RESTART_AFFECTED_VERSIONS,
        (
            ("4.36.1F", AffectedStatus.AFFECTED),
            ("4.36.2F", AffectedStatus.NOT_AFFECTED),
            ("4.35.99M", AffectedStatus.NOT_AFFECTED),
        ),
    )


ISIS_EMPTY = {"vrfs": {"default": {"isisInstances": {}}}}
ISIS_INTERFACE_ABSENT = ISIS_EMPTY
ISIS_INTERFACE_OMITS_DOWN = {"vrfs": {"default": {"isisInstances": {"1": {"interfaces": {}}}}}}
ISIS_BROADCAST = {
    "vrfs": {
        "default": {
            "isisInstances": {
                "1": {
                    "interfaces": {
                        "Ethernet1": {
                            "enabled": True,
                            "mtu": 1497,
                            "interfaceType": "broadcast",
                            "intfLevels": {"1": {"numAdjacencies": 0, "passive": False}},
                        }
                    }
                }
            }
        }
    }
}
ISIS_CONFIGURED = {"vrfs": {"default": {"isisInstances": {"1": {"enabled": True}}}}}
ISIS_GRACEFUL_RESTART = {"vrfs": {"default": {"isisInstances": {"1": {"gracefulRestart": "enabled"}}}}}
ISIS_GRACEFUL_RESTART_NON_DEFAULT = {
    "vrfs": {
        "default": {"isisInstances": {"1": {"gracefulRestart": "disabled"}}},
        "TOTO": {"isisInstances": {"BLAH2": {"gracefulRestart": "enabled"}}},
    }
}


def expected_result(status: Status, issues: tuple[Issue, ...]) -> UnitTestResult:
    """Build parent and per-vulnerability expectations."""
    # pylint: disable=duplicate-code
    atomic_results: list[AtomicResult] = []
    for vulnerability, (issue_status, message, remediation) in zip(ADVISORY.vulnerabilities, issues, strict=True):
        atomic: AtomicResult = {"description": f"Verify {vulnerability.id}.", "result": issue_status, "messages": [message]}
        if remediation is not None:
            atomic["remediation"] = remediation
        atomic_results.append(atomic)
    return {
        "result": status,
        "messages": [message for _, message, _ in issues],
        "remediations": list(dict.fromkeys(remediation for _, _, remediation in issues if remediation is not None)),
        "atomic_results": atomic_results,
    }
    # pylint: enable=duplicate-code


DATA: AntaUnitTestData = {
    (SA160, "failure-all-three-issues"): {
        "version": build_eos_version("4.36.1F"),
        "eos_data": [ISIS_BROADCAST, ISIS_CONFIGURED, ISIS_GRACEFUL_RESTART],
        "expected": expected_result(
            AntaTestStatus.FAILURE,
            (
                (AntaTestStatus.FAILURE, "IS-IS non-passive broadcast interface is enabled", BROADCAST_REMEDIATION),
                (AntaTestStatus.FAILURE, "IS-IS feature is enabled", LSP_AND_GRACEFUL_RESTART_REMEDIATION),
                (AntaTestStatus.FAILURE, "IS-IS graceful restart is enabled", LSP_AND_GRACEFUL_RESTART_REMEDIATION),
            ),
        ),
    },
    (SA160, "failure-only-older-broadcast-issue"): {
        "version": build_eos_version("4.35.5M"),
        "eos_data": [ISIS_BROADCAST, ISIS_CONFIGURED, ISIS_GRACEFUL_RESTART],
        "expected": expected_result(
            AntaTestStatus.FAILURE,
            (
                (AntaTestStatus.FAILURE, "IS-IS non-passive broadcast interface is enabled", OLD_BROADCAST_REMEDIATION),
                (AntaTestStatus.SUCCESS, "outside the affected releases", None),
                (AntaTestStatus.SUCCESS, "outside the affected releases", None),
            ),
        ),
    },
    (SA160, "failure-graceful-restart-in-non-default-vrf"): {
        "version": build_eos_version("4.36.1F"),
        "eos_data": [ISIS_INTERFACE_ABSENT, ISIS_EMPTY, ISIS_GRACEFUL_RESTART_NON_DEFAULT],
        "expected": expected_result(
            AntaTestStatus.FAILURE,
            (
                (AntaTestStatus.SUCCESS, "IS-IS feature is disabled", None),
                (AntaTestStatus.SUCCESS, "IS-IS feature is disabled", None),
                (AntaTestStatus.FAILURE, "IS-IS graceful restart is enabled", LSP_AND_GRACEFUL_RESTART_REMEDIATION),
            ),
        ),
    },
    (SA160, "inconclusive-enabled-isis-without-observable-broadcast-interface"): {
        "version": build_eos_version("4.35.5M"),
        "eos_data": [ISIS_INTERFACE_OMITS_DOWN, ISIS_CONFIGURED, ISIS_EMPTY],
        "expected": expected_result(
            AntaTestStatus.FAILURE,
            (
                (AntaTestStatus.FAILURE, "assessment is inconclusive", OLD_BROADCAST_REMEDIATION),
                (AntaTestStatus.SUCCESS, "outside the affected releases", None),
                (AntaTestStatus.SUCCESS, "IS-IS graceful restart is disabled", None),
            ),
        ),
    },
    (SA160, "success-all-prerequisites-absent"): {
        "version": None,
        "eos_data": [ISIS_INTERFACE_ABSENT, ISIS_EMPTY, ISIS_EMPTY],
        "expected": expected_result(
            AntaTestStatus.SUCCESS,
            tuple((AntaTestStatus.SUCCESS, "is disabled", None) for _ in ADVISORY.vulnerabilities),
        ),
    },
    (SA160, "success-fixed-version"): {
        "version": build_eos_version("4.36.2F"),
        "eos_data": [ISIS_BROADCAST, ISIS_CONFIGURED, ISIS_GRACEFUL_RESTART],
        "expected": expected_result(
            AntaTestStatus.SUCCESS,
            tuple((AntaTestStatus.SUCCESS, "outside the affected releases", None) for _ in ADVISORY.vulnerabilities),
        ),
    },
    (SA160, "error-missing-version"): {
        "version": None,
        "eos_data": [ISIS_BROADCAST, ISIS_CONFIGURED, ISIS_GRACEFUL_RESTART],
        "expected": expected_result(
            AntaTestStatus.ERROR,
            tuple((AntaTestStatus.ERROR, "EOS version", None) for _ in ADVISORY.vulnerabilities),
        ),
    },
}
