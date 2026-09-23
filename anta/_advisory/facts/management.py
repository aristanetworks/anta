# Copyright (c) 2026 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Facts derived from EOS management-service state."""

from __future__ import annotations

import json
import re
import shlex
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, ClassVar, TypeVar

from anta._advisory.facts.models import (
    CommandsFactDefinition,
    ConfigurationFact,
    ConfigurationState,
    CredentialSyntaxFact,
    CredentialSyntaxState,
    Fact,
    FactDefinition,
    FactProblemKind,
    FactSource,
    FactSourceKind,
    FeatureFact,
    FeatureName,
    FeatureRef,
    FeatureState,
    MitigationFact,
    MitigationState,
    SubFeature,
    UnavailableFact,
)
from anta._advisory.optional_commands import OptionalAntaCommand, is_unsupported_optional_command
from anta._eos.parsing import ParseFail, ParseFailureReason, ParseResult, ParseSuccessful
from anta._eos.version import EOSVersion, parse_eos_version
from anta.models import AntaCommand

if TYPE_CHECKING:
    from anta.device import AntaDevice

RISKY_TRACE_SELECTORS = ("service/9", "interceptor/9", "transport_socketcli/9")
GNMI_COMMAND = OptionalAntaCommand(command="show management api gnmi", revision=1)
DOT1X_COMMAND = OptionalAntaCommand(command="show dot1x all", revision=1)
RADIUS_PROXY_CONFIG_COMMAND = AntaCommand(command="show running-config section radius proxy", ofmt="text")
GNSI_COMMAND = OptionalAntaCommand(command="show management api gnsi", revision=1)
GNPSI_COMMAND = OptionalAntaCommand(command="show management api gnpsi", revision=1)
GNPSI_TRACE_COMMAND = OptionalAntaCommand(command="show trace Gnpsi | grep Auth", ofmt="text", defer_errors=True)
MIN_ENABLED_GNSI_TRANSPORTS = 2
MIN_GNSI_ACCTZ_PATHZ_VERSION = EOSVersion(4, 33, 2)
FeatureFactT = TypeVar("FeatureFactT", bound=FactDefinition[Any])
PATHZ_POLICY_COMMAND = OptionalAntaCommand(
    command="bash timeout 10 sh -c 'if test -f /persist/sys/gnsi/pathz/policy.json; then cat /persist/sys/gnsi/pathz/policy.json; else echo null; fi'",
    ofmt="text",
)
GRIBI_COMMAND = OptionalAntaCommand(command="show management api gribi", revision=1)
TRACE_COMMAND = OptionalAntaCommand(command="show running-config section trace", ofmt="text")
RESTCONF_COMMAND = OptionalAntaCommand(command="show management api restconf", revision=1)
NETCONF_COMMAND = OptionalAntaCommand(command="show management api netconf", revision=1)
SSL_PROFILE_COMMAND = OptionalAntaCommand(command="show management security ssl profile", revision=1)
SNMP_COMMAND = AntaCommand(command="show snmp", revision=1)
SNMPV3_USER_COMMAND = OptionalAntaCommand(command="show snmp user", revision=1)
SNMPV3_USER_CONFIG_COMMAND = AntaCommand(command="show running-config | include ^snmp-server user", ofmt="text")


@dataclass(frozen=True, slots=True)
class _GnmiConfig:
    """Deserialized gNMI configuration without fact-specific interpretation."""

    service_enabled: bool | None
    transports: tuple[object, ...]


@dataclass(frozen=True, slots=True)
class _GnpsiTransport:
    """Deserialized gNPSI transport fields without fact-specific interpretation."""

    enabled: object
    security_type: object
    authentication_methods: object


@dataclass(frozen=True, slots=True)
class _GnpsiConfig:
    """Deserialized gNPSI service and transport state."""

    enabled: object
    transports: tuple[_GnpsiTransport, ...]


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


def _deserialize_gnpsi_config(output: Mapping[str, object]) -> _GnpsiConfig | FactProblemKind:
    """Deserialize the structured gNPSI service output without evaluating exposure."""
    if "enabled" not in output or "transports" not in output:
        return FactProblemKind.MISSING
    transports = output["transports"]
    if not isinstance(transports, Mapping):
        return FactProblemKind.MALFORMED

    parsed: list[_GnpsiTransport] = []
    for transport in transports.values():
        if not isinstance(transport, Mapping):
            return FactProblemKind.MALFORMED
        parsed.append(
            _GnpsiTransport(
                enabled=transport.get("enabled"),
                security_type=transport.get("securityType"),
                authentication_methods=transport.get("authnUsernamePriority"),
            )
        )
    return _GnpsiConfig(enabled=output["enabled"], transports=tuple(parsed))


def _gnpsi_security_type(value: str) -> str:
    """Normalize an EOS gNPSI security-type token for comparison."""
    return re.sub(r"[^a-z]", "", value.casefold())


def _gnpsi_authentication(transport: _GnpsiTransport) -> tuple[str, frozenset[str]] | FactProblemKind:
    """Return validated security and authentication fields for one enabled transport."""
    if transport.security_type is None or transport.authentication_methods is None:
        return FactProblemKind.MISSING
    if not isinstance(transport.security_type, str) or (
        not isinstance(transport.authentication_methods, Sequence)
        or isinstance(transport.authentication_methods, (str, bytes))
        or not all(isinstance(method, str) for method in transport.authentication_methods)
    ):
        return FactProblemKind.MALFORMED
    security_type = _gnpsi_security_type(transport.security_type)
    if security_type not in {"tls", "mtls", "mutualtls", "tlsmutual"}:
        return FactProblemKind.MALFORMED
    return security_type, frozenset(method for method in transport.authentication_methods if isinstance(method, str))


def _feature_source(command: AntaCommand) -> FactSource:
    """Return the source for one command-derived fact."""
    return FactSource(command.command, FactSourceKind.COMMAND)


def _version_aware_gnsi_service_absence(
    device: AntaDevice,
    commands: tuple[AntaCommand, ...],
    fact: Fact[FeatureFactT],
    field: str,
    unsupported: FeatureFactT,
) -> Fact[FeatureFactT]:
    """Interpret a missing Acctz or Pathz field using the EOS schema boundary."""
    if (
        not isinstance(fact, UnavailableFact)
        or fact.problem is not FactProblemKind.MISSING
        or len(commands) != 1
        or commands[0].errors
        or field in commands[0].json_output
    ):
        return fact

    device_version = device.version
    version = device_version if isinstance(device_version, EOSVersion) else parse_eos_version(str(device_version)).unwrap_or_none()
    if version is None:
        return fact
    if version < MIN_GNSI_ACCTZ_PATHZ_VERSION:
        return unsupported.available(fact.source)
    return fact


_SNMPV3_CREDENTIAL_CLAUSES = frozenset({"auth", "priv"})
_SNMPV3_LOCAL_VERSION_INDEX = 4
_SNMPV3_REMOTE_VERSION_INDEX = 6


