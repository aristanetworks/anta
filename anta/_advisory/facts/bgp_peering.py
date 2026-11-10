# Copyright (c) 2026 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Persistent BGP Link-State activation and administrative disablement."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, ClassVar

from anta._advisory.facts.models import (
    CommandsFactDefinition,
    ConfigurationFact,
    ConfigurationState,
    Fact,
    FactProblemKind,
    FactSource,
    FactSourceKind,
    FeatureName,
    FeatureRef,
    SubFeature,
)
from anta._advisory.optional_commands import OptionalAntaCommand, is_unsupported_optional_command

if TYPE_CHECKING:
    from anta.models import AntaCommand

_BGP_CHILD_INDENT = 3


@dataclass(frozen=True, slots=True)
class BgpLinkStatePeeringScope:
    """Configured BGP instance, VRF, and administratively enabled AF activations.

    Activated names can be static neighbors or peer groups, including unused
    groups. They do not represent instantiated peers or negotiated sessions.
    """

    instance: str
    vrf: str
    activated_neighbors: tuple[str, ...]


@dataclass(slots=True)
class _Scope:
    """Administrative settings and Link-State activation in one BGP VRF."""

    malformed: bool = False
    shutdown: bool = False
    af_shutdown: bool = False
    activations: dict[str, bool] = field(default_factory=dict)
    neighbor_shutdown: dict[str, bool] = field(default_factory=dict)
    peer_groups: dict[str, str] = field(default_factory=dict)
    declared_groups: set[str] = field(default_factory=set)


@dataclass(slots=True)
class _Instance:
    """One persistent BGP hierarchy with its default and named VRF settings."""

    name: str
    malformed: bool = False
    shutdown: bool = False
    scopes: dict[str, _Scope] = field(default_factory=lambda: {"default": _Scope()})


def _scope_context(instance: _Instance, parents: tuple[str, ...]) -> tuple[str, _Scope, bool] | None:
    """Identify only direct BGP, VRF, and Link-State AF parents."""
    vrf = "default"
    remainder = parents
    if parents and parents[0].startswith("vrf "):
        vrf = parents[0].removeprefix("vrf ")
        remainder = parents[1:]
    if remainder not in ((), ("address-family link-state",)):
        return None
    scope = instance.scopes.get(vrf)
    return (vrf, scope, bool(remainder)) if scope is not None else None


def _neighbor_setting(scope: _Scope, text: str, *, address_family: bool) -> bool:
    """Record exact activation, shutdown, and peer-group membership commands."""
    setting = "activate" if address_family else "shutdown"
    match = re.fullmatch(rf"(?P<no>no )?neighbor (?P<name>\S+) {setting}", text)
    if match is not None:
        target = scope.activations if address_family else scope.neighbor_shutdown
        target[match["name"]] = match["no"] is None
        return True
    if not address_family:
        declaration = re.fullmatch(r"neighbor (?P<name>\S+) peer group", text)
        if declaration is not None:
            scope.declared_groups.add(declaration["name"])
            return True
        membership = re.fullmatch(r"neighbor (?P<name>\S+) peer group (?P<group>\S+)", text)
        if membership is not None:
            scope.peer_groups[membership["name"]] = membership["group"]
            return True
    # Incomplete forms of the settings we interpret cannot establish absence.
    words = text.removeprefix("no ").split()
    match words:
        case ["neighbor", target] | ["neighbor", _, target, *_] if target == setting:
            return False
        case _:
            return True


def _declaration(instance: _Instance, parents: tuple[str, ...], text: str) -> bool | None:
    """Validate hierarchy declarations; return None for ordinary settings."""
    if text.startswith("vrf ") or text == "vrf":
        if parents or re.fullmatch(r"vrf \S+", text) is None:
            return False
        instance.scopes.setdefault(text.removeprefix("vrf "), _Scope())
        return True
    if text.startswith("address-family"):
        valid_parent = not parents or (len(parents) == 1 and parents[0].startswith("vrf "))
        if text.startswith("address-family link-state"):
            return valid_parent and text == "address-family link-state"
        return valid_parent and re.fullmatch(r"address-family \S+(?: \S+)?", text) is not None
    return None


def _consume(instance: _Instance, parents: tuple[str, ...], text: str) -> bool:
    """Apply a direct setting without leaking across sibling hierarchies."""
    declaration = _declaration(instance, parents, text)
    if declaration is not None:
        return declaration
    context = _scope_context(instance, parents)
    if context is None:
        return True
    vrf, scope, af = context
    if text in {"shutdown", "no shutdown"}:
        disabled = text == "shutdown"
        if af:
            scope.af_shutdown = disabled
        elif vrf == "default" and not parents:
            instance.shutdown = disabled
        else:
            scope.shutdown = disabled
        return True
    valid = not text.startswith(("shutdown ", "no shutdown ")) and _neighbor_setting(scope, text, address_family=af)
    if not valid:
        # Default-VRF settings can govern the whole instance or inherited groups.
        # Other settings are confined to the identified VRF/AF scope.
        if not parents:
            instance.malformed = True
        else:
            scope.malformed = True
    return True


