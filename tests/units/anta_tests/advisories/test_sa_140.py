# Copyright (c) 2026 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
# ruff: noqa: D102, F811
# pylint: disable=duplicate-code, missing-function-docstring, redefined-outer-name
"""Unit tests for Arista Security Advisory 140."""

from __future__ import annotations

import unittest
from typing import TYPE_CHECKING, Any, Literal, cast
from unittest.mock import AsyncMock

from anta._advisory.eos_versions import AffectedStatus, evaluate_version
from anta._advisory.facts.eos import EosVersionFact, SecureBootFact
from anta._advisory.facts.models import AvailableFact, FactProblemKind, FactSource, FactSourceKind, FeatureName, FeatureState, FeatureValue
from anta._advisory.findings.models import AffectedResult, EosReleaseAssessment, ErrorResult, NotAffectedResult, VersionRelation
from anta._advisory.results import _get_atomic_vulnerability_ids
from anta._eos.version import parse_eos_version
from anta.result_manager.models import AntaTestStatus
from anta.tests.advisories.sa_140 import (
    ADVISORY,
    AFFECTED_VERSION_MATRIX,
    VerifySA140,
    _assess_sa140,
)
from tests.units.anta_tests import build_eos_version, test
from tests.units.anta_tests.advisories import OfflineAntaDevice

if TYPE_CHECKING:
    from anta.device import DeviceVersion
    from tests.units.anta_tests import AntaUnitTestData, UnitTestResult

TEST_SOURCE = FactSource("unit test", FactSourceKind.DEVICE_METADATA)


def expected_result(
    status: Literal[
        AntaTestStatus.SUCCESS,
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
                "description": f"Verify {ADVISORY.vulnerabilities[0].id}.",
                "result": status,
                "messages": [message],
                "remediations": [remediation] if remediation else [],
            }
        ],
    }


_DATA: AntaUnitTestData = {
    (VerifySA140, "failure-secure-boot-supported-and-enabled"): {
        "version": build_eos_version("4.35.1F"),
        "eos_data": [{"securebootSupported": True, "securebootEnabled": True}],
        "expected": expected_result(
            AntaTestStatus.FAILURE,
            "The device is affected because EOS version '4.35.1F' is affected and the Secure Boot feature is enabled",
            "Upgrade to",
        ),
    },
    (VerifySA140, "success-secure-boot-disabled"): {
        "version": build_eos_version("4.35.1F"),
        "eos_data": [{"securebootSupported": True, "securebootEnabled": False}],
        "expected": expected_result(
            AntaTestStatus.SUCCESS,
            "The device is not affected because the Secure Boot feature is disabled",
            "",
        ),
    },
    (VerifySA140, "success-fixed-version"): {
        "version": build_eos_version("4.35.2F"),
        "eos_data": [{}],
        "expected": expected_result(
            AntaTestStatus.SUCCESS,
            "The device is not affected because EOS version '4.35.2F' is outside the affected releases",
            "",
        ),
    },
    (VerifySA140, "error-missing-device-version"): {
        "version": None,
        "eos_data": [{}],
        "expected": expected_result(
            AntaTestStatus.ERROR,
            "The test could not determine the EOS version because it is missing from device metadata",
            "",
        ),
    },
    (VerifySA140, "success-secure-boot-unsupported-empty-output"): {
        "version": build_eos_version("4.35.1F"),
        "eos_data": [{}],
        "expected": expected_result(
            AntaTestStatus.SUCCESS,
            "The device is not affected because the Secure Boot feature is not supported",
            "",
        ),
    },
    (VerifySA140, "error-missing-secure-boot-evidence"): {
        "version": build_eos_version("4.35.1F"),
        "eos_data": [{"securebootSupported": True}],
        "expected": expected_result(
            AntaTestStatus.ERROR,
            "The test could not determine the Secure Boot feature state because the 'show boot' output is incomplete",
            "",
        ),
    },
    (VerifySA140, "error-malformed-secure-boot-evidence"): {
        "version": build_eos_version("4.35.1F"),
        "eos_data": [{"securebootSupported": "true", "securebootEnabled": True}],
        "expected": expected_result(
            AntaTestStatus.ERROR,
            "The test could not determine the Secure Boot feature state because the 'show boot' output is invalid",
            "",
        ),
    },
}


class TestSA140VersionMatrix(unittest.TestCase):
    """Validate every affected endpoint and fixed-release boundary."""

    def test_version_boundaries(self) -> None:
        cases = (
            ("4.36.0F", AffectedStatus.NOT_AFFECTED),
            ("4.35.1F", AffectedStatus.AFFECTED),
            ("4.35.1.99F", AffectedStatus.AFFECTED),
            ("4.35.2F", AffectedStatus.NOT_AFFECTED),
            ("4.34.5M", AffectedStatus.AFFECTED),
            ("4.34.6M", AffectedStatus.NOT_AFFECTED),
            ("4.33.7M", AffectedStatus.AFFECTED),
            ("4.33.8M", AffectedStatus.NOT_AFFECTED),
            ("4.32.9M", AffectedStatus.AFFECTED),
            ("4.32.10M", AffectedStatus.NOT_AFFECTED),
            ("4.31.10M", AffectedStatus.AFFECTED),
            ("4.31.11M", AffectedStatus.NOT_AFFECTED),
            ("4.30.10M", AffectedStatus.AFFECTED),
            ("4.30.11M", AffectedStatus.NOT_AFFECTED),
            ("4.29.99M", AffectedStatus.NOT_AFFECTED),
        )
        for version, expected in cases:
            with self.subTest(version=version):
                evaluation = evaluate_version(parse_eos_version(version), AFFECTED_VERSION_MATRIX)
                assert evaluation.affected_status is expected


