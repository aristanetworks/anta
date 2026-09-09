# Copyright (c) 2026 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Unit tests for Arista Security Advisory 161."""

from __future__ import annotations

from functools import partial
from typing import TYPE_CHECKING

from anta._advisory.eos_versions import AffectedStatus
from anta._advisory.facts.eos import EosVersionFact
from anta._advisory.facts.models import AvailableFact, FeatureName, FeatureState, FeatureValue, SubFeature
from anta._advisory.facts.network_services import MlagDualPrimaryErrdisableFact
from anta._advisory.findings.models import AffectedResult, ErrorResult, NotAffectedResult
from anta._advisory.remediation import FixedRelease, software_version_plan
from anta._eos.version import EOSVersion
from anta.result_manager.models import AntaTestStatus
from anta.tests.advisories.sa_161 import ADVISORY, AFFECTED_VERSION_MATRIX, SA161, _assess_sa161
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


def mlag_fact(state: FeatureState) -> AvailableFact[FeatureValue]:
    """Build normalized local MLAG state for direct assessment tests."""
    feature = SubFeature(FeatureName.MLAG, "dual-primary heartbeat with errdisable-all action")
    return available_fact(MlagDualPrimaryErrdisableFact, FeatureValue(feature, state))


def test_sa161_assessment_contract() -> None:
    """Assess stable local configuration without depending on transient peer state."""
    assert isinstance(_assess_sa161(unavailable_fact(EosVersionFact), mlag_fact(FeatureState.DISABLED)), NotAffectedResult)
    assert isinstance(_assess_sa161(eos_version_fact("4.36.1F"), mlag_fact(FeatureState.ENABLED)), AffectedResult)
    assert isinstance(_assess_sa161(eos_version_fact("4.36.2F"), mlag_fact(FeatureState.ENABLED)), NotAffectedResult)
    assert isinstance(_assess_sa161(unavailable_fact(EosVersionFact), mlag_fact(FeatureState.ENABLED)), ErrorResult)


def test_sa161_version_boundaries() -> None:
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


EXPOSED_MLAG = {
    "domainId": "mlagDomain",
    "peerLink": "Port-Channel10",
    "state": "inactive",
    "peerLinkStatus": "lowerLayerDown",
    "heartbeatPeerAddress": "192.0.2.2",
    "dualPrimaryDetectionState": "disabled",
    "detail": {"dualPrimaryDetectionDelay": 5, "dualPrimaryAction": "errdisableAllInterfaces"},
}

DATA: AntaUnitTestData = {
    (SA161, "failure-configured"): {
        "version": build_eos_version("4.36.1F"),
        "eos_data": [{**EXPOSED_MLAG, "state": "active", "peerLinkStatus": "up", "dualPrimaryDetectionState": "configured"}],
        "expected": expected_result(AntaTestStatus.FAILURE, "MLAG dual-primary heartbeat with errdisable-all action is enabled", REMEDIATION),
    },
    (SA161, "success-local-prerequisite-absent"): {
        "version": None,
        "eos_data": [{**EXPOSED_MLAG, "detail": {}}],
        "expected": expected_result(AntaTestStatus.SUCCESS, "MLAG dual-primary heartbeat with errdisable-all action is disabled", None),
    },
    (SA161, "failure-transient-operational-state-does-not-soften"): {
        "version": build_eos_version("4.36.1F"),
        "eos_data": [EXPOSED_MLAG],
        "expected": expected_result(AntaTestStatus.FAILURE, "MLAG dual-primary heartbeat with errdisable-all action is enabled", REMEDIATION),
    },
    (SA161, "error-partial-mlag-output"): {
        "version": build_eos_version("4.36.1F"),
        "eos_data": [{**EXPOSED_MLAG, "detail": None}],
        "expected": expected_result(AntaTestStatus.ERROR, "MLAG dual-primary errdisable exposure state", None),
    },
    (SA161, "success-fixed-version"): {
        "version": build_eos_version("4.36.2F"),
        "eos_data": [EXPOSED_MLAG],
        "expected": expected_result(AntaTestStatus.SUCCESS, "outside the affected releases", None),
    },
    (SA161, "error-missing-version"): {
        "version": None,
        "eos_data": [EXPOSED_MLAG],
        "expected": expected_result(AntaTestStatus.ERROR, "EOS version", None),
    },
}
