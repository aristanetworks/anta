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
from anta._advisory.facts.eos import EosVersionFact
from anta._advisory.facts.management import (
    GnmiMtlsFact,
    GnmiTransportFact,
    GribiMtlsFact,
    GribiTransportFact,
    _deserialize_gnmi_config,
    _GnmiConfig,
    _ssl_profile_has_mtls,
)
from anta._advisory.facts.models import (
    AvailableFact,
    ComponentSoftwareVersion,
    Fact,
    FactProblemKind,
    FactSource,
    FactSourceKind,
    FeatureName,
    FeatureState,
    FeatureValue,
    MitigationState,
    MitigationValue,
    UnavailableFact,
)
from anta._advisory.facts.software import TerminAttrVersionFact
from anta._advisory.facts.terminattr import TerminAttrGrpcFact, TerminAttrMtlsFact, _terminattr_grpc_arguments
from anta._advisory.findings.models import AffectedResult, MitigatedResult, NotAffectedResult, VulnerabilityResult
from anta._advisory.remediation import upgrade_remediation
from anta._advisory.results import _get_atomic_vulnerability_ids
from anta._eos.version import parse_eos_version
from anta.result_manager.models import AntaTestStatus
from anta.tests.advisories.sa_146 import (
    ADVISORY,
    EOS_AFFECTED_VERSION_MATRIX,
    EOS_FIXED_RELEASES,
    TERMINATTR_FIXED_RELEASES,
    VerifySA146,
    _assess_sa146,
    _eos_release_assessment,
    _GrpcPath,
    _is_affected_terminattr_version,
    _terminattr_version_assessment,
)
from tests.units.anta_tests import build_eos_version, test
from tests.units.anta_tests.advisories import OfflineAntaDevice

if TYPE_CHECKING:
    from anta.device import DeviceVersion
    from anta.models import AntaCommand
    from tests.units.anta_tests import AntaUnitTestData, UnitTestResult


SOURCE = FactSource("unit test", FactSourceKind.DEVICE_METADATA)
UNSUPPORTED_ERROR = "Incomplete command (at token 1: 'module')"


def _command(template: AntaCommand, output: dict[str, Any] | str) -> AntaCommand:
    """Populate one fact command for parser tests."""
    command = template.model_copy()
    command.output = output
    return command


def _unsupported_command(template: AntaCommand) -> AntaCommand:
    """Populate one optional fact command with a recognized unsupported error."""
    return template.model_copy(update={"errors": [UNSUPPORTED_ERROR]})


def _feature_bool(fact: Fact[FeatureValue]) -> bool | None:
    """Project a feature fact to the legacy parser truth table."""
    if isinstance(fact, UnavailableFact):
        return None
    return fact.value.state is FeatureState.ENABLED