def _snmpv3_credential_clause_states(
    tokens: tuple[str, ...],
    observed_clauses: frozenset[str],
) -> tuple[CredentialSyntaxState, ...] | None:
    """Return the credential syntax states in one normalized SNMPv3 user line."""
    states: list[CredentialSyntaxState] = []
    index = 0
    while index < len(tokens):
        clause = tokens[index]
        if clause not in _SNMPV3_CREDENTIAL_CLAUSES:
            index += 1
            continue
        if index + 2 >= len(tokens) or tokens[index + 1] in {"auth", "priv", "key"}:
            return None
        value_index = index + 2
        if tokens[value_index] == "key":
            if index + 4 >= len(tokens) or tokens[index + 3] != "7" or tokens[index + 4] in {"auth", "priv", "key"}:
                return None
            if clause in observed_clauses:
                states.append(CredentialSyntaxState.ENCRYPTED)
            index += 5
            continue
        if tokens[value_index] in {"auth", "priv"}:
            return None
        if clause in observed_clauses:
            states.append(CredentialSyntaxState.LEGACY)
        index += 3
    return tuple(states)


def _snmpv3_credential_syntax(
    config_output: str,
    observed_clauses: frozenset[str] = _SNMPV3_CREDENTIAL_CLAUSES,
) -> CredentialSyntaxState | None:
    """Normalize local and remote SNMPv3 user credentials without retaining their values."""
    observed: set[CredentialSyntaxState] = set()
    for line in config_output.splitlines():
        if not line.strip():
            continue
        try:
            tokens = tuple(shlex.split(line))
        except ValueError:
            return None
        if tuple(tokens[:2]) != ("snmp-server", "user"):
            return None
        version_index = (
            _SNMPV3_REMOTE_VERSION_INDEX
            if len(tokens) > _SNMPV3_LOCAL_VERSION_INDEX and tokens[_SNMPV3_LOCAL_VERSION_INDEX] == "remote"
            else _SNMPV3_LOCAL_VERSION_INDEX
        )
        if len(tokens) <= version_index or tokens[version_index] != "v3":
            continue
        states = _snmpv3_credential_clause_states(tokens[version_index + 1 :], observed_clauses)
        if states is None:
            return None
        observed.update(states)

    return _classify_snmpv3_credential_syntax(observed)


def _classify_snmpv3_credential_syntax(observed: set[CredentialSyntaxState]) -> CredentialSyntaxState:
    """Collapse observed credential clauses into one normalized syntax state."""
    if not observed:
        return CredentialSyntaxState.NOT_CONFIGURED
    if observed == {CredentialSyntaxState.ENCRYPTED}:
        return CredentialSyntaxState.ENCRYPTED
    if observed == {CredentialSyntaxState.LEGACY}:
        return CredentialSyntaxState.LEGACY
    return CredentialSyntaxState.MIXED


def _parse_dot1x_controlled_authenticator(output: Mapping[str, object]) -> ParseResult[bool]:  # noqa: PLR0911
    """Parse whether system control and a controlled authenticator interface are present."""
    system_control = output.get("systemAuthControl")
    interfaces = output.get("interfaces")
    if not isinstance(system_control, bool):
        return ParseFail(ParseFailureReason.MALFORMED, "show dot1x all systemAuthControl is not a boolean")
    if not isinstance(interfaces, Mapping):
        return ParseFail(ParseFailureReason.MALFORMED, "show dot1x all interfaces is not a mapping")
    if not system_control:
        return ParseSuccessful(value=False)
    for name, interface in interfaces.items():
        if not isinstance(interface, Mapping):
            return ParseFail(ParseFailureReason.MALFORMED, f"show dot1x all interface {name!r} is not a mapping")
        port_control = interface.get("portControl")
        if not isinstance(port_control, str):
            return ParseFail(ParseFailureReason.MALFORMED, f"show dot1x all interface {name!r} portControl is not a string")
        if port_control == "controlled":
            return ParseSuccessful(value=True)
    return ParseSuccessful(value=False)


@dataclass(frozen=True, slots=True)
class Dot1xControlledAuthenticatorFact(FeatureFact, CommandsFactDefinition["Dot1xControlledAuthenticatorFact"]):
    """Effective 802.1X authenticator with controlled port state."""

    feature: ClassVar[FeatureRef] = SubFeature(FeatureName.DOT1X, "controlled authenticator")
    key: ClassVar[str] = "feature.dot1x.controlled_authenticator"
    label: ClassVar[str] = "802.1X controlled authenticator state"
    commands: ClassVar[tuple[AntaCommand, ...]] = (DOT1X_COMMAND,)

    @classmethod
    def parse(cls, commands: tuple[AntaCommand, ...]) -> Fact[Dot1xControlledAuthenticatorFact]:
        """Normalize system control and effective interface port-control state."""
        (command,) = commands
        source = _feature_source(command)
        if is_unsupported_optional_command(command):
            return cls(FeatureState.UNSUPPORTED).available(source)
        parsed = _parse_dot1x_controlled_authenticator(command.json_output)
        if isinstance(parsed, ParseFail):
            return cls.unavailable(FactProblemKind(parsed.reason.value), source)
        state = FeatureState.ENABLED if parsed.value else FeatureState.DISABLED
        return cls(state).available(source)


@dataclass(frozen=True, slots=True)
class Dot1xDynamicAuthorizationFact(FeatureFact, CommandsFactDefinition["Dot1xDynamicAuthorizationFact"]):
    """Effective 802.1X dynamic authorization with an authenticator interface."""

    feature: ClassVar[FeatureRef] = SubFeature(FeatureName.DOT1X, "dynamic authorization authenticator")
    key: ClassVar[str] = "feature.dot1x.dynamic_authorization"
    label: ClassVar[str] = "802.1X dynamic-authorization state"
    commands: ClassVar[tuple[AntaCommand, ...]] = (DOT1X_COMMAND,)

    @classmethod
    def parse(cls, commands: tuple[AntaCommand, ...]) -> Fact[Dot1xDynamicAuthorizationFact]:
        """Normalize the structured global and interface prerequisites."""
        (command,) = commands
        source = _feature_source(command)
        if is_unsupported_optional_command(command):
            return cls(FeatureState.UNSUPPORTED).available(source)
        dynamic_authorization = command.json_output.get("dynAuth")
        if not isinstance(dynamic_authorization, bool):
            return cls.unavailable(FactProblemKind.MALFORMED, source)
        if not dynamic_authorization:
            return cls(FeatureState.DISABLED).available(source)
        parsed = _parse_dot1x_controlled_authenticator(command.json_output)
        if isinstance(parsed, ParseFail):
            return cls.unavailable(FactProblemKind(parsed.reason.value), source)
        state = FeatureState.ENABLED if parsed.value else FeatureState.DISABLED
        return cls(state).available(source)


