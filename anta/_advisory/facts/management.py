# Copyright (c) 2026 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Facts derived from EOS management-service state."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import TYPE_CHECKING

from anta._advisory.facts.models import (
    CommandFactDefinition,
    ConfigurationState,
    ConfigurationValue,
    Fact,
    FactProblemKind,
    FactSource,
    FactSourceKind,
    FeatureName,
    FeatureState,
    FeatureValue,
    MitigationState,
    MitigationValue,
    MultiCommandFactDefinition,
    SubFeature,
)
from anta._advisory.optional_commands import OptionalAntaCommand, is_unsupported_optional_command

if TYPE_CHECKING:
    from anta.models import AntaCommand

RISKY_TRACE_SELECTORS = ("service/9", "interceptor/9", "transport_socketcli/9")
GNMI_COMMAND = OptionalAntaCommand(command="show management api gnmi", revision=1)
GRIBI_COMMAND = OptionalAntaCommand(command="show management api gribi", revision=1)
TRACE_COMMAND = OptionalAntaCommand(command="show running-config section trace", ofmt="text")
SSL_PROFILE_COMMAND = OptionalAntaCommand(command="show management security ssl profile", revision=1)


def _enabled_gnmi_transports(gnmi_output: Mapping[str, object]) -> tuple[Mapping[str, object], ...] | None:
    """Return enabled gNMI transports across observed EOS schemas."""
    transports = gnmi_output.get("transports")
    service_enabled = gnmi_output.get("enabled")
    if transports is None:
        if not isinstance(service_enabled, bool):
            return None
        return (gnmi_output,) if service_enabled else ()
    if not isinstance(transports, Mapping) or (service_enabled is not None and not isinstance(service_enabled, bool)):
        return None

    enabled_transports: list[Mapping[str, object]] = []
    for transport in transports.values():
        if not isinstance(transport, Mapping) or not isinstance((enabled := transport.get("enabled")), bool):
            return None
        if enabled:
            enabled_transports.append(transport)
    if service_enabled is False and enabled_transports:
        return None
    return tuple(enabled_transports)


def _gnmi_transport_values(gnmi_output: Mapping[str, object]) -> tuple[object, ...] | None:
    """Return transport values from nested or flattened EOS gNMI output."""
    if "transports" not in gnmi_output:
        enabled = gnmi_output.get("enabled")
        if not isinstance(enabled, bool):
            return None
        return (gnmi_output,) if enabled else ()
    transports = gnmi_output.get("transports")
    if not isinstance(transports, Mapping):
        return None
    service_enabled = gnmi_output.get("enabled")
    if service_enabled is not None and not isinstance(service_enabled, bool):
        return None
    values = tuple(transports.values())
    if service_enabled is False and any(isinstance(transport, Mapping) and transport.get("enabled") is True for transport in values):
        return None
    return values


def _feature_source(command: AntaCommand) -> FactSource:
    """Return the source for one command-derived fact."""
    return FactSource(command.command, FactSourceKind.COMMAND)


class GnmiTransportFact(CommandFactDefinition[FeatureValue]):
    """Effective gNMI transport state."""

    key = "feature.gnmi.transport"
    label = "gNMI transport state"
    command = GNMI_COMMAND

    @classmethod
    def parse(cls, command: AntaCommand) -> Fact[FeatureValue]:
        source = _feature_source(command)
        if is_unsupported_optional_command(command):
            return cls.available(FeatureValue(FeatureName.GNMI, FeatureState.UNSUPPORTED), source)
        transports = _gnmi_transport_values(command.json_output)
        if transports is None:
            return cls.unavailable(FactProblemKind.MALFORMED, source)
        unknown = False
        for transport in transports:
            if not isinstance(transport, Mapping):
                unknown = True
                continue
            enabled = transport.get("enabled")
            if enabled is True:
                return cls.available(FeatureValue(FeatureName.GNMI, FeatureState.ENABLED), source)
            if enabled is not False:
                unknown = True
        if unknown:
            return cls.unavailable(FactProblemKind.MALFORMED, source)
        state = FeatureState.DISABLED
        return cls.available(FeatureValue(FeatureName.GNMI, state), source)


class GnmiAccountingFact(CommandFactDefinition[FeatureValue]):
    """Accounting state across enabled gNMI transports."""

    key = "feature.gnmi.accounting"
    label = "gNMI transport accounting state"
    command = GNMI_COMMAND

    @classmethod
    def parse(cls, command: AntaCommand) -> Fact[FeatureValue]:
        source = _feature_source(command)
        feature = SubFeature(FeatureName.GNMI, "transport accounting")
        if is_unsupported_optional_command(command):
            return cls.available(FeatureValue(feature, FeatureState.UNSUPPORTED), source)
        transports = _gnmi_transport_values(command.json_output)
        if transports is None:
            return cls.unavailable(FactProblemKind.MALFORMED, source)
        unknown = False
        for transport in transports:
            if not isinstance(transport, Mapping):
                unknown = True
                continue
            enabled = transport.get("enabled")
            if enabled is False:
                continue
            if enabled is not True:
                unknown = True
                continue
            accounting = transport.get("accounting")
            if accounting is True:
                return cls.available(FeatureValue(feature, FeatureState.ENABLED), source)
            if accounting is not False:
                unknown = True
        if unknown:
            return cls.unavailable(FactProblemKind.MISSING, source)
        return cls.available(FeatureValue(feature, FeatureState.DISABLED), source)


