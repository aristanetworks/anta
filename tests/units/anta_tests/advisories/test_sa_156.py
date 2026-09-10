# Copyright (c) 2026 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Unit tests for Arista Security Advisory 156."""

from __future__ import annotations

from functools import partial
from typing import TYPE_CHECKING

from anta._advisory.eos_versions import AffectedStatus
from anta._advisory.facts.eos import EosVersionFact
from anta._advisory.facts.models import AvailableFact, FeatureName, FeatureState, FeatureValue, MitigationState, MitigationValue, SubFeature
from anta._advisory.facts.network_services import (
    DhcpRelayActiveFact,
    DhcpRelayInterface,
    DhcpRelayScope,
    DhcpRelayScopeFact,
    DhcpReplySourceValidationFact,
    IpAddressFamily,
    IpLockingCoverage,
    IpLockingCoverageFact,
    IpLockingMitigationFact,
    IpLockingScope,
)
from anta._advisory.findings.models import AffectedResult, ErrorResult, MitigatedResult, NotAffectedResult, VulnerabilityResult
from anta._advisory.remediation import ApplyConfiguration, FixedRelease, RemediationPlan, Sequence, software_version_action
from anta._eos.version import EOSVersion
from anta.result_manager.models import AntaTestStatus
from anta.tests.advisories.sa_156 import ADVISORY, AFFECTED_VERSION_MATRIX, SA156, _assess_sa156
from tests.units.anta_tests import build_eos_version, test
from tests.units.anta_tests.advisories import build_expected_advisory_result
from tests.units.anta_tests.advisories.fact_builders import assert_version_statuses, available_fact, eos_version_fact, unavailable_fact

if TYPE_CHECKING:
    from anta._advisory.facts.models import Fact
    from tests.units.anta_tests import AntaUnitTestData

FIXED_RELEASES = (
    FixedRelease(EOSVersion(4, 36, 2, suffix="F")),
    FixedRelease(EOSVersion(4, 35, 6, suffix="M")),
    FixedRelease(EOSVersion(4, 34, 8, suffix="M")),
    FixedRelease(EOSVersion(4, 33, 10, suffix="M")),
)
CONFIGURATION = ApplyConfiguration(("dhcp relay", "reply source-address validation"))
FULL_REMEDIATION = RemediationPlan(Sequence((software_version_action(FIXED_RELEASES, current_version=EOSVersion(4, 36, 1, suffix="F")), CONFIGURATION)))
CONFIGURATION_REMEDIATION = RemediationPlan(CONFIGURATION)
expected_result = partial(build_expected_advisory_result, ADVISORY.vulnerabilities[0].id)

IPV4 = frozenset((IpAddressFamily.IPV4,))
IPV6 = frozenset((IpAddressFamily.IPV6,))
DUAL_STACK = frozenset((IpAddressFamily.IPV4, IpAddressFamily.IPV6))
RELAY_DUAL_STACK = DhcpRelayScope((DhcpRelayInterface("Vlan100", DUAL_STACK),))
RELAY_IPV6 = DhcpRelayScope((DhcpRelayInterface("Vlan100", IPV6),))
IP_LOCKING_DUAL_STACK = IpLockingCoverage((), (IpLockingScope("100", DUAL_STACK),))
IP_LOCKING_IPV4 = IpLockingCoverage((), (IpLockingScope("100", IPV4),))
IP_LOCKING_OTHER_VLAN = IpLockingCoverage((), (IpLockingScope("200", DUAL_STACK),))
IP_LOCKING_INACTIVE = {"active": False}
IP_LOCKING_VLAN_DUAL_STACK = {
    "active": True,
    "enabledIntfs": {},
    "enabledVlans": {"100": {"ipv4Enabled": True, "ipv4Mode": "enforcementDisabled", "ipv6Enabled": True, "ipv6Mode": "enforcementDisabled"}},
}
IP_LOCKING_VLAN_IPV4 = {
    "active": True,
    "enabledIntfs": {},
    "enabledVlans": {"100": {"ipv4Enabled": True, "ipv4Mode": "enforcementDisabled", "ipv6Enabled": False, "ipv6Mode": "enforcementDisabled"}},
}
DHCP_RELAY_DUAL_STACK = """DHCP relay is active
Interface: Vlan100
  DHCPv4 servers: 192.0.2.10
  DHCPv6 servers: 2001:db8::10"""
