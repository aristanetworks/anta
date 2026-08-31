# Copyright (c) 2026 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
# ruff: noqa: D102, F811, FBT003
# pylint: disable=duplicate-code, missing-function-docstring, redefined-outer-name
"""Unit tests for Arista Security Advisory 117."""

from __future__ import annotations

import unittest
from typing import TYPE_CHECKING, Any, Literal, cast
from unittest.mock import AsyncMock

from anta._advisory.eos_versions import AffectedStatus, evaluate_version
from anta._advisory.results import _get_atomic_vulnerability_ids
from anta._advisory.status import AdvisoryAssessment, AdvisoryStatus
from anta._eos.version import parse_eos_version
from anta.result_manager.models import AntaTestStatus
from anta.tests.advisories.sa_117 import (
    ADVISORY,
    AFFECTED_VERSION_MATRIX,
    VerifySA117,
    _assess_sa117,
    _evaluate_gnmi_accounting_enabled,
    _evaluate_gnmi_transport_enabled,
    _evaluate_risky_trace_configuration,
)
from tests.units.anta_tests import test
from tests.units.anta_tests.advisories import OfflineAntaDevice

if TYPE_CHECKING:
    from collections.abc import Mapping

    from tests.units.anta_tests import AntaUnitTestData, UnitTestResult


def expected_result(
    status: Literal[
        AntaTestStatus.SUCCESS,
        AntaTestStatus.INCONCLUSIVE,
        AntaTestStatus.FAILURE,
        AntaTestStatus.ERROR,
    ],
    message: str,
    remediation: str,
) -> UnitTestResult:
    """Build matching parent and atomic expectations for one production case."""
    return {
        "result": status,
        "messages": [message],
        "remediations": [remediation] if remediation else [],
        "atomic_results": [
            {
                "description": ADVISORY.vulnerabilities[0].description,
                "result": status,
                "messages": [message],
                "remediations": [remediation] if remediation else [],
            }
        ],
    }