class TestSA140Assessment(unittest.TestCase):
    """Validate semantic classification before ANTA projection."""

    @staticmethod
    def version_fact(version: str) -> AvailableFact[DeviceVersion]:
        """Build normalized device-version evidence for assessment tests."""
        parsed_version = parse_eos_version(version)
        assert parsed_version is not None
        return EosVersionFact.available(parsed_version, TEST_SOURCE)

    def test_affected_and_safe_configuration_states(self) -> None:
        affected = _assess_sa140(
            self.version_fact("4.35.1F"),
            SecureBootFact.available(FeatureValue(FeatureName.SECURE_BOOT, FeatureState.ENABLED), TEST_SOURCE),
        )
        disabled = _assess_sa140(
            self.version_fact("4.35.1F"),
            SecureBootFact.available(FeatureValue(FeatureName.SECURE_BOOT, FeatureState.DISABLED), TEST_SOURCE),
        )

        assert isinstance(affected, AffectedResult)
        condition = affected.conditions[0]
        assert isinstance(condition, AvailableFact)
        assert isinstance(condition.value, FeatureValue)
        assert condition.value.state is FeatureState.ENABLED
        assert affected.context[0].relation is VersionRelation.AFFECTED
        assert "4.35.2F or later" in affected.remediation
        assert "http" not in affected.remediation
        assert isinstance(disabled, NotAffectedResult)
        disabled_evidence = cast("AvailableFact[FeatureValue]", disabled.decisive[0])
        assert disabled_evidence.value.state is FeatureState.DISABLED

    def test_fixed_version_short_circuits_boot_evidence(self) -> None:
        finding = _assess_sa140(
            self.version_fact("4.35.2F"),
            SecureBootFact.unavailable(FactProblemKind.MISSING, TEST_SOURCE),
        )

        assert isinstance(finding, NotAffectedResult)
        version_assessment = cast("EosReleaseAssessment", finding.decisive[0])
        assert version_assessment.relation is VersionRelation.OUTSIDE_SCOPE

    def test_unsupported_secure_boot_is_not_affected(self) -> None:
        secure_boot = SecureBootFact.available(FeatureValue(FeatureName.SECURE_BOOT, FeatureState.UNSUPPORTED), TEST_SOURCE)
        finding = _assess_sa140(self.version_fact("4.35.1F"), secure_boot)

        assert isinstance(finding, NotAffectedResult)
        secure_boot_evidence = cast("AvailableFact[FeatureValue]", finding.decisive[0])
        assert secure_boot_evidence.value.state is FeatureState.UNSUPPORTED

    def test_unavailable_required_fact_is_error(self) -> None:
        finding = _assess_sa140(
            self.version_fact("4.35.1F"),
            SecureBootFact.unavailable(FactProblemKind.MALFORMED, TEST_SOURCE),
        )

        assert isinstance(finding, ErrorResult)
        assert finding.problems[0].definition is SecureBootFact


class TestVerifySA140(unittest.IsolatedAsyncioTestCase):
    """Validate atomic projection and required-command behavior."""

    async def run_test(
        self,
        boot_output: dict[str, Any],
        version: str | None = "4.35.1F",
    ) -> VerifySA140:
        """Run the ANTA test with synthetic structured EOS output."""
        device = OfflineAntaDevice("unit-test")
        device.version = parse_eos_version(version) if version is not None else None
        await device.refresh()
        eos_data: list[dict[str, Any] | str] = [boot_output]
        test = cast("Any", VerifySA140)(device=device, eos_data=eos_data)

        await test.test(eos_data=eos_data)

        return test

    def test_commands_are_derived_from_required_facts(self) -> None:
        """Derive commands from the facts required by the advisory test."""
        assert VerifySA140.commands == [SecureBootFact.command]

    async def test_error_atomic_result_preserves_vulnerability_association(self) -> None:
        test = await self.run_test({"securebootSupported": True})

        assert test.result.result is AntaTestStatus.ERROR
        assert len(test.result.atomic_results) == 1
        assert _get_atomic_vulnerability_ids(test.result.atomic_results[0]) == ("CVE-2026-10040",)

    async def test_unsupported_boot_command_uses_native_anta_handling(self) -> None:
        device = OfflineAntaDevice("unit-test")
        device.version = parse_eos_version("4.35.1F")
        await device.refresh()
        eos_data: list[dict[str, Any] | str] = [{}]
        test = cast("Any", VerifySA140)(device=device, eos_data=eos_data)
        test.instance_commands[0].output = None
        test.instance_commands[0].errors = ["This command is not supported on this hardware platform"]
        test.collect = AsyncMock()

        await test.test()

        assert test.result.result is AntaTestStatus.SKIPPED
        assert "show boot" in test.result.messages[0]
