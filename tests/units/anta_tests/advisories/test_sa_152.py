# Copyright (c) 2026 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
# ruff: noqa: D102
# pylint: disable=duplicate-code, missing-function-docstring
"""Unit tests for Arista Security Advisory 152."""

from __future__ import annotations

import unittest
from functools import partial
from typing import TYPE_CHECKING

from anta._advisory.eos_versions import AffectedStatus, evaluate_version
from anta._advisory.facts.aaa import LoginAuthenticationFact
from anta._advisory.facts.eos import EosVersionFact
from anta._advisory.facts.management_access import PasswordManagementServiceFact
from anta._advisory.facts.models import Fact, FactProblemKind, FactSource, FactSourceKind, FeatureName, FeatureState, FeatureValue, SubFeature
from anta._advisory.findings.models import AffectedResult, ErrorResult, NotAffectedResult
from anta._advisory.remediation import FixedRelease, software_version_plan
from anta._eos.version import EOSVersion, parse_eos_version
from anta.result_manager.models import AntaTestStatus
from anta.tests.advisories.sa_152 import ADVISORY, AFFECTED_VERSION_MATRIX, SA152, _assess_sa152
from tests.units.anta_tests import build_eos_version, test
from tests.units.anta_tests.advisories import build_expected_advisory_result

if TYPE_CHECKING:
    from tests.units.anta_tests import AntaUnitTestData

SOURCE = FactSource("unit test", FactSourceKind.DEVICE_METADATA)
AAA_LOCAL = {"loginAuthenMethods": {"default": {"methods": ["local"]}}}
AAA_NONE = {"loginAuthenMethods": {"default": {"methods": ["none"]}}}


EXPECTED_REMEDIATION = software_version_plan(
    (
        FixedRelease(EOSVersion(4, 36, 1, suffix="F")),
        FixedRelease(EOSVersion(4, 35, 6, suffix="M")),
        FixedRelease(EOSVersion(4, 34, 8, suffix="M")),
        FixedRelease(EOSVersion(4, 33, 9, suffix="M")),
    ),
    current_version=EOSVersion(4, 35, 5, suffix="M"),
)
expected = partial(build_expected_advisory_result, ADVISORY.vulnerabilities[0].id)


DATA: AntaUnitTestData = {
    (SA152, "affected-default-password-ssh"): {
        "version": build_eos_version("4.35.5M"),
        "eos_data": [AAA_LOCAL, "", ""],
        "expected": expected(
            AntaTestStatus.FAILURE,
            "The device is affected because EOS version '4.35.5M' is affected, the AAA login authentication is enabled, "
            "and the AAA password-based management service is enabled",
            EXPECTED_REMEDIATION,
        ),
    },
    (SA152, "affected-telnet"): {
        "version": build_eos_version("4.35.5M"),
        "eos_data": [AAA_LOCAL, "management ssh\n   authentication protocol public-key", "management telnet\n   no shutdown"],
        "expected": expected(AntaTestStatus.FAILURE, "the AAA password-based management service is enabled", EXPECTED_REMEDIATION),
    },
    (SA152, "affected-password-ssh-in-configured-vrf-regardless-of-operational-state"): {
        "version": build_eos_version("4.35.5M"),
        "eos_data": [AAA_LOCAL, "management ssh\n   vrf MGMT", ""],
        "expected": expected(AntaTestStatus.FAILURE, "the AAA password-based management service is enabled", EXPECTED_REMEDIATION),
    },
    (SA152, "not-affected-login-none"): {
        "version": None,
        "eos_data": [AAA_NONE, "", ""],
        "expected": expected(AntaTestStatus.SUCCESS, "The device is not affected because the AAA login authentication is disabled", None),
    },
    (SA152, "not-affected-public-key-only"): {
        "version": None,
        "eos_data": [AAA_LOCAL, "management ssh\n   authentication protocol public-key", ""],
        "expected": expected(AntaTestStatus.SUCCESS, "The device is not affected because the AAA password-based management service is disabled", None),
    },
    (SA152, "not-affected-explicit-default-closes-other-vrfs"): {
        "version": None,
        "eos_data": [AAA_LOCAL, "management ssh\n   vrf default\n      shutdown", ""],
        "expected": expected(AntaTestStatus.SUCCESS, "The device is not affected because the AAA password-based management service is disabled", None),
    },
    (SA152, "not-affected-fixed-version"): {
        "version": build_eos_version("4.35.6M"),
        "eos_data": [{}, "bad", "bad"],
        "expected": expected(AntaTestStatus.SUCCESS, "The device is not affected because EOS version '4.35.6M' is outside the affected releases", None),
    },
    (SA152, "error-missing-login-methods"): {
        "version": build_eos_version("4.35.5M"),
        "eos_data": [{}, "", ""],
        "expected": expected(AntaTestStatus.ERROR, "The test could not determine the login authentication state", None),
    },
}


def version_fact(value: str) -> Fact[EOSVersion]:
    """Build an EOS version fact."""
    parsed = parse_eos_version(value).unwrap()
    return EosVersionFact.available(parsed, SOURCE)


def feature(definition, name: str, state: FeatureState):  # noqa: ANN001, ANN201
    """Build an AAA subfeature fact."""
    return definition.available(FeatureValue(SubFeature(FeatureName.AAA, name), state), SOURCE)


class TestSA152Assessment(unittest.TestCase):
    """Validate pure assessment branches."""

    def test_version_boundaries(self) -> None:
        """Validate every affected and adjacent release boundary."""
        for version, state in (
            ("4.36.0F", AffectedStatus.AFFECTED),
            ("4.36.0.99F", AffectedStatus.AFFECTED),
            ("4.36.1F", AffectedStatus.NOT_AFFECTED),
            ("4.35.5M", AffectedStatus.AFFECTED),
            ("4.35.6M", AffectedStatus.NOT_AFFECTED),
            ("4.34.7M", AffectedStatus.AFFECTED),
            ("4.34.7.1M", AffectedStatus.AFFECTED),
            ("4.34.7.99M", AffectedStatus.AFFECTED),
            ("4.34.8M", AffectedStatus.NOT_AFFECTED),
            ("4.33.8M", AffectedStatus.AFFECTED),
            ("4.33.9M", AffectedStatus.NOT_AFFECTED),
            ("4.32.99M", AffectedStatus.AFFECTED),
            ("4.1.0F", AffectedStatus.AFFECTED),
            ("4.37.0F", AffectedStatus.NOT_AFFECTED),
        ):
            parsed = parse_eos_version(version).unwrap()
            assert evaluate_version(parsed, AFFECTED_VERSION_MATRIX).affected_status is state

    def test_states(self) -> None:
        version = version_fact("4.35.5M")
        login = feature(LoginAuthenticationFact, "login authentication", FeatureState.ENABLED)
        service = feature(PasswordManagementServiceFact, "password-based management service", FeatureState.ENABLED)
        assert isinstance(_assess_sa152(version, login, service), AffectedResult)
        assert isinstance(_assess_sa152(version, feature(LoginAuthenticationFact, "login authentication", FeatureState.DISABLED), service), NotAffectedResult)
        unavailable = PasswordManagementServiceFact.unavailable(FactProblemKind.MISSING, SOURCE)
        assert isinstance(_assess_sa152(version, login, unavailable), ErrorResult)
