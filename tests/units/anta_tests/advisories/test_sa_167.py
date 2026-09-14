# Copyright (c) 2026 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
# ruff: noqa: D102
# pylint: disable=duplicate-code, missing-function-docstring, redefined-outer-name
"""Unit tests for Arista Security Advisory 167."""

from __future__ import annotations

import unittest
from functools import partial
from typing import TYPE_CHECKING, Any, cast
from unittest.mock import AsyncMock

from anta._advisory.eos_versions import AffectedStatus, evaluate_version
from anta._advisory.facts.eos import EosVersionFact
from anta._advisory.facts.management import GnsiAuthzFact, GnsiTransportFact
from anta._advisory.facts.models import AvailableFact, Fact, FactProblemKind, FactSource, FactSourceKind, FeatureName, FeatureState, FeatureValue, SubFeature
from anta._advisory.findings.models import AffectedResult, ErrorResult, NotAffectedResult, VersionRelation
from anta._advisory.remediation import FixedRelease, software_version_plan
from anta._advisory.results import _get_atomic_vulnerability_ids
from anta._eos.version import EOSVersion, parse_eos_version
from anta.result_manager.models import AntaTestStatus
from anta.tests.advisories.sa_167 import ADVISORY, AFFECTED_VERSION_MATRIX, SA167, _assess_sa167
from tests.units.anta_tests import build_eos_version, test
from tests.units.anta_tests.advisories import OfflineAntaDevice, build_expected_advisory_result

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
expected_result = partial(build_expected_advisory_result, ADVISORY.vulnerabilities[0].id)


def gnsi_eos_data(output: dict[str, Any]) -> list[dict[str, Any] | str]:
    """Supply the shared gNSI output to each fact-owned command wrapper."""
    return [output, output]


