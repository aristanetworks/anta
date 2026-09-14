# Copyright (c) 2026 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
# ruff: noqa: D102
# pylint: disable=duplicate-code, missing-function-docstring
"""Unit tests for Arista Security Advisory 177."""

from __future__ import annotations

import unittest
from functools import partial
from typing import TYPE_CHECKING

from anta._advisory.eos_versions import AffectedStatus, evaluate_version
from anta._advisory.facts.eos import EosVersionFact
from anta._advisory.facts.models import Fact, FactDefinition, FactProblemKind, FactSource, FactSourceKind, FeatureName, FeatureState, FeatureValue, SubFeature
from anta._advisory.facts.network_services import MlagConfiguredFact
from anta._advisory.facts.platform import PlatformIdentityFact
from anta._advisory.facts.routing import PimSparseModeFact
from anta._advisory.findings.models import AffectedResult, ErrorResult, NotAffectedResult
from anta._advisory.remediation import FixedRelease, software_version_plan
from anta._eos.platform import PlatformFamily
from anta._eos.version import EOSVersion, parse_eos_version
from anta.result_manager.models import AntaTestStatus
from anta.tests.advisories.sa_177 import ADVISORY, AFFECTED_PLATFORM_FAMILIES, AFFECTED_VERSION_MATRIX, SA177, _assess_sa177
from tests.units.anta_tests import build_eos_platform, build_eos_version, test
from tests.units.anta_tests.advisories import build_expected_advisory_result

if TYPE_CHECKING:
    from anta._eos.platform import PlatformIdentity
    from tests.units.anta_tests import AntaUnitTestData

SOURCE = FactSource("unit test", FactSourceKind.DEVICE_METADATA)
EXPECTED_FIXED_RELEASES = (
    FixedRelease(EOSVersion(4, 36, 2, suffix="F")),
    FixedRelease(EOSVersion(4, 35, 6, suffix="M")),
    FixedRelease(EOSVersion(4, 34, 8, suffix="M")),
)
EXPECTED_REMEDIATION = software_version_plan(EXPECTED_FIXED_RELEASES, current_version=EOSVersion(4, 35, 5, suffix="M"))
expected = partial(build_expected_advisory_result, ADVISORY.vulnerabilities[0].id)
MLAG_CONFIGURED = {
    "domainId": "mlagDomain",
    "localInterface": "Vlan4094",
    "peerAddress": "192.0.2.2",
    "peerLink": "Port-Channel10",
    "state": "inactive",
}
MLAG_NOT_CONFIGURED: dict[str, object] = {}


DATA: AntaUnitTestData = {
    (SA177, "affected-pim-and-active-mlag"): {
        "version": build_eos_version("4.35.5M"),
        "platform": build_eos_platform("cEOSLab"),
        "eos_data": ["pim ipv4 sparse-mode", MLAG_CONFIGURED],
        "expected": expected(
            AntaTestStatus.FAILURE,
            "The device is affected because EOS version '4.35.5M' is affected, platform 'cEOSLab' is within the affected platform scope, "
            "the PIM sparse-mode interface is enabled, and the MLAG configuration is enabled",
            EXPECTED_REMEDIATION,
        ),
    },
    (SA177, "not-affected-without-pim"): {
        "version": None,
        "platform": None,
        "eos_data": ["", MLAG_NOT_CONFIGURED],
        "expected": expected(AntaTestStatus.SUCCESS, "The device is not affected because the PIM sparse-mode interface is disabled", None),
    },
    (SA177, "not-affected-without-configured-mlag"): {
        "version": None,
        "platform": None,
        "eos_data": ["pim ipv6 sparse-mode", MLAG_NOT_CONFIGURED],
        "expected": expected(AntaTestStatus.SUCCESS, "The device is not affected because the MLAG configuration is disabled", None),
    },
    (SA177, "not-affected-fixed-release"): {
        "version": build_eos_version("4.35.6M"),
        "platform": None,
        "eos_data": ["pim ipv4 sparse-mode", MLAG_CONFIGURED],
        "expected": expected(AntaTestStatus.SUCCESS, "The device is not affected because EOS version '4.35.6M' is outside the affected releases", None),
    },
    (SA177, "not-affected-platform"): {
        "version": None,
        "platform": build_eos_platform("DCS-DL-7700R4C-38PE-B"),
        "eos_data": ["pim ipv4 sparse-mode extra", MLAG_CONFIGURED],
        "expected": expected(
            AntaTestStatus.SUCCESS,
            "The device is not affected because platform 'DCS-DL-7700R4C-38PE-B' is outside the affected platform scope",
            None,
        ),
    },
    (SA177, "error-missing-version"): {
        "version": None,
        "platform": build_eos_platform("cEOSLab"),
        "eos_data": ["pim ipv4 sparse-mode", MLAG_CONFIGURED],
        "expected": expected(AntaTestStatus.ERROR, "The test could not determine the EOS version because it is missing from device metadata", None),
    },
    (SA177, "error-missing-platform"): {
        "version": build_eos_version("4.35.5M"),
        "platform": None,
        "eos_data": ["pim ipv4 sparse-mode", MLAG_CONFIGURED],
        "expected": expected(AntaTestStatus.ERROR, "The test could not determine the platform identity because it is missing from device metadata", None),
    },
    (SA177, "error-invalid-prerequisites"): {
        "version": build_eos_version("4.35.5M"),
        "platform": build_eos_platform("cEOSLab"),
        "eos_data": ["pim ipv4 sparse-mode extra", {**MLAG_CONFIGURED, "domainId": True}],
        "expected": expected(
            AntaTestStatus.ERROR,
            "The test could not determine the PIM sparse-mode interface state because the 'show running-config | include "
            "pim.*sparse-mode' output is invalid. The test could not determine the MLAG configuration state because the 'show mlag detail' output is invalid.",
            None,
        ),
    },
}


