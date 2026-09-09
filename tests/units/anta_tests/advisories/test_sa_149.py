# Copyright (c) 2026 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Unit tests for Arista Security Advisory 149."""

from __future__ import annotations

from functools import partial
from typing import TYPE_CHECKING

from anta._advisory.eos_versions import AffectedStatus
from anta._advisory.facts.eos import EosVersionFact
from anta._advisory.facts.management import Dot1xDynamicAuthorizationFact, RadiusProxyDynamicAuthorizationFact
from anta._advisory.facts.models import AvailableFact, FeatureName, FeatureState, FeatureValue, SubFeature
from anta._advisory.facts.platform import PlatformIdentityFact
from anta._advisory.findings.models import AffectedResult, ErrorResult, NotAffectedResult
from anta._advisory.remediation import FixedRelease, software_version_plan
from anta._eos.version import EOSVersion
from anta.result_manager.models import AntaTestStatus
from anta.tests.advisories.sa_149 import ADVISORY, AFFECTED_VERSION_MATRIX, SA149, _assess_sa149
from tests.units.anta_tests import build_eos_platform, build_eos_version, test
from tests.units.anta_tests.advisories import build_expected_advisory_result
from tests.units.anta_tests.advisories.fact_builders import assert_version_statuses, available_fact, eos_version_fact, unavailable_fact

if TYPE_CHECKING:
    from anta._eos.platform import PlatformIdentity
    from tests.units.anta_tests import AntaUnitTestData

FIXED_RELEASES = (
    FixedRelease(EOSVersion(4, 36, 2, suffix="F")),
    FixedRelease(EOSVersion(4, 35, 6, suffix="M")),
    FixedRelease(EOSVersion(4, 34, 8, suffix="M")),
)
REMEDIATION = software_version_plan(FIXED_RELEASES, current_version=EOSVersion(4, 36, 1, suffix="F"))
expected_result = partial(build_expected_advisory_result, ADVISORY.vulnerabilities[0].id)
DOT1X: dict[str, object] = {
    "systemAuthControl": True,
    "dynAuth": True,
    "interfaces": {"Ethernet1": {"portControl": "controlled"}},
}
RADIUS_PROXY = """radius proxy
   dynamic-authorization
   client group CG1
      client ipv4 192.0.2.0/24 vrf default"""


def platform_fact(model: str) -> AvailableFact[PlatformIdentity]:
    """Build normalized platform identity for direct assessment tests."""
    platform = build_eos_platform(model)
    assert platform is not None
    return available_fact(PlatformIdentityFact, platform)


def sa149_feature_fact(
    definition: type[Dot1xDynamicAuthorizationFact | RadiusProxyDynamicAuthorizationFact], state: FeatureState
) -> AvailableFact[FeatureValue]:
    """Build one normalized SA149 feature prerequisite."""
    if definition is Dot1xDynamicAuthorizationFact:
        feature = SubFeature(FeatureName.DOT1X, "dynamic authorization authenticator")
    else:
        feature = SubFeature(FeatureName.RADIUS_PROXY, "dynamic authorization client group")
    return available_fact(definition, FeatureValue(feature, state))


def test_sa149_assessment_contract() -> None:
    """Require both features and one explicitly affected physical family."""
    dot1x_enabled = sa149_feature_fact(Dot1xDynamicAuthorizationFact, FeatureState.ENABLED)
    dot1x_disabled = sa149_feature_fact(Dot1xDynamicAuthorizationFact, FeatureState.DISABLED)
    radius_enabled = sa149_feature_fact(RadiusProxyDynamicAuthorizationFact, FeatureState.ENABLED)
    assert isinstance(
        _assess_sa149(unavailable_fact(EosVersionFact), unavailable_fact(PlatformIdentityFact), dot1x_disabled, radius_enabled), NotAffectedResult
    )
    assert isinstance(_assess_sa149(eos_version_fact("4.36.1F"), platform_fact("DCS-7050CX3-32S"), dot1x_enabled, radius_enabled), AffectedResult)
    assert isinstance(_assess_sa149(eos_version_fact("4.36.1F"), platform_fact("DCS-7050SX2-128"), dot1x_enabled, radius_enabled), NotAffectedResult)
    assert isinstance(_assess_sa149(eos_version_fact("4.36.1F"), unavailable_fact(PlatformIdentityFact), dot1x_enabled, radius_enabled), ErrorResult)
    assert isinstance(_assess_sa149(eos_version_fact("4.36.1F"), platform_fact("DCS-UNRECOGNIZED"), dot1x_enabled, radius_enabled), ErrorResult)
    assert isinstance(_assess_sa149(eos_version_fact("4.36.2F"), platform_fact("DCS-7050CX3-32S"), dot1x_enabled, radius_enabled), NotAffectedResult)


def test_sa149_version_boundaries() -> None:
    """Cover every source-defined affected EOS boundary and excluded train."""
    assert_version_statuses(
        AFFECTED_VERSION_MATRIX,
        (
            ("4.36.1F", AffectedStatus.AFFECTED),
            ("4.36.2F", AffectedStatus.NOT_AFFECTED),
            ("4.35.5M", AffectedStatus.AFFECTED),
            ("4.35.6M", AffectedStatus.NOT_AFFECTED),
            ("4.34.7.1M", AffectedStatus.AFFECTED),
            ("4.34.7.99M", AffectedStatus.AFFECTED),
            ("4.33.99M", AffectedStatus.NOT_AFFECTED),
        ),
    )


DATA: AntaUnitTestData = {
    (SA149, "failure-both-features-on-physical-platform"): {
        "version": build_eos_version("4.36.1F"),
        "platform": build_eos_platform("DCS-7050CX3-32S"),
        "eos_data": [DOT1X, RADIUS_PROXY],
        "expected": expected_result(AntaTestStatus.FAILURE, "RADIUS proxy dynamic authorization client group is enabled", REMEDIATION),
    },
    (SA149, "success-dot1x-absent-short-circuits-other-inputs"): {
        "version": None,
        "platform": None,
        "eos_data": [{"systemAuthControl": False, "dynAuth": False, "interfaces": {}}, RADIUS_PROXY],
        "expected": expected_result(AntaTestStatus.SUCCESS, "802.1X dynamic authorization authenticator is disabled", None),
    },
    (SA149, "success-radius-proxy-absent"): {
        "version": None,
        "platform": None,
        "eos_data": [DOT1X, ""],
        "expected": expected_result(AntaTestStatus.SUCCESS, "RADIUS proxy dynamic authorization client group is disabled", None),
    },
    (SA149, "success-virtual-platform"): {
        "version": build_eos_version("4.36.1F"),
        "platform": build_eos_platform("cEOSLab"),
        "eos_data": [DOT1X, RADIUS_PROXY],
        "expected": expected_result(AntaTestStatus.SUCCESS, "outside the affected platform scope", None),
    },
    (SA149, "success-excluded-physical-platform-family"): {
        "version": build_eos_version("4.36.1F"),
        "platform": build_eos_platform("DCS-7050SX2-128"),
        "eos_data": [DOT1X, RADIUS_PROXY],
        "expected": expected_result(AntaTestStatus.SUCCESS, "outside the affected platform scope", None),
    },
    (SA149, "error-missing-version"): {
        "version": None,
        "platform": build_eos_platform("DCS-7050CX3-32S"),
        "eos_data": [DOT1X, RADIUS_PROXY],
        "expected": expected_result(AntaTestStatus.ERROR, "EOS version", None),
    },
}