DATA: AntaUnitTestData = {
    (SA167, "affected-authz-exposed"): {
        "version": build_eos_version("4.35.5M"),
        "eos_data": gnsi_eos_data({"transports": {"default": {"enabled": True}}, "authzEnabled": True}),
        "expected": expected_result(
            AntaTestStatus.FAILURE,
            "The device is affected because EOS version '4.35.5M' is affected, the gNSI transport is enabled, and the gNSI Authz service is enabled",
            EXPECTED_REMEDIATION,
        ),
    },
    (SA167, "success-no-enabled-transport"): {
        "version": build_eos_version("4.35.5M"),
        "eos_data": gnsi_eos_data({"transports": {"default": {"enabled": False}}}),
        "expected": expected_result(AntaTestStatus.SUCCESS, "The device is not affected because the gNSI transport is disabled", None),
    },
    (SA167, "success-authz-disabled"): {
        "version": build_eos_version("4.35.5M"),
        "eos_data": gnsi_eos_data({"transports": {"default": {"enabled": True}}, "authzEnabled": False}),
        "expected": expected_result(AntaTestStatus.SUCCESS, "The device is not affected because the gNSI Authz service is disabled", None),
    },
    (SA167, "success-fixed-version"): {
        "version": build_eos_version("4.35.6M"),
        "eos_data": gnsi_eos_data({}),
        "expected": expected_result(
            AntaTestStatus.SUCCESS,
            "The device is not affected because EOS version '4.35.6M' is outside the affected releases",
            None,
        ),
    },
    (SA167, "error-missing-version"): {
        "version": None,
        "eos_data": gnsi_eos_data({}),
        "expected": expected_result(
            AntaTestStatus.ERROR,
            "The test could not determine the EOS version because it is missing from device metadata",
            None,
        ),
    },
    (SA167, "error-missing-transport"): {
        "version": build_eos_version("4.35.5M"),
        "eos_data": gnsi_eos_data({"authzEnabled": True}),
        "expected": expected_result(
            AntaTestStatus.ERROR,
            "The test could not determine the gNSI transport state because the 'show management api gnsi' output is incomplete",
            None,
        ),
    },
    (SA167, "error-missing-authz"): {
        "version": build_eos_version("4.35.5M"),
        "eos_data": gnsi_eos_data({"transports": {"default": {"enabled": True}}}),
        "expected": expected_result(
            AntaTestStatus.ERROR,
            "The test could not determine the gNSI Authz service state because the 'show management api gnsi' output is incomplete",
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


def feature_fact(definition: type[GnsiTransportFact | GnsiAuthzFact], name: str, state: FeatureState) -> AvailableFact[FeatureValue]:
    """Build a normalized gNSI subfeature fact."""
    return definition.available(FeatureValue(SubFeature(FeatureName.GNSI, name), state), SOURCE)


class TestSA167VersionMatrix(unittest.TestCase):
    """Validate every source-published version boundary."""

    def test_version_boundaries(self) -> None:
        for version, expected in (
            ("4.36.0.1F", AffectedStatus.AFFECTED),
            ("4.36.0.99F", AffectedStatus.AFFECTED),
            ("4.36.1F", AffectedStatus.NOT_AFFECTED),
            ("4.35.5M", AffectedStatus.AFFECTED),
            ("4.35.6M", AffectedStatus.NOT_AFFECTED),
            ("4.34.7M", AffectedStatus.AFFECTED),
            ("4.34.8M", AffectedStatus.NOT_AFFECTED),
            ("4.33.8M", AffectedStatus.AFFECTED),
            ("4.33.9M", AffectedStatus.NOT_AFFECTED),
            ("4.32.99M", AffectedStatus.AFFECTED),
            ("4.31.0F", AffectedStatus.AFFECTED),
            ("4.30.99M", AffectedStatus.NOT_AFFECTED),
            ("4.37.0F", AffectedStatus.NOT_AFFECTED),
        ):
            with self.subTest(version=version):
                parsed = parse_eos_version(version).unwrap()
                assert evaluate_version(parsed, AFFECTED_VERSION_MATRIX).affected_status is expected


class TestSA167Assessment(unittest.TestCase):
    """Validate the pure SA167 assessment branches."""

    def test_enabled_authz_is_affected(self) -> None:
        finding = _assess_sa167(
            version_fact("4.35.5M"),
            feature_fact(GnsiTransportFact, "transport", FeatureState.ENABLED),
            feature_fact(GnsiAuthzFact, "Authz service", FeatureState.ENABLED),
        )

        assert isinstance(finding, AffectedResult)
        assert len(finding.conditions) == 2
        assert finding.remediation == EXPECTED_REMEDIATION

    def test_false_prerequisites_close_the_path(self) -> None:
        missing = GnsiAuthzFact.unavailable(FactProblemKind.MISSING, SOURCE)
        for transport_state, authz, expected in (
            (FeatureState.DISABLED, missing, GnsiTransportFact),
            (FeatureState.UNSUPPORTED, missing, GnsiTransportFact),
            (FeatureState.ENABLED, feature_fact(GnsiAuthzFact, "Authz service", FeatureState.DISABLED), GnsiAuthzFact),
            (FeatureState.ENABLED, feature_fact(GnsiAuthzFact, "Authz service", FeatureState.UNSUPPORTED), GnsiAuthzFact),
        ):
            with self.subTest(transport=transport_state, expected=expected.key):
                finding = _assess_sa167(
                    version_fact("4.35.5M"),
                    feature_fact(GnsiTransportFact, "transport", transport_state),
                    authz,
                )
                assert isinstance(finding, NotAffectedResult)
                assert cast("Any", finding.decisive[0]).definition is expected

    def test_fixed_version_short_circuits_configuration(self) -> None:
        finding = _assess_sa167(
            version_fact("4.35.6M"),
            GnsiTransportFact.unavailable(FactProblemKind.MISSING, SOURCE),
            GnsiAuthzFact.unavailable(FactProblemKind.MISSING, SOURCE),
        )

        assert isinstance(finding, NotAffectedResult)
        assert cast("Any", finding.decisive[0]).relation is VersionRelation.OUTSIDE_SCOPE

    def test_missing_required_facts_are_errors(self) -> None:
        enabled_transport = feature_fact(GnsiTransportFact, "transport", FeatureState.ENABLED)
        enabled_authz = feature_fact(GnsiAuthzFact, "Authz service", FeatureState.ENABLED)
        for version, transport, authz, expected in (
            (version_fact(None), enabled_transport, enabled_authz, EosVersionFact),
            (version_fact("4.35.5M"), GnsiTransportFact.unavailable(FactProblemKind.MALFORMED, SOURCE), enabled_authz, GnsiTransportFact),
            (version_fact("4.35.5M"), enabled_transport, GnsiAuthzFact.unavailable(FactProblemKind.MISSING, SOURCE), GnsiAuthzFact),
        ):
            with self.subTest(expected=expected.key):
                finding = _assess_sa167(version, transport, authz)
                assert isinstance(finding, ErrorResult)
                assert finding.problems[0].definition is expected


class TestSA167(unittest.IsolatedAsyncioTestCase):
    """Validate command derivation and optional-command projection."""

    def test_shared_command_wrappers_are_preserved(self) -> None:
        assert SA167.commands == [GnsiTransportFact.commands[0], GnsiAuthzFact.commands[0]]

    async def test_unsupported_gnsi_command_proves_not_affected(self) -> None:
        device = OfflineAntaDevice("unit-test")
        device.version = parse_eos_version("4.35.5M").unwrap()
        await device.refresh()
        test_instance = cast("Any", SA167)(device=device, eos_data=[{}, {}])
        for command in test_instance.instance_commands:
            command.output = None
            command.errors = ["This command is not supported on this hardware platform"]
        test_instance.collect = AsyncMock()

        await test_instance.test()

        assert test_instance.result.result is AntaTestStatus.SUCCESS
        assert _get_atomic_vulnerability_ids(test_instance.result.atomic_results[0]) == (ADVISORY.vulnerabilities[0].id,)
        assert "gNSI transport is not supported" in test_instance.result.messages[0]
