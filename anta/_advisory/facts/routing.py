# Copyright (c) 2026 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Facts derived from EOS routing protocol state and configuration."""

from __future__ import annotations

import re
from collections.abc import Mapping
from dataclasses import dataclass
from ipaddress import IPv4Address, IPv4Network
from typing import ClassVar

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
    MitigationFact,
    MitigationState,
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
OSPFV3_CONFIG_COMMAND = OptionalAntaCommand(command="show running-config section ospfv3", ofmt="text")
PIM_SPARSE_MODE_COMMAND = OptionalAntaCommand(command="show running-config | include pim.*sparse-mode", ofmt="text")
LOOSE_URPF_COMMAND = AntaCommand(command="show running-config | include verify unicast source reachable-via any", ofmt="text")
RIP_CONFIG_COMMAND = OptionalAntaCommand(command=r"show running-config all section ^router\srip", ofmt="text", defer_errors=True)
RIP_AUTHENTICATION_CONFIG_COMMAND = OptionalAntaCommand(command=r"show running-config sanitized section ^\s+rip\sauthentication", ofmt="text", defer_errors=True)
IP_INTERFACE_COMMAND = OptionalAntaCommand(command="show ip interface", revision=2, defer_errors=True)
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
_RIP_ROUTER = re.compile(r"^router rip(?: vrf (?P<vrf>\S+))?$")
_RIP_NETWORK = re.compile(r"^network (?P<prefix>\d{1,3}(?:\.\d{1,3}){3}/\d{1,2})$")
_RIP_MD5_AUTHENTICATION = re.compile(r"^rip authentication algorithm md5\s")


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


@dataclass(frozen=True, slots=True)
class Ospfv3ConfiguredFact(FeatureFact, CommandsFactDefinition["Ospfv3ConfiguredFact"]):
    """Presence of an OSPFv3 routing process in any VRF using current EOS syntax."""

    feature: ClassVar[FeatureRef] = SubFeature(FeatureName.OSPFV3, "routing process")
    key: ClassVar[str] = "feature.ospfv3.configured"
    label: ClassVar[str] = "OSPFv3 configuration state"
    commands: ClassVar[tuple[AntaCommand, ...]] = (OSPFV3_SUMMARY_COMMAND,)

    @classmethod
    def parse(cls, commands: tuple[AntaCommand, ...]) -> Fact[Ospfv3ConfiguredFact]:
        """Normalize current structured OSPFv3 summary output."""
        (command,) = commands
        source = FactSource(command.command, FactSourceKind.COMMAND)
        if is_unsupported_optional_command(command):
            return cls(FeatureState.UNSUPPORTED).available(source)
        configured = _ospfv3_process_configured(command.json_output)
        if isinstance(configured, FactProblemKind):
            return cls.unavailable(configured, source)
        state = FeatureState.ENABLED if configured else FeatureState.DISABLED
        return cls(state).available(source)


@dataclass(frozen=True, slots=True)
class LegacyOspfv3ConfiguredFact(FeatureFact, CommandsFactDefinition["LegacyOspfv3ConfiguredFact"]):
    """Presence of an OSPFv3 routing process in any VRF exposed through legacy IPv6 syntax."""

    feature: ClassVar[FeatureRef] = SubFeature(FeatureName.OSPFV3, "legacy IPv6 routing process")
    key: ClassVar[str] = "feature.ospfv3.legacy_configured"
    label: ClassVar[str] = "legacy OSPFv3 configuration state"
    commands: ClassVar[tuple[AntaCommand, ...]] = (LEGACY_OSPFV3_SUMMARY_COMMAND,)

    @classmethod
    def parse(cls, commands: tuple[AntaCommand, ...]) -> Fact[LegacyOspfv3ConfiguredFact]:
        """Normalize legacy structured IPv6 OSPF summary output."""
        (command,) = commands
        source = FactSource(command.command, FactSourceKind.COMMAND)
        if is_unsupported_optional_command(command):
            return cls(FeatureState.UNSUPPORTED).available(source)
        configured = _legacy_ospfv3_process_configured(command.json_output)
        if isinstance(configured, FactProblemKind):
            return cls.unavailable(configured, source)
        state = FeatureState.ENABLED if configured else FeatureState.DISABLED
        return cls(state).available(source)


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


