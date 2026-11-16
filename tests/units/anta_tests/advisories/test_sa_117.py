# Copyright (c) 2026 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
# ruff: noqa: D102, F811
# pylint: disable=duplicate-code, missing-function-docstring, redefined-outer-name
"""Unit tests for Arista Security Advisory 117."""

from __future__ import annotations

import unittest
from functools import partial
from typing import TYPE_CHECKING, Any, cast
from unittest.mock import AsyncMock

from anta._advisory.eos_versions import AffectedStatus, evaluate_version
from anta._advisory.facts.eos import EosVersionFact
from anta._advisory.facts.management import GnmiTransportFact
from anta._advisory.facts.models import (
    Fact,
    FactProblemKind,
    FactSource,
    FactSourceKind,
    FeatureState,
    UnavailableFact,
)
from anta._advisory.findings.models import ErrorResult, InconclusiveResult, NotAffectedResult, VulnerabilityResult
from anta._advisory.remediation import FixedRelease, software_version_plan
from anta._advisory.results import _get_atomic_vulnerability_ids
from anta._eos.version import EOSVersion, parse_eos_version
from anta.result_manager.models import AntaTestStatus
from anta.tests.advisories.sa_117 import (
    ADVISORY,
    AFFECTED_VERSION_MATRIX,
    SA117,
    _assess_sa117,
)
from tests.units.anta_tests import (
    build_eos_version,
    test,  # noqa: F401 - Pytest collects this imported test function.
)
from tests.units.anta_tests.advisories import OfflineAntaDevice, build_expected_advisory_result

EXPECTED_FIXED_RELEASES = (
    FixedRelease(EOSVersion(4, 30, 10, suffix="M")),
    FixedRelease(EOSVersion(4, 31, 7, suffix="M")),
    FixedRelease(EOSVersion(4, 32, 5, suffix="M")),
    FixedRelease(EOSVersion(4, 33, 2, suffix="F")),
)
EXPECTED_4_32_REMEDIATION = software_version_plan(
    EXPECTED_FIXED_RELEASES,
    current_version=EOSVersion(4, 32, 4, suffix="M"),
)
EXPECTED_4_33_REMEDIATION = software_version_plan(
    EXPECTED_FIXED_RELEASES,
    current_version=EOSVersion(4, 33, 0, suffix="F"),
)

if TYPE_CHECKING:
    from collections.abc import Mapping

    from anta.models import AntaCommand
    from tests.units.anta_tests import AntaUnitTestData


def _command(command: AntaCommand, output: dict[str, object] | str) -> AntaCommand:
    """Return one populated copy of a fact command."""
    populated = command.model_copy()
    populated.output = output
    return populated


def _evaluate_gnmi_transport_enabled(output: Mapping[str, object]) -> bool | None:
    fact = GnmiTransportFact.parse((_command(GnmiTransportFact.commands[0], dict(output)),))
    if isinstance(fact, UnavailableFact):
        return None
    return fact.value.state is FeatureState.ENABLED


expected_result = partial(build_expected_advisory_result, ADVISORY.vulnerabilities[0].id)
INCONCLUSIVE_4_32 = "The assessment is inconclusive and the device may be affected. Indications: EOS version '4.32.4M' is affected and the gNMI feature is enabled."


def sa117_eos_data(gnmi: dict[str, Any]) -> list[dict[str, Any] | str]:
    """Return production command data in required-fact declaration order."""
    return [gnmi]


