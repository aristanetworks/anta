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
from anta._advisory.facts.management import GnmiAccountingFact, GnmiTransportFact, RiskyOpenConfigTraceFact
from anta._advisory.facts.models import (
    AvailableFact,
    ConfigurationState,
    ConfigurationValue,
    Fact,
    FactProblemKind,
    FactSource,
    FactSourceKind,
    FeatureName,
    FeatureState,
    FeatureValue,
    SubFeature,
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
    VerifySA117,
    _assess_sa117,
)
from tests.units.anta_tests import build_eos_version, test
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


def _feature_bool(fact: Fact[FeatureValue]) -> bool | None:
    """Project a feature fact to the legacy truth table used by parser cases."""
    if isinstance(fact, UnavailableFact):
        return None
    return fact.value.state is FeatureState.ENABLED


def _evaluate_gnmi_transport_enabled(output: Mapping[str, object]) -> bool | None:
    return _feature_bool(GnmiTransportFact.parse((_command(GnmiTransportFact.commands[0], dict(output)),)))


def _evaluate_gnmi_accounting_enabled(output: Mapping[str, object]) -> bool | None:
    return _feature_bool(GnmiAccountingFact.parse((_command(GnmiAccountingFact.commands[0], dict(output)),)))


def _evaluate_risky_trace_configuration(output: str) -> bool:
    fact = RiskyOpenConfigTraceFact.parse((_command(RiskyOpenConfigTraceFact.commands[0], output),))
    assert isinstance(fact, AvailableFact)
    return fact.value.state is ConfigurationState.CONFIGURED


expected_result = partial(build_expected_advisory_result, ADVISORY.vulnerabilities[0].id)


def sa117_eos_data(gnmi: dict[str, Any], trace: str) -> list[dict[str, Any] | str]:
    """Return production command data in required-fact declaration order."""
    return [gnmi, gnmi, trace]


