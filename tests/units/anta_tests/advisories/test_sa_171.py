# Copyright (c) 2026 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Unit tests for Arista Security Advisory 171."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Literal, TypeAlias

from anta._advisory.eos_versions import AffectedStatus
from anta._advisory.facts.eos import EosVersionFact
from anta._advisory.facts.models import (
    AvailableFact,
    ConfigurationState,
    ConfigurationValue,
    FeatureName,
    FeatureState,
    FeatureValue,
    MitigationState,
    MitigationValue,
    SubFeature,
)
from anta._advisory.facts.routing import Ospfv2BroadcastAuthenticationFact, Ospfv2ProcessConfiguredFact, Ospfv2SegmentRoutingFact
from anta._advisory.facts.software import SA171HotfixFact
from anta._advisory.findings.models import AffectedResult, ErrorResult, InconclusiveResult, MitigatedResult, NotAffectedResult
from anta._advisory.remediation import FixedRelease, RemediationPlan, software_version_plan
from anta._eos.version import EOSVersion
from anta.result_manager.models import AntaTestStatus
from anta.tests.advisories.sa_171 import (
    ADVISORY,
    BROADCAST_AFFECTED_VERSIONS,
    SA171,
    SEGMENT_ROUTING_AFFECTED_VERSIONS,
    SEGMENT_ROUTING_FIXED_RELEASES,
    SEGMENT_ROUTING_ID,
    _assess_broadcast_issue,
)
from tests.units.anta_tests import build_eos_version, test
from tests.units.anta_tests.advisories.fact_builders import assert_version_statuses, available_fact, eos_version_fact, unavailable_fact

if TYPE_CHECKING:
    from tests.units.anta_tests import AntaUnitTestData, AtomicResult, UnitTestResult

Status: TypeAlias = Literal[AntaTestStatus.SUCCESS, AntaTestStatus.FAILURE, AntaTestStatus.ERROR]
Issue: TypeAlias = tuple[Status, str, RemediationPlan | None]


def ospfv2_fact(
    definition: type[Ospfv2BroadcastAuthenticationFact | Ospfv2SegmentRoutingFact],
    name: str,
    state: FeatureState,
) -> AvailableFact[FeatureValue]:
    """Build one normalized OSPFv2 fact for direct assessment tests."""
    return available_fact(definition, FeatureValue(SubFeature(FeatureName.OSPFV2, name), state))


def hotfix_fact(state: MitigationState) -> AvailableFact[MitigationValue]:
    """Build one normalized SA171 hotfix fact for direct assessment tests."""
    return available_fact(SA171HotfixFact, MitigationValue(state))


def ospfv2_configuration(state: ConfigurationState) -> AvailableFact[ConfigurationValue]:
    """Build the OSPFv2 routing-process configuration fact."""
    return available_fact(Ospfv2ProcessConfiguredFact, ConfigurationValue(SubFeature(FeatureName.OSPFV2, "routing process"), state))


