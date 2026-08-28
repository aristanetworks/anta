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
from anta._advisory.results import _get_atomic_vulnerability_ids
from anta._advisory.status import AdvisoryStatus
from anta._eos.version import parse_eos_version
from anta.result_manager.models import AntaTestStatus
from anta.tests.advisories.sa_140 import (
    ADVISORY,
    AFFECTED_VERSION_MATRIX,
    VerifySA140,
    _assess_sa140,
    _is_secure_boot_supported_and_enabled,
)
from tests.units.anta_tests import test
from tests.units.anta_tests.advisories import OfflineAntaDevice

if TYPE_CHECKING:
    from tests.units.anta_tests import AntaUnitTestData, UnitTestResult


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
                "description": ADVISORY.vulnerabilities[0].description,
                "result": status,
                "messages": [message],
                "remediations": [remediation] if remediation else [],
            }
        ],
    }


_DATA: AntaUnitTestData = {
    (VerifySA140, "failure-secure-boot-supported-and-enabled"): {
        "version": "4.35.1F",
        "eos_data": [{"securebootSupported": True, "securebootEnabled": True}],
        "expected": expected_result(
            AntaTestStatus.FAILURE,
            "The device is affected because EOS version '4.35.1F' is affected and Secure Boot is supported and enabled",
            "Upgrade to",
        ),
    },
    (VerifySA140, "success-secure-boot-disabled"): {
        "version": "4.35.1F",
        "eos_data": [{"securebootSupported": True, "securebootEnabled": False}],
        "expected": expected_result(
            AntaTestStatus.SUCCESS,
            "The device is not affected because Secure Boot is unsupported or disabled",
            "",
        ),
    },
    (VerifySA140, "success-fixed-version"): {
        "version": "4.35.2F",
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
            "The EOS version is unavailable from the refreshed device metadata",
            "Collect or correct valid refreshed device EOS version metadata",
        ),
    },
    (VerifySA140, "success-secure-boot-unsupported-empty-output"): {
        "version": "4.35.1F",
        "eos_data": [{}],
        "expected": expected_result(
            AntaTestStatus.SUCCESS,
            "The device is not affected because Secure Boot is unsupported or disabled",
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


class TestSA140SecureBoot(unittest.TestCase):
    """Validate all structured Secure Boot state combinations."""

    def test_supported_and_enabled_is_exposed(self) -> None:
        assert _is_secure_boot_supported_and_enabled({"securebootSupported": True, "securebootEnabled": True})

    def test_any_false_prerequisite_is_safe(self) -> None:
        for output in (
            {"securebootSupported": False, "securebootEnabled": False},
            {"securebootSupported": True, "securebootEnabled": False},
            {"securebootSupported": False},
            {"securebootEnabled": False},
        ):
            with self.subTest(output=output):
                assert not _is_secure_boot_supported_and_enabled(output)

    def test_missing_or_malformed_evidence_is_unknown(self) -> None:
        for output in (
            {"securebootSupported": True},
            {"securebootEnabled": True},
            {"securebootSupported": False, "securebootEnabled": True},
            {"securebootSupported": "true", "securebootEnabled": True},
            {"securebootSupported": True, "securebootEnabled": 1},
        ):
            with self.subTest(output=output):
                assert _is_secure_boot_supported_and_enabled(output) is None


class TestSA140Assessment(unittest.TestCase):
    """Validate semantic classification before ANTA projection."""

    def test_affected_and_safe_configuration_states(self) -> None:
        affected_status, affected_message, affected_remediation = _assess_sa140(
            parse_eos_version("4.35.1F"),
            {"securebootSupported": True, "securebootEnabled": True},
        )
        disabled_status, _, disabled_remediation = _assess_sa140(
            parse_eos_version("4.35.1F"),
            {"securebootSupported": True, "securebootEnabled": False},
        )

        assert affected_status is AdvisoryStatus.AFFECTED
        assert "affected" in affected_message
        assert "4.35.2F or later" in affected_remediation
        assert "http" not in affected_remediation
        assert disabled_status is AdvisoryStatus.NOT_AFFECTED
        assert disabled_remediation == ""

    def test_fixed_version_short_circuits_boot_evidence(self) -> None:
        status, _, _ = _assess_sa140(parse_eos_version("4.35.2F"), {})

        assert status is AdvisoryStatus.NOT_AFFECTED

    def test_empty_boot_output_is_not_affected(self) -> None:
        status, _, _ = _assess_sa140(parse_eos_version("4.35.1F"), {})

        assert status is AdvisoryStatus.NOT_AFFECTED


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
