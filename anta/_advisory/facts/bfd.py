# Copyright (c) 2026 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Facts derived from BFD administrative state and persistent configuration."""

from __future__ import annotations

import re
from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, ClassVar, TypeVar, cast

from anta._advisory.facts.models import (
    CommandsFactDefinition,
    Fact,
    FactDefinition,
    FactProblemKind,
    FactSource,
    FactSourceKind,
    FeatureFact,
    FeatureName,
    FeatureRef,
    FeatureState,
    SubFeature,
    UnavailableFact,
)
from anta._advisory.optional_commands import OptionalAntaCommand, is_unsupported_optional_command

if TYPE_CHECKING:
    from anta.models import AntaCommand

# EOS does not render S-BFD configuration in JSON; the section filter also returns unrelated blocks with nested `sbfd` lines.
SBFD_CONFIG_COMMAND = OptionalAntaCommand(command="show running-config section sbfd", ofmt="text", defer_errors=True)
_SBFD_REFLECTOR = re.compile(r"^reflector local-discriminator (?P<discriminator>\d{1,3}(?:\.\d{1,3}){3}|\d+)(?P<proxy> proxy)?$")
_SBFD_ROUND_TRIP_DELAY = re.compile(r"^initiator measurement delay round-trip(?:\s.*)?$")


@dataclass(frozen=True, slots=True)
class _ConfigNode:
    """One configuration line and its indented children."""

    line: str
    children: tuple[_ConfigNode, ...]


@dataclass(slots=True)
class _ConfigNodeBuilder:
    """Mutable configuration node used while reading indented lines."""

    line: str
    indent: int
    children: list[_ConfigNodeBuilder] = field(default_factory=list)

    def freeze(self) -> _ConfigNode:
        """Return the immutable node."""
        return _ConfigNode(self.line, tuple(child.freeze() for child in self.children))


def _config_tree(config: str) -> tuple[_ConfigNode, ...] | None:
    """Return the indentation hierarchy of text configuration, or ``None`` when it cannot be nested."""
    root = _ConfigNodeBuilder("", -1)
    stack = [root]
    for raw_line in config.splitlines():
        line = raw_line.strip()
        if not line or line == "!":
            continue
        indent = len(raw_line) - len(raw_line.lstrip(" "))
        while indent <= stack[-1].indent:
            stack.pop()
        if indent > 0 and stack[-1] is root:
            return None
        node = _ConfigNodeBuilder(line, indent)
        stack[-1].children.append(node)
        stack.append(node)
    return root.freeze().children


def _at_most_one(nodes: tuple[_ConfigNode, ...], line: str) -> tuple[_ConfigNode, ...] | None:
    """Return the nodes rendered with one line, or ``None`` when that line is repeated."""
    matches = tuple(node for node in nodes if node.line == line)
    return matches if len(matches) <= 1 else None


def _router_bfd_mode(config: str, submode: str) -> tuple[_ConfigNode, ...] | None:
    """Return the nodes configured in one ``router bfd`` submode, or ``None`` when its boundaries cannot be interpreted.

    An absent ``router bfd`` block or submode has no configured children.
    """
    tree = _config_tree(config)
    router_bfd = _at_most_one(tree, "router bfd") if tree is not None else None
    modes = _at_most_one(router_bfd[0].children, submode) if router_bfd else router_bfd
    if modes is None:
        return None
    return tuple(child for mode in modes for child in mode.children)


def _sbfd_mode(command: AntaCommand) -> tuple[_ConfigNode, ...] | FactProblemKind:
    """Return the collected ``router bfd`` S-BFD mode settings, or the problem that prevents reading them."""
    if is_unsupported_optional_command(command):
        return FactProblemKind.UNSUPPORTED
    if command.errors:
        return FactProblemKind.COLLECTION_FAILED
    if not isinstance(command.output, str):
        return FactProblemKind.MISSING if command.output is None else FactProblemKind.MALFORMED
    mode = _router_bfd_mode(command.output, "sbfd")
    return FactProblemKind.MALFORMED if mode is None else mode