def test_sa171_assessment_contract() -> None:
    """Apply active exposure, configured-but-inactive fallback, and independent version boundaries."""
    broadcast_enabled = ospfv2_fact(
        Ospfv2BroadcastAuthenticationFact,
        "broadcast cryptographic authentication",
        FeatureState.ENABLED,
    )
    broadcast_disabled = ospfv2_fact(
        Ospfv2BroadcastAuthenticationFact,
        "broadcast cryptographic authentication",
        FeatureState.DISABLED,
    )
    assert isinstance(
        _assess_broadcast_issue(
            unavailable_fact(EosVersionFact),
            broadcast_disabled,
            ospfv2_configuration(ConfigurationState.NOT_CONFIGURED),
            hotfix_fact(MitigationState.INEFFECTIVE),
        ),
        NotAffectedResult,
    )
    assert isinstance(
        _assess_broadcast_issue(
            eos_version_fact("4.34.7M"),
            broadcast_enabled,
            ospfv2_configuration(ConfigurationState.CONFIGURED),
            hotfix_fact(MitigationState.INEFFECTIVE),
        ),
        AffectedResult,
    )
    assert isinstance(
        _assess_broadcast_issue(
            eos_version_fact("4.34.7.1M"),
            broadcast_enabled,
            ospfv2_configuration(ConfigurationState.CONFIGURED),
            hotfix_fact(MitigationState.INEFFECTIVE),
        ),
        NotAffectedResult,
    )
    assert isinstance(
        _assess_broadcast_issue(
            eos_version_fact("4.34.7M"),
            unavailable_fact(Ospfv2BroadcastAuthenticationFact),
            ospfv2_configuration(ConfigurationState.CONFIGURED),
            hotfix_fact(MitigationState.INEFFECTIVE),
        ),
        ErrorResult,
    )
    assert isinstance(
        _assess_broadcast_issue(
            eos_version_fact("4.34.7M"),
            broadcast_disabled,
            ospfv2_configuration(ConfigurationState.CONFIGURED),
            hotfix_fact(MitigationState.INEFFECTIVE),
        ),
        InconclusiveResult,
    )
    assert isinstance(
        _assess_broadcast_issue(
            eos_version_fact("4.34.7.1M"),
            broadcast_disabled,
            ospfv2_configuration(ConfigurationState.CONFIGURED),
            hotfix_fact(MitigationState.INEFFECTIVE),
        ),
        NotAffectedResult,
    )
    assert isinstance(
        _assess_broadcast_issue(
            eos_version_fact("4.34.7M"),
            broadcast_disabled,
            unavailable_fact(Ospfv2ProcessConfiguredFact),
            hotfix_fact(MitigationState.INEFFECTIVE),
        ),
        ErrorResult,
    )
    assert isinstance(
        _assess_broadcast_issue(
            unavailable_fact(EosVersionFact),
            broadcast_disabled,
            ospfv2_configuration(ConfigurationState.NOT_CONFIGURED),
            hotfix_fact(MitigationState.INEFFECTIVE),
        ),
        NotAffectedResult,
    )

    mitigated = _assess_broadcast_issue(
        eos_version_fact("4.34.7M"),
        broadcast_enabled,
        ospfv2_configuration(ConfigurationState.CONFIGURED),
        hotfix_fact(MitigationState.EFFECTIVE),
    )
    assert isinstance(mitigated, MitigatedResult)
    mitigated_without_active_interface = _assess_broadcast_issue(
        eos_version_fact("4.34.7M"),
        broadcast_disabled,
        ospfv2_configuration(ConfigurationState.CONFIGURED),
        hotfix_fact(MitigationState.EFFECTIVE),
    )
    assert isinstance(mitigated_without_active_interface, MitigatedResult)
    assert isinstance(
        _assess_broadcast_issue(
            eos_version_fact("4.34.7M"),
            broadcast_disabled,
            ospfv2_configuration(ConfigurationState.CONFIGURED),
            unavailable_fact(SA171HotfixFact),
        ),
        ErrorResult,
    )
    assert isinstance(
        _assess_broadcast_issue(
            eos_version_fact("4.34.7M"),
            broadcast_enabled,
            ospfv2_configuration(ConfigurationState.CONFIGURED),
            unavailable_fact(SA171HotfixFact),
        ),
        ErrorResult,
    )
    assert isinstance(
        _assess_broadcast_issue(
            eos_version_fact("4.35.4M"),
            broadcast_enabled,
            ospfv2_configuration(ConfigurationState.CONFIGURED),
            hotfix_fact(MitigationState.EFFECTIVE),
        ),
        AffectedResult,
    )


def test_sa171_version_boundaries() -> None:
    """Cover every source-defined boundary, including the different 4.34 fixes."""
    common_boundaries = (
        ("4.36.1F", AffectedStatus.AFFECTED),
        ("4.36.2F", AffectedStatus.NOT_AFFECTED),
        ("4.35.5M", AffectedStatus.AFFECTED),
        ("4.35.6M", AffectedStatus.NOT_AFFECTED),
        ("4.33.9M", AffectedStatus.AFFECTED),
        ("4.33.10M", AffectedStatus.NOT_AFFECTED),
        ("4.32.99M", AffectedStatus.AFFECTED),
    )
    assert_version_statuses(
        BROADCAST_AFFECTED_VERSIONS,
        (
            *common_boundaries,
            ("4.34.7M", AffectedStatus.AFFECTED),
            ("4.34.7.1M", AffectedStatus.NOT_AFFECTED),
            ("4.34.7.99M", AffectedStatus.NOT_AFFECTED),
        ),
    )
    assert_version_statuses(
        SEGMENT_ROUTING_AFFECTED_VERSIONS,
        (
            *common_boundaries,
            ("4.34.7M", AffectedStatus.AFFECTED),
            ("4.34.7.1M", AffectedStatus.AFFECTED),
            ("4.34.7.99M", AffectedStatus.AFFECTED),
            ("4.34.8M", AffectedStatus.NOT_AFFECTED),
        ),
    )


