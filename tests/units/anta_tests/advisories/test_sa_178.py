# Copyright (c) 2026 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
# ruff: noqa: D102
# pylint: disable=duplicate-code, missing-function-docstring, redefined-outer-name
"""Unit tests for Arista Security Advisory 178."""

from __future__ import annotations

import asyncio
import unittest
from functools import partial
from typing import TYPE_CHECKING, Any

from anta._advisory.eos_versions import AffectedStatus, evaluate_version
from anta._advisory.facts.eos import EosVersionFact
from anta._advisory.facts.management import SnmpV3AuthenticationFact, SnmpV3CredentialSyntaxFact
from anta._advisory.facts.models import (
    AvailableFact,
    CredentialSyntaxState,
    Fact,
    FactProblemKind,
    FactSource,
    FactSourceKind,
    FeatureState,
    MitigationState,
)
from anta._advisory.facts.software import SA178HotfixFact
from anta._advisory.findings.models import AffectedEosRelease, AffectedResult, ErrorResult, MitigatedCondition, MitigatedResult, NotAffectedResult, VersionRelation
from anta._advisory.remediation import FixedRelease, RemediationPlan, RunCommand, Sequence, software_version_action, software_version_plan
from anta._advisory.results import _AdvisoryAtomicTestResult
from anta._advisory.status import AdvisoryStatus
from anta._eos.version import EOSVersion, parse_eos_version
from anta.result_manager.models import AntaTestStatus
from anta.tests.advisories.sa_178 import ADVISORY, AFFECTED_VERSION_MATRIX, HOTFIX_RELEASES, SA178, _assess_sa178
from tests.units.anta_tests import build_eos_version, test
from tests.units.anta_tests.advisories import build_expected_advisory_result

if TYPE_CHECKING:
    from anta.device import AntaDevice
    from tests.units.anta_tests import AntaUnitTestData

SOURCE = FactSource("unit test", FactSourceKind.DEVICE_METADATA)
LEGACY_USER = "snmp-server user alice operators v3 localized 80000001 auth sha A1B2 priv aes C3D4"
ENCRYPTED_USER = "snmp-server user alice operators v3 localized 80000001 auth sha key 7 A1B2 priv aes key 7 C3D4"
MIXED_USER = "snmp-server user alice operators v3 localized 80000001 auth sha key 7 A1B2 priv aes C3D4"
REMOTE_LEGACY_USER = (
    "snmp-server user remote operators remote 192.0.2.1 v3 localized 800000000301020304 auth sha256 8cbb4157a6094abec416eb3a4731c7ef425f67fde50262ce5273e4dc873e7eaf"
)
REMOTE_UDP_PORT_LEGACY_USER = (
    "snmp-server user remoteport operators remote 192.0.2.2 udp-port 1162 v3 localized 800000000301020305 auth sha256 "
    "863e9b56ccbfd7d764cf718cb7cc5c5dff575871b59df84e98c21b0c049b1ed5"
)
NO_AUTHENTICATION_USERS = "snmp-server user bob noauthgrp v3\nsnmp-server user v2user noauthgrp v2c\nsnmp-server user remotenoauth noauthgrp remote 192.0.2.1 v3"
HOTFIX = "SecurityAdvisory178_CVE-2026-73440_Hotfix.swix"
PERSISTENT_HOTFIX: tuple[dict[str, Any], list[str]] = ({HOTFIX: {"status": "installed", "boot": True}}, [HOTFIX])
NON_PERSISTENT_HOTFIX: tuple[dict[str, Any], list[str]] = ({HOTFIX: {"status": "installed", "boot": False}}, [])