@dataclass(frozen=True, slots=True)
class RadiusProxyDynamicAuthorizationFact(FeatureFact, CommandsFactDefinition["RadiusProxyDynamicAuthorizationFact"]):
    """Configured RADIUS proxy dynamic authorization with a client group."""

    feature: ClassVar[FeatureRef] = SubFeature(FeatureName.RADIUS_PROXY, "dynamic authorization client group")
    key: ClassVar[str] = "feature.radius_proxy.dynamic_authorization"
    label: ClassVar[str] = "RADIUS proxy dynamic-authorization state"
    commands: ClassVar[tuple[AntaCommand, ...]] = (RADIUS_PROXY_CONFIG_COMMAND,)

    @classmethod
    def parse(cls, commands: tuple[AntaCommand, ...]) -> Fact[RadiusProxyDynamicAuthorizationFact]:
        """Normalize the complete source-defined RADIUS proxy prerequisite."""
        (command,) = commands
        lines = tuple(line.strip() for line in command.text_output.splitlines() if line.strip() and line.strip() != "!")
        configured = "radius proxy" in lines and "dynamic-authorization" in lines and any(line.startswith("client group ") for line in lines)
        state = FeatureState.ENABLED if configured else FeatureState.DISABLED
        return cls(state).available(_feature_source(command))


@dataclass(frozen=True, slots=True)
class SnmpAgentFact(FeatureFact, CommandsFactDefinition["SnmpAgentFact"]):
    """Effective SNMP agent state."""

    feature: ClassVar[FeatureRef] = SubFeature(FeatureName.SNMP, "agent")
    key: ClassVar[str] = "feature.snmp.agent"
    label: ClassVar[str] = "SNMP agent state"
    commands: ClassVar[tuple[AntaCommand, ...]] = (SNMP_COMMAND,)

    @classmethod
    def parse(cls, commands: tuple[AntaCommand, ...]) -> Fact[SnmpAgentFact]:
        """Normalize the structured top-level SNMP enablement flag."""
        (command,) = commands
        source = _feature_source(command)
        enabled = command.json_output.get("enabled")
        if enabled is None:
            return cls.unavailable(FactProblemKind.MISSING, source)
        if not isinstance(enabled, bool):
            return cls.unavailable(FactProblemKind.MALFORMED, source)
        state = FeatureState.ENABLED if enabled else FeatureState.DISABLED
        return cls(state).available(source)


@dataclass(frozen=True, slots=True)
class SnmpV3AuthenticationFact(FeatureFact, CommandsFactDefinition["SnmpV3AuthenticationFact"]):
    """Whether a local or remote SNMPv3 user has a configured authentication key."""

    feature: ClassVar[FeatureRef] = SubFeature(FeatureName.SNMPV3, "authentication key")
    key: ClassVar[str] = "feature.snmpv3.authentication_key"
    label: ClassVar[str] = "SNMPv3 authentication key state"
    commands: ClassVar[tuple[AntaCommand, ...]] = (SNMPV3_USER_COMMAND,)

    @classmethod
    # pylint: disable-next=too-many-return-statements
    def parse(cls, commands: tuple[AntaCommand, ...]) -> Fact[SnmpV3AuthenticationFact]:  # noqa: C901, PLR0911
        """Normalize SNMPv3 authentication-key presence from structured operational state."""
        (command,) = commands
        source = _feature_source(command)
        if is_unsupported_optional_command(command):
            return cls(FeatureState.UNSUPPORTED).available(source)
        if "usersByVersion" not in command.json_output:
            return cls.unavailable(FactProblemKind.MISSING, source)
        users_by_version = command.json_output["usersByVersion"]
        if not isinstance(users_by_version, Mapping):
            return cls.unavailable(FactProblemKind.MALFORMED, source)
        version = users_by_version.get("v3")
        if version is None:
            return cls(FeatureState.DISABLED).available(source)
        if not isinstance(version, Mapping):
            return cls.unavailable(FactProblemKind.MALFORMED, source)
        users = version.get("users")
        if users is None:
            return cls(FeatureState.DISABLED).available(source)
        if not isinstance(users, Mapping):
            return cls.unavailable(FactProblemKind.MALFORMED, source)
        enabled = False
        for user in users.values():
            if not isinstance(user, Mapping):
                return cls.unavailable(FactProblemKind.MALFORMED, source)
            parameters = user.get("v3Params")
            if parameters is None:
                continue
            if not isinstance(parameters, Mapping):
                return cls.unavailable(FactProblemKind.MALFORMED, source)
            authentication_type = parameters.get("authType")
            if authentication_type is not None and not isinstance(authentication_type, str):
                return cls.unavailable(FactProblemKind.MALFORMED, source)
            enabled |= isinstance(authentication_type, str) and authentication_type.casefold() not in {"", "none", "noauth"}
        state = FeatureState.ENABLED if enabled else FeatureState.DISABLED
        return cls(state).available(source)


@dataclass(frozen=True, slots=True)
class SnmpV3CredentialSyntaxFact(CredentialSyntaxFact, CommandsFactDefinition["SnmpV3CredentialSyntaxFact"]):
    """Storage syntax used by configured local and remote SNMPv3 credentials."""

    feature: ClassVar[FeatureRef] = SubFeature(FeatureName.SNMPV3, "credential syntax")
    key: ClassVar[str] = "configuration.snmpv3.credential_syntax"
    label: ClassVar[str] = "SNMPv3 credential syntax"
    commands: ClassVar[tuple[AntaCommand, ...]] = (SNMPV3_USER_CONFIG_COMMAND,)

    @classmethod
    def parse(cls, commands: tuple[AntaCommand, ...]) -> Fact[SnmpV3CredentialSyntaxFact]:
        """Normalize credential syntax from the narrow SNMP user configuration output."""
        (command,) = commands
        source = _feature_source(command)
        state = _snmpv3_credential_syntax(command.text_output)
        if state is None:
            return cls.unavailable(FactProblemKind.MALFORMED, source)
        return cls(state).available(source)


@dataclass(frozen=True, slots=True)
class GnsiTransportFact(FeatureFact, CommandsFactDefinition["GnsiTransportFact"]):
    """Effective gNSI transport state."""

    feature: ClassVar[FeatureRef] = SubFeature(FeatureName.GNSI, "transport")
    key: ClassVar[str] = "feature.gnsi.transport"
    label: ClassVar[str] = "gNSI transport state"
    commands: ClassVar[tuple[AntaCommand, ...]] = (GNSI_COMMAND,)

    @classmethod
    def parse(cls, commands: tuple[AntaCommand, ...]) -> Fact[GnsiTransportFact]:
        """Normalize whether at least one configured gNSI transport is enabled."""
        (command,) = commands
        source = _feature_source(command)
        if is_unsupported_optional_command(command):
            return cls(FeatureState.UNSUPPORTED).available(source)

        transports = command.json_output.get("transports")
        if transports is None:
            return cls.unavailable(FactProblemKind.MISSING, source)
        if not isinstance(transports, Mapping):
            return cls.unavailable(FactProblemKind.MALFORMED, source)

        enabled = False
        for transport in transports.values():
            if not isinstance(transport, Mapping) or not isinstance((transport_enabled := transport.get("enabled")), bool):
                return cls.unavailable(FactProblemKind.MALFORMED, source)
            enabled = enabled or transport_enabled
        state = FeatureState.ENABLED if enabled else FeatureState.DISABLED
        return cls(state).available(source)


