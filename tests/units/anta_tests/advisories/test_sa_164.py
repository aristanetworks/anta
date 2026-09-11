# Copyright (c) 2026 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
# ruff: noqa: D102
# pylint: disable=duplicate-code, missing-function-docstring, redefined-outer-name
"""Unit tests for Arista Security Advisory 164."""

from __future__ import annotations

import unittest
from functools import partial
from typing import TYPE_CHECKING, Any, cast

from anta._advisory.eos_versions import AffectedStatus, evaluate_version
from anta._advisory.facts.eos import EosVersionFact
from anta._advisory.facts.management import GnmiTransportFact, GnsiPathzFact, GnsiPathzPolicyOverlapFact
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
from anta._advisory.findings.models import AffectedResult, ErrorResult, NotAffectedResult, VersionRelation
from anta._advisory.remediation import FixedRelease, software_version_plan
from anta._eos.version import EOSVersion, parse_eos_version
from anta.result_manager.models import AntaTestStatus
from anta.tests.advisories.sa_164 import ADVISORY, AFFECTED_VERSION_MATRIX, SA164, _assess_sa164
from tests.units.anta_tests import build_eos_version, test
from tests.units.anta_tests.advisories import build_expected_advisory_result

if TYPE_CHECKING:
    from tests.units.anta_tests import AntaUnitTestData

SOURCE = FactSource("unit test", FactSourceKind.DEVICE_METADATA)
EXPECTED_REMEDIATION = software_version_plan(
    (
        FixedRelease(EOSVersion(4, 36, 1, suffix="F")),
        FixedRelease(EOSVersion(4, 35, 6, suffix="M")),
        FixedRelease(EOSVersion(4, 34, 7, suffix="M")),
        FixedRelease(EOSVersion(4, 33, 9, suffix="M")),
    ),
    current_version=EOSVersion(4, 35, 5, suffix="M"),
)
expected_result = partial(build_expected_advisory_result, ADVISORY.vulnerabilities[0].id)
OVERLAPPING_POLICY = '{"rules": [{"user": "alice", "path": {"elem": [{"name": "interfaces"}]}}, {"group": "operators", "path": {"elem": [{"name": "interfaces"}]}}]}'
DISJOINT_POLICY = '{"rules": [{"user": "alice", "path": {"elem": [{"name": "interfaces"}]}}, {"group": "operators", "path": {"elem": [{"name": "system"}]}}]}'


