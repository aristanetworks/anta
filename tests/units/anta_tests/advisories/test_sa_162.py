# Copyright (c) 2026 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
# ruff: noqa: D102
# pylint: disable=duplicate-code, missing-function-docstring, redefined-outer-name
"""Unit tests for Arista Security Advisory 162."""

from __future__ import annotations

import unittest
from functools import partial
from typing import TYPE_CHECKING, Any, cast
from unittest.mock import AsyncMock

from anta._advisory.eos_versions import AffectedStatus, evaluate_version
from anta._advisory.facts.eos import EosVersionFact
from anta._advisory.facts.management import GnsiCertzFact, GnsiTransportFact
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
from anta._advisory.findings.models import AffectedResult, EosReleaseAssessment, ErrorResult, InconclusiveResult, NotAffectedResult, VersionRelation
from anta._advisory.remediation import FixedRelease, software_version_plan
from anta._advisory.results import _get_atomic_vulnerability_ids
from anta._eos.version import EOSVersion, parse_eos_version
from anta.result_manager.models import AntaTestStatus
from anta.tests.advisories.sa_162 import ADVISORY, AFFECTED_VERSION_MATRIX, SA162, _assess_sa162
from tests.units.anta_tests import build_eos_version, test
from tests.units.anta_tests.advisories import OfflineAntaDevice, build_expected_advisory_result

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
expected_result = partial(build_expected_advisory_result, ADVISORY.vulnerabilities[0].id)


def gnsi_eos_data(output: dict[str, Any]) -> list[dict[str, Any] | str]:
    """Supply the shared gNSI output to each fact-owned command wrapper."""
    return [output, output]


