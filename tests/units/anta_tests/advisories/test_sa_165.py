# Copyright (c) 2026 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
# pylint: disable=duplicate-code
"""Unit tests for Arista Security Advisory 165."""

from __future__ import annotations

from functools import partial
from typing import TYPE_CHECKING

from anta._advisory.eos_versions import AffectedStatus
from anta._advisory.facts.eos import EosVersionFact
from anta._advisory.facts.management import GnsiCredentialzFact
from anta._advisory.facts.models import AvailableFact, FeatureName, FeatureState, FeatureValue, SubFeature
from anta._advisory.findings.models import AffectedResult, ErrorResult, NotAffectedResult
from anta._advisory.remediation import FixedRelease, software_version_plan
from anta._eos.version import EOSVersion
from anta.result_manager.models import AntaTestStatus
from anta.tests.advisories.sa_165 import ADVISORY, AFFECTED_VERSION_MATRIX, SA165, _assess_sa165
from tests.units.anta_tests import build_eos_version, test
from tests.units.anta_tests.advisories import build_expected_advisory_result
from tests.units.anta_tests.advisories.fact_builders import assert_version_statuses, available_fact, eos_version_fact, unavailable_fact

if TYPE_CHECKING:
    from tests.units.anta_tests import AntaUnitTestData

FIXED_RELEASES = (
    FixedRelease(EOSVersion(4, 36, 1, suffix="F")),
    FixedRelease(EOSVersion(4, 35, 6, suffix="M")),
    FixedRelease(EOSVersion(4, 34, 7, hotfix=1, suffix="M")),
    FixedRelease(EOSVersion(4, 33, 9, suffix="M")),
)
REMEDIATION = software_version_plan(FIXED_RELEASES, current_version=EOSVersion(4, 36, 0, hotfix=1, suffix="F"))
expected_result = partial(build_expected_advisory_result, ADVISORY.vulnerabilities[0].id)


def credentialz_fact(state: FeatureState) -> AvailableFact[FeatureValue]:
    """Build normalized Credentialz state for direct assessment tests."""
    return available_fact(GnsiCredentialzFact, FeatureValue(SubFeature(FeatureName.GNSI, "Credentialz service"), state))


def test_sa165_assessment_contract() -> None:
    """Return affected, safe, and error outcomes from typed Credentialz state."""
    assert isinstance(_assess_sa165(unavailable_fact(EosVersionFact), credentialz_fact(FeatureState.DISABLED)), NotAffectedResult)
    assert isinstance(_assess_sa165(eos_version_fact("4.36.0.1F"), credentialz_fact(FeatureState.ENABLED)), AffectedResult)
    assert isinstance(_assess_sa165(eos_version_fact("4.34.7.1M"), credentialz_fact(FeatureState.ENABLED)), NotAffectedResult)
    assert isinstance(_assess_sa165(unavailable_fact(EosVersionFact), credentialz_fact(FeatureState.ENABLED)), ErrorResult)


def test_sa165_version_boundaries() -> None:
    """Cover every source-defined affected and first-fixed EOS boundary."""
    assert_version_statuses(
        AFFECTED_VERSION_MATRIX,
        (
            ("4.36.0.1F", AffectedStatus.AFFECTED),
            ("4.36.0.99F", AffectedStatus.AFFECTED),
            ("4.36.1F", AffectedStatus.NOT_AFFECTED),
            ("4.35.5M", AffectedStatus.AFFECTED),
            ("4.35.6M", AffectedStatus.NOT_AFFECTED),
            ("4.34.7M", AffectedStatus.AFFECTED),
            ("4.34.7.1M", AffectedStatus.NOT_AFFECTED),
            ("4.34.7.99M", AffectedStatus.NOT_AFFECTED),
            ("4.33.8M", AffectedStatus.AFFECTED),
            ("4.33.9M", AffectedStatus.NOT_AFFECTED),
            ("4.30.99M", AffectedStatus.AFFECTED),
            ("4.29.99M", AffectedStatus.NOT_AFFECTED),
        ),
    )


DATA: AntaUnitTestData = {
    (SA165, "failure-credentialz-enabled"): {
        "version": build_eos_version("4.36.0.1F"),
        "eos_data": [{"credentialzEnabled": True}],
        "expected": expected_result(AntaTestStatus.FAILURE, "gNSI Credentialz service is enabled", REMEDIATION),
    },
    (SA165, "success-credentialz-disabled-short-circuits-version"): {
        "version": None,
        "eos_data": [{"credentialzEnabled": False}],
        "expected": expected_result(AntaTestStatus.SUCCESS, "gNSI Credentialz service is disabled", None),
    },
    (SA165, "success-fixed-version"): {
        "version": build_eos_version("4.36.1F"),
        "eos_data": [{"credentialzEnabled": True}],
        "expected": expected_result(AntaTestStatus.SUCCESS, "outside the affected releases", None),
    },
    (SA165, "success-first-fixed-4.34-hotfix"): {
        "version": build_eos_version("4.34.7.1M"),
        "eos_data": [{"credentialzEnabled": True}],
        "expected": expected_result(AntaTestStatus.SUCCESS, "outside the affected releases", None),
    },
    (SA165, "error-missing-credentialz-state"): {
        "version": build_eos_version("4.36.0.1F"),
        "eos_data": [{}],
        "expected": expected_result(AntaTestStatus.ERROR, "gNSI Credentialz service state", None),
    },
}
