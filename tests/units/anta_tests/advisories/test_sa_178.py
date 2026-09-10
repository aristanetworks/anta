# Copyright (c) 2026 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
# ruff: noqa: D102
# pylint: disable=duplicate-code, missing-function-docstring, redefined-outer-name
"""Unit tests for Arista Security Advisory 178."""

from __future__ import annotations

import unittest
from functools import partial
from typing import TYPE_CHECKING

from anta._advisory.eos_versions import AffectedStatus, evaluate_version
from anta._advisory.facts.eos import EosVersionFact
from anta._advisory.facts.management import SnmpV3AuthenticationFact, SnmpV3CredentialSyntaxFact
from anta._advisory.facts.models import (
    AvailableFact,
    CredentialSyntaxState,
    CredentialSyntaxValue,
    Fact,
    FactProblemKind,
    FactSource,
    FactSourceKind,
    FeatureName,
    FeatureState,
    FeatureValue,
    SubFeature,
)
from anta._advisory.findings.models import AffectedResult, ErrorResult, NotAffectedResult, VersionRelation
from anta._advisory.remediation import FixedRelease, RemediationPlan, RunCommand, Sequence, software_version_action
from anta._eos.version import EOSVersion, parse_eos_version
from anta.result_manager.models import AntaTestStatus
from anta.tests.advisories.sa_178 import ADVISORY, AFFECTED_VERSION_MATRIX, SA178, _assess_sa178
from tests.units.anta_tests import build_eos_version, test
from tests.units.anta_tests.advisories import build_expected_advisory_result

if TYPE_CHECKING:
    from tests.units.anta_tests import AntaUnitTestData

SOURCE = FactSource("unit test", FactSourceKind.DEVICE_METADATA)
LEGACY_USER = "snmp-server user alice operators v3 localized 80000001 auth sha A1B2 priv aes C3D4"
ENCRYPTED_USER = "snmp-server user alice operators v3 localized 80000001 auth sha key 7 A1B2 priv aes key 7 C3D4"
MIXED_USER = "snmp-server user alice operators v3 localized 80000001 auth sha key 7 A1B2 priv aes C3D4"
SNMP_AUTH_ENABLED: dict[str, object] = {"usersByVersion": {"v3": {"users": {"alice": {"v3Params": {"authType": "SHA-256", "privType": "AES-128"}}}}}}
SNMP_AUTH_DISABLED: dict[str, object] = {"usersByVersion": {}}


EXPECTED_FIXED_RELEASES = (
    FixedRelease(EOSVersion(4, 36, 2, suffix="F")),
    FixedRelease(EOSVersion(4, 35, 6, suffix="M")),
    FixedRelease(EOSVersion(4, 34, 8, suffix="M")),
    FixedRelease(EOSVersion(4, 33, 10, suffix="M")),
)
EXPECTED_CONVERT_ACTION = RunCommand(("configure convert new-syntax",))
EXPECTED_AFFECTED_REMEDIATION = RemediationPlan(
    Sequence((software_version_action(EXPECTED_FIXED_RELEASES, current_version=EOSVersion(4, 36, 1, suffix="F")), EXPECTED_CONVERT_ACTION))
)
EXPECTED_CONVERT_REMEDIATION = RemediationPlan(EXPECTED_CONVERT_ACTION)
expected_result = partial(build_expected_advisory_result, ADVISORY.vulnerabilities[0].id)


