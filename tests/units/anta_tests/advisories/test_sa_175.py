# Copyright (c) 2026 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
# ruff: noqa: D102
# pylint: disable=duplicate-code, missing-function-docstring, redefined-outer-name
"""Unit tests for Arista Security Advisory 175."""

from __future__ import annotations

import unittest
from functools import partial
from typing import TYPE_CHECKING

from anta._advisory.eos_versions import AffectedStatus, evaluate_version
from anta._advisory.facts.eos import EosVersionFact
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
from anta._advisory.facts.routing import PimSparseModeFact
from anta._advisory.findings.models import AffectedResult, ErrorResult, NotAffectedResult, VersionRelation
from anta._advisory.remediation import FixedRelease, software_version_plan
from anta._eos.version import EOSVersion, parse_eos_version
from anta.result_manager.models import AntaTestStatus
from anta.tests.advisories.sa_175 import ADVISORY, AFFECTED_VERSION_MATRIX, SA175, _assess_sa175
from tests.units.anta_tests import build_eos_version, test
from tests.units.anta_tests.advisories import build_expected_advisory_result

if TYPE_CHECKING:
    from tests.units.anta_tests import AntaUnitTestData

SOURCE = FactSource("unit test", FactSourceKind.DEVICE_METADATA)
EXPECTED_FIXED_RELEASES = (
    FixedRelease(EOSVersion(4, 36, 2, suffix="F")),
    FixedRelease(EOSVersion(4, 35, 6, suffix="M")),
    FixedRelease(EOSVersion(4, 34, 8, suffix="M")),
    FixedRelease(EOSVersion(4, 33, 9, suffix="M")),
)
EXPECTED_4_35_REMEDIATION = software_version_plan(EXPECTED_FIXED_RELEASES, current_version=EOSVersion(4, 35, 5, suffix="M"))
EXPECTED_4_32_REMEDIATION = software_version_plan(EXPECTED_FIXED_RELEASES, current_version=EOSVersion(4, 32, 99, suffix="M"))
expected_result = partial(build_expected_advisory_result, ADVISORY.vulnerabilities[0].id)


DATA: AntaUnitTestData = {
    (SA175, "failure-canonical-ipv4-sparse-mode"): {
        "version": build_eos_version("4.35.5M"),
        "eos_data": ["pim ipv4 sparse-mode"],
        "expected": expected_result(
            AntaTestStatus.FAILURE,
            "The device is affected because EOS version '4.35.5M' is affected and the PIM sparse-mode interface is enabled",
            EXPECTED_4_35_REMEDIATION,
        ),
    },
    (SA175, "failure-legacy-ipv6-sparse-mode"): {
        "version": build_eos_version("4.32.99M"),
        "eos_data": ["ipv6 pim sparse-mode"],
        "expected": expected_result(
            AntaTestStatus.FAILURE,
            "The device is affected because EOS version '4.32.99M' is affected and the PIM sparse-mode interface is enabled",
            EXPECTED_4_32_REMEDIATION,
        ),
    },
    (SA175, "success-no-sparse-mode-short-circuits-version"): {
        "version": None,
        "eos_data": [""],
        "expected": expected_result(AntaTestStatus.SUCCESS, "The device is not affected because the PIM sparse-mode interface is disabled", None),
    },
    (SA175, "success-fixed-version-short-circuits-config"): {
        "version": build_eos_version("4.35.6M"),
        "eos_data": ["pim ipv4 sparse-mode extra"],
        "expected": expected_result(
            AntaTestStatus.SUCCESS,
            "The device is not affected because EOS version '4.35.6M' is outside the affected releases",
            None,
        ),
    },
    (SA175, "error-missing-version"): {
        "version": None,
        "eos_data": ["pim ipv4 sparse-mode"],
        "expected": expected_result(
            AntaTestStatus.ERROR,
            "The test could not determine the EOS version because it is missing from device metadata",
            None,
        ),
    },
    (SA175, "error-malformed-pim-output"): {
        "version": build_eos_version("4.35.5M"),
        "eos_data": ["pim ipv4 sparse-mode extra"],
        "expected": expected_result(
            AntaTestStatus.ERROR,
            "The test could not determine the PIM sparse-mode interface state because the 'show running-config | include pim.*sparse-mode' output is invalid",
            None,
        ),
    },
}