@dataclass(frozen=True, slots=True)
class SbfdReflectorProxyFact(FeatureFact, CommandsFactDefinition["SbfdReflectorProxyFact"]):
    """Persistent S-BFD reflector configured to respond on behalf of another endpoint.

    A reflector without the ``proxy`` keyword, or no reflector, is disabled. Operational S-BFD sessions are not consulted.
    EOS retains a single reflector local discriminator, so repeated reflector discriminators are not an EOS output shape.
    Unrelated S-BFD lines do not affect this fact, but unrecognized nesting in the S-BFD mode prevents proving the proxy absent.
    """

    local_discriminator: str | None = None
    feature: ClassVar[FeatureRef] = SubFeature(FeatureName.SBFD, "reflector proxy")
    key: ClassVar[str] = "feature.sbfd.reflector_proxy"
    label: ClassVar[str] = "S-BFD reflector proxy state"
    commands: ClassVar[tuple[AntaCommand, ...]] = (SBFD_CONFIG_COMMAND,)

    @classmethod
    def parse(cls, commands: tuple[AntaCommand, ...]) -> Fact[SbfdReflectorProxyFact]:
        """Normalize the reflector local discriminator and its proxy keyword."""
        (command,) = commands
        source = FactSource(command.command, FactSourceKind.COMMAND)
        mode = _sbfd_mode(command)
        if isinstance(mode, FactProblemKind):
            return cls.unavailable(mode, source)
        reflectors = [node for node in mode if node.line.startswith("reflector local-discriminator")]
        reflector = _SBFD_REFLECTOR.fullmatch(reflectors[0].line) if len(reflectors) == 1 and not reflectors[0].children else None
        if reflectors and reflector is None:
            return cls.unavailable(FactProblemKind.MALFORMED, source)
        discriminator = reflector.group("discriminator") if reflector is not None else None
        if reflector is not None and reflector.group("proxy") is not None:
            return cls(FeatureState.ENABLED, discriminator).available(source)
        if any(node.children for node in mode):
            return cls.unavailable(FactProblemKind.MALFORMED, source)
        return cls(FeatureState.DISABLED, discriminator).available(source)


@dataclass(frozen=True, slots=True)
class SbfdInitiatorRoundTripDelayFact(FeatureFact, CommandsFactDefinition["SbfdInitiatorRoundTripDelayFact"]):
    """Persistent S-BFD initiator round-trip delay measurement. Operational S-BFD sessions are not consulted.

    Unrelated S-BFD lines do not affect this fact, but an unrecognized initiator measurement or unrecognized nesting in the S-BFD mode
    prevents proving the measurement absent.
    """

    feature: ClassVar[FeatureRef] = SubFeature(FeatureName.SBFD, "initiator round-trip delay measurement")
    key: ClassVar[str] = "feature.sbfd.initiator_round_trip_delay"
    label: ClassVar[str] = "S-BFD initiator round-trip delay measurement state"
    commands: ClassVar[tuple[AntaCommand, ...]] = (SBFD_CONFIG_COMMAND,)

    @classmethod
    def parse(cls, commands: tuple[AntaCommand, ...]) -> Fact[SbfdInitiatorRoundTripDelayFact]:
        """Normalize the initiator round-trip delay measurement setting."""
        (command,) = commands
        source = FactSource(command.command, FactSourceKind.COMMAND)
        mode = _sbfd_mode(command)
        if isinstance(mode, FactProblemKind):
            return cls.unavailable(mode, source)
        measurements = [node for node in mode if node.line.startswith("initiator measurement")]
        if any(not node.children and _SBFD_ROUND_TRIP_DELAY.fullmatch(node.line) for node in measurements):
            return cls(FeatureState.ENABLED).available(source)
        if measurements or any(node.children for node in mode):
            return cls.unavailable(FactProblemKind.MALFORMED, source)
        return cls(FeatureState.DISABLED).available(source)


