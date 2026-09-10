# Copyright (c) 2026 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Unit tests for Arista Security Advisory 172."""

from __future__ import annotations

from functools import partial
from typing import TYPE_CHECKING

from anta._advisory.eos_versions import AffectedStatus
from anta._advisory.facts.eos import EosVersionFact
from anta._advisory.facts.models import AvailableFact, FeatureName, FeatureState, FeatureValue, MitigationState, MitigationValue, SubFeature
from anta._advisory.facts.routing import LegacyOspfv3ConfiguredFact, Ospfv3ConfiguredFact, Ospfv3IpsecAuthenticationFact
from anta._advisory.findings.models import AffectedResult, ErrorResult, MitigatedResult, NotAffectedResult
from anta._advisory.remediation import FixedRelease, software_version_plan
from anta._eos.version import EOSVersion
from anta.result_manager.models import AntaTestStatus
from anta.tests.advisories.sa_172 import ADVISORY, AFFECTED_VERSION_MATRIX, SA172, _assess_sa172
from tests.units.anta_tests import build_eos_version, test
from tests.units.anta_tests.advisories import build_expected_advisory_result
from tests.units.anta_tests.advisories.fact_builders import assert_version_statuses, available_fact, eos_version_fact, unavailable_fact

if TYPE_CHECKING:
    from tests.units.anta_tests import AntaUnitTestData

FIXED_RELEASES = (
    FixedRelease(EOSVersion(4, 36, 2, suffix="F")),
    FixedRelease(EOSVersion(4, 35, 6, suffix="M")),
    FixedRelease(EOSVersion(4, 34, 8, suffix="M")),
    FixedRelease(EOSVersion(4, 33, 10, suffix="M")),
)
REMEDIATION = software_version_plan(FIXED_RELEASES, current_version=EOSVersion(4, 36, 1, suffix="F"))
expected_result = partial(build_expected_advisory_result, ADVISORY.vulnerabilities[0].id)
UNAUTHENTICATED_CONFIG = "interface Ethernet1\n   ospfv3 ipv6 area 0.0.0.0\nrouter ospfv3\n   router-id 1.1.1.1"
AUTHENTICATED_CONFIG = "interface Ethernet1\n   ospfv3 authentication ipsec spi 35 md5 passphrase 7 REDACTED\n   ospfv3 ipv6 area 0.0.0.0\nrouter ospfv3"
EMPTY_OSPFV3 = {"vrfs": {}}
CURRENT_OSPFV3 = {"vrfs": {"default": {"addressFamily": {"ipv6": {}}}}}
LEGACY_OSPFV3 = {"vrfs": {"default": {"instList": {"0": {}}}}}
MALFORMED_OSPFV3 = {"vrfs": []}


def ospfv3_fact(definition: type[Ospfv3ConfiguredFact | LegacyOspfv3ConfiguredFact], state: FeatureState) -> AvailableFact[FeatureValue]:
    """Build one normalized OSPFv3 observation for direct assessment tests."""
    name = "routing process" if definition is Ospfv3ConfiguredFact else "legacy IPv6 routing process"
    return available_fact(definition, FeatureValue(SubFeature(FeatureName.OSPFV3, name), state))


def authentication_fact(state: MitigationState) -> AvailableFact[MitigationValue]:
    """Build normalized OSPFv3 IPsec authentication coverage for direct assessment tests."""
    return available_fact(Ospfv3IpsecAuthenticationFact, MitigationValue(state))


