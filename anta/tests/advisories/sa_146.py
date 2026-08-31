# Copyright (c) 2026 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""ANTA test for Arista Security Advisory 146."""

from __future__ import annotations

import re
import shlex
from collections.abc import Mapping, Sequence
from typing import TYPE_CHECKING, ClassVar

from anta._advisory.base import _AntaAdvisoryTest
from anta._advisory.eos_versions import AffectedStatus, VersionRule, evaluate_version
from anta._advisory.models import (
    _AdvisoryMetadata,
    _AdvisoryVulnerability,
    _AdvisoryVulnerabilitySeverity,
)
from anta._advisory.optional_commands import (
    OptionalAntaCommand,
    OptionalCommandsMixin,
    is_unsupported_optional_command,
)
from anta._advisory.remediation import (
    FixedRelease,
    evidence_remediation,
    no_remediation,
    upgrade_remediation,
)
from anta._advisory.status import AdvisoryStatus, project_advisory_status
from anta.decorators import preview_test_class
from anta.models import AntaCommand, AntaTemplate

if TYPE_CHECKING:
    from anta._advisory.status import AdvisoryAssessment
    from anta.device import DeviceVersion

EOS_AFFECTED_VERSION_MATRIX: tuple[VersionRule, ...] = (
    VersionRule(major=4, minor=36, patch_lte=1),
    VersionRule(major=4, minor=35, patch_lte=5),
    VersionRule(major=4, minor=34, patch_lt=7),
    VersionRule(major=4, minor=34, patch_eq=7, hotfix_lte=1),
    VersionRule(major=4, minor=33, patch_lte=8),
    VersionRule(major=4, minor_lt=33),
)

EOS_FIXED_RELEASES = (
    FixedRelease("4.36.2F", "4.36"),
    FixedRelease("4.35.6M", "4.35"),
    FixedRelease("4.34.8M", "4.34"),
    FixedRelease("4.33.9M", "4.33"),
)

TERMINATTR_FIXED_RELEASES = (
    FixedRelease("v1.46.0", "v1.46", "TerminAttr"),
    FixedRelease("v1.45.1", "v1.45", "TerminAttr"),
    FixedRelease("v1.43.8", "v1.43", "TerminAttr"),
    FixedRelease("v1.40.13", "v1.40", "TerminAttr"),
    FixedRelease("v1.37.13", "v1.37", "TerminAttr"),
    FixedRelease("v1.34.14", "v1.34", "TerminAttr"),
    FixedRelease("v1.31.17", "v1.31", "TerminAttr"),
)

TERMINATTR_VERSION_PATTERN = re.compile(r"^v(?P<major>\d+)\.(?P<minor>\d+)\.(?P<patch>\d+)$")
TERMINATTR_LAST_AFFECTED_PATCH = {31: 16, 34: 13, 37: 12, 40: 12, 43: 7, 45: 0}
TERMINATTR_FULLY_AFFECTED_MINOR_RANGES = ((0, 30), (32, 33), (35, 36), (38, 39), (41, 42))
TERMINATTR_EXEC_PREFIX = ("exec", "/usr/bin/TerminAttr")

ADVISORY = _AdvisoryMetadata(
    sa_number="0146",
    title="Security Advisory 0146",
    vulnerabilities=(
        _AdvisoryVulnerability(
            id="GHSA-hrxh-6v49-42gf",
            severity=_AdvisoryVulnerabilitySeverity.HIGH,
            description=("HTTP/2 Rapid Reset denial-of-service rate-limit bypass in affected gRPC servers."),
        ),
    ),
    url=("https://www.arista.com/en/support/advisories-notices/security-advisory/24500-security-advisory-0146"),
    description=(
        "Arista Networks is providing this security update in response to the gRPC-Go security "
        "vulnerabilities published as GHSA-hrxh-6v49-42gf. Arista products are affected solely "
        "by the HTTP/2 Rapid Reset denial-of-service bypass, in which an unauthenticated remote "
        "attacker can exploit unthrottled HTTP/2 stream resets to bypass rate-limiting controls, "
        "consume excessive CPU resources, and cause a denial of service."
    ),
)


