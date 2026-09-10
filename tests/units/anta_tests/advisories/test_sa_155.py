# Copyright (c) 2026 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Unit tests for Arista Security Advisory 155."""

from __future__ import annotations

from functools import partial
from typing import TYPE_CHECKING

from anta._advisory.eos_versions import AffectedStatus
from anta._advisory.facts.eos import EosVersionFact
from anta._advisory.facts.models import AvailableFact, FeatureName, FeatureState, FeatureValue, SubFeature
from anta._advisory.facts.network_services import DhcpOption82Fact
from anta._advisory.findings.models import AffectedResult, ErrorResult, NotAffectedResult
from anta._advisory.remediation import FixedRelease, software_version_plan
from anta._eos.version import EOSVersion
from anta.result_manager.models import AntaTestStatus
from anta.tests.advisories.sa_155 import ADVISORY, AFFECTED_VERSION_MATRIX, SA155, _assess_sa155
from tests.units.anta_tests import build_eos_version, test
from tests.units.anta_tests.advisories import build_expected_advisory_result
from tests.units.anta_tests.advisories.fact_builders import assert_version_statuses, available_fact, eos_version_fact, unavailable_fact

if TYPE_CHECKING:
    from tests.units.anta_tests import AntaUnitTestData

FIXED_RELEASES = (
    FixedRelease(EOSVersion(4, 35, 6, suffix="M")),
    FixedRelease(EOSVersion(4, 34, 8, suffix="M")),
    FixedRelease(EOSVersion(4, 33, 10, suffix="M")),
)
REMEDIATION = software_version_plan(FIXED_RELEASES, current_version=EOSVersion(4, 35, 5, suffix="M"))
expected_result = partial(build_expected_advisory_result, ADVISORY.vulnerabilities[0].id)
RELAY_ACTIVE_OPTION82 = {"activeState": True, "option82": True}
RELAY_INACTIVE = {"activeState": False}
SNOOPING_OPTION82_CONFIG = "ip dhcp snooping\nip dhcp snooping information option\nip dhcp snooping vlan 100"


def option82_fact(state: FeatureState) -> AvailableFact[FeatureValue]:
    """Build normalized DHCP Option 82 state for direct assessment tests."""
    return available_fact(DhcpOption82Fact, FeatureValue(SubFeature(FeatureName.DHCP, "Option 82 exposure"), state))


def test_sa155_assessment_contract() -> None:
    """Return each supported result type from typed facts and safe short-circuits."""
    assert isinstance(_assess_sa155(unavailable_fact(EosVersionFact), option82_fact(FeatureState.DISABLED)), NotAffectedResult)
    assert isinstance(_assess_sa155(eos_version_fact("4.35.5M"), option82_fact(FeatureState.ENABLED)), AffectedResult)
    assert isinstance(_assess_sa155(eos_version_fact("4.35.6M"), option82_fact(FeatureState.ENABLED)), NotAffectedResult)
    assert isinstance(_assess_sa155(unavailable_fact(EosVersionFact), option82_fact(FeatureState.ENABLED)), ErrorResult)


def test_sa155_version_boundaries() -> None:
    """Cover every source-defined affected EOS boundary and excluded train."""
    assert_version_statuses(
        AFFECTED_VERSION_MATRIX,
        (
            ("4.36.0F", AffectedStatus.NOT_AFFECTED),
            ("4.35.5M", AffectedStatus.AFFECTED),
            ("4.35.6M", AffectedStatus.NOT_AFFECTED),
            ("4.34.7.1M", AffectedStatus.AFFECTED),
            ("4.34.7.99M", AffectedStatus.AFFECTED),
            ("4.33.9M", AffectedStatus.AFFECTED),
            ("4.33.10M", AffectedStatus.NOT_AFFECTED),
            ("4.32.99M", AffectedStatus.AFFECTED),
        ),
    )


DATA: AntaUnitTestData = {
    (SA155, "failure-relay-option82"): {
        "version": build_eos_version("4.35.5M"),
        "eos_data": ["ip dhcp relay information option\ninterface Management1\n   ip address dhcp", RELAY_ACTIVE_OPTION82],
        "expected": expected_result(AntaTestStatus.FAILURE, "DHCP Option 82 exposure is enabled", REMEDIATION),
    },
    (SA155, "success-no-option82-short-circuits-version"): {
        "version": None,
        "eos_data": ["", RELAY_INACTIVE],
        "expected": expected_result(AntaTestStatus.SUCCESS, "DHCP Option 82 exposure is disabled", None),
    },
    (SA155, "success-fixed-version"): {
        "version": build_eos_version("4.35.6M"),
        "eos_data": [SNOOPING_OPTION82_CONFIG, RELAY_INACTIVE],
        "expected": expected_result(AntaTestStatus.SUCCESS, "outside the affected releases", None),
    },
    (SA155, "error-missing-version"): {
        "version": None,
        "eos_data": [SNOOPING_OPTION82_CONFIG, RELAY_INACTIVE],
        "expected": expected_result(AntaTestStatus.ERROR, "EOS version", None),
    },
}