@dataclass(frozen=True, slots=True)
class GnsiMultipleTransportsFact(FeatureFact, CommandsFactDefinition["GnsiMultipleTransportsFact"]):
    """Presence of at least two enabled gNSI transports."""

    feature: ClassVar[FeatureRef] = SubFeature(FeatureName.GNSI, "multiple-transport mode")
    key: ClassVar[str] = "feature.gnsi.multiple_transports"
    label: ClassVar[str] = "gNSI multiple-transport state"
    commands: ClassVar[tuple[AntaCommand, ...]] = (GNSI_COMMAND,)

    @classmethod
    def parse(cls, commands: tuple[AntaCommand, ...]) -> Fact[GnsiMultipleTransportsFact]:
        """Normalize whether at least two configured gNSI transports are enabled."""
        (command,) = commands
        source = _feature_source(command)
        if is_unsupported_optional_command(command):
            return cls(FeatureState.UNSUPPORTED).available(source)

        transports = command.json_output.get("transports")
        if transports is None:
            return cls.unavailable(FactProblemKind.MISSING, source)
        if not isinstance(transports, Mapping):
            return cls.unavailable(FactProblemKind.MALFORMED, source)

        enabled_count = 0
        for transport in transports.values():
            if not isinstance(transport, Mapping) or not isinstance((transport_enabled := transport.get("enabled")), bool):
                return cls.unavailable(FactProblemKind.MALFORMED, source)
            enabled_count += transport_enabled
        state = FeatureState.ENABLED if enabled_count >= MIN_ENABLED_GNSI_TRANSPORTS else FeatureState.DISABLED
        return cls(state).available(source)


@dataclass(frozen=True, slots=True)
class GnsiCertzFact(FeatureFact, CommandsFactDefinition["GnsiCertzFact"]):
    """Effective gNSI Certz service state."""

    feature: ClassVar[FeatureRef] = SubFeature(FeatureName.GNSI, "Certz service")
    key: ClassVar[str] = "feature.gnsi.certz"
    label: ClassVar[str] = "gNSI Certz service state"
    commands: ClassVar[tuple[AntaCommand, ...]] = (GNSI_COMMAND,)

    @classmethod
    def parse(cls, commands: tuple[AntaCommand, ...]) -> Fact[GnsiCertzFact]:
        """Normalize the top-level Certz enablement flag."""
        (command,) = commands
        source = _feature_source(command)
        if is_unsupported_optional_command(command):
            return cls(FeatureState.UNSUPPORTED).available(source)

        enabled = command.json_output.get("certzEnabled")
        if enabled is None:
            return cls.unavailable(FactProblemKind.MISSING, source)
        if not isinstance(enabled, bool):
            return cls.unavailable(FactProblemKind.MALFORMED, source)
        state = FeatureState.ENABLED if enabled else FeatureState.DISABLED
        return cls(state).available(source)


@dataclass(frozen=True, slots=True)
class GnsiCredentialzFact(FeatureFact, CommandsFactDefinition["GnsiCredentialzFact"]):
    """Effective gNSI Credentialz service state."""

    feature: ClassVar[FeatureRef] = SubFeature(FeatureName.GNSI, "Credentialz service")
    key: ClassVar[str] = "feature.gnsi.credentialz"
    label: ClassVar[str] = "gNSI Credentialz service state"
    commands: ClassVar[tuple[AntaCommand, ...]] = (GNSI_COMMAND,)

    @classmethod
    def parse(cls, commands: tuple[AntaCommand, ...]) -> Fact[GnsiCredentialzFact]:
        """Normalize the top-level Credentialz enablement flag."""
        (command,) = commands
        source = _feature_source(command)
        if is_unsupported_optional_command(command):
            return cls(FeatureState.UNSUPPORTED).available(source)
        enabled = command.json_output.get("credentialzEnabled")
        if enabled is None:
            return cls.unavailable(FactProblemKind.MISSING, source)
        if not isinstance(enabled, bool):
            return cls.unavailable(FactProblemKind.MALFORMED, source)
        state = FeatureState.ENABLED if enabled else FeatureState.DISABLED
        return cls(state).available(source)


@dataclass(frozen=True, slots=True)
class GnsiAuthzFact(FeatureFact, CommandsFactDefinition["GnsiAuthzFact"]):
    """Effective gNSI Authz service state."""

    feature: ClassVar[FeatureRef] = SubFeature(FeatureName.GNSI, "Authz service")
    key: ClassVar[str] = "feature.gnsi.authz"
    label: ClassVar[str] = "gNSI Authz service state"
    commands: ClassVar[tuple[AntaCommand, ...]] = (GNSI_COMMAND,)

    @classmethod
    def parse(cls, commands: tuple[AntaCommand, ...]) -> Fact[GnsiAuthzFact]:
        """Normalize the top-level Authz enablement flag."""
        (command,) = commands
        source = _feature_source(command)
        if is_unsupported_optional_command(command):
            return cls(FeatureState.UNSUPPORTED).available(source)

        enabled = command.json_output.get("authzEnabled")
        if enabled is None:
            return cls.unavailable(FactProblemKind.MISSING, source)
        if not isinstance(enabled, bool):
            return cls.unavailable(FactProblemKind.MALFORMED, source)
        state = FeatureState.ENABLED if enabled else FeatureState.DISABLED
        return cls(state).available(source)


@dataclass(frozen=True, slots=True)
class GnsiAcctzFact(FeatureFact, CommandsFactDefinition["GnsiAcctzFact"]):
    """Effective gNSI Acctz service state."""

    feature: ClassVar[FeatureRef] = SubFeature(FeatureName.GNSI, "Acctz service")
    key: ClassVar[str] = "feature.gnsi.acctz"
    label: ClassVar[str] = "gNSI Acctz service state"
    commands: ClassVar[tuple[AntaCommand, ...]] = (GNSI_COMMAND,)

    @classmethod
    def derive(cls, device: AntaDevice, commands: tuple[AntaCommand, ...] = ()) -> Fact[GnsiAcctzFact]:
        """Interpret an absent Acctz field according to the EOS response schema."""
        fact = super(GnsiAcctzFact, cls).derive(device, commands)
        return _version_aware_gnsi_service_absence(device, commands, fact, "acctzEnabled", cls(FeatureState.UNSUPPORTED))

    @classmethod
    def parse(cls, commands: tuple[AntaCommand, ...]) -> Fact[GnsiAcctzFact]:
        """Normalize the top-level Acctz enablement flag."""
        (command,) = commands
        source = _feature_source(command)
        if is_unsupported_optional_command(command):
            return cls(FeatureState.UNSUPPORTED).available(source)
        if "acctzEnabled" not in command.json_output:
            return cls.unavailable(FactProblemKind.MISSING, source)
        enabled = command.json_output["acctzEnabled"]
        if not isinstance(enabled, bool):
            return cls.unavailable(FactProblemKind.MALFORMED, source)
        state = FeatureState.ENABLED if enabled else FeatureState.DISABLED
        return cls(state).available(source)