@dataclass(frozen=True, slots=True)
class Ospfv2BroadcastAuthenticationFact(FeatureFact, CommandsFactDefinition["Ospfv2BroadcastAuthenticationFact"]):
    """OSPFv2 broadcast interface with cryptographic authentication."""

    feature: ClassVar[FeatureRef] = SubFeature(FeatureName.OSPFV2, "broadcast cryptographic authentication")
    key: ClassVar[str] = "feature.ospfv2.broadcast_cryptographic_authentication"
    label: ClassVar[str] = "OSPFv2 broadcast cryptographic-authentication exposure state"
    commands: ClassVar[tuple[AntaCommand, ...]] = (OSPFV2_INTERFACE_COMMAND, OSPFV2_SUMMARY_COMMAND)

    @classmethod
    # pylint: disable-next=too-many-return-statements
    def parse(cls, commands: tuple[AntaCommand, ...]) -> Fact[Ospfv2BroadcastAuthenticationFact]:  # noqa: PLR0911
        """Find cryptographic authentication on active OSPFv2 broadcast interfaces."""
        interface_command, summary_command = commands
        interface_source = FactSource(interface_command.command, FactSourceKind.COMMAND)
        if is_unsupported_optional_command(interface_command):
            return cls(FeatureState.UNSUPPORTED).available(interface_source)
        interfaces = _ospfv2_interfaces(interface_command.text_output)
        if interfaces is None:
            return cls.unavailable(FactProblemKind.MALFORMED, interface_source)
        candidates = tuple(interface for interface in interfaces if interface.broadcast)
        if not candidates:
            return cls(FeatureState.DISABLED).available(interface_source)
        if any(interface.cryptographic_authentication for interface in candidates):
            return cls(FeatureState.ENABLED).available(interface_source)
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
        return cls(state).available(summary_source)


@dataclass(frozen=True, slots=True)
class Ospfv2ProcessConfiguredFact(ConfigurationFact, CommandsFactDefinition["Ospfv2ProcessConfiguredFact"]):
    """Presence of an OSPFv2 routing process."""

    feature: ClassVar[FeatureRef] = SubFeature(FeatureName.OSPFV2, "routing process")
    key: ClassVar[str] = "configuration.ospfv2.routing_process"
    label: ClassVar[str] = "OSPFv2 routing-process configuration state"
    commands: ClassVar[tuple[AntaCommand, ...]] = (OSPFV2_PROCESS_CONFIG_COMMAND,)

    @classmethod
    def parse(cls, commands: tuple[AntaCommand, ...]) -> Fact[Ospfv2ProcessConfiguredFact]:
        """Return whether any OSPFv2 routing process is configured."""
        (command,) = commands
        source = FactSource(command.command, FactSourceKind.COMMAND)
        if is_unsupported_optional_command(command):
            return cls.unavailable(FactProblemKind.UNSUPPORTED, source)
        state = ConfigurationState.CONFIGURED if command.text_output.strip() else ConfigurationState.NOT_CONFIGURED
        return cls(state).available(source)


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


@dataclass(frozen=True, slots=True)
class Ospfv2SegmentRoutingFact(FeatureFact, CommandsFactDefinition["Ospfv2SegmentRoutingFact"]):
    """Presence of an OSPFv2 segment-routing instance."""

    feature: ClassVar[FeatureRef] = SubFeature(FeatureName.OSPFV2, "segment routing")
    key: ClassVar[str] = "feature.ospfv2.segment_routing"
    label: ClassVar[str] = "OSPFv2 segment-routing state"
    commands: ClassVar[tuple[AntaCommand, ...]] = (OSPFV2_SEGMENT_ROUTING_COMMAND,)

    @classmethod
    def parse(cls, commands: tuple[AntaCommand, ...]) -> Fact[Ospfv2SegmentRoutingFact]:
        """Normalize structured instance presence.

        An empty ``instList`` is disabled, including when EOS only reports that
        segment routing is administratively shutdown.
        """
        (command,) = commands
        source = FactSource(command.command, FactSourceKind.COMMAND)
        if is_unsupported_optional_command(command):
            return cls(FeatureState.UNSUPPORTED).available(source)
        enabled = _ospfv2_segment_routing_enabled(command.json_output)
        if isinstance(enabled, FactProblemKind):
            return cls.unavailable(enabled, source)
        return cls(FeatureState.ENABLED if enabled else FeatureState.DISABLED).available(source)