# Returns distinguish absent, malformed, disabled, and enabled evidence.
def _enabled_gnmi_transports(  # noqa: PLR0911
    gnmi_output: Mapping[str, object],
) -> tuple[Mapping[str, object], ...] | None:
    """Return enabled gNMI transports across observed EOS JSON schema variants."""
    service_enabled = gnmi_output.get("enabled")
    if not isinstance(service_enabled, bool):
        return None

    transports = gnmi_output.get("transports")
    if transports is None:
        # Older releases expose one flattened transport. This shape was observed on EOS
        # 4.35.4M and the top-level enabled flag is authoritative for that transport.
        return (gnmi_output,) if service_enabled else ()
    if not isinstance(transports, Mapping):
        return None

    enabled_transports: list[Mapping[str, object]] = []
    for transport in transports.values():
        if not isinstance(transport, Mapping):
            return None
        enabled = transport.get("enabled")
        if not isinstance(enabled, bool):
            return None
        if enabled:
            enabled_transports.append(transport)

    if not service_enabled and enabled_transports:
        return None
    return tuple(enabled_transports)


def _evaluate_gnmi_grpc_enabled(gnmi_output: Mapping[str, object]) -> bool | None:
    """Return whether at least one gNMI gRPC transport is enabled."""
    transports = _enabled_gnmi_transports(gnmi_output)
    return None if transports is None else bool(transports)


def _evaluate_gribi_grpc_enabled(gribi_output: Mapping[str, object]) -> bool | None:
    """Return whether the gRIBI gRPC service is enabled."""
    enabled = gribi_output.get("enabled")
    return enabled if isinstance(enabled, bool) else None


def _evaluate_terminattr_enabled(terminattr_output: Mapping[str, object]) -> bool | None:
    """Return whether the TerminAttr daemon is administratively enabled."""
    daemons = terminattr_output.get("daemons")
    if not isinstance(daemons, Mapping):
        return None

    daemon = daemons.get("TerminAttr")
    if daemon is None:
        return False
    if not isinstance(daemon, Mapping):
        return None

    enabled = daemon.get("enabled")
    return enabled if isinstance(enabled, bool) else None


def _has_argument(arguments: Sequence[str], name: str) -> bool:
    """Return whether command arguments contain a valued short-form option."""
    option = f"-{name}"
    for index, argument in enumerate(arguments):
        if argument.startswith(f"{option}="):
            return bool(argument.removeprefix(f"{option}="))
        if argument == option:
            return index + 1 < len(arguments) and not arguments[index + 1].startswith("-")
    return False


def _terminattr_grpc_arguments(running_config_output: str) -> tuple[str, ...] | None:
    """Return arguments from the first TerminAttr exec line containing ``-grpcaddr``."""
    for line in running_config_output.splitlines():
        try:
            tokens = shlex.split(line)
        except ValueError:
            continue
        if tuple(tokens[:2]) != TERMINATTR_EXEC_PREFIX:
            continue
        arguments = tuple(tokens[2:])
        if _has_argument(arguments, "grpcaddr"):
            return arguments
    return None


def _has_terminattr_grpcaddr(running_config_output: str) -> bool:
    """Return whether the narrow TerminAttr configuration contains ``-grpcaddr``."""
    return _terminattr_grpc_arguments(running_config_output) is not None


def _extract_terminattr_version(show_version_output: Mapping[str, object]) -> str | None:
    """Extract the Streaming Telemetry Agent version from ``show version detail``."""
    details = show_version_output.get("details")
    if not isinstance(details, Mapping):
        return None
    packages = details.get("packages")
    if not isinstance(packages, Mapping):
        return None
    terminattr = packages.get("TerminAttr-core")
    if not isinstance(terminattr, Mapping):
        return None
    version = terminattr.get("version")
    if not isinstance(version, str) or not version.strip():
        return None
    return version.strip()