@dataclass(frozen=True, slots=True)
class GnsiPathzFact(FeatureFact, CommandsFactDefinition["GnsiPathzFact"]):
    """Effective gNSI Pathz service state."""

    feature: ClassVar[FeatureRef] = SubFeature(FeatureName.GNSI, "Pathz service")
    key: ClassVar[str] = "feature.gnsi.pathz"
    label: ClassVar[str] = "gNSI Pathz service state"
    commands: ClassVar[tuple[AntaCommand, ...]] = (GNSI_COMMAND,)

    @classmethod
    def derive(cls, device: AntaDevice, commands: tuple[AntaCommand, ...] = ()) -> Fact[GnsiPathzFact]:
        """Interpret an absent Pathz field according to the EOS response schema."""
        fact = super(GnsiPathzFact, cls).derive(device, commands)
        return _version_aware_gnsi_service_absence(device, commands, fact, "pathzEnabled", cls(FeatureState.UNSUPPORTED))

    @classmethod
    def parse(cls, commands: tuple[AntaCommand, ...]) -> Fact[GnsiPathzFact]:
        """Normalize the top-level Pathz enablement flag."""
        (command,) = commands
        source = _feature_source(command)
        if is_unsupported_optional_command(command):
            return cls(FeatureState.UNSUPPORTED).available(source)

        if "pathzEnabled" not in command.json_output:
            return cls.unavailable(FactProblemKind.MISSING, source)
        enabled = command.json_output["pathzEnabled"]
        if not isinstance(enabled, bool):
            return cls.unavailable(FactProblemKind.MALFORMED, source)
        state = FeatureState.ENABLED if enabled else FeatureState.DISABLED
        return cls(state).available(source)


def _pathz_policy_has_user_group_overlap(output: str) -> bool | None:
    """Return whether a Pathz policy contains user and group rules for the same path."""
    try:
        policy = json.loads(output)
    except json.JSONDecodeError:
        return None
    if policy is None:
        return False
    if not isinstance(policy, Mapping):
        return None
    rules = policy.get("rules", [])
    if not isinstance(rules, list):
        return None

    paths = _pathz_policy_rule_paths(rules)
    if paths is None:
        return None
    user_paths, group_paths = paths
    return bool(user_paths & group_paths)


def _pathz_policy_rule_paths(rules: list[object]) -> tuple[set[str], set[str]] | None:
    """Return canonical user and group paths from valid Pathz rules."""
    user_paths: set[str] = set()
    group_paths: set[str] = set()
    for rule in rules:
        if not isinstance(rule, Mapping):
            return None
        has_user = "user" in rule
        has_group = "group" in rule
        if not has_user and not has_group:
            continue
        if has_user == has_group or not isinstance(path := rule.get("path"), Mapping):
            return None
        serialized_path = json.dumps(path, sort_keys=True, separators=(",", ":"))
        (user_paths if has_user else group_paths).add(serialized_path)
    return user_paths, group_paths


@dataclass(frozen=True, slots=True)
class GnsiPathzPolicyOverlapFact(FeatureFact, CommandsFactDefinition["GnsiPathzPolicyOverlapFact"]):
    """Presence of Pathz user and group rules applying to the same path."""

    feature: ClassVar[FeatureRef] = SubFeature(FeatureName.GNSI, "Pathz policy user/group overlap")
    key: ClassVar[str] = "feature.gnsi.pathz_policy_user_group_overlap"
    label: ClassVar[str] = "Pathz policy user/group overlap"
    commands: ClassVar[tuple[AntaCommand, ...]] = (PATHZ_POLICY_COMMAND,)

    @classmethod
    def parse(cls, commands: tuple[AntaCommand, ...]) -> Fact[GnsiPathzPolicyOverlapFact]:
        """Normalize the persisted Pathz policy without retaining policy contents."""
        (command,) = commands
        source = _feature_source(command)
        if is_unsupported_optional_command(command):
            return cls.unavailable(FactProblemKind.UNSUPPORTED, source)
        if command.errors:
            return cls.unavailable(FactProblemKind.COLLECTION_FAILED, source)
        overlap = _pathz_policy_has_user_group_overlap(command.text_output)
        if overlap is None:
            problem = FactProblemKind.MISSING if not command.text_output.strip() else FactProblemKind.MALFORMED
            return cls.unavailable(problem, source)
        state = FeatureState.ENABLED if overlap else FeatureState.DISABLED
        return cls(state).available(source)


@dataclass(frozen=True, slots=True)
class GnmiTransportFact(FeatureFact, CommandsFactDefinition["GnmiTransportFact"]):
    """Effective gNMI transport state."""

    feature: ClassVar[FeatureRef] = FeatureName.GNMI
    key: ClassVar[str] = "feature.gnmi.transport"
    label: ClassVar[str] = "gNMI transport state"
    commands: ClassVar[tuple[AntaCommand, ...]] = (GNMI_COMMAND,)

    @classmethod
    def parse(cls, commands: tuple[AntaCommand, ...]) -> Fact[GnmiTransportFact]:
        (command,) = commands
        source = _feature_source(command)
        if is_unsupported_optional_command(command):
            return cls(FeatureState.UNSUPPORTED).available(source)
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
                return cls(FeatureState.ENABLED).available(source)
            if enabled is not False:
                unknown = True
        if unknown:
            return cls.unavailable(FactProblemKind.MALFORMED, source)
        state = FeatureState.DISABLED
        return cls(state).available(source)


@dataclass(frozen=True, slots=True)
class GnmiAccountingFact(FeatureFact, CommandsFactDefinition["GnmiAccountingFact"]):
    """Accounting state across enabled gNMI transports."""

    feature: ClassVar[FeatureRef] = SubFeature(FeatureName.GNMI, "transport accounting")
    key: ClassVar[str] = "feature.gnmi.accounting"
    label: ClassVar[str] = "gNMI transport accounting state"
    commands: ClassVar[tuple[AntaCommand, ...]] = (GNMI_COMMAND,)

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
    def parse(cls, commands: tuple[AntaCommand, ...]) -> Fact[GnmiAccountingFact]:
        (command,) = commands
        source = _feature_source(command)
        if is_unsupported_optional_command(command):
            return cls(FeatureState.UNSUPPORTED).available(source)
        config = _deserialize_gnmi_config(command.json_output)
        if config is None:
            return cls.unavailable(FactProblemKind.MALFORMED, source)
        state = cls._state(config)
        if isinstance(state, FactProblemKind):
            return cls.unavailable(state, source)
        return cls(state).available(source)


@dataclass(frozen=True, slots=True)
class GnmiAuthorizationFact(FeatureFact, CommandsFactDefinition["GnmiAuthorizationFact"]):
    """Request authorization on at least one enabled gNMI transport."""

    feature: ClassVar[FeatureRef] = SubFeature(FeatureName.GNMI, "request authorization")
    key: ClassVar[str] = "feature.gnmi.authorization"
    label: ClassVar[str] = "gNMI request-authorization state"
    commands: ClassVar[tuple[AntaCommand, ...]] = (GNMI_COMMAND,)

    @classmethod
    def parse(cls, commands: tuple[AntaCommand, ...]) -> Fact[GnmiAuthorizationFact]:
        """Normalize authorization state across enabled transports."""
        (command,) = commands
        source = _feature_source(command)
        if is_unsupported_optional_command(command):
            return cls(FeatureState.UNSUPPORTED).available(source)
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
            authorization = transport.get("authorization")
            if enabled is True and authorization is True:
                return cls(FeatureState.ENABLED).available(source)
            if enabled not in {True, False} or (enabled is True and authorization not in {True, False}):
                unknown = True
        if unknown:
            return cls.unavailable(FactProblemKind.MISSING, source)
        return cls(FeatureState.DISABLED).available(source)


