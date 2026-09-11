# Copyright (c) 2026 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
# ruff: noqa: D102
# pylint: disable=duplicate-code, missing-function-docstring, redefined-outer-name
"""Unit tests for Arista Security Advisory 173."""

from __future__ import annotations

import unittest
from typing import TYPE_CHECKING, Any, Literal, TypeAlias

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
    MitigationState,
    MitigationValue,
    SubFeature,
)
from anta._advisory.facts.routing import LegacyOspfv3ConfiguredFact, Ospfv3ConfiguredFact, Ospfv3IpsecAuthenticationFact
from anta._advisory.facts.software import SA173HotfixFact
from anta._advisory.findings.models import AffectedResult, ErrorResult, MitigatedResult, NotAffectedResult, VersionRelation
from anta._advisory.remediation import FixedRelease, RemediationPlan, software_version_plan
from anta._eos.version import EOSVersion, parse_eos_version
from anta.result_manager.models import AntaTestStatus
from anta.tests.advisories.sa_173 import ADVISORY, AFFECTED_VERSION_MATRIX, HOTFIX_RELEASES, SA173, _assess_sa173
from tests.units.anta_tests import build_eos_version, test
from tests.units.anta_tests.advisories import build_expected_advisory_result

if TYPE_CHECKING:
    from tests.units.anta_tests import AntaUnitTestData, UnitTestResult

SOURCE = FactSource("unit test", FactSourceKind.DEVICE_METADATA)
ProductionStatus: TypeAlias = Literal[AntaTestStatus.SUCCESS, AntaTestStatus.FAILURE, AntaTestStatus.ERROR]
EMPTY_OSPFV3: dict[str, Any] = {"vrfs": {}}
CURRENT_OSPFV3: dict[str, Any] = {"vrfs": {"default": {"addressFamily": {"ipv6": {}}}}}
CURRENT_OSPFV3_NON_DEFAULT: dict[str, Any] = {"vrfs": {"TOTO": {"addressFamily": {"ipv6": {}}}}}
LEGACY_OSPFV3: dict[str, Any] = {"vrfs": {"default": {"instList": {"0": {}}}}}
MALFORMED_OSPFV3: dict[str, Any] = {"vrfs": []}
UNAUTHENTICATED_CONFIG = "interface Ethernet1\n   ospfv3 ipv6 area 0.0.0.0\nrouter ospfv3\n   router-id 1.1.1.1"
UNAUTHENTICATED_NON_DEFAULT_CONFIG = "interface Ethernet1\n   vrf TOTO\n   ospfv3 ipv6 area 0.0.0.0\nrouter ospfv3 vrf TOTO\n   router-id 1.1.1.1"
INTERFACE_AUTHENTICATION = "interface Ethernet1\n   ospfv3 authentication ipsec spi 35 md5 passphrase 7 REDACTED\n   ospfv3 ipv6 area 0.0.0.0\nrouter ospfv3"
AREA_AUTHENTICATION = "interface Ethernet1\n   ospfv3 ipv6 area 0.0.0.0\nrouter ospfv3\n   area 0.0.0.0 authentication ipsec spi 34 md5 passphrase 7 REDACTED"
PARTIAL_AUTHENTICATION = (
    "interface Ethernet1\n   ospfv3 authentication ipsec spi 35 md5 passphrase 7 REDACTED\n   ospfv3 ipv6 area 0.0.0.0\n"
    "interface Ethernet2\n   ospfv3 ipv6 area 0.0.0.1\nrouter ospfv3"
)
EXPECTED_FIXED_RELEASES = (
    FixedRelease(EOSVersion(4, 36, 1, suffix="F")),
    FixedRelease(EOSVersion(4, 35, 5, suffix="M")),
    FixedRelease(EOSVersion(4, 34, 7, suffix="M")),
    FixedRelease(EOSVersion(4, 33, 9, suffix="M")),
)


def eos_data(
    current: dict[str, Any],
    legacy: dict[str, Any],
    config: str,
    extensions: dict[str, Any] | None = None,
    boot_extensions: list[str] | None = None,
) -> list[dict[str, Any] | str]:
    """Supply output to every fact-owned command wrapper."""
    return [current, legacy, config, {"extensions": extensions or {}}, {"extensions": boot_extensions or []}]


