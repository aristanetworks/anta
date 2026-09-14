# Copyright (c) 2026 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Facts derived from management-access configuration."""

from __future__ import annotations

from dataclasses import dataclass, field
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
    SubFeature,
)
from anta._advisory.optional_commands import OptionalAntaCommand, is_unsupported_optional_command

if TYPE_CHECKING:
    from anta.models import AntaCommand

SSH_CONFIG_COMMAND = OptionalAntaCommand(command="show running-config section management ssh", ofmt="text")
TELNET_CONFIG_COMMAND = OptionalAntaCommand(command="show running-config section management telnet", ofmt="text")
PASSWORD_PROTOCOLS = frozenset({"keyboard-interactive", "password"})
DEFAULT_SSH_PROTOCOLS = frozenset({"keyboard-interactive", "public-key"})
GLOBAL_INDENTATION = 3
VRF_INDENTATION = 6


@dataclass(slots=True)
class _ServiceConfig:
    """Normalized narrow configuration for one management service."""

    global_enabled: bool
    vrfs: dict[str, bool] = field(default_factory=dict)
    protocols: frozenset[str] = frozenset()


# pylint: disable-next=too-many-return-statements,too-many-branches
def _parse_service_config(output: str, service: str) -> _ServiceConfig | None:  # noqa: C901, PLR0911, PLR0912
    """Parse SSH or Telnet without collecting all-default configuration."""
    default_enabled = service == "ssh"
    default_protocols = DEFAULT_SSH_PROTOCOLS if service == "ssh" else frozenset()
    lines = [line for line in output.splitlines() if line.strip() not in {"", "!"}]
    if not lines:
        return _ServiceConfig(default_enabled, protocols=default_protocols)
    if lines[0].strip() != f"management {service}":
        return None

    config = _ServiceConfig(default_enabled, protocols=default_protocols)
    global_state_seen = False
    protocols_seen = False
    current_vrf: str | None = None
    vrf_state_seen: set[str] = set()
    for raw_line in lines[1:]:
        line = raw_line.strip()
        indentation = len(raw_line) - len(raw_line.lstrip())
        if indentation == GLOBAL_INDENTATION:
            current_vrf = None
            if line.startswith("vrf "):
                current_vrf = line.removeprefix("vrf ").strip()
                if not current_vrf or current_vrf in config.vrfs:
                    return None
                config.vrfs[current_vrf] = True
            elif line in {"shutdown", "no shutdown"}:
                if global_state_seen:
                    return None
                config.global_enabled = line == "no shutdown"
                global_state_seen = True
            elif line.startswith("authentication protocol "):
                if service != "ssh" or protocols_seen:
                    return None
                protocols = line.removeprefix("authentication protocol ").split()
                if not protocols:
                    return None
                config.protocols = frozenset(protocols)
                protocols_seen = True
            continue
        if indentation == VRF_INDENTATION and current_vrf is not None and line in {"shutdown", "no shutdown"}:
            if current_vrf in vrf_state_seen:
                return None
            config.vrfs[current_vrf] = line == "no shutdown"
            vrf_state_seen.add(current_vrf)
        elif line in {"shutdown", "no shutdown"} or indentation < GLOBAL_INDENTATION:
            return None
    return config


def _enabled_in_configured_scope(config: _ServiceConfig, *, all_vrfs_by_default: bool) -> bool:
    """Return whether a service is configured as enabled in at least one VRF scope."""
    if all_vrfs_by_default and config.vrfs:
        return any(config.vrfs.values())
    return config.global_enabled or any(config.vrfs.values())


class PasswordManagementServiceFact(CommandsFactDefinition[FeatureValue]):
    """Password-capable SSH or Telnet service configured in at least one VRF scope."""

    key = "feature.management.password_service"
    label = "password-based management service state"
    commands = (SSH_CONFIG_COMMAND, TELNET_CONFIG_COMMAND)

    @classmethod
    def parse(cls, commands: tuple[AntaCommand, ...]) -> Fact[FeatureValue]:
        """Normalize SSH protocols and configured SSH/Telnet VRF scope."""
        ssh_command, telnet_command = commands
        for command in commands:
            if is_unsupported_optional_command(command):
                return cls.unavailable(FactProblemKind.UNSUPPORTED, FactSource(command.command, FactSourceKind.COMMAND))

        ssh_source = FactSource(ssh_command.command, FactSourceKind.COMMAND)
        ssh = _parse_service_config(ssh_command.text_output, "ssh")
        if ssh is None:
            return cls.unavailable(FactProblemKind.MALFORMED, ssh_source)

        telnet_source = FactSource(telnet_command.command, FactSourceKind.COMMAND)
        telnet = _parse_service_config(telnet_command.text_output, "telnet")
        if telnet is None:
            return cls.unavailable(FactProblemKind.MALFORMED, telnet_source)

        ssh_enabled = False
        if PASSWORD_PROTOCOLS.intersection(ssh.protocols):
            ssh_enabled = _enabled_in_configured_scope(ssh, all_vrfs_by_default=True)
        telnet_enabled = _enabled_in_configured_scope(telnet, all_vrfs_by_default=False)
        state = FeatureState.ENABLED if ssh_enabled or telnet_enabled else FeatureState.DISABLED
        source = FactSource(", ".join(command.command for command in commands), FactSourceKind.COMMAND)
        return cls.available(FeatureValue(SubFeature(FeatureName.AAA, "password-based management service"), state), source)