@dataclass(frozen=True, slots=True)
class IsisNonPassiveBroadcastInterfaceFact(FeatureFact, CommandsFactDefinition["IsisNonPassiveBroadcastInterfaceFact"]):
    """Presence of an enabled, non-passive IS-IS broadcast interface."""

    feature: ClassVar[FeatureRef] = SubFeature(FeatureName.ISIS, "non-passive broadcast interface")
    key: ClassVar[str] = "feature.isis.non_passive_broadcast_interface"
    label: ClassVar[str] = "IS-IS non-passive broadcast-interface exposure state"
    commands: ClassVar[tuple[AntaCommand, ...]] = (ISIS_INTERFACE_COMMAND,)

    @classmethod
    def parse(cls, commands: tuple[AntaCommand, ...]) -> Fact[IsisNonPassiveBroadcastInterfaceFact]:
        """Normalize modeled interface, network-type, and per-level passive state."""
        (command,) = commands
        source = FactSource(command.command, FactSourceKind.COMMAND)
        if is_unsupported_optional_command(command):
            return cls(FeatureState.UNSUPPORTED).available(source)
        instances = _isis_instances(command.json_output)
        if isinstance(instances, FactProblemKind):
            return cls.unavailable(instances, source)
        exposed = _isis_non_passive_broadcast_interface(instances)
        if isinstance(exposed, FactProblemKind):
            return cls.unavailable(exposed, source)
        state = FeatureState.ENABLED if exposed else FeatureState.DISABLED
        return cls(state).available(source)


@dataclass(frozen=True, slots=True)
class IsisConfiguredFact(FeatureFact, CommandsFactDefinition["IsisConfiguredFact"]):
    """Presence of an enabled IS-IS instance."""

    feature: ClassVar[FeatureRef] = FeatureName.ISIS
    key: ClassVar[str] = "feature.isis"
    label: ClassVar[str] = "IS-IS feature state"
    commands: ClassVar[tuple[AntaCommand, ...]] = (ISIS_SUMMARY_COMMAND,)

    @classmethod
    def parse(cls, commands: tuple[AntaCommand, ...]) -> Fact[IsisConfiguredFact]:
        """Normalize an IS-IS summary or its established empty state."""
        (command,) = commands
        source = FactSource(command.command, FactSourceKind.COMMAND)
        if is_unsupported_optional_command(command):
            return cls(FeatureState.UNSUPPORTED).available(source)
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
        return cls(state).available(source)


@dataclass(frozen=True, slots=True)
class IsisGracefulRestartFact(FeatureFact, CommandsFactDefinition["IsisGracefulRestartFact"]):
    """Presence of enabled IS-IS graceful restart."""

    feature: ClassVar[FeatureRef] = SubFeature(FeatureName.ISIS, "graceful restart")
    key: ClassVar[str] = "feature.isis.graceful_restart"
    label: ClassVar[str] = "IS-IS graceful-restart state"
    commands: ClassVar[tuple[AntaCommand, ...]] = (ISIS_GRACEFUL_RESTART_COMMAND,)

    @classmethod
    def parse(cls, commands: tuple[AntaCommand, ...]) -> Fact[IsisGracefulRestartFact]:
        """Normalize the explicit graceful-restart status."""
        (command,) = commands
        source = FactSource(command.command, FactSourceKind.COMMAND)
        if is_unsupported_optional_command(command):
            return cls(FeatureState.UNSUPPORTED).available(source)
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
        return cls(state).available(source)


@dataclass(frozen=True, slots=True)
class Ospfv3IpsecAuthenticationFact(MitigationFact, CommandsFactDefinition["Ospfv3IpsecAuthenticationFact"]):
    """IPsec authentication coverage across every configured OSPFv3 interface scope."""

    key: ClassVar[str] = "mitigation.ospfv3.ipsec_authentication"
    label: ClassVar[str] = "OSPFv3 IPsec authentication coverage"
    commands: ClassVar[tuple[AntaCommand, ...]] = (OSPFV3_CONFIG_COMMAND,)

    @classmethod
    def parse(cls, commands: tuple[AntaCommand, ...]) -> Fact[Ospfv3IpsecAuthenticationFact]:
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
        return cls(state).available(config_source)


