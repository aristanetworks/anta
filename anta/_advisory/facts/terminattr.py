# Copyright (c) 2026 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Facts derived from TerminAttr configuration and daemon state."""

from __future__ import annotations

import shlex
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import TYPE_CHECKING, ClassVar

from anta._advisory.facts.models import (
    CommandsFactDefinition,
    Fact,
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
)
from anta._advisory.optional_commands import OptionalAntaCommand, is_unsupported_optional_command

if TYPE_CHECKING:
    from anta.models import AntaCommand

TERMINATTR_DAEMON_COMMAND = OptionalAntaCommand(command="show daemon", revision=1)
TERMINATTR_CONFIG_COMMAND = OptionalAntaCommand(command="show running-config section grpcaddr", ofmt="text")
TERMINATTR_EXEC_PREFIX = ("exec", "/usr/bin/TerminAttr")


def _has_argument(arguments: Sequence[str], name: str) -> bool:
    """Return whether command arguments contain a valued short-form option."""
    option = f"-{name}"
    for index, argument in enumerate(arguments):
        if argument.startswith(f"{option}="):
            return bool(argument.removeprefix(f"{option}="))
        if argument == option:
            return index + 1 < len(arguments) and not arguments[index + 1].startswith("-")
    return False


def _terminattr_grpc_arguments(config_output: str) -> tuple[str, ...] | None:
    """Return arguments from the first TerminAttr exec line containing ``-grpcaddr``."""
    for line in config_output.splitlines():
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


@dataclass(frozen=True, slots=True)
class TerminAttrGrpcFact(FeatureFact, CommandsFactDefinition["TerminAttrGrpcFact"]):
    """Effective TerminAttr gRPC server state."""

    feature: ClassVar[FeatureRef] = FeatureName.TERMINATTR
    key: ClassVar[str] = "feature.terminattr.grpc"
    label: ClassVar[str] = "TerminAttr gRPC server state"
    commands: ClassVar[tuple[AntaCommand, ...]] = (TERMINATTR_DAEMON_COMMAND, TERMINATTR_CONFIG_COMMAND)

    @classmethod
    def parse(cls, commands: tuple[AntaCommand, ...]) -> Fact[TerminAttrGrpcFact]:  # noqa: PLR0911
        daemon, config = commands
        source = FactSource("show daemon and show running-config section grpcaddr", FactSourceKind.COMMAND)
        if is_unsupported_optional_command(config):
            return cls.unavailable(FactProblemKind.UNSUPPORTED, source)
        if _terminattr_grpc_arguments(config.text_output) is None:
            return cls(FeatureState.DISABLED).available(source)
        if is_unsupported_optional_command(daemon):
            return cls.unavailable(FactProblemKind.UNSUPPORTED, source)
        daemons = daemon.json_output.get("daemons")
        if not isinstance(daemons, Mapping):
            return cls.unavailable(FactProblemKind.MALFORMED, source)
        terminattr = daemons.get("TerminAttr")
        if terminattr is None:
            return cls(FeatureState.DISABLED).available(source)
        if not isinstance(terminattr, Mapping) or not isinstance((enabled := terminattr.get("enabled")), bool):
            return cls.unavailable(FactProblemKind.MALFORMED, source)
        return cls(FeatureState.ENABLED if enabled else FeatureState.DISABLED).available(source)


@dataclass(frozen=True, slots=True)
class TerminAttrMtlsFact(MitigationFact, CommandsFactDefinition["TerminAttrMtlsFact"]):
    """mTLS configuration on the TerminAttr gRPC server."""

    key: ClassVar[str] = "mitigation.terminattr.mtls"
    label: ClassVar[str] = "TerminAttr mTLS"
    commands: ClassVar[tuple[AntaCommand, ...]] = (TERMINATTR_CONFIG_COMMAND,)

    @classmethod
    def parse(cls, commands: tuple[AntaCommand, ...]) -> Fact[TerminAttrMtlsFact]:
        (command,) = commands
        source = FactSource(command.command, FactSourceKind.COMMAND)
        if is_unsupported_optional_command(command):
            return cls.unavailable(FactProblemKind.UNSUPPORTED, source)
        arguments = _terminattr_grpc_arguments(command.text_output)
        effective = arguments is not None and all(_has_argument(arguments, flag) for flag in ("certfile", "keyfile", "clientcafile"))
        state = MitigationState.EFFECTIVE if effective else MitigationState.INEFFECTIVE
        return cls(state).available(source)


@dataclass(frozen=True, slots=True)
class TerminAttrTlsConnection:
    """One configured secure CloudVision client and its explicit CA selection.

    Authentication credentials are deliberately not retained in the fact.
    ``ca_file`` records configured intent only; it does not establish effective
    trust because cached roots and fallback behavior are not observable here.
    """

    cluster: str
    addresses: tuple[str, ...]
    ca_file: str | None


