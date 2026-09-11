# Copyright (c) 2026 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Unit tests for Arista Security Advisory 157."""

from __future__ import annotations

from typing import TYPE_CHECKING, Literal, TypeAlias

from anta._advisory.eos_versions import AffectedStatus
from anta._advisory.facts.eos import EosVersionFact
from anta._advisory.facts.models import AvailableFact, FeatureName, FeatureState, FeatureValue, SubFeature
from anta._advisory.facts.network_services import VrrpAntiReplayFact, VrrpFact, VrrpV2IpAhFact
from anta._advisory.findings.models import AffectedResult, ErrorResult, NotAffectedResult
from anta._advisory.remediation import (
    AnyOf,
    ApplyConfiguration,
    ChangeSoftwareVersion,
    ConditionalAction,
    FixedRelease,
    KnownFixedReleases,
    OperationalAction,
    RemediationPlan,
    Sequence,
    SoftwareTarget,
    software_version_action,
    software_version_plan,
)
from anta._eos.version import EOSVersion
from anta.result_manager.models import AntaTestStatus
from anta.tests.advisories.sa_157 import ADVISORY, AFFECTED_VERSION_MATRIX, SA157, _assess_bypass, _assess_logging, _assess_replay
from tests.units.anta_tests import build_eos_version, test
from tests.units.anta_tests.advisories.fact_builders import assert_version_statuses, available_fact, eos_version_fact, unavailable_fact

if TYPE_CHECKING:
    from tests.units.anta_tests import AntaUnitTestData, AtomicResult, UnitTestResult

Status: TypeAlias = Literal[AntaTestStatus.SUCCESS, AntaTestStatus.FAILURE, AntaTestStatus.ERROR]
Issue: TypeAlias = tuple[Status, str, RemediationPlan | None]
FIXED_RELEASES = (
    FixedRelease(EOSVersion(4, 36, 2, suffix="F")),
    FixedRelease(EOSVersion(4, 35, 6, suffix="M")),
    FixedRelease(EOSVersion(4, 34, 8, suffix="M")),
    FixedRelease(EOSVersion(4, 33, 10, suffix="M")),
)
SOFTWARE_REMEDIATION = software_version_plan(FIXED_RELEASES, current_version=EOSVersion(4, 36, 1, suffix="F"))
ANTI_REPLAY = ApplyConfiguration(("vrrp ipv4 authentication anti-replay",))
REPLAY_REMEDIATION = RemediationPlan(Sequence((software_version_action(FIXED_RELEASES, current_version=EOSVersion(4, 36, 1, suffix="F")), ANTI_REPLAY)))
ANTI_REPLAY_REMEDIATION = RemediationPlan(ANTI_REPLAY)
LOGGING_REMEDIATION = RemediationPlan(
    AnyOf(
        (
            ChangeSoftwareVersion(SoftwareTarget.EOS, EOSVersion(4, 36, 1, suffix="F"), KnownFixedReleases(FIXED_RELEASES)),
            ConditionalAction(
                "VRRP is not operationally required",
                OperationalAction("Disable VRRP as described in the advisory."),
            ),
        )
    )
)
VRRP_V2_IP_AH = """interface Ethernet1
   vrrp 1 ipv4 192.0.2.1
   vrrp 1 peer authentication ietf-md5 key-string 7 REDACTED
!"""
VRRP_V3_IPV6 = """interface Ethernet1
   vrrp 1 ipv6 2001:db8::1
!"""


def vrrp_fact(definition: type[VrrpFact | VrrpV2IpAhFact | VrrpAntiReplayFact], state: FeatureState) -> AvailableFact[FeatureValue]:
    """Build normalized VRRP state for direct assessment tests."""
    if definition is VrrpFact:
        feature = FeatureName.VRRP
    elif definition is VrrpV2IpAhFact:
        feature = SubFeature(FeatureName.VRRP, "version 2 IP-AH authentication")
    else:
        feature = SubFeature(FeatureName.VRRP, "authentication anti-replay")
    return available_fact(definition, FeatureValue(feature, state))