BROADCAST_INTERFACE = """Ethernet1 is up
  Interface Address 192.0.2.3/24, instance 1, VRF default, Area 0.0.0.0
  Network Type Broadcast, Cost: 10
  Neighbor Count is 0
  Message-digest authentication, using key id 1"""
BROADCAST_PROCESS_CONFIG = """router ospf 1
   router-id 192.0.2.1
   max-lsa 12000"""
SEGMENT_ROUTING_EXPOSED = {"vrfs": {"default": {"instList": {"1": {}}}}}
SEGMENT_ROUTING_DISABLED = {"vrfs": {"default": {"instList": {}}}}
BROADCAST_RELEASES = (
    FixedRelease(EOSVersion(4, 36, 2, suffix="F")),
    FixedRelease(EOSVersion(4, 35, 6, suffix="M")),
    FixedRelease(EOSVersion(4, 34, 7, hotfix=1, suffix="M")),
    FixedRelease(EOSVersion(4, 33, 10, suffix="M")),
)
SEGMENT_ROUTING_RELEASES = (
    FixedRelease(EOSVersion(4, 36, 2, suffix="F")),
    FixedRelease(EOSVersion(4, 35, 6, suffix="M")),
    FixedRelease(EOSVersion(4, 34, 8, suffix="M")),
    FixedRelease(EOSVersion(4, 33, 10, suffix="M")),
)
BROADCAST_REMEDIATION = software_version_plan(BROADCAST_RELEASES, current_version=EOSVersion(4, 36, 1, suffix="F"))
SEGMENT_ROUTING_REMEDIATION = software_version_plan(SEGMENT_ROUTING_RELEASES, current_version=EOSVersion(4, 36, 1, suffix="F"))
BOUNDARY_REMEDIATION = software_version_plan(SEGMENT_ROUTING_RELEASES, current_version=EOSVersion(4, 34, 7, hotfix=1, suffix="M"))
HOTFIX_OUTSIDE_RELEASE_REMEDIATION = software_version_plan(BROADCAST_RELEASES, current_version=EOSVersion(4, 35, 4, suffix="M"))


def eos_data(
    interface: str,
    summary: str,
    process_config: str,
    segment_routing: dict[str, Any],
    extensions: object | None = None,
    boot_extensions: object | None = None,
) -> list[dict[str, Any] | str]:
    """Supply output to every fact-owned command wrapper."""
    return [
        interface,
        summary,
        process_config,
        segment_routing,
        {"extensions": {} if extensions is None else extensions},
        {"extensions": [] if boot_extensions is None else boot_extensions},
    ]


