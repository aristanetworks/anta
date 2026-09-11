# Copyright (c) 2026 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
# ruff: noqa: D102
# pylint: disable=duplicate-code, missing-function-docstring, redefined-outer-name
"""Unit tests for Arista Security Advisory 176."""

from __future__ import annotations

import unittest
from functools import partial
from typing import TYPE_CHECKING

from anta._advisory.eos_versions import AffectedStatus, evaluate_version
from anta._advisory.facts.eos import EosVersionFact
from anta._advisory.facts.models import (
    AvailableFact,
    Fact,
    FactProblemKind,
    FactSource,
    FactSourceKind,
    FeatureName,
    FeatureState,
    FeatureValue,
    SubFeature,
)
from anta._advisory.facts.platform import PlatformIdentityFact, SwitchCardIdentityFact
from anta._advisory.facts.routing import LooseUrpfFact
from anta._advisory.findings.models import AffectedResult, ErrorResult, NotAffectedResult
from anta._advisory.remediation import FixedRelease, software_version_plan
from anta._eos.version import EOSVersion, parse_eos_version
from anta.result_manager.models import AntaTestStatus
from anta.tests.advisories.sa_176 import ADVISORY, AFFECTED_VERSION_MATRIX, SA176, _assess_sa176
from tests.units.anta_tests import build_eos_platform, build_eos_version, test
from tests.units.anta_tests.advisories import build_expected_advisory_result

if TYPE_CHECKING:
    from anta._eos.platform import PlatformComponentIdentity, PlatformIdentity
    from tests.units.anta_tests import AntaUnitTestData

SOURCE = FactSource("unit test", FactSourceKind.DEVICE_METADATA)
EXPECTED_FIXED_RELEASES = (FixedRelease(EOSVersion(4, 36, 0, suffix="F")), FixedRelease(EOSVersion(4, 35, 5, suffix="M")))
EXPECTED_4_35_4_REMEDIATION = software_version_plan(EXPECTED_FIXED_RELEASES, current_version=EOSVersion(4, 35, 4, suffix="M"))
EXPECTED_4_35_2_REMEDIATION = software_version_plan(EXPECTED_FIXED_RELEASES, current_version=EOSVersion(4, 35, 2, suffix="F"))
expected_result = partial(build_expected_advisory_result, ADVISORY.vulnerabilities[0].id)


def modules(model: str) -> dict[str, object]:
    """Return minimal structured module inventory."""
    return {"modules": {"Switchcard1": {"modelName": model}}}


_DATA: AntaUnitTestData = {
    (SA176, "failure-7050x4-loose-ipv4-urpf"): {
        "version": build_eos_version("4.35.4M"),
        "platform": build_eos_platform("DCS-7050CX4-40D"),
        "eos_data": ["ip verify unicast source reachable-via any"],
        "expected": expected_result(
            AntaTestStatus.FAILURE,
            "The device is affected because EOS version '4.35.4M' is affected, platform 'DCS-7050CX4-40D' is within the affected platform "
            "scope, and the uRPF loose-mode interface is enabled",
            EXPECTED_4_35_4_REMEDIATION,
        ),
    },
    (SA176, "failure-7358x4-switch-card-loose-ipv6-urpf"): {
        "version": build_eos_version("4.35.2F"),
        "platform": build_eos_platform("7368-F", modules("7358X4-SC")),
        "eos_data": ["ipv6 verify unicast source reachable-via any allow-default"],
        "expected": expected_result(
            AntaTestStatus.FAILURE,
            "The device is affected because EOS version '4.35.2F' is affected, switch card '7358X4-SC' is within the affected platform scope, "
            "and the uRPF loose-mode interface is enabled",
            EXPECTED_4_35_2_REMEDIATION,
        ),
    },
    (SA176, "success-no-loose-urpf-short-circuits-other-facts"): {
        "version": None,
        "platform": None,
        "eos_data": [""],
        "expected": expected_result(AntaTestStatus.SUCCESS, "The device is not affected because the uRPF loose-mode interface is disabled", None),
    },
    (SA176, "success-fixed-version-short-circuits-platform"): {
        "version": build_eos_version("4.35.5M"),
        "platform": None,
        "eos_data": ["ip verify unicast source reachable-via any"],
        "expected": expected_result(
            AntaTestStatus.SUCCESS,
            "The device is not affected because EOS version '4.35.5M' is outside the affected releases",
            None,
        ),
    },
    (SA176, "success-unaffected-platform"): {
        "version": build_eos_version("4.35.4M"),
        "platform": build_eos_platform("DCS-7050CX3-32S"),
        "eos_data": ["ip verify unicast source reachable-via any"],
        "expected": expected_result(
            AntaTestStatus.SUCCESS,
            "The device is not affected because platform 'DCS-7050CX3-32S' is outside the affected platform scope",
            None,
        ),
    },
    (SA176, "success-7368x4-switch-card"): {
        "version": build_eos_version("4.35.4M"),
        "platform": build_eos_platform("DCS-7368-CH", modules("7368X4-SC")),
        "eos_data": ["ip verify unicast source reachable-via any"],
        "expected": expected_result(
            AntaTestStatus.SUCCESS,
            "The device is not affected because switch card '7368X4-SC' is outside the affected platform scope",
            None,
        ),
    },
    (SA176, "error-missing-version"): {
        "version": None,
        "platform": build_eos_platform("DCS-7050CX4-40D"),
        "eos_data": ["ip verify unicast source reachable-via any"],
        "expected": expected_result(
            AntaTestStatus.ERROR,
            "The test could not determine the EOS version because it is missing from device metadata",
            None,
        ),
    },
    (SA176, "error-missing-switch-card-on-modular-chassis"): {
        "version": build_eos_version("4.35.4M"),
        "platform": build_eos_platform("7358-R"),
        "eos_data": ["ip verify unicast source reachable-via any"],
        "expected": expected_result(
            AntaTestStatus.ERROR,
            "The test could not determine the switch-card platform identity because it is missing from device metadata",
            None,
        ),
    },
    (SA176, "error-malformed-loose-urpf-output"): {
        "version": build_eos_version("4.35.4M"),
        "platform": build_eos_platform("DCS-7050CX4-40D"),
        "eos_data": ["ip verify unicast source reachable-via rx"],
        "expected": expected_result(
            AntaTestStatus.ERROR,
            "The test could not determine the loose uRPF interface state because the "
            "'show running-config | include verify unicast source reachable-via any' output is invalid",
            None,
        ),
    },
}