BFD_SUMMARY_COMMAND = OptionalAntaCommand(command="show bfd peers summary", defer_errors=True)
BFD_GLOBAL_CONFIG_COMMAND = OptionalAntaCommand(command=r"show running-config sanitized section ^router\sbfd$", ofmt="text", defer_errors=True)
BFD_INTERFACE_AUTH_CONFIG_COMMAND = OptionalAntaCommand(
    command=r"show running-config sanitized section ^\s+bfd\sauthentication\smode\s", ofmt="text", defer_errors=True
)
_BFD_GLOBAL_AUTHENTICATION = re.compile(r"authentication[ \t]+mode[ \t]+(?P<mode>\S+)(?:[ \t]+.*)?", flags=re.IGNORECASE)
_BFD_INTERFACE_AUTHENTICATION = re.compile(r"bfd[ \t]+authentication[ \t]+mode[ \t]+(?P<mode>\S+)(?:[ \t]+.*)?", flags=re.IGNORECASE)
_KEYED_MODES = frozenset({"md5", "sha1"})


def _bfd_global_authentication_configured(config: str, modes: frozenset[str] | None = None) -> bool | None:
    """Match every non-disabled authentication mode by default, or only the supplied modes."""
    lines = tuple(line.strip() for line in config.splitlines() if line.strip())
    if lines and lines[0] != "router bfd":
        return None
    malformed = False
    for line in lines[1:]:
        if (match := _BFD_GLOBAL_AUTHENTICATION.fullmatch(line)) is not None:
            mode = match.group("mode").casefold()
            if mode != "disabled" and (modes is None or mode in modes):
                return True
        elif re.match(r"authentication\b", line):
            malformed = True
    return None if malformed else False


def _bfd_interface_authentication_configured(config: str, modes: frozenset[str] | None = None) -> bool | None:
    """Match interface authentication, accepting every non-disabled mode by default."""
    present = False
    malformed = False
    parent = ""
    child_indent: int | None = None
    for raw in config.splitlines():
        line = raw.strip()
        if not line or line == "!":
            continue
        indent = len(raw) - len(raw.lstrip(" \t"))
        if indent == 0:
            parent = line
            child_indent = None
            malformed |= not line.startswith(("router ", "interface", "management "))
            continue
        child_indent = indent if child_indent is None else min(child_indent, indent)
        if not re.match(r"bfd[ \t]+authentication\b", line):
            continue
        if re.fullmatch(r"interface[ \t]+\S+", parent) is None or indent != child_indent:
            malformed |= not parent or parent.startswith("interface")
        elif (match := _BFD_INTERFACE_AUTHENTICATION.fullmatch(line)) is None:
            malformed = True
        else:
            mode = match.group("mode").casefold()
            present |= mode != "disabled" and (modes is None or mode in modes)
    return True if present else None if malformed else False


def _command_problem(command: AntaCommand) -> FactProblemKind | None:
    """Retain the reason a command cannot supply evidence."""
    if is_unsupported_optional_command(command):
        return FactProblemKind.UNSUPPORTED
    if command.errors:
        return FactProblemKind.COLLECTION_FAILED
    return FactProblemKind.MISSING if command.output is None else None


def _bfd_configuration(command: AntaCommand, *, interface: bool, modes: frozenset[str] | None = None) -> bool | FactProblemKind:
    """Read one independently collected persistent authentication scope."""
    problem = _command_problem(command)
    if problem is not None:
        return problem
    if not isinstance(command.output, str):
        return FactProblemKind.MALFORMED
    parser = _bfd_interface_authentication_configured if interface else _bfd_global_authentication_configured
    configured = parser(command.output, modes)
    return FactProblemKind.MALFORMED if configured is None else configured


_BfdFactT = TypeVar("_BfdFactT", "BfdAuthenticationFact", "BfdKeyedAuthenticationFact")


@dataclass(frozen=True, slots=True)
class BfdAuthenticationUnavailableFact(UnavailableFact[_BfdFactT]):
    """Retain each required BFD command failure without changing the shared fact model."""

    additional_problems: tuple[UnavailableFact[_BfdFactT], ...] = ()

    @property
    def problems(self) -> tuple[UnavailableFact[_BfdFactT], ...]:
        """Expose the primary and remaining required problems to assessments."""
        return (self, *self.additional_problems)