@dataclass(frozen=True, slots=True)
class PimSparseModeFact(FeatureFact, CommandsFactDefinition["PimSparseModeFact"]):
    """Presence of PIM sparse mode on any IPv4 or IPv6 interface."""

    feature: ClassVar[FeatureRef] = SubFeature(FeatureName.PIM, "sparse-mode interface")
    key: ClassVar[str] = "feature.pim.sparse_mode"
    label: ClassVar[str] = "PIM sparse-mode interface state"
    commands: ClassVar[tuple[AntaCommand, ...]] = (PIM_SPARSE_MODE_COMMAND,)

    @classmethod
    def parse(cls, commands: tuple[AntaCommand, ...]) -> Fact[PimSparseModeFact]:
        """Normalize canonical and legacy interface command syntax."""
        (command,) = commands
        source = FactSource(command.command, FactSourceKind.COMMAND)
        if is_unsupported_optional_command(command):
            return cls.unavailable(FactProblemKind.UNSUPPORTED, source)
        lines = tuple(line.strip() for line in command.text_output.splitlines() if line.strip())
        if any(line not in PIM_SPARSE_MODE_COMMANDS for line in lines):
            return cls.unavailable(FactProblemKind.MALFORMED, source)
        state = FeatureState.ENABLED if lines else FeatureState.DISABLED
        return cls(state).available(source)


@dataclass(frozen=True, slots=True)
class LooseUrpfFact(FeatureFact, CommandsFactDefinition["LooseUrpfFact"]):
    """Presence of loose IPv4 or IPv6 uRPF on any interface."""

    feature: ClassVar[FeatureRef] = SubFeature(FeatureName.URPF, "loose-mode interface")
    key: ClassVar[str] = "feature.urpf.loose_mode"
    label: ClassVar[str] = "loose uRPF interface state"
    commands: ClassVar[tuple[AntaCommand, ...]] = (LOOSE_URPF_COMMAND,)

    @classmethod
    def parse(cls, commands: tuple[AntaCommand, ...]) -> Fact[LooseUrpfFact]:
        """Normalize the narrow loose-uRPF configuration output."""
        (command,) = commands
        source = FactSource(command.command, FactSourceKind.COMMAND)
        lines = tuple(line.strip() for line in command.text_output.splitlines() if line.strip())
        if any(LOOSE_URPF_PATTERN.fullmatch(line) is None for line in lines):
            return cls.unavailable(FactProblemKind.MALFORMED, source)
        state = FeatureState.ENABLED if lines else FeatureState.DISABLED
        return cls(state).available(source)


def _config_blocks(config: str) -> tuple[tuple[str, tuple[str, ...]], ...] | None:
    """Split section output into top-level lines and their stripped child lines."""
    blocks: list[tuple[str, list[str]]] = []
    for raw_line in config.splitlines():
        line = raw_line.strip()
        if not line or line == "!":
            continue
        if raw_line == raw_line.lstrip():
            blocks.append((line, []))
        elif blocks:
            blocks[-1][1].append(line)
        else:
            return None
    return tuple((parent, tuple(children)) for parent, children in blocks)


@dataclass(frozen=True, slots=True)
class _RipInstance:
    """One configured RIP instance and the network prefixes that select its interfaces."""

    vrf: str
    enabled: bool
    networks: tuple[IPv4Network, ...]


def _rip_instance(parent: str, children: tuple[str, ...]) -> _RipInstance | None:
    """Return one RIP instance whose administrative state must be explicitly rendered."""
    if (match := _RIP_ROUTER.fullmatch(parent)) is None:
        return None
    states = tuple(line == "no shutdown" for line in children if line in {"shutdown", "no shutdown"})
    if len(states) != 1:
        return None
    networks: list[IPv4Network] = []
    for line in children:
        if not line.startswith("network "):
            continue
        if (network := _RIP_NETWORK.fullmatch(line)) is None:
            return None
        try:
            networks.append(IPv4Network(network.group("prefix"), strict=False))
        except ValueError:
            return None
    return _RipInstance(match.group("vrf") or "default", states[0], tuple(networks))


def _rip_instances(config: str) -> tuple[_RipInstance, ...] | None:
    """Return every RIP instance from ``running-config all`` section output."""
    blocks = _config_blocks(config)
    if blocks is None:
        return None
    instances: list[_RipInstance] = []
    for parent, children in blocks:
        instance = _rip_instance(parent, children)
        if instance is None or any(existing.vrf == instance.vrf for existing in instances):
            return None
        instances.append(instance)
    return tuple(instances)


