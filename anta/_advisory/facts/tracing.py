# Copyright (c) 2026 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Facts derived from EOS agent tracing."""

from __future__ import annotations

import re
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
    SubFeature,
)
from anta._advisory.optional_commands import OptionalAntaCommand, is_unsupported_optional_command

if TYPE_CHECKING:
    from anta.models import AntaCommand

TRACE_CONFIG_COMMAND = OptionalAntaCommand(command="show running-config section trace", ofmt="text")
TRACE_SETTING_PATTERN = re.compile(r"^trace (?P<agent>\S+) setting (?P<settings>\S+)$")


def _level_expression_includes(expression: str, target: int) -> bool | None:
    """Return whether an EOS trace-level expression includes one target level."""
    if expression == "*":
        return True
    if (full_range := re.fullmatch(r"(?P<start>\d+)-(?P<end>\d+)", expression)) is not None:
        start = int(full_range.group("start"))
        end = int(full_range.group("end"))
        return None if start > end else start <= target <= end
    if not expression.isdigit():
        return None
    # EOS canonicalizes separate single-digit levels as a compact string, such
    # as `levels 0 3 4` becoming `/034` in the sanitized configuration.
    return str(target) in expression


def _selector_matches(selector: str, facility: str) -> bool | None:
    """Return whether one EOS regex selector matches a trace facility."""
    if selector == "*":
        return True
    try:
        return re.search(selector, facility) is not None
    except re.error:
        return None


def _setting_enables_facility(settings: str, facility: str, level: int) -> bool | None:
    """Evaluate one effective facility level from an EOS trace setting."""
    enabled = False
    for directive in settings.split(","):
        disabled = directive.startswith("-")
        candidate = directive[1:] if disabled else directive
        selector, separator, levels = candidate.rpartition("/")
        if not separator or not selector or not levels:
            return None
        selector_matches = _selector_matches(selector, facility)
        level_matches = _level_expression_includes(levels, level)
        if selector_matches is None or level_matches is None:
            return None
        if selector_matches and level_matches:
            enabled = not disabled
    return enabled


def _trace_level_enabled(config: str, agent: str, facility: str, level: int) -> bool | None:
    """Return the effective state of one agent facility level."""
    settings: list[str] = []
    for raw_line in config.splitlines():
        line = raw_line.strip()
        if not line or line == "!" or not line.startswith(f"trace {agent} "):
            continue
        if (match := TRACE_SETTING_PATTERN.fullmatch(line)) is None:
            return None
        settings.append(match.group("settings"))
    if not settings:
        return False
    if len(settings) != 1:
        return None
    return _setting_enables_facility(settings[0], facility, level)


def _trace_levels_enabled(config: str, agent: str, facility: str, levels: tuple[int, ...]) -> bool | None:
    """Return whether any target level is enabled, retaining unknown input."""
    states = tuple(_trace_level_enabled(config, agent, facility, level) for level in levels)
    if any(state is True for state in states):
        return True
    if any(state is None for state in states):
        return None
    return False


def _parse_agent_trace(
    command: AntaCommand,
    *,
    agent: str,
    facility: str,
    levels: tuple[int, ...],
) -> tuple[FeatureState | FactProblemKind, FactSource]:
    """Normalize one advisory-specific risky trace selection."""
    source = FactSource(command.command, FactSourceKind.COMMAND)
    if is_unsupported_optional_command(command):
        return FactProblemKind.UNSUPPORTED, source
    enabled = _trace_levels_enabled(command.text_output, agent, facility, levels)
    if enabled is None:
        return FactProblemKind.MALFORMED, source
    state = FeatureState.ENABLED if enabled else FeatureState.DISABLED
    return state, source


@dataclass(frozen=True, slots=True)
class ConfigAgentPrivateKeyTraceFact(FeatureFact, CommandsFactDefinition["ConfigAgentPrivateKeyTraceFact"]):
    """Risky ConfigAgent private-key trace levels."""

    feature: ClassVar[FeatureRef] = SubFeature(FeatureName.AGENT_TRACING, "risk for ConfigAgent private keys")
    key: ClassVar[str] = "feature.agent_tracing.config_agent_private_key"
    label: ClassVar[str] = "ConfigAgent private-key trace state"
    commands: ClassVar[tuple[AntaCommand, ...]] = (TRACE_CONFIG_COMMAND,)

    @classmethod
    def parse(cls, commands: tuple[AntaCommand, ...]) -> Fact[ConfigAgentPrivateKeyTraceFact]:
        """Normalize risky ConfigAgent private-key trace levels."""
        (command,) = commands
        result, source = _parse_agent_trace(command, agent="ConfigAgent", facility="MgmtSecuritySslCertKey", levels=(0, 3, 4))
        return cls(result).available(source) if isinstance(result, FeatureState) else cls.unavailable(result, source)


@dataclass(frozen=True, slots=True)
class AaaPasswordTraceFact(FeatureFact, CommandsFactDefinition["AaaPasswordTraceFact"]):
    """Risky Aaa user-password trace level."""

    feature: ClassVar[FeatureRef] = SubFeature(FeatureName.AGENT_TRACING, "risk for Aaa user passwords")
    key: ClassVar[str] = "feature.agent_tracing.aaa_password"
    label: ClassVar[str] = "Aaa user-password trace state"
    commands: ClassVar[tuple[AntaCommand, ...]] = (TRACE_CONFIG_COMMAND,)

    @classmethod
    def parse(cls, commands: tuple[AntaCommand, ...]) -> Fact[AaaPasswordTraceFact]:
        """Normalize the risky Aaa user-password trace level."""
        (command,) = commands
        result, source = _parse_agent_trace(command, agent="Aaa", facility="PyServer", levels=(4,))
        return cls(result).available(source) if isinstance(result, FeatureState) else cls.unavailable(result, source)


@dataclass(frozen=True, slots=True)
class AaaTacacsKeyTraceFact(FeatureFact, CommandsFactDefinition["AaaTacacsKeyTraceFact"]):
    """Risky Aaa TACACS+ shared-key trace level."""

    feature: ClassVar[FeatureRef] = SubFeature(FeatureName.AGENT_TRACING, "risk for Aaa TACACS+ shared keys")
    key: ClassVar[str] = "feature.agent_tracing.aaa_tacacs_key"
    label: ClassVar[str] = "Aaa TACACS+ shared-key trace state"
    commands: ClassVar[tuple[AntaCommand, ...]] = (TRACE_CONFIG_COMMAND,)

    @classmethod
    def parse(cls, commands: tuple[AntaCommand, ...]) -> Fact[AaaTacacsKeyTraceFact]:
        """Normalize the risky Aaa TACACS+ shared-key trace level."""
        (command,) = commands
        result, source = _parse_agent_trace(command, agent="Aaa", facility="Tacacs", levels=(6,))
        return cls(result).available(source) if isinstance(result, FeatureState) else cls.unavailable(result, source)
