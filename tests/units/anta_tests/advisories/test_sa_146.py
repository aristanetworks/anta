# Copyright (c) 2026 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
# ruff: noqa: D102, F811
# pylint: disable=missing-function-docstring, redefined-outer-name
"""Unit tests for Arista Security Advisory 146."""

from __future__ import annotations

import unittest
from typing import TYPE_CHECKING, Any, Literal, cast
from unittest.mock import AsyncMock

from anta._advisory.eos_versions import AffectedStatus, evaluate_version
from anta._advisory.remediation import upgrade_remediation
from anta._advisory.results import _get_atomic_vulnerability_ids
from anta._advisory.status import AdvisoryAssessment, AdvisoryStatus
from anta._eos.version import parse_eos_version_or_none
from anta.result_manager.models import AntaTestStatus
from anta.tests.advisories.sa_146 import (
    ADVISORY,
    EOS_AFFECTED_VERSION_MATRIX,
    EOS_FIXED_RELEASES,
    TERMINATTR_FIXED_RELEASES,
    VerifySA146,
    _assess_sa146,
    _evaluate_gnmi_grpc_enabled,
    _evaluate_gnmi_mtls,
    _evaluate_gribi_grpc_enabled,
    _evaluate_gribi_mtls,
    _evaluate_terminattr_enabled,
    _evaluate_terminattr_mtls,
    _extract_terminattr_version,
    _has_terminattr_grpcaddr,
    _is_affected_terminattr_version,
    _ssl_profile_has_mtls,
)
from tests.units.anta_tests import build_eos_version, test
from tests.units.anta_tests.advisories import OfflineAntaDevice

if TYPE_CHECKING:
    from tests.units.anta_tests import AntaUnitTestData, UnitTestResult


def version_output(*, eos: str = "4.35.5M", terminattr: str | None = "v1.45.0") -> dict[str, Any]:
    """Return compact ``show version detail`` output."""
    packages: dict[str, Any] = {}
    if terminattr is not None:
        packages["TerminAttr-core"] = {"version": terminattr, "release": "1"}
    return {"version": eos, "details": {"packages": packages}}


def gnmi_output(*, enabled: bool, profile: str = "") -> dict[str, Any]:
    """Return compact gNMI service output using the multi-transport schema."""
    return {
        "enabled": enabled,
        "transports": {"default": {"enabled": enabled, "sslProfile": profile}} if enabled else {},
    }


def gribi_output(*, enabled: bool, profile: str = "", mtls: bool = False) -> dict[str, Any]:
    """Return compact gRIBI output using fields observed on EOS 4.35.4M."""
    return {"enabled": enabled, "sslProfile": profile, "mTls": mtls}


def ssl_profiles(*, valid: bool = True, trusted: bool = True) -> dict[str, Any]:
    """Return compact SSL profile status using observed EOS field names."""
    return {
        "profileStatus": {
            "mtls": {
                "profileState": "valid" if valid else "invalid",
                "profileError": [] if valid else [{"errorType": "invalid"}],
                "certName": "target.crt",
                "keyName": "target.key",
                "trustedCertificates": ["ca.crt"] if trusted else [],
            }
        }
    }


def terminattr_output(*, enabled: bool) -> dict[str, Any]:
    """Return compact TerminAttr daemon output."""
    return {"daemons": {"TerminAttr": {"enabled": enabled, "running": enabled}}}


TERMINATTR_GRPC = "daemon TerminAttr\n   exec /usr/bin/TerminAttr -grpcaddr 0.0.0.0:6042"
TERMINATTR_MTLS = TERMINATTR_GRPC + " -certfile /persist/target.crt -keyfile /persist/target.key -clientcafile /persist/ca.crt"


def sa146_eos_data(
    *,
    gnmi: dict[str, Any] | None = None,
    gribi: dict[str, Any] | None = None,
    terminattr: dict[str, Any] | None = None,
    grpcaddr: str = "",
    profiles: dict[str, Any] | None = None,
    version: dict[str, Any] | None = None,
) -> list[dict[str, Any] | str]:
    """Return production command data in declaration order."""
    return [
        version if version is not None else version_output(),
        gnmi if gnmi is not None else gnmi_output(enabled=False),
        gribi if gribi is not None else gribi_output(enabled=False),
        terminattr if terminattr is not None else terminattr_output(enabled=False),
        grpcaddr,
        profiles if profiles is not None else ssl_profiles(),
    ]


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
                "description": f"Verify {ADVISORY.vulnerabilities[0].id}.",
                "result": status,
                "messages": [message],
                "remediations": [remediation] if remediation else [],
            }
        ],
    }