@dataclass(frozen=True, slots=True)
class RestconfTransportFact(FeatureFact, CommandsFactDefinition["RestconfTransportFact"]):
    """Effective RESTCONF transport state."""

    feature: ClassVar[FeatureRef] = FeatureName.RESTCONF
    key: ClassVar[str] = "feature.restconf.transport"
    label: ClassVar[str] = "RESTCONF transport state"
    commands: ClassVar[tuple[AntaCommand, ...]] = (RESTCONF_COMMAND,)

    @classmethod
    def parse(cls, commands: tuple[AntaCommand, ...]) -> Fact[RestconfTransportFact]:
        """Normalize structured RESTCONF enablement."""
        (command,) = commands
        source = _feature_source(command)
        if is_unsupported_optional_command(command):
            return cls(FeatureState.UNSUPPORTED).available(source)
        if "enabled" not in command.json_output:
            return cls.unavailable(FactProblemKind.MISSING, source)
        enabled = command.json_output["enabled"]
        if not isinstance(enabled, bool):
            return cls.unavailable(FactProblemKind.MALFORMED, source)
        return cls(FeatureState.ENABLED if enabled else FeatureState.DISABLED).available(source)


@dataclass(frozen=True, slots=True)
class NetconfTransportFact(FeatureFact, CommandsFactDefinition["NetconfTransportFact"]):
    """Effective NETCONF transport state."""

    feature: ClassVar[FeatureRef] = FeatureName.NETCONF
    key: ClassVar[str] = "feature.netconf.transport"
    label: ClassVar[str] = "NETCONF transport state"
    commands: ClassVar[tuple[AntaCommand, ...]] = (NETCONF_COMMAND,)

    @classmethod
    def parse(cls, commands: tuple[AntaCommand, ...]) -> Fact[NetconfTransportFact]:
        """Normalize structured NETCONF enablement."""
        (command,) = commands
        source = _feature_source(command)
        if is_unsupported_optional_command(command):
            return cls(FeatureState.UNSUPPORTED).available(source)
        if "enabled" not in command.json_output:
            return cls.unavailable(FactProblemKind.MISSING, source)
        enabled = command.json_output["enabled"]
        if not isinstance(enabled, bool):
            return cls.unavailable(FactProblemKind.MALFORMED, source)
        return cls(FeatureState.ENABLED if enabled else FeatureState.DISABLED).available(source)


@dataclass(frozen=True, slots=True)
class GnpsiTransportFact(FeatureFact, CommandsFactDefinition["GnpsiTransportFact"]):
    """Effective gNPSI transport state."""

    feature: ClassVar[FeatureRef] = SubFeature(FeatureName.GNPSI, "transport")
    key: ClassVar[str] = "feature.gnpsi.transport"
    label: ClassVar[str] = "gNPSI transport state"
    commands: ClassVar[tuple[AntaCommand, ...]] = (GNPSI_COMMAND,)

    @classmethod
    def parse(cls, commands: tuple[AntaCommand, ...]) -> Fact[GnpsiTransportFact]:
        """Normalize enabled transports and the explicit disabled state."""
        (command,) = commands
        source = _feature_source(command)
        if is_unsupported_optional_command(command):
            return cls(FeatureState.UNSUPPORTED).available(source)
        config = _deserialize_gnpsi_config(command.json_output)
        if isinstance(config, FactProblemKind):
            return cls.unavailable(config, source)
        if not isinstance(config.enabled, bool):
            return cls.unavailable(FactProblemKind.MALFORMED, source)
        state = FeatureState.ENABLED if config.enabled else FeatureState.DISABLED
        return cls(state).available(source)


@dataclass(frozen=True, slots=True)
class GnpsiAuthenticationExposureFact(FeatureFact, CommandsFactDefinition["GnpsiAuthenticationExposureFact"]):
    """gNPSI authentication combinations exposed to request execution."""

    feature: ClassVar[FeatureRef] = SubFeature(FeatureName.GNPSI, "exposed authentication mode")
    key: ClassVar[str] = "feature.gnpsi.authentication_exposure"
    label: ClassVar[str] = "gNPSI authentication exposure state"
    commands: ClassVar[tuple[AntaCommand, ...]] = (GNPSI_COMMAND,)

    @classmethod
    # pylint: disable-next=too-many-return-statements
    def parse(cls, commands: tuple[AntaCommand, ...]) -> Fact[GnpsiAuthenticationExposureFact]:  # noqa: C901, PLR0911
        """Normalize TLS metadata and mTLS common-name authentication paths."""
        (command,) = commands
        source = _feature_source(command)
        if is_unsupported_optional_command(command):
            return cls(FeatureState.UNSUPPORTED).available(source)
        config = _deserialize_gnpsi_config(command.json_output)
        if isinstance(config, FactProblemKind):
            return cls.unavailable(config, source)
        if not isinstance(config.enabled, bool):
            return cls.unavailable(FactProblemKind.MALFORMED, source)
        if not config.enabled:
            return cls(FeatureState.DISABLED).available(source)
        if any(not isinstance(transport.enabled, bool) for transport in config.transports):
            return cls.unavailable(FactProblemKind.MALFORMED, source)
        enabled_transports = tuple(transport for transport in config.transports if transport.enabled is True)
        if not enabled_transports:
            return cls(FeatureState.DISABLED).available(source)
        problem: FactProblemKind | None = None
        for transport in enabled_transports:
            authentication = _gnpsi_authentication(transport)
            if isinstance(authentication, FactProblemKind):
                problem = authentication if problem is None or authentication is FactProblemKind.MALFORMED else problem
                continue
            security_type, methods = authentication
            mutual_tls = security_type in {"mtls", "mutualtls", "tlsmutual"}
            tls = security_type == "tls"
            if (mutual_tls and "x509-common-name" in methods) or (tls and "metadata" in methods):
                return cls(FeatureState.ENABLED).available(source)
        if problem is not None:
            return cls.unavailable(problem, source)
        return cls(FeatureState.DISABLED).available(source)


