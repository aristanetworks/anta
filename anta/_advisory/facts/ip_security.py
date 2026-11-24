# Copyright (c) 2026 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Facts derived from configured EOS IPsec controllers and SA policies."""

from __future__ import annotations

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
    SubFeature,
)
from anta._advisory.optional_commands import OptionalAntaCommand, is_unsupported_optional_command

if TYPE_CHECKING:
    from anta.models import AntaCommand

KEY_CONTROLLER_COMMAND = OptionalAntaCommand(command="show ip security key controller local", revision=1, defer_errors=True)
SECURITY_ASSOCIATION_COMMAND = OptionalAntaCommand(command="show ip security security-association", revision=1, defer_errors=True)


def _command_problem(command: AntaCommand) -> FactProblemKind | None:
    """Distinguish unsupported, failed, absent, and malformed command output."""
    if is_unsupported_optional_command(command):
        return FactProblemKind.UNSUPPORTED
    if command.errors:
        return FactProblemKind.COLLECTION_FAILED
    if command.output is None:
        return FactProblemKind.MISSING
    if not isinstance(command.output, Mapping):
        return FactProblemKind.MALFORMED
    return None


def _replay_window(policy: object) -> int | FactProblemKind:
    """Deserialize one policy's configured replay window."""
    if not isinstance(policy, Mapping):
        return FactProblemKind.MALFORMED
    window = policy.get("replayWindowSize")
    if window is None:
        return FactProblemKind.MISSING
    if not isinstance(window, int) or isinstance(window, bool) or window < 0:
        return FactProblemKind.MALFORMED
    return window


@dataclass(frozen=True, slots=True)
class IpsecKeyControllerFact(FeatureFact, CommandsFactDefinition["IpsecKeyControllerFact"]):
    """Local controller presence, independent of selected profile or key activity."""

    feature: ClassVar[FeatureRef] = SubFeature(FeatureName.IPSEC, "key controller")
    key: ClassVar[str] = "feature.ipsec.key_controller"
    label: ClassVar[str] = "IPsec key controller state"
    commands: ClassVar[tuple[AntaCommand, ...]] = (KEY_CONTROLLER_COMMAND,)

    @classmethod
    def parse(cls, commands: tuple[AntaCommand, ...]) -> Fact[IpsecKeyControllerFact]:
        """Treat an empty JSON root as absent and a nonempty controller object as configured."""
        (command,) = commands
        source = FactSource(command.command, FactSourceKind.COMMAND)
        if problem := _command_problem(command):
            return cls.unavailable(problem, source)
        output = command.json_output
        if not output:
            return cls(FeatureState.DISABLED).available(source)
        if "keyController" not in output:
            return cls.unavailable(FactProblemKind.MISSING, source)
        controller = output["keyController"]
        if not isinstance(controller, Mapping):
            return cls.unavailable(FactProblemKind.MALFORMED, source)
        if not controller:
            return cls.unavailable(FactProblemKind.MISSING, source)
        return cls(FeatureState.ENABLED).available(source)


@dataclass(frozen=True, slots=True)
class IpsecSaAntiReplayFact(FeatureFact, CommandsFactDefinition["IpsecSaAntiReplayFact"]):
    """Whether any configured SA policy enables anti-replay detection."""

    feature: ClassVar[FeatureRef] = SubFeature(FeatureName.IPSEC, "SA policy anti-replay detection")
    key: ClassVar[str] = "feature.ipsec.sa_policy.anti_replay"
    label: ClassVar[str] = "IPsec SA policy anti-replay detection state"
    commands: ClassVar[tuple[AntaCommand, ...]] = (SECURITY_ASSOCIATION_COMMAND,)

    @classmethod
    def parse(cls, commands: tuple[AntaCommand, ...]) -> Fact[IpsecSaAntiReplayFact]:
        """Retain any complete positive policy even alongside unrelated bad entries."""
        (command,) = commands
        source = FactSource(command.command, FactSourceKind.COMMAND)
        if problem := _command_problem(command):
            return cls.unavailable(problem, source)
        policies = command.json_output.get("ipsecSecurityAssociations")
        if not isinstance(policies, Mapping):
            return cls.unavailable(FactProblemKind.MISSING if policies is None else FactProblemKind.MALFORMED, source)
        windows = tuple(_replay_window(policy) if isinstance(name, str) and name.strip() else FactProblemKind.MALFORMED for name, policy in policies.items())
        if any(isinstance(window, int) and window > 0 for window in windows):
            return cls(FeatureState.ENABLED).available(source)
        problems = {window for window in windows if isinstance(window, FactProblemKind)}
        if problems:
            problem = FactProblemKind.MALFORMED if FactProblemKind.MALFORMED in problems else FactProblemKind.MISSING
            return cls.unavailable(problem, source)
        return cls(FeatureState.DISABLED).available(source)