def version_fact(version: str | None) -> CollectedFact[EOSVersion]:
    """Build an EOS version fact for assessment tests."""
    if version is None:
        return EosVersionFact.unavailable(FactProblemKind.MISSING, SOURCE)
    parsed = parse_eos_version(version).unwrap()
    return EosVersionFact.available(parsed, SOURCE)


def sparse_mode_fact(state: FeatureState) -> AvailableFact[FeatureValue]:
    """Build a PIM sparse-mode fact."""
    return PimSparseModeFact.available(FeatureValue(SubFeature(FeatureName.PIM, "sparse-mode interface"), state), SOURCE)


class TestSA175VersionMatrix(unittest.TestCase):
    """Validate every source-published version boundary."""

    def test_version_boundaries(self) -> None:
        for version, expected in (
            ("4.37.0F", AffectedStatus.NOT_AFFECTED),
            ("4.36.1F", AffectedStatus.AFFECTED),
            ("4.36.1.99F", AffectedStatus.AFFECTED),
            ("4.36.2F", AffectedStatus.NOT_AFFECTED),
            ("4.35.5M", AffectedStatus.AFFECTED),
            ("4.35.6M", AffectedStatus.NOT_AFFECTED),
            ("4.34.7M", AffectedStatus.AFFECTED),
            ("4.34.7.1M", AffectedStatus.AFFECTED),
            ("4.34.7.99M", AffectedStatus.AFFECTED),
            ("4.34.8M", AffectedStatus.NOT_AFFECTED),
            ("4.33.8M", AffectedStatus.AFFECTED),
            ("4.33.9M", AffectedStatus.NOT_AFFECTED),
            ("4.32.99M", AffectedStatus.AFFECTED),
            ("4.31.0F", AffectedStatus.AFFECTED),
            ("4.1.0F", AffectedStatus.AFFECTED),
        ):
            with self.subTest(version=version):
                parsed = parse_eos_version(version).unwrap()
                assert evaluate_version(parsed, AFFECTED_VERSION_MATRIX).affected_status is expected


class TestSA175Assessment(unittest.TestCase):
    """Validate the pure SA175 assessment branches."""

    def test_sparse_mode_on_affected_version_is_affected(self) -> None:
        finding = _assess_sa175(version_fact("4.35.5M"), sparse_mode_fact(FeatureState.ENABLED))

        assert isinstance(finding, AffectedResult)
        assert finding.context[0].relation is VersionRelation.AFFECTED

    def test_no_sparse_mode_short_circuits_missing_version(self) -> None:
        finding = _assess_sa175(version_fact(None), sparse_mode_fact(FeatureState.DISABLED))

        assert isinstance(finding, NotAffectedResult)

    def test_fixed_version_short_circuits_missing_configuration(self) -> None:
        finding = _assess_sa175(
            version_fact("4.35.6M"),
            PimSparseModeFact.unavailable(FactProblemKind.MALFORMED, SOURCE),
        )

        assert isinstance(finding, NotAffectedResult)

    def test_unavailable_required_facts_are_errors(self) -> None:
        cases = (
            (version_fact(None), sparse_mode_fact(FeatureState.ENABLED), EosVersionFact),
            (version_fact("4.35.5M"), PimSparseModeFact.unavailable(FactProblemKind.MALFORMED, SOURCE), PimSparseModeFact),
        )
        for version, sparse_mode, expected_definition in cases:
            with self.subTest(expected_definition=expected_definition.key):
                finding = _assess_sa175(version, sparse_mode)
                assert isinstance(finding, ErrorResult)
                assert finding.problems[0].definition is expected_definition