def _rip_md5_interfaces(config: str) -> tuple[str, ...] | None:
    """Return interfaces with any RIP MD5 authentication statement."""
    blocks = _config_blocks(config)
    if blocks is None:
        return None
    interfaces: list[str] = []
    for parent, children in blocks:
        interface = parent.removeprefix("interface ").strip()
        if not parent.startswith("interface ") or not interface or not children or any(not line.startswith("rip authentication ") for line in children):
            return None
        if any(_RIP_MD5_AUTHENTICATION.match(line) is not None for line in children):
            interfaces.append(interface)
    return tuple(interfaces)


@dataclass(frozen=True, slots=True)
class _Ipv4InterfaceAddressing:
    """IPv4 addressing that a routing protocol can match against its network statements."""

    vrf: str
    addresses: tuple[IPv4Address, ...]


def _ipv4_address(value: object) -> IPv4Address | FactProblemKind | None:
    """Return one structured interface address, where ``0.0.0.0`` means that no address is assigned."""
    if not isinstance(value, Mapping):
        return FactProblemKind.MISSING if value is None else FactProblemKind.MALFORMED
    address = value.get("address")
    if not isinstance(address, str):
        return FactProblemKind.MISSING if address is None else FactProblemKind.MALFORMED
    try:
        parsed = IPv4Address(address)
    except ValueError:
        return FactProblemKind.MALFORMED
    return None if parsed.is_unspecified else parsed


def _ipv4_interface_addressing(interface: object) -> _Ipv4InterfaceAddressing | FactProblemKind:
    """Return the VRF and current primary and secondary addresses of one structured interface."""
    if not isinstance(interface, Mapping):
        return FactProblemKind.MALFORMED
    addressing = interface.get("interfaceAddress")
    if not isinstance(addressing, Mapping):
        return FactProblemKind.MISSING if addressing is None else FactProblemKind.MALFORMED
    vrf, secondaries = interface.get("vrf"), addressing.get("secondaryIpsOrderedList")
    if vrf is None or secondaries is None:
        return FactProblemKind.MISSING
    if not isinstance(vrf, str) or not vrf or not isinstance(secondaries, list):
        return FactProblemKind.MALFORMED
    addresses: list[IPv4Address] = []
    for value in (addressing.get("primaryIp"), *secondaries):
        address = _ipv4_address(value)
        if isinstance(address, FactProblemKind):
            return address
        if address is not None:
            addresses.append(address)
    return _Ipv4InterfaceAddressing(vrf, tuple(addresses))


def _enabled_rip_networks(config: str) -> dict[str, tuple[IPv4Network, ...]] | None:
    """Return the network prefixes of every enabled RIP instance with at least one network, keyed by VRF."""
    instances = _rip_instances(config)
    if instances is None:
        return None
    return {instance.vrf: instance.networks for instance in instances if instance.enabled and instance.networks}


def _rip_selects_interface(
    names: tuple[str, ...],
    enabled_networks: Mapping[str, tuple[IPv4Network, ...]],
    interfaces: Mapping[object, object],
) -> bool | FactProblemKind:
    """Return whether an enabled RIP instance selects one of the named interfaces in its own VRF."""
    problem: FactProblemKind | None = None
    for name in names:
        if name not in interfaces:
            continue
        addressing = _ipv4_interface_addressing(interfaces[name])
        if isinstance(addressing, FactProblemKind):
            problem = addressing if addressing is FactProblemKind.MALFORMED else problem or addressing
            continue
        networks = enabled_networks.get(addressing.vrf, ())
        if any(address in network for address in addressing.addresses for network in networks):
            return True
    return problem or False


def _ipv4_dhcp_addressing(interface: object) -> tuple[str, bool] | FactProblemKind:
    """Return the VRF of one structured interface and whether DHCP assigns its IPv4 address."""
    if not isinstance(interface, Mapping):
        return FactProblemKind.MALFORMED
    addressing = interface.get("interfaceAddress")
    if not isinstance(addressing, Mapping):
        return FactProblemKind.MISSING if addressing is None else FactProblemKind.MALFORMED
    vrf, dhcp = interface.get("vrf"), addressing.get("dhcp")
    if vrf is None or dhcp is None:
        return FactProblemKind.MISSING
    if not isinstance(vrf, str) or not vrf or not isinstance(dhcp, bool):
        return FactProblemKind.MALFORMED
    return vrf, dhcp