def expected_remediation(version: str) -> RemediationPlan:
    """Build the expected version remediation independently from production constants."""
    return software_version_plan(EXPECTED_FIXED_RELEASES, current_version=parse_eos_version(version).unwrap())


def expected_result(status: ProductionStatus, message: str, remediation: RemediationPlan | None) -> UnitTestResult:
    """Build matching parent and atomic expectations for one production case."""
    return build_expected_advisory_result(ADVISORY.vulnerabilities[0].id, status, message, remediation)


_DATA: AntaUnitTestData = {
    (SA173, "failure-configured-without-authentication"): {
        "version": build_eos_version("4.35.4M"),
        "eos_data": eos_data(CURRENT_OSPFV3, EMPTY_OSPFV3, UNAUTHENTICATED_CONFIG),
        "expected": expected_result(
            AntaTestStatus.FAILURE,
            "The device is affected because EOS version '4.35.4M' is affected and the OSPFv3 routing process is enabled",
            expected_remediation("4.35.4M"),
        ),
    },
    (SA173, "failure-partial-authentication-coverage"): {
        "version": build_eos_version("4.33.8M"),
        "eos_data": eos_data(CURRENT_OSPFV3, EMPTY_OSPFV3, PARTIAL_AUTHENTICATION),
        "expected": expected_result(
            AntaTestStatus.FAILURE,
            "The device is affected because EOS version '4.33.8M' is affected and the OSPFv3 routing process is enabled",
            expected_remediation("4.33.8M"),
        ),
    },
    (SA173, "failure-configured-in-non-default-vrf"): {
        "version": build_eos_version("4.35.4M"),
        "eos_data": eos_data(CURRENT_OSPFV3_NON_DEFAULT, EMPTY_OSPFV3, UNAUTHENTICATED_NON_DEFAULT_CONFIG),
        "expected": expected_result(
            AntaTestStatus.FAILURE,
            "The device is affected because EOS version '4.35.4M' is affected and the OSPFv3 routing process is enabled",
            expected_remediation("4.35.4M"),
        ),
    },
    (SA173, "mitigated-interface-authentication"): {
        "version": build_eos_version("4.36.0F"),
        "eos_data": eos_data(CURRENT_OSPFV3, EMPTY_OSPFV3, INTERFACE_AUTHENTICATION),
        "expected": expected_result(
            AntaTestStatus.SUCCESS,
            (
                "The device is affected but mitigated because EOS version '4.36.0F' is affected and the OSPFv3 routing process is enabled and "
                "OSPFv3 IPsec authentication coverage is effective"
            ),
            expected_remediation("4.36.0F"),
        ),
    },
    (SA173, "mitigated-area-authentication"): {
        "version": build_eos_version("4.34.6M"),
        "eos_data": eos_data(CURRENT_OSPFV3, EMPTY_OSPFV3, AREA_AUTHENTICATION),
        "expected": expected_result(
            AntaTestStatus.SUCCESS,
            (
                "The device is affected but mitigated because EOS version '4.34.6M' is affected and the OSPFv3 routing process is enabled and "
                "OSPFv3 IPsec authentication coverage is effective"
            ),
            expected_remediation("4.34.6M"),
        ),
    },
    (SA173, "mitigated-persistent-hotfix"): {
        "version": build_eos_version("4.35.4M"),
        "eos_data": eos_data(
            CURRENT_OSPFV3,
            EMPTY_OSPFV3,
            UNAUTHENTICATED_CONFIG,
            {SA173HotfixFact.extension_name: {"status": "installed", "boot": True}},
            [SA173HotfixFact.extension_name],
        ),
        "expected": expected_result(
            AntaTestStatus.SUCCESS,
            (
                "The device is affected but mitigated because EOS version '4.35.4M' is affected and the OSPFv3 routing process is enabled and "
                "SA173 SWIX hotfix is effective"
            ),
            expected_remediation("4.35.4M"),
        ),
    },
    (SA173, "failure-hotfix-outside-applicable-release"): {
        "version": build_eos_version("4.35.3M"),
        "eos_data": eos_data(
            CURRENT_OSPFV3,
            EMPTY_OSPFV3,
            UNAUTHENTICATED_CONFIG,
            {SA173HotfixFact.extension_name: {"status": "installed", "boot": True}},
            [SA173HotfixFact.extension_name],
        ),
        "expected": expected_result(
            AntaTestStatus.FAILURE,
            "The device is affected because EOS version '4.35.3M' is affected and the OSPFv3 routing process is enabled",
            expected_remediation("4.35.3M"),
        ),
    },
    (SA173, "success-no-ospfv3-configuration-short-circuits-other-inputs"): {
        "version": None,
        "eos_data": eos_data(EMPTY_OSPFV3, EMPTY_OSPFV3, "router ospfv3 vrf"),
        "expected": expected_result(AntaTestStatus.SUCCESS, "The device is not affected because the OSPFv3 routing process is disabled", None),
    },
    (SA173, "success-fixed-version-short-circuits-command-errors"): {
        "version": build_eos_version("4.35.5M"),
        "eos_data": eos_data(MALFORMED_OSPFV3, MALFORMED_OSPFV3, "router ospfv3 vrf"),
        "expected": expected_result(
            AntaTestStatus.SUCCESS,
            "The device is not affected because EOS version '4.35.5M' is outside the affected releases",
            None,
        ),
    },
    (SA173, "error-missing-version"): {
        "version": None,
        "eos_data": eos_data(CURRENT_OSPFV3, EMPTY_OSPFV3, UNAUTHENTICATED_CONFIG),
        "expected": expected_result(
            AntaTestStatus.ERROR,
            "The test could not determine the EOS version because it is missing from device metadata",
            None,
        ),
    },
    (SA173, "error-invalid-ospfv3-observation"): {
        "version": build_eos_version("4.35.4M"),
        "eos_data": eos_data(MALFORMED_OSPFV3, EMPTY_OSPFV3, UNAUTHENTICATED_CONFIG),
        "expected": expected_result(
            AntaTestStatus.ERROR,
            "The test could not determine the OSPFv3 configuration state because the 'show ospfv3 vrf all' output is invalid",
            None,
        ),
    },
    (SA173, "error-malformed-authentication-config"): {
        "version": build_eos_version("4.35.4M"),
        "eos_data": eos_data(CURRENT_OSPFV3, EMPTY_OSPFV3, "router ospfv3 vrf"),
        "expected": expected_result(
            AntaTestStatus.ERROR,
            "The test could not determine the OSPFv3 IPsec authentication coverage because the 'show running-config section ospfv3' output is invalid",
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


def ospfv3_fact(definition: type[Ospfv3ConfiguredFact | LegacyOspfv3ConfiguredFact], state: FeatureState) -> AvailableFact[FeatureValue]:
    """Build one current or legacy OSPFv3 configuration fact."""
    name = "routing process" if definition is Ospfv3ConfiguredFact else "legacy IPv6 routing process"
    return definition.available(FeatureValue(SubFeature(FeatureName.OSPFV3, name), state), SOURCE)


def authentication_fact(state: MitigationState) -> AvailableFact[MitigationValue]:
    """Build an OSPFv3 IPsec authentication fact."""
    return Ospfv3IpsecAuthenticationFact.available(MitigationValue(state), SOURCE)


def hotfix_fact(state: MitigationState) -> AvailableFact[MitigationValue]:
    """Build a persistent SA173 hotfix fact."""
    return SA173HotfixFact.available(MitigationValue(state), SOURCE)


class TestSA173VersionMatrix(unittest.TestCase):
    """Validate every source-published and user-confirmed version boundary."""

    def test_version_boundaries(self) -> None:
        for version, expected in (
            ("4.37.0F", AffectedStatus.NOT_AFFECTED),
            ("4.36.0F", AffectedStatus.AFFECTED),
            ("4.36.0.99F", AffectedStatus.AFFECTED),
            ("4.36.1F", AffectedStatus.NOT_AFFECTED),
            ("4.35.4M", AffectedStatus.AFFECTED),
            ("4.35.5M", AffectedStatus.NOT_AFFECTED),
            ("4.34.6M", AffectedStatus.AFFECTED),
            ("4.34.7M", AffectedStatus.NOT_AFFECTED),
            ("4.33.8M", AffectedStatus.AFFECTED),
            ("4.33.9M", AffectedStatus.NOT_AFFECTED),
            ("4.32.10M", AffectedStatus.AFFECTED),
            ("4.32.11M", AffectedStatus.NOT_AFFECTED),
            ("4.31.99M", AffectedStatus.AFFECTED),
            ("4.1.0F", AffectedStatus.AFFECTED),
        ):
            with self.subTest(version=version):
                parsed = parse_eos_version(version).unwrap()
                assert evaluate_version(parsed, AFFECTED_VERSION_MATRIX).affected_status is expected


class TestSA173Assessment(unittest.TestCase):
    """Validate the pure SA173 assessment branches."""

    def test_configured_ospfv3_without_authentication_is_affected(self) -> None:
        finding = _assess_sa173(
            version_fact("4.35.4M"),
            ospfv3_fact(Ospfv3ConfiguredFact, FeatureState.ENABLED),
            ospfv3_fact(LegacyOspfv3ConfiguredFact, FeatureState.DISABLED),
            authentication_fact(MitigationState.INEFFECTIVE),
            hotfix_fact(MitigationState.INEFFECTIVE),
        )

        assert isinstance(finding, AffectedResult)
        assert finding.context[0].relation is VersionRelation.AFFECTED

    def test_legacy_ospfv3_configuration_is_affected(self) -> None:
        finding = _assess_sa173(
            version_fact("4.31.99M"),
            ospfv3_fact(Ospfv3ConfiguredFact, FeatureState.UNSUPPORTED),
            ospfv3_fact(LegacyOspfv3ConfiguredFact, FeatureState.ENABLED),
            authentication_fact(MitigationState.INEFFECTIVE),
            hotfix_fact(MitigationState.INEFFECTIVE),
        )

        assert isinstance(finding, AffectedResult)
        assert isinstance(finding.conditions[0], AvailableFact)
        assert finding.conditions[0].definition is LegacyOspfv3ConfiguredFact

    def test_complete_authentication_coverage_is_mitigated(self) -> None:
        authentication = authentication_fact(MitigationState.EFFECTIVE)
        finding = _assess_sa173(
            version_fact("4.35.4M"),
            ospfv3_fact(Ospfv3ConfiguredFact, FeatureState.ENABLED),
            ospfv3_fact(LegacyOspfv3ConfiguredFact, FeatureState.DISABLED),
            authentication,
            hotfix_fact(MitigationState.INEFFECTIVE),
        )

        assert isinstance(finding, MitigatedResult)
        assert finding.mitigated_conditions[0].mitigations == (authentication,)
        assert finding.remediation == expected_remediation("4.35.4M")

    def test_persistent_hotfix_is_mitigated_without_ipsec_input(self) -> None:
        """A complete hotfix can close the path without the alternative IPsec fact."""
        hotfix = hotfix_fact(MitigationState.EFFECTIVE)
        finding = _assess_sa173(
            version_fact("4.35.4M"),
            ospfv3_fact(Ospfv3ConfiguredFact, FeatureState.ENABLED),
            ospfv3_fact(LegacyOspfv3ConfiguredFact, FeatureState.DISABLED),
            Ospfv3IpsecAuthenticationFact.unavailable(FactProblemKind.MISSING, SOURCE),
            hotfix,
        )

        assert isinstance(finding, MitigatedResult)
        assert finding.mitigated_conditions[0].mitigations == (hotfix,)

    def test_hotfix_is_limited_to_exact_releases(self) -> None:
        """Accept the persistent SWIX only on the four releases listed by the advisory."""
        hotfix = hotfix_fact(MitigationState.EFFECTIVE)
        for version in HOTFIX_RELEASES:
            with self.subTest(version=version, applicable=True):
                finding = _assess_sa173(
                    version_fact(version),
                    ospfv3_fact(Ospfv3ConfiguredFact, FeatureState.ENABLED),
                    ospfv3_fact(LegacyOspfv3ConfiguredFact, FeatureState.DISABLED),
                    Ospfv3IpsecAuthenticationFact.unavailable(FactProblemKind.MISSING, SOURCE),
                    hotfix,
                )
                assert isinstance(finding, MitigatedResult)
                assert finding.mitigated_conditions[0].mitigations == (hotfix,)

        for version in ("4.36.0F", "4.35.3M", "4.34.5M", "4.33.7M", "4.32.10M"):
            with self.subTest(version=version, applicable=False):
                finding = _assess_sa173(
                    version_fact(version),
                    ospfv3_fact(Ospfv3ConfiguredFact, FeatureState.ENABLED),
                    ospfv3_fact(LegacyOspfv3ConfiguredFact, FeatureState.DISABLED),
                    authentication_fact(MitigationState.INEFFECTIVE),
                    hotfix,
                )
                assert isinstance(finding, AffectedResult)

    def test_no_ospfv3_configuration_short_circuits_other_facts(self) -> None:
        for state in (FeatureState.DISABLED, FeatureState.UNSUPPORTED):
            with self.subTest(state=state):
                finding = _assess_sa173(
                    version_fact(None),
                    ospfv3_fact(Ospfv3ConfiguredFact, state),
                    ospfv3_fact(LegacyOspfv3ConfiguredFact, state),
                    Ospfv3IpsecAuthenticationFact.unavailable(FactProblemKind.MALFORMED, SOURCE),
                    SA173HotfixFact.unavailable(FactProblemKind.MALFORMED, SOURCE),
                )
                assert isinstance(finding, NotAffectedResult)

    def test_fixed_version_short_circuits_command_facts(self) -> None:
        finding = _assess_sa173(
            version_fact("4.35.5M"),
            Ospfv3ConfiguredFact.unavailable(FactProblemKind.MISSING, SOURCE),
            LegacyOspfv3ConfiguredFact.unavailable(FactProblemKind.MISSING, SOURCE),
            Ospfv3IpsecAuthenticationFact.unavailable(FactProblemKind.MALFORMED, SOURCE),
            SA173HotfixFact.unavailable(FactProblemKind.MALFORMED, SOURCE),
        )

        assert isinstance(finding, NotAffectedResult)

    def test_unavailable_required_facts_are_errors(self) -> None:
        cases = (
            (
                version_fact(None),
                ospfv3_fact(Ospfv3ConfiguredFact, FeatureState.ENABLED),
                ospfv3_fact(LegacyOspfv3ConfiguredFact, FeatureState.DISABLED),
                authentication_fact(MitigationState.INEFFECTIVE),
                hotfix_fact(MitigationState.INEFFECTIVE),
                EosVersionFact,
            ),
            (
                version_fact("4.35.4M"),
                Ospfv3ConfiguredFact.unavailable(FactProblemKind.MISSING, SOURCE),
                ospfv3_fact(LegacyOspfv3ConfiguredFact, FeatureState.DISABLED),
                authentication_fact(MitigationState.INEFFECTIVE),
                hotfix_fact(MitigationState.INEFFECTIVE),
                Ospfv3ConfiguredFact,
            ),
            (
                version_fact("4.35.4M"),
                ospfv3_fact(Ospfv3ConfiguredFact, FeatureState.ENABLED),
                ospfv3_fact(LegacyOspfv3ConfiguredFact, FeatureState.DISABLED),
                Ospfv3IpsecAuthenticationFact.unavailable(FactProblemKind.MALFORMED, SOURCE),
                hotfix_fact(MitigationState.INEFFECTIVE),
                Ospfv3IpsecAuthenticationFact,
            ),
            (
                version_fact("4.35.4M"),
                ospfv3_fact(Ospfv3ConfiguredFact, FeatureState.ENABLED),
                ospfv3_fact(LegacyOspfv3ConfiguredFact, FeatureState.DISABLED),
                authentication_fact(MitigationState.INEFFECTIVE),
                SA173HotfixFact.unavailable(FactProblemKind.MISSING, SOURCE),
                SA173HotfixFact,
            ),
        )
        for version, current, legacy, authentication, hotfix, expected_definition in cases:
            with self.subTest(expected_definition=expected_definition.key):
                finding = _assess_sa173(version, current, legacy, authentication, hotfix)
                assert isinstance(finding, ErrorResult)
                assert finding.problems[0].definition is expected_definition