_DATA: AntaUnitTestData = {
    (VerifySA117, "inconclusive-accounting-enabled"): {
        "version": build_eos_version("4.32.4M"),
        "eos_data": sa117_eos_data({"transports": {"default": {"enabled": True, "accounting": True}}}, ""),
        "expected": expected_result(
            AntaTestStatus.INCONCLUSIVE,
            "The assessment is inconclusive and the device may be affected. Indications: EOS version '4.32.4M' is affected, "
            "the gNMI feature is enabled, and the gNMI transport accounting is enabled.",
            EXPECTED_4_32_REMEDIATION,
        ),
    },
    (VerifySA117, "inconclusive-flattened-accounting-enabled"): {
        "version": build_eos_version("4.33.0F"),
        "eos_data": sa117_eos_data({"enabled": True, "accounting": True}, ""),
        "expected": expected_result(
            AntaTestStatus.INCONCLUSIVE,
            "The assessment is inconclusive and the device may be affected. Indications: EOS version '4.33.0F' is affected, "
            "the gNMI feature is enabled, and the gNMI transport accounting is enabled.",
            EXPECTED_4_33_REMEDIATION,
        ),
    },
    (VerifySA117, "inconclusive-risky-trace-configured"): {
        "version": build_eos_version("4.32.4M"),
        "eos_data": sa117_eos_data(
            {"transports": {"default": {"enabled": True, "accounting": False}}},
            "trace OpenConfig setting service/9\n",
        ),
        "expected": expected_result(
            AntaTestStatus.INCONCLUSIVE,
            "The assessment is inconclusive and the device may be affected. Indications: EOS version '4.32.4M' is affected, "
            "the gNMI feature is enabled, and the OpenConfig tracing advisory-identified selector configuration is configured.",
            EXPECTED_4_32_REMEDIATION,
        ),
    },
    (VerifySA117, "success-risky-trace-with-transport-disabled"): {
        "version": build_eos_version("4.32.4M"),
        "eos_data": sa117_eos_data({"transports": {}}, "trace OpenConfig setting service/9\n"),
        "expected": expected_result(
            AntaTestStatus.SUCCESS,
            "The device is not affected because the gNMI feature is disabled.",
            None,
        ),
    },
    (VerifySA117, "success-disabled-transport-with-accounting"): {
        "version": build_eos_version("4.32.4M"),
        "eos_data": sa117_eos_data({"transports": {"default": {"enabled": False, "accounting": True}}}, ""),
        "expected": expected_result(
            AntaTestStatus.SUCCESS,
            "The device is not affected because the gNMI feature is disabled.",
            None,
        ),
    },
    (VerifySA117, "success-flattened-disabled-transport"): {
        "version": build_eos_version("4.33.0F"),
        "eos_data": sa117_eos_data({"enabled": False, "accounting": True}, ""),
        "expected": expected_result(
            AntaTestStatus.SUCCESS,
            "The device is not affected because the gNMI feature is disabled.",
            None,
        ),
    },
    (VerifySA117, "success-accounting-and-tracing-disabled"): {
        "version": build_eos_version("4.32.4M"),
        "eos_data": sa117_eos_data(
            {"transports": {"default": {"enabled": True, "accounting": False}}},
            "trace OpenConfig setting harmless/1\n",
        ),
        "expected": expected_result(
            AntaTestStatus.SUCCESS,
            "The device is not affected because the gNMI transport accounting is disabled and the OpenConfig tracing "
            "advisory-identified selector configuration is not configured.",
            None,
        ),
    },
    (VerifySA117, "success-fixed-version"): {
        "version": build_eos_version("4.32.5M"),
        "eos_data": sa117_eos_data({}, ""),
        "expected": expected_result(
            AntaTestStatus.SUCCESS,
            "The device is not affected because EOS version '4.32.5M' is outside the affected releases",
            None,
        ),
    },
    (VerifySA117, "success-excluded-version-suffix"): {
        "version": build_eos_version("4.33.1FX-wbb"),
        "eos_data": sa117_eos_data({}, ""),
        "expected": expected_result(
            AntaTestStatus.SUCCESS,
            "The device is not affected because EOS version '4.33.1FX-wbb' is outside the affected releases",
            None,
        ),
    },
    (VerifySA117, "error-missing-device-version"): {
        "version": None,
        "eos_data": sa117_eos_data({}, ""),
        "expected": expected_result(
            AntaTestStatus.ERROR,
            "The test could not determine the EOS version because it is missing from device metadata.",
            None,
        ),
    },
    (VerifySA117, "error-malformed-transport-state"): {
        "version": build_eos_version("4.32.4M"),
        "eos_data": sa117_eos_data({}, ""),
        "expected": expected_result(
            AntaTestStatus.ERROR,
            "The test could not determine the gNMI transport state because the 'show management api gnmi' output is invalid.",
            None,
        ),
    },
    (VerifySA117, "error-malformed-accounting-state"): {
        "version": build_eos_version("4.32.4M"),
        "eos_data": sa117_eos_data({"transports": {"default": {"enabled": True}}}, ""),
        "expected": expected_result(
            AntaTestStatus.ERROR,
            "The test could not determine the gNMI transport accounting state because the 'show management api gnmi' output is incomplete.",
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
    """Validate transport, accounting, and trace evidence normalization."""

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

    def test_accounting_only_applies_to_enabled_transports(self) -> None:
        cases = (
            ({}, None),
            ({"enabled": False, "accounting": True}, False),
            ({"enabled": True, "accounting": False}, False),
            ({"enabled": True, "accounting": True}, True),
            ({"enabled": True}, None),
            ({"enabled": "invalid", "accounting": True}, None),
            ({"transports": {}}, False),
            ({"transports": None}, None),
            ({"transports": {"default": {"enabled": False, "accounting": True}}}, False),
            ({"transports": {"default": {"enabled": True, "accounting": False}}}, False),
            ({"transports": {"default": {"enabled": True, "accounting": True}}}, True),
            ({"transports": {"default": {"enabled": True}}}, None),
            (
                {
                    "transports": {
                        "unknown": {"enabled": True},
                        "affected": {"enabled": True, "accounting": True},
                    }
                },
                True,
            ),
        )
        for output, expected in cases:
            with self.subTest(output=output):
                assert _evaluate_gnmi_accounting_enabled(output) is expected

    def test_trace_selectors(self) -> None:
        for selector in ("service/9", "interceptor/9", "transport_socketcli/9"):
            with self.subTest(selector=selector):
                assert _evaluate_risky_trace_configuration(f"trace OpenConfig setting harmless/1,{selector}\n")

        assert not _evaluate_risky_trace_configuration("")
        assert not _evaluate_risky_trace_configuration("trace OpenConfig setting harmless/1\n")
        assert not _evaluate_risky_trace_configuration("trace OpenConfig setting notservice/9\n")


class TestSA117Assessment(unittest.TestCase):
    """Validate semantic classification and remediation for CVE-2025-0936."""

    def assess(
        self,
        *,
        version: object = "4.32.4M",
        gnmi: Mapping[str, object] | None = None,
        trace: bool | None = False,
    ) -> VulnerabilityResult:
        """Run the pure assessment helper with concise defaults."""
        output = {"transports": {"default": {"enabled": True, "accounting": False}}} if gnmi is None else gnmi
        source = FactSource("unit test", FactSourceKind.DEVICE_METADATA)
        if version is None:
            version_fact: Fact[EOSVersion] = EosVersionFact.unavailable(FactProblemKind.MISSING, source)
        else:
            parsed_version = parse_eos_version(version if isinstance(version, str) else str(version)).unwrap_or_none()
            version_fact = (
                EosVersionFact.available(parsed_version, source) if parsed_version is not None else EosVersionFact.unavailable(FactProblemKind.INVALID, source)
            )
        gnmi_command = _command(GnmiTransportFact.commands[0], dict(output))
        gnmi_fact = GnmiTransportFact.parse((gnmi_command,))
        accounting_fact = GnmiAccountingFact.parse((gnmi_command,))
        trace_feature = SubFeature(FeatureName.TRACE, "advisory-identified selector")
        trace_fact: Fact[ConfigurationValue] = (
            RiskyOpenConfigTraceFact.unavailable(FactProblemKind.UNSUPPORTED, source)
            if trace is None
            else RiskyOpenConfigTraceFact.available(
                ConfigurationValue(trace_feature, ConfigurationState.CONFIGURED if trace else ConfigurationState.NOT_CONFIGURED), source
            )
        )
        return _assess_sa117(version_fact, gnmi_fact, accounting_fact, trace_fact)

    def test_exposure_signals_are_inconclusive_without_control_evidence(self) -> None:
        accounting = self.assess(gnmi={"transports": {"default": {"enabled": True, "accounting": True}}})
        tracing = self.assess(trace=True)

        for finding in (accounting, tracing):
            assert isinstance(finding, InconclusiveResult)
            assert tuple(item.subject for item in finding.unresolved) == ("gNOI File service state", "effective gNSI Authz control")
            assert finding.remediation == EXPECTED_4_32_REMEDIATION

    def test_not_affected_paths(self) -> None:
        findings = (self.assess(version="4.32.5M", gnmi={}), self.assess(gnmi={"transports": {}}), self.assess())
        assert all(isinstance(finding, NotAffectedResult) for finding in findings)

    def test_fixed_version_ignores_optional_evidence(self) -> None:
        finding = self.assess(version="4.32.5M", gnmi={}, trace=None)
        assert isinstance(finding, NotAffectedResult)

    def test_unknown_required_evidence_is_error(self) -> None:
        cases = (
            {"version": None, "gnmi": {"transports": {}}, "trace": False},
            {"version": "4.32.4M", "gnmi": {}, "trace": False},
            {"version": "4.32.4M", "gnmi": {"transports": {"default": {"enabled": True}}}, "trace": False},
            {"version": "4.32.4M", "gnmi": {"transports": {"default": {"enabled": True, "accounting": False}}}, "trace": None},
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

    def test_true_or_branch_overrides_unknown_other_branch(self) -> None:
        accounting = self.assess(gnmi={"transports": {"default": {"enabled": True, "accounting": True}}}, trace=None)
        tracing = self.assess(gnmi={"transports": {"default": {"enabled": True}}}, trace=True)

        assert isinstance(accounting, InconclusiveResult)
        assert isinstance(tracing, InconclusiveResult)


class TestVerifySA117(unittest.IsolatedAsyncioTestCase):
    """Validate command orchestration and atomic-result projection."""

    async def run_test(
        self,
        gnmi_output: dict[str, Any],
        trace_output: str,
        version: str = "4.32.4M",
    ) -> VerifySA117:
        """Run SA117 with synthetic EOS output."""
        device = OfflineAntaDevice("unit-test")
        device.version = parse_eos_version(version).unwrap()
        await device.refresh()
        eos_data = sa117_eos_data(gnmi_output, trace_output)
        test = cast("Any", VerifySA117)(device=device, eos_data=eos_data)
        await test.test(eos_data=eos_data)
        return test

    async def test_error_atomic_result_preserves_vulnerability_association(self) -> None:
        test = await self.run_test({}, "")

        assert len(test.result.atomic_results) == 1
        assert _get_atomic_vulnerability_ids(test.result.atomic_results[0]) == ("CVE-2025-0936",)

    async def test_fixed_version_ignores_unsupported_optional_commands(self) -> None:
        device = OfflineAntaDevice("unit-test")
        device.version = parse_eos_version("4.32.5M").unwrap()
        await device.refresh()
        eos_data = sa117_eos_data({}, "")
        test = cast("Any", VerifySA117)(device=device, eos_data=eos_data)
        for command in test.instance_commands:
            command.output = None
            command.errors = ["This command is not supported on this hardware platform"]
        test.collect = AsyncMock()

        await test.test()

        assert test.result.result is AntaTestStatus.SUCCESS

    async def test_unsupported_required_optional_command_is_error(self) -> None:
        device = OfflineAntaDevice("unit-test")
        device.version = parse_eos_version("4.32.4M").unwrap()
        await device.refresh()
        eos_data = sa117_eos_data({"transports": {"default": {"enabled": True, "accounting": False}}}, "")
        test = cast("Any", VerifySA117)(device=device, eos_data=eos_data)
        test.instance_commands[2].output = None
        test.instance_commands[2].errors = ["This command is not supported on this hardware platform"]
        test.collect = AsyncMock()

        await test.test()

        assert test.result.result is AntaTestStatus.ERROR
        assert "show running-config section trace" in test.result.messages[0]