def _rip_vrf_has_dhcp_interface(
    names: tuple[str, ...],
    enabled_networks: Mapping[str, tuple[IPv4Network, ...]],
    interfaces: Mapping[object, object],
) -> bool | FactProblemKind:
    """Return whether one of the named interfaces uses DHCP addressing in a VRF with an enabled RIP network."""
    problem: FactProblemKind | None = None
    for name in names:
        if name not in interfaces:
            continue
        addressing = _ipv4_dhcp_addressing(interfaces[name])
        if isinstance(addressing, FactProblemKind):
            problem = addressing if addressing is FactProblemKind.MALFORMED else problem or addressing
            continue
        vrf, dhcp = addressing
        if dhcp and vrf in enabled_networks:
            return True
    return problem or False


def _management_interface_names(interfaces: Mapping[object, object]) -> tuple[str, ...]:
    """Return the interfaces whose names start with ``Management``."""
    return tuple(name for name in interfaces if isinstance(name, str) and name.startswith("Management"))


@dataclass(frozen=True, slots=True)
class RipEnabledFact(FeatureFact, CommandsFactDefinition["RipEnabledFact"]):
    """Presence of a RIP instance that is not administratively shut down in any VRF."""

    feature: ClassVar[FeatureRef] = FeatureName.RIP
    key: ClassVar[str] = "feature.rip"
    label: ClassVar[str] = "RIP feature state"
    commands: ClassVar[tuple[AntaCommand, ...]] = (RIP_CONFIG_COMMAND,)

    @classmethod
    def parse(cls, commands: tuple[AntaCommand, ...]) -> Fact[RipEnabledFact]:
        """Normalize the explicitly rendered administrative state of every RIP instance."""
        (command,) = commands
        source = FactSource(command.command, FactSourceKind.COMMAND)
        if command.errors:
            return cls.unavailable(FactProblemKind.COLLECTION_FAILED, source)
        instances = _rip_instances(command.text_output)
        if instances is None:
            return cls.unavailable(FactProblemKind.MALFORMED, source)
        state = FeatureState.ENABLED if any(instance.enabled for instance in instances) else FeatureState.DISABLED
        return cls(state).available(source)


@dataclass(frozen=True, slots=True)
class RipMd5AuthenticationFact(FeatureFact, CommandsFactDefinition["RipMd5AuthenticationFact"]):
    """Presence of RIP MD5 authentication on an interface selected by an enabled RIP instance in the same VRF.

    An instance selects an interface when one of its ``network`` prefixes contains a current primary or secondary interface address,
    including an address leased by DHCP. Any MD5 authentication statement counts, including a key definition without a transmit key and a
    transmit key with ``rx-disabled``.
    """

    feature: ClassVar[FeatureRef] = SubFeature(FeatureName.RIP, "MD5 authentication")
    key: ClassVar[str] = "feature.rip.md5_authentication"
    label: ClassVar[str] = "RIP MD5 authentication state"
    commands: ClassVar[tuple[AntaCommand, ...]] = (RIP_CONFIG_COMMAND, RIP_AUTHENTICATION_CONFIG_COMMAND, IP_INTERFACE_COMMAND)

    @classmethod
    # pylint: disable-next=too-many-return-statements
    def parse(cls, commands: tuple[AntaCommand, ...]) -> Fact[RipMd5AuthenticationFact]:  # noqa: PLR0911
        """Correlate interface MD5 authentication with enabled RIP network prefixes in the interface VRF."""
        rip_command, authentication_command, interface_command = commands
        rip_source = FactSource(rip_command.command, FactSourceKind.COMMAND)
        authentication_source = FactSource(authentication_command.command, FactSourceKind.COMMAND)
        interface_source = FactSource(interface_command.command, FactSourceKind.COMMAND)

        if authentication_command.errors:
            return cls.unavailable(FactProblemKind.COLLECTION_FAILED, authentication_source)
        md5_interfaces = _rip_md5_interfaces(authentication_command.text_output)
        if md5_interfaces == ():
            return cls(FeatureState.DISABLED).available(authentication_source)
        if rip_command.errors:
            return cls.unavailable(FactProblemKind.COLLECTION_FAILED, rip_source)
        enabled_networks = _enabled_rip_networks(rip_command.text_output)
        if enabled_networks == {}:
            return cls(FeatureState.DISABLED).available(rip_source)
        if md5_interfaces is None:
            return cls.unavailable(FactProblemKind.MALFORMED, authentication_source)
        if enabled_networks is None:
            return cls.unavailable(FactProblemKind.MALFORMED, rip_source)

        if interface_command.errors:
            return cls.unavailable(FactProblemKind.COLLECTION_FAILED, interface_source)
        interfaces = interface_command.json_output.get("interfaces")
        if not isinstance(interfaces, Mapping):
            return cls.unavailable(FactProblemKind.MISSING if interfaces is None else FactProblemKind.MALFORMED, interface_source)
        selected = _rip_selects_interface(md5_interfaces, enabled_networks, interfaces)
        if isinstance(selected, FactProblemKind):
            return cls.unavailable(selected, interface_source)
        return cls(FeatureState.ENABLED).available(authentication_source) if selected else cls(FeatureState.DISABLED).available(interface_source)


