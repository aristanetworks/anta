# Copyright (c) 2026 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Persistent BGP Link-State activation correlated with its DPS consumer role."""

from __future__ import annotations

import re
from collections.abc import Mapping
from dataclasses import dataclass
from typing import TYPE_CHECKING, ClassVar

from anta._advisory.facts.bgp_peering import BgpLinkStatePeeringFact, BgpLinkStatePeeringScope
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
    UnavailableFact,
)
from anta._advisory.optional_commands import OptionalAntaCommand, is_unsupported_optional_command

if TYPE_CHECKING:
    from anta.models import AntaCommand

_BGP_CHILD_INDENT = 3
_AS_COMPONENT_MAX = 65535
_AS_MAX = 4294967295


@dataclass(frozen=True, slots=True)
class BgpLinkStateScope:
    """Configured AF activations and consumer role in one BGP instance/VRF."""

    instance: str
    vrf: str
    consumer_dps: bool
    activated_neighbors: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class _ConsumerScope:
    """One typed role and the configured instance identity reported by EOS."""

    instance: str
    vrf: str
    enabled: bool


def _as_number(value: object) -> int | None:
    """Normalize numeric and asdot ASNs without guessing an instance identity."""
    if isinstance(value, bool) or not isinstance(value, (str, int)):
        return None
    text = str(value)
    if re.fullmatch(r"[0-9]+", text):
        number = int(text)
        return number if number <= _AS_MAX else None
    match = re.fullmatch(r"([0-9]+)\.([0-9]+)", text)
    if match is None:
        return None
    high, low = int(match[1]), int(match[2])
    return high * (_AS_COMPONENT_MAX + 1) + low if max(high, low) <= _AS_COMPONENT_MAX else None


def _configured_consumers(config: str) -> set[tuple[str, str]]:
    """Retain explicit DPS consumer roles within their persistent scopes."""
    consumers: set[tuple[str, str]] = set()
    instance, vrf = "", "default"
    family_indent: int | None = None
    for raw in config.splitlines():
        text = raw.strip()
        indent = len(raw) - len(raw.lstrip())
        if not text or text == "!":
            continue
        if indent == 0:
            instance, vrf, family_indent = text.removeprefix("router bgp "), "default", None
        elif indent == _BGP_CHILD_INDENT:
            vrf = text.removeprefix("vrf ") if text.startswith("vrf ") else "default"
        if family_indent is not None and indent <= family_indent:
            family_indent = None
        if text == "address-family link-state":
            family_indent = indent
        elif family_indent is not None and text.startswith("path-selection role ") and "consumer" in text.split()[2:]:
            consumers.add((instance, vrf))
    return consumers


def _role_value(link_state: object) -> bool | FactProblemKind:  # noqa: PLR0911
    """Read typed revision-three roles, including the valid empty AF object."""
    if not isinstance(link_state, Mapping):
        return FactProblemKind.MALFORMED
    if not link_state:
        return False
    roles = link_state.get("bgpLsProtoRoles")
    if roles is None:
        return FactProblemKind.MISSING
    if not isinstance(roles, list):
        return FactProblemKind.MALFORMED
    enabled = False
    for role in roles:
        if not isinstance(role, Mapping):
            return FactProblemKind.MALFORMED
        if "role" not in role or "protocol" not in role:
            return FactProblemKind.MISSING
        if not isinstance(role["role"], str) or not isinstance(role["protocol"], str):
            return FactProblemKind.MALFORMED
        enabled |= role["role"] == "consumer" and role["protocol"] == "dps"
    return enabled


def _consumer_scope(vrf: str, output: object) -> _ConsumerScope | FactProblemKind:
    """Validate configured role identity without requiring an operational router ID."""
    if not isinstance(output, Mapping):
        return FactProblemKind.MALFORMED
    asn, families = output.get("localAs"), output.get("afiSafiConfig")
    if asn is None or families is None:
        return FactProblemKind.MISSING
    if _as_number(asn) is None or not isinstance(families, Mapping):
        return FactProblemKind.MALFORMED
    if "linkState" not in families:
        return FactProblemKind.MISSING
    role = _role_value(families["linkState"])
    return role if isinstance(role, FactProblemKind) else _ConsumerScope(str(asn), vrf, role)