DATA: AntaUnitTestData = {
    (SA162, "failure-certz-enabled"): {
        "version": build_eos_version("4.35.5M"),
        "eos_data": gnsi_eos_data({"transports": {"default": {"enabled": True}}, "certzEnabled": True}),
        "expected": expected_result(
            AntaTestStatus.FAILURE,
            "The device is affected because EOS version '4.35.5M' is affected, the gNSI transport is enabled, and the gNSI Certz service is enabled",
            EXPECTED_REMEDIATION,
        ),
    },
    (SA162, "inconclusive-historical-bootz-state"): {
        "version": build_eos_version("4.35.5M"),
        "eos_data": gnsi_eos_data({"transports": {"default": {"enabled": True}}, "certzEnabled": False}),
        "expected": expected_result(
            AntaTestStatus.FAILURE,
            "The assessment is inconclusive and the device may be affected. Indications: EOS version '4.35.5M' is affected. Unresolved: "
            "initial Bootz CertzProfile certificate contents is historical state",
            EXPECTED_REMEDIATION,
        ),
    },
    (SA162, "inconclusive-disabled-transport-leaves-bootz-history"): {
        "version": build_eos_version("4.35.5M"),
        "eos_data": gnsi_eos_data({"transports": {"default": {"enabled": False}}}),
        "expected": expected_result(
            AntaTestStatus.FAILURE,
            "Indications: EOS version '4.35.5M' is affected. Unresolved: initial Bootz CertzProfile certificate contents is historical state",
            EXPECTED_REMEDIATION,
        ),
    },
    (SA162, "success-fixed-version-ignores-unneeded-output"): {
        "version": build_eos_version("4.35.6M"),
        "eos_data": gnsi_eos_data({}),
        "expected": expected_result(
            AntaTestStatus.SUCCESS,
            "The device is not affected because EOS version '4.35.6M' is outside the affected releases",
            None,
        ),
    },
    (SA162, "error-missing-version"): {
        "version": None,
        "eos_data": gnsi_eos_data({}),
        "expected": expected_result(
            AntaTestStatus.ERROR,
            "The test could not determine the EOS version because it is missing from device metadata",
            None,
        ),
    },
    (SA162, "error-missing-transport-state"): {
        "version": build_eos_version("4.35.5M"),
        "eos_data": gnsi_eos_data({"certzEnabled": True}),
        "expected": expected_result(
            AntaTestStatus.ERROR,
            "The test could not determine the gNSI transport state because the 'show management api gnsi' output is incomplete",
            None,
        ),
    },
    (SA162, "error-malformed-transport-state"): {
        "version": build_eos_version("4.35.5M"),
        "eos_data": gnsi_eos_data({"transports": {"default": {"enabled": "yes"}}, "certzEnabled": True}),
        "expected": expected_result(
            AntaTestStatus.ERROR,
            "The test could not determine the gNSI transport state because the 'show management api gnsi' output is invalid",
            None,
        ),
    },
    (SA162, "error-missing-certz-state"): {
        "version": build_eos_version("4.35.5M"),
        "eos_data": gnsi_eos_data({"transports": {"default": {"enabled": True}}}),
        "expected": expected_result(
            AntaTestStatus.ERROR,
            "The test could not determine the gNSI Certz service state because the 'show management api gnsi' output is incomplete",
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


def feature_fact(definition: type[GnsiTransportFact | GnsiCertzFact], name: str, state: FeatureState) -> AvailableFact[FeatureValue]:
    """Build a normalized gNSI subfeature fact."""
    return definition.available(FeatureValue(SubFeature(FeatureName.GNSI, name), state), SOURCE)


class TestSA162VersionMatrix(unittest.TestCase):
    """Validate every source-published version boundary."""

    def test_version_boundaries(self) -> None:
        for version, expected in (
            ("4.36.0.1F", AffectedStatus.AFFECTED),
            ("4.36.0.99F", AffectedStatus.AFFECTED),
            ("4.36.1F", AffectedStatus.NOT_AFFECTED),
            ("4.35.5M", AffectedStatus.AFFECTED),
            ("4.35.6M", AffectedStatus.NOT_AFFECTED),
            ("4.34.7M", AffectedStatus.AFFECTED),
            ("4.34.7.1M", AffectedStatus.NOT_AFFECTED),
            ("4.34.7.99M", AffectedStatus.NOT_AFFECTED),
            ("4.33.8M", AffectedStatus.AFFECTED),
            ("4.33.9M", AffectedStatus.NOT_AFFECTED),
            ("4.32.99M", AffectedStatus.AFFECTED),
            ("4.31.0F", AffectedStatus.AFFECTED),
            ("4.30.1F", AffectedStatus.NOT_AFFECTED),
            ("4.30.2F", AffectedStatus.AFFECTED),
            ("4.29.99M", AffectedStatus.NOT_AFFECTED),
            ("4.37.0F", AffectedStatus.NOT_AFFECTED),
        ):
            with self.subTest(version=version):
                parsed = parse_eos_version(version).unwrap()
                assert evaluate_version(parsed, AFFECTED_VERSION_MATRIX).affected_status is expected


class TestSA162Assessment(unittest.TestCase):
    """Validate the pure SA162 assessment branches."""

    def test_certz_exposure_is_affected(self) -> None:
        finding = _assess_sa162(
            version_fact("4.35.5M"),
            feature_fact(GnsiTransportFact, "transport", FeatureState.ENABLED),
            feature_fact(GnsiCertzFact, "Certz service", FeatureState.ENABLED),
        )

        assert isinstance(finding, AffectedResult)
        assert len(finding.conditions) == 2
        assert finding.context[0].relation is VersionRelation.AFFECTED
        assert finding.remediation == EXPECTED_REMEDIATION

    def test_disabled_certz_leaves_bootz_history_inconclusive(self) -> None:
        finding = _assess_sa162(
            version_fact("4.35.5M"),
            feature_fact(GnsiTransportFact, "transport", FeatureState.ENABLED),
            feature_fact(GnsiCertzFact, "Certz service", FeatureState.DISABLED),
        )

        assert isinstance(finding, InconclusiveResult)
        assert finding.unresolved[0].kind.name == "HISTORICAL_STATE"
        assert finding.remediation == EXPECTED_REMEDIATION

    def test_no_transport_still_leaves_bootz_history_inconclusive(self) -> None:
        missing_certz = GnsiCertzFact.unavailable(FactProblemKind.MISSING, SOURCE)
        for state in (FeatureState.DISABLED, FeatureState.UNSUPPORTED):
            with self.subTest(state=state):
                transport = feature_fact(GnsiTransportFact, "transport", state)
                finding = _assess_sa162(version_fact("4.35.5M"), transport, missing_certz)
                assert isinstance(finding, InconclusiveResult)
                assert cast("EosReleaseAssessment", finding.indications[0]).relation is VersionRelation.AFFECTED

    def test_fixed_version_short_circuits_configuration(self) -> None:
        finding = _assess_sa162(
            version_fact("4.35.6M"),
            GnsiTransportFact.unavailable(FactProblemKind.MISSING, SOURCE),
            GnsiCertzFact.unavailable(FactProblemKind.MISSING, SOURCE),
        )

        assert isinstance(finding, NotAffectedResult)
        assert cast("Any", finding.decisive[0]).relation is VersionRelation.OUTSIDE_SCOPE

    def test_required_observable_input_errors(self) -> None:
        enabled_transport = feature_fact(GnsiTransportFact, "transport", FeatureState.ENABLED)
        for version, transport, certz, definition in (
            (version_fact(None), enabled_transport, feature_fact(GnsiCertzFact, "Certz service", FeatureState.ENABLED), EosVersionFact),
            (
                version_fact("4.35.5M"),
                GnsiTransportFact.unavailable(FactProblemKind.MALFORMED, SOURCE),
                feature_fact(GnsiCertzFact, "Certz service", FeatureState.ENABLED),
                GnsiTransportFact,
            ),
            (
                version_fact("4.35.5M"),
                enabled_transport,
                GnsiCertzFact.unavailable(FactProblemKind.MISSING, SOURCE),
                GnsiCertzFact,
            ),
        ):
            with self.subTest(definition=definition.key):
                finding = _assess_sa162(version, transport, certz)
                assert isinstance(finding, ErrorResult)
                assert finding.problems[0].definition is definition


class TestSA162(unittest.IsolatedAsyncioTestCase):
    """Validate command derivation and optional-command projection."""

    def test_shared_command_wrappers_are_preserved(self) -> None:
        assert SA162.commands == [GnsiTransportFact.commands[0], GnsiCertzFact.commands[0]]

    async def test_unsupported_gnsi_command_leaves_bootz_history_inconclusive(self) -> None:
        device = OfflineAntaDevice("unit-test")
        device.version = parse_eos_version("4.35.5M").unwrap()
        await device.refresh()
        test_instance = cast("Any", SA162)(device=device, eos_data=[{}, {}])
        for command in test_instance.instance_commands:
            command.output = None
            command.errors = ["This command is not supported on this hardware platform"]
        test_instance.collect = AsyncMock()

        await test_instance.test()

        assert test_instance.result.result is AntaTestStatus.FAILURE
        assert _get_atomic_vulnerability_ids(test_instance.result.atomic_results[0]) == (ADVISORY.vulnerabilities[0].id,)
        assert "initial Bootz CertzProfile certificate contents is historical state" in test_instance.result.messages[0]