EXPECTED_FIXED_RELEASES = (
    FixedRelease(EOSVersion(4, 36, 3, suffix="M")),
    FixedRelease(EOSVersion(4, 35, 7, suffix="M")),
    FixedRelease(EOSVersion(4, 34, 9, suffix="M")),
    FixedRelease(EOSVersion(4, 33, 11, suffix="M")),
)
EXPECTED_CONVERT_ACTION = RunCommand(("configure convert new-syntax",))
EXPECTED_CONVERT_REMEDIATION = RemediationPlan(EXPECTED_CONVERT_ACTION)
expected_result = partial(build_expected_advisory_result, ADVISORY.vulnerabilities[0].id)


def expected_affected_remediation(version: str) -> RemediationPlan:
    """Build the expected upgrade-then-convert remediation independently from production constants."""
    current_version = parse_eos_version(version).unwrap()
    return RemediationPlan(Sequence((software_version_action(EXPECTED_FIXED_RELEASES, current_version=current_version), EXPECTED_CONVERT_ACTION)))


def eos_data(config: str, hotfix: tuple[dict[str, Any], list[str]] = ({}, [])) -> list[dict[str, Any] | str]:
    """Supply output to every fact-owned command wrapper, including the shared SNMP user configuration."""
    extensions, boot_extensions = hotfix
    return [config, config, {"extensions": extensions}, {"extensions": boot_extensions}]


