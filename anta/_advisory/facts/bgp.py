# Copyright (c) 2026 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""BGP instance presence, listen ports, address-family activation, and routing protocol model."""

from __future__ import annotations

import re
from collections.abc import Mapping
from dataclasses import dataclass
from typing import TYPE_CHECKING, ClassVar

from anta._advisory.facts.models import (
    CommandsFactDefinition,
    ConfigurationFact,
    ConfigurationState,
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

_DEFAULT_BGP_PORT = 179
_LISTEN_PORT_KEYS = {"bgpIpv4ListenPort": "IPv4", "bgpIpv6ListenPort": "IPv6"}
_ACTIVATE = re.compile(r"neighbor \S+ activate")
_BGP_RUNNING_CONFIG = OptionalAntaCommand(command="show running-config | section router bgp", ofmt="text", revision=1, defer_errors=True)


def _source(command: AntaCommand) -> FactSource:
    """Preserve the exact command responsible for an observation."""
    return FactSource(command.command, FactSourceKind.COMMAND)


def _json(command: AntaCommand) -> dict[str, object] | FactProblemKind:
    """Read JSON without treating failed or missing collection as absence."""
    if command.error:
        return FactProblemKind.UNSUPPORTED if is_unsupported_optional_command(command) else FactProblemKind.COLLECTION_FAILED
    if command.output is None:
        return FactProblemKind.MISSING
    return command.output if isinstance(command.output, dict) else FactProblemKind.MALFORMED


def _text(command: AntaCommand) -> str | FactProblemKind:
    """Read text without treating failed or missing collection as absence."""
    if command.error:
        return FactProblemKind.UNSUPPORTED if is_unsupported_optional_command(command) else FactProblemKind.COLLECTION_FAILED
    if command.output is None:
        return FactProblemKind.MISSING
    return command.output if isinstance(command.output, str) else FactProblemKind.MALFORMED


def _bgp_inactive(command: AntaCommand) -> bool:
    """Return whether every command error is the EOS response for no active BGP instance."""
    return command.error and all(error.strip() in {"BGP inactive", "% BGP inactive"} for error in command.errors)


@dataclass(frozen=True, slots=True)
class BgpInstanceFact(FeatureFact, CommandsFactDefinition["BgpInstanceFact"]):
    """Presence of a BGP instance in any VRF, independent of peer/session counts."""

    feature: ClassVar[FeatureRef] = FeatureName.BGP
    key: ClassVar[str] = "feature.bgp.instances"
    label: ClassVar[str] = "BGP instance presence"
    commands: ClassVar[tuple[AntaCommand, ...]] = (OptionalAntaCommand(command="show bgp instance vrf all", ofmt="text", defer_errors=True),)

    @classmethod
    def parse(cls, commands: tuple[AntaCommand, ...]) -> Fact[BgpInstanceFact]:
        """Recognize instances or complete absence using text supported by older EOS."""
        (command,) = commands
        source = _source(command)
        if command.error:
            problem = FactProblemKind.UNSUPPORTED if is_unsupported_optional_command(command) else FactProblemKind.COLLECTION_FAILED
            return cls(FeatureState.DISABLED).available(source) if _bgp_inactive(command) else cls.unavailable(problem, source)
        output = command.output
        if output is None:
            return cls.unavailable(FactProblemKind.MISSING, source)
        if not isinstance(output, str):
            return cls.unavailable(FactProblemKind.MALFORMED, source)
        if re.search(r"^BGP instance information for VRF \S+[ \t]*$", output, re.MULTILINE):
            return cls(FeatureState.ENABLED).available(source)
        lines = tuple(line.strip() for line in output.splitlines() if line.strip())
        if all(re.fullmatch(r"BGP is disabled for VRF \S+(?: \([^()\r\n]+\))?", line) for line in lines):
            return cls(FeatureState.DISABLED).available(source)
        return cls.unavailable(FactProblemKind.MALFORMED, source)


@dataclass(frozen=True, slots=True)
class MultiAgentRoutingFact(FeatureFact, CommandsFactDefinition["MultiAgentRoutingFact"]):
    """Whether the configured or operating routing protocol model is multi-agent."""

    feature: ClassVar[FeatureRef] = SubFeature(FeatureName.ROUTING_MODEL, "multi-agent")
    key: ClassVar[str] = "feature.routing_model.multi_agent"
    label: ClassVar[str] = "multi-agent routing protocol model"
    commands: ClassVar[tuple[AntaCommand, ...]] = (OptionalAntaCommand(command="show ip route summary", revision=3, defer_errors=True),)

    @classmethod
    def parse(cls, commands: tuple[AntaCommand, ...]) -> Fact[MultiAgentRoutingFact]:
        """Require both models to be ribd before establishing multi-agent absence."""
        (command,) = commands
        source = _source(command)
        output = _json(command)
        if isinstance(output, FactProblemKind):
            return cls.unavailable(output, source)
        if "protoModelStatus" not in output:
            return cls.unavailable(FactProblemKind.MISSING, source)
        status = output["protoModelStatus"]
        if not isinstance(status, dict):
            return cls.unavailable(FactProblemKind.MALFORMED, source)
        state = _routing_model_state(status)
        return cls.unavailable(state, source) if isinstance(state, FactProblemKind) else cls(state).available(source)


def _routing_model_state(status: dict[str, object]) -> FeatureState | FactProblemKind:
    """Preserve a known multi-agent model despite an unavailable companion observation."""
    keys = ("configuredProtoModel", "operatingProtoModel")
    models = tuple(status.get(key) for key in keys)
    if "multi-agent" in models:
        return FeatureState.ENABLED
    if any(key not in status for key in keys):
        return FactProblemKind.MISSING
    if not all(isinstance(model, str) for model in models):
        return FactProblemKind.MALFORMED
    return FeatureState.DISABLED if models == ("ribd", "ribd") else FactProblemKind.INVALID


@dataclass(frozen=True, slots=True)
class BgpListenPort:
    """A BGP listen port other than TCP 179 reported for one VRF and address family."""

    vrf: str
    address_family: str
    port: int


def _non_default_ports(vrfs: Mapping[str, object]) -> tuple[tuple[BgpListenPort, ...], FactProblemKind | None]:
    """Collect valid non-default ports from every VRF and address family, and the most severe unreadable port."""
    ports: list[BgpListenPort] = []
    problem: FactProblemKind | None = None
    for vrf, instance in vrfs.items():
        if not isinstance(instance, Mapping):
            problem = FactProblemKind.MALFORMED
            continue
        for key, family in _LISTEN_PORT_KEYS.items():
            port = instance.get(key)
            if port is None:
                problem = problem or FactProblemKind.MISSING
            elif isinstance(port, bool) or not isinstance(port, int):
                problem = FactProblemKind.MALFORMED
            elif port != _DEFAULT_BGP_PORT:
                ports.append(BgpListenPort(str(vrf), family, port))
    return tuple(ports), problem


@dataclass(frozen=True, slots=True)
class BgpNonDefaultListenPortFact(ConfigurationFact, CommandsFactDefinition["BgpNonDefaultListenPortFact"]):
    """BGP listen ports other than TCP 179 reported for any VRF and address family.

    Only VRFs where BGP is running are reported: the EOS `BGP inactive` response or an empty VRF list, as with a missing
    router ID, establishes absence. A global `shutdown` hides only the default VRF; named VRFs keep reporting their ports.

    A valid non-default port establishes the configuration even when another VRF or address family is unreadable; ``problem``
    then records that ``ports`` may be incomplete. Without such a port, any unreadable VRF or address family is unavailable.
    """

    feature: ClassVar[FeatureRef] = SubFeature(FeatureName.BGP, "non-default listen port")
    key: ClassVar[str] = "configuration.bgp.listen_port.non_default"
    label: ClassVar[str] = "BGP listen port"
    ports: tuple[BgpListenPort, ...] = ()
    problem: FactProblemKind | None = None
    commands: ClassVar[tuple[AntaCommand, ...]] = (OptionalAntaCommand(command="show bgp instance vrf all", revision=3, defer_errors=True),)

    @classmethod
    def parse(cls, commands: tuple[AntaCommand, ...]) -> Fact[BgpNonDefaultListenPortFact]:
        """Prefer a valid non-default port; otherwise require both listen ports in every VRF before establishing absence."""
        (command,) = commands
        source = _source(command)
        if _bgp_inactive(command):
            return cls(ConfigurationState.NOT_CONFIGURED).available(source)
        output = _json(command)
        if isinstance(output, FactProblemKind):
            return cls.unavailable(output, source)
        vrfs = output.get("vrfs")
        if not isinstance(vrfs, Mapping):
            return cls.unavailable(FactProblemKind.MISSING if vrfs is None else FactProblemKind.MALFORMED, source)
        ports, problem = _non_default_ports(vrfs)
        if ports:
            return cls(ConfigurationState.CONFIGURED, ports, problem).available(source)
        if problem is not None:
            return cls.unavailable(problem, source)
        return cls(ConfigurationState.NOT_CONFIGURED).available(source)


def _activated(config: str, address_families: tuple[str, ...]) -> tuple[str, ...]:
    """Return the target address families with any `neighbor <name> activate` beneath them, at any depth of the BGP configuration."""
    activated: set[str] = set()
    family: str | None = None
    family_indent = 0
    for raw in config.splitlines():
        text = raw.strip()
        if not text or text == "!":
            continue
        indent = len(raw) - len(raw.lstrip())
        if family is not None and indent <= family_indent:
            family = None
        if text.startswith("address-family ") and text.removeprefix("address-family ") in address_families:
            family, family_indent = text.removeprefix("address-family "), indent
        elif family is not None and _ACTIVATE.fullmatch(text):
            activated.add(family)
    return tuple(address_family for address_family in address_families if address_family in activated)


def _parse_activation(commands: tuple[AntaCommand, ...], address_families: tuple[str, ...]) -> tuple[FactSource, tuple[str, ...] | FactProblemKind]:
    """Read the scoped BGP running configuration; empty output means no BGP configuration."""
    (command,) = commands
    text = _text(command)
    return _source(command), text if isinstance(text, FactProblemKind) else _activated(text, address_families)


@dataclass(frozen=True, slots=True)
class BgpPathSelectionActivationFact(ConfigurationFact, CommandsFactDefinition["BgpPathSelectionActivationFact"]):
    """Any neighbor or peer group activated in the BGP path-selection address family.

    Peer-group membership and neighbor, VRF, or BGP shutdown are not evaluated.
    """

    feature: ClassVar[FeatureRef] = SubFeature(FeatureName.BGP, "path-selection address family")
    key: ClassVar[str] = "configuration.bgp.address_family.path_selection"
    label: ClassVar[str] = "BGP path-selection address-family activation"
    address_families: ClassVar[tuple[str, ...]] = ("path-selection",)
    activated: tuple[str, ...] = ()
    commands: ClassVar[tuple[AntaCommand, ...]] = (_BGP_RUNNING_CONFIG,)

    @classmethod
    def parse(cls, commands: tuple[AntaCommand, ...]) -> Fact[BgpPathSelectionActivationFact]:
        """Derive activation solely from the scoped BGP running configuration."""
        source, activated = _parse_activation(commands, cls.address_families)
        if isinstance(activated, FactProblemKind):
            return cls.unavailable(activated, source)
        return cls(ConfigurationState.CONFIGURED if activated else ConfigurationState.NOT_CONFIGURED, activated).available(source)


@dataclass(frozen=True, slots=True)
class BgpSrTeActivationFact(ConfigurationFact, CommandsFactDefinition["BgpSrTeActivationFact"]):
    """Any neighbor or peer group activated in the BGP IPv4 or IPv6 SR-TE address family, globally or in a VRF.

    Peer-group membership and neighbor, VRF, or BGP shutdown are not evaluated.
    """

    feature: ClassVar[FeatureRef] = SubFeature(FeatureName.BGP, "SR-TE address family")
    key: ClassVar[str] = "configuration.bgp.address_family.sr_te"
    label: ClassVar[str] = "BGP SR-TE address-family activation"
    address_families: ClassVar[tuple[str, ...]] = ("ipv4 sr-te", "ipv6 sr-te")
    activated: tuple[str, ...] = ()
    commands: ClassVar[tuple[AntaCommand, ...]] = (_BGP_RUNNING_CONFIG,)

    @classmethod
    def parse(cls, commands: tuple[AntaCommand, ...]) -> Fact[BgpSrTeActivationFact]:
        """Derive activation solely from the scoped BGP running configuration."""
        source, activated = _parse_activation(commands, cls.address_families)
        if isinstance(activated, FactProblemKind):
            return cls.unavailable(activated, source)
        return cls(ConfigurationState.CONFIGURED if activated else ConfigurationState.NOT_CONFIGURED, activated).available(source)