def _bfd_authentication(definition: type[_BfdFactT], commands: tuple[AntaCommand, ...], modes: frozenset[str] | None = None) -> Fact[_BfdFactT]:
    """Combine administrative state and configuration, retaining every required failure."""
    summary, global_config, interface_config = commands
    summary_problem = _command_problem(summary)
    admin_down = summary.output.get("adminDown") if isinstance(summary.output, Mapping) else None
    summary_source = FactSource(summary.command, FactSourceKind.COMMAND)
    if summary_problem is FactProblemKind.UNSUPPORTED:
        return definition(FeatureState.UNSUPPORTED).available(summary_source)
    if summary_problem is None and admin_down is True:
        return definition(FeatureState.DISABLED).available(summary_source)
    global_state = _bfd_configuration(global_config, interface=False, modes=modes)
    interface_state = _bfd_configuration(interface_config, interface=True, modes=modes)
    observations = ((global_state, global_config), (interface_state, interface_config))
    witness = next((command for configured, command in observations if configured is True), None)
    if global_state is False and interface_state is False:
        return definition(FeatureState.DISABLED).available(FactSource(interface_config.command, FactSourceKind.COMMAND))
    # Both nominal BFD classes bind FactDefinition to themselves; preserve that relation through the constrained type variable.
    fact_definition = cast("type[FactDefinition[_BfdFactT]]", definition)
    problems: list[UnavailableFact[_BfdFactT]] = []
    if summary_problem is None and not isinstance(admin_down, bool):
        summary_problem = FactProblemKind.MISSING if admin_down is None else FactProblemKind.MALFORMED
    if summary_problem is not None:
        problems.append(UnavailableFact[_BfdFactT](definition=fact_definition, problem=summary_problem, source=summary_source))
    if witness is not None:
        if not problems:
            return definition(FeatureState.ENABLED).available(FactSource(witness.command, FactSourceKind.COMMAND))
    else:
        problems.extend(
            UnavailableFact[_BfdFactT](definition=fact_definition, problem=configured, source=FactSource(command.command, FactSourceKind.COMMAND))
            for configured, command in observations
            if isinstance(configured, FactProblemKind)
        )
    first, *remaining = problems
    return BfdAuthenticationUnavailableFact[_BfdFactT](definition=fact_definition, problem=first.problem, source=first.source, additional_problems=tuple(remaining))


@dataclass(frozen=True, slots=True)
class BfdAuthenticationFact(FeatureFact, CommandsFactDefinition["BfdAuthenticationFact"]):
    """Configured BFD authentication while BFD is administratively enabled."""

    feature: ClassVar[FeatureRef] = SubFeature(FeatureName.BFD, "authentication")
    key: ClassVar[str] = "feature.bfd.authentication"
    label: ClassVar[str] = "BFD authentication state"
    commands: ClassVar[tuple[AntaCommand, ...]] = (BFD_SUMMARY_COMMAND, BFD_GLOBAL_CONFIG_COMMAND, BFD_INTERFACE_AUTH_CONFIG_COMMAND)

    @classmethod
    def parse(cls, commands: tuple[AntaCommand, ...]) -> Fact[BfdAuthenticationFact]:
        """Include every non-disabled mode, without requiring live peers."""
        return _bfd_authentication(cls, commands)


@dataclass(frozen=True, slots=True)
class BfdKeyedAuthenticationFact(FeatureFact, CommandsFactDefinition["BfdKeyedAuthenticationFact"]):
    """Configured MD5/SHA1 BFD authentication while BFD is administratively enabled."""

    feature: ClassVar[FeatureRef] = SubFeature(FeatureName.BFD, "keyed MD5/SHA1 authentication")
    key: ClassVar[str] = "feature.bfd.keyed_authentication"
    label: ClassVar[str] = "BFD keyed MD5/SHA1 authentication state"
    commands: ClassVar[tuple[AntaCommand, ...]] = BfdAuthenticationFact.commands

    @classmethod
    def parse(cls, commands: tuple[AntaCommand, ...]) -> Fact[BfdKeyedAuthenticationFact]:
        """Restrict the shared configuration parser to keyed modes."""
        return _bfd_authentication(cls, commands, modes=_KEYED_MODES)
