# Copyright (c) 2026 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
# ruff: noqa: D102
# pylint: disable=duplicate-code, missing-function-docstring
"""Unit tests for Arista Security Advisory 169."""

from __future__ import annotations

import unittest
from functools import partial
from typing import TYPE_CHECKING, Any

from anta._advisory.eos_versions import AffectedStatus, evaluate_version
from anta._advisory.facts.eos import EosVersionFact
from anta._advisory.facts.management import GnsiAuthzFact, GnsiMultipleTransportsFact, GnsiTransportFact
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
from anta._advisory.findings.models import AffectedResult, ErrorResult, InconclusiveResult, NotAffectedResult
from anta._advisory.remediation import FixedRelease, software_version_plan
from anta._eos.version import EOSVersion, parse_eos_version
from anta.result_manager.models import AntaTestStatus
from anta.tests.advisories.sa_169 import ADVISORY, AFFECTED_VERSION_MATRIX, SA169, _assess_sa169
from tests.units.anta_tests import build_eos_version, test
from tests.units.anta_tests.advisories import build_expected_advisory_result

if TYPE_CHECKING:
    from tests.units.anta_tests import AntaUnitTestData

SOURCE = FactSource("unit test", FactSourceKind.DEVICE_METADATA)
EXPECTED_REMEDIATION = software_version_plan(
    (
        FixedRelease(EOSVersion(4, 36, 1, suffix="F")),
        FixedRelease(EOSVersion(4, 35, 6, suffix="M")),
        FixedRelease(EOSVersion(4, 34, 7, suffix="M", hotfix=1)),
        FixedRelease(EOSVersion(4, 33, 9, suffix="M")),
    ),
    current_version=EOSVersion(4, 35, 5, suffix="M"),
)
expected = partial(build_expected_advisory_result, ADVISORY.vulnerabilities[0].id)


def gnsi(*, enabled_transports: int, authz: bool) -> dict[str, Any]:
    """Return the shared gNSI schema."""
    return {"transports": {f"transport-{index}": {"enabled": True} for index in range(enabled_transports)}, "authzEnabled": authz}


def gnsi_eos_data(output: dict[str, Any]) -> list[dict[str, Any] | str]:
    """Supply the shared gNSI output to each fact-owned command wrapper."""
    return [output, output, output]


_DATA: AntaUnitTestData = {
    (SA169, "inconclusive-prerequisites-active"): {
        "version": build_eos_version("4.35.5M"),
        "eos_data": gnsi_eos_data(gnsi(enabled_transports=1, authz=True)),
        "expected": expected(
            AntaTestStatus.FAILURE,
            "The assessment is inconclusive and the device may be affected. Indications: EOS version '4.35.5M' is affected, the gNSI transport "
            "is enabled, and the gNSI Authz service is enabled",
            EXPECTED_REMEDIATION,
        ),
    },
    (SA169, "affected-multiple-transports"): {
        "version": build_eos_version("4.35.5M"),
        "eos_data": gnsi_eos_data(gnsi(enabled_transports=2, authz=True)),
        "expected": expected(AntaTestStatus.FAILURE, "the gNSI multiple-transport mode is enabled", EXPECTED_REMEDIATION),
    },
    (SA169, "not-affected-authz-disabled"): {
        "version": None,
        "eos_data": gnsi_eos_data(gnsi(enabled_transports=1, authz=False)),
        "expected": expected(AntaTestStatus.SUCCESS, "The device is not affected because the gNSI Authz service is disabled", None),
    },
    (SA169, "not-affected-no-transport"): {
        "version": None,
        "eos_data": gnsi_eos_data(gnsi(enabled_transports=0, authz=True)),
        "expected": expected(AntaTestStatus.SUCCESS, "The device is not affected because the gNSI transport is disabled", None),
    },
    (SA169, "not-affected-fixed-version"): {
        "version": build_eos_version("4.35.6M"),
        "eos_data": gnsi_eos_data(gnsi(enabled_transports=1, authz=True)),
        "expected": expected(AntaTestStatus.SUCCESS, "The device is not affected because EOS version '4.35.6M' is outside the affected releases", None),
    },
    (SA169, "error-missing-authz"): {
        "version": build_eos_version("4.35.5M"),
        "eos_data": gnsi_eos_data({"transports": {"default": {"enabled": True}}}),
        "expected": expected(
            AntaTestStatus.ERROR,
            "The test could not determine the gNSI Authz service state because the 'show management api gnsi' output is incomplete",
            None,
        ),
    },
    (SA169, "error-malformed-transport-cardinality"): {
        "version": build_eos_version("4.35.5M"),
        "eos_data": gnsi_eos_data({"transports": {"default": {}}, "authzEnabled": True}),
        "expected": expected(AntaTestStatus.ERROR, "The test could not determine the gNSI transport state", None),
    },
}


def version_fact(value: str) -> CollectedFact[EOSVersion]:
    """Build a version fact."""
    parsed = parse_eos_version(value).unwrap()
    return EosVersionFact.available(parsed, SOURCE)


def feature_fact(definition: type[GnsiTransportFact | GnsiMultipleTransportsFact | GnsiAuthzFact], state: FeatureState) -> AvailableFact[FeatureValue]:
    """Build one gNSI feature fact."""
    name = "transport" if definition is GnsiTransportFact else "multiple-transport mode" if definition is GnsiMultipleTransportsFact else "Authz service"
    return definition.available(FeatureValue(SubFeature(FeatureName.GNSI, name), state), SOURCE)


class TestSA169Assessment(unittest.TestCase):
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
            ("4.34.6M", AffectedStatus.AFFECTED),
            ("4.34.7M", AffectedStatus.AFFECTED),
            ("4.34.7.1M", AffectedStatus.NOT_AFFECTED),
            ("4.34.7.99M", AffectedStatus.NOT_AFFECTED),
            ("4.33.8M", AffectedStatus.AFFECTED),
            ("4.33.9M", AffectedStatus.NOT_AFFECTED),
            ("4.32.11M", AffectedStatus.AFFECTED),
            ("4.32.12M", AffectedStatus.NOT_AFFECTED),
            ("4.31.10M", AffectedStatus.AFFECTED),
            ("4.31.11M", AffectedStatus.NOT_AFFECTED),
            ("4.30.99M", AffectedStatus.NOT_AFFECTED),
        ):
            parsed = parse_eos_version(version).unwrap()
            assert evaluate_version(parsed, AFFECTED_VERSION_MATRIX).affected_status is state

    def test_states(self) -> None:
        version = version_fact("4.35.5M")
        transport = feature_fact(GnsiTransportFact, FeatureState.ENABLED)
        one_transport = feature_fact(GnsiMultipleTransportsFact, FeatureState.DISABLED)
        multiple_transports = feature_fact(GnsiMultipleTransportsFact, FeatureState.ENABLED)
        authz = feature_fact(GnsiAuthzFact, FeatureState.ENABLED)
        assert isinstance(_assess_sa169(version, transport, one_transport, authz), InconclusiveResult)
        assert isinstance(_assess_sa169(version, transport, multiple_transports, authz), AffectedResult)
        assert isinstance(
            _assess_sa169(version, feature_fact(GnsiTransportFact, FeatureState.DISABLED), one_transport, authz),
            NotAffectedResult,
        )
        unavailable = GnsiAuthzFact.unavailable(FactProblemKind.MISSING, SOURCE)
        assert isinstance(_assess_sa169(version, transport, one_transport, unavailable), ErrorResult)