_DATA: AntaUnitTestData = {
    (SA164, "affected-overlapping-policy"): {
        "version": build_eos_version("4.35.5M"),
        "eos_data": [{"transports": {"default": {"enabled": True}}}, {"pathzEnabled": True}, OVERLAPPING_POLICY],
        "expected": expected_result(
            AntaTestStatus.FAILURE,
            "the gNSI Pathz policy user/group overlap is enabled",
            EXPECTED_REMEDIATION,
        ),
    },
    (SA164, "not-affected-disjoint-policy"): {
        "version": build_eos_version("4.35.5M"),
        "eos_data": [{"transports": {"default": {"enabled": True}}}, {"pathzEnabled": True}, DISJOINT_POLICY],
        "expected": expected_result(AntaTestStatus.SUCCESS, "the gNSI Pathz policy user/group overlap is disabled", None),
    },
    (SA164, "not-affected-no-policy"): {
        "version": build_eos_version("4.35.5M"),
        "eos_data": [{"transports": {"default": {"enabled": True}}}, {"pathzEnabled": True}, "null"],
        "expected": expected_result(AntaTestStatus.SUCCESS, "the gNSI Pathz policy user/group overlap is disabled", None),
    },
    (SA164, "success-pathz-disabled-with-missing-gnmi"): {
        "version": build_eos_version("4.35.5M"),
        "eos_data": [{}, {"pathzEnabled": False}, ""],
        "expected": expected_result(AntaTestStatus.SUCCESS, "The device is not affected because the gNSI Pathz service is disabled", None),
    },
    (SA164, "success-no-enabled-gnmi-with-missing-pathz"): {
        "version": build_eos_version("4.35.5M"),
        "eos_data": [{"transports": {}}, {}, ""],
        "expected": expected_result(AntaTestStatus.SUCCESS, "The device is not affected because the gNMI feature is disabled", None),
    },
    (SA164, "success-fixed-version"): {
        "version": build_eos_version("4.35.6M"),
        "eos_data": [{}, {}, ""],
        "expected": expected_result(
            AntaTestStatus.SUCCESS,
            "The device is not affected because EOS version '4.35.6M' is outside the affected releases",
            None,
        ),
    },
    (SA164, "error-missing-version"): {
        "version": None,
        "eos_data": [{}, {}, ""],
        "expected": expected_result(
            AntaTestStatus.ERROR,
            "The test could not determine the EOS version because it is missing from device metadata",
            None,
        ),
    },
    (SA164, "error-missing-gnmi-state"): {
        "version": build_eos_version("4.35.5M"),
        "eos_data": [{}, {"pathzEnabled": True}, OVERLAPPING_POLICY],
        "expected": expected_result(
            AntaTestStatus.ERROR,
            "The test could not determine the gNMI transport state because the 'show management api gnmi' output is invalid",
            None,
        ),
    },
    (SA164, "error-missing-pathz-state"): {
        "version": build_eos_version("4.35.5M"),
        "eos_data": [{"transports": {"default": {"enabled": True}}}, {}, OVERLAPPING_POLICY],
        "expected": expected_result(
            AntaTestStatus.ERROR,
            "The test could not determine the gNSI Pathz service state because the 'show management api gnsi' output is incomplete",
            None,
        ),
    },
    (SA164, "error-malformed-policy"): {
        "version": build_eos_version("4.35.5M"),
        "eos_data": [{"transports": {"default": {"enabled": True}}}, {"pathzEnabled": True}, "{"],
        "expected": expected_result(AntaTestStatus.ERROR, "The test could not determine the Pathz policy user/group overlap", None),
    },
}


def version_fact(version: str | None) -> CollectedFact[EOSVersion]:
    """Build an EOS version fact for assessment tests."""
    if version is None:
        return EosVersionFact.unavailable(FactProblemKind.MISSING, SOURCE)
    parsed = parse_eos_version(version).unwrap()
    return EosVersionFact.available(parsed, SOURCE)


def feature_fact(
    definition: type[GnmiTransportFact | GnsiPathzFact | GnsiPathzPolicyOverlapFact],
    feature: FeatureName | SubFeature,
    state: FeatureState,
) -> AvailableFact[FeatureValue]:
    """Build a normalized management-feature fact."""
    return definition.available(FeatureValue(feature, state), SOURCE)


class TestSA164VersionMatrix(unittest.TestCase):
    """Validate every source-published version boundary."""

    def test_version_boundaries(self) -> None:
        for version, expected in (
            ("4.36.0.1F", AffectedStatus.AFFECTED),
            ("4.36.0.99F", AffectedStatus.AFFECTED),
            ("4.36.1F", AffectedStatus.NOT_AFFECTED),
            ("4.35.5M", AffectedStatus.AFFECTED),
            ("4.35.6M", AffectedStatus.NOT_AFFECTED),
            ("4.34.6M", AffectedStatus.AFFECTED),
            ("4.34.7M", AffectedStatus.NOT_AFFECTED),
            ("4.33.1F", AffectedStatus.NOT_AFFECTED),
            ("4.33.2F", AffectedStatus.AFFECTED),
            ("4.33.8M", AffectedStatus.AFFECTED),
            ("4.33.9M", AffectedStatus.NOT_AFFECTED),
            ("4.32.99M", AffectedStatus.NOT_AFFECTED),
            ("4.37.0F", AffectedStatus.NOT_AFFECTED),
        ):
            with self.subTest(version=version):
                parsed = parse_eos_version(version).unwrap()
                assert evaluate_version(parsed, AFFECTED_VERSION_MATRIX).affected_status is expected


