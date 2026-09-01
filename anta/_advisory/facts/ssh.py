# Copyright (c) 2026 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Facts derived from EOS management SSH configuration."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from anta._advisory.facts.models import (
    CommandFactDefinition,
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
GLOBAL_INDENTATION = 3
VRF_INDENTATION = 6


@dataclass
class _SshConfigState:
    """Track effective global and per-VRF SSH shutdown state."""

    global_enabled: bool = True
    global_state_seen: bool = False
    vrf_states: dict[str, bool] = field(default_factory=dict)
    vrf_state_seen: set[str] = field(default_factory=set)

    def set_global_state(self, directive: str) -> bool:
        """Apply one global state directive."""
        if self.global_state_seen:
            return False
        self.global_enabled = directive == SSH_ENABLED_DIRECTIVE
        self.global_state_seen = True
        return True

    def add_vrf(self, name: str) -> bool:
        """Add one explicitly configured VRF."""
        if not name or name in self.vrf_states:
            return False
        self.vrf_states[name] = True
        return True

    def set_vrf_state(self, name: str, directive: str) -> bool:
        """Apply one VRF state directive."""
        if name in self.vrf_state_seen:
            return False
        self.vrf_states[name] = directive == SSH_ENABLED_DIRECTIVE
        self.vrf_state_seen.add(name)
        return True

    def accepts_connections(self) -> bool:
        """Return whether any global or VRF listener remains enabled."""
        return any(self.vrf_states.values()) or self.global_enabled


def _parse_ssh_listener_state(config_output: str) -> bool | None:  # noqa: C901, PLR0911
    """Infer whether SSH accepts connections from its narrow configuration section."""
    lines = [line for line in config_output.splitlines() if line.strip() not in {"", "!"}]
    if not lines:
        return True
    if lines[0].strip() != "management ssh":
        return None

    state = _SshConfigState()
    current_vrf: str | None = None
    for raw_line in lines[1:]:
        line = raw_line.strip()
        indentation = len(raw_line) - len(raw_line.lstrip())
        if indentation == GLOBAL_INDENTATION:
            if line in SSH_SHUTDOWN_DIRECTIVES:
                current_vrf = None
                if not state.set_global_state(line):
                    return None
            elif line.startswith("vrf "):
                current_vrf = line.removeprefix("vrf ").strip()
                if not state.add_vrf(current_vrf):
                    return None
            else:
                current_vrf = None
        elif indentation == VRF_INDENTATION and current_vrf is not None:
            if line in SSH_SHUTDOWN_DIRECTIVES and not state.set_vrf_state(current_vrf, line):
                return None
        elif line in SSH_SHUTDOWN_DIRECTIVES or indentation < GLOBAL_INDENTATION:
            return None
    return state.accepts_connections()


def _parse_strict_host_key_checking(config_output: str) -> bool | None:
    """Return the effective strict host-key checking state from the SSH section."""
    lines = [line for line in config_output.splitlines() if line.strip() not in {"", "!"}]
    if not lines:
        return False
    if lines[0].strip() != "management ssh":
        return None

    state: bool | None = None
    for raw_line in lines[1:]:
        line = raw_line.strip()
        indentation = len(raw_line) - len(raw_line.lstrip())
        if indentation < GLOBAL_INDENTATION:
            return None
        if line not in {"hostkey client strict-checking", "no hostkey client strict-checking"}:
            continue
        if indentation != GLOBAL_INDENTATION or state is not None:
            return None
        state = line == "hostkey client strict-checking"
    return state if state is not None else False


class SshServerFact(CommandFactDefinition[FeatureValue]):
    """Effective management SSH listener state."""

    key = "feature.ssh.server"
    label = "SSH server state"
    command = SSH_CONFIG_COMMAND

    @classmethod
    def parse(cls, command: AntaCommand) -> Fact[FeatureValue]:
        source = FactSource(command.command, FactSourceKind.COMMAND)
        if is_unsupported_optional_command(command):
            return cls.unavailable(FactProblemKind.UNSUPPORTED, source)
        enabled = _parse_ssh_listener_state(command.text_output)
        if enabled is None:
            return cls.unavailable(FactProblemKind.MALFORMED, source)
        state = FeatureState.ENABLED if enabled else FeatureState.DISABLED
        return cls.available(FeatureValue(FeatureName.SSH, state), source)


class StrictHostKeyCheckingFact(CommandFactDefinition[MitigationValue]):
    """Effective SSH client strict host-key checking state."""

    key = "mitigation.ssh.strict_host_key_checking"
    label = "SSH client strict host-key checking"
    command = SSH_CONFIG_COMMAND

    @classmethod
    def parse(cls, command: AntaCommand) -> Fact[MitigationValue]:
        source = FactSource(command.command, FactSourceKind.COMMAND)
        if is_unsupported_optional_command(command):
            return cls.unavailable(FactProblemKind.UNSUPPORTED, source)
        if _parse_ssh_listener_state(command.text_output) is None:
            return cls.unavailable(FactProblemKind.MALFORMED, source)
        enabled = _parse_strict_host_key_checking(command.text_output)
        if enabled is None:
            return cls.unavailable(FactProblemKind.MALFORMED, source)
        state = MitigationState.EFFECTIVE if enabled else MitigationState.INEFFECTIVE
        return cls.available(MitigationValue("SSH client strict host-key checking", state), source)
