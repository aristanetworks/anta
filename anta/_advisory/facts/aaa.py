# Copyright (c) 2026 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Facts derived from EOS AAA state."""

from __future__ import annotations

import re
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
    SubFeature,
)
from anta._advisory.optional_commands import OptionalAntaCommand, is_unsupported_optional_command

if TYPE_CHECKING:
    from anta.models import AntaCommand

AAA_CONFIG_COMMAND = OptionalAntaCommand(command="show running-config section aaa", ofmt="text")
AAA_METHODS_COMMAND = OptionalAntaCommand(command="show aaa methods authentication", revision=1)
COMMAND_AUTHORIZATION = re.compile(r"^aaa authorization commands (?P<levels>all|[0-9,-]+) default (?P<methods>.+)$")
RANGE_BOUNDARY_COUNT = 2


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


class LevelZeroCommandAuthorizationFact(CommandsFactDefinition[MitigationValue]):
    """Explicit privilege-level-zero command authorization without the ``none`` method."""

    key = "mitigation.aaa.level_zero_command_authorization"
    label = "AAA privilege-level-zero command authorization"
    commands = (AAA_CONFIG_COMMAND,)

    @classmethod
    def parse(cls, commands: tuple[AntaCommand, ...]) -> Fact[MitigationValue]:
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
        return cls.available(MitigationValue(state), source)


class LoginAuthenticationFact(CommandsFactDefinition[FeatureValue]):
    """Effective default login authentication state."""

    key = "feature.aaa.login_authentication"
    label = "login authentication state"
    commands = (AAA_METHODS_COMMAND,)

    @classmethod
    def parse(cls, commands: tuple[AntaCommand, ...]) -> Fact[FeatureValue]:
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
        return cls.available(FeatureValue(SubFeature(FeatureName.AAA, "login authentication"), state), source)