_DATA: AntaUnitTestData = {
    (SA178, "success-affected-version-with-encrypted-syntax"): {
        "version": build_eos_version("4.36.1F"),
        "eos_data": eos_data(ENCRYPTED_USER),
        "expected": expected_result(
            AntaTestStatus.SUCCESS,
            "The device is not affected because the SNMPv3 credential syntax is encrypted",
            None,
        ),
    },
    (SA178, "failure-affected-version-with-legacy-syntax"): {
        "version": build_eos_version("4.36.1F"),
        "eos_data": eos_data(LEGACY_USER),
        "expected": expected_result(
            AntaTestStatus.FAILURE,
            "The device is affected because EOS version '4.36.1F' is affected, the SNMPv3 authentication key is enabled, and the SNMPv3 credential syntax is legacy",
            expected_affected_remediation("4.36.1F"),
        ),
    },
    (SA178, "failure-affected-version-with-mixed-syntax"): {
        "version": build_eos_version("4.36.1F"),
        "eos_data": eos_data(MIXED_USER),
        "expected": expected_result(
            AntaTestStatus.FAILURE,
            "The device is affected because EOS version '4.36.1F' is affected, the SNMPv3 authentication key is enabled, and the SNMPv3 credential "
            "syntax is mixed legacy and encrypted",
            expected_affected_remediation("4.36.1F"),
        ),
    },
    (SA178, "failure-affected-version-with-remote-user-legacy-syntax"): {
        "version": build_eos_version("4.36.0F"),
        "eos_data": eos_data(f"{NO_AUTHENTICATION_USERS}\n{REMOTE_LEGACY_USER}"),
        "expected": expected_result(
            AntaTestStatus.FAILURE,
            "The device is affected because EOS version '4.36.0F' is affected, the SNMPv3 authentication key is enabled, and the SNMPv3 credential syntax is legacy",
            expected_affected_remediation("4.36.0F"),
        ),
    },
    (SA178, "failure-affected-version-with-remote-udp-port-user-legacy-syntax"): {
        "version": build_eos_version("4.34.7M"),
        "eos_data": eos_data(REMOTE_UDP_PORT_LEGACY_USER),
        "expected": expected_result(
            AntaTestStatus.FAILURE,
            "The device is affected because EOS version '4.34.7M' is affected, the SNMPv3 authentication key is enabled, and the SNMPv3 credential syntax is legacy",
            expected_affected_remediation("4.34.7M"),
        ),
    },
    (SA178, "failure-hotfix-release-without-hotfix"): {
        "version": build_eos_version("4.36.2F"),
        "eos_data": eos_data(LEGACY_USER),
        "expected": expected_result(
            AntaTestStatus.FAILURE,
            "The device is affected because EOS version '4.36.2F' is affected, the SNMPv3 authentication key is enabled, and the SNMPv3 credential syntax is legacy",
            expected_affected_remediation("4.36.2F"),
        ),
    },
    (SA178, "failure-hotfix-release-with-non-persistent-hotfix"): {
        "version": build_eos_version("4.33.10M"),
        "eos_data": eos_data(LEGACY_USER, NON_PERSISTENT_HOTFIX),
        "expected": expected_result(
            AntaTestStatus.FAILURE,
            "The device is affected because EOS version '4.33.10M' is affected, the SNMPv3 authentication key is enabled, and the SNMPv3 credential "
            "syntax is legacy",
            expected_affected_remediation("4.33.10M"),
        ),
    },
    (SA178, "failure-hotfix-release-with-persistent-hotfix-and-legacy-syntax"): {
        "version": build_eos_version("4.35.6M"),
        "eos_data": eos_data(LEGACY_USER, PERSISTENT_HOTFIX),
        "expected": expected_result(
            AntaTestStatus.FAILURE,
            "The device is affected because the SNMPv3 authentication key is enabled and the SNMPv3 credential syntax is legacy. Mitigated conditions: EOS "
            "version '4.35.6M' is affected and SA178 SWIX hotfix is effective",
            EXPECTED_CONVERT_REMEDIATION,
        ),
    },
    (SA178, "success-hotfix-release-with-persistent-hotfix-and-encrypted-syntax"): {
        "version": build_eos_version("4.34.8M"),
        "eos_data": eos_data(ENCRYPTED_USER, PERSISTENT_HOTFIX),
        "expected": expected_result(
            AntaTestStatus.SUCCESS,
            "The device is affected but mitigated because the SNMPv3 credential syntax is encrypted and EOS version '4.34.8M' is affected and SA178 "
            "SWIX hotfix is effective",
            software_version_plan(EXPECTED_FIXED_RELEASES, current_version=EOSVersion(4, 34, 8, suffix="M")),
        ),
    },
    (SA178, "failure-fixed-version-with-legacy-syntax"): {
        "version": build_eos_version("4.36.3M"),
        "eos_data": eos_data(LEGACY_USER),
        "expected": expected_result(
            AntaTestStatus.FAILURE,
            "The device is affected because EOS version '4.36.3M' is fixed, the SNMPv3 authentication key is enabled, and the SNMPv3 credential syntax is legacy",
            EXPECTED_CONVERT_REMEDIATION,
        ),
    },
    (SA178, "failure-fixed-version-with-mixed-syntax"): {
        "version": build_eos_version("4.35.7M"),
        "eos_data": eos_data(MIXED_USER),
        "expected": expected_result(
            AntaTestStatus.FAILURE,
            "The device is affected because EOS version '4.35.7M' is fixed, the SNMPv3 authentication key is enabled, and the SNMPv3 credential "
            "syntax is mixed legacy and encrypted",
            EXPECTED_CONVERT_REMEDIATION,
        ),
    },
    (SA178, "success-fixed-version-with-encrypted-syntax"): {
        "version": build_eos_version("4.36.3M"),
        "eos_data": eos_data(ENCRYPTED_USER),
        "expected": expected_result(
            AntaTestStatus.SUCCESS,
            "The device is not affected because the SNMPv3 credential syntax is encrypted",
            None,
        ),
    },
    (SA178, "success-no-snmpv3-credentials-short-circuits-other-inputs"): {
        "version": None,
        "eos_data": ["", "", {}, {}],
        "expected": expected_result(
            AntaTestStatus.SUCCESS,
            "The device is not affected because the SNMPv3 authentication key is disabled",
            None,
        ),
    },
    (SA178, "success-local-and-remote-users-without-authentication"): {
        "version": build_eos_version("4.36.0F"),
        "eos_data": eos_data(NO_AUTHENTICATION_USERS),
        "expected": expected_result(
            AntaTestStatus.SUCCESS,
            "The device is not affected because the SNMPv3 authentication key is disabled",
            None,
        ),
    },
    (SA178, "error-missing-version"): {
        "version": None,
        "eos_data": eos_data(LEGACY_USER),
        "expected": expected_result(
            AntaTestStatus.ERROR,
            "The test could not determine the EOS version because it is missing from device metadata",
            None,
        ),
    },
    (SA178, "error-malformed-snmp-user-configuration"): {
        "version": build_eos_version("4.36.3M"),
        "eos_data": eos_data("snmp-server user alice operators v3 auth sha key 7"),
        "expected": expected_result(
            AntaTestStatus.ERROR,
            "The test could not determine the SNMPv3 authentication key state because the 'show running-config | include ^snmp-server user' output is "
            "invalid. The test could not determine the SNMPv3 credential syntax because the 'show running-config | include ^snmp-server user' output "
            "is invalid",
            None,
        ),
    },
    (SA178, "error-hotfix-release-with-unavailable-hotfix-state"): {
        "version": build_eos_version("4.36.2F"),
        "eos_data": [LEGACY_USER, LEGACY_USER, {}, {"extensions": []}],
        "expected": expected_result(
            AntaTestStatus.ERROR,
            "The test could not determine the SA178 SWIX hotfix because the 'show extensions' output is incomplete",
            None,
        ),
    },
    (SA178, "failure-non-hotfix-release-ignores-unavailable-hotfix-state"): {
        "version": build_eos_version("4.36.1F"),
        "eos_data": [LEGACY_USER, LEGACY_USER, {}, {"extensions": []}],
        "expected": expected_result(
            AntaTestStatus.FAILURE,
            "The device is affected because EOS version '4.36.1F' is affected, the SNMPv3 authentication key is enabled, and the SNMPv3 credential syntax is legacy",
            expected_affected_remediation("4.36.1F"),
        ),
    },
}


