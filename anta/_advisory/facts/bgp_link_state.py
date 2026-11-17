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


def _consumer_scopes(output: object, required_vrfs: set[str]) -> dict[str, _ConsumerScope | FactProblemKind] | FactProblemKind:
    """Retain independent role observations and problems for every activated VRF."""
    if not isinstance(output, Mapping):
        return FactProblemKind.MISSING if output is None else FactProblemKind.MALFORMED
    vrfs = output.get("vrfs")
    if not isinstance(vrfs, Mapping):
        return FactProblemKind.MISSING if vrfs is None else FactProblemKind.MALFORMED
    return {vrf: _consumer_scope(vrf, vrfs[vrf]) if vrf in vrfs else FactProblemKind.MISSING for vrf in sorted(required_vrfs)}


def _scope_observations(scope: BgpLinkStatePeeringScope, role: _ConsumerScope, explicit: set[tuple[str, str]]) -> tuple[BgpLinkStateScope, ...]:
    """Keep identity and role contradictions local to the activation they challenge."""
    observed = BgpLinkStateScope(scope.instance, scope.vrf, role.enabled, scope.activated_neighbors)
    if _as_number(scope.instance) != _as_number(role.instance):
        return observed, BgpLinkStateScope(role.instance, scope.vrf, role.enabled, scope.activated_neighbors)
    if (scope.instance, scope.vrf) in explicit and not role.enabled:
        return observed, BgpLinkStateScope(scope.instance, scope.vrf, consumer_dps=True, activated_neighbors=scope.activated_neighbors)
    return (observed,)


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
    def parse(cls, commands: tuple[AntaCommand, ...]) -> Fact[BgpLinkStateDpsConsumerFact]:
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
        result = cls._correlated_value(peering.value.scopes, roles, _configured_consumers(config.text_output), source)
        if not isinstance(result, UnavailableFact) and result.value.state is ConfigurationState.NOT_CONFIGURED and peering.value.uncertain_scopes:
            return cls.unavailable(FactProblemKind.MALFORMED, peering.source)
        return result

    @classmethod
    def _correlated_value(
        cls,
        activations: tuple[BgpLinkStatePeeringScope, ...],
        roles: dict[str, _ConsumerScope | FactProblemKind],
        explicit: set[tuple[str, str]],
        source: FactSource,
    ) -> Fact[BgpLinkStateDpsConsumerFact]:
        """Let a consistent consumer win; otherwise report a stable required problem."""
        scopes: list[BgpLinkStateScope] = []
        problems: set[FactProblemKind] = set()
        contradictions: list[tuple[BgpLinkStateScope, ...]] = []
        for activation in sorted(activations, key=lambda scope: (scope.instance, scope.vrf)):
            role = roles[activation.vrf]
            if isinstance(role, FactProblemKind):
                problems.add(role)
                continue
            observations = _scope_observations(activation, role, explicit)
            if len(observations) > 1:
                contradictions.append(observations)
            else:
                scopes.extend(observations)
        value = cls._scoped_value(tuple(scopes))
        if value.state is ConfigurationState.CONFIGURED:
            return value.available(source)
        if contradictions:
            return cls.unavailable(FactProblemKind.CONTRADICTORY, source, observations=tuple(cls._scoped_value((scope,)) for scope in contradictions[0]))
        if problems:
            problem = FactProblemKind.MALFORMED if FactProblemKind.MALFORMED in problems else FactProblemKind.MISSING
            return cls.unavailable(problem, source)
        return value.available(source)
