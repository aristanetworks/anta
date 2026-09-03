# Copyright (c) 2026 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Facts derived from EOS management SSH configuration."""

from __future__ import annotations

from dataclasses import dataclass
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

SSH_CONFIG_COMMAND = OptionalAntaCommand(command="show running-config section management ssh", ofmt="text")
SSH_SHUTDOWN_DIRECTIVES = {"shutdown", "no shutdown"}
SSH_ENABLED_DIRECTIVE = "no shutdown"
SSH_STRICT_CHECKING_DIRECTIVES = {"hostkey client strict-checking", "no hostkey client strict-checking"}
SSH_STRICT_CHECKING_ENABLED_DIRECTIVE = "hostkey client strict-checking"
GLOBAL_INDENTATION = 3
VRF_INDENTATION = 6


@dataclass(frozen=True, slots=True)
class _SshVrfConfig:
    """One deserialized management SSH VRF stanza."""

    name: str
    directives: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class _SshConfig:
    """Deserialized management SSH section without fact-specific interpretation."""

    global_directives: tuple[str, ...]
    vrfs: tuple[_SshVrfConfig, ...]


def _deserialize_ssh_config(config_output: str) -> _SshConfig | None:
    """Deserialize the management SSH hierarchy while preserving its directives."""
    lines = [line for line in config_output.splitlines() if line.strip() not in {"", "!"}]
    if not lines:
        return _SshConfig(global_directives=(), vrfs=())
    if lines[0].strip() != "management ssh":
        return None

    global_directives: list[str] = []
    vrfs: list[tuple[str, list[str]]] = []
    in_vrf = False
    for raw_line in lines[1:]:
        line = raw_line.strip()
        indentation = len(raw_line) - len(raw_line.lstrip())
        if indentation == GLOBAL_INDENTATION:
            if line == "vrf" or line.startswith("vrf "):
                vrfs.append((line.removeprefix("vrf").strip(), []))
                in_vrf = True
            else:
                global_directives.append(line)
                in_vrf = False
        elif indentation == VRF_INDENTATION and in_vrf:
            vrfs[-1][1].append(line)
        else:
            return None
    return _SshConfig(global_directives=tuple(global_directives), vrfs=tuple(_SshVrfConfig(name, tuple(directives)) for name, directives in vrfs))


def _ssh_listener_enabled(config: _SshConfig) -> bool | None:
    """Interpret the effective listener state from deserialized SSH configuration."""
    global_states = [directive for directive in config.global_directives if directive in SSH_SHUTDOWN_DIRECTIVES]
    if len(global_states) > 1:
        return None
    global_enabled = not global_states or global_states[0] == SSH_ENABLED_DIRECTIVE

    vrf_states: dict[str, bool] = {}
    for vrf in config.vrfs:
        if not vrf.name or vrf.name in vrf_states:
            return None
        states = [directive for directive in vrf.directives if directive in SSH_SHUTDOWN_DIRECTIVES]
        if len(states) > 1:
            return None
        vrf_states[vrf.name] = not states or states[0] == SSH_ENABLED_DIRECTIVE
    return global_enabled or any(vrf_states.values())


def _strict_host_key_checking_enabled(config: _SshConfig) -> bool | None:
    """Interpret strict host-key checking from deserialized SSH configuration."""
    if any(directive in SSH_STRICT_CHECKING_DIRECTIVES for vrf in config.vrfs for directive in vrf.directives):
        return None
    states = [directive for directive in config.global_directives if directive in SSH_STRICT_CHECKING_DIRECTIVES]
    if len(states) > 1:
        return None
    return bool(states and states[0] == SSH_STRICT_CHECKING_ENABLED_DIRECTIVE)


class SshServerFact(CommandsFactDefinition[FeatureValue]):
    """Effective management SSH listener state."""

    key = "feature.ssh.server"
    label = "SSH server state"
    commands = (SSH_CONFIG_COMMAND,)

    @classmethod
    def parse(cls, commands: tuple[AntaCommand, ...]) -> Fact[FeatureValue]:
        (command,) = commands
        source = FactSource(command.command, FactSourceKind.COMMAND)
        if is_unsupported_optional_command(command):
            return cls.unavailable(FactProblemKind.UNSUPPORTED, source)
        config = _deserialize_ssh_config(command.text_output)
        if config is None:
            return cls.unavailable(FactProblemKind.MALFORMED, source)
        enabled = _ssh_listener_enabled(config)
        if enabled is None:
            return cls.unavailable(FactProblemKind.MALFORMED, source)
        state = FeatureState.ENABLED if enabled else FeatureState.DISABLED
        return cls.available(FeatureValue(FeatureName.SSH, state), source)


class StrictHostKeyCheckingFact(CommandsFactDefinition[MitigationValue]):
    """Effective SSH client strict host-key checking state."""

    key = "mitigation.ssh.strict_host_key_checking"
    label = "SSH client strict host-key checking"
    commands = (SSH_CONFIG_COMMAND,)

    @classmethod
    def parse(cls, commands: tuple[AntaCommand, ...]) -> Fact[MitigationValue]:
        (command,) = commands
        source = FactSource(command.command, FactSourceKind.COMMAND)
        if is_unsupported_optional_command(command):
            return cls.unavailable(FactProblemKind.UNSUPPORTED, source)
        config = _deserialize_ssh_config(command.text_output)
        if config is None:
            return cls.unavailable(FactProblemKind.MALFORMED, source)
        enabled = _strict_host_key_checking_enabled(config)
        if enabled is None:
            return cls.unavailable(FactProblemKind.MALFORMED, source)
        state = MitigationState.EFFECTIVE if enabled else MitigationState.INEFFECTIVE
        return cls.available(MitigationValue("SSH client strict host-key checking", state), source)