def version_fact(version: str | None) -> Fact[EosVersionFact]:
    """Build an EOS version fact for assessment tests."""
    if version is None:
        return EosVersionFact.unavailable(FactProblemKind.MISSING, SOURCE)
    parsed = parse_eos_version(version).unwrap()
    return EosVersionFact.from_version(parsed).available(SOURCE)


def syntax_fact(state: CredentialSyntaxState) -> AvailableFact[SnmpV3CredentialSyntaxFact]:
    """Build an SNMPv3 credential syntax fact."""
    return SnmpV3CredentialSyntaxFact(state).available(SOURCE)


def authentication_fact(state: FeatureState) -> AvailableFact[SnmpV3AuthenticationFact]:
    """Build an SNMPv3 authentication-key fact."""
    return SnmpV3AuthenticationFact(state).available(SOURCE)


def hotfix_fact(state: MitigationState) -> AvailableFact[SA178HotfixFact]:
    """Build an SA178 hotfix fact."""
    return SA178HotfixFact(state).available(SOURCE)


class TestSA178VersionMatrix(unittest.TestCase):
    """Validate every source-published version boundary."""

    def test_version_boundaries(self) -> None:
        for version, expected in (
            ("4.37.0F", AffectedStatus.NOT_AFFECTED),
            ("4.36.3M", AffectedStatus.NOT_AFFECTED),
            ("4.36.2.1F", AffectedStatus.AFFECTED),
            ("4.36.2F", AffectedStatus.AFFECTED),
            ("4.36.1F", AffectedStatus.AFFECTED),
            ("4.35.7M", AffectedStatus.NOT_AFFECTED),
            ("4.35.6.99M", AffectedStatus.AFFECTED),
            ("4.35.6M", AffectedStatus.AFFECTED),
            ("4.34.9M", AffectedStatus.NOT_AFFECTED),
            ("4.34.8.1M", AffectedStatus.AFFECTED),
            ("4.34.8M", AffectedStatus.AFFECTED),
            ("4.33.11M", AffectedStatus.NOT_AFFECTED),
            ("4.33.10M", AffectedStatus.AFFECTED),
            ("4.32.99M", AffectedStatus.AFFECTED),
            ("4.1.0F", AffectedStatus.AFFECTED),
        ):
            with self.subTest(version=version):
                parsed = parse_eos_version(version).unwrap()
                assert evaluate_version(parsed, AFFECTED_VERSION_MATRIX).affected_status is expected

    def test_hotfix_releases_match_the_advisory(self) -> None:
        assert {"4.36.2F", "4.35.6M", "4.34.8M", "4.33.10M"} == HOTFIX_RELEASES