_DATA: AntaUnitTestData = {
    (VerifySA146, "failure-gnmi-without-mtls"): {
        "version": build_eos_version("4.35.5M"),
        "eos_data": sa146_eos_data(gnmi=gnmi_output(enabled=True)),
        "expected": expected_result(
            AntaTestStatus.FAILURE,
            "The device is affected because vulnerable gRPC server path(s) are enabled without complete mTLS: gNMI",
            "Upgrade to",
        ),
    },
    (VerifySA146, "failure-gribi-without-mtls"): {
        "version": build_eos_version("4.35.5M"),
        "eos_data": sa146_eos_data(gribi=gribi_output(enabled=True)),
        "expected": expected_result(
            AntaTestStatus.FAILURE,
            "The device is affected because vulnerable gRPC server path(s) are enabled without complete mTLS: gRIBI",
            "Upgrade to",
        ),
    },
    (VerifySA146, "failure-terminattr-without-mtls"): {
        "version": build_eos_version("4.35.5M"),
        "eos_data": sa146_eos_data(
            terminattr=terminattr_output(enabled=True),
            grpcaddr=TERMINATTR_GRPC,
        ),
        "expected": expected_result(
            AntaTestStatus.FAILURE,
            "The device is affected because vulnerable gRPC server path(s) are enabled without complete mTLS: TerminAttr",
            "Upgrade to",
        ),
    },
    (VerifySA146, "failure-mixed-eos-and-terminattr-paths"): {
        "version": build_eos_version("4.35.5M"),
        "eos_data": sa146_eos_data(
            gnmi=gnmi_output(enabled=True),
            terminattr=terminattr_output(enabled=True),
            grpcaddr=TERMINATTR_GRPC,
        ),
        "expected": expected_result(
            AntaTestStatus.FAILURE,
            "The device is affected because vulnerable gRPC server path(s) are enabled without complete mTLS: gNMI, TerminAttr",
            upgrade_remediation(EOS_FIXED_RELEASES + TERMINATTR_FIXED_RELEASES),
        ),
    },
    (VerifySA146, "failure-known-path-with-malformed-sibling"): {
        "version": build_eos_version("4.35.5M"),
        "eos_data": sa146_eos_data(gnmi=gnmi_output(enabled=True), gribi={}),
        "expected": expected_result(
            AntaTestStatus.FAILURE,
            "The device is affected because vulnerable gRPC server path(s) are enabled without complete mTLS: gNMI",
            "Upgrade to",
        ),
    },
    (VerifySA146, "inconclusive-all-paths-mitigated"): {
        "version": build_eos_version("4.35.5M"),
        "eos_data": sa146_eos_data(
            gnmi=gnmi_output(enabled=True, profile="mtls"),
            gribi=gribi_output(enabled=True, profile="mtls", mtls=True),
            terminattr=terminattr_output(enabled=True),
            grpcaddr=TERMINATTR_MTLS,
        ),
        "expected": expected_result(
            AntaTestStatus.INCONCLUSIVE,
            "The device is affected but mitigated because verified mTLS covers the affected gRPC server path(s): gNMI, gRIBI, TerminAttr",
            "Upgrade to",
        ),
    },
    (VerifySA146, "failure-terminattr-independent-of-fixed-eos"): {
        "version": build_eos_version("4.36.2F"),
        "eos_data": sa146_eos_data(
            terminattr=terminattr_output(enabled=True),
            grpcaddr=TERMINATTR_GRPC,
            version=version_output(eos="4.36.2F", terminattr="v1.45.0"),
        ),
        "expected": expected_result(
            AntaTestStatus.FAILURE,
            "The device is affected because vulnerable gRPC server path(s) are enabled without complete mTLS: TerminAttr",
            "Upgrade to",
        ),
    },
    (VerifySA146, "success-fixed-eos-and-terminattr"): {
        "version": build_eos_version("4.35.6M"),
        "eos_data": sa146_eos_data(
            gnmi=gnmi_output(enabled=True),
            version=version_output(eos="4.35.6M", terminattr="v1.45.1"),
        ),
        "expected": expected_result(
            AntaTestStatus.SUCCESS,
            "The device is not affected because no enabled gRPC server is on an affected software version",
            "",
        ),
    },
    (VerifySA146, "success-terminattr-not-configured"): {
        "version": build_eos_version("4.35.5M"),
        "eos_data": sa146_eos_data(terminattr={"daemons": {}}),
        "expected": expected_result(
            AntaTestStatus.SUCCESS,
            "The device is not affected because no enabled gRPC server is on an affected software version",
            "",
        ),
    },
    (VerifySA146, "success-fixed-versions-ignore-malformed-service-output"): {
        "version": build_eos_version("4.35.6M"),
        "eos_data": sa146_eos_data(
            gnmi={},
            gribi={},
            terminattr={},
            version=version_output(eos="4.35.6M", terminattr="v1.45.1"),
        ),
        "expected": expected_result(
            AntaTestStatus.SUCCESS,
            "The device is not affected because no enabled gRPC server is on an affected software version",
            "",
        ),
    },
    (VerifySA146, "error-malformed-gnmi-enabled-state"): {
        "version": build_eos_version("4.35.5M"),
        "eos_data": sa146_eos_data(gnmi={}),
        "expected": expected_result(
            AntaTestStatus.ERROR,
            "The following required evidence is unavailable or invalid: gNMI enabled state",
            "Collect or correct gNMI enabled state",
        ),
    },
    (VerifySA146, "error-malformed-gnmi-mtls-state"): {
        "version": build_eos_version("4.35.5M"),
        "eos_data": sa146_eos_data(
            gnmi=gnmi_output(enabled=True, profile="mtls"),
            profiles={},
        ),
        "expected": expected_result(
            AntaTestStatus.ERROR,
            "The following required evidence is unavailable or invalid: gNMI mTLS state",
            "Collect or correct gNMI mTLS state",
        ),
    },
}