@dataclass(frozen=True, slots=True)
class GnpsiMutualTlsSpiffeMitigationFact(MitigationFact, CommandsFactDefinition["GnpsiMutualTlsSpiffeMitigationFact"]):
    """Mutual TLS with exclusively x509-spiffe authentication on every enabled gNPSI transport."""

    key: ClassVar[str] = "mitigation.gnpsi.mutual_tls_spiffe"
    label: ClassVar[str] = "gNPSI mutual TLS with only x509-spiffe authentication"
    commands: ClassVar[tuple[AntaCommand, ...]] = (GNPSI_COMMAND,)

    @classmethod
    # pylint: disable-next=too-many-return-statements
    def parse(cls, commands: tuple[AntaCommand, ...]) -> Fact[GnpsiMutualTlsSpiffeMitigationFact]:  # noqa: C901, PLR0911
        """Verify the exact authentication control across every enabled transport."""
        (command,) = commands
        source = _feature_source(command)
        if is_unsupported_optional_command(command):
            return cls.unavailable(FactProblemKind.UNSUPPORTED, source)
        config = _deserialize_gnpsi_config(command.json_output)
        if isinstance(config, FactProblemKind):
            return cls.unavailable(config, source)
        if not isinstance(config.enabled, bool):
            return cls.unavailable(FactProblemKind.MALFORMED, source)
        if not config.enabled:
            return cls(MitigationState.INEFFECTIVE).available(source)
        if any(not isinstance(transport.enabled, bool) for transport in config.transports):
            return cls.unavailable(FactProblemKind.MALFORMED, source)
        enabled_transports = tuple(transport for transport in config.transports if transport.enabled is True)
        if not enabled_transports:
            return cls(MitigationState.INEFFECTIVE).available(source)
        problem: FactProblemKind | None = None
        for transport in enabled_transports:
            authentication = _gnpsi_authentication(transport)
            if isinstance(authentication, FactProblemKind):
                problem = authentication if problem is None or authentication is FactProblemKind.MALFORMED else problem
                continue
            security_type, methods = authentication
            if security_type not in {"mtls", "mutualtls", "tlsmutual"} or methods != {"x509-spiffe"}:
                return cls(MitigationState.INEFFECTIVE).available(source)
        if problem is not None:
            return cls.unavailable(problem, source)
        return cls(MitigationState.EFFECTIVE).available(source)


@dataclass(frozen=True, slots=True)
class GnpsiEosRpcAuthTraceFact(FeatureFact, CommandsFactDefinition["GnpsiEosRpcAuthTraceFact"]):
    """Explicit gNPSI EosRpcAuth trace state."""

    feature: ClassVar[FeatureRef] = SubFeature(FeatureName.GNPSI, "EosRpcAuth trace")
    key: ClassVar[str] = "feature.gnpsi.eos_rpc_auth_trace"
    label: ClassVar[str] = "gNPSI EosRpcAuth trace state"
    commands: ClassVar[tuple[AntaCommand, ...]] = (GNPSI_TRACE_COMMAND,)

    @classmethod
    def parse(cls, commands: tuple[AntaCommand, ...]) -> Fact[GnpsiEosRpcAuthTraceFact]:
        """Normalize the explicit trace-facility status."""
        (command,) = commands
        source = _feature_source(command)
        if is_unsupported_optional_command(command):
            return cls(FeatureState.UNSUPPORTED).available(source)
        if command.error:
            return cls.unavailable(FactProblemKind.COLLECTION_FAILED, source)
        output = command.text_output.strip()
        if not output:
            return cls(FeatureState.DISABLED).available(source)
        enabled = re.search(r"^EosRpcAuth\s+enabled\b", output, re.MULTILINE) is not None
        disabled = re.search(r"^EosRpcAuth\s+disabled\b", output, re.MULTILINE) is not None
        if enabled == disabled:
            return cls.unavailable(FactProblemKind.MALFORMED, source)
        return cls(FeatureState.ENABLED if enabled else FeatureState.DISABLED).available(source)


@dataclass(frozen=True, slots=True)
class _GnmiAuthorizationCandidates:
    """SSL profiles that may expose gNMI request authorization."""

    profile_names: tuple[str, ...]
    incomplete_transport: bool


def _gnmi_authorization_candidate(transport: object) -> tuple[str | None, bool]:
    """Return one candidate SSL profile and whether its transport is incomplete."""
    if not isinstance(transport, Mapping):
        return None, True
    enabled = transport.get("enabled")
    authorization = transport.get("authorization")
    if enabled is False or authorization is False:
        return None, False
    if enabled is not True or authorization is not True:
        return None, True
    profile_name = transport.get("sslProfile")
    if profile_name in (None, ""):
        return None, False
    if not isinstance(profile_name, str):
        return None, True
    return profile_name, False


@dataclass(frozen=True, slots=True)
class GnmiMtlsAuthorizationFact(FeatureFact, CommandsFactDefinition["GnmiMtlsAuthorizationFact"]):
    """Enabled gNMI transport with both request authorization and mutual TLS."""

    feature: ClassVar[FeatureRef] = SubFeature(FeatureName.GNMI, "mTLS request authorization")
    key: ClassVar[str] = "feature.gnmi.mtls_authorization"
    label: ClassVar[str] = "gNMI mTLS request authorization state"
    commands: ClassVar[tuple[AntaCommand, ...]] = (GNMI_COMMAND, SSL_PROFILE_COMMAND)

    @classmethod
    def _candidates(cls, gnmi: AntaCommand) -> Fact[GnmiMtlsAuthorizationFact] | _GnmiAuthorizationCandidates:
        """Return candidate profiles or a result decided by gNMI output alone."""
        source = _feature_source(gnmi)
        if is_unsupported_optional_command(gnmi):
            return cls(FeatureState.UNSUPPORTED).available(source)
        config = _deserialize_gnmi_config(gnmi.json_output)
        if config is None:
            return cls.unavailable(FactProblemKind.MALFORMED, source)
        if config.service_enabled is False and any(isinstance(transport, Mapping) and transport.get("enabled") is True for transport in config.transports):
            return cls.unavailable(FactProblemKind.MALFORMED, source)

        profile_names: list[str] = []
        incomplete = False
        for transport in config.transports:
            profile_name, candidate_incomplete = _gnmi_authorization_candidate(transport)
            incomplete = incomplete or candidate_incomplete
            if profile_name is not None:
                profile_names.append(profile_name)

        if profile_names:
            return _GnmiAuthorizationCandidates(tuple(profile_names), incomplete)
        if incomplete:
            return cls.unavailable(FactProblemKind.MISSING, source)
        return cls(FeatureState.DISABLED).available(source)

    @classmethod
    def _evaluate_candidates(cls, candidates: _GnmiAuthorizationCandidates, ssl: AntaCommand, gnmi: AntaCommand) -> Fact[GnmiMtlsAuthorizationFact]:
        """Evaluate candidate profiles and retain the command causing uncertainty."""
        ssl_source = _feature_source(ssl)
        if is_unsupported_optional_command(ssl):
            return cls.unavailable(FactProblemKind.UNSUPPORTED, ssl_source)

        states = tuple(_ssl_profile_has_mtls(profile_name, ssl.json_output) for profile_name in candidates.profile_names)
        if True in states:
            return cls(FeatureState.ENABLED).available(ssl_source)
        if None in states:
            return cls.unavailable(FactProblemKind.MISSING, ssl_source)
        if candidates.incomplete_transport:
            return cls.unavailable(FactProblemKind.MISSING, _feature_source(gnmi))
        return cls(FeatureState.DISABLED).available(ssl_source)

    @classmethod
    def parse(cls, commands: tuple[AntaCommand, ...]) -> Fact[GnmiMtlsAuthorizationFact]:
        """Normalize exposure without combining state from different transports."""
        gnmi, ssl = commands
        candidates = cls._candidates(gnmi)
        if not isinstance(candidates, _GnmiAuthorizationCandidates):
            return candidates
        return cls._evaluate_candidates(candidates, ssl, gnmi)