class TestSA178Assessment(unittest.TestCase):
    """Validate the pure SA178 assessment branches."""

    def test_affected_version_requires_legacy_syntax(self) -> None:
        authentication = authentication_fact(FeatureState.ENABLED)
        no_hotfix = hotfix_fact(MitigationState.INEFFECTIVE)
        legacy = _assess_sa178(version_fact("4.36.1F"), authentication, syntax_fact(CredentialSyntaxState.LEGACY), no_hotfix)
        encrypted = _assess_sa178(version_fact("4.36.1F"), authentication, syntax_fact(CredentialSyntaxState.ENCRYPTED), no_hotfix)

        assert isinstance(legacy, AffectedResult)
        assert legacy.context[0].relation is VersionRelation.AFFECTED
        assert legacy.remediation == expected_affected_remediation("4.36.1F")
        assert isinstance(encrypted, NotAffectedResult)

    def test_fixed_version_requires_encrypted_syntax(self) -> None:
        authentication = authentication_fact(FeatureState.ENABLED)
        no_hotfix = hotfix_fact(MitigationState.INEFFECTIVE)
        encrypted_syntax = syntax_fact(CredentialSyntaxState.ENCRYPTED)
        legacy = _assess_sa178(version_fact("4.36.3M"), authentication, syntax_fact(CredentialSyntaxState.LEGACY), no_hotfix)
        encrypted = _assess_sa178(version_fact("4.36.3M"), authentication, encrypted_syntax, no_hotfix)

        assert isinstance(legacy, AffectedResult)
        assert legacy.context[0].relation is VersionRelation.FIXED
        assert legacy.remediation == EXPECTED_CONVERT_REMEDIATION
        assert isinstance(encrypted, NotAffectedResult)
        assert encrypted.decisive == (encrypted_syntax,)

    def test_persistent_hotfix_mitigates_the_affected_release_on_listed_releases(self) -> None:
        authentication = authentication_fact(FeatureState.ENABLED)
        legacy = syntax_fact(CredentialSyntaxState.LEGACY)
        for version in ("4.36.2F", "4.35.6M", "4.34.8M", "4.33.10M"):
            with self.subTest(version=version):
                observed_version = version_fact(version)
                assert isinstance(observed_version, AvailableFact)
                effective_hotfix = hotfix_fact(MitigationState.EFFECTIVE)
                hotfixed = _assess_sa178(observed_version, authentication, legacy, effective_hotfix)
                unpatched_hotfix = hotfix_fact(MitigationState.INEFFECTIVE)
                unpatched = _assess_sa178(observed_version, authentication, legacy, unpatched_hotfix)

                assert isinstance(hotfixed, AffectedResult)
                assert not hotfixed.context
                assert hotfixed.conditions == (authentication, legacy)
                assert hotfixed.mitigated_conditions == (MitigatedCondition(AffectedEosRelease(observed_version), (effective_hotfix,)),)
                assert hotfixed.remediation == EXPECTED_CONVERT_REMEDIATION
                assert isinstance(unpatched, AffectedResult)
                assert unpatched.context[0].relation is VersionRelation.AFFECTED
                assert unpatched.conditions == (authentication, legacy)
                assert unpatched.remediation == expected_affected_remediation(version)

    def test_encrypted_credentials_with_persistent_hotfix_are_mitigated(self) -> None:
        authentication = authentication_fact(FeatureState.ENABLED)
        encrypted = syntax_fact(CredentialSyntaxState.ENCRYPTED)
        effective_hotfix = hotfix_fact(MitigationState.EFFECTIVE)
        for version in ("4.36.2F", "4.35.6M", "4.34.8M", "4.33.10M"):
            with self.subTest(version=version):
                observed_version = version_fact(version)
                assert isinstance(observed_version, AvailableFact)
                finding = _assess_sa178(observed_version, authentication, encrypted, effective_hotfix)

                assert isinstance(finding, MitigatedResult)
                assert finding.context == (encrypted,)
                assert finding.mitigated_conditions == (MitigatedCondition(AffectedEosRelease(observed_version), (effective_hotfix,)),)
                assert finding.remediation == software_version_plan(EXPECTED_FIXED_RELEASES, current_version=observed_version.value)

    def test_encrypted_credentials_without_confirmed_applicable_hotfix_are_not_affected(self) -> None:
        encrypted = syntax_fact(CredentialSyntaxState.ENCRYPTED)
        effective_hotfix = hotfix_fact(MitigationState.EFFECTIVE)
        unavailable_hotfix = SA178HotfixFact.unavailable(FactProblemKind.COLLECTION_FAILED, SOURCE)
        for version, hotfix in (
            ("4.36.3M", effective_hotfix),
            ("4.36.1F", effective_hotfix),
            ("4.36.2.1F", effective_hotfix),
            ("4.36.2F", hotfix_fact(MitigationState.INEFFECTIVE)),
            ("4.36.2F", unavailable_hotfix),
            (None, effective_hotfix),
        ):
            with self.subTest(version=version, hotfix=hotfix):
                finding = _assess_sa178(version_fact(version), authentication_fact(FeatureState.ENABLED), encrypted, hotfix)

                assert isinstance(finding, NotAffectedResult)
                assert finding.decisive == (encrypted,)

    def test_encrypted_credentials_with_unavailable_authentication_remain_not_affected(self) -> None:
        encrypted = syntax_fact(CredentialSyntaxState.ENCRYPTED)
        finding = _assess_sa178(
            version_fact("4.35.6M"),
            SnmpV3AuthenticationFact.unavailable(FactProblemKind.MALFORMED, SOURCE),
            encrypted,
            hotfix_fact(MitigationState.EFFECTIVE),
        )

        assert isinstance(finding, NotAffectedResult)
        assert finding.decisive == (encrypted,)

    def test_hotfix_is_limited_to_exact_releases(self) -> None:
        authentication = authentication_fact(FeatureState.ENABLED)
        legacy = syntax_fact(CredentialSyntaxState.LEGACY)
        for version in ("4.36.2.1F", "4.36.1F", "4.35.5M", "4.32.11M"):
            with self.subTest(version=version):
                finding = _assess_sa178(version_fact(version), authentication, legacy, hotfix_fact(MitigationState.EFFECTIVE))

                assert isinstance(finding, AffectedResult)
                assert finding.context[0].relation is VersionRelation.AFFECTED
                assert finding.conditions == (authentication, legacy)
                assert finding.remediation == expected_affected_remediation(version)

    def test_false_prerequisite_short_circuits_unavailable_facts(self) -> None:
        unavailable_hotfix = SA178HotfixFact.unavailable(FactProblemKind.MISSING, SOURCE)
        no_credentials = _assess_sa178(
            version_fact(None),
            authentication_fact(FeatureState.DISABLED),
            syntax_fact(CredentialSyntaxState.NOT_CONFIGURED),
            unavailable_hotfix,
        )
        encrypted = _assess_sa178(
            version_fact("4.36.2F"),
            authentication_fact(FeatureState.ENABLED),
            syntax_fact(CredentialSyntaxState.ENCRYPTED),
            unavailable_hotfix,
        )

        assert isinstance(no_credentials, NotAffectedResult)
        assert isinstance(encrypted, NotAffectedResult)

    def test_unconfigured_credentials_short_circuit_other_unavailable_facts(self) -> None:
        unconfigured = syntax_fact(CredentialSyntaxState.NOT_CONFIGURED)
        finding = _assess_sa178(
            version_fact(None),
            SnmpV3AuthenticationFact.unavailable(FactProblemKind.MALFORMED, SOURCE),
            unconfigured,
            SA178HotfixFact.unavailable(FactProblemKind.MISSING, SOURCE),
        )

        assert isinstance(finding, NotAffectedResult)
        assert finding.decisive == (unconfigured,)

    def test_unavailable_required_facts_are_errors(self) -> None:
        finding = _assess_sa178(
            version_fact(None),
            SnmpV3AuthenticationFact.unavailable(FactProblemKind.MALFORMED, SOURCE),
            SnmpV3CredentialSyntaxFact.unavailable(FactProblemKind.MALFORMED, SOURCE),
            SA178HotfixFact.unavailable(FactProblemKind.MISSING, SOURCE),
        )

        assert isinstance(finding, ErrorResult)
        assert len(finding.problems) == 3

    def test_unavailable_hotfix_is_aggregated_on_listed_releases(self) -> None:
        unavailable_syntax = SnmpV3CredentialSyntaxFact.unavailable(FactProblemKind.MALFORMED, SOURCE)
        unavailable_hotfix = SA178HotfixFact.unavailable(FactProblemKind.MISSING, SOURCE)
        finding = _assess_sa178(version_fact("4.34.8M"), authentication_fact(FeatureState.ENABLED), unavailable_syntax, unavailable_hotfix)

        assert isinstance(finding, ErrorResult)
        assert finding.problems == (unavailable_syntax, unavailable_hotfix)

    def test_affected_version_with_unavailable_syntax_is_error(self) -> None:
        finding = _assess_sa178(
            version_fact("4.36.1F"),
            authentication_fact(FeatureState.ENABLED),
            SnmpV3CredentialSyntaxFact.unavailable(FactProblemKind.MALFORMED, SOURCE),
            hotfix_fact(MitigationState.INEFFECTIVE),
        )

        assert isinstance(finding, ErrorResult)
        assert finding.problems == (SnmpV3CredentialSyntaxFact.unavailable(FactProblemKind.MALFORMED, SOURCE),)