_DATA: AntaUnitTestData = {
    (SA117, "inconclusive-accounting-enabled"): {
        "version": build_eos_version("4.32.4M"),
        "eos_data": sa117_eos_data({"transports": {"default": {"enabled": True, "accounting": True}}}),
        "expected": expected_result(AntaTestStatus.FAILURE, INCONCLUSIVE_4_32, EXPECTED_4_32_REMEDIATION),
    },
    (SA117, "inconclusive-flattened-gnmi-enabled"): {
        "version": build_eos_version("4.33.0F"),
        "eos_data": sa117_eos_data({"enabled": True, "accounting": True}),
        "expected": expected_result(
            AntaTestStatus.FAILURE,
            "The assessment is inconclusive and the device may be affected. Indications: EOS version '4.33.0F' is affected and the gNMI feature is enabled.",
            EXPECTED_4_33_REMEDIATION,
        ),
    },
    (SA117, "inconclusive-accounting-disabled"): {
        "version": build_eos_version("4.32.4M"),
        "eos_data": sa117_eos_data({"transports": {"default": {"enabled": True, "accounting": False}}}),
        "expected": expected_result(AntaTestStatus.FAILURE, INCONCLUSIVE_4_32, EXPECTED_4_32_REMEDIATION),
    },
    (SA117, "inconclusive-accounting-state-missing"): {
        "version": build_eos_version("4.32.4M"),
        "eos_data": sa117_eos_data({"transports": {"default": {"enabled": True}}}),
        "expected": expected_result(AntaTestStatus.FAILURE, INCONCLUSIVE_4_32, EXPECTED_4_32_REMEDIATION),
    },
    (SA117, "success-no-transport"): {
        "version": build_eos_version("4.32.4M"),
        "eos_data": sa117_eos_data({"transports": {}}),
        "expected": expected_result(
            AntaTestStatus.SUCCESS,
            "The device is not affected because the gNMI feature is disabled.",
            None,
        ),
    },
    (SA117, "success-disabled-transport-with-accounting"): {
        "version": build_eos_version("4.32.4M"),
        "eos_data": sa117_eos_data({"transports": {"default": {"enabled": False, "accounting": True}}}),
        "expected": expected_result(
            AntaTestStatus.SUCCESS,
            "The device is not affected because the gNMI feature is disabled.",
            None,
        ),
    },
    (SA117, "success-flattened-disabled-transport"): {
        "version": build_eos_version("4.33.0F"),
        "eos_data": sa117_eos_data({"enabled": False, "accounting": True}),
        "expected": expected_result(
            AntaTestStatus.SUCCESS,
            "The device is not affected because the gNMI feature is disabled.",
            None,
        ),
    },
    (SA117, "success-fixed-version"): {
        "version": build_eos_version("4.32.5M"),
        "eos_data": sa117_eos_data({}),
        "expected": expected_result(
            AntaTestStatus.SUCCESS,
            "The device is not affected because EOS version '4.32.5M' is outside the affected releases",
            None,
        ),
    },
    (SA117, "success-excluded-version-suffix"): {
        "version": build_eos_version("4.33.1FX-wbb"),
        "eos_data": sa117_eos_data({}),
        "expected": expected_result(
            AntaTestStatus.SUCCESS,
            "The device is not affected because EOS version '4.33.1FX-wbb' is outside the affected releases",
            None,
        ),
    },
    (SA117, "error-missing-device-version"): {
        "version": None,
        "eos_data": sa117_eos_data({}),
        "expected": expected_result(
            AntaTestStatus.ERROR,
            "The test could not determine the EOS version because it is missing from device metadata.",
            None,
        ),
    },
    (SA117, "error-malformed-transport-state"): {
        "version": build_eos_version("4.32.4M"),
        "eos_data": sa117_eos_data({}),
        "expected": expected_result(
            AntaTestStatus.ERROR,
            "The test could not determine the gNMI transport state because the 'show management api gnmi' output is invalid.",
            None,
        ),
    },
}


class TestSA117VersionMatrix(unittest.TestCase):
    """Validate every published affected and fixed-release boundary."""

    def test_version_boundaries(self) -> None:
        cases = (
            ("4.30.0F", AffectedStatus.NOT_AFFECTED),
            ("4.30.1F", AffectedStatus.AFFECTED),
            ("4.30.9M", AffectedStatus.AFFECTED),
            ("4.30.10M", AffectedStatus.NOT_AFFECTED),
            ("4.31.6M", AffectedStatus.AFFECTED),
            ("4.31.7M", AffectedStatus.NOT_AFFECTED),
            ("4.32.4M", AffectedStatus.AFFECTED),
            ("4.32.5M", AffectedStatus.NOT_AFFECTED),
            ("4.33.0F", AffectedStatus.AFFECTED),
            ("4.33.1F", AffectedStatus.AFFECTED),
            ("4.33.1FX-wbb", AffectedStatus.NOT_AFFECTED),
            ("4.33.2F", AffectedStatus.NOT_AFFECTED),
        )
        for version, expected in cases:
            with self.subTest(version=version):
                evaluation = evaluate_version(parse_eos_version(version).unwrap(), AFFECTED_VERSION_MATRIX)
                assert evaluation.affected_status is expected


class TestSA117Evidence(unittest.TestCase):
    """Validate transport evidence normalization."""

    def test_transport_enabled_truth_table(self) -> None:
        cases = (
            ({}, None),
            ({"enabled": False}, False),
            ({"enabled": True}, True),
            ({"enabled": "invalid"}, None),
            ({"transports": {}}, False),
            ({"transports": None}, None),
            ({"transports": {"default": {"enabled": False}}}, False),
            ({"transports": {"default": {"enabled": True}}}, True),
            ({"transports": {"default": {}}}, None),
            ({"transports": {"default": "invalid"}}, None),
            ({"transports": {"unknown": {}, "enabled": {"enabled": True}}}, True),
        )
        for output, expected in cases:
            with self.subTest(output=output):
                assert _evaluate_gnmi_transport_enabled(output) is expected