class TestSA146EOSVersions(unittest.TestCase):
    """Validate every documented EOS affected and fixed boundary."""

    def test_version_boundaries(self) -> None:
        cases = (
            ("4.36.1F", AffectedStatus.AFFECTED),
            ("4.36.2F", AffectedStatus.NOT_AFFECTED),
            ("4.35.5M", AffectedStatus.AFFECTED),
            ("4.35.6M", AffectedStatus.NOT_AFFECTED),
            ("4.34.6M", AffectedStatus.AFFECTED),
            ("4.34.7M", AffectedStatus.AFFECTED),
            ("4.34.7.1M", AffectedStatus.AFFECTED),
            ("4.34.7.2M", AffectedStatus.NOT_AFFECTED),
            ("4.34.8M", AffectedStatus.NOT_AFFECTED),
            ("4.33.8M", AffectedStatus.AFFECTED),
            ("4.33.9M", AffectedStatus.NOT_AFFECTED),
            ("4.32.99M", AffectedStatus.AFFECTED),
        )
        for version, expected in cases:
            with self.subTest(version=version):
                assert evaluate_version(parse_eos_version_or_none(version), EOS_AFFECTED_VERSION_MATRIX).affected_status is expected


class TestSA146TerminAttrVersions(unittest.TestCase):
    """Validate every discontinuous Streaming Telemetry Agent range."""

    def test_version_boundaries(self) -> None:
        cases = (
            ("v0.99.99", True),
            ("v1.30.99", True),
            ("v1.31.16", True),
            ("v1.31.17", False),
            ("v1.32.99", True),
            ("v1.33.99", True),
            ("v1.34.13", True),
            ("v1.34.14", False),
            ("v1.35.99", True),
            ("v1.36.99", True),
            ("v1.37.12", True),
            ("v1.37.13", False),
            ("v1.38.99", True),
            ("v1.39.99", True),
            ("v1.40.12", True),
            ("v1.40.13", False),
            ("v1.41.99", True),
            ("v1.42.99", True),
            ("v1.43.7", True),
            ("v1.43.8", False),
            ("v1.44.0", False),
            ("v1.45.0", True),
            ("v1.45.1", False),
            ("v1.46.0", False),
            ("v2.0.0", False),
        )
        for version, expected in cases:
            with self.subTest(version=version):
                assert _is_affected_terminattr_version(version) is expected

    def test_unknown_version_formats(self) -> None:
        for version in ("", "1.45.0", "v1.45", "v1.45.0-rc1"):
            with self.subTest(version=version):
                assert _is_affected_terminattr_version(version) is None