DHCP_RELAY_IPV6 = """DHCP relay is active
Interface: Vlan100
  DHCPv4 servers:
  DHCPv6 servers: 2001:db8::10"""


def dhcp_fact(definition: type[DhcpRelayActiveFact | DhcpReplySourceValidationFact], state: FeatureState) -> AvailableFact[FeatureValue]:
    """Build normalized DHCP state for direct assessment tests."""
    name = "relay" if definition is DhcpRelayActiveFact else "relay reply source-address validation"
    return available_fact(definition, FeatureValue(SubFeature(FeatureName.DHCP, name), state))


def mitigation_fact(state: MitigationState) -> AvailableFact[MitigationValue]:
    """Build normalized IP-locking mitigation state."""
    return available_fact(IpLockingMitigationFact, MitigationValue(state))


def assess(
    version: str,
    *,
    validation: Fact[FeatureValue],
    mitigation: Fact[MitigationValue],
    relay: Fact[FeatureValue] | None = None,
    relay_scope: Fact[DhcpRelayScope] | None = None,
    coverage: Fact[IpLockingCoverage] | None = None,
) -> VulnerabilityResult:
    """Assess one concise direct-fact scenario."""
    return _assess_sa156(
        eos_version_fact(version),
        relay or dhcp_fact(DhcpRelayActiveFact, FeatureState.ENABLED),
        validation,
        mitigation,
        relay_scope or available_fact(DhcpRelayScopeFact, RELAY_DUAL_STACK),
        coverage or available_fact(IpLockingCoverageFact, IP_LOCKING_DUAL_STACK),
    )


def test_sa156_safe_short_circuits() -> None:
    """Ignore unavailable later facts after relay absence or complete resolution proves safety."""
    unavailable_validation = unavailable_fact(DhcpReplySourceValidationFact)
    unavailable_mitigation = unavailable_fact(IpLockingMitigationFact)
    unavailable_scope = unavailable_fact(DhcpRelayScopeFact)
    unavailable_coverage = unavailable_fact(IpLockingCoverageFact)
    assert isinstance(
        _assess_sa156(
            unavailable_fact(EosVersionFact),
            dhcp_fact(DhcpRelayActiveFact, FeatureState.DISABLED),
            unavailable_validation,
            unavailable_mitigation,
            unavailable_scope,
            unavailable_coverage,
        ),
        NotAffectedResult,
    )
    assert isinstance(
        assess("4.36.2F", validation=dhcp_fact(DhcpReplySourceValidationFact, FeatureState.ENABLED), mitigation=unavailable_mitigation),
        NotAffectedResult,
    )


