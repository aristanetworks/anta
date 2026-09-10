# Copyright (c) 2026 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
# ruff: noqa: D102
# pylint: disable=duplicate-code, missing-function-docstring
"""Unit tests for Arista Security Advisory 154."""

from __future__ import annotations

import unittest
from functools import partial
from typing import TYPE_CHECKING

from anta._advisory.eos_versions import AffectedStatus, evaluate_version
from anta._advisory.facts.eos import EosVersionFact
from anta._advisory.facts.models import AvailableFact, Fact, FactProblemKind, FactSource, FactSourceKind, FeatureName, FeatureState, FeatureValue, SubFeature
from anta._advisory.facts.routing import BfdAuthenticationFact
from anta._advisory.findings.models import AffectedResult, ErrorResult, NotAffectedResult
from anta._advisory.remediation import FixedRelease, software_version_plan
from anta._eos.version import EOSVersion, parse_eos_version
from anta.result_manager.models import AntaTestStatus
from anta.tests.advisories.sa_154 import ADVISORY, AFFECTED_VERSION_MATRIX, SA154, _assess_sa154
from tests.units.anta_tests import build_eos_version, test
from tests.units.anta_tests.advisories import build_expected_advisory_result

if TYPE_CHECKING:
    from tests.units.anta_tests import AntaUnitTestData

SOURCE = FactSource("unit test", FactSourceKind.DEVICE_METADATA)
EXPECTED_REMEDIATION = software_version_plan(
    (
        FixedRelease(EOSVersion(4, 36, 2, suffix="F")),
        FixedRelease(EOSVersion(4, 35, 6, suffix="M")),
        FixedRelease(EOSVersion(4, 34, 8, suffix="M")),
        FixedRelease(EOSVersion(4, 33, 9, suffix="M")),
    ),
    current_version=EOSVersion(4, 36, 1, suffix="F"),
)
expected = partial(build_expected_advisory_result, ADVISORY.vulnerabilities[0].id)


def eos_data(*, admin_down: object = False, global_config: str = "", interface_config: str = "") -> list[dict[str, object] | str]:
    """Return BFD administrative state and authentication configuration without peer data."""
    return [{"adminDown": admin_down}, global_config, interface_config]


DATA: AntaUnitTestData = {
    (SA154, "affected-authenticated-bfd"): {
        "version": build_eos_version("4.36.1F"),
        "eos_data": eos_data(global_config="router bfd\n   authentication mode md5 shared-secret profile test"),
        "expected": expected(
            AntaTestStatus.FAILURE,
            "The device is affected because EOS version '4.36.1F' is affected and the BFD authentication is enabled",
            EXPECTED_REMEDIATION,
        ),
    },
    (SA154, "not-affected-no-bfd-authentication"): {
        "version": None,
        "eos_data": eos_data(),
        "expected": expected(AntaTestStatus.SUCCESS, "The device is not affected because the BFD authentication is disabled", None),
    },
    (SA154, "not-affected-fixed-version"): {
        "version": build_eos_version("4.36.2F"),
        "eos_data": eos_data(global_config="router bfd\n   authentication mode md5 shared-secret profile test"),
        "expected": expected(AntaTestStatus.SUCCESS, "The device is not affected because EOS version '4.36.2F' is outside the affected releases", None),
    },
    (SA154, "error-malformed-bfd"): {
        "version": build_eos_version("4.36.1F"),
        "eos_data": eos_data(admin_down=None),
        "expected": expected(
            AntaTestStatus.ERROR,
            "The test could not determine the BFD authentication state because the 'show bfd peers summary' output is incomplete",
            None,
        ),
    },
}


def version_fact(value: str | None) -> Fact[EOSVersion]:
    """Build a version fact."""
    if value is None:
        return EosVersionFact.unavailable(FactProblemKind.MISSING, SOURCE)
    parsed = parse_eos_version(value).unwrap()
    return EosVersionFact.available(parsed, SOURCE)


def bfd_fact(state: FeatureState) -> AvailableFact[FeatureValue]:
    """Build a BFD authentication fact."""
    return BfdAuthenticationFact.available(FeatureValue(SubFeature(FeatureName.BFD, "authentication"), state), SOURCE)


class TestSA154Assessment(unittest.TestCase):
    """Validate version boundaries and pure assessment branches."""

    def test_version_boundaries(self) -> None:
        for version, state in (
            ("4.36.1F", AffectedStatus.AFFECTED),
            ("4.36.2F", AffectedStatus.NOT_AFFECTED),
            ("4.35.5M", AffectedStatus.AFFECTED),
            ("4.35.6M", AffectedStatus.NOT_AFFECTED),
            ("4.34.7M", AffectedStatus.AFFECTED),
            ("4.34.8M", AffectedStatus.NOT_AFFECTED),
            ("4.33.8M", AffectedStatus.AFFECTED),
            ("4.33.9M", AffectedStatus.NOT_AFFECTED),
            ("4.1.0F", AffectedStatus.AFFECTED),
        ):
            parsed = parse_eos_version(version).unwrap()
            assert evaluate_version(parsed, AFFECTED_VERSION_MATRIX).affected_status is state

    def test_assessment_states(self) -> None:
        assert isinstance(_assess_sa154(version_fact("4.36.1F"), bfd_fact(FeatureState.ENABLED)), AffectedResult)
        assert isinstance(_assess_sa154(version_fact(None), bfd_fact(FeatureState.DISABLED)), NotAffectedResult)
        malformed = BfdAuthenticationFact.unavailable(FactProblemKind.MALFORMED, SOURCE)
        assert isinstance(_assess_sa154(version_fact("4.36.1F"), malformed), ErrorResult)