class TestSA146Evidence(unittest.TestCase):
    """Validate service, software, and complete mTLS evidence."""

    def test_gnmi_transport_schema_variants(self) -> None:
        assert _evaluate_gnmi_grpc_enabled(gnmi_output(enabled=True))
        assert not _evaluate_gnmi_grpc_enabled(gnmi_output(enabled=False))
        assert not _evaluate_gnmi_grpc_enabled({"enabled": False, "port": 0, "sslProfile": "", "error": ""})
        assert _evaluate_gnmi_grpc_enabled({}) is None
        assert _evaluate_gnmi_grpc_enabled({"enabled": False, "transports": {"default": {"enabled": True}}}) is None

    def test_gribi_and_terminattr_states(self) -> None:
        assert _evaluate_gribi_grpc_enabled(gribi_output(enabled=True))
        assert not _evaluate_gribi_grpc_enabled(gribi_output(enabled=False))
        assert _evaluate_gribi_grpc_enabled({"enabled": "true"}) is None
        assert _evaluate_terminattr_enabled(terminattr_output(enabled=True))
        assert not _evaluate_terminattr_enabled(terminattr_output(enabled=False))
        assert not _evaluate_terminattr_enabled({"daemons": {}})
        assert _evaluate_terminattr_enabled({}) is None

    def test_terminattr_configuration_and_version(self) -> None:
        assert _has_terminattr_grpcaddr(TERMINATTR_GRPC)
        assert _has_terminattr_grpcaddr("exec /usr/bin/TerminAttr -grpcaddr=0.0.0.0:6042")
        assert not _has_terminattr_grpcaddr("daemon TerminAttr")
        assert _evaluate_terminattr_mtls(TERMINATTR_MTLS)
        assert _evaluate_terminattr_mtls("exec /usr/bin/TerminAttr -grpcaddr=0.0.0.0:6042 -certfile=target.crt -keyfile=target.key -clientcafile=ca.crt")
        assert not _evaluate_terminattr_mtls("exec /usr/bin/TerminAttr -grpcaddr 0.0.0.0:6042 -certfile -keyfile target.key -clientcafile ca.crt")
        assert not _evaluate_terminattr_mtls(TERMINATTR_GRPC)
        unrelated_mtls = TERMINATTR_GRPC + "\ndaemon Other\n   exec /usr/bin/Other -certfile other.crt -keyfile other.key -clientcafile ca.crt"
        assert not _evaluate_terminattr_mtls(unrelated_mtls)
        assert _extract_terminattr_version(version_output()) == "v1.45.0"
        assert _extract_terminattr_version(version_output(terminattr=None)) is None

    def test_ssl_profile_requires_valid_server_and_trust_material(self) -> None:
        assert _ssl_profile_has_mtls("mtls", ssl_profiles())
        assert not _ssl_profile_has_mtls("", ssl_profiles())
        assert not _ssl_profile_has_mtls("mtls", ssl_profiles(valid=False))
        assert not _ssl_profile_has_mtls("mtls", ssl_profiles(trusted=False))
        assert _ssl_profile_has_mtls("missing", ssl_profiles()) is None
        assert _ssl_profile_has_mtls("mtls", {}) is None

    def test_mtls_must_cover_every_enabled_transport(self) -> None:
        gnmi = {
            "enabled": True,
            "transports": {
                "default": {"enabled": True, "sslProfile": "mtls"},
                "other": {"enabled": True, "sslProfile": ""},
            },
        }
        assert not _evaluate_gnmi_mtls(gnmi, ssl_profiles())
        gnmi["transports"]["other"]["sslProfile"] = "mtls"
        assert _evaluate_gnmi_mtls(gnmi, ssl_profiles())

        assert _evaluate_gribi_mtls(gribi_output(enabled=True, profile="mtls", mtls=True), ssl_profiles())
        assert not _evaluate_gribi_mtls(gribi_output(enabled=True, profile="mtls", mtls=False), ssl_profiles())


class TestSA146Assessment(unittest.TestCase):
    """Validate semantic state precedence across independent gRPC paths."""

    def assess(self, **overrides: bool | None) -> AdvisoryAssessment:
        """Assess default disabled paths with selected evidence overrides."""
        arguments: dict[str, bool | None] = {
            "eos_affected": True,
            "gnmi_enabled": False,
            "gnmi_mtls": None,
            "gribi_enabled": False,
            "gribi_mtls": None,
            "terminattr_affected": True,
            "terminattr_enabled": False,
            "terminattr_mtls": None,
        }
        arguments.update(overrides)
        return _assess_sa146(**arguments)

    def test_affected_mitigated_and_not_affected(self) -> None:
        affected, affected_message, affected_remediation = self.assess(gnmi_enabled=True, gnmi_mtls=False)
        mitigated, mitigated_message, mitigated_remediation = self.assess(gnmi_enabled=True, gnmi_mtls=True)
        disabled, _, _ = self.assess()

        assert affected is AdvisoryStatus.AFFECTED
        assert "affected" in affected_message
        assert mitigated is AdvisoryStatus.MITIGATED
        assert "mitigated" in mitigated_message
        assert disabled is AdvisoryStatus.NOT_AFFECTED
        assert "4.36.2F or later" in affected_remediation
        assert "4.36.2F or later" in mitigated_remediation
        assert "mTLS" not in mitigated_remediation
        assert "http" not in affected_remediation

    def test_affected_precedes_unknown_sibling_and_mitigated_path(self) -> None:
        affected_with_unknown, _, remediation = self.assess(
            gnmi_enabled=True,
            gnmi_mtls=False,
            gribi_enabled=None,
        )
        affected, affected_message, _ = self.assess(
            gnmi_enabled=True,
            gnmi_mtls=True,
            terminattr_enabled=True,
            terminattr_mtls=False,
        )

        assert affected_with_unknown is AdvisoryStatus.AFFECTED
        assert "4.36.2F or later" in remediation
        assert affected is AdvisoryStatus.AFFECTED
        assert "affected" in affected_message

    def test_fixed_versions_ignore_missing_optional_evidence(self) -> None:
        status, _, _ = self.assess(
            eos_affected=False,
            gnmi_enabled=None,
            gribi_enabled=None,
            terminattr_affected=False,
            terminattr_enabled=None,
        )

        assert status is AdvisoryStatus.NOT_AFFECTED


