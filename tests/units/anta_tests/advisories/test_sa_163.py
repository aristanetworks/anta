# Copyright (c) 2026 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
# ruff: noqa: D102
# pylint: disable=duplicate-code, missing-function-docstring
"""Unit tests for Arista Security Advisory 163."""

from __future__ import annotations

import unittest
from functools import partial
from typing import TYPE_CHECKING

from anta._advisory.eos_versions import AffectedStatus, evaluate_version
from anta._advisory.facts.aaa import LevelZeroCommandAuthorizationFact
from anta._advisory.facts.eos import EosVersionFact
from anta._advisory.facts.management import GnmiMtlsAuthorizationFact
from anta._advisory.facts.models import (
    Fact,
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
from anta._advisory.findings.models import AffectedResult, ErrorResult, MitigatedResult, NotAffectedResult
from anta._advisory.remediation import FixedRelease, software_version_plan
from anta._eos.version import EOSVersion, parse_eos_version
from anta.result_manager.models import AntaTestStatus
from anta.tests.advisories.sa_163 import ADVISORY, AFFECTED_VERSION_MATRIX, SA163, _assess_sa163
from tests.units.anta_tests import build_eos_version, test
from tests.units.anta_tests.advisories import build_expected_advisory_result

if TYPE_CHECKING:
    from tests.units.anta_tests import AntaUnitTestData

SOURCE = FactSource("unit test", FactSourceKind.DEVICE_METADATA)
EXPECTED_REMEDIATION = software_version_plan(
    (
        FixedRelease(EOSVersion(4, 36, 1, suffix="F")),
        FixedRelease(EOSVersion(4, 35, 6, suffix="M")),
        FixedRelease(EOSVersion(4, 34, 8, suffix="M")),
        FixedRelease(EOSVersion(4, 33, 9, suffix="M")),
    ),
    current_version=EOSVersion(4, 35, 5, suffix="M"),
)
TRUSTED_PROFILE = {
    "profileStatus": {
        "oc": {
            "profileState": "valid",
            "profileError": [],
            "certName": "server.crt",
            "keyName": "server.key",
            "trustedCertificates": ["shared_ca.crt"],
        },
        "plain": {
            "profileState": "valid",
            "profileError": [],
            "certName": "server.crt",
            "keyName": "server.key",
            "trustedCertificates": [],
        },
    }
}


expected = partial(build_expected_advisory_result, ADVISORY.vulnerabilities[0].id)


def transport(*, enabled: bool = True, authorization: bool = True, profile: str = "oc") -> dict[str, object]:
    """Return one structured gNMI transport."""
    return {"enabled": enabled, "authorization": authorization, "sslProfile": profile}


DATA: AntaUnitTestData = {
    (SA163, "affected-exposed-transport"): {
        "version": build_eos_version("4.35.5M"),
        "eos_data": [{"transports": {"default": transport()}}, TRUSTED_PROFILE, ""],
        "expected": expected(
            AntaTestStatus.FAILURE,
            "The device is affected because EOS version '4.35.5M' is affected and the gNMI mTLS request authorization is enabled",
            EXPECTED_REMEDIATION,
        ),
    },
    (SA163, "mitigated-level-zero-authorization"): {
        "version": build_eos_version("4.35.5M"),
        "eos_data": [{"transports": {"default": transport()}}, TRUSTED_PROFILE, "aaa authorization commands 0 default local group tacacs+"],
        "expected": expected(
            AntaTestStatus.SUCCESS,
            "The device is affected but mitigated because EOS version '4.35.5M' is affected and the gNMI mTLS request authorization is enabled "
            "and AAA privilege-level-zero command authorization is effective",
            EXPECTED_REMEDIATION,
        ),
    },
    (SA163, "not-affected-no-exposed-transport"): {
        "version": None,
        "eos_data": [{"transports": {"default": transport(authorization=False)}}, {}, ""],
        "expected": expected(AntaTestStatus.SUCCESS, "The device is not affected because the gNMI mTLS request authorization is disabled", None),
    },
    (SA163, "not-affected-cross-transport-state"): {
        "version": None,
        "eos_data": [
            {"transports": {"authorized": transport(profile="plain"), "trusted": transport(authorization=False)}},
            TRUSTED_PROFILE,
            "",
        ],
        "expected": expected(AntaTestStatus.SUCCESS, "The device is not affected because the gNMI mTLS request authorization is disabled", None),
    },
    (SA163, "not-affected-fixed-version"): {
        "version": build_eos_version("4.35.6M"),
        "eos_data": [{}, {}, ""],
        "expected": expected(AntaTestStatus.SUCCESS, "The device is not affected because EOS version '4.35.6M' is outside the affected releases", None),
    },
    (SA163, "error-missing-transport-state"): {
        "version": build_eos_version("4.35.5M"),
        "eos_data": [{}, {}, ""],
        "expected": expected(AntaTestStatus.ERROR, "The test could not determine the gNMI mTLS request authorization state", None),
    },
}


def version_fact(value: str) -> Fact[EOSVersion]:
    """Build an EOS version fact."""
    parsed = parse_eos_version(value).unwrap()
    return EosVersionFact.available(parsed, SOURCE)


def exposure(state: FeatureState):  # noqa: ANN201
    """Build a gNMI exposure fact."""
    return GnmiMtlsAuthorizationFact.available(FeatureValue(SubFeature(FeatureName.GNMI, "mTLS request authorization"), state), SOURCE)


def mitigation(state: MitigationState):  # noqa: ANN201
    """Build a level-zero authorization mitigation fact."""
    return LevelZeroCommandAuthorizationFact.available(MitigationValue(state), SOURCE)


class TestSA163Assessment(unittest.TestCase):
    """Validate pure assessment branches."""

    def test_version_boundaries(self) -> None:
        """Validate every affected and adjacent release boundary."""
        for version, state in (
            ("4.36.0F", AffectedStatus.AFFECTED),
            ("4.36.0.1F", AffectedStatus.AFFECTED),
            ("4.36.0.99F", AffectedStatus.AFFECTED),
            ("4.36.1F", AffectedStatus.NOT_AFFECTED),
            ("4.35.5M", AffectedStatus.AFFECTED),
            ("4.35.6M", AffectedStatus.NOT_AFFECTED),
            ("4.34.7M", AffectedStatus.AFFECTED),
            ("4.34.8M", AffectedStatus.NOT_AFFECTED),
            ("4.33.8M", AffectedStatus.AFFECTED),
            ("4.33.9M", AffectedStatus.NOT_AFFECTED),
            ("4.32.11M", AffectedStatus.AFFECTED),
            ("4.32.12M", AffectedStatus.NOT_AFFECTED),
            ("4.31.99M", AffectedStatus.AFFECTED),
            ("4.29.0F", AffectedStatus.AFFECTED),
            ("4.28.99M", AffectedStatus.NOT_AFFECTED),
        ):
            parsed = parse_eos_version(version).unwrap()
            assert evaluate_version(parsed, AFFECTED_VERSION_MATRIX).affected_status is state

    def test_states(self) -> None:
        version = version_fact("4.35.5M")
        enabled = exposure(FeatureState.ENABLED)
        assert isinstance(_assess_sa163(version, enabled, mitigation(MitigationState.INEFFECTIVE)), AffectedResult)
        assert isinstance(_assess_sa163(version, enabled, mitigation(MitigationState.EFFECTIVE)), MitigatedResult)
        assert isinstance(_assess_sa163(version, exposure(FeatureState.DISABLED), mitigation(MitigationState.INEFFECTIVE)), NotAffectedResult)
        unavailable = GnmiMtlsAuthorizationFact.unavailable(FactProblemKind.MISSING, SOURCE)
        assert isinstance(_assess_sa163(version, unavailable, mitigation(MitigationState.EFFECTIVE)), ErrorResult)