class TestSA178(unittest.TestCase):
    """Validate required-command derivation."""

    def test_commands_are_derived_from_required_facts(self) -> None:
        assert SA178.commands == [
            SnmpV3AuthenticationFact.commands[0],
            SnmpV3CredentialSyntaxFact.commands[0],
            *SA178HotfixFact.commands,
        ]


def test_hotfixed_encrypted_credentials_project_as_mitigated(device: AntaDevice) -> None:
    """Keep the semantic mitigated status, hotfix evidence, and fixed-release guidance in the executed test result."""
    device.version = build_eos_version("4.35.6M")
    advisory_test = SA178(device, eos_data=eos_data(ENCRYPTED_USER, PERSISTENT_HOTFIX))

    asyncio.run(advisory_test.test())

    assert advisory_test.result.result is AntaTestStatus.SUCCESS
    atomic_result = advisory_test.result.atomic_results[0]
    assert isinstance(atomic_result, _AdvisoryAtomicTestResult)
    assert atomic_result.advisory_status is AdvisoryStatus.MITIGATED
    assert atomic_result.messages == [
        (
            "The device is affected but mitigated because the SNMPv3 credential syntax is encrypted and EOS version '4.35.6M' is affected and SA178 "
            "SWIX hotfix is effective."
        )
    ]
    assert atomic_result.remediation == software_version_plan(EXPECTED_FIXED_RELEASES, current_version=EOSVersion(4, 35, 6, suffix="M"))