def expected_result(status: Status, issues: tuple[Issue, Issue]) -> UnitTestResult:
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
    (SA171, "failure-both-issues"): {
        "version": build_eos_version("4.36.1F"),
        "eos_data": eos_data(BROADCAST_INTERFACE, "", BROADCAST_PROCESS_CONFIG, SEGMENT_ROUTING_EXPOSED),
        "expected": expected_result(
            AntaTestStatus.FAILURE,
            (
                (AntaTestStatus.FAILURE, "OSPFv2 broadcast cryptographic authentication is enabled", BROADCAST_REMEDIATION),
                (AntaTestStatus.FAILURE, "OSPFv2 segment routing is enabled", SEGMENT_ROUTING_REMEDIATION),
            ),
        ),
    },
    (SA171, "failure-segment-routing-at-split-boundary"): {
        "version": build_eos_version("4.34.7.1M"),
        "eos_data": eos_data(BROADCAST_INTERFACE, "", BROADCAST_PROCESS_CONFIG, SEGMENT_ROUTING_EXPOSED),
        "expected": expected_result(
            AntaTestStatus.FAILURE,
            (
                (AntaTestStatus.SUCCESS, "outside the affected releases", None),
                (AntaTestStatus.FAILURE, "OSPFv2 segment routing is enabled", BOUNDARY_REMEDIATION),
            ),
        ),
    },
    (SA171, "success-both-prerequisites-absent"): {
        "version": None,
        "eos_data": eos_data("", "", "", SEGMENT_ROUTING_DISABLED),
        "expected": expected_result(
            AntaTestStatus.SUCCESS,
            (
                (AntaTestStatus.SUCCESS, "configuration is not configured", None),
                (AntaTestStatus.SUCCESS, "is disabled", None),
            ),
        ),
    },
    (SA171, "inconclusive-configured-without-active-broadcast-authentication"): {
        "version": build_eos_version("4.36.1F"),
        "eos_data": eos_data("", "", BROADCAST_PROCESS_CONFIG, SEGMENT_ROUTING_DISABLED),
        "expected": expected_result(
            AntaTestStatus.FAILURE,
            (
                (AntaTestStatus.FAILURE, "assessment is inconclusive", BROADCAST_REMEDIATION),
                (AntaTestStatus.SUCCESS, "is disabled", None),
            ),
        ),
    },
    (SA171, "success-fixed-version"): {
        "version": build_eos_version("4.36.2F"),
        "eos_data": eos_data(BROADCAST_INTERFACE, "", BROADCAST_PROCESS_CONFIG, SEGMENT_ROUTING_EXPOSED),
        "expected": expected_result(
            AntaTestStatus.SUCCESS,
            (
                (AntaTestStatus.SUCCESS, "outside the affected releases", None),
                (AntaTestStatus.SUCCESS, "outside the affected releases", None),
            ),
        ),
    },
    (SA171, "error-malformed-ospfv2-output"): {
        "version": build_eos_version("4.36.1F"),
        "eos_data": eos_data(
            "unexpected",
            "unexpected",
            BROADCAST_PROCESS_CONFIG,
            {"vrfs": []},
        ),
        "expected": expected_result(
            AntaTestStatus.ERROR,
            (
                (AntaTestStatus.ERROR, "OSPFv2 broadcast cryptographic-authentication exposure state", None),
                (AntaTestStatus.ERROR, "OSPFv2 segment-routing state", None),
            ),
        ),
    },
    (SA171, "mitigated-persistent-hotfix"): {
        "version": build_eos_version("4.34.7M"),
        "eos_data": eos_data(
            BROADCAST_INTERFACE,
            "",
            BROADCAST_PROCESS_CONFIG,
            SEGMENT_ROUTING_DISABLED,
            {"sa171-SecurityAdvisory171_CVE-2026-73435.swix": {"status": "installed", "boot": True}},
            ["sa171-SecurityAdvisory171_CVE-2026-73435.swix"],
        ),
        "expected": expected_result(
            AntaTestStatus.SUCCESS,
            (
                (
                    AntaTestStatus.SUCCESS,
                    "SA171 CVE-2026-73435 SWIX hotfix is effective",
                    software_version_plan(BROADCAST_RELEASES, current_version=EOSVersion(4, 34, 7, suffix="M")),
                ),
                (AntaTestStatus.SUCCESS, "is disabled", None),
            ),
        ),
    },
    (SA171, "mitigated-persistent-hotfix-without-active-interface"): {
        "version": build_eos_version("4.34.7M"),
        "eos_data": eos_data(
            "",
            "",
            BROADCAST_PROCESS_CONFIG,
            SEGMENT_ROUTING_DISABLED,
            {"sa171-SecurityAdvisory171_CVE-2026-73435.swix": {"status": "installed", "boot": True}},
            ["sa171-SecurityAdvisory171_CVE-2026-73435.swix"],
        ),
        "expected": expected_result(
            AntaTestStatus.SUCCESS,
            (
                (
                    AntaTestStatus.SUCCESS,
                    "SA171 CVE-2026-73435 SWIX hotfix is effective",
                    software_version_plan(BROADCAST_RELEASES, current_version=EOSVersion(4, 34, 7, suffix="M")),
                ),
                (AntaTestStatus.SUCCESS, "is disabled", None),
            ),
        ),
    },
    (SA171, "failure-hotfix-outside-applicable-release"): {
        "version": build_eos_version("4.35.4M"),
        "eos_data": eos_data(
            BROADCAST_INTERFACE,
            "",
            BROADCAST_PROCESS_CONFIG,
            SEGMENT_ROUTING_DISABLED,
            {"sa171-SecurityAdvisory171_CVE-2026-73435.swix": {"status": "installed", "boot": True}},
            ["sa171-SecurityAdvisory171_CVE-2026-73435.swix"],
        ),
        "expected": expected_result(
            AntaTestStatus.FAILURE,
            (
                (
                    AntaTestStatus.FAILURE,
                    "OSPFv2 broadcast cryptographic authentication is enabled",
                    HOTFIX_OUTSIDE_RELEASE_REMEDIATION,
                ),
                (AntaTestStatus.SUCCESS, "is disabled", None),
            ),
        ),
    },
}
