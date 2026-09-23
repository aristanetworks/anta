# Copyright (c) 2026 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
# ruff: noqa: D102
# pylint: disable=duplicate-code, missing-function-docstring
"""Unit tests for Arista Security Advisory 174."""

from __future__ import annotations

import unittest
from functools import partial
from typing import TYPE_CHECKING, Any

from anta._advisory.eos_versions import AffectedStatus, evaluate_version
from anta._advisory.facts.eos import EosVersionFact
from anta._advisory.facts.management import GnsiAcctzFact, GnsiAuthzFact
from anta._advisory.facts.models import (
    Fact,
    FactProblemKind,
    FactSource,
    FactSourceKind,
    FeatureState,
)
from anta._advisory.facts.p4_runtime import P4RuntimeAccountingFact, P4RuntimeFact, P4RuntimeMtlsFact
from anta._advisory.findings.models import AffectedResult, ErrorResult, InconclusiveResult, NotAffectedResult
from anta._advisory.remediation import FixedRelease, software_version_plan
from anta._eos.version import EOSVersion, parse_eos_version
from anta.result_manager.models import AntaTestStatus
from anta.tests.advisories.sa_174 import ADVISORY, AFFECTED_VERSION_MATRIX, SA174, _assess_sa174
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
    ),
    current_version=EOSVersion(4, 35, 5, suffix="M"),
)
TRUSTED_PROFILE: dict[str, Any] = {"profileStatus": {"campus": {"trustedCertificates": ["root-ca.crt"]}}}


expected = partial(build_expected_advisory_result, ADVISORY.vulnerabilities[0].id)


def p4(*, enabled: bool = True, profile: str = "campus", accounting: bool = False) -> dict[str, Any]:
    """Return structured P4Runtime output."""
    return {"enabled": enabled, "transport": {"sslProfile": profile, "accountingRequests": accounting}}


def eos_data(p4_output: dict[str, Any], ssl_output: dict[str, Any], gnsi_output: dict[str, Any]) -> list[dict[str, Any] | str]:
    """Supply shared command output to each fact-owned command wrapper."""
    return [p4_output, p4_output, ssl_output, p4_output, gnsi_output, gnsi_output]


_DATA: AntaUnitTestData = {
    (SA174, "affected-without-mtls"): {
        "version": build_eos_version("4.35.5M"),
        "eos_data": eos_data(p4(profile=""), {}, {}),
        "expected": expected(
            AntaTestStatus.FAILURE,
            "The device is affected because EOS version '4.35.5M' is affected, the P4Runtime feature is enabled, and the P4Runtime mTLS is disabled",
            EXPECTED_REMEDIATION,
        ),
    },
    (SA174, "affected-p4-accounting-without-authz"): {
        "version": build_eos_version("4.35.5M"),
        "eos_data": eos_data(p4(accounting=True), TRUSTED_PROFILE, {"acctzEnabled": False, "authzEnabled": False}),
        "expected": expected(
            AntaTestStatus.FAILURE,
            "the P4Runtime accounting is enabled, and the gNSI Authz service is disabled",
            EXPECTED_REMEDIATION,
        ),
    },
    (SA174, "affected-acctz-without-authz"): {
        "version": build_eos_version("4.35.5M"),
        "eos_data": eos_data(p4(), TRUSTED_PROFILE, {"acctzEnabled": True, "authzEnabled": False}),
        "expected": expected(AntaTestStatus.FAILURE, "the gNSI Acctz service is enabled, and the gNSI Authz service is disabled", EXPECTED_REMEDIATION),
    },
    (SA174, "inconclusive-authz-policy-scope"): {
        "version": build_eos_version("4.35.5M"),
        "eos_data": eos_data(p4(accounting=True), TRUSTED_PROFILE, {"acctzEnabled": False, "authzEnabled": True}),
        "expected": expected(
            AntaTestStatus.FAILURE,
            "Unresolved: whether the installed gNSI Authz policy permits only the documented SPIFFE identity is device state not exposed",
            EXPECTED_REMEDIATION,
        ),
    },
    (SA174, "not-affected-disabled"): {
        "version": None,
        "eos_data": eos_data({"enabled": False}, {}, {}),
        "expected": expected(AntaTestStatus.SUCCESS, "The device is not affected because the P4Runtime feature is disabled", None),
    },
    (SA174, "not-affected-no-accounting"): {
        "version": build_eos_version("4.35.5M"),
        "eos_data": eos_data(p4(), TRUSTED_PROFILE, {"acctzEnabled": False, "authzEnabled": False}),
        "expected": expected(AntaTestStatus.SUCCESS, "the P4Runtime accounting is disabled and the gNSI Acctz service is disabled", None),
    },
    (SA174, "not-affected-unsupported-acctz"): {
        "version": build_eos_version("4.31.10M"),
        "eos_data": eos_data(p4(), TRUSTED_PROFILE, {}),
        "expected": expected(AntaTestStatus.SUCCESS, "the P4Runtime accounting is disabled and the gNSI Acctz service is not supported", None),
    },
    (SA174, "not-affected-fixed-version"): {
        "version": build_eos_version("4.35.6M"),
        "eos_data": eos_data({}, {}, {}),
        "expected": expected(AntaTestStatus.SUCCESS, "The device is not affected because EOS version '4.35.6M' is outside the affected releases", None),
    },
    (SA174, "error-missing-p4-state"): {
        "version": build_eos_version("4.35.5M"),
        "eos_data": eos_data({}, {}, {}),
        "expected": expected(AntaTestStatus.ERROR, "The test could not determine the P4Runtime state because the 'show p4-runtime' output is incomplete", None),
    },
    (SA174, "error-missing-accounting-state"): {
        "version": build_eos_version("4.35.5M"),
        "eos_data": eos_data(
            {"enabled": True, "transport": {"sslProfile": "campus"}},
            TRUSTED_PROFILE,
            {"acctzEnabled": False, "authzEnabled": True},
        ),
        "expected": expected(AntaTestStatus.ERROR, "The test could not determine the P4Runtime accounting state", None),
    },
}