class TestSA117Assessment(unittest.TestCase):
    """Validate semantic classification and remediation for CVE-2025-0936."""

    def assess(
        self,
        *,
        version: object = "4.32.4M",
        gnmi: Mapping[str, object] | None = None,
    ) -> VulnerabilityResult:
        """Run the pure assessment helper with concise defaults."""
        output = {"transports": {"default": {"enabled": True, "accounting": False}}} if gnmi is None else gnmi
        source = FactSource("unit test", FactSourceKind.DEVICE_METADATA)
        if version is None:
            version_fact: Fact[EosVersionFact] = EosVersionFact.unavailable(FactProblemKind.MISSING, source)
        else:
            parsed_version = parse_eos_version(version if isinstance(version, str) else str(version)).unwrap_or_none()
            version_fact = (
                EosVersionFact.from_version(parsed_version).available(source)
                if parsed_version is not None
                else EosVersionFact.unavailable(FactProblemKind.INVALID, source)
            )
        gnmi_fact = GnmiTransportFact.parse((_command(GnmiTransportFact.commands[0], dict(output)),))
        return _assess_sa117(version_fact, gnmi_fact)

    def test_enabled_gnmi_is_inconclusive_without_control_evidence(self) -> None:
        for accounting in (True, False):
            with self.subTest(accounting=accounting):
                finding = self.assess(gnmi={"transports": {"default": {"enabled": True, "accounting": accounting}}})
                assert isinstance(finding, InconclusiveResult)
                assert tuple(item.subject for item in finding.unresolved) == ("gNOI File service state", "effective gNSI Authz control")
                assert finding.remediation == EXPECTED_4_32_REMEDIATION

    def test_not_affected_paths(self) -> None:
        findings = (self.assess(version="4.32.5M", gnmi={}), self.assess(gnmi={"transports": {}}))
        assert all(isinstance(finding, NotAffectedResult) for finding in findings)

    def test_unknown_required_evidence_is_error(self) -> None:
        cases = (
            {"version": None, "gnmi": {"transports": {}}},
            {"version": "4.32.4M", "gnmi": {}},
        )
        for case in cases:
            with self.subTest(case=case):
                assert isinstance(self.assess(**case), ErrorResult)

    def test_invalid_available_version_is_error(self) -> None:
        """Reject available device-version metadata that cannot be parsed as EOS."""

        class InvalidDeviceVersion:
            """Device-version metadata with a deliberately invalid EOS representation."""

            def __str__(self) -> str:
                return "not-an-eos-version"

            def to_dict(self) -> dict[str, str | int]:
                return {}

        finding = self.assess(version=InvalidDeviceVersion())

        assert isinstance(finding, ErrorResult)
        assert finding.problems[0].definition is EosVersionFact
        assert finding.problems[0].problem is FactProblemKind.INVALID


class TestSA117(unittest.IsolatedAsyncioTestCase):
    """Validate command orchestration and atomic-result projection."""

    async def run_test(self, gnmi_output: dict[str, Any], version: str = "4.32.4M") -> SA117:
        """Run SA117 with synthetic EOS output."""
        device = OfflineAntaDevice("unit-test")
        device.version = parse_eos_version(version).unwrap()
        await device.refresh()
        eos_data = sa117_eos_data(gnmi_output)
        test = cast("Any", SA117)(device=device, eos_data=eos_data)
        await test.test(eos_data=eos_data)
        return test

    async def test_error_atomic_result_preserves_vulnerability_association(self) -> None:
        test = await self.run_test({})

        assert len(test.result.atomic_results) == 1
        assert _get_atomic_vulnerability_ids(test.result.atomic_results[0]) == ("CVE-2025-0936",)

    async def test_fixed_version_ignores_unsupported_optional_commands(self) -> None:
        device = OfflineAntaDevice("unit-test")
        device.version = parse_eos_version("4.32.5M").unwrap()
        await device.refresh()
        eos_data = sa117_eos_data({})
        test = cast("Any", SA117)(device=device, eos_data=eos_data)
        for command in test.instance_commands:
            command.output = None
            command.errors = ["This command is not supported on this hardware platform"]
        test.collect = AsyncMock()

        await test.test()

        assert test.result.result is AntaTestStatus.SUCCESS
