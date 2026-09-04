# Copyright (c) 2026 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Facts derived from EOS management-service state."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import TYPE_CHECKING

from anta._advisory.facts.models import (
    CommandsFactDefinition,
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


@dataclass(frozen=True, slots=True)
class _GnmiConfig:
    """Deserialized gNMI configuration without fact-specific interpretation."""

    service_enabled: bool | None
    transports: tuple[object, ...]


def _deserialize_gnmi_config(gnmi_output: Mapping[str, object]) -> _GnmiConfig | None:
    """Deserialize flattened and nested EOS gNMI output without evaluating it."""
    if "transports" not in gnmi_output:
        service_enabled = gnmi_output.get("enabled")
        if not isinstance(service_enabled, bool):
            return None
        return _GnmiConfig(service_enabled=service_enabled, transports=(gnmi_output,))
    transports = gnmi_output.get("transports")
    if not isinstance(transports, Mapping):
        return None
    service_enabled = gnmi_output.get("enabled")
    if service_enabled is not None and not isinstance(service_enabled, bool):
        return None
    return _GnmiConfig(service_enabled=service_enabled, transports=tuple(transports.values()))


def _feature_source(command: AntaCommand) -> FactSource:
    """Return the source for one command-derived fact."""
    return FactSource(command.command, FactSourceKind.COMMAND)


class GnmiTransportFact(CommandsFactDefinition[FeatureValue]):
    """Effective gNMI transport state."""

    key = "feature.gnmi.transport"
    label = "gNMI transport state"
    commands = (GNMI_COMMAND,)

    @classmethod
    def parse(cls, commands: tuple[AntaCommand, ...]) -> Fact[FeatureValue]:
        (command,) = commands
        source = _feature_source(command)
        if is_unsupported_optional_command(command):
            return cls.available(FeatureValue(FeatureName.GNMI, FeatureState.UNSUPPORTED), source)
        config = _deserialize_gnmi_config(command.json_output)
        if config is None:
            return cls.unavailable(FactProblemKind.MALFORMED, source)
        if config.service_enabled is False and any(isinstance(transport, Mapping) and transport.get("enabled") is True for transport in config.transports):
            return cls.unavailable(FactProblemKind.MALFORMED, source)
        unknown = False
        for transport in config.transports:
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


class GnmiAccountingFact(CommandsFactDefinition[FeatureValue]):
    """Accounting state across enabled gNMI transports."""

    key = "feature.gnmi.accounting"
    label = "gNMI transport accounting state"
    commands = (GNMI_COMMAND,)

    @staticmethod
    def _state(config: _GnmiConfig) -> FeatureState | FactProblemKind:
        """Interpret accounting state from neutral gNMI configuration."""
        if config.service_enabled is False and any(isinstance(transport, Mapping) and transport.get("enabled") is True for transport in config.transports):
            return FactProblemKind.MALFORMED
        unknown = False
        for transport in config.transports:
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
                return FeatureState.ENABLED
            if accounting is not False:
                unknown = True
        return FactProblemKind.MISSING if unknown else FeatureState.DISABLED

    @classmethod
    def parse(cls, commands: tuple[AntaCommand, ...]) -> Fact[FeatureValue]:
        (command,) = commands
        source = _feature_source(command)
        feature = SubFeature(FeatureName.GNMI, "transport accounting")
        if is_unsupported_optional_command(command):
            return cls.available(FeatureValue(feature, FeatureState.UNSUPPORTED), source)
        config = _deserialize_gnmi_config(command.json_output)
        if config is None:
            return cls.unavailable(FactProblemKind.MALFORMED, source)
        state = cls._state(config)
        if isinstance(state, FactProblemKind):
            return cls.unavailable(state, source)
        return cls.available(FeatureValue(feature, state), source)


class RiskyOpenConfigTraceFact(CommandsFactDefinition[ConfigurationValue]):
    """Presence of an advisory-identified OpenConfig trace selector."""

    key = "configuration.openconfig.risky_trace_selector"
    label = "OpenConfig trace selector configuration"
    commands = (TRACE_COMMAND,)

    @classmethod
    def parse(cls, commands: tuple[AntaCommand, ...]) -> Fact[ConfigurationValue]:
        (command,) = commands
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


class GribiTransportFact(CommandsFactDefinition[FeatureValue]):
    """Effective gRIBI service state."""

    key = "feature.gribi.transport"
    label = "gRIBI service state"
    commands = (GRIBI_COMMAND,)

    @classmethod
    def parse(cls, commands: tuple[AntaCommand, ...]) -> Fact[FeatureValue]:
        (command,) = commands
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


class GnmiMtlsFact(CommandsFactDefinition[MitigationValue]):
    """mTLS coverage across enabled gNMI transports."""

    key = "mitigation.gnmi.mtls"
    label = "gNMI mTLS"
    commands = (GNMI_COMMAND, SSL_PROFILE_COMMAND)

    @staticmethod
    def _enabled_transports(config: _GnmiConfig) -> tuple[Mapping[str, object], ...] | None:
        """Select transports whose mTLS coverage this fact must evaluate."""
        transports: list[Mapping[str, object]] = []
        for transport in config.transports:
            if not isinstance(transport, Mapping) or not isinstance((enabled := transport.get("enabled")), bool):
                return None
            if enabled:
                transports.append(transport)
        if (config.service_enabled is False and transports) or not transports:
            return None
        return tuple(transports)

    @classmethod
    def _profile_names(cls, gnmi: AntaCommand) -> Fact[MitigationValue] | tuple[str, ...]:
        """Return configured gNMI SSL profiles or a result decided by gNMI output alone."""
        source = _feature_source(gnmi)
        if is_unsupported_optional_command(gnmi):
            return cls.unavailable(FactProblemKind.UNSUPPORTED, source)
        config = _deserialize_gnmi_config(gnmi.json_output)
        if config is None:
            return cls.unavailable(FactProblemKind.INVALID, source)
        transports = cls._enabled_transports(config)
        if transports is None:
            return cls.unavailable(FactProblemKind.INVALID, source)

        profile_names = tuple(transport.get("sslProfile") for transport in transports)
        if any(profile_name in (None, "") for profile_name in profile_names):
            return cls.available(MitigationValue(MitigationState.INEFFECTIVE), source)
        if any(not isinstance(profile_name, str) for profile_name in profile_names):
            return cls.unavailable(FactProblemKind.MISSING, source)
        return tuple(profile_name for profile_name in profile_names if isinstance(profile_name, str))

    @classmethod
    def _evaluate_profiles(cls, profile_names: tuple[str, ...], ssl: AntaCommand) -> Fact[MitigationValue]:
        """Evaluate configured gNMI profiles using SSL-profile output."""
        source = _feature_source(ssl)
        if is_unsupported_optional_command(ssl):
            return cls.unavailable(FactProblemKind.UNSUPPORTED, source)

        states = tuple(_ssl_profile_has_mtls(profile_name, ssl.json_output) for profile_name in profile_names)
        if False in states:
            return cls.available(MitigationValue(MitigationState.INEFFECTIVE), source)
        if None in states:
            return cls.unavailable(FactProblemKind.MISSING, source)
        return cls.available(MitigationValue(MitigationState.EFFECTIVE), source)

    @classmethod
    def parse(cls, commands: tuple[AntaCommand, ...]) -> Fact[MitigationValue]:
        gnmi, ssl = commands
        profile_names = cls._profile_names(gnmi)
        if not isinstance(profile_names, tuple):
            return profile_names
        return cls._evaluate_profiles(profile_names, ssl)


class GribiMtlsFact(CommandsFactDefinition[MitigationValue]):
    """mTLS state for the gRIBI service."""

    key = "mitigation.gribi.mtls"
    label = "gRIBI mTLS"
    commands = (GRIBI_COMMAND, SSL_PROFILE_COMMAND)

    @classmethod
    def _profile_name(cls, gribi: AntaCommand) -> Fact[MitigationValue] | str:
        """Return the gRIBI SSL profile or a result decided by gRIBI output alone."""
        source = _feature_source(gribi)
        if is_unsupported_optional_command(gribi):
            return cls.unavailable(FactProblemKind.UNSUPPORTED, source)
        enabled = gribi.json_output.get("mTls")
        if not isinstance(enabled, bool):
            return cls.unavailable(FactProblemKind.MISSING, source)
        if not enabled:
            return cls.available(MitigationValue(MitigationState.INEFFECTIVE), source)

        profile_name = gribi.json_output.get("sslProfile")
        if profile_name in (None, ""):
            return cls.available(MitigationValue(MitigationState.INEFFECTIVE), source)
        if not isinstance(profile_name, str):
            return cls.unavailable(FactProblemKind.MISSING, source)
        return profile_name

    @classmethod
    def _evaluate_profile(cls, profile_name: str, ssl: AntaCommand) -> Fact[MitigationValue]:
        """Evaluate the configured gRIBI profile using SSL-profile output."""
        source = _feature_source(ssl)
        if is_unsupported_optional_command(ssl):
            return cls.unavailable(FactProblemKind.UNSUPPORTED, source)
        mtls = _ssl_profile_has_mtls(profile_name, ssl.json_output)
        if mtls is None:
            return cls.unavailable(FactProblemKind.MISSING, source)
        state = MitigationState.EFFECTIVE if mtls else MitigationState.INEFFECTIVE
        return cls.available(MitigationValue(state), source)

    @classmethod
    def parse(cls, commands: tuple[AntaCommand, ...]) -> Fact[MitigationValue]:
        gribi, ssl = commands
        profile_name = cls._profile_name(gribi)
        if not isinstance(profile_name, str):
            return profile_name
        return cls._evaluate_profile(profile_name, ssl)