# Parsing TerminAttr's command line is not this author's favorite choice.
# No supported structured interface was found that exposes effective client
# settings for every configured cluster. Runtime connection records can disappear
# when connections close, so their absence cannot prove a client is unconfigured.
# Keep this parser limited to the evidence needed by advisory assessments.
# Keep each option-validation failure mapped to its specific fact problem kind.
def _tls_client_options(arguments: Sequence[str]) -> dict[str, dict[str, str]] | FactProblemKind:  # noqa: C901
    """Normalize flat and per-cluster CloudVision address/authentication options."""
    clusters: dict[str, dict[str, str]] = {}
    primary_options: dict[str, str] = {}
    index = 0
    while index < len(arguments):
        option, separator, value = arguments[index].partition("=")
        index += 1
        if option not in {"-cvaddr", "-cvauth", "-cvopt", "--cvaddr", "--cvauth", "--cvopt"}:
            continue
        if not separator:
            if index == len(arguments) or arguments[index].startswith("-"):
                return FactProblemKind.MISSING
            value = arguments[index]
            index += 1
        name = option.lstrip("-").removeprefix("cv")
        if name == "opt":
            scoped_option, separator, value = value.partition("=")
            cluster, dot, name = scoped_option.partition(".")
            if not separator or not dot or not cluster or "." in name:
                return FactProblemKind.MALFORMED
            if name not in {"addr", "auth"}:
                continue
            if not value:
                return FactProblemKind.MISSING
            options = clusters.setdefault(cluster, {})
        else:
            options = primary_options
        if name in options:
            return FactProblemKind.INVALID
        options[name] = value
    if primary_options:
        # TerminAttr merges nonempty global fields into primary after parsing all
        # cvopt entries, so precedence does not depend on command-line order.
        clusters.setdefault("primary", {}).update({name: value for name, value in primary_options.items() if value})
    return clusters


def _tls_connections(options: Mapping[str, Mapping[str, str]]) -> tuple[TerminAttrTlsConnection, ...] | FactProblemKind:
    """Retain CA selection separately for every secure connection scope."""
    connections = []
    for cluster, values in sorted(options.items()):
        if "addr" not in values or "auth" not in values:
            return FactProblemKind.MISSING
        addresses = tuple(values["addr"].split(","))
        authentication = values["auth"].split(",")
        mode = authentication[0]
        required_count = {"token-secure": 2, "certs": 3}.get(mode)
        if required_count is None:
            return FactProblemKind.UNSUPPORTED
        if len(authentication) not in {required_count, required_count + 1} or not all(authentication) or not all(addresses):
            return FactProblemKind.MALFORMED
        ca_file = authentication[-1] if len(authentication) == required_count + 1 else None
        connections.append(TerminAttrTlsConnection(cluster, addresses, ca_file))
    return tuple(connections)


@dataclass(frozen=True, slots=True)
class TerminAttrTlsClientFact(FeatureFact, CommandsFactDefinition["TerminAttrTlsClientFact"]):
    """Persistent secure CloudVision clients, including explicit-CA configurations.

    Only ``certs`` and ``token-secure`` authentication are supported. Other
    authentication modes are unavailable, rather than being interpreted as
    absence of TLS. An explicit CA path cannot prove that cached trust and
    system-bundle fallback exclude compromised roots. Dynamic segmentation
    subscriptions (``cvconfig``) do not change client selection. Daemon running
    state and current sessions are intentionally not used to classify clients.
    """

    feature: ClassVar[SubFeature] = SubFeature(FeatureName.TERMINATTR, "CloudVision TLS client")
    key: ClassVar[str] = "feature.terminattr.tls_client"
    label: ClassVar[str] = "TerminAttr TLS client configuration"
    # A fixed component makes this observation unnecessary. Retain every failure
    # for the assessment rather than letting collection preempt that decision.
    commands: ClassVar[tuple[AntaCommand, ...]] = (OptionalAntaCommand(command="show running-configuration | section TerminAttr", ofmt="text", defer_errors=True),)
    connections: tuple[TerminAttrTlsConnection, ...] = ()

    @classmethod
    # Keep the parser's validation stages explicit so each unavailable reason stays distinct.
    # pylint: disable-next=too-many-return-statements,too-many-branches
    def parse(cls, commands: tuple[AntaCommand, ...]) -> Fact[TerminAttrTlsClientFact]:  # noqa: C901, PLR0911
        """Parse the configured daemon, including per-cluster CA boundaries."""
        (command,) = commands
        source = FactSource(command.command, FactSourceKind.COMMAND)
        if is_unsupported_optional_command(command):
            return cls.unavailable(FactProblemKind.UNSUPPORTED, source)
        if command.errors:
            return cls.unavailable(FactProblemKind.COLLECTION_FAILED, source)
        if not isinstance(command.output, str):
            return cls.unavailable(FactProblemKind.MISSING if command.output is None else FactProblemKind.MALFORMED, source)
        lines = tuple(line.strip() for line in command.text_output.splitlines() if line.strip() and line.strip() != "!")
        if not lines:
            return cls(FeatureState.DISABLED).available(source)
        if lines[0] != "daemon TerminAttr":
            return cls.unavailable(FactProblemKind.MALFORMED, source)
        if lines.count("daemon TerminAttr") != 1 or ("shutdown" in lines and "no shutdown" in lines):
            return cls.unavailable(FactProblemKind.INVALID, source)
        if "shutdown" in lines:
            return cls(FeatureState.DISABLED).available(source)
        if "no shutdown" not in lines:
            return cls.unavailable(FactProblemKind.MISSING, source)
        exec_lines = tuple(line for line in lines if line.startswith("exec "))
        if len(exec_lines) != 1:
            return cls.unavailable(FactProblemKind.MISSING if not exec_lines else FactProblemKind.INVALID, source)
        try:
            tokens = shlex.split(exec_lines[0])
        except ValueError:
            return cls.unavailable(FactProblemKind.MALFORMED, source)
        if tuple(tokens[:2]) != TERMINATTR_EXEC_PREFIX:
            return cls.unavailable(FactProblemKind.UNSUPPORTED, source)
        options = _tls_client_options(tokens[2:])
        if isinstance(options, FactProblemKind):
            return cls.unavailable(options, source)
        connections = _tls_connections(options)
        if isinstance(connections, FactProblemKind):
            return cls.unavailable(connections, source)
        state = FeatureState.ENABLED if connections else FeatureState.DISABLED
        return cls(state, connections).available(source)