@dataclass(frozen=True, slots=True)
class RipDhcpMd5InterfaceFact(ConfigurationFact, CommandsFactDefinition["RipDhcpMd5InterfaceFact"]):
    """Presence of a DHCP-addressed interface with RIP MD5 authentication in a VRF with an enabled RIP network.

    The current lease is not considered: a later lease can place the interface address within a RIP network without any configuration change.
    """

    feature: ClassVar[FeatureRef] = SubFeature(FeatureName.RIP, "DHCP MD5 authentication interface")
    key: ClassVar[str] = "configuration.rip.dhcp_md5_authentication_interface"
    label: ClassVar[str] = "RIP DHCP MD5 authentication interface configuration state"
    commands: ClassVar[tuple[AntaCommand, ...]] = (RIP_CONFIG_COMMAND, RIP_AUTHENTICATION_CONFIG_COMMAND, IP_INTERFACE_COMMAND)

    @classmethod
    # pylint: disable-next=too-many-return-statements
    def parse(cls, commands: tuple[AntaCommand, ...]) -> Fact[RipDhcpMd5InterfaceFact]:  # noqa: PLR0911
        """Correlate DHCP addressing of interfaces with RIP MD5 authentication with enabled RIP instances in the interface VRF."""
        rip_command, authentication_command, interface_command = commands
        rip_source = FactSource(rip_command.command, FactSourceKind.COMMAND)
        authentication_source = FactSource(authentication_command.command, FactSourceKind.COMMAND)
        interface_source = FactSource(interface_command.command, FactSourceKind.COMMAND)

        if authentication_command.errors:
            return cls.unavailable(FactProblemKind.COLLECTION_FAILED, authentication_source)
        md5_interfaces = _rip_md5_interfaces(authentication_command.text_output)
        if md5_interfaces == ():
            return cls(ConfigurationState.NOT_CONFIGURED).available(authentication_source)
        if rip_command.errors:
            return cls.unavailable(FactProblemKind.COLLECTION_FAILED, rip_source)
        enabled_networks = _enabled_rip_networks(rip_command.text_output)
        if enabled_networks == {}:
            return cls(ConfigurationState.NOT_CONFIGURED).available(rip_source)
        if md5_interfaces is None:
            return cls.unavailable(FactProblemKind.MALFORMED, authentication_source)
        if enabled_networks is None:
            return cls.unavailable(FactProblemKind.MALFORMED, rip_source)

        if interface_command.errors:
            return cls.unavailable(FactProblemKind.COLLECTION_FAILED, interface_source)
        interfaces = interface_command.json_output.get("interfaces")
        if not isinstance(interfaces, Mapping):
            return cls.unavailable(FactProblemKind.MISSING if interfaces is None else FactProblemKind.MALFORMED, interface_source)
        configured = _rip_vrf_has_dhcp_interface(md5_interfaces, enabled_networks, interfaces)
        if isinstance(configured, FactProblemKind):
            return cls.unavailable(configured, interface_source)
        return cls(ConfigurationState.CONFIGURED if configured else ConfigurationState.NOT_CONFIGURED).available(interface_source)