def _is_affected_terminattr_version(version_string: str) -> bool | None:
    """Return whether a TerminAttr version is in one documented affected range."""
    match = TERMINATTR_VERSION_PATTERN.fullmatch(version_string.strip())
    if match is None:
        return None

    major = int(match.group("major"))
    minor = int(match.group("minor"))
    patch = int(match.group("patch"))
    if major != 1:
        return major < 1

    if (last_affected_patch := TERMINATTR_LAST_AFFECTED_PATCH.get(minor)) is not None:
        return patch <= last_affected_patch
    return any(first_minor <= minor <= last_minor for first_minor, last_minor in TERMINATTR_FULLY_AFFECTED_MINOR_RANGES)


def _ssl_profile_is_valid(profile: Mapping[str, object]) -> bool:
    """Return whether an SSL profile has valid server identity material."""
    if profile.get("profileState") != "valid" or profile.get("profileError") != []:
        return False
    return all(isinstance(value, str) and value.strip() for value in (profile.get("certName"), profile.get("keyName")))


def _ssl_profile_trust_is_valid(profile: Mapping[str, object]) -> bool | None:
    """Return whether an SSL profile has valid trusted client certificates."""
    trusted_certificates = profile.get("trustedCertificates")
    if not isinstance(trusted_certificates, Sequence) or isinstance(trusted_certificates, str | bytes):
        return None
    if not trusted_certificates:
        return False
    if not all(isinstance(certificate, str) and certificate.strip() for certificate in trusted_certificates):
        return None
    return True


def _ssl_profile_has_mtls(
    profile_name: object,
    ssl_profiles_output: Mapping[str, object],
) -> bool | None:
    """Return whether a named, valid SSL profile enforces mutual TLS."""
    if profile_name is None or profile_name == "":
        return False
    if not isinstance(profile_name, str):
        return None

    profile_status = ssl_profiles_output.get("profileStatus")
    if not isinstance(profile_status, Mapping):
        return None
    profile = profile_status.get(profile_name)
    if not isinstance(profile, Mapping):
        return None

    if not _ssl_profile_is_valid(profile):
        return False
    return _ssl_profile_trust_is_valid(profile)


def _evaluate_gnmi_mtls(
    gnmi_output: Mapping[str, object],
    ssl_profiles_output: Mapping[str, object],
) -> bool | None:
    """Return whether mTLS covers every enabled gNMI transport."""
    transports = _enabled_gnmi_transports(gnmi_output)
    if transports is None or not transports:
        return None

    unknown = False
    for transport in transports:
        profile_mtls = _ssl_profile_has_mtls(transport.get("sslProfile"), ssl_profiles_output)
        if profile_mtls is False:
            return False
        if profile_mtls is None:
            unknown = True
    return None if unknown else True


def _evaluate_gribi_mtls(
    gribi_output: Mapping[str, object],
    ssl_profiles_output: Mapping[str, object],
) -> bool | None:
    """Return whether the enabled gRIBI service enforces mTLS."""
    mtls = gribi_output.get("mTls")
    if not isinstance(mtls, bool):
        return None
    if not mtls:
        return False
    return _ssl_profile_has_mtls(gribi_output.get("sslProfile"), ssl_profiles_output)


def _evaluate_terminattr_mtls(running_config_output: str) -> bool:
    """Return whether the TerminAttr gRPC command contains every documented mTLS flag."""
    arguments = _terminattr_grpc_arguments(running_config_output)
    if arguments is None:
        return False
    required_flags = ("certfile", "keyfile", "clientcafile")
    return all(_has_argument(arguments, flag) for flag in required_flags)


def _optional_json_output(command: AntaCommand) -> tuple[Mapping[str, object], bool]:
    """Return normalized JSON output and whether an optional command is unsupported."""
    unsupported = is_unsupported_optional_command(command)
    return ({} if unsupported else command.json_output), unsupported


def _optional_text_output(command: AntaCommand) -> tuple[str, bool]:
    """Return normalized text output and whether an optional command is unsupported."""
    unsupported = is_unsupported_optional_command(command)
    return ("" if unsupported else command.text_output), unsupported