class TestSA164Assessment(unittest.TestCase):
    """Validate the pure SA164 assessment branches."""

    @staticmethod
    def enabled_facts() -> tuple[AvailableFact[FeatureValue], AvailableFact[FeatureValue], AvailableFact[FeatureValue]]:
        """Return active gNMI, Pathz, and policy-overlap facts."""
        return (
            feature_fact(GnmiTransportFact, FeatureName.GNMI, FeatureState.ENABLED),
            feature_fact(GnsiPathzFact, SubFeature(FeatureName.GNSI, "Pathz service"), FeatureState.ENABLED),
            feature_fact(GnsiPathzPolicyOverlapFact, SubFeature(FeatureName.GNSI, "Pathz policy user/group overlap"), FeatureState.ENABLED),
        )

    def test_overlapping_policy_is_affected(self) -> None:
        gnmi, pathz, overlap = self.enabled_facts()
        finding = _assess_sa164(version_fact("4.35.5M"), gnmi, pathz, overlap)

        assert isinstance(finding, AffectedResult)
        assert len(finding.conditions) == 3
        assert finding.remediation == EXPECTED_REMEDIATION

    def test_either_false_prerequisite_closes_the_path(self) -> None:
        _gnmi, pathz, overlap = self.enabled_facts()
        cases = (
            (
                GnmiTransportFact.unavailable(FactProblemKind.MISSING, SOURCE),
                feature_fact(GnsiPathzFact, pathz.value.feature, FeatureState.DISABLED),
                GnsiPathzFact,
            ),
            (
                feature_fact(GnmiTransportFact, FeatureName.GNMI, FeatureState.DISABLED),
                GnsiPathzFact.unavailable(FactProblemKind.MISSING, SOURCE),
                GnmiTransportFact,
            ),
        )
        for gnmi_fact, pathz_fact, expected in cases:
            with self.subTest(expected=expected.key):
                finding = _assess_sa164(version_fact("4.35.5M"), gnmi_fact, pathz_fact, overlap)
                assert isinstance(finding, NotAffectedResult)
                assert cast("Any", finding.decisive[0]).definition is expected

    def test_fixed_version_short_circuits_configuration(self) -> None:
        finding = _assess_sa164(
            version_fact("4.35.6M"),
            GnmiTransportFact.unavailable(FactProblemKind.MISSING, SOURCE),
            GnsiPathzFact.unavailable(FactProblemKind.MISSING, SOURCE),
            GnsiPathzPolicyOverlapFact.unavailable(FactProblemKind.MISSING, SOURCE),
        )

        assert isinstance(finding, NotAffectedResult)
        assert cast("Any", finding.decisive[0]).relation is VersionRelation.OUTSIDE_SCOPE

    def test_unavailable_required_facts_are_errors(self) -> None:
        gnmi, pathz, overlap = self.enabled_facts()
        cases = (
            (version_fact(None), gnmi, pathz, overlap, 1),
            (version_fact("4.35.5M"), GnmiTransportFact.unavailable(FactProblemKind.MALFORMED, SOURCE), pathz, overlap, 1),
            (version_fact("4.35.5M"), gnmi, GnsiPathzFact.unavailable(FactProblemKind.MISSING, SOURCE), overlap, 1),
            (version_fact("4.35.5M"), gnmi, pathz, GnsiPathzPolicyOverlapFact.unavailable(FactProblemKind.MALFORMED, SOURCE), 1),
            (
                version_fact("4.35.5M"),
                GnmiTransportFact.unavailable(FactProblemKind.MALFORMED, SOURCE),
                GnsiPathzFact.unavailable(FactProblemKind.MISSING, SOURCE),
                GnsiPathzPolicyOverlapFact.unavailable(FactProblemKind.MALFORMED, SOURCE),
                3,
            ),
        )
        for version, gnmi_fact, pathz_fact, overlap_fact, expected_count in cases:
            with self.subTest(expected_count=expected_count):
                finding = _assess_sa164(version, gnmi_fact, pathz_fact, overlap_fact)
                assert isinstance(finding, ErrorResult)
                assert len(finding.problems) == expected_count
