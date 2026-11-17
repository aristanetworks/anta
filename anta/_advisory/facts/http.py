# Copyright (c) 2026 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Configured eAPI service and management HTTP default-service settings."""

from __future__ import annotations

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


_DEFAULT_SERVICE_SECTIONS = frozenset({"management api http-commands", "management http-server"})
_GLOBAL_INDENTATION = 3


def _command_problem(command: AntaCommand) -> FactProblemKind | None:
    """Keep failed or unsupported collection distinct from observed disablement."""
    if is_unsupported_optional_command(command):
        return FactProblemKind.UNSUPPORTED
    return FactProblemKind.COLLECTION_FAILED if command.errors else None


def _default_services_line(line: str, indentation: int) -> FeatureState | FactProblemKind | None:
    """Distinguish a global setting from unrelated arguments containing its name."""
    tokens = line.split()
    if tokens[0] != "default-services" and tokens[:2] not in (["no", "default-services"], ["default", "default-services"]):
        return None
    if indentation != _GLOBAL_INDENTATION or line not in {"default-services", "no default-services"}:
        return FactProblemKind.INVALID
    return FeatureState.ENABLED if line == "default-services" else FeatureState.DISABLED


def _default_services_settings(output: object) -> tuple[FeatureState, ...] | FactProblemKind:
    """Read explicit global flags from both possible full-default carriers."""
    if not isinstance(output, str):
        return FactProblemKind.MISSING if output is None else FactProblemKind.MALFORMED
    sections: set[str] = set()
    settings: dict[str, FeatureState] = {}
    current: str | None = None
    for raw_line in output.splitlines():
        line = raw_line.strip()
        if not line or line == "!":
            continue
        indentation = len(raw_line) - len(raw_line.lstrip())
        if indentation == 0:
            if line not in _DEFAULT_SERVICE_SECTIONS or line in sections:
                return FactProblemKind.MALFORMED
            sections.add(line)
            current = line
            continue
        if current is None:
            return FactProblemKind.MALFORMED
        setting = _default_services_line(line, indentation)
        if isinstance(setting, FactProblemKind):
            return setting
        if setting is None:
            continue
        if current in settings:
            return FactProblemKind.MALFORMED
        settings[current] = setting
    return tuple(settings.values()) if settings else FactProblemKind.MISSING


@dataclass(frozen=True, slots=True)
class EapiEnabledFact(FeatureFact, CommandsFactDefinition["EapiEnabledFact"]):
    """Whether the eAPI service is configured as enabled."""

    feature: ClassVar[FeatureRef] = FeatureName.EAPI
    key: ClassVar[str] = "feature.eapi.enabled"
    label: ClassVar[str] = "eAPI service state"
    commands: ClassVar[tuple[AntaCommand, ...]] = (OptionalAntaCommand(command="show management api http-commands", revision=1, defer_errors=True),)

    @classmethod
    def parse(cls, commands: tuple[AntaCommand, ...]) -> Fact[EapiEnabledFact]:
        """Read the configured service flag without gating it on live listeners."""
        (command,) = commands
        source = FactSource(command.command, FactSourceKind.COMMAND)
        problem = _command_problem(command)
        if problem is not None:
            return cls.unavailable(problem, source)
        output = command.output
        if output is None:
            return cls.unavailable(FactProblemKind.MISSING, source)
        if not isinstance(output, dict):
            return cls.unavailable(FactProblemKind.MALFORMED, source)
        enabled = output.get("enabled")
        if enabled is None:
            return cls.unavailable(FactProblemKind.MISSING, source)
        if not isinstance(enabled, bool):
            return cls.unavailable(FactProblemKind.MALFORMED, source)
        return cls(FeatureState.ENABLED if enabled else FeatureState.DISABLED).available(source)


@dataclass(frozen=True, slots=True)
class HttpDefaultServicesFact(FeatureFact, CommandsFactDefinition["HttpDefaultServicesFact"]):
    """Explicit management HTTP default-service state from full-default configuration."""

    feature: ClassVar[FeatureRef] = SubFeature(FeatureName.HTTP_SERVER, "default services")
    key: ClassVar[str] = "feature.management_http.default_services"
    label: ClassVar[str] = "management HTTP default-service state"
    commands: ClassVar[tuple[AntaCommand, ...]] = (
        OptionalAntaCommand(
            command="show running-config all | section ^management (api http-commands|http-server)",
            ofmt="text",
            defer_errors=True,
        ),
    )

    @classmethod
    def parse(cls, commands: tuple[AntaCommand, ...]) -> Fact[HttpDefaultServicesFact]:
        """Resolve the actual carrier without interpreting an omitted flag as disabled."""
        (command,) = commands
        source = FactSource(command.command, FactSourceKind.COMMAND)
        problem = _command_problem(command)
        if problem is not None:
            return cls.unavailable(problem, source)
        settings = _default_services_settings(command.output)
        if isinstance(settings, FactProblemKind):
            return cls.unavailable(settings, source)
        if len(set(settings)) > 1:
            return cls.unavailable(FactProblemKind.CONTRADICTORY, source, observations=tuple(cls(state) for state in settings))
        return cls(settings[0]).available(source)