def test_sa172_assessment_contract() -> None:
    """Evaluate both OSPFv3 observations without hiding unavailable alternatives."""
    current_disabled = ospfv3_fact(Ospfv3ConfiguredFact, FeatureState.DISABLED)
    legacy_disabled = ospfv3_fact(LegacyOspfv3ConfiguredFact, FeatureState.DISABLED)
    current_enabled = ospfv3_fact(Ospfv3ConfiguredFact, FeatureState.ENABLED)
    legacy_missing = unavailable_fact(LegacyOspfv3ConfiguredFact)
    ineffective = authentication_fact(MitigationState.INEFFECTIVE)
    assert isinstance(_assess_sa172(unavailable_fact(EosVersionFact), current_disabled, legacy_disabled, ineffective), NotAffectedResult)
    assert isinstance(_assess_sa172(eos_version_fact("4.36.1F"), current_enabled, legacy_missing, ineffective), AffectedResult)
    assert isinstance(
        _assess_sa172(eos_version_fact("4.36.1F"), current_enabled, legacy_missing, authentication_fact(MitigationState.EFFECTIVE)),
        MitigatedResult,
    )
    assert isinstance(
        _assess_sa172(eos_version_fact("4.36.1F"), current_enabled, legacy_missing, unavailable_fact(Ospfv3IpsecAuthenticationFact)),
        ErrorResult,
    )
    assert isinstance(_assess_sa172(eos_version_fact("4.36.2F"), current_enabled, legacy_missing, ineffective), NotAffectedResult)
    assert isinstance(
        _assess_sa172(
            eos_version_fact("4.36.2F"),
            unavailable_fact(Ospfv3ConfiguredFact),
            legacy_missing,
            unavailable_fact(Ospfv3IpsecAuthenticationFact),
        ),
        NotAffectedResult,
    )
    assert isinstance(_assess_sa172(eos_version_fact("4.36.2F"), current_disabled, legacy_missing, ineffective), NotAffectedResult)
    assert isinstance(_assess_sa172(eos_version_fact("4.36.1F"), current_disabled, legacy_missing, ineffective), ErrorResult)


def test_sa172_version_boundaries() -> None:
    """Cover every source-defined affected and first-fixed EOS boundary."""
    # pylint: disable=duplicate-code
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
    # pylint: enable=duplicate-code


_DATA: AntaUnitTestData = {
    (SA172, "failure-current-ospfv3"): {
        "version": build_eos_version("4.36.1F"),
        "eos_data": [CURRENT_OSPFV3, EMPTY_OSPFV3, UNAUTHENTICATED_CONFIG],
        "expected": expected_result(AntaTestStatus.FAILURE, "OSPFv3 routing process is enabled", REMEDIATION),
    },
    (SA172, "failure-legacy-ospfv3"): {
        "version": build_eos_version("4.36.1F"),
        "eos_data": [EMPTY_OSPFV3, LEGACY_OSPFV3, UNAUTHENTICATED_CONFIG],
        "expected": expected_result(AntaTestStatus.FAILURE, "legacy IPv6 routing process is enabled", REMEDIATION),
    },
    (SA172, "success-both-observations-empty"): {
        "version": None,
        "eos_data": [EMPTY_OSPFV3, EMPTY_OSPFV3, "unexpected"],
        "expected": expected_result(AntaTestStatus.SUCCESS, "routing process is disabled", None),
    },
    (SA172, "success-fixed-version"): {
        "version": build_eos_version("4.36.2F"),
        "eos_data": [CURRENT_OSPFV3, EMPTY_OSPFV3, "unexpected"],
        "expected": expected_result(AntaTestStatus.SUCCESS, "outside the affected releases", None),
    },
    (SA172, "success-fixed-version-short-circuits-unavailable-observations"): {
        "version": build_eos_version("4.36.2F"),
        "eos_data": [MALFORMED_OSPFV3, MALFORMED_OSPFV3, "unexpected"],
        "expected": expected_result(AntaTestStatus.SUCCESS, "outside the affected releases", None),
    },
    (SA172, "error-neither-observation-valid"): {
        "version": build_eos_version("4.36.1F"),
        "eos_data": [MALFORMED_OSPFV3, MALFORMED_OSPFV3, "unexpected"],
        "expected": expected_result(AntaTestStatus.ERROR, "OSPFv3 configuration state", None),
    },
    (SA172, "mitigated-complete-ipsec-authentication"): {
        "version": build_eos_version("4.36.1F"),
        "eos_data": [CURRENT_OSPFV3, EMPTY_OSPFV3, AUTHENTICATED_CONFIG],
        "expected": expected_result(
            AntaTestStatus.SUCCESS,
            "OSPFv3 IPsec authentication coverage is effective",
            REMEDIATION,
        ),
    },
    (SA172, "error-ipsec-authentication-unavailable"): {
        "version": build_eos_version("4.36.1F"),
        "eos_data": [CURRENT_OSPFV3, EMPTY_OSPFV3, "unexpected"],
        "expected": expected_result(AntaTestStatus.ERROR, "OSPFv3 IPsec authentication coverage", None),
    },
}
