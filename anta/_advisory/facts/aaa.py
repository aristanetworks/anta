# Copyright (c) 2026 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Facts derived from EOS AAA state."""

from __future__ import annotations

import re
from collections.abc import Mapping
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

AAA_CONFIG_COMMAND = OptionalAntaCommand(command="show running-config section aaa", ofmt="text")
AAA_METHODS_COMMAND = OptionalAntaCommand(command="show aaa methods authentication", revision=1)
# Interpret all failures as unavailable observations: ``show radius`` is only needed
# for named groups, and decisive scope evidence must survive either failure.
AAA_ACCOUNTING_METHODS_COMMAND = OptionalAntaCommand(command="show aaa methods accounting", revision=1, defer_errors=True)
RADIUS_COMMAND = OptionalAntaCommand(command="show radius", revision=1, defer_errors=True)
COMMAND_AUTHORIZATION = re.compile(r"^aaa authorization commands (?P<levels>all|[0-9,-]+) default (?P<methods>.+)$")
RANGE_BOUNDARY_COUNT = 2
BUILTIN_RADIUS_GROUP = "radius"


def _includes_level_zero(expression: str) -> bool | None:
    """Return whether an EOS privilege-level expression includes level zero."""
    if expression == "all":
        return True
    for item in expression.split(","):
        if item.isdigit():
            if int(item) == 0:
                return True
            continue
        boundaries = item.split("-")
        if len(boundaries) != RANGE_BOUNDARY_COUNT or not all(value.isdigit() for value in boundaries):
            return None
        start, end = (int(value) for value in boundaries)
        if start > end:
            return None
        if start == 0:
            return True
    return False


@dataclass(frozen=True, slots=True)
class LevelZeroCommandAuthorizationFact(MitigationFact, CommandsFactDefinition["LevelZeroCommandAuthorizationFact"]):
    """Explicit privilege-level-zero command authorization without the ``none`` method."""

    key: ClassVar[str] = "mitigation.aaa.level_zero_command_authorization"
    label: ClassVar[str] = "AAA privilege-level-zero command authorization"
    commands: ClassVar[tuple[AntaCommand, ...]] = (AAA_CONFIG_COMMAND,)

    @classmethod
    def parse(cls, commands: tuple[AntaCommand, ...]) -> Fact[LevelZeroCommandAuthorizationFact]:
        """Normalize the effective default command-authorization method list for level zero."""
        (command,) = commands
        source = FactSource(command.command, FactSourceKind.COMMAND)
        if is_unsupported_optional_command(command):
            return cls.unavailable(FactProblemKind.UNSUPPORTED, source)
        applicable: list[tuple[str, ...]] = []
        for raw_line in command.text_output.splitlines():
            line = raw_line.strip()
            if not line or line == "!" or not line.startswith("aaa authorization commands "):
                continue
            match = COMMAND_AUTHORIZATION.fullmatch(line)
            if match is None:
                return cls.unavailable(FactProblemKind.MALFORMED, source)
            includes_zero = _includes_level_zero(match.group("levels"))
            if includes_zero is None:
                return cls.unavailable(FactProblemKind.MALFORMED, source)
            if includes_zero:
                applicable.append(tuple(match.group("methods").split()))
        effective = bool(applicable) and all("none" not in methods for methods in applicable)
        state = MitigationState.EFFECTIVE if effective else MitigationState.INEFFECTIVE
        return cls(state).available(source)


@dataclass(frozen=True, slots=True)
class LoginAuthenticationFact(FeatureFact, CommandsFactDefinition["LoginAuthenticationFact"]):
    """Effective default login authentication state."""

    feature: ClassVar[FeatureRef] = SubFeature(FeatureName.AAA, "login authentication")
    key: ClassVar[str] = "feature.aaa.login_authentication"
    label: ClassVar[str] = "login authentication state"
    commands: ClassVar[tuple[AntaCommand, ...]] = (AAA_METHODS_COMMAND,)

    @classmethod
    def parse(cls, commands: tuple[AntaCommand, ...]) -> Fact[LoginAuthenticationFact]:
        """Normalize whether the default login method list requires authentication."""
        (command,) = commands
        source = FactSource(command.command, FactSourceKind.COMMAND)
        if is_unsupported_optional_command(command):
            return cls.unavailable(FactProblemKind.UNSUPPORTED, source)
        login_methods = command.json_output.get("loginAuthenMethods")
        if not isinstance(login_methods, dict) or not isinstance(default := login_methods.get("default"), dict):
            return cls.unavailable(FactProblemKind.MISSING, source)
        methods = default.get("methods")
        if not isinstance(methods, list) or not methods or not all(isinstance(method, str) and method.strip() for method in methods):
            return cls.unavailable(FactProblemKind.MALFORMED, source)
        enabled = "none" not in {method.strip().lower() for method in methods}
        state = FeatureState.ENABLED if enabled else FeatureState.DISABLED
        return cls(state).available(source)


def _required_mapping(value: object) -> Mapping[str, object] | FactProblemKind:
    """Return a required JSON object or the problem preventing its use."""
    if value is None:
        return FactProblemKind.MISSING
    if not isinstance(value, Mapping):
        return FactProblemKind.MALFORMED
    return value


