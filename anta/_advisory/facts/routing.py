# Copyright (c) 2026 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Facts derived from EOS routing protocol state and configuration."""

from __future__ import annotations

import re
from collections.abc import Mapping
from dataclasses import dataclass

from anta._advisory.facts.models import (
    CommandsFactDefinition,
    ConfigurationState,
    ConfigurationValue,
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
from anta.models import AntaCommand

OSPFV3_SUMMARY_COMMAND = OptionalAntaCommand(command="show ospfv3 vrf all", revision=1)
LEGACY_OSPFV3_SUMMARY_COMMAND = OptionalAntaCommand(command="show ipv6 ospf vrf all", revision=1)
OSPFV2_INTERFACE_COMMAND = OptionalAntaCommand(command="show ip ospf interface vrf all", ofmt="text")
OSPFV2_SUMMARY_COMMAND = OptionalAntaCommand(command="show ip ospf vrf all", ofmt="text")
OSPFV2_PROCESS_CONFIG_COMMAND = OptionalAntaCommand(command=r"show running-config section ^router\sospf\s", ofmt="text")
OSPFV2_SEGMENT_ROUTING_COMMAND = OptionalAntaCommand(command="show ip ospf segment-routing", revision=1)
ISIS_INTERFACE_COMMAND = OptionalAntaCommand(command="show isis interface detail vrf all", revision=1)
ISIS_SUMMARY_COMMAND = OptionalAntaCommand(command="show isis summary vrf all", revision=1)
ISIS_GRACEFUL_RESTART_COMMAND = OptionalAntaCommand(command="show isis graceful-restart vrf all", revision=1)
BFD_SUMMARY_COMMAND = OptionalAntaCommand(command="show bfd peers summary")
BFD_GLOBAL_CONFIG_COMMAND = OptionalAntaCommand(command="show running-config section router bfd", ofmt="text")
BFD_INTERFACE_AUTH_CONFIG_COMMAND = OptionalAntaCommand(command="show running-config | include bfd authentication", ofmt="text")
OSPFV3_CONFIG_COMMAND = OptionalAntaCommand(command="show running-config section ospfv3", ofmt="text")
PIM_SPARSE_MODE_COMMAND = OptionalAntaCommand(command="show running-config | include pim.*sparse-mode", ofmt="text")
LOOSE_URPF_COMMAND = AntaCommand(command="show running-config | include verify unicast source reachable-via any", ofmt="text")
AREA_AUTHENTICATION_PATTERN = re.compile(r"^area (?P<area>\S+) (?:authentication|encryption) ipsec\b")
INTERFACE_AUTHENTICATION_PATTERN = re.compile(r"^ospfv3 (?:authentication|encryption) ipsec\b")
OSPFV3_INTERFACE_AREA_PATTERN = re.compile(r"^ospfv3 (?P<family>ipv[46]) area (?P<area>\S+)\b")
OSPFV3_ADDRESS_FAMILY_PATTERN = re.compile(r"^address-family (?P<family>ipv[46])$")
PIM_SPARSE_MODE_COMMANDS = {
    "pim ipv4 sparse-mode",
    "pim ipv6 sparse-mode",
    "ip pim sparse-mode",
    "ipv6 pim sparse-mode",
}
LOOSE_URPF_PATTERN = re.compile(r"^(?:ip|ipv6) verify unicast source reachable-via any(?:\s+.*)?$")
_BFD_GLOBAL_AUTHENTICATION = re.compile(r"^authentication mode (?P<mode>\S+)(?:\s+.*)?$", flags=re.IGNORECASE)
_BFD_INTERFACE_AUTHENTICATION = re.compile(r"^bfd authentication mode (?P<mode>\S+)(?:\s+.*)?$", flags=re.IGNORECASE)


def _bfd_global_authentication_configured(config: str) -> bool | None:
    """Return whether global or peer-specific BFD authentication is configured."""
    global_lines = tuple(line.strip() for line in config.splitlines() if line.strip())
    if global_lines and global_lines[0] != "router bfd":
        return None
    global_modes = tuple(match.group("mode") for line in global_lines[1:] if (match := _BFD_GLOBAL_AUTHENTICATION.fullmatch(line)) is not None)
    return any(mode.casefold() != "disabled" for mode in global_modes)


def _bfd_interface_authentication_configured(config: str) -> bool | None:
    """Return whether interface-specific BFD authentication is configured."""
    interface_modes: list[str] = []
    for line in (line.strip() for line in config.splitlines() if line.strip()):
        if (match := _BFD_INTERFACE_AUTHENTICATION.fullmatch(line)) is None:
            return None
        interface_modes.append(match.group("mode"))
    return any(mode.casefold() != "disabled" for mode in interface_modes)


def _isis_instance_values(vrf: object) -> tuple[Mapping[str, object], ...] | FactProblemKind:
    """Return IS-IS instances from one structured EOS VRF."""
    if not isinstance(vrf, Mapping):
        return FactProblemKind.MALFORMED
    vrf_instances = vrf.get("isisInstances")
    if vrf_instances is None:
        return FactProblemKind.MISSING
    if not isinstance(vrf_instances, Mapping):
        return FactProblemKind.MALFORMED
    instances: list[Mapping[str, object]] = []
    for instance in vrf_instances.values():
        if not isinstance(instance, Mapping):
            return FactProblemKind.MALFORMED
        instances.append(instance)
    return tuple(instances)


def _ospfv3_vrfs(output: Mapping[str, object]) -> tuple[Mapping[str, object], ...] | FactProblemKind:
    """Return validated VRF entries from structured OSPFv3 output."""
    vrfs = output.get("vrfs")
    if vrfs is None:
        return FactProblemKind.MISSING
    if not isinstance(vrfs, Mapping):
        return FactProblemKind.MALFORMED
    entries: list[Mapping[str, object]] = []
    for name, vrf in vrfs.items():
        if not isinstance(name, str) or not name or not isinstance(vrf, Mapping):
            return FactProblemKind.MALFORMED
        entries.append(vrf)
    return tuple(entries)


def _ospfv3_process_configured(output: Mapping[str, object]) -> bool | FactProblemKind:
    """Return whether current structured output contains an OSPFv3 process in any VRF."""
    vrfs = _ospfv3_vrfs(output)
    if isinstance(vrfs, FactProblemKind):
        return vrfs
    for vrf in vrfs:
        if "addressFamily" not in vrf:
            continue
        if not isinstance(vrf["addressFamily"], Mapping):
            return FactProblemKind.MALFORMED
        return True
    return False


def _legacy_ospfv3_process_configured(output: Mapping[str, object]) -> bool | FactProblemKind:
    """Return whether legacy structured output contains an OSPFv3 process in any VRF."""
    vrfs = _ospfv3_vrfs(output)
    if isinstance(vrfs, FactProblemKind):
        return vrfs
    for vrf in vrfs:
        instances = vrf.get("instList")
        if instances is None:
            continue
        if not isinstance(instances, Mapping):
            return FactProblemKind.MALFORMED
        if instances:
            return True
    return False


def _isis_instances(output: Mapping[str, object]) -> tuple[Mapping[str, object], ...] | FactProblemKind:
    """Return IS-IS instances from structured EOS output."""
    vrfs = output.get("vrfs")
    if vrfs is None:
        return FactProblemKind.MISSING
    if not isinstance(vrfs, Mapping):
        return FactProblemKind.MALFORMED

    instances: list[Mapping[str, object]] = []
    for vrf in vrfs.values():
        vrf_instances = _isis_instance_values(vrf)
        if isinstance(vrf_instances, FactProblemKind):
            return vrf_instances
        instances.extend(vrf_instances)
    return tuple(instances)


def _isis_non_passive_levels(levels: object) -> bool | FactProblemKind:
    """Return whether any IS-IS level is non-passive."""
    if levels is None:
        return FactProblemKind.MISSING
    if not isinstance(levels, Mapping):
        return FactProblemKind.MALFORMED

    problem: FactProblemKind | None = None
    for level in levels.values():
        if not isinstance(level, Mapping):
            problem = FactProblemKind.MALFORMED
            continue
        passive = level.get("passive")
        if passive is None:
            problem = problem or FactProblemKind.MISSING
        elif not isinstance(passive, bool):
            problem = FactProblemKind.MALFORMED
        elif not passive:
            return True
    return problem or False


def _isis_non_passive_interface(interface: object) -> bool | FactProblemKind:
    """Return whether one interface is an enabled, non-passive broadcast interface."""
    if not isinstance(interface, Mapping):
        return FactProblemKind.MALFORMED
    enabled = interface.get("enabled")
    if not isinstance(enabled, bool):
        return FactProblemKind.MISSING if enabled is None else FactProblemKind.MALFORMED
    if not enabled:
        return False
    interface_type = interface.get("interfaceType")
    if not isinstance(interface_type, str):
        return FactProblemKind.MISSING if interface_type is None else FactProblemKind.MALFORMED
    if interface_type.casefold() != "broadcast":
        return False
    return _isis_non_passive_levels(interface.get("intfLevels"))


def _isis_non_passive_broadcast_interface(instances: tuple[Mapping[str, object], ...]) -> bool | FactProblemKind:
    """Return whether any enabled IS-IS broadcast interface has a non-passive level."""
    problem: FactProblemKind | None = None
    for instance in instances:
        interfaces = instance.get("interfaces")
        if interfaces is None:
            problem = problem or FactProblemKind.MISSING
            continue
        if not isinstance(interfaces, Mapping):
            problem = FactProblemKind.MALFORMED
            continue
        for interface in interfaces.values():
            state = _isis_non_passive_interface(interface)
            if state is True:
                return True
            if isinstance(state, FactProblemKind):
                problem = state if state is FactProblemKind.MALFORMED else problem or state
    return problem or False


def _parse_config_parent(line: str) -> tuple[str | None, str | None] | None:
    """Return the interface or OSPFv3 VRF identified by one parent line."""
    if line.startswith("interface "):
        interface = line.removeprefix("interface ").strip()
        return (interface, None) if interface else None
    if line == "router ospfv3":
        return None, "default"
    if line.startswith("router ospfv3 vrf "):
        vrf = line.removeprefix("router ospfv3 vrf ").strip()
        return (None, vrf) if vrf else None
    return None


@dataclass(frozen=True, slots=True)
class _Ospfv3InterfaceScope:
    """One persistently configured OSPFv3 interface and address-family scope."""

    interface: str
    vrf: str
    family: str
    area: str


def _parse_ospfv3_security_child(
    line: str,
    current_interface: str | None,
    current_vrf: str | None,
    current_family: str,
    configured_scopes: set[_Ospfv3InterfaceScope],
    interface_authentication: set[str],
    area_authentication: set[tuple[str, str, str]],
) -> tuple[str | None, str]:
    """Parse one indented OSPFv3 security line and return its VRF and address family."""
    if current_interface is not None:
        if line.startswith("vrf "):
            interface_vrf = line.removeprefix("vrf ").strip()
            if interface_vrf:
                current_vrf = interface_vrf
        elif INTERFACE_AUTHENTICATION_PATTERN.match(line) is not None:
            interface_authentication.add(current_interface)
        else:
            match = OSPFV3_INTERFACE_AREA_PATTERN.match(line)
            if match is not None and current_vrf is not None:
                configured_scopes.add(_Ospfv3InterfaceScope(current_interface, current_vrf, match.group("family"), match.group("area")))
    elif current_vrf is not None:
        family_match = OSPFV3_ADDRESS_FAMILY_PATTERN.match(line)
        if family_match is not None:
            current_family = family_match.group("family")
        else:
            area_match = AREA_AUTHENTICATION_PATTERN.match(line)
            if area_match is not None:
                area_authentication.add((current_vrf, current_family, area_match.group("area")))
    return current_vrf, current_family


def _parse_ospfv3_security(config: str) -> tuple[set[_Ospfv3InterfaceScope], set[str], set[tuple[str, str, str]]] | None:
    """Return configured OSPFv3 scopes and their interface- or area-level IPsec protection."""
    configured_scopes: set[_Ospfv3InterfaceScope] = set()
    interface_authentication: set[str] = set()
    area_authentication: set[tuple[str, str, str]] = set()
    current_interface: str | None = None
    current_vrf: str | None = None
    current_family = "ipv6"

    for raw_line in config.splitlines():
        line = raw_line.strip()
        if not line or line == "!":
            continue
        if raw_line == raw_line.lstrip():
            parent = _parse_config_parent(line)
            if parent is None:
                return None
            current_interface, current_vrf = parent
            if current_interface is not None:
                current_vrf = "default"
            current_family = "ipv6"
            continue

        current_vrf, current_family = _parse_ospfv3_security_child(
            line,
            current_interface,
            current_vrf,
            current_family,
            configured_scopes,
            interface_authentication,
            area_authentication,
        )

    return configured_scopes, interface_authentication, area_authentication


class Ospfv3ConfiguredFact(CommandsFactDefinition[FeatureValue]):
    """Presence of an OSPFv3 routing process in any VRF using current EOS syntax."""

    key = "feature.ospfv3.configured"
    label = "OSPFv3 configuration state"
    commands = (OSPFV3_SUMMARY_COMMAND,)

    @classmethod
    def parse(cls, commands: tuple[AntaCommand, ...]) -> Fact[FeatureValue]:
        """Normalize current structured OSPFv3 summary output."""
        (command,) = commands
        source = FactSource(command.command, FactSourceKind.COMMAND)
        feature = SubFeature(FeatureName.OSPFV3, "routing process")
        if is_unsupported_optional_command(command):
            return cls.available(FeatureValue(feature, FeatureState.UNSUPPORTED), source)
        configured = _ospfv3_process_configured(command.json_output)
        if isinstance(configured, FactProblemKind):
            return cls.unavailable(configured, source)
        state = FeatureState.ENABLED if configured else FeatureState.DISABLED
        return cls.available(FeatureValue(feature, state), source)


class LegacyOspfv3ConfiguredFact(CommandsFactDefinition[FeatureValue]):
    """Presence of an OSPFv3 routing process in any VRF exposed through legacy IPv6 syntax."""

    key = "feature.ospfv3.legacy_configured"
    label = "legacy OSPFv3 configuration state"
    commands = (LEGACY_OSPFV3_SUMMARY_COMMAND,)

    @classmethod
    def parse(cls, commands: tuple[AntaCommand, ...]) -> Fact[FeatureValue]:
        """Normalize legacy structured IPv6 OSPF summary output."""
        (command,) = commands
        source = FactSource(command.command, FactSourceKind.COMMAND)
        feature = SubFeature(FeatureName.OSPFV3, "legacy IPv6 routing process")
        if is_unsupported_optional_command(command):
            return cls.available(FeatureValue(feature, FeatureState.UNSUPPORTED), source)
        configured = _legacy_ospfv3_process_configured(command.json_output)
        if isinstance(configured, FactProblemKind):
            return cls.unavailable(configured, source)
        state = FeatureState.ENABLED if configured else FeatureState.DISABLED
        return cls.available(FeatureValue(feature, state), source)


@dataclass(frozen=True, slots=True)
class _Ospfv2Interface:
    """OSPFv2 interface identity and exposure-relevant state."""

    name: str
    instance: str
    vrf: str
    area: str
    broadcast: bool
    cryptographic_authentication: bool


_OSPFV2_INTERFACE_ADDRESS = re.compile(r"^Interface Address .*, instance (?P<instance>\S+), VRF (?P<vrf>\S+), Area (?P<area>\S+)$")
_OSPFV2_NETWORK_TYPE = re.compile(r"^Network Type (?P<network_type>[^,]+)(?:,.*)?$")
_OSPFV2_INSTANCE = re.compile(r"^OSPF instance (?P<instance>\S+) .* VRF (?P<vrf>\S+)$")


def _ospfv2_interfaces(output: str) -> tuple[_Ospfv2Interface, ...] | None:
    """Return normalized active OSPFv2 interface state."""
    if not output.strip():
        return ()
    interfaces: list[_Ospfv2Interface] = []
    current_name: str | None = None
    current_identity: tuple[str, str, str] | None = None
    network_type: str | None = None
    authenticated = False
    interface_count = 0

    def append_current() -> None:
        if current_name is not None and current_identity is not None and network_type is not None:
            instance, vrf, area = current_identity
            interfaces.append(_Ospfv2Interface(current_name, instance, vrf, area, network_type.casefold() == "broadcast", authenticated))

    for raw_line in output.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        if raw_line == raw_line.lstrip() and " is " in line:
            append_current()
            current_name = line.split(" is ", 1)[0]
            current_identity = None
            interface_count += 1
            network_type = None
            authenticated = False
            continue
        if current_name is not None:
            if (match := _OSPFV2_INTERFACE_ADDRESS.match(line)) is not None:
                current_identity = (match.group("instance"), match.group("vrf"), match.group("area"))
            if (network_type_match := _OSPFV2_NETWORK_TYPE.match(line)) is not None:
                network_type = network_type_match.group("network_type").strip()
            authenticated |= (
                line.startswith("Message-digest authentication")
                or re.fullmatch(r"Message-digest sha\S+ authentication(?:,.*)?", line, flags=re.IGNORECASE) is not None
            )
    append_current()
    return tuple(interfaces) if interface_count > 0 and len(interfaces) == interface_count else None


def _ospfv2_area_authentication(
    output: str,
) -> tuple[set[tuple[str, str, str]], set[tuple[str, str, str]]] | None:
    """Return observed OSPFv2 areas and those with cryptographic authentication."""
    if not output.strip():
        return set(), set()
    observed: set[tuple[str, str, str]] = set()
    authenticated: set[tuple[str, str, str]] = set()
    current_instance: str | None = None
    current_vrf: str | None = None
    current_area: str | None = None
    saw_instance = False
    for raw_line in output.splitlines():
        line = raw_line.strip()
        if (match := _OSPFV2_INSTANCE.match(line)) is not None:
            current_instance = match.group("instance")
            current_vrf = match.group("vrf")
            current_area = None
            saw_instance = True
            continue
        if (area_match := re.fullmatch(r"Area (?P<area>\S+)", line)) is not None:
            area = area_match.group("area")
            current_area = area
            if current_instance is not None and current_vrf is not None:
                observed.add((current_instance, current_vrf, area))
            continue
        if "Area has " in line and " authentication" in line and current_instance is not None and current_vrf is not None and current_area is not None:
            method = line.split("Area has ", 1)[1].split(" authentication", 1)[0].casefold()
            if method not in {"no", "none", "simple"}:
                authenticated.add((current_instance, current_vrf, current_area))
    return (observed, authenticated) if saw_instance else None


class Ospfv2BroadcastAuthenticationFact(CommandsFactDefinition[FeatureValue]):
    """OSPFv2 broadcast interface with cryptographic authentication."""

    key = "feature.ospfv2.broadcast_cryptographic_authentication"
    label = "OSPFv2 broadcast cryptographic-authentication exposure state"
    commands = (OSPFV2_INTERFACE_COMMAND, OSPFV2_SUMMARY_COMMAND)

    @classmethod
    # pylint: disable-next=too-many-return-statements
    def parse(cls, commands: tuple[AntaCommand, ...]) -> Fact[FeatureValue]:  # noqa: PLR0911
        """Find cryptographic authentication on active OSPFv2 broadcast interfaces."""
        interface_command, summary_command = commands
        feature = SubFeature(FeatureName.OSPFV2, "broadcast cryptographic authentication")
        interface_source = FactSource(interface_command.command, FactSourceKind.COMMAND)
        if is_unsupported_optional_command(interface_command):
            return cls.available(FeatureValue(feature, FeatureState.UNSUPPORTED), interface_source)
        interfaces = _ospfv2_interfaces(interface_command.text_output)
        if interfaces is None:
            return cls.unavailable(FactProblemKind.MALFORMED, interface_source)
        candidates = tuple(interface for interface in interfaces if interface.broadcast)
        if not candidates:
            return cls.available(FeatureValue(feature, FeatureState.DISABLED), interface_source)
        if any(interface.cryptographic_authentication for interface in candidates):
            return cls.available(FeatureValue(feature, FeatureState.ENABLED), interface_source)
        summary_source = FactSource(summary_command.command, FactSourceKind.COMMAND)
        if is_unsupported_optional_command(summary_command):
            return cls.unavailable(FactProblemKind.UNSUPPORTED, summary_source)
        area_authentication = _ospfv2_area_authentication(summary_command.text_output)
        if area_authentication is None:
            return cls.unavailable(FactProblemKind.MALFORMED, summary_source)
        observed_areas, authenticated_areas = area_authentication
        candidate_areas = {(interface.instance, interface.vrf, interface.area) for interface in candidates}
        exposed = bool(candidate_areas & authenticated_areas)
        if not exposed and not candidate_areas.issubset(observed_areas):
            return cls.unavailable(FactProblemKind.MISSING, summary_source)
        state = FeatureState.ENABLED if exposed else FeatureState.DISABLED
        return cls.available(FeatureValue(feature, state), summary_source)


class Ospfv2ProcessConfiguredFact(CommandsFactDefinition[ConfigurationValue]):
    """Presence of an OSPFv2 routing process."""

    key = "configuration.ospfv2.routing_process"
    label = "OSPFv2 routing-process configuration state"
    commands = (OSPFV2_PROCESS_CONFIG_COMMAND,)

    @classmethod
    def parse(cls, commands: tuple[AntaCommand, ...]) -> Fact[ConfigurationValue]:
        """Return whether any OSPFv2 routing process is configured."""
        (command,) = commands
        source = FactSource(command.command, FactSourceKind.COMMAND)
        feature = SubFeature(FeatureName.OSPFV2, "routing process")
        if is_unsupported_optional_command(command):
            return cls.unavailable(FactProblemKind.UNSUPPORTED, source)
        state = ConfigurationState.CONFIGURED if command.text_output.strip() else ConfigurationState.NOT_CONFIGURED
        return cls.available(ConfigurationValue(feature, state), source)


def _ospfv2_segment_routing_enabled(output: Mapping[str, object]) -> bool | FactProblemKind:
    """Return whether any VRF reports an OSPFv2 segment-routing instance."""
    vrfs = output.get("vrfs")
    if vrfs is None:
        return FactProblemKind.MISSING
    if not isinstance(vrfs, Mapping):
        return FactProblemKind.MALFORMED
    enabled = False
    for vrf in vrfs.values():
        if not isinstance(vrf, Mapping):
            return FactProblemKind.MALFORMED
        inst_list = vrf.get("instList")
        if inst_list is None:
            return FactProblemKind.MISSING
        if not isinstance(inst_list, Mapping):
            return FactProblemKind.MALFORMED
        if inst_list:
            enabled = True
    return enabled


class Ospfv2SegmentRoutingFact(CommandsFactDefinition[FeatureValue]):
    """Presence of an OSPFv2 segment-routing instance."""

    key = "feature.ospfv2.segment_routing"
    label = "OSPFv2 segment-routing state"
    commands = (OSPFV2_SEGMENT_ROUTING_COMMAND,)

    @classmethod
    def parse(cls, commands: tuple[AntaCommand, ...]) -> Fact[FeatureValue]:
        """Normalize structured instance presence.

        An empty ``instList`` is disabled, including when EOS only reports that
        segment routing is administratively shutdown.
        """
        (command,) = commands
        source = FactSource(command.command, FactSourceKind.COMMAND)
        feature = SubFeature(FeatureName.OSPFV2, "segment routing")
        if is_unsupported_optional_command(command):
            return cls.available(FeatureValue(feature, FeatureState.UNSUPPORTED), source)
        enabled = _ospfv2_segment_routing_enabled(command.json_output)
        if isinstance(enabled, FactProblemKind):
            return cls.unavailable(enabled, source)
        return cls.available(FeatureValue(feature, FeatureState.ENABLED if enabled else FeatureState.DISABLED), source)


class IsisNonPassiveBroadcastInterfaceFact(CommandsFactDefinition[FeatureValue]):
    """Presence of an enabled, non-passive IS-IS broadcast interface."""

    key = "feature.isis.non_passive_broadcast_interface"
    label = "IS-IS non-passive broadcast-interface exposure state"
    commands = (ISIS_INTERFACE_COMMAND,)

    @classmethod
    def parse(cls, commands: tuple[AntaCommand, ...]) -> Fact[FeatureValue]:
        """Normalize modeled interface, network-type, and per-level passive state."""
        (command,) = commands
        source = FactSource(command.command, FactSourceKind.COMMAND)
        feature = SubFeature(FeatureName.ISIS, "non-passive broadcast interface")
        if is_unsupported_optional_command(command):
            return cls.available(FeatureValue(feature, FeatureState.UNSUPPORTED), source)
        instances = _isis_instances(command.json_output)
        if isinstance(instances, FactProblemKind):
            return cls.unavailable(instances, source)
        exposed = _isis_non_passive_broadcast_interface(instances)
        if isinstance(exposed, FactProblemKind):
            return cls.unavailable(exposed, source)
        state = FeatureState.ENABLED if exposed else FeatureState.DISABLED
        return cls.available(FeatureValue(feature, state), source)


class IsisConfiguredFact(CommandsFactDefinition[FeatureValue]):
    """Presence of an enabled IS-IS instance."""

    key = "feature.isis"
    label = "IS-IS feature state"
    commands = (ISIS_SUMMARY_COMMAND,)

    @classmethod
    def parse(cls, commands: tuple[AntaCommand, ...]) -> Fact[FeatureValue]:
        """Normalize an IS-IS summary or its established empty state."""
        (command,) = commands
        source = FactSource(command.command, FactSourceKind.COMMAND)
        if is_unsupported_optional_command(command):
            return cls.available(FeatureValue(FeatureName.ISIS, FeatureState.UNSUPPORTED), source)
        instances = _isis_instances(command.json_output)
        if isinstance(instances, FactProblemKind):
            return cls.unavailable(instances, source)
        problem: FactProblemKind | None = None
        enabled = False
        for instance in instances:
            value = instance.get("enabled")
            if value is None:
                problem = problem or FactProblemKind.MISSING
            elif isinstance(value, bool):
                enabled |= value
            else:
                problem = FactProblemKind.MALFORMED
        if not enabled and problem is not None:
            return cls.unavailable(problem, source)
        state = FeatureState.ENABLED if enabled else FeatureState.DISABLED
        return cls.available(FeatureValue(FeatureName.ISIS, state), source)


class IsisGracefulRestartFact(CommandsFactDefinition[FeatureValue]):
    """Presence of enabled IS-IS graceful restart."""

    key = "feature.isis.graceful_restart"
    label = "IS-IS graceful-restart state"
    commands = (ISIS_GRACEFUL_RESTART_COMMAND,)

    @classmethod
    def parse(cls, commands: tuple[AntaCommand, ...]) -> Fact[FeatureValue]:
        """Normalize the explicit graceful-restart status."""
        (command,) = commands
        source = FactSource(command.command, FactSourceKind.COMMAND)
        feature = SubFeature(FeatureName.ISIS, "graceful restart")
        if is_unsupported_optional_command(command):
            return cls.available(FeatureValue(feature, FeatureState.UNSUPPORTED), source)
        instances = _isis_instances(command.json_output)
        if isinstance(instances, FactProblemKind):
            return cls.unavailable(instances, source)
        problem: FactProblemKind | None = None
        enabled = False
        for instance in instances:
            value = instance.get("gracefulRestart")
            if value is None:
                problem = problem or FactProblemKind.MISSING
            elif not isinstance(value, str) or value.casefold() not in {"enabled", "disabled"}:
                problem = FactProblemKind.MALFORMED
            else:
                enabled |= value.casefold() == "enabled"
        if not enabled and problem is not None:
            return cls.unavailable(problem, source)
        state = FeatureState.ENABLED if enabled else FeatureState.DISABLED
        return cls.available(FeatureValue(feature, state), source)


class Ospfv3IpsecAuthenticationFact(CommandsFactDefinition[MitigationValue]):
    """IPsec authentication coverage across every configured OSPFv3 interface scope."""

    key = "mitigation.ospfv3.ipsec_authentication"
    label = "OSPFv3 IPsec authentication coverage"
    commands = (OSPFV3_CONFIG_COMMAND,)

    @classmethod
    def parse(cls, commands: tuple[AntaCommand, ...]) -> Fact[MitigationValue]:
        """Verify interface- or address-family-specific area authentication for every configured scope."""
        (config_command,) = commands
        config_source = FactSource(config_command.command, FactSourceKind.COMMAND)
        if is_unsupported_optional_command(config_command):
            return cls.unavailable(FactProblemKind.UNSUPPORTED, config_source)
        security = _parse_ospfv3_security(config_command.text_output)
        if security is None:
            return cls.unavailable(FactProblemKind.MALFORMED, config_source)
        scopes, interfaces, areas = security
        effective = bool(scopes) and all(scope.interface in interfaces or (scope.vrf, scope.family, scope.area) in areas for scope in scopes)
        state = MitigationState.EFFECTIVE if effective else MitigationState.INEFFECTIVE
        return cls.available(MitigationValue(state), config_source)


class PimSparseModeFact(CommandsFactDefinition[FeatureValue]):
    """Presence of PIM sparse mode on any IPv4 or IPv6 interface."""

    key = "feature.pim.sparse_mode"
    label = "PIM sparse-mode interface state"
    commands = (PIM_SPARSE_MODE_COMMAND,)

    @classmethod
    def parse(cls, commands: tuple[AntaCommand, ...]) -> Fact[FeatureValue]:
        """Normalize canonical and legacy interface command syntax."""
        (command,) = commands
        source = FactSource(command.command, FactSourceKind.COMMAND)
        feature = SubFeature(FeatureName.PIM, "sparse-mode interface")
        if is_unsupported_optional_command(command):
            return cls.unavailable(FactProblemKind.UNSUPPORTED, source)
        lines = tuple(line.strip() for line in command.text_output.splitlines() if line.strip())
        if any(line not in PIM_SPARSE_MODE_COMMANDS for line in lines):
            return cls.unavailable(FactProblemKind.MALFORMED, source)
        state = FeatureState.ENABLED if lines else FeatureState.DISABLED
        return cls.available(FeatureValue(feature, state), source)


class LooseUrpfFact(CommandsFactDefinition[FeatureValue]):
    """Presence of loose IPv4 or IPv6 uRPF on any interface."""

    key = "feature.urpf.loose_mode"
    label = "loose uRPF interface state"
    commands = (LOOSE_URPF_COMMAND,)

    @classmethod
    def parse(cls, commands: tuple[AntaCommand, ...]) -> Fact[FeatureValue]:
        """Normalize the narrow loose-uRPF configuration output."""
        (command,) = commands
        source = FactSource(command.command, FactSourceKind.COMMAND)
        lines = tuple(line.strip() for line in command.text_output.splitlines() if line.strip())
        if any(LOOSE_URPF_PATTERN.fullmatch(line) is None for line in lines):
            return cls.unavailable(FactProblemKind.MALFORMED, source)
        feature = SubFeature(FeatureName.URPF, "loose-mode interface")
        state = FeatureState.ENABLED if lines else FeatureState.DISABLED
        return cls.available(FeatureValue(feature, state), source)


class BfdAuthenticationFact(CommandsFactDefinition[FeatureValue]):
    """Presence of configured BFD authentication while BFD is enabled."""

    key = "feature.bfd.authentication"
    label = "BFD authentication state"
    commands = (BFD_SUMMARY_COMMAND, BFD_GLOBAL_CONFIG_COMMAND, BFD_INTERFACE_AUTH_CONFIG_COMMAND)

    @classmethod
    def parse(cls, commands: tuple[AntaCommand, ...]) -> Fact[FeatureValue]:
        """Combine BFD administrative state with global, peer-specific, and interface authentication configuration."""
        summary, global_config, interface_config = commands
        feature = SubFeature(FeatureName.BFD, "authentication")
        summary_source = FactSource(summary.command, FactSourceKind.COMMAND)
        if is_unsupported_optional_command(summary):
            state = FeatureState.UNSUPPORTED
            source_command = summary
        else:
            admin_down = summary.json_output.get("adminDown")
            if not isinstance(admin_down, bool):
                return cls.unavailable(FactProblemKind.MISSING if admin_down is None else FactProblemKind.MALFORMED, summary_source)
            if admin_down:
                return cls.available(FeatureValue(feature, FeatureState.DISABLED), summary_source)

            for command in (global_config, interface_config):
                source = FactSource(command.command, FactSourceKind.COMMAND)
                if is_unsupported_optional_command(command):
                    return cls.unavailable(FactProblemKind.UNSUPPORTED, source)
            global_configured = _bfd_global_authentication_configured(global_config.text_output)
            if global_configured is None:
                return cls.unavailable(FactProblemKind.MALFORMED, FactSource(global_config.command, FactSourceKind.COMMAND))
            interface_configured = _bfd_interface_authentication_configured(interface_config.text_output)
            if interface_configured is None:
                return cls.unavailable(FactProblemKind.MALFORMED, FactSource(interface_config.command, FactSourceKind.COMMAND))
            state = FeatureState.ENABLED if global_configured or interface_configured else FeatureState.DISABLED
            source_command = global_config if global_configured else interface_config if interface_configured else summary
        return cls.available(FeatureValue(feature, state), FactSource(source_command.command, FactSourceKind.COMMAND))