@dataclass(frozen=True, slots=True)
class RiskyOpenConfigTraceFact(ConfigurationFact, CommandsFactDefinition["RiskyOpenConfigTraceFact"]):
    """Presence of an advisory-identified OpenConfig trace selector."""

    feature: ClassVar[FeatureRef] = SubFeature(FeatureName.TRACE, "advisory-identified selector")
    key: ClassVar[str] = "configuration.openconfig.risky_trace_selector"
    label: ClassVar[str] = "OpenConfig trace selector configuration"
    commands: ClassVar[tuple[AntaCommand, ...]] = (TRACE_COMMAND,)

    @classmethod
    def parse(cls, commands: tuple[AntaCommand, ...]) -> Fact[RiskyOpenConfigTraceFact]:
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
        state = ConfigurationState.CONFIGURED if configured else ConfigurationState.NOT_CONFIGURED
        return cls(state).available(source)


@dataclass(frozen=True, slots=True)
class GribiTransportFact(FeatureFact, CommandsFactDefinition["GribiTransportFact"]):
    """Effective gRIBI service state."""

    feature: ClassVar[FeatureRef] = FeatureName.GRIBI
    key: ClassVar[str] = "feature.gribi.transport"
    label: ClassVar[str] = "gRIBI service state"
    commands: ClassVar[tuple[AntaCommand, ...]] = (GRIBI_COMMAND,)

    @classmethod
    def parse(cls, commands: tuple[AntaCommand, ...]) -> Fact[GribiTransportFact]:
        (command,) = commands
        source = _feature_source(command)
        if is_unsupported_optional_command(command):
            return cls(FeatureState.UNSUPPORTED).available(source)
        enabled = command.json_output.get("enabled")
        if not isinstance(enabled, bool):
            return cls.unavailable(FactProblemKind.MALFORMED, source)
        return cls(FeatureState.ENABLED if enabled else FeatureState.DISABLED).available(source)


def _ssl_profile_is_valid(profile: Mapping[str, object]) -> bool:
    """Return whether an SSL profile has valid server identity material."""
    if profile.get("profileState") != "valid" or profile.get("profileError") != []:
        return False
    return all(isinstance(value, str) and value.strip() for value in (profile.get("certName"), profile.get("keyName")))


def _ssl_profile_trust_is_valid(profile: Mapping[str, object]) -> bool | None:
    """Return whether an SSL profile has valid trusted client certificates."""
    if "trustedCertificates" not in profile:
        return False
    trusted = profile["trustedCertificates"]
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


@dataclass(frozen=True, slots=True)
class GnmiMtlsFact(MitigationFact, CommandsFactDefinition["GnmiMtlsFact"]):
    """mTLS coverage across enabled gNMI transports."""

    key: ClassVar[str] = "mitigation.gnmi.mtls"
    label: ClassVar[str] = "gNMI mTLS"
    commands: ClassVar[tuple[AntaCommand, ...]] = (GNMI_COMMAND, SSL_PROFILE_COMMAND)

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
    def _profile_names(cls, gnmi: AntaCommand) -> Fact[GnmiMtlsFact] | tuple[str, ...]:
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
            return cls(MitigationState.INEFFECTIVE).available(source)
        if any(not isinstance(profile_name, str) for profile_name in profile_names):
            return cls.unavailable(FactProblemKind.MISSING, source)
        return tuple(profile_name for profile_name in profile_names if isinstance(profile_name, str))

    @classmethod
    def _evaluate_profiles(cls, profile_names: tuple[str, ...], ssl: AntaCommand) -> Fact[GnmiMtlsFact]:
        """Evaluate configured gNMI profiles using SSL-profile output."""
        source = _feature_source(ssl)
        if is_unsupported_optional_command(ssl):
            return cls.unavailable(FactProblemKind.UNSUPPORTED, source)

        states = tuple(_ssl_profile_has_mtls(profile_name, ssl.json_output) for profile_name in profile_names)
        if False in states:
            return cls(MitigationState.INEFFECTIVE).available(source)
        if None in states:
            return cls.unavailable(FactProblemKind.MISSING, source)
        return cls(MitigationState.EFFECTIVE).available(source)

    @classmethod
    def parse(cls, commands: tuple[AntaCommand, ...]) -> Fact[GnmiMtlsFact]:
        gnmi, ssl = commands
        profile_names = cls._profile_names(gnmi)
        if not isinstance(profile_names, tuple):
            return profile_names
        return cls._evaluate_profiles(profile_names, ssl)


@dataclass(frozen=True, slots=True)
class GribiMtlsFact(MitigationFact, CommandsFactDefinition["GribiMtlsFact"]):
    """mTLS state for the gRIBI service."""

    key: ClassVar[str] = "mitigation.gribi.mtls"
    label: ClassVar[str] = "gRIBI mTLS"
    commands: ClassVar[tuple[AntaCommand, ...]] = (GRIBI_COMMAND, SSL_PROFILE_COMMAND)

    @classmethod
    def _profile_name(cls, gribi: AntaCommand) -> Fact[GribiMtlsFact] | str:
        """Return the gRIBI SSL profile or a result decided by gRIBI output alone."""
        source = _feature_source(gribi)
        if is_unsupported_optional_command(gribi):
            return cls.unavailable(FactProblemKind.UNSUPPORTED, source)
        enabled = gribi.json_output.get("mTls")
        if not isinstance(enabled, bool):
            return cls.unavailable(FactProblemKind.MISSING, source)
        if not enabled:
            return cls(MitigationState.INEFFECTIVE).available(source)

        profile_name = gribi.json_output.get("sslProfile")
        if profile_name in (None, ""):
            return cls(MitigationState.INEFFECTIVE).available(source)
        if not isinstance(profile_name, str):
            return cls.unavailable(FactProblemKind.MISSING, source)
        return profile_name

    @classmethod
    def _evaluate_profile(cls, profile_name: str, ssl: AntaCommand) -> Fact[GribiMtlsFact]:
        """Evaluate the configured gRIBI profile using SSL-profile output."""
        source = _feature_source(ssl)
        if is_unsupported_optional_command(ssl):
            return cls.unavailable(FactProblemKind.UNSUPPORTED, source)
        mtls = _ssl_profile_has_mtls(profile_name, ssl.json_output)
        if mtls is None:
            return cls.unavailable(FactProblemKind.MISSING, source)
        state = MitigationState.EFFECTIVE if mtls else MitigationState.INEFFECTIVE
        return cls(state).available(source)

    @classmethod
    def parse(cls, commands: tuple[AntaCommand, ...]) -> Fact[GribiMtlsFact]:
        gribi, ssl = commands
        profile_name = cls._profile_name(gribi)
        if not isinstance(profile_name, str):
            return profile_name
        return cls._evaluate_profile(profile_name, ssl)