def version_fact(version: str | None) -> Fact[EOSVersion]:
    """Build an EOS version fact."""
    if version is None:
        return EosVersionFact.unavailable(FactProblemKind.MISSING, SOURCE)
    return EosVersionFact.available(parse_eos_version(version).unwrap(), SOURCE)


def platform_fact(model: str | None) -> Fact[PlatformIdentity]:
    """Build a platform identity fact."""
    if model is None:
        return PlatformIdentityFact.unavailable(FactProblemKind.MISSING, SOURCE)
    platform = build_eos_platform(model)
    assert platform is not None
    return PlatformIdentityFact.available(platform, SOURCE)


def feature_fact(definition: type[FactDefinition[FeatureValue]], feature: SubFeature, state: FeatureState) -> Fact[FeatureValue]:
    """Build one available feature fact."""
    return definition.available(FeatureValue(feature, state), SOURCE)


class TestSA177Assessment(unittest.TestCase):
    """Validate source boundaries and pure assessment branches."""

    def test_version_boundaries(self) -> None:
        for version, state in (
            ("4.37.0F", AffectedStatus.NOT_AFFECTED),
            ("4.36.1F", AffectedStatus.AFFECTED),
            ("4.36.2F", AffectedStatus.NOT_AFFECTED),
            ("4.35.5M", AffectedStatus.AFFECTED),
            ("4.35.6M", AffectedStatus.NOT_AFFECTED),
            ("4.34.1F", AffectedStatus.NOT_AFFECTED),
            ("4.34.2F", AffectedStatus.AFFECTED),
            ("4.34.7.1M", AffectedStatus.AFFECTED),
            ("4.34.8M", AffectedStatus.NOT_AFFECTED),
            ("4.33.99M", AffectedStatus.NOT_AFFECTED),
        ):
            with self.subTest(version=version):
                assert evaluate_version(parse_eos_version(version).unwrap(), AFFECTED_VERSION_MATRIX).affected_status is state

    def test_platform_scope_matches_source(self) -> None:
        assert {
            PlatformFamily.SERIES_710,
            PlatformFamily.SERIES_720_D,
            PlatformFamily.SERIES_720_XP,
            PlatformFamily.SERIES_722_XPM,
            PlatformFamily.SERIES_750_X,
            PlatformFamily.SERIES_7010_TX,
            PlatformFamily.SERIES_7020_R,
            PlatformFamily.SERIES_7020_R4,
            PlatformFamily.SERIES_7130,
            PlatformFamily.SERIES_7170,
            PlatformFamily.SERIES_7050_X3,
            PlatformFamily.SERIES_7050_X4,
            PlatformFamily.SERIES_7060_X,
            PlatformFamily.SERIES_7060_X2,
            PlatformFamily.SERIES_7060_X4,
            PlatformFamily.SERIES_7060_X5,
            PlatformFamily.SERIES_7060_X6,
            PlatformFamily.SERIES_7260_X,
            PlatformFamily.SERIES_7260_X3,
            PlatformFamily.SERIES_7280_R,
            PlatformFamily.SERIES_7280_R2,
            PlatformFamily.SERIES_7280_R3,
            PlatformFamily.SERIES_7280_R4,
            PlatformFamily.SERIES_7300_X,
            PlatformFamily.SERIES_7300_X3,
            PlatformFamily.SERIES_7320_X,
            PlatformFamily.SERIES_7358_X4,
            PlatformFamily.SERIES_7388_X5,
            PlatformFamily.SERIES_7500_R,
            PlatformFamily.SERIES_7500_R2,
            PlatformFamily.SERIES_7500_R3,
            PlatformFamily.SERIES_7800_R3,
            PlatformFamily.SERIES_7800_R4,
            PlatformFamily.CEOS_LAB,
            PlatformFamily.VEOS_LAB,
        } == AFFECTED_PLATFORM_FAMILIES

    def test_assessment_states(self) -> None:
        pim_enabled = feature_fact(PimSparseModeFact, SubFeature(FeatureName.PIM, "sparse-mode interface"), FeatureState.ENABLED)
        pim_disabled = feature_fact(PimSparseModeFact, SubFeature(FeatureName.PIM, "sparse-mode interface"), FeatureState.DISABLED)
        mlag_configured = feature_fact(MlagConfiguredFact, SubFeature(FeatureName.MLAG, "configuration"), FeatureState.ENABLED)
        mlag_not_configured = feature_fact(MlagConfiguredFact, SubFeature(FeatureName.MLAG, "configuration"), FeatureState.DISABLED)

        assert isinstance(_assess_sa177(version_fact("4.35.5M"), platform_fact("cEOSLab"), pim_enabled, mlag_configured), AffectedResult)
        assert isinstance(_assess_sa177(version_fact(None), platform_fact(None), pim_disabled, mlag_configured), NotAffectedResult)
        assert isinstance(_assess_sa177(version_fact(None), platform_fact(None), pim_enabled, mlag_not_configured), NotAffectedResult)
        assert isinstance(_assess_sa177(version_fact("4.35.6M"), platform_fact(None), pim_enabled, mlag_configured), NotAffectedResult)
        assert isinstance(_assess_sa177(version_fact(None), platform_fact("DCS-DL-7700R4C-38PE-B"), pim_enabled, mlag_configured), NotAffectedResult)
        assert isinstance(_assess_sa177(version_fact(None), platform_fact("cEOSLab"), pim_enabled, mlag_configured), ErrorResult)
        assert isinstance(_assess_sa177(version_fact("4.35.5M"), platform_fact("DCS-UNRECOGNIZED"), pim_enabled, mlag_configured), ErrorResult)

    def test_unavailable_prerequisites_are_preserved(self) -> None:
        finding = _assess_sa177(
            version_fact("4.35.5M"),
            platform_fact("cEOSLab"),
            PimSparseModeFact.unavailable(FactProblemKind.MALFORMED, SOURCE),
            MlagConfiguredFact.unavailable(FactProblemKind.MISSING, SOURCE),
        )
        assert isinstance(finding, ErrorResult)
        assert tuple(problem.definition for problem in finding.problems) == (PimSparseModeFact, MlagConfiguredFact)

    def test_unavailable_scope_facts_are_preserved(self) -> None:
        pim_enabled = feature_fact(PimSparseModeFact, SubFeature(FeatureName.PIM, "sparse-mode interface"), FeatureState.ENABLED)
        mlag_configured = feature_fact(MlagConfiguredFact, SubFeature(FeatureName.MLAG, "configuration"), FeatureState.ENABLED)
        finding = _assess_sa177(version_fact(None), platform_fact(None), pim_enabled, mlag_configured)
        assert isinstance(finding, ErrorResult)
        assert tuple(problem.definition for problem in finding.problems) == (EosVersionFact, PlatformIdentityFact)