def test_sa156_resolution_and_mitigation_paths() -> None:
    """Distinguish complete resolution, verified mitigation, and uncovered exposure."""
    validation_enabled = dhcp_fact(DhcpReplySourceValidationFact, FeatureState.ENABLED)
    validation_disabled = dhcp_fact(DhcpReplySourceValidationFact, FeatureState.DISABLED)
    ineffective = mitigation_fact(MitigationState.INEFFECTIVE)
    effective = mitigation_fact(MitigationState.EFFECTIVE)

    assert isinstance(assess("4.36.1F", validation=validation_enabled, mitigation=ineffective), AffectedResult)
    assert isinstance(assess("4.36.2F", validation=validation_disabled, mitigation=ineffective), AffectedResult)
    assert isinstance(assess("4.36.1F", validation=validation_enabled, mitigation=effective), MitigatedResult)
    assert isinstance(assess("4.36.2F", validation=validation_disabled, mitigation=effective), MitigatedResult)
    assert isinstance(assess("4.36.2F", validation=unavailable_fact(DhcpReplySourceValidationFact), mitigation=effective), MitigatedResult)
    assert isinstance(
        assess("4.36.2F", validation=validation_disabled, mitigation=effective, coverage=available_fact(IpLockingCoverageFact, IP_LOCKING_IPV4)),
        AffectedResult,
    )
    assert isinstance(
        assess("4.36.2F", validation=validation_disabled, mitigation=effective, coverage=available_fact(IpLockingCoverageFact, IP_LOCKING_OTHER_VLAN)),
        AffectedResult,
    )
    assert isinstance(
        assess(
            "4.36.1F",
            validation=validation_enabled,
            mitigation=effective,
            relay_scope=available_fact(DhcpRelayScopeFact, RELAY_IPV6),
            coverage=available_fact(IpLockingCoverageFact, IpLockingCoverage((), (IpLockingScope("100", IPV6),))),
        ),
        MitigatedResult,
    )


def test_sa156_unavailable_required_facts_are_errors() -> None:
    """Require every observable fact needed by the remaining resolution or mitigation branches."""
    validation_disabled = dhcp_fact(DhcpReplySourceValidationFact, FeatureState.DISABLED)
    effective = mitigation_fact(MitigationState.EFFECTIVE)
    ineffective = mitigation_fact(MitigationState.INEFFECTIVE)

    assert isinstance(assess("4.36.1F", validation=validation_disabled, mitigation=unavailable_fact(IpLockingMitigationFact)), ErrorResult)
    assert isinstance(assess("4.36.2F", validation=unavailable_fact(DhcpReplySourceValidationFact), mitigation=ineffective), ErrorResult)
    assert isinstance(assess("4.36.1F", validation=validation_disabled, mitigation=effective, relay_scope=unavailable_fact(DhcpRelayScopeFact)), ErrorResult)
    assert isinstance(assess("4.36.1F", validation=validation_disabled, mitigation=effective, coverage=unavailable_fact(IpLockingCoverageFact)), ErrorResult)


def test_sa156_version_boundaries() -> None:
    """Cover every source-defined affected EOS boundary."""
    # pylint: disable=duplicate-code
    assert_version_statuses(
        AFFECTED_VERSION_MATRIX,
        (
            ("4.36.1F", AffectedStatus.AFFECTED),
            ("4.36.2F", AffectedStatus.NOT_AFFECTED),
            ("4.35.5M", AffectedStatus.AFFECTED),
            ("4.35.6M", AffectedStatus.NOT_AFFECTED),
            ("4.34.7.1M", AffectedStatus.AFFECTED),
            ("4.34.7.99M", AffectedStatus.AFFECTED),
            ("4.33.9M", AffectedStatus.AFFECTED),
            ("4.33.10M", AffectedStatus.NOT_AFFECTED),
            ("4.32.99M", AffectedStatus.AFFECTED),
        ),
    )
    # pylint: enable=duplicate-code