def _evaluate_terminattr_path(
    version_output: Mapping[str, object],
    terminattr_output: Mapping[str, object],
    config_output: str,
    *,
    terminattr_unsupported: bool,
    config_unsupported: bool,
) -> tuple[bool | None, bool | None, bool | None]:
    """Return TerminAttr version, enabled-state, and mTLS applicability evidence."""
    terminattr_version = _extract_terminattr_version(version_output)
    affected = None if terminattr_version is None else _is_affected_terminattr_version(terminattr_version)
    grpcaddr = None if config_unsupported else _has_terminattr_grpcaddr(config_output)

    if grpcaddr is False:
        enabled = False
    elif terminattr_unsupported:
        # Configured grpcaddr positively establishes the feature, so an unsupported
        # feature command is contradictory rather than feature-absence evidence.
        enabled = None if grpcaddr is True else False
    elif grpcaddr is None:
        enabled = None
    else:
        enabled = _evaluate_terminattr_enabled(terminattr_output)

    mtls = None if enabled is not True else _evaluate_terminattr_mtls(config_output)
    return affected, enabled, mtls


def _evaluate_eos_applicability(
    device_version: DeviceVersion | None,
) -> tuple[bool | None, str | None]:
    """Return affected EOS status and normalized version text."""
    evaluation = evaluate_version(device_version, EOS_AFFECTED_VERSION_MATRIX)
    if evaluation.affected_status is AffectedStatus.UNKNOWN:
        return None, evaluation.version
    return evaluation.affected_status is AffectedStatus.AFFECTED, evaluation.version


def _record_path(
    name: str,
    *,
    enabled: bool | None,
    affected_version: bool | None,
    mtls: bool | None,
    affected_paths: list[str],
    mitigated_paths: list[str],
    errors: list[str],
) -> None:
    """Classify one independent gRPC exposure path into aggregate evidence."""
    if affected_version is False or enabled is False:
        return
    if affected_version is None:
        errors.append(f"{name} software version applicability")
        return
    if enabled is None:
        errors.append(f"{name} enabled state")
        return
    if mtls is None:
        errors.append(f"{name} mTLS state")
        return
    if mtls:
        mitigated_paths.append(name)
    else:
        affected_paths.append(name)


def _assess_sa146(
    *,
    eos_affected: bool | None,
    gnmi_enabled: bool | None,
    gnmi_mtls: bool | None,
    gribi_enabled: bool | None,
    gribi_mtls: bool | None,
    terminattr_affected: bool | None,
    terminattr_enabled: bool | None,
    terminattr_mtls: bool | None,
) -> AdvisoryAssessment:
    """Return the semantic GHSA status, result message, and remediation text."""
    affected_paths: list[str] = []
    mitigated_paths: list[str] = []
    errors: list[str] = []
    _record_path(
        "gNMI",
        enabled=gnmi_enabled,
        affected_version=eos_affected,
        mtls=gnmi_mtls,
        affected_paths=affected_paths,
        mitigated_paths=mitigated_paths,
        errors=errors,
    )
    _record_path(
        "gRIBI",
        enabled=gribi_enabled,
        affected_version=eos_affected,
        mtls=gribi_mtls,
        affected_paths=affected_paths,
        mitigated_paths=mitigated_paths,
        errors=errors,
    )
    _record_path(
        "TerminAttr",
        enabled=terminattr_enabled,
        affected_version=terminattr_affected,
        mtls=terminattr_mtls,
        affected_paths=affected_paths,
        mitigated_paths=mitigated_paths,
        errors=errors,
    )

    if affected_paths:
        releases = (EOS_FIXED_RELEASES if any(path != "TerminAttr" for path in affected_paths) else ()) + (
            TERMINATTR_FIXED_RELEASES if "TerminAttr" in affected_paths else ()
        )
        return (
            AdvisoryStatus.AFFECTED,
            f"The device is affected because vulnerable gRPC server path(s) are enabled without complete mTLS: {', '.join(affected_paths)}.",
            upgrade_remediation(releases),
        )

    if errors:
        return (
            AdvisoryStatus.ERROR,
            f"The following required evidence is unavailable or invalid: {', '.join(errors)}.",
            evidence_remediation(", ".join(errors)),
        )

    if mitigated_paths:
        releases = (EOS_FIXED_RELEASES if any(path != "TerminAttr" for path in mitigated_paths) else ()) + (
            TERMINATTR_FIXED_RELEASES if "TerminAttr" in mitigated_paths else ()
        )
        return (
            AdvisoryStatus.MITIGATED,
            f"The device is affected but mitigated because verified mTLS covers the affected gRPC server path(s): {', '.join(mitigated_paths)}.",
            upgrade_remediation(releases),
        )

    return (
        AdvisoryStatus.NOT_AFFECTED,
        "The device is not affected because no enabled gRPC server is on an affected software version.",
        no_remediation(),
    )


