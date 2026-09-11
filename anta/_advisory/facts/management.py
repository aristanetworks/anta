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

from anta._advisory.facts.models import (
    CommandsFactDefinition,
    ConfigurationState,
    ConfigurationValue,
    CredentialSyntaxState,
    CredentialSyntaxValue,
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
from anta._eos.parsing import ParseFail, ParseFailureReason, ParseResult, ParseSuccessful
from anta.models import AntaCommand

RISKY_TRACE_SELECTORS = ("service/9", "interceptor/9", "transport_socketcli/9")
GNMI_COMMAND = OptionalAntaCommand(command="show management api gnmi", revision=1)
DOT1X_COMMAND = OptionalAntaCommand(command="show dot1x all", revision=1)
RADIUS_PROXY_CONFIG_COMMAND = AntaCommand(command="show running-config section radius proxy", ofmt="text")
GNSI_COMMAND = OptionalAntaCommand(command="show management api gnsi", revision=1)
GNPSI_COMMAND = OptionalAntaCommand(command="show management api gnpsi", revision=1)
GNPSI_TRACE_COMMAND = OptionalAntaCommand(command="show trace Gnpsi | grep Auth", ofmt="text", defer_errors=True)
MIN_ENABLED_GNSI_TRANSPORTS = 2
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


class Dot1xControlledAuthenticatorFact(CommandsFactDefinition[FeatureValue]):
    """Effective 802.1X authenticator with controlled port state."""

    key = "feature.dot1x.controlled_authenticator"
    label = "802.1X controlled authenticator state"
    commands = (DOT1X_COMMAND,)

    @classmethod
    def parse(cls, commands: tuple[AntaCommand, ...]) -> Fact[FeatureValue]:
        """Normalize system control and effective interface port-control state."""
        (command,) = commands
        source = _feature_source(command)
        feature = SubFeature(FeatureName.DOT1X, "controlled authenticator")
        if is_unsupported_optional_command(command):
            return cls.available(FeatureValue(feature, FeatureState.UNSUPPORTED), source)
        parsed = _parse_dot1x_controlled_authenticator(command.json_output)
        if isinstance(parsed, ParseFail):
            return cls.unavailable(FactProblemKind(parsed.reason.value), source)
        state = FeatureState.ENABLED if parsed.value else FeatureState.DISABLED
        return cls.available(FeatureValue(feature, state), source)


class Dot1xDynamicAuthorizationFact(CommandsFactDefinition[FeatureValue]):
    """Effective 802.1X dynamic authorization with an authenticator interface."""

    key = "feature.dot1x.dynamic_authorization"
    label = "802.1X dynamic-authorization state"
    commands = (DOT1X_COMMAND,)

    @classmethod
    def parse(cls, commands: tuple[AntaCommand, ...]) -> Fact[FeatureValue]:
        """Normalize the structured global and interface prerequisites."""
        (command,) = commands
        feature = SubFeature(FeatureName.DOT1X, "dynamic authorization authenticator")
        source = _feature_source(command)
        if is_unsupported_optional_command(command):
            return cls.available(FeatureValue(feature, FeatureState.UNSUPPORTED), source)
        dynamic_authorization = command.json_output.get("dynAuth")
        if not isinstance(dynamic_authorization, bool):
            return cls.unavailable(FactProblemKind.MALFORMED, source)
        if not dynamic_authorization:
            return cls.available(FeatureValue(feature, FeatureState.DISABLED), source)
        parsed = _parse_dot1x_controlled_authenticator(command.json_output)
        if isinstance(parsed, ParseFail):
            return cls.unavailable(FactProblemKind(parsed.reason.value), source)
        state = FeatureState.ENABLED if parsed.value else FeatureState.DISABLED
        return cls.available(FeatureValue(feature, state), source)


class RadiusProxyDynamicAuthorizationFact(CommandsFactDefinition[FeatureValue]):
    """Configured RADIUS proxy dynamic authorization with a client group."""

    key = "feature.radius_proxy.dynamic_authorization"
    label = "RADIUS proxy dynamic-authorization state"
    commands = (RADIUS_PROXY_CONFIG_COMMAND,)

    @classmethod
    def parse(cls, commands: tuple[AntaCommand, ...]) -> Fact[FeatureValue]:
        """Normalize the complete source-defined RADIUS proxy prerequisite."""
        (command,) = commands
        lines = tuple(line.strip() for line in command.text_output.splitlines() if line.strip() and line.strip() != "!")
        configured = "radius proxy" in lines and "dynamic-authorization" in lines and any(line.startswith("client group ") for line in lines)
        state = FeatureState.ENABLED if configured else FeatureState.DISABLED
        feature = SubFeature(FeatureName.RADIUS_PROXY, "dynamic authorization client group")
        return cls.available(FeatureValue(feature, state), _feature_source(command))


class SnmpAgentFact(CommandsFactDefinition[FeatureValue]):
    """Effective SNMP agent state."""

    key = "feature.snmp.agent"
    label = "SNMP agent state"
    commands = (SNMP_COMMAND,)

    @classmethod
    def parse(cls, commands: tuple[AntaCommand, ...]) -> Fact[FeatureValue]:
        """Normalize the structured top-level SNMP enablement flag."""
        (command,) = commands
        source = _feature_source(command)
        enabled = command.json_output.get("enabled")
        if enabled is None:
            return cls.unavailable(FactProblemKind.MISSING, source)
        if not isinstance(enabled, bool):
            return cls.unavailable(FactProblemKind.MALFORMED, source)
        feature = SubFeature(FeatureName.SNMP, "agent")
        state = FeatureState.ENABLED if enabled else FeatureState.DISABLED
        return cls.available(FeatureValue(feature, state), source)


class SnmpV3AuthenticationFact(CommandsFactDefinition[FeatureValue]):
    """Whether a local or remote SNMPv3 user has a configured authentication key."""

    key = "feature.snmpv3.authentication_key"
    label = "SNMPv3 authentication key state"
    commands = (SNMPV3_USER_COMMAND,)

    @classmethod
    # pylint: disable-next=too-many-return-statements
    def parse(cls, commands: tuple[AntaCommand, ...]) -> Fact[FeatureValue]:  # noqa: C901, PLR0911
        """Normalize SNMPv3 authentication-key presence from structured operational state."""
        (command,) = commands
        source = _feature_source(command)
        feature = SubFeature(FeatureName.SNMPV3, "authentication key")
        if is_unsupported_optional_command(command):
            return cls.available(FeatureValue(feature, FeatureState.UNSUPPORTED), source)
        if "usersByVersion" not in command.json_output:
            return cls.unavailable(FactProblemKind.MISSING, source)
        users_by_version = command.json_output["usersByVersion"]
        if not isinstance(users_by_version, Mapping):
            return cls.unavailable(FactProblemKind.MALFORMED, source)
        version = users_by_version.get("v3")
        if version is None:
            return cls.available(FeatureValue(feature, FeatureState.DISABLED), source)
        if not isinstance(version, Mapping):
            return cls.unavailable(FactProblemKind.MALFORMED, source)
        users = version.get("users")
        if users is None:
            return cls.available(FeatureValue(feature, FeatureState.DISABLED), source)
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
        return cls.available(FeatureValue(feature, state), source)


class SnmpV3CredentialSyntaxFact(CommandsFactDefinition[CredentialSyntaxValue]):
    """Storage syntax used by configured local and remote SNMPv3 credentials."""

    key = "configuration.snmpv3.credential_syntax"
    label = "SNMPv3 credential syntax"
    commands = (SNMPV3_USER_CONFIG_COMMAND,)

    @classmethod
    def parse(cls, commands: tuple[AntaCommand, ...]) -> Fact[CredentialSyntaxValue]:
        """Normalize credential syntax from the narrow SNMP user configuration output."""
        (command,) = commands
        source = _feature_source(command)
        state = _snmpv3_credential_syntax(command.text_output)
        if state is None:
            return cls.unavailable(FactProblemKind.MALFORMED, source)
        feature = SubFeature(FeatureName.SNMPV3, "credential syntax")
        return cls.available(CredentialSyntaxValue(feature, state), source)


class GnsiTransportFact(CommandsFactDefinition[FeatureValue]):
    """Effective gNSI transport state."""

    key = "feature.gnsi.transport"
    label = "gNSI transport state"
    commands = (GNSI_COMMAND,)

    @classmethod
    def parse(cls, commands: tuple[AntaCommand, ...]) -> Fact[FeatureValue]:
        """Normalize whether at least one configured gNSI transport is enabled."""
        (command,) = commands
        source = _feature_source(command)
        feature = SubFeature(FeatureName.GNSI, "transport")
        if is_unsupported_optional_command(command):
            return cls.available(FeatureValue(feature, FeatureState.UNSUPPORTED), source)

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
        return cls.available(FeatureValue(feature, state), source)


class GnsiMultipleTransportsFact(CommandsFactDefinition[FeatureValue]):
    """Presence of at least two enabled gNSI transports."""

    key = "feature.gnsi.multiple_transports"
    label = "gNSI multiple-transport state"
    commands = (GNSI_COMMAND,)

    @classmethod
    def parse(cls, commands: tuple[AntaCommand, ...]) -> Fact[FeatureValue]:
        """Normalize whether at least two configured gNSI transports are enabled."""
        (command,) = commands
        source = _feature_source(command)
        feature = SubFeature(FeatureName.GNSI, "multiple-transport mode")
        if is_unsupported_optional_command(command):
            return cls.available(FeatureValue(feature, FeatureState.UNSUPPORTED), source)

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
        return cls.available(FeatureValue(feature, state), source)


class GnsiCertzFact(CommandsFactDefinition[FeatureValue]):
    """Effective gNSI Certz service state."""

    key = "feature.gnsi.certz"
    label = "gNSI Certz service state"
    commands = (GNSI_COMMAND,)

    @classmethod
    def parse(cls, commands: tuple[AntaCommand, ...]) -> Fact[FeatureValue]:
        """Normalize the top-level Certz enablement flag."""
        (command,) = commands
        source = _feature_source(command)
        feature = SubFeature(FeatureName.GNSI, "Certz service")
        if is_unsupported_optional_command(command):
            return cls.available(FeatureValue(feature, FeatureState.UNSUPPORTED), source)

        enabled = command.json_output.get("certzEnabled")
        if enabled is None:
            return cls.unavailable(FactProblemKind.MISSING, source)
        if not isinstance(enabled, bool):
            return cls.unavailable(FactProblemKind.MALFORMED, source)
        state = FeatureState.ENABLED if enabled else FeatureState.DISABLED
        return cls.available(FeatureValue(feature, state), source)


class GnsiCredentialzFact(CommandsFactDefinition[FeatureValue]):
    """Effective gNSI Credentialz service state."""

    key = "feature.gnsi.credentialz"
    label = "gNSI Credentialz service state"
    commands = (GNSI_COMMAND,)

    @classmethod
    def parse(cls, commands: tuple[AntaCommand, ...]) -> Fact[FeatureValue]:
        """Normalize the top-level Credentialz enablement flag."""
        (command,) = commands
        source = _feature_source(command)
        feature = SubFeature(FeatureName.GNSI, "Credentialz service")
        if is_unsupported_optional_command(command):
            return cls.available(FeatureValue(feature, FeatureState.UNSUPPORTED), source)
        enabled = command.json_output.get("credentialzEnabled")
        if enabled is None:
            return cls.unavailable(FactProblemKind.MISSING, source)
        if not isinstance(enabled, bool):
            return cls.unavailable(FactProblemKind.MALFORMED, source)
        state = FeatureState.ENABLED if enabled else FeatureState.DISABLED
        return cls.available(FeatureValue(feature, state), source)


class GnsiAuthzFact(CommandsFactDefinition[FeatureValue]):
    """Effective gNSI Authz service state."""

    key = "feature.gnsi.authz"
    label = "gNSI Authz service state"
    commands = (GNSI_COMMAND,)

    @classmethod
    def parse(cls, commands: tuple[AntaCommand, ...]) -> Fact[FeatureValue]:
        """Normalize the top-level Authz enablement flag."""
        (command,) = commands
        source = _feature_source(command)
        feature = SubFeature(FeatureName.GNSI, "Authz service")
        if is_unsupported_optional_command(command):
            return cls.available(FeatureValue(feature, FeatureState.UNSUPPORTED), source)

        enabled = command.json_output.get("authzEnabled")
        if enabled is None:
            return cls.unavailable(FactProblemKind.MISSING, source)
        if not isinstance(enabled, bool):
            return cls.unavailable(FactProblemKind.MALFORMED, source)
        state = FeatureState.ENABLED if enabled else FeatureState.DISABLED
        return cls.available(FeatureValue(feature, state), source)


class GnsiAcctzFact(CommandsFactDefinition[FeatureValue]):
    """Effective gNSI Acctz service state."""

    key = "feature.gnsi.acctz"
    label = "gNSI Acctz service state"
    commands = (GNSI_COMMAND,)

    @classmethod
    def parse(cls, commands: tuple[AntaCommand, ...]) -> Fact[FeatureValue]:
        """Normalize the top-level Acctz enablement flag."""
        (command,) = commands
        source = _feature_source(command)
        feature = SubFeature(FeatureName.GNSI, "Acctz service")
        if is_unsupported_optional_command(command):
            return cls.available(FeatureValue(feature, FeatureState.UNSUPPORTED), source)
        enabled = command.json_output.get("acctzEnabled")
        if enabled is None:
            return cls.unavailable(FactProblemKind.MISSING, source)
        if not isinstance(enabled, bool):
            return cls.unavailable(FactProblemKind.MALFORMED, source)
        state = FeatureState.ENABLED if enabled else FeatureState.DISABLED
        return cls.available(FeatureValue(feature, state), source)


class GnsiPathzFact(CommandsFactDefinition[FeatureValue]):
    """Effective gNSI Pathz service state."""

    key = "feature.gnsi.pathz"
    label = "gNSI Pathz service state"
    commands = (GNSI_COMMAND,)

    @classmethod
    def parse(cls, commands: tuple[AntaCommand, ...]) -> Fact[FeatureValue]:
        """Normalize the top-level Pathz enablement flag."""
        (command,) = commands
        source = _feature_source(command)
        feature = SubFeature(FeatureName.GNSI, "Pathz service")
        if is_unsupported_optional_command(command):
            return cls.available(FeatureValue(feature, FeatureState.UNSUPPORTED), source)

        enabled = command.json_output.get("pathzEnabled")
        if enabled is None:
            return cls.unavailable(FactProblemKind.MISSING, source)
        if not isinstance(enabled, bool):
            return cls.unavailable(FactProblemKind.MALFORMED, source)
        state = FeatureState.ENABLED if enabled else FeatureState.DISABLED
        return cls.available(FeatureValue(feature, state), source)


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


class GnsiPathzPolicyOverlapFact(CommandsFactDefinition[FeatureValue]):
    """Presence of Pathz user and group rules applying to the same path."""

    key = "feature.gnsi.pathz_policy_user_group_overlap"
    label = "Pathz policy user/group overlap"
    commands = (PATHZ_POLICY_COMMAND,)

    @classmethod
    def parse(cls, commands: tuple[AntaCommand, ...]) -> Fact[FeatureValue]:
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
        feature = SubFeature(FeatureName.GNSI, "Pathz policy user/group overlap")
        state = FeatureState.ENABLED if overlap else FeatureState.DISABLED
        return cls.available(FeatureValue(feature, state), source)


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


class GnmiAuthorizationFact(CommandsFactDefinition[FeatureValue]):
    """Request authorization on at least one enabled gNMI transport."""

    key = "feature.gnmi.authorization"
    label = "gNMI request-authorization state"
    commands = (GNMI_COMMAND,)

    @classmethod
    def parse(cls, commands: tuple[AntaCommand, ...]) -> Fact[FeatureValue]:
        """Normalize authorization state across enabled transports."""
        (command,) = commands
        source = _feature_source(command)
        feature = SubFeature(FeatureName.GNMI, "request authorization")
        if is_unsupported_optional_command(command):
            return cls.available(FeatureValue(feature, FeatureState.UNSUPPORTED), source)
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
                return cls.available(FeatureValue(feature, FeatureState.ENABLED), source)
            if enabled not in {True, False} or (enabled is True and authorization not in {True, False}):
                unknown = True
        if unknown:
            return cls.unavailable(FactProblemKind.MISSING, source)
        return cls.available(FeatureValue(feature, FeatureState.DISABLED), source)


class RestconfTransportFact(CommandsFactDefinition[FeatureValue]):
    """Effective RESTCONF transport state."""

    key = "feature.restconf.transport"
    label = "RESTCONF transport state"
    commands = (RESTCONF_COMMAND,)

    @classmethod
    def parse(cls, commands: tuple[AntaCommand, ...]) -> Fact[FeatureValue]:
        """Normalize structured RESTCONF enablement."""
        (command,) = commands
        source = _feature_source(command)
        if is_unsupported_optional_command(command):
            return cls.available(FeatureValue(FeatureName.RESTCONF, FeatureState.UNSUPPORTED), source)
        if "enabled" not in command.json_output:
            return cls.unavailable(FactProblemKind.MISSING, source)
        enabled = command.json_output["enabled"]
        if not isinstance(enabled, bool):
            return cls.unavailable(FactProblemKind.MALFORMED, source)
        return cls.available(FeatureValue(FeatureName.RESTCONF, FeatureState.ENABLED if enabled else FeatureState.DISABLED), source)


class NetconfTransportFact(CommandsFactDefinition[FeatureValue]):
    """Effective NETCONF transport state."""

    key = "feature.netconf.transport"
    label = "NETCONF transport state"
    commands = (NETCONF_COMMAND,)

    @classmethod
    def parse(cls, commands: tuple[AntaCommand, ...]) -> Fact[FeatureValue]:
        """Normalize structured NETCONF enablement."""
        (command,) = commands
        source = _feature_source(command)
        if is_unsupported_optional_command(command):
            return cls.available(FeatureValue(FeatureName.NETCONF, FeatureState.UNSUPPORTED), source)
        if "enabled" not in command.json_output:
            return cls.unavailable(FactProblemKind.MISSING, source)
        enabled = command.json_output["enabled"]
        if not isinstance(enabled, bool):
            return cls.unavailable(FactProblemKind.MALFORMED, source)
        return cls.available(FeatureValue(FeatureName.NETCONF, FeatureState.ENABLED if enabled else FeatureState.DISABLED), source)


class GnpsiTransportFact(CommandsFactDefinition[FeatureValue]):
    """Effective gNPSI transport state."""

    key = "feature.gnpsi.transport"
    label = "gNPSI transport state"
    commands = (GNPSI_COMMAND,)

    @classmethod
    def parse(cls, commands: tuple[AntaCommand, ...]) -> Fact[FeatureValue]:
        """Normalize enabled transports and the explicit disabled state."""
        (command,) = commands
        source = _feature_source(command)
        feature = SubFeature(FeatureName.GNPSI, "transport")
        if is_unsupported_optional_command(command):
            return cls.available(FeatureValue(feature, FeatureState.UNSUPPORTED), source)
        config = _deserialize_gnpsi_config(command.json_output)
        if isinstance(config, FactProblemKind):
            return cls.unavailable(config, source)
        if not isinstance(config.enabled, bool):
            return cls.unavailable(FactProblemKind.MALFORMED, source)
        state = FeatureState.ENABLED if config.enabled else FeatureState.DISABLED
        return cls.available(FeatureValue(feature, state), source)


class GnpsiAuthenticationExposureFact(CommandsFactDefinition[FeatureValue]):
    """gNPSI authentication combinations exposed to request execution."""

    key = "feature.gnpsi.authentication_exposure"
    label = "gNPSI authentication exposure state"
    commands = (GNPSI_COMMAND,)

    @classmethod
    # pylint: disable-next=too-many-return-statements
    def parse(cls, commands: tuple[AntaCommand, ...]) -> Fact[FeatureValue]:  # noqa: C901, PLR0911
        """Normalize TLS metadata and mTLS common-name authentication paths."""
        (command,) = commands
        source = _feature_source(command)
        feature = SubFeature(FeatureName.GNPSI, "exposed authentication mode")
        if is_unsupported_optional_command(command):
            return cls.available(FeatureValue(feature, FeatureState.UNSUPPORTED), source)
        config = _deserialize_gnpsi_config(command.json_output)
        if isinstance(config, FactProblemKind):
            return cls.unavailable(config, source)
        if not isinstance(config.enabled, bool):
            return cls.unavailable(FactProblemKind.MALFORMED, source)
        if not config.enabled:
            return cls.available(FeatureValue(feature, FeatureState.DISABLED), source)
        if any(not isinstance(transport.enabled, bool) for transport in config.transports):
            return cls.unavailable(FactProblemKind.MALFORMED, source)
        enabled_transports = tuple(transport for transport in config.transports if transport.enabled is True)
        if not enabled_transports:
            return cls.available(FeatureValue(feature, FeatureState.DISABLED), source)
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
                return cls.available(FeatureValue(feature, FeatureState.ENABLED), source)
        if problem is not None:
            return cls.unavailable(problem, source)
        return cls.available(FeatureValue(feature, FeatureState.DISABLED), source)


class GnpsiMutualTlsSpiffeMitigationFact(CommandsFactDefinition[MitigationValue]):
    """Mutual TLS with exclusively x509-spiffe authentication on every enabled gNPSI transport."""

    key = "mitigation.gnpsi.mutual_tls_spiffe"
    label = "gNPSI mutual TLS with only x509-spiffe authentication"
    commands = (GNPSI_COMMAND,)

    @classmethod
    # pylint: disable-next=too-many-return-statements
    def parse(cls, commands: tuple[AntaCommand, ...]) -> Fact[MitigationValue]:  # noqa: C901, PLR0911
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
            return cls.available(MitigationValue(MitigationState.INEFFECTIVE), source)
        if any(not isinstance(transport.enabled, bool) for transport in config.transports):
            return cls.unavailable(FactProblemKind.MALFORMED, source)
        enabled_transports = tuple(transport for transport in config.transports if transport.enabled is True)
        if not enabled_transports:
            return cls.available(MitigationValue(MitigationState.INEFFECTIVE), source)
        problem: FactProblemKind | None = None
        for transport in enabled_transports:
            authentication = _gnpsi_authentication(transport)
            if isinstance(authentication, FactProblemKind):
                problem = authentication if problem is None or authentication is FactProblemKind.MALFORMED else problem
                continue
            security_type, methods = authentication
            if security_type not in {"mtls", "mutualtls", "tlsmutual"} or methods != {"x509-spiffe"}:
                return cls.available(MitigationValue(MitigationState.INEFFECTIVE), source)
        if problem is not None:
            return cls.unavailable(problem, source)
        return cls.available(MitigationValue(MitigationState.EFFECTIVE), source)


class GnpsiEosRpcAuthTraceFact(CommandsFactDefinition[FeatureValue]):
    """Explicit gNPSI EosRpcAuth trace state."""

    key = "feature.gnpsi.eos_rpc_auth_trace"
    label = "gNPSI EosRpcAuth trace state"
    commands = (GNPSI_TRACE_COMMAND,)

    @classmethod
    def parse(cls, commands: tuple[AntaCommand, ...]) -> Fact[FeatureValue]:
        """Normalize the explicit trace-facility status."""
        (command,) = commands
        source = _feature_source(command)
        feature = SubFeature(FeatureName.GNPSI, "EosRpcAuth trace")
        if is_unsupported_optional_command(command):
            return cls.available(FeatureValue(feature, FeatureState.UNSUPPORTED), source)
        if command.error:
            return cls.unavailable(FactProblemKind.COLLECTION_FAILED, source)
        output = command.text_output.strip()
        if not output:
            return cls.available(FeatureValue(feature, FeatureState.DISABLED), source)
        enabled = re.search(r"^EosRpcAuth\s+enabled\b", output, re.MULTILINE) is not None
        disabled = re.search(r"^EosRpcAuth\s+disabled\b", output, re.MULTILINE) is not None
        if enabled == disabled:
            return cls.unavailable(FactProblemKind.MALFORMED, source)
        return cls.available(FeatureValue(feature, FeatureState.ENABLED if enabled else FeatureState.DISABLED), source)


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


class GnmiMtlsAuthorizationFact(CommandsFactDefinition[FeatureValue]):
    """Enabled gNMI transport with both request authorization and mutual TLS."""

    key = "feature.gnmi.mtls_authorization"
    label = "gNMI mTLS request authorization state"
    commands = (GNMI_COMMAND, SSL_PROFILE_COMMAND)

    @classmethod
    def _candidates(cls, gnmi: AntaCommand) -> Fact[FeatureValue] | _GnmiAuthorizationCandidates:
        """Return candidate profiles or a result decided by gNMI output alone."""
        source = _feature_source(gnmi)
        feature = SubFeature(FeatureName.GNMI, "mTLS request authorization")
        if is_unsupported_optional_command(gnmi):
            return cls.available(FeatureValue(feature, FeatureState.UNSUPPORTED), source)
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
        return cls.available(FeatureValue(feature, FeatureState.DISABLED), source)

    @classmethod
    def _evaluate_candidates(cls, candidates: _GnmiAuthorizationCandidates, ssl: AntaCommand, gnmi: AntaCommand) -> Fact[FeatureValue]:
        """Evaluate candidate profiles and retain the command causing uncertainty."""
        ssl_source = _feature_source(ssl)
        feature = SubFeature(FeatureName.GNMI, "mTLS request authorization")
        if is_unsupported_optional_command(ssl):
            return cls.unavailable(FactProblemKind.UNSUPPORTED, ssl_source)

        states = tuple(_ssl_profile_has_mtls(profile_name, ssl.json_output) for profile_name in candidates.profile_names)
        if True in states:
            return cls.available(FeatureValue(feature, FeatureState.ENABLED), ssl_source)
        if None in states:
            return cls.unavailable(FactProblemKind.MISSING, ssl_source)
        if candidates.incomplete_transport:
            return cls.unavailable(FactProblemKind.MISSING, _feature_source(gnmi))
        return cls.available(FeatureValue(feature, FeatureState.DISABLED), ssl_source)

    @classmethod
    def parse(cls, commands: tuple[AntaCommand, ...]) -> Fact[FeatureValue]:
        """Normalize exposure without combining state from different transports."""
        gnmi, ssl = commands
        candidates = cls._candidates(gnmi)
        if not isinstance(candidates, _GnmiAuthorizationCandidates):
            return candidates
        return cls._evaluate_candidates(candidates, ssl, gnmi)


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