def _consumer_scopes(output: object, required_vrfs: set[str]) -> dict[str, _ConsumerScope] | FactProblemKind:
    """Require complete role coverage only for persistently activated scopes."""
    if not isinstance(output, Mapping):
        return FactProblemKind.MISSING if output is None else FactProblemKind.MALFORMED
    vrfs = output.get("vrfs")
    if not isinstance(vrfs, Mapping):
        return FactProblemKind.MISSING if vrfs is None else FactProblemKind.MALFORMED
    if not required_vrfs.issubset(vrfs):
        return FactProblemKind.MISSING
    scopes: dict[str, _ConsumerScope] = {}
    for vrf in required_vrfs:
        scope = _consumer_scope(vrf, vrfs[vrf])
        if isinstance(scope, FactProblemKind):
            return scope
        scopes[vrf] = scope
    return scopes


def _correlate(activations: tuple[BgpLinkStatePeeringScope, ...], roles: dict[str, _ConsumerScope], *, role_identity: bool = False) -> tuple[BgpLinkStateScope, ...]:
    """Retain the configured and structured observations of the same scopes."""
    return tuple(
        BgpLinkStateScope(roles[scope.vrf].instance if role_identity else scope.instance, scope.vrf, roles[scope.vrf].enabled, scope.activated_neighbors)
        for scope in activations
    )


@dataclass(frozen=True, slots=True)
class BgpLinkStateDpsConsumerFact(ConfigurationFact, CommandsFactDefinition["BgpLinkStateDpsConsumerFact"]):
    """Persistent Link-State activation and DPS consumer role in the same scope."""

    feature: ClassVar[FeatureRef] = SubFeature(FeatureName.BGP_LS, "DPS consumer peering")
    key: ClassVar[str] = "configuration.bgp_ls.dps_consumer_peering"
    label: ClassVar[str] = "BGP-LS DPS consumer peering"
    scopes: tuple[BgpLinkStateScope, ...] = ()
    commands: ClassVar[tuple[AntaCommand, ...]] = (
        OptionalAntaCommand(command="show running-config | section router bgp", ofmt="text", revision=1, defer_errors=True),
        OptionalAntaCommand(command="show bgp instance vrf all", revision=3, defer_errors=True),
    )

    @classmethod
    def _scoped_value(cls, scopes: tuple[BgpLinkStateScope, ...]) -> BgpLinkStateDpsConsumerFact:
        """Preserve full scoped observations, including contradictory ones."""
        state = ConfigurationState.CONFIGURED if any(scope.consumer_dps and scope.activated_neighbors for scope in scopes) else ConfigurationState.NOT_CONFIGURED
        return cls(state, scopes)

    @classmethod
    def parse(cls, commands: tuple[AntaCommand, ...]) -> Fact[BgpLinkStateDpsConsumerFact]:  # noqa: PLR0911
        """Correlate persistent AF activation with typed configured consumer roles."""
        config, instance = commands
        peering = BgpLinkStatePeeringFact.parse((config,))
        if isinstance(peering, UnavailableFact):
            return cls.unavailable(peering.problem, peering.source)
        if peering.value.state is ConfigurationState.NOT_CONFIGURED:
            return cls(ConfigurationState.NOT_CONFIGURED).available(peering.source)
        source = FactSource(instance.command, FactSourceKind.COMMAND)
        if instance.error:
            kind = FactProblemKind.UNSUPPORTED if is_unsupported_optional_command(instance) else FactProblemKind.COLLECTION_FAILED
            return cls.unavailable(kind, source)
        roles = _consumer_scopes(instance.output, {scope.vrf for scope in peering.value.scopes})
        if isinstance(roles, FactProblemKind):
            return cls.unavailable(roles, source)
        scopes = _correlate(peering.value.scopes, roles)
        if any(_as_number(scope.instance) != _as_number(roles[scope.vrf].instance) for scope in peering.value.scopes):
            observed_scopes = _correlate(peering.value.scopes, roles, role_identity=True)
            return cls.unavailable(FactProblemKind.CONTRADICTORY, source, observations=(cls._scoped_value(scopes), cls._scoped_value(observed_scopes)))
        explicit = _configured_consumers(config.text_output)
        if any((scope.instance, scope.vrf) in explicit and not scope.consumer_dps for scope in scopes):
            configured_scopes = tuple(
                BgpLinkStateScope(scope.instance, scope.vrf, scope.consumer_dps or (scope.instance, scope.vrf) in explicit, scope.activated_neighbors)
                for scope in scopes
            )
            return cls.unavailable(FactProblemKind.CONTRADICTORY, source, observations=(cls._scoped_value(scopes), cls._scoped_value(configured_scopes)))
        return cls._scoped_value(scopes).available(source)