@preview_test_class
class VerifySA146(OptionalCommandsMixin, _AntaAdvisoryTest):
    """Assess the SA146 HTTP/2 Rapid Reset exposure and documented mTLS control.

    Expected Results
    ----------------
    * Success: The test will pass if no affected gRPC service is enabled.
    * Failure: The test will fail if an affected gRPC service is enabled without mTLS.
    * Inconclusive: The test is inconclusive if all affected services are mitigated with mTLS.
    * Error: The test will error if evidence required for an enabled service is invalid.

    Examples
    --------
    ```yaml
    anta.tests.advisories.sa_146:
      - VerifySA146:
    ```
    """

    advisory: ClassVar[_AdvisoryMetadata] = ADVISORY
    commands: ClassVar[list[AntaCommand | AntaTemplate]] = [
        AntaCommand(command="show version detail", revision=1),
        OptionalAntaCommand(command="show management api gnmi", revision=1),
        OptionalAntaCommand(command="show management api gribi", revision=1),
        OptionalAntaCommand(command="show daemon", revision=1),
        OptionalAntaCommand(command="show running-config section grpcaddr", ofmt="text"),
        OptionalAntaCommand(command="show management security ssl profile", revision=1),
    ]
    description = "Verify whether the device is impacted by SA 0146."
    _atomic_support = True

    @_AntaAdvisoryTest.anta_test
    # pylint: disable-next=too-many-locals
    def test(self) -> None:
        """Assess and project GHSA-hrxh-6v49-42gf."""
        version_output = self.instance_commands[0].json_output
        gnmi_command, gribi_command, terminattr_command, config_command, ssl_command = self.instance_commands[1:]

        gnmi_output, gnmi_unsupported = _optional_json_output(gnmi_command)
        gribi_output, gribi_unsupported = _optional_json_output(gribi_command)
        terminattr_output, terminattr_unsupported = _optional_json_output(terminattr_command)
        config_output, config_unsupported = _optional_text_output(config_command)
        ssl_output, _ = _optional_json_output(ssl_command)

        eos_affected, _ = _evaluate_eos_applicability(self.device.version)
        gnmi_enabled = False if gnmi_unsupported else _evaluate_gnmi_grpc_enabled(gnmi_output)
        gribi_enabled = False if gribi_unsupported else _evaluate_gribi_grpc_enabled(gribi_output)
        terminattr_affected, terminattr_enabled, terminattr_mtls = _evaluate_terminattr_path(
            version_output,
            terminattr_output,
            config_output,
            terminattr_unsupported=terminattr_unsupported,
            config_unsupported=config_unsupported,
        )

        status, message, remediation = _assess_sa146(
            eos_affected=eos_affected,
            gnmi_enabled=gnmi_enabled,
            gnmi_mtls=(None if gnmi_enabled is not True else _evaluate_gnmi_mtls(gnmi_output, ssl_output)),
            gribi_enabled=gribi_enabled,
            gribi_mtls=(None if gribi_enabled is not True else _evaluate_gribi_mtls(gribi_output, ssl_output)),
            terminattr_affected=terminattr_affected,
            terminattr_enabled=terminattr_enabled,
            terminattr_mtls=terminattr_mtls,
        )
        vulnerability = ADVISORY.vulnerabilities[0]
        atomic_result = self.result.add(
            f"Verify {vulnerability.id}.",
            vulnerability_ids=(vulnerability.id,),
        )
        project_advisory_status(atomic_result, status, message, remediation)