class RiskyOpenConfigTraceFact(CommandFactDefinition[ConfigurationValue]):
    """Presence of an advisory-identified OpenConfig trace selector."""

    key = "configuration.openconfig.risky_trace_selector"
    label = "OpenConfig trace selector configuration"
    command = TRACE_COMMAND

    @classmethod
    def parse(cls, command: AntaCommand) -> Fact[ConfigurationValue]:
        source = _feature_source(command)
        if is_unsupported_optional_command(command):
            return cls.unavailable(FactProblemKind.UNSUPPORTED, source)
        prefix = "trace OpenConfig setting "
        configured = False
        for line in command.text_output.splitlines():
            candidate = line.lstrip()
            if candidate.startswith(prefix):
                selectors = {selector.strip() for selector in candidate.removeprefix(prefix).split(",")}
                configured = any(selector in selectors for selector in RISKY_TRACE_SELECTORS)
                if configured:
                    break
        feature = SubFeature(FeatureName.TRACE, "advisory-identified selector")
        state = ConfigurationState.CONFIGURED if configured else ConfigurationState.NOT_CONFIGURED
        return cls.available(ConfigurationValue(feature, state), source)


class GribiTransportFact(CommandFactDefinition[FeatureValue]):
    """Effective gRIBI service state."""

    key = "feature.gribi.transport"
    label = "gRIBI service state"
    command = GRIBI_COMMAND

    @classmethod
    def parse(cls, command: AntaCommand) -> Fact[FeatureValue]:
        source = _feature_source(command)
        if is_unsupported_optional_command(command):
            return cls.available(FeatureValue(FeatureName.GRIBI, FeatureState.UNSUPPORTED), source)
        enabled = command.json_output.get("enabled")
        if not isinstance(enabled, bool):
            return cls.unavailable(FactProblemKind.MALFORMED, source)
        return cls.available(FeatureValue(FeatureName.GRIBI, FeatureState.ENABLED if enabled else FeatureState.DISABLED), source)


def _ssl_profile_is_valid(profile: Mapping[str, object]) -> bool:
    """Return whether an SSL profile has valid server identity material."""
    if profile.get("profileState") != "valid" or profile.get("profileError") != []:
        return False
    return all(isinstance(value, str) and value.strip() for value in (profile.get("certName"), profile.get("keyName")))


def _ssl_profile_trust_is_valid(profile: Mapping[str, object]) -> bool | None:
    """Return whether an SSL profile has valid trusted client certificates."""
    trusted = profile.get("trustedCertificates")
    if not isinstance(trusted, Sequence) or isinstance(trusted, str | bytes):
        return None
    if not trusted:
        return False
    return True if all(isinstance(certificate, str) and certificate.strip() for certificate in trusted) else None


def _ssl_profile_has_mtls(profile_name: object, ssl_output: Mapping[str, object]) -> bool | None:
    """Return whether a named, valid SSL profile enforces mutual TLS."""
    if profile_name in (None, ""):
        return False
    if not isinstance(profile_name, str):
        return None
    profiles = ssl_output.get("profileStatus")
    if not isinstance(profiles, Mapping) or not isinstance((profile := profiles.get(profile_name)), Mapping):
        return None
    if not _ssl_profile_is_valid(profile):
        return False
    return _ssl_profile_trust_is_valid(profile)


class GnmiMtlsFact(MultiCommandFactDefinition[MitigationValue]):
    """mTLS coverage across enabled gNMI transports."""

    key = "mitigation.gnmi.mtls"
    label = "gNMI mTLS"
    commands = (GNMI_COMMAND, SSL_PROFILE_COMMAND)

    @classmethod
    def parse(cls, commands: tuple[AntaCommand, ...]) -> Fact[MitigationValue]:
        gnmi, ssl = commands
        source = FactSource("show management api gnmi and show management security ssl profile", FactSourceKind.COMMAND)
        if is_unsupported_optional_command(gnmi) or is_unsupported_optional_command(ssl):
            return cls.unavailable(FactProblemKind.UNSUPPORTED, source)
        transports = _enabled_gnmi_transports(gnmi.json_output)
        if transports is None or not transports:
            return cls.unavailable(FactProblemKind.INVALID, source)
        unknown = False
        for transport in transports:
            mtls = _ssl_profile_has_mtls(transport.get("sslProfile"), ssl.json_output)
            if mtls is False:
                return cls.available(MitigationValue("gNMI mTLS", MitigationState.INEFFECTIVE), source)
            if mtls is None:
                unknown = True
        if unknown:
            return cls.unavailable(FactProblemKind.MISSING, source)
        return cls.available(MitigationValue("gNMI mTLS", MitigationState.EFFECTIVE), source)


class GribiMtlsFact(MultiCommandFactDefinition[MitigationValue]):
    """mTLS state for the gRIBI service."""

    key = "mitigation.gribi.mtls"
    label = "gRIBI mTLS"
    commands = (GRIBI_COMMAND, SSL_PROFILE_COMMAND)

    @classmethod
    def parse(cls, commands: tuple[AntaCommand, ...]) -> Fact[MitigationValue]:
        gribi, ssl = commands
        source = FactSource("show management api gribi and show management security ssl profile", FactSourceKind.COMMAND)
        if is_unsupported_optional_command(gribi) or is_unsupported_optional_command(ssl):
            return cls.unavailable(FactProblemKind.UNSUPPORTED, source)
        enabled = gribi.json_output.get("mTls")
        if not isinstance(enabled, bool):
            return cls.unavailable(FactProblemKind.MISSING, source)
        mtls = False if not enabled else _ssl_profile_has_mtls(gribi.json_output.get("sslProfile"), ssl.json_output)
        if mtls is None:
            return cls.unavailable(FactProblemKind.MISSING, source)
        state = MitigationState.EFFECTIVE if mtls else MitigationState.INEFFECTIVE
        return cls.available(MitigationValue("gRIBI mTLS", state), source)