def version_fact(value: str) -> Fact[EosVersionFact]:
    """Build an EOS version fact."""
    parsed = parse_eos_version(value).unwrap()
    return EosVersionFact.from_version(parsed).available(SOURCE)


def authz_fact(state: FeatureState) -> Fact[GnsiAuthzFact]:
    """Build a gNSI Authz feature fact."""
    return GnsiAuthzFact(state).available(SOURCE)


class TestSA174Assessment(unittest.TestCase):
    """Validate pure assessment branches."""

    def test_version_boundaries(self) -> None:
        """Validate every affected and adjacent release boundary."""
        for version, state in (
            ("4.36.1F", AffectedStatus.AFFECTED),
            ("4.36.2F", AffectedStatus.NOT_AFFECTED),
            ("4.35.5M", AffectedStatus.AFFECTED),
            ("4.35.6M", AffectedStatus.NOT_AFFECTED),
            ("4.34.7M", AffectedStatus.AFFECTED),
            ("4.34.8M", AffectedStatus.NOT_AFFECTED),
            ("4.33.99M", AffectedStatus.AFFECTED),
            ("4.30.0F", AffectedStatus.AFFECTED),
            ("4.29.1F", AffectedStatus.NOT_AFFECTED),
            ("4.29.2F", AffectedStatus.AFFECTED),
            ("4.29.99M", AffectedStatus.AFFECTED),
            ("4.28.99M", AffectedStatus.NOT_AFFECTED),
        ):
            parsed = parse_eos_version(version).unwrap()
            assert evaluate_version(parsed, AFFECTED_VERSION_MATRIX).affected_status is state

    def test_states(self) -> None:
        version = version_fact("4.35.5M")
        enabled = P4RuntimeFact(FeatureState.ENABLED).available(SOURCE)
        mtls = P4RuntimeMtlsFact(FeatureState.ENABLED).available(SOURCE)
        accounting = P4RuntimeAccountingFact(FeatureState.ENABLED).available(SOURCE)
        acctz = GnsiAcctzFact(FeatureState.DISABLED).available(SOURCE)
        assert isinstance(_assess_sa174(version, enabled, mtls, accounting, acctz, authz_fact(FeatureState.DISABLED)), AffectedResult)
        assert isinstance(_assess_sa174(version, enabled, mtls, accounting, acctz, authz_fact(FeatureState.ENABLED)), InconclusiveResult)
        disabled = P4RuntimeFact(FeatureState.DISABLED).available(SOURCE)
        unavailable = P4RuntimeMtlsFact.unavailable(FactProblemKind.MISSING, SOURCE)
        assert isinstance(_assess_sa174(version, disabled, unavailable, accounting, acctz, authz_fact(FeatureState.ENABLED)), NotAffectedResult)
        assert isinstance(_assess_sa174(version, enabled, unavailable, accounting, acctz, authz_fact(FeatureState.ENABLED)), ErrorResult)

    def test_every_accounting_path_with_authz_is_inconclusive(self) -> None:
        """Keep every accounting path inconclusive until the Authz policy is verified."""
        version = version_fact("4.35.5M")
        enabled = P4RuntimeFact(FeatureState.ENABLED).available(SOURCE)
        mtls = P4RuntimeMtlsFact(FeatureState.ENABLED).available(SOURCE)
        p4_enabled = P4RuntimeAccountingFact(FeatureState.ENABLED).available(SOURCE)
        p4_disabled = P4RuntimeAccountingFact(FeatureState.DISABLED).available(SOURCE)
        acctz_enabled = GnsiAcctzFact(FeatureState.ENABLED).available(SOURCE)
        acctz_disabled = GnsiAcctzFact(FeatureState.DISABLED).available(SOURCE)
        enabled_authz = authz_fact(FeatureState.ENABLED)

        assert isinstance(_assess_sa174(version, enabled, mtls, p4_enabled, acctz_disabled, enabled_authz), InconclusiveResult)
        assert isinstance(_assess_sa174(version, enabled, mtls, p4_disabled, acctz_enabled, enabled_authz), InconclusiveResult)
        both = _assess_sa174(version, enabled, mtls, p4_enabled, acctz_enabled, enabled_authz)
        assert isinstance(both, InconclusiveResult)
        assert len(both.indications) == 6
