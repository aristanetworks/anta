# Copyright (c) 2026 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Facts derived from TerminAttr configuration and daemon state."""

from __future__ import annotations

import shlex
from collections.abc import Mapping, Sequence
from typing import TYPE_CHECKING

from anta._advisory.facts.models import (
    CommandsFactDefinition,
    Fact,
    FactProblemKind,
    FactSource,
    FactSourceKind,
    FeatureName,
    FeatureState,
    FeatureValue,
    MitigationState,
    MitigationValue,
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


class TerminAttrGrpcFact(CommandsFactDefinition[FeatureValue]):
    """Effective TerminAttr gRPC server state."""

    key = "feature.terminattr.grpc"
    label = "TerminAttr gRPC server state"
    commands = (TERMINATTR_DAEMON_COMMAND, TERMINATTR_CONFIG_COMMAND)

    @classmethod
    def parse(cls, commands: tuple[AntaCommand, ...]) -> Fact[FeatureValue]:  # noqa: PLR0911
        daemon, config = commands
        source = FactSource("show daemon and show running-config section grpcaddr", FactSourceKind.COMMAND)
        if is_unsupported_optional_command(config):
            return cls.unavailable(FactProblemKind.UNSUPPORTED, source)
        if _terminattr_grpc_arguments(config.text_output) is None:
            return cls.available(FeatureValue(FeatureName.TERMINATTR, FeatureState.DISABLED), source)
        if is_unsupported_optional_command(daemon):
            return cls.unavailable(FactProblemKind.UNSUPPORTED, source)
        daemons = daemon.json_output.get("daemons")
        if not isinstance(daemons, Mapping):
            return cls.unavailable(FactProblemKind.MALFORMED, source)
        terminattr = daemons.get("TerminAttr")
        if terminattr is None:
            return cls.available(FeatureValue(FeatureName.TERMINATTR, FeatureState.DISABLED), source)
        if not isinstance(terminattr, Mapping) or not isinstance((enabled := terminattr.get("enabled")), bool):
            return cls.unavailable(FactProblemKind.MALFORMED, source)
        return cls.available(FeatureValue(FeatureName.TERMINATTR, FeatureState.ENABLED if enabled else FeatureState.DISABLED), source)


class TerminAttrMtlsFact(CommandsFactDefinition[MitigationValue]):
    """mTLS configuration on the TerminAttr gRPC server."""

    key = "mitigation.terminattr.mtls"
    label = "TerminAttr mTLS"
    commands = (TERMINATTR_CONFIG_COMMAND,)

    @classmethod
    def parse(cls, commands: tuple[AntaCommand, ...]) -> Fact[MitigationValue]:
        (command,) = commands
        source = FactSource(command.command, FactSourceKind.COMMAND)
        if is_unsupported_optional_command(command):
            return cls.unavailable(FactProblemKind.UNSUPPORTED, source)
        arguments = _terminattr_grpc_arguments(command.text_output)
        effective = arguments is not None and all(_has_argument(arguments, flag) for flag in ("certfile", "keyfile", "clientcafile"))
        state = MitigationState.EFFECTIVE if effective else MitigationState.INEFFECTIVE
        return cls.available(MitigationValue(state), source)