def version_fact(version: str | None) -> Fact[EOSVersion]:
    """Build an EOS version fact for assessment tests."""
    if version is None:
        return EosVersionFact.unavailable(FactProblemKind.MISSING, SOURCE)
    parsed = parse_eos_version(version).unwrap()
    return EosVersionFact.available(parsed, SOURCE)


def platform_fact(model: str | None) -> Fact[PlatformIdentity]:
    """Build a platform identity fact."""
    if model is None:
        return PlatformIdentityFact.unavailable(FactProblemKind.MISSING, SOURCE)
    platform = build_eos_platform(model)
    assert platform is not None
    return PlatformIdentityFact.available(platform, SOURCE)


def switch_card_fact(model: str | None) -> Fact[PlatformComponentIdentity]:
    """Build a switch-card identity fact."""
    if model is None:
        return SwitchCardIdentityFact.unavailable(FactProblemKind.MISSING, SOURCE)
    platform = build_eos_platform("7368-F", modules(model))
    assert platform is not None
    switch_card = next(module for module in platform.modules if module.model == model)
    return SwitchCardIdentityFact.available(switch_card, SOURCE)


def loose_urpf_fact(state: FeatureState) -> AvailableFact[FeatureValue]:
    """Build a loose-uRPF feature fact."""
    return LooseUrpfFact.available(FeatureValue(SubFeature(FeatureName.URPF, "loose-mode interface"), state), SOURCE)


class TestSA176VersionMatrix(unittest.TestCase):
    """Validate the source range and confirmed fixed releases."""

    def test_version_boundaries(self) -> None:
        for version, expected in (
            ("4.35.0F", AffectedStatus.AFFECTED),
            ("4.35.1F", AffectedStatus.AFFECTED),
            ("4.35.2F", AffectedStatus.AFFECTED),
            ("4.35.4.99M", AffectedStatus.AFFECTED),
            ("4.35.5M", AffectedStatus.NOT_AFFECTED),
            ("4.36.0F", AffectedStatus.NOT_AFFECTED),
            ("4.34.99M", AffectedStatus.NOT_AFFECTED),
        ):
            with self.subTest(version=version):
                parsed = parse_eos_version(version).unwrap()
                assert evaluate_version(parsed, AFFECTED_VERSION_MATRIX).affected_status is expected


class TestSA176Assessment(unittest.TestCase):
    """Validate platform resolution and safe short-circuits."""

    def test_platform_variants(self) -> None:
        cases = (
            ("DCS-7050CX4-40D", None, AffectedResult),
            ("7358-R", "7358X4-SC", AffectedResult),
            ("7368-F", "7358X4-SC", AffectedResult),
            ("DCS-7368-CH", "7368X4-SC", NotAffectedResult),
            ("DCS-7050CX3-32S", None, NotAffectedResult),
        )
        for platform, switch_card, expected_type in cases:
            with self.subTest(platform=platform, switch_card=switch_card):
                finding = _assess_sa176(
                    version_fact("4.35.4M"),
                    platform_fact(platform),
                    switch_card_fact(switch_card),
                    loose_urpf_fact(FeatureState.ENABLED),
                )
                assert isinstance(finding, expected_type)

    def test_positive_switch_card_resolves_missing_chassis_identity(self) -> None:
        finding = _assess_sa176(
            version_fact("4.35.4M"),
            platform_fact(None),
            switch_card_fact("7358X4-SC"),
            loose_urpf_fact(FeatureState.ENABLED),
        )

        assert isinstance(finding, AffectedResult)

    def test_missing_switch_card_on_modular_chassis_is_error(self) -> None:
        finding = _assess_sa176(
            version_fact("4.35.4M"),
            platform_fact("7368-F"),
            switch_card_fact(None),
            loose_urpf_fact(FeatureState.ENABLED),
        )

        assert isinstance(finding, ErrorResult)

    def test_unknown_platform_is_error(self) -> None:
        finding = _assess_sa176(
            version_fact("4.35.4M"),
            platform_fact("DCS-UNRECOGNIZED"),
            switch_card_fact(None),
            loose_urpf_fact(FeatureState.ENABLED),
        )

        assert isinstance(finding, ErrorResult)

    def test_no_loose_urpf_short_circuits_missing_applicability(self) -> None:
        finding = _assess_sa176(
            version_fact(None),
            platform_fact(None),
            switch_card_fact(None),
            loose_urpf_fact(FeatureState.DISABLED),
        )

        assert isinstance(finding, NotAffectedResult)