DATA: AntaUnitTestData = {
    (SA178, "success-affected-version-with-encrypted-syntax"): {
        "version": build_eos_version("4.36.1F"),
        "eos_data": [SNMP_AUTH_ENABLED, ENCRYPTED_USER],
        "expected": expected_result(
            AntaTestStatus.SUCCESS,
            "The device is not affected because the SNMPv3 credential syntax is encrypted",
            None,
        ),
    },
    (SA178, "failure-affected-version-with-legacy-syntax"): {
        "version": build_eos_version("4.36.1F"),
        "eos_data": [SNMP_AUTH_ENABLED, LEGACY_USER],
        "expected": expected_result(
            AntaTestStatus.FAILURE,
            "The device is affected because EOS version '4.36.1F' is affected, the SNMPv3 authentication key is enabled, and the SNMPv3 credential syntax is legacy",
            EXPECTED_AFFECTED_REMEDIATION,
        ),
    },
    (SA178, "failure-affected-version-with-mixed-syntax"): {
        "version": build_eos_version("4.36.1F"),
        "eos_data": [SNMP_AUTH_ENABLED, MIXED_USER],
        "expected": expected_result(
            AntaTestStatus.FAILURE,
            "The device is affected because EOS version '4.36.1F' is affected, the SNMPv3 authentication key is enabled, and the SNMPv3 credential "
            "syntax is mixed legacy and encrypted",
            EXPECTED_AFFECTED_REMEDIATION,
        ),
    },
    (SA178, "failure-fixed-version-with-legacy-syntax"): {
        "version": build_eos_version("4.36.2F"),
        "eos_data": [SNMP_AUTH_ENABLED, LEGACY_USER],
        "expected": expected_result(
            AntaTestStatus.FAILURE,
            "The device is affected because EOS version '4.36.2F' is fixed, the SNMPv3 authentication key is enabled, and the SNMPv3 credential syntax is legacy",
            EXPECTED_CONVERT_REMEDIATION,
        ),
    },
    (SA178, "failure-fixed-version-with-mixed-syntax"): {
        "version": build_eos_version("4.35.6M"),
        "eos_data": [SNMP_AUTH_ENABLED, MIXED_USER],
        "expected": expected_result(
            AntaTestStatus.FAILURE,
            "The device is affected because EOS version '4.35.6M' is fixed, the SNMPv3 authentication key is enabled, and the SNMPv3 credential "
            "syntax is mixed legacy and encrypted",
            EXPECTED_CONVERT_REMEDIATION,
        ),
    },
    (SA178, "success-fixed-version-with-encrypted-syntax"): {
        "version": build_eos_version("4.36.2F"),
        "eos_data": [SNMP_AUTH_ENABLED, ENCRYPTED_USER],
        "expected": expected_result(
            AntaTestStatus.SUCCESS,
            "The device is not affected because the SNMPv3 credential syntax is encrypted",
            None,
        ),
    },
    (SA178, "success-no-snmpv3-credentials-short-circuits-other-inputs"): {
        "version": None,
        "eos_data": [SNMP_AUTH_DISABLED, ""],
        "expected": expected_result(
            AntaTestStatus.SUCCESS,
            "The device is not affected because the SNMPv3 authentication key is disabled",
            None,
        ),
    },
    (SA178, "error-missing-version"): {
        "version": None,
        "eos_data": [SNMP_AUTH_ENABLED, LEGACY_USER],
        "expected": expected_result(
            AntaTestStatus.ERROR,
            "The test could not determine the EOS version because it is missing from device metadata",
            None,
        ),
    },
    (SA178, "error-malformed-credential-syntax"): {
        "version": build_eos_version("4.36.2F"),
        "eos_data": [SNMP_AUTH_ENABLED, "snmp-server user alice operators v3 auth sha key 7"],
        "expected": expected_result(
            AntaTestStatus.ERROR,
            "The test could not determine the SNMPv3 credential syntax because the 'show running-config | include ^snmp-server user' output is invalid",
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


def syntax_fact(state: CredentialSyntaxState) -> AvailableFact[CredentialSyntaxValue]:
    """Build an SNMPv3 credential syntax fact."""
    return SnmpV3CredentialSyntaxFact.available(CredentialSyntaxValue(SubFeature(FeatureName.SNMPV3, "credential syntax"), state), SOURCE)


def authentication_fact(state: FeatureState) -> AvailableFact[FeatureValue]:
    """Build an SNMPv3 authentication-key fact."""
    return SnmpV3AuthenticationFact.available(FeatureValue(SubFeature(FeatureName.SNMPV3, "authentication key"), state), SOURCE)


class TestSA178VersionMatrix(unittest.TestCase):
    """Validate every source-published version boundary."""

    def test_version_boundaries(self) -> None:
        for version, expected in (
            ("4.37.0F", AffectedStatus.NOT_AFFECTED),
            ("4.36.1F", AffectedStatus.AFFECTED),
            ("4.36.1.99F", AffectedStatus.AFFECTED),
            ("4.36.2F", AffectedStatus.NOT_AFFECTED),
            ("4.35.5M", AffectedStatus.AFFECTED),
            ("4.35.5.99M", AffectedStatus.AFFECTED),
            ("4.35.6M", AffectedStatus.NOT_AFFECTED),
            ("4.34.7M", AffectedStatus.AFFECTED),
            ("4.34.7.1M", AffectedStatus.AFFECTED),
            ("4.34.7.99M", AffectedStatus.AFFECTED),
            ("4.34.8M", AffectedStatus.NOT_AFFECTED),
            ("4.33.9M", AffectedStatus.AFFECTED),
            ("4.33.10M", AffectedStatus.NOT_AFFECTED),
            ("4.32.99M", AffectedStatus.AFFECTED),
            ("4.1.0F", AffectedStatus.AFFECTED),
        ):
            with self.subTest(version=version):
                parsed = parse_eos_version(version).unwrap()
                assert evaluate_version(parsed, AFFECTED_VERSION_MATRIX).affected_status is expected


class TestSA178Assessment(unittest.TestCase):
    """Validate the pure SA178 assessment branches."""

    def test_affected_version_requires_legacy_syntax(self) -> None:
        authentication = authentication_fact(FeatureState.ENABLED)
        legacy = _assess_sa178(
            version_fact("4.36.1F"),
            authentication,
            syntax_fact(CredentialSyntaxState.LEGACY),
        )
        encrypted = _assess_sa178(version_fact("4.36.1F"), authentication, syntax_fact(CredentialSyntaxState.ENCRYPTED))

        assert isinstance(legacy, AffectedResult)
        assert legacy.context[0].relation is VersionRelation.AFFECTED
        assert legacy.remediation == EXPECTED_AFFECTED_REMEDIATION
        assert isinstance(encrypted, NotAffectedResult)

    def test_fixed_version_requires_encrypted_syntax(self) -> None:
        authentication = authentication_fact(FeatureState.ENABLED)
        encrypted_syntax = syntax_fact(CredentialSyntaxState.ENCRYPTED)
        legacy = _assess_sa178(version_fact("4.36.2F"), authentication, syntax_fact(CredentialSyntaxState.LEGACY))
        encrypted = _assess_sa178(version_fact("4.36.2F"), authentication, encrypted_syntax)

        assert isinstance(legacy, AffectedResult)
        assert legacy.context[0].relation is VersionRelation.FIXED
        assert isinstance(encrypted, NotAffectedResult)
        assert encrypted.decisive == (encrypted_syntax,)

    def test_false_prerequisite_short_circuits_unavailable_facts(self) -> None:
        no_credentials = _assess_sa178(
            version_fact(None),
            authentication_fact(FeatureState.DISABLED),
            syntax_fact(CredentialSyntaxState.NOT_CONFIGURED),
        )

        assert isinstance(no_credentials, NotAffectedResult)

    def test_unavailable_required_facts_are_errors(self) -> None:
        finding = _assess_sa178(
            version_fact(None),
            SnmpV3AuthenticationFact.unavailable(FactProblemKind.MALFORMED, SOURCE),
            SnmpV3CredentialSyntaxFact.unavailable(FactProblemKind.MALFORMED, SOURCE),
        )

        assert isinstance(finding, ErrorResult)
        assert len(finding.problems) == 3

    def test_affected_version_with_unavailable_syntax_is_error(self) -> None:
        finding = _assess_sa178(
            version_fact("4.36.1F"),
            authentication_fact(FeatureState.ENABLED),
            SnmpV3CredentialSyntaxFact.unavailable(FactProblemKind.MALFORMED, SOURCE),
        )

        assert isinstance(finding, ErrorResult)
        assert finding.problems == (SnmpV3CredentialSyntaxFact.unavailable(FactProblemKind.MALFORMED, SOURCE),)


class TestSA178(unittest.TestCase):
    """Validate required-command derivation."""

    def test_commands_are_derived_from_required_facts(self) -> None:
        assert SA178.commands == [SnmpV3AuthenticationFact.commands[0], SnmpV3CredentialSyntaxFact.commands[0]]