def test_sa157_simple_assessment_contracts() -> None:
    """Assess bypass and logging from their independent VRRP prerequisites."""
    ip_ah_enabled = vrrp_fact(VrrpV2IpAhFact, FeatureState.ENABLED)
    vrrp_enabled = vrrp_fact(VrrpFact, FeatureState.ENABLED)
    assert isinstance(_assess_bypass(unavailable_fact(EosVersionFact), vrrp_fact(VrrpV2IpAhFact, FeatureState.DISABLED)), NotAffectedResult)
    assert isinstance(_assess_bypass(eos_version_fact("4.36.1F"), ip_ah_enabled), AffectedResult)
    assert isinstance(_assess_bypass(eos_version_fact("4.36.2F"), ip_ah_enabled), NotAffectedResult)
    assert isinstance(_assess_bypass(unavailable_fact(EosVersionFact), ip_ah_enabled), ErrorResult)
    assert isinstance(_assess_logging(unavailable_fact(EosVersionFact), vrrp_fact(VrrpFact, FeatureState.DISABLED)), NotAffectedResult)
    logging = _assess_logging(eos_version_fact("4.36.1F"), vrrp_enabled)
    assert isinstance(logging, AffectedResult)
    assert logging.remediation == LOGGING_REMEDIATION


def test_sa157_replay_assessment_contract() -> None:
    """Require both fixed software and anti-replay without demanding irrelevant IP-AH state."""
    ip_ah_enabled = vrrp_fact(VrrpV2IpAhFact, FeatureState.ENABLED)
    anti_replay_enabled = vrrp_fact(VrrpAntiReplayFact, FeatureState.ENABLED)
    anti_replay_disabled = vrrp_fact(VrrpAntiReplayFact, FeatureState.DISABLED)
    assert isinstance(_assess_replay(eos_version_fact("4.36.1F"), ip_ah_enabled, anti_replay_enabled), AffectedResult)
    assert isinstance(_assess_replay(eos_version_fact("4.36.2F"), unavailable_fact(VrrpV2IpAhFact), anti_replay_enabled), NotAffectedResult)
    affected = _assess_replay(eos_version_fact("4.36.2F"), ip_ah_enabled, anti_replay_disabled)
    assert isinstance(affected, AffectedResult)
    assert len(affected.conditions) == 2
    assert isinstance(_assess_replay(eos_version_fact("4.36.2F"), unavailable_fact(VrrpV2IpAhFact), anti_replay_disabled), ErrorResult)
    assert isinstance(_assess_replay(eos_version_fact("4.37.0F"), ip_ah_enabled, unavailable_fact(VrrpAntiReplayFact)), ErrorResult)
    assert isinstance(_assess_replay(eos_version_fact("4.37.0F"), ip_ah_enabled, anti_replay_enabled), NotAffectedResult)


def test_sa157_version_boundaries() -> None:
    """Cover every source-defined affected and first-fixed EOS boundary."""
    assert_version_statuses(
        AFFECTED_VERSION_MATRIX,
        (
            ("4.36.1F", AffectedStatus.AFFECTED),
            ("4.36.2F", AffectedStatus.NOT_AFFECTED),
            ("4.35.5M", AffectedStatus.AFFECTED),
            ("4.35.6M", AffectedStatus.NOT_AFFECTED),
            ("4.34.7M", AffectedStatus.AFFECTED),
            ("4.34.8M", AffectedStatus.NOT_AFFECTED),
            ("4.33.9M", AffectedStatus.AFFECTED),
            ("4.33.10M", AffectedStatus.NOT_AFFECTED),
            ("4.32.99M", AffectedStatus.AFFECTED),
        ),
    )


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