def _command_problem(command: AntaCommand) -> FactProblemKind | None:
    """Keep failed or unsupported collection distinct from observed accounting state."""
    if is_unsupported_optional_command(command):
        return FactProblemKind.UNSUPPORTED
    return FactProblemKind.COLLECTION_FAILED if command.errors else None


def _dot1x_accounting_groups(output: object) -> tuple[str, ...] | FactProblemKind:
    """Return the method names in the default 802.1X accounting list, without any ``group`` prefix.

    EOS 4.32 and 4.33 report group methods as ``group NAME`` while EOS 4.35 reports ``NAME``.
    """
    default_list = _required_mapping(output)
    for key in ("dot1xAcctMethods", "dot1x"):
        if isinstance(default_list, FactProblemKind):
            return default_list
        default_list = _required_mapping(default_list.get(key))
    if isinstance(default_list, FactProblemKind):
        return default_list
    methods = default_list.get("defaultMethods")
    if methods is None:
        return FactProblemKind.MISSING
    if not isinstance(methods, list) or not all(isinstance(method, str) and method.strip() for method in methods):
        return FactProblemKind.MALFORMED
    return tuple(method.strip().removeprefix("group ").strip() for method in methods)


def _radius_server_groups(output: object) -> tuple[frozenset[str], frozenset[str]] | FactProblemKind:
    """Return the names of configured RADIUS server groups and of groups whose type cannot be read."""
    radius = _required_mapping(output)
    if isinstance(radius, FactProblemKind):
        return radius
    groups = _required_mapping(radius.get("groups"))
    if isinstance(groups, FactProblemKind):
        return groups
    radius_groups: set[str] = set()
    unresolved: set[str] = set()
    for name, group in groups.items():
        if not isinstance(name, str) or not name:
            return FactProblemKind.MALFORMED
        if not isinstance(group, Mapping) or not isinstance(server_group := group.get("serverGroup"), str):
            unresolved.add(name)
        elif server_group == "RADIUS":
            radius_groups.add(name)
    return frozenset(radius_groups), frozenset(unresolved)


@dataclass(frozen=True, slots=True)
class Dot1xRadiusAccountingFact(FeatureFact, CommandsFactDefinition["Dot1xRadiusAccountingFact"]):
    """Configured 802.1X accounting through at least one RADIUS server group.

    The default 802.1X accounting list is the only 802.1X accounting list. Its built-in
    ``radius`` group counts directly; a named group counts only when ``show radius``
    reports it as a RADIUS server group. Configured RADIUS servers, server reachability,
    and the start-stop or stop-only action are not part of this fact.

    One referenced RADIUS group establishes the enabled state despite other unreadable
    groups. Without one, an unreadable referenced group leaves the fact unavailable, while
    unreadable unreferenced groups are irrelevant.
    """

    feature: ClassVar[FeatureRef] = SubFeature(FeatureName.DOT1X, "RADIUS accounting")
    key: ClassVar[str] = "feature.dot1x.radius_accounting"
    label: ClassVar[str] = "802.1X RADIUS accounting state"
    commands: ClassVar[tuple[AntaCommand, ...]] = (AAA_ACCOUNTING_METHODS_COMMAND, RADIUS_COMMAND)

    @classmethod
    def parse(cls, commands: tuple[AntaCommand, ...]) -> Fact[Dot1xRadiusAccountingFact]:
        """Resolve the default 802.1X accounting methods against configured RADIUS server groups."""
        accounting, radius = commands
        accounting_source = FactSource(accounting.command, FactSourceKind.COMMAND)
        problem = _command_problem(accounting)
        if problem is not None:
            return cls.unavailable(problem, accounting_source)
        methods = _dot1x_accounting_groups(accounting.output)
        if isinstance(methods, FactProblemKind):
            return cls.unavailable(methods, accounting_source)
        if not methods:
            return cls(FeatureState.DISABLED).available(accounting_source)
        if BUILTIN_RADIUS_GROUP in methods:
            return cls(FeatureState.ENABLED).available(accounting_source)
        return cls._resolve_named_groups(methods, radius)

    @classmethod
    def _resolve_named_groups(cls, methods: tuple[str, ...], radius: AntaCommand) -> Fact[Dot1xRadiusAccountingFact]:
        """Decide whether any named accounting method is a configured RADIUS server group."""
        radius_source = FactSource(radius.command, FactSourceKind.COMMAND)
        problem = _command_problem(radius)
        if problem is not None:
            return cls.unavailable(problem, radius_source)
        groups = _radius_server_groups(radius.output)
        if isinstance(groups, FactProblemKind):
            return cls.unavailable(groups, radius_source)
        radius_groups, unresolved = groups
        if radius_groups.intersection(methods):
            return cls(FeatureState.ENABLED).available(radius_source)
        if unresolved.intersection(methods):
            return cls.unavailable(FactProblemKind.MALFORMED, radius_source)
        return cls(FeatureState.DISABLED).available(radius_source)