def _configuration(config: str) -> tuple[_Instance, ...] | None:
    """Parse the exact scoped running-config hierarchy, retaining sibling bounds."""
    instances: list[_Instance] = []
    stack: list[str] = []
    for raw in config.splitlines():
        text = raw.strip()
        if not text or text == "!":
            continue
        spaces = len(raw) - len(raw.lstrip(" "))
        if "\t" in raw[: len(raw) - len(raw.lstrip())] or spaces % _BGP_CHILD_INDENT:
            return None
        level = spaces // _BGP_CHILD_INDENT
        if level == 0:
            root = re.fullmatch(r"router bgp (?P<instance>\S+)", text)
            if root is None:
                return None
            instances.append(_Instance(root["instance"]))
            stack = [text]
            continue
        if not instances or level > len(stack):
            return None
        stack = stack[:level]
        if not _consume(instances[-1], tuple(stack[1:]), text):
            return None
        stack.append(text)
    return tuple(instances)


def _disabled(name: str, shutdown: dict[str, bool], groups: dict[str, str]) -> bool:
    """Resolve confirmed shutdown through group inheritance; cycles stay enabled."""
    visited: set[str] = set()
    while name not in visited:
        visited.add(name)
        if name in shutdown:
            return shutdown[name]
        if name not in groups:
            return False
        name = groups[name]
    return False


def _inherits(name: str, ancestor: str, groups: dict[str, str], activations: dict[str, bool]) -> bool:
    """Return whether a member inherits activation without explicit deactivation."""
    visited: set[str] = set()
    while name in groups and name not in visited:
        if activations.get(name) is False:
            return False
        visited.add(name)
        name = groups[name]
        if name == ancestor:
            return True
    return False


def _activations(instance: _Instance, scope: _Scope) -> tuple[str, ...]:
    """Retain activation unless persistent administrative disablement is proved."""
    if instance.shutdown or scope.shutdown or scope.af_shutdown:
        return ()
    default = instance.scopes["default"]
    inherited_groups = default.declared_groups - scope.declared_groups if scope is not default else default.declared_groups
    shutdown = {name: state for name, state in default.neighbor_shutdown.items() if name in inherited_groups} | scope.neighbor_shutdown
    groups = {name: group for name, group in default.peer_groups.items() if name in inherited_groups} | scope.peer_groups
    enabled: list[str] = []
    for name, active in scope.activations.items():
        if not active:
            continue
        members = (member for member in groups if _inherits(member, name, groups, scope.activations))
        if not _disabled(name, shutdown, groups) or any(not _disabled(member, shutdown, groups) for member in members):
            enabled.append(name)
    return tuple(enabled)


@dataclass(frozen=True, slots=True)
class BgpLinkStatePeeringFact(ConfigurationFact, CommandsFactDefinition["BgpLinkStatePeeringFact"]):
    """Conservative persistent Link-State AF activation, with no runtime peer gate.

    Scopes contain configured names, not runtime peer/ASN/router-ID observations.
    Uncertain scopes are retained separately so correlated consumers cannot infer
    absence from an incomplete activation inventory.
    """

    feature: ClassVar[FeatureRef] = SubFeature(FeatureName.BGP_LS, "peering")
    key: ClassVar[str] = "configuration.bgp_ls.peering"
    label: ClassVar[str] = "BGP-LS peering"
    scopes: tuple[BgpLinkStatePeeringScope, ...] = ()
    uncertain_scopes: tuple[tuple[str, str], ...] = ()
    commands: ClassVar[tuple[AntaCommand, ...]] = (
        OptionalAntaCommand(command="show running-config | section router bgp", ofmt="text", revision=1, defer_errors=True),
    )

    @classmethod
    def parse(cls, commands: tuple[AntaCommand, ...]) -> Fact[BgpLinkStatePeeringFact]:
        """Derive AF activation solely from persistent configuration."""
        (command,) = commands
        source = FactSource(command.command, FactSourceKind.COMMAND)
        if command.error:
            problem = FactProblemKind.UNSUPPORTED if is_unsupported_optional_command(command) else FactProblemKind.COLLECTION_FAILED
            return cls.unavailable(problem, source)
        if command.output is None:
            return cls.unavailable(FactProblemKind.MISSING, source)
        if not isinstance(command.output, str):
            return cls.unavailable(FactProblemKind.MALFORMED, source)
        instances = _configuration(command.output)
        if instances is None:
            return cls.unavailable(FactProblemKind.MALFORMED, source)
        scopes = tuple(
            BgpLinkStatePeeringScope(instance.name, vrf, names)
            for instance in instances
            for vrf, scope in instance.scopes.items()
            if not instance.malformed and not scope.malformed and (names := _activations(instance, scope))
        )
        uncertain_scopes = tuple((instance.name, vrf) for instance in instances for vrf, scope in instance.scopes.items() if instance.malformed or scope.malformed)
        if uncertain_scopes and not scopes:
            return cls.unavailable(FactProblemKind.MALFORMED, source)
        state = ConfigurationState.CONFIGURED if scopes else ConfigurationState.NOT_CONFIGURED
        return cls(state, scopes, uncertain_scopes).available(source)