_DATA: AntaUnitTestData = {
    (SA157, "failure-all-three-issues"): {
        "version": build_eos_version("4.36.1F"),
        "eos_data": [VRRP_V2_IP_AH, VRRP_V2_IP_AH, ""],
        "expected": expected_result(
            AntaTestStatus.FAILURE,
            (
                (AntaTestStatus.FAILURE, "VRRP version 2 IP-AH authentication is enabled", SOFTWARE_REMEDIATION),
                (AntaTestStatus.FAILURE, "VRRP version 2 IP-AH authentication is enabled", REPLAY_REMEDIATION),
                (AntaTestStatus.FAILURE, "VRRP feature is enabled", LOGGING_REMEDIATION),
            ),
        ),
    },
    (SA157, "failure-vrrpv3-ipv6-logging-only"): {
        "version": build_eos_version("4.36.1F"),
        "eos_data": [VRRP_V3_IPV6, VRRP_V3_IPV6, ""],
        "expected": expected_result(
            AntaTestStatus.FAILURE,
            (
                (AntaTestStatus.SUCCESS, "VRRP version 2 IP-AH authentication is disabled", None),
                (AntaTestStatus.SUCCESS, "VRRP version 2 IP-AH authentication is disabled", None),
                (AntaTestStatus.FAILURE, "VRRP feature is enabled", LOGGING_REMEDIATION),
            ),
        ),
    },
    (SA157, "success-fixed-with-anti-replay"): {
        "version": build_eos_version("4.36.2F"),
        "eos_data": [VRRP_V2_IP_AH, VRRP_V2_IP_AH, "vrrp ipv4 authentication anti-replay"],
        "expected": expected_result(
            AntaTestStatus.SUCCESS,
            (
                (AntaTestStatus.SUCCESS, "outside the affected releases", None),
                (AntaTestStatus.SUCCESS, "VRRP authentication anti-replay is enabled", None),
                (AntaTestStatus.SUCCESS, "outside the affected releases", None),
            ),
        ),
    },
    (SA157, "failure-fixed-without-anti-replay"): {
        "version": build_eos_version("4.36.2F"),
        "eos_data": [VRRP_V2_IP_AH, VRRP_V2_IP_AH, ""],
        "expected": expected_result(
            AntaTestStatus.FAILURE,
            (
                (AntaTestStatus.SUCCESS, "outside the affected releases", None),
                (AntaTestStatus.FAILURE, "VRRP authentication anti-replay is disabled", ANTI_REPLAY_REMEDIATION),
                (AntaTestStatus.SUCCESS, "outside the affected releases", None),
            ),
        ),
    },
    (SA157, "failure-new-train-without-anti-replay"): {
        "version": build_eos_version("4.37.0F"),
        "eos_data": [VRRP_V2_IP_AH, VRRP_V2_IP_AH, ""],
        "expected": expected_result(
            AntaTestStatus.FAILURE,
            (
                (AntaTestStatus.SUCCESS, "outside the affected releases", None),
                (AntaTestStatus.FAILURE, "VRRP authentication anti-replay is disabled", ANTI_REPLAY_REMEDIATION),
                (AntaTestStatus.SUCCESS, "outside the affected releases", None),
            ),
        ),
    },
    (SA157, "success-no-vrrp-short-circuits-version"): {
        "version": None,
        "eos_data": ["", "", "unexpected"],
        "expected": expected_result(
            AntaTestStatus.SUCCESS,
            tuple((AntaTestStatus.SUCCESS, "is disabled", None) for _ in ADVISORY.vulnerabilities),
        ),
    },
    (SA157, "error-missing-version"): {
        "version": None,
        "eos_data": [VRRP_V2_IP_AH, VRRP_V2_IP_AH, ""],
        "expected": expected_result(
            AntaTestStatus.ERROR,
            tuple((AntaTestStatus.ERROR, "EOS version", None) for _ in ADVISORY.vulnerabilities),
        ),
    },
}