DATA: AntaUnitTestData = {
    (SA156, "failure-affected-release-even-with-setting"): {
        "version": build_eos_version("4.36.1F"),
        "eos_data": [{"activeState": True}, "reply source-address validation", IP_LOCKING_INACTIVE, "DHCP relay is active", IP_LOCKING_INACTIVE],
        "expected": expected_result(AntaTestStatus.FAILURE, "DHCP relay is enabled", FULL_REMEDIATION),
    },
    (SA156, "failure-conditional-fixed-without-setting"): {
        "version": build_eos_version("4.36.2F"),
        "eos_data": [{"activeState": True}, "", IP_LOCKING_INACTIVE, "DHCP relay is active", IP_LOCKING_INACTIVE],
        "expected": expected_result(AntaTestStatus.FAILURE, "DHCP relay reply source-address validation is disabled", CONFIGURATION_REMEDIATION),
    },
    (SA156, "success-conditional-fixed-with-setting"): {
        "version": build_eos_version("4.36.2F"),
        "eos_data": [{"activeState": True}, "reply source-address validation", {}, "unexpected", {}],
        "expected": expected_result(AntaTestStatus.SUCCESS, "conditionally fixed", None),
    },
    (SA156, "success-required-setting-short-circuits-invalid-relay-state"): {
        "version": build_eos_version("4.36.2F"),
        "eos_data": [{}, "reply source-address validation", {}, "unexpected", {}],
        "expected": expected_result(AntaTestStatus.SUCCESS, "conditionally fixed", None),
    },
    (SA156, "success-relay-inactive-short-circuits-later-facts"): {
        "version": None,
        "eos_data": [{"activeState": False}, "unexpected", {}, "unexpected", {}],
        "expected": expected_result(AntaTestStatus.SUCCESS, "DHCP relay is disabled", None),
    },
    (SA156, "error-new-train-with-invalid-setting-output"): {
        "version": build_eos_version("4.37.0F"),
        "eos_data": [{"activeState": True}, "unexpected", IP_LOCKING_INACTIVE, "DHCP relay is active", IP_LOCKING_INACTIVE],
        "expected": expected_result(AntaTestStatus.ERROR, "reply source-address validation state", None),
    },
    (SA156, "success-new-train-with-setting"): {
        "version": build_eos_version("4.37.0F"),
        "eos_data": [{"activeState": True}, "reply source-address validation", {}, "unexpected", {}],
        "expected": expected_result(AntaTestStatus.SUCCESS, "conditionally fixed", None),
    },
    (SA156, "mitigated-affected-release-with-dual-stack-vlan-coverage"): {
        "version": build_eos_version("4.36.1F"),
        "eos_data": [{"activeState": True}, "reply source-address validation", IP_LOCKING_VLAN_DUAL_STACK, DHCP_RELAY_DUAL_STACK, IP_LOCKING_VLAN_DUAL_STACK],
        "expected": expected_result(AntaTestStatus.SUCCESS, "affected but mitigated", FULL_REMEDIATION),
    },
    (SA156, "mitigated-conditional-fixed-ipv6-only-relay"): {
        "version": build_eos_version("4.36.2F"),
        "eos_data": [{"activeState": True}, "", IP_LOCKING_VLAN_DUAL_STACK, DHCP_RELAY_IPV6, IP_LOCKING_VLAN_DUAL_STACK],
        "expected": expected_result(AntaTestStatus.SUCCESS, "affected but mitigated", CONFIGURATION_REMEDIATION),
    },
    (SA156, "failure-dual-stack-relay-with-ipv4-only-ip-locking"): {
        "version": build_eos_version("4.36.2F"),
        "eos_data": [{"activeState": True}, "", IP_LOCKING_VLAN_IPV4, DHCP_RELAY_DUAL_STACK, IP_LOCKING_VLAN_IPV4],
        "expected": expected_result(AntaTestStatus.FAILURE, "reply source-address validation is disabled", CONFIGURATION_REMEDIATION),
    },
    (SA156, "error-ip-locking-state-is-missing"): {
        "version": build_eos_version("4.36.1F"),
        "eos_data": [{"activeState": True}, "", {}, "DHCP relay is active", {}],
        "expected": expected_result(AntaTestStatus.ERROR, "IP locking with locked-address enforcement disabled", None),
    },
    (SA156, "error-effective-ip-locking-with-missing-relay-scope"): {
        "version": build_eos_version("4.36.1F"),
        "eos_data": [{"activeState": True}, "", IP_LOCKING_VLAN_DUAL_STACK, "DHCP relay is active", IP_LOCKING_VLAN_DUAL_STACK],
        "expected": expected_result(AntaTestStatus.ERROR, "DHCP relay interface and address-family scope", None),
    },
}