class TestVerifySA146(unittest.IsolatedAsyncioTestCase):
    """Validate atomic projection and optional-command handling."""

    async def run_test(
        self,
        *,
        gnmi: dict[str, Any] | None = None,
        gribi: dict[str, Any] | None = None,
        terminattr: dict[str, Any] | None = None,
        grpcaddr: str = "",
        profiles: dict[str, Any] | None = None,
        version: dict[str, Any] | None = None,
    ) -> VerifySA146:
        """Run the ANTA test with synthetic outputs in declaration order."""
        device = OfflineAntaDevice("unit-test")
        detail_output = version if version is not None else version_output()
        eos_version = detail_output.get("version")
        device.version = parse_eos_version_or_none(eos_version) if isinstance(eos_version, str) else None
        await device.refresh()
        eos_data = [
            detail_output,
            gnmi if gnmi is not None else gnmi_output(enabled=False),
            gribi if gribi is not None else gribi_output(enabled=False),
            terminattr if terminattr is not None else terminattr_output(enabled=False),
            grpcaddr,
            profiles if profiles is not None else ssl_profiles(),
        ]
        test = cast("Any", VerifySA146)(device=device, eos_data=eos_data)
        await test.test(eos_data=eos_data)
        return test

    async def test_atomic_result_has_vulnerability_association(self) -> None:
        test = await self.run_test(gnmi={})
        assert _get_atomic_vulnerability_ids(test.result.atomic_results[0]) == ("GHSA-hrxh-6v49-42gf",)

    async def test_unsupported_optional_service_is_absent(self) -> None:
        device = OfflineAntaDevice("unit-test")
        device.version = parse_eos_version_or_none("4.35.5M")
        await device.refresh()
        eos_data = [
            version_output(),
            gnmi_output(enabled=False),
            {},
            terminattr_output(enabled=False),
            "",
            ssl_profiles(),
        ]
        test = cast("Any", VerifySA146)(device=device, eos_data=eos_data)
        test.instance_commands[2].output = None
        test.instance_commands[2].errors = ["This command is not supported on this hardware platform"]
        test.collect = AsyncMock()
        await test.test()

        assert test.result.result is AntaTestStatus.SUCCESS

    async def test_configured_terminattr_with_unsupported_daemon_command_is_error(self) -> None:
        device = OfflineAntaDevice("unit-test")
        device.version = parse_eos_version_or_none("4.35.5M")
        await device.refresh()
        eos_data = sa146_eos_data(terminattr={}, grpcaddr=TERMINATTR_GRPC)
        test = cast("Any", VerifySA146)(device=device, eos_data=eos_data)
        test.instance_commands[3].output = None
        test.instance_commands[3].errors = ["This command is not supported on this hardware platform"]
        test.collect = AsyncMock()
        await test.test()

        assert test.result.result is AntaTestStatus.ERROR
        assert "TerminAttr enabled state" in test.result.messages[0]

    async def test_unsupported_required_profile_evidence_is_error(self) -> None:
        device = OfflineAntaDevice("unit-test")
        device.version = parse_eos_version_or_none("4.35.5M")
        await device.refresh()
        eos_data = [
            version_output(),
            gnmi_output(enabled=True, profile="mtls"),
            gribi_output(enabled=False),
            terminattr_output(enabled=False),
            "",
            {},
        ]
        test = cast("Any", VerifySA146)(device=device, eos_data=eos_data)
        test.instance_commands[5].output = None
        test.instance_commands[5].errors = ["This command is not supported on this hardware platform"]
        test.collect = AsyncMock()
        await test.test()

        assert test.result.result is AntaTestStatus.ERROR