_DATA: AntaUnitTestData = {
    (VerifySA117, "inconclusive-accounting-enabled"): {
        "version": "4.32.4M",
        "eos_data": [
            {"transports": {"default": {"enabled": True, "accounting": True}}},
            "",
        ],
        "expected": expected_result(
            AntaTestStatus.INCONCLUSIVE,
            "The assessment is inconclusive and the device may be affected because EOS version '4.32.4M' has an enabled gNMI transport with accounting enabled",
            "Upgrade to",
        ),
    },
    (VerifySA117, "inconclusive-flattened-accounting-enabled"): {
        "version": "4.33.0F",
        "eos_data": [
            {"enabled": True, "accounting": True},
            "",
        ],
        "expected": expected_result(
            AntaTestStatus.INCONCLUSIVE,
            "The assessment is inconclusive and the device may be affected because EOS version '4.33.0F' has an enabled gNMI transport with accounting enabled",
            "Upgrade to",
        ),
    },
    (VerifySA117, "inconclusive-risky-trace-configured"): {
        "version": "4.32.4M",
        "eos_data": [
            {"transports": {"default": {"enabled": True, "accounting": False}}},
            "trace OpenConfig setting service/9\n",
        ],
        "expected": expected_result(
            AntaTestStatus.INCONCLUSIVE,
            "The assessment is inconclusive and the device may be affected because EOS version "
            "'4.32.4M' has an enabled gNMI transport and OpenConfig tracing includes a selector "
            "identified by the advisory",
            "Upgrade to",
        ),
    },
    (VerifySA117, "success-risky-trace-with-transport-disabled"): {
        "version": "4.32.4M",
        "eos_data": [
            {"transports": {}},
            "trace OpenConfig setting service/9\n",
        ],
        "expected": expected_result(
            AntaTestStatus.SUCCESS,
            "The device is not affected because no gNMI transport is enabled",
            "",
        ),
    },
    (VerifySA117, "success-disabled-transport-with-accounting"): {
        "version": "4.32.4M",
        "eos_data": [
            {"transports": {"default": {"enabled": False, "accounting": True}}},
            "",
        ],
        "expected": expected_result(
            AntaTestStatus.SUCCESS,
            "The device is not affected because no gNMI transport is enabled",
            "",
        ),
    },
    (VerifySA117, "success-flattened-disabled-transport"): {
        "version": "4.33.0F",
        "eos_data": [
            {"enabled": False, "accounting": True},
            "",
        ],
        "expected": expected_result(
            AntaTestStatus.SUCCESS,
            "The device is not affected because no gNMI transport is enabled",
            "",
        ),
    },
    (VerifySA117, "success-accounting-and-tracing-disabled"): {
        "version": "4.32.4M",
        "eos_data": [
            {"transports": {"default": {"enabled": True, "accounting": False}}},
            "trace OpenConfig setting harmless/1\n",
        ],
        "expected": expected_result(
            AntaTestStatus.SUCCESS,
            "The device is not affected because enabled gNMI transports do not use accounting and no advisory-identified OpenConfig trace selector is configured",
            "",
        ),
    },
    (VerifySA117, "success-fixed-version"): {
        "version": "4.32.5M",
        "eos_data": [{}, ""],
        "expected": expected_result(
            AntaTestStatus.SUCCESS,
            "The device is not affected because EOS version '4.32.5M' is outside the affected releases",
            "",
        ),
    },
    (VerifySA117, "success-excluded-version-suffix"): {
        "version": "4.33.1FX-wbb",
        "eos_data": [{}, ""],
        "expected": expected_result(
            AntaTestStatus.SUCCESS,
            "The device is not affected because EOS version '4.33.1FX-wbb' is outside the affected releases",
            "",
        ),
    },
    (VerifySA117, "error-missing-device-version"): {
        "version": None,
        "eos_data": [{}, ""],
        "expected": expected_result(
            AntaTestStatus.ERROR,
            "The EOS version is unavailable from the refreshed device metadata",
            "Collect or correct valid refreshed device EOS version metadata",
        ),
    },
    (VerifySA117, "error-malformed-transport-state"): {
        "version": "4.32.4M",
        "eos_data": [{}, ""],
        "expected": expected_result(
            AntaTestStatus.ERROR,
            "The gNMI transport enabled state is missing or malformed",
            "Collect or correct valid gNMI transport enabled-state evidence",
        ),
    },
    (VerifySA117, "error-malformed-accounting-state"): {
        "version": "4.32.4M",
        "eos_data": [
            {"transports": {"default": {"enabled": True}}},
            "",
        ],
        "expected": expected_result(
            AntaTestStatus.ERROR,
            "The accounting state of an enabled gNMI transport is missing or malformed",
            "Collect or correct valid gNMI transport accounting evidence",
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
                evaluation = evaluate_version(parse_eos_version(version), AFFECTED_VERSION_MATRIX)
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
    ) -> AdvisoryAssessment:
        """Run the pure assessment helper with concise defaults."""
        output = {"transports": {"default": {"enabled": True, "accounting": False}}} if gnmi is None else gnmi
        device_version = parse_eos_version(version) if isinstance(version, str) else None
        return _assess_sa117(device_version, output, trace)

    def test_exposure_signals_are_inconclusive_without_control_evidence(self) -> None:
        accounting_status, accounting_message, accounting_remediation = self.assess(gnmi={"transports": {"default": {"enabled": True, "accounting": True}}})
        tracing_status, tracing_message, tracing_remediation = self.assess(trace=True)

        for status, message, remediation in (
            (accounting_status, accounting_message, accounting_remediation),
            (tracing_status, tracing_message, tracing_remediation),
        ):
            assert status is AdvisoryStatus.INCONCLUSIVE
            assert "may be affected" in message
            assert "gNOI File" in message
            assert "gNSI Authz" in message
            assert "4.30.10M or later" in remediation
            assert "4.33.2F or later" in remediation
            assert "http" not in remediation

    def test_not_affected_paths(self) -> None:
        fixed, _, fixed_remediation = self.assess(version="4.32.5M", gnmi={})
        disabled, _, disabled_remediation = self.assess(gnmi={"transports": {}})
        safe, _, safe_remediation = self.assess()

        for status in (fixed, disabled, safe):
            assert status is AdvisoryStatus.NOT_AFFECTED
        assert fixed_remediation == ""
        assert disabled_remediation == ""
        assert safe_remediation == ""

    def test_fixed_version_ignores_optional_evidence(self) -> None:
        status, _, remediation = _assess_sa117(parse_eos_version("4.32.5M"), None, None)

        assert status is AdvisoryStatus.NOT_AFFECTED
        assert remediation == ""

    def test_unknown_required_evidence_is_error(self) -> None:
        cases = (
            (None, {"transports": {}}, False, "device metadata"),
            (parse_eos_version("4.32.4M"), None, False, "show management api gnmi"),
            (parse_eos_version("4.32.4M"), {}, False, "transport enabled state"),
            (
                parse_eos_version("4.32.4M"),
                {"transports": {"default": {"enabled": True}}},
                False,
                "accounting state",
            ),
            (
                parse_eos_version("4.32.4M"),
                {"transports": {"default": {"enabled": True, "accounting": False}}},
                None,
                "trace configuration",
            ),
        )
        for version, gnmi, trace, message in cases:
            with self.subTest(message=message):
                status, result_message, remediation = _assess_sa117(version, gnmi, trace)
                assert status is AdvisoryStatus.ERROR
                assert message in result_message
                assert "rerun" in remediation

    def test_true_or_branch_overrides_unknown_other_branch(self) -> None:
        accounting, _, _ = _assess_sa117(
            parse_eos_version("4.32.4M"),
            {"transports": {"default": {"enabled": True, "accounting": True}}},
            None,
        )
        tracing, _, _ = _assess_sa117(
            parse_eos_version("4.32.4M"),
            {"transports": {"default": {"enabled": True}}},
            True,
        )

        assert accounting is AdvisoryStatus.INCONCLUSIVE
        assert tracing is AdvisoryStatus.INCONCLUSIVE


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
        device.version = parse_eos_version(version)
        await device.refresh()
        eos_data = [gnmi_output, trace_output]
        test = cast("Any", VerifySA117)(device=device, eos_data=eos_data)
        await test.test(eos_data=eos_data)
        return test

    async def test_error_atomic_result_preserves_vulnerability_association(self) -> None:
        test = await self.run_test({}, "")

        assert len(test.result.atomic_results) == 1
        assert _get_atomic_vulnerability_ids(test.result.atomic_results[0]) == ("CVE-2025-0936",)

    async def test_fixed_version_ignores_unsupported_optional_commands(self) -> None:
        device = OfflineAntaDevice("unit-test")
        device.version = parse_eos_version("4.32.5M")
        await device.refresh()
        eos_data = [{}, ""]
        test = cast("Any", VerifySA117)(device=device, eos_data=eos_data)
        for command in test.instance_commands:
            command.output = None
            command.errors = ["This command is not supported on this hardware platform"]
        test.collect = AsyncMock()

        await test.test()

        assert test.result.result is AntaTestStatus.SUCCESS

    async def test_unsupported_required_optional_command_is_error(self) -> None:
        device = OfflineAntaDevice("unit-test")
        device.version = parse_eos_version("4.32.4M")
        await device.refresh()
        eos_data = [
            {"transports": {"default": {"enabled": True, "accounting": False}}},
            "",
        ]
        test = cast("Any", VerifySA117)(device=device, eos_data=eos_data)
        test.instance_commands[1].output = None
        test.instance_commands[1].errors = ["This command is not supported on this hardware platform"]
        test.collect = AsyncMock()

        await test.test()

        assert test.result.result is AntaTestStatus.ERROR
        assert "show running-config section trace" in test.result.messages[0]