@dataclass(frozen=True, slots=True)
class RipManagementInterfaceFact(FeatureFact, CommandsFactDefinition["RipManagementInterfaceFact"]):
    """Presence of a management interface selected by an enabled RIP instance in the same VRF.

    Management interfaces are the interfaces whose names start with ``Management``. An instance selects one when one of its ``network`` prefixes contains a
    current primary or secondary interface address, including an address leased by DHCP. EOS does not render RIP processing on a management
    interface in its configuration, so selection is derived from the RIP networks and the interface addressing.
    """

    feature: ClassVar[FeatureRef] = SubFeature(FeatureName.RIP, "management interface")
    key: ClassVar[str] = "feature.rip.management_interface"
    label: ClassVar[str] = "RIP management interface state"
    commands: ClassVar[tuple[AntaCommand, ...]] = (RIP_CONFIG_COMMAND, IP_INTERFACE_COMMAND)

    @classmethod
    # pylint: disable-next=too-many-return-statements
    def parse(cls, commands: tuple[AntaCommand, ...]) -> Fact[RipManagementInterfaceFact]:  # noqa: PLR0911
        """Correlate management interface addresses with enabled RIP network prefixes in the interface VRF."""
        rip_command, interface_command = commands
        rip_source = FactSource(rip_command.command, FactSourceKind.COMMAND)
        interface_source = FactSource(interface_command.command, FactSourceKind.COMMAND)

        if rip_command.errors:
            return cls.unavailable(FactProblemKind.COLLECTION_FAILED, rip_source)
        enabled_networks = _enabled_rip_networks(rip_command.text_output)
        if enabled_networks is None:
            return cls.unavailable(FactProblemKind.MALFORMED, rip_source)
        if not enabled_networks:
            return cls(FeatureState.DISABLED).available(rip_source)

        if interface_command.errors:
            return cls.unavailable(FactProblemKind.COLLECTION_FAILED, interface_source)
        interfaces = interface_command.json_output.get("interfaces")
        if not isinstance(interfaces, Mapping):
            return cls.unavailable(FactProblemKind.MISSING if interfaces is None else FactProblemKind.MALFORMED, interface_source)
        selected = _rip_selects_interface(_management_interface_names(interfaces), enabled_networks, interfaces)
        if isinstance(selected, FactProblemKind):
            return cls.unavailable(selected, interface_source)
        return cls(FeatureState.ENABLED if selected else FeatureState.DISABLED).available(interface_source)


@dataclass(frozen=True, slots=True)
class RipDhcpManagementInterfaceFact(ConfigurationFact, CommandsFactDefinition["RipDhcpManagementInterfaceFact"]):
    """Presence of a DHCP-addressed management interface in a VRF with an enabled RIP network.

    Management interfaces are the interfaces whose names start with ``Management``. The current lease is not considered: a later lease can
    place the interface address within a RIP network without any configuration change.
    """

    feature: ClassVar[FeatureRef] = SubFeature(FeatureName.RIP, "DHCP management interface")
    key: ClassVar[str] = "configuration.rip.dhcp_management_interface"
    label: ClassVar[str] = "RIP DHCP management interface configuration state"
    commands: ClassVar[tuple[AntaCommand, ...]] = (RIP_CONFIG_COMMAND, IP_INTERFACE_COMMAND)

    @classmethod
    # pylint: disable-next=too-many-return-statements
    def parse(cls, commands: tuple[AntaCommand, ...]) -> Fact[RipDhcpManagementInterfaceFact]:  # noqa: PLR0911
        """Correlate DHCP addressing of management interfaces with enabled RIP instances in the interface VRF."""
        rip_command, interface_command = commands
        rip_source = FactSource(rip_command.command, FactSourceKind.COMMAND)
        interface_source = FactSource(interface_command.command, FactSourceKind.COMMAND)

        if rip_command.errors:
            return cls.unavailable(FactProblemKind.COLLECTION_FAILED, rip_source)
        enabled_networks = _enabled_rip_networks(rip_command.text_output)
        if enabled_networks is None:
            return cls.unavailable(FactProblemKind.MALFORMED, rip_source)
        if not enabled_networks:
            return cls(ConfigurationState.NOT_CONFIGURED).available(rip_source)

        if interface_command.errors:
            return cls.unavailable(FactProblemKind.COLLECTION_FAILED, interface_source)
        interfaces = interface_command.json_output.get("interfaces")
        if not isinstance(interfaces, Mapping):
            return cls.unavailable(FactProblemKind.MISSING if interfaces is None else FactProblemKind.MALFORMED, interface_source)
        configured = _rip_vrf_has_dhcp_interface(_management_interface_names(interfaces), enabled_networks, interfaces)
        if isinstance(configured, FactProblemKind):
            return cls.unavailable(configured, interface_source)
        return cls(ConfigurationState.CONFIGURED if configured else ConfigurationState.NOT_CONFIGURED).available(interface_source)