def _mitigation_bool(fact: Fact[MitigationValue]) -> bool | None:
    """Project a mitigation fact to the legacy parser truth table."""
    if isinstance(fact, UnavailableFact):
        return None
    return fact.value.state is MitigationState.EFFECTIVE


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
    gnmi_output_data = gnmi if gnmi is not None else gnmi_output(enabled=False)
    gribi_output_data = gribi if gribi is not None else gribi_output(enabled=False)
    terminattr_output_data = terminattr if terminattr is not None else terminattr_output(enabled=False)
    ssl_profile_output_data = profiles if profiles is not None else ssl_profiles()
    return [
        version if version is not None else version_output(),
        gnmi_output_data,
        gribi_output_data,
        terminattr_output_data,
        grpcaddr,
        gnmi_output_data,
        ssl_profile_output_data,
        gribi_output_data,
        ssl_profile_output_data,
        grpcaddr,
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
            "The device is affected because EOS version '4.35.5M' is affected and the gNMI feature is enabled.",
            "Upgrade to",
        ),
    },
    (VerifySA146, "failure-gribi-without-mtls"): {
        "version": build_eos_version("4.35.5M"),
        "eos_data": sa146_eos_data(gribi=gribi_output(enabled=True)),
        "expected": expected_result(
            AntaTestStatus.FAILURE,
            "The device is affected because EOS version '4.35.5M' is affected and the gRIBI feature is enabled.",
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
            "The device is affected because TerminAttr 'v1.45.0' is affected and the TerminAttr feature is enabled.",
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
            "The device is affected because EOS version '4.35.5M' is affected, TerminAttr 'v1.45.0' is affected, the gNMI feature is enabled, "
            "and the TerminAttr feature is enabled.",
            upgrade_remediation(EOS_FIXED_RELEASES + TERMINATTR_FIXED_RELEASES),
        ),
    },
    (VerifySA146, "failure-known-path-with-malformed-sibling"): {
        "version": build_eos_version("4.35.5M"),
        "eos_data": sa146_eos_data(gnmi=gnmi_output(enabled=True), gribi={}),
        "expected": expected_result(
            AntaTestStatus.FAILURE,
            "The device is affected because EOS version '4.35.5M' is affected and the gNMI feature is enabled.",
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
            "The device is affected but mitigated because EOS version '4.35.5M' is affected, TerminAttr 'v1.45.0' is affected, "
            "the gNMI feature is enabled and gNMI mTLS is effective, the gRIBI feature is enabled and gRIBI mTLS is effective, "
            "and the TerminAttr feature is enabled and TerminAttr mTLS is effective.",
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
            "The device is affected because TerminAttr 'v1.45.0' is affected and the TerminAttr feature is enabled.",
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
            "The device is not affected because EOS version '4.35.6M' is outside the affected releases, the gRIBI feature is disabled, "
            "and the TerminAttr feature is disabled.",
            "",
        ),
    },
    (VerifySA146, "success-terminattr-not-configured"): {
        "version": build_eos_version("4.35.5M"),
        "eos_data": sa146_eos_data(terminattr={"daemons": {}}),
        "expected": expected_result(
            AntaTestStatus.SUCCESS,
            "The device is not affected because the gNMI feature is disabled, the gRIBI feature is disabled, and the TerminAttr feature is disabled.",
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
            "The device is not affected because EOS version '4.35.6M' is outside the affected releases and the TerminAttr feature is disabled.",
            "",
        ),
    },
    (VerifySA146, "error-malformed-gnmi-enabled-state"): {
        "version": build_eos_version("4.35.5M"),
        "eos_data": sa146_eos_data(gnmi={}),
        "expected": expected_result(
            AntaTestStatus.ERROR,
            "The test could not determine the gNMI transport state because the 'show management api gnmi' output is invalid.",
            "",
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
            "The test could not determine the gNMI mTLS because the 'show management security ssl profile' output is incomplete.",
            "",
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
                assert evaluate_version(parse_eos_version(version), EOS_AFFECTED_VERSION_MATRIX).affected_status is expected


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
    """Validate service, component-version, and complete mTLS evidence."""

    def test_gnmi_deserializer_preserves_fact_neutral_transport_data(self) -> None:
        enabled_transport = {"enabled": True, "accounting": False, "sslProfile": "mtls"}
        output = {"enabled": False, "transports": {"default": enabled_transport, "unparsed": "unexpected"}}

        assert _deserialize_gnmi_config(output) == _GnmiConfig(
            service_enabled=False,
            transports=(enabled_transport, "unexpected"),
        )
        assert _deserialize_gnmi_config({"enabled": True, "port": 6030}) == _GnmiConfig(
            service_enabled=True,
            transports=({"enabled": True, "port": 6030},),
        )
        assert _deserialize_gnmi_config({"enabled": "yes"}) is None
        assert _deserialize_gnmi_config({"transports": []}) is None

    def test_gnmi_transport_schema_variants(self) -> None:
        assert _feature_bool(GnmiTransportFact.parse((_command(GnmiTransportFact.commands[0], gnmi_output(enabled=True)),)))
        assert not _feature_bool(GnmiTransportFact.parse((_command(GnmiTransportFact.commands[0], gnmi_output(enabled=False)),)))
        assert not _feature_bool(GnmiTransportFact.parse((_command(GnmiTransportFact.commands[0], {"enabled": False, "port": 0, "sslProfile": "", "error": ""}),)))
        assert _feature_bool(GnmiTransportFact.parse((_command(GnmiTransportFact.commands[0], {}),))) is None
        contradictory = {"enabled": False, "transports": {"default": {"enabled": True}}}
        assert _feature_bool(GnmiTransportFact.parse((_command(GnmiTransportFact.commands[0], contradictory),))) is None

    def test_gribi_and_terminattr_states(self) -> None:
        assert _feature_bool(GribiTransportFact.parse((_command(GribiTransportFact.commands[0], gribi_output(enabled=True)),)))
        assert not _feature_bool(GribiTransportFact.parse((_command(GribiTransportFact.commands[0], gribi_output(enabled=False)),)))
        assert _feature_bool(GribiTransportFact.parse((_command(GribiTransportFact.commands[0], {"enabled": "true"}),))) is None

        def terminattr_fact(daemon: dict[str, Any]) -> Fact[FeatureValue]:
            return TerminAttrGrpcFact.parse(
                (
                    _command(TerminAttrGrpcFact.commands[0], daemon),
                    _command(TerminAttrGrpcFact.commands[1], TERMINATTR_GRPC),
                )
            )

        assert _feature_bool(terminattr_fact(terminattr_output(enabled=True)))
        assert not _feature_bool(terminattr_fact(terminattr_output(enabled=False)))
        assert not _feature_bool(terminattr_fact({"daemons": {}}))
        assert _feature_bool(terminattr_fact({})) is None

    def test_terminattr_configuration_and_version(self) -> None:
        assert _terminattr_grpc_arguments(TERMINATTR_GRPC) is not None
        assert _terminattr_grpc_arguments("exec /usr/bin/TerminAttr -grpcaddr=0.0.0.0:6042") is not None
        assert _terminattr_grpc_arguments("daemon TerminAttr") is None
        assert _mitigation_bool(TerminAttrMtlsFact.parse((_command(TerminAttrMtlsFact.commands[0], TERMINATTR_MTLS),)))
        assert _mitigation_bool(
            TerminAttrMtlsFact.parse(
                (
                    _command(
                        TerminAttrMtlsFact.commands[0],
                        "exec /usr/bin/TerminAttr -grpcaddr=0.0.0.0:6042 -certfile=target.crt -keyfile=target.key -clientcafile=ca.crt",
                    ),
                )
            )
        )
        assert not _mitigation_bool(
            TerminAttrMtlsFact.parse(
                (
                    _command(
                        TerminAttrMtlsFact.commands[0],
                        "exec /usr/bin/TerminAttr -grpcaddr 0.0.0.0:6042 -certfile -keyfile target.key -clientcafile ca.crt",
                    ),
                )
            )
        )
        assert not _mitigation_bool(TerminAttrMtlsFact.parse((_command(TerminAttrMtlsFact.commands[0], TERMINATTR_GRPC),)))
        unrelated_mtls = TERMINATTR_GRPC + "\ndaemon Other\n   exec /usr/bin/Other -certfile other.crt -keyfile other.key -clientcafile ca.crt"
        assert not _mitigation_bool(TerminAttrMtlsFact.parse((_command(TerminAttrMtlsFact.commands[0], unrelated_mtls),)))
        version_fact = TerminAttrVersionFact.parse((_command(TerminAttrVersionFact.commands[0], version_output()),))
        assert isinstance(version_fact, AvailableFact)
        assert version_fact.value.version == "v1.45.0"
        assert isinstance(TerminAttrVersionFact.parse((_command(TerminAttrVersionFact.commands[0], version_output(terminattr=None)),)), UnavailableFact)

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
        assert not _mitigation_bool(GnmiMtlsFact.parse((_command(GnmiMtlsFact.commands[0], gnmi), _command(GnmiMtlsFact.commands[1], ssl_profiles()))))
        gnmi["transports"]["other"]["sslProfile"] = "mtls"
        assert _mitigation_bool(GnmiMtlsFact.parse((_command(GnmiMtlsFact.commands[0], gnmi), _command(GnmiMtlsFact.commands[1], ssl_profiles()))))

        assert _mitigation_bool(
            GribiMtlsFact.parse(
                (
                    _command(GribiMtlsFact.commands[0], gribi_output(enabled=True, profile="mtls", mtls=True)),
                    _command(GribiMtlsFact.commands[1], ssl_profiles()),
                )
            )
        )
        assert not _mitigation_bool(
            GribiMtlsFact.parse(
                (
                    _command(GribiMtlsFact.commands[0], gribi_output(enabled=True, profile="mtls", mtls=False)),
                    _command(GribiMtlsFact.commands[1], ssl_profiles()),
                )
            )
        )

    def test_mtls_uses_the_decisive_command_as_its_fact_source(self) -> None:
        ssl_unsupported = _unsupported_command(GnmiMtlsFact.commands[1])

        gnmi_without_profile = GnmiMtlsFact.parse(
            (_command(GnmiMtlsFact.commands[0], gnmi_output(enabled=True)), ssl_unsupported),
        )
        assert isinstance(gnmi_without_profile, AvailableFact)
        assert gnmi_without_profile.value.state is MitigationState.INEFFECTIVE
        assert gnmi_without_profile.source.name == GnmiMtlsFact.commands[0].command

        gnmi_requiring_profile = GnmiMtlsFact.parse(
            (_command(GnmiMtlsFact.commands[0], gnmi_output(enabled=True, profile="mtls")), ssl_unsupported),
        )
        assert isinstance(gnmi_requiring_profile, UnavailableFact)
        assert gnmi_requiring_profile.problem is FactProblemKind.UNSUPPORTED
        assert gnmi_requiring_profile.source.name == GnmiMtlsFact.commands[1].command

        gribi_without_mtls = GribiMtlsFact.parse(
            (_command(GribiMtlsFact.commands[0], gribi_output(enabled=True, profile="mtls", mtls=False)), ssl_unsupported),
        )
        assert isinstance(gribi_without_mtls, AvailableFact)
        assert gribi_without_mtls.value.state is MitigationState.INEFFECTIVE
        assert gribi_without_mtls.source.name == GribiMtlsFact.commands[0].command

        gribi_requiring_profile = GribiMtlsFact.parse(
            (_command(GribiMtlsFact.commands[0], gribi_output(enabled=True, profile="mtls", mtls=True)), ssl_unsupported),
        )
        assert isinstance(gribi_requiring_profile, UnavailableFact)
        assert gribi_requiring_profile.problem is FactProblemKind.UNSUPPORTED
        assert gribi_requiring_profile.source.name == GribiMtlsFact.commands[1].command


class TestSA146Assessment(unittest.TestCase):
    """Validate semantic state precedence across independent gRPC paths."""

    def assess(self, **overrides: bool | None) -> VulnerabilityResult:
        """Assess default disabled paths with selected fact overrides."""
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

        def feature(definition: type[GnmiTransportFact | GribiTransportFact | TerminAttrGrpcFact], enabled: bool | None) -> Fact[FeatureValue]:
            if enabled is None:
                return definition.unavailable(FactProblemKind.MALFORMED, SOURCE)
            name = FeatureName.GNMI if definition is GnmiTransportFact else FeatureName.GRIBI if definition is GribiTransportFact else FeatureName.TERMINATTR
            return definition.available(
                FeatureValue(name, FeatureState.ENABLED if enabled else FeatureState.DISABLED),
                SOURCE,
            )

        def mitigation(definition: type[GnmiMtlsFact | GribiMtlsFact | TerminAttrMtlsFact], enabled: bool | None) -> Fact[MitigationValue]:
            if enabled is None:
                return definition.unavailable(FactProblemKind.MISSING, SOURCE)
            return definition.available(
                MitigationValue(definition.label.removesuffix(" state"), MitigationState.EFFECTIVE if enabled else MitigationState.INEFFECTIVE),
                SOURCE,
            )

        eos_version: Fact[DeviceVersion] = (
            EosVersionFact.unavailable(FactProblemKind.MISSING, SOURCE)
            if arguments["eos_affected"] is None
            else EosVersionFact.available(
                cast("DeviceVersion", parse_eos_version("4.35.5M" if arguments["eos_affected"] else "4.35.6M")),
                SOURCE,
            )
        )
        terminattr_version = (
            TerminAttrVersionFact.unavailable(FactProblemKind.MISSING, SOURCE)
            if arguments["terminattr_affected"] is None
            else TerminAttrVersionFact.available(
                ComponentSoftwareVersion("TerminAttr", "v1.45.0" if arguments["terminattr_affected"] else "v1.45.1"),
                SOURCE,
            )
        )
        return _assess_sa146(
            (
                _GrpcPath(
                    _eos_release_assessment(eos_version),
                    feature(GnmiTransportFact, arguments["gnmi_enabled"]),
                    mitigation(GnmiMtlsFact, arguments["gnmi_mtls"]),
                    EOS_FIXED_RELEASES,
                ),
                _GrpcPath(
                    _eos_release_assessment(eos_version),
                    feature(GribiTransportFact, arguments["gribi_enabled"]),
                    mitigation(GribiMtlsFact, arguments["gribi_mtls"]),
                    EOS_FIXED_RELEASES,
                ),
                _GrpcPath(
                    _terminattr_version_assessment(terminattr_version),
                    feature(TerminAttrGrpcFact, arguments["terminattr_enabled"]),
                    mitigation(TerminAttrMtlsFact, arguments["terminattr_mtls"]),
                    TERMINATTR_FIXED_RELEASES,
                ),
            )
        )

    def test_affected_mitigated_and_not_affected(self) -> None:
        affected = self.assess(gnmi_enabled=True, gnmi_mtls=False)
        mitigated = self.assess(gnmi_enabled=True, gnmi_mtls=True)
        disabled = self.assess()

        assert isinstance(affected, AffectedResult)
        assert isinstance(mitigated, MitigatedResult)
        assert isinstance(disabled, NotAffectedResult)
        assert "4.36.2F or later" in affected.remediation
        assert "4.36.2F or later" in mitigated.remediation
        assert "mTLS" not in mitigated.remediation
        assert "http" not in affected.remediation

    def test_affected_precedes_unknown_sibling_and_mitigated_path(self) -> None:
        affected_with_unknown = self.assess(
            gnmi_enabled=True,
            gnmi_mtls=False,
            gribi_enabled=None,
        )
        affected = self.assess(
            gnmi_enabled=True,
            gnmi_mtls=True,
            terminattr_enabled=True,
            terminattr_mtls=False,
        )

        assert isinstance(affected_with_unknown, AffectedResult)
        assert "4.36.2F or later" in affected_with_unknown.remediation
        assert isinstance(affected, AffectedResult)

    def test_fixed_versions_ignore_missing_optional_evidence(self) -> None:
        finding = self.assess(
            eos_affected=False,
            gnmi_enabled=None,
            gribi_enabled=None,
            terminattr_affected=False,
            terminattr_enabled=None,
        )

        assert isinstance(finding, NotAffectedResult)


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
        device.version = parse_eos_version(eos_version) if isinstance(eos_version, str) else None
        await device.refresh()
        eos_data = sa146_eos_data(gnmi=gnmi, gribi=gribi, terminattr=terminattr, grpcaddr=grpcaddr, profiles=profiles, version=detail_output)
        test = cast("Any", VerifySA146)(device=device, eos_data=eos_data)
        await test.test(eos_data=eos_data)
        return test

    async def test_atomic_result_has_vulnerability_association(self) -> None:
        test = await self.run_test(gnmi={})
        assert _get_atomic_vulnerability_ids(test.result.atomic_results[0]) == ("GHSA-hrxh-6v49-42gf",)

    async def test_unsupported_optional_service_is_absent(self) -> None:
        device = OfflineAntaDevice("unit-test")
        device.version = parse_eos_version("4.35.5M")
        await device.refresh()
        eos_data = sa146_eos_data(gribi={})
        test = cast("Any", VerifySA146)(device=device, eos_data=eos_data)
        test.instance_commands[2].output = None
        test.instance_commands[2].errors = ["This command is not supported on this hardware platform"]
        test.collect = AsyncMock()
        await test.test()

        assert test.result.result is AntaTestStatus.SUCCESS

    async def test_configured_terminattr_with_unsupported_daemon_command_is_error(self) -> None:
        device = OfflineAntaDevice("unit-test")
        device.version = parse_eos_version("4.35.5M")
        await device.refresh()
        eos_data = sa146_eos_data(terminattr={}, grpcaddr=TERMINATTR_GRPC)
        test = cast("Any", VerifySA146)(device=device, eos_data=eos_data)
        test.instance_commands[3].output = None
        test.instance_commands[3].errors = ["This command is not supported on this hardware platform"]
        test.collect = AsyncMock()
        await test.test()

        assert test.result.result is AntaTestStatus.ERROR
        assert "TerminAttr gRPC server state" in test.result.messages[0]

    async def test_unsupported_required_profile_evidence_is_error(self) -> None:
        device = OfflineAntaDevice("unit-test")
        device.version = parse_eos_version("4.35.5M")
        await device.refresh()
        eos_data = sa146_eos_data(gnmi=gnmi_output(enabled=True, profile="mtls"), profiles={})
        test = cast("Any", VerifySA146)(device=device, eos_data=eos_data)
        test.instance_commands[6].output = None
        test.instance_commands[6].errors = ["This command is not supported on this hardware platform"]
        test.collect = AsyncMock()
        await test.test()

        assert test.result.result is AntaTestStatus.ERROR
