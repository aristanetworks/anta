# Copyright (c) 2026 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Facts derived from EOS first-hop, discovery, and address-assignment services."""

from __future__ import annotations

import re
from collections.abc import Mapping
from dataclasses import dataclass
from enum import Enum
from typing import ClassVar

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
from anta.models import AntaCommand

VRRP_CONFIG_COMMAND = AntaCommand(command="show running-config section vrrp", ofmt="text")
VRRP_ANTI_REPLAY_COMMAND = AntaCommand(command="show running-config | include ^vrrp ipv4 authentication anti-replay$", ofmt="text")
DHCP_RELAY_COMMAND = OptionalAntaCommand(command="show ip dhcp relay", revision=1)
DHCP_RELAY_SCOPE_COMMAND = OptionalAntaCommand(command="show ip dhcp relay", ofmt="text")
DHCP_CONFIG_COMMAND = AntaCommand(command="show running-config section dhcp", ofmt="text")
DHCP_REPLY_VALIDATION_COMMAND = AntaCommand(command="show running-config | include ^\\s*reply source-address validation$", ofmt="text")
MLAG_COMMAND = OptionalAntaCommand(command="show mlag detail", revision=2)
IP_LOCKING_COMMAND = OptionalAntaCommand(command="show address locking", revision=1)

_VRRP_ADDRESS_FAMILY_PATTERN = re.compile(r"^vrrp (?P<id>\d+) (?P<family>ipv[46])(?:\s+(?:version (?P<version>[23])|\S+))?$")
_VRRP_IP_AH_PATTERN = re.compile(r"^vrrp (?P<id>\d+) peer authentication ietf-md5\b")
_DHCP_RELAY_INTERFACE_PATTERN = re.compile(r"^Interface:\s+(?P<name>\S+)\s*$")
_DHCP_RELAY_SERVERS_PATTERN = re.compile(r"^\s+DHCP(?P<family>v[46]) servers:\s*(?P<servers>.*)$")
_VRRP_VERSION_2 = 2


class IpAddressFamily(str, Enum):
    """IP address families exposed by DHCP relay and covered by IP locking."""

    IPV4 = "IPv4"
    IPV6 = "IPv6"


@dataclass(frozen=True, slots=True)
class DhcpRelayInterface:
    """One DHCP relay interface and the helper-address families configured on it."""

    name: str
    families: frozenset[IpAddressFamily]


@dataclass(frozen=True, slots=True)
class DhcpRelayScope:
    """Operational DHCP relay interfaces and their active helper-address families."""

    interfaces: tuple[DhcpRelayInterface, ...]


@dataclass(frozen=True, slots=True)
class IpLockingScope:
    """One interface or VLAN and its enforcement-disabled IP address families."""

    name: str
    families: frozenset[IpAddressFamily]


@dataclass(frozen=True, slots=True)
class IpLockingCoverage:
    """Operational enforcement-disabled IP-locking coverage."""

    interfaces: tuple[IpLockingScope, ...]
    vlans: tuple[IpLockingScope, ...]


def _source(command: AntaCommand) -> FactSource:
    """Build an exact command source."""
    return FactSource(command.command, FactSourceKind.COMMAND)


def _vrrp_state(config: str) -> tuple[bool, bool]:
    """Return configured VRRP and VRRPv2 IP-AH exposure states."""
    configured = False
    versions: dict[tuple[str, str], int] = {}
    ip_ah: set[tuple[str, str]] = set()
    interface = ""
    for raw_line in config.splitlines():
        line = raw_line.strip()
        if not line or line == "!":
            continue
        if raw_line == raw_line.lstrip():
            interface = line.removeprefix("interface ") if line.startswith("interface ") else ""
            continue
        if (match := _VRRP_ADDRESS_FAMILY_PATTERN.match(line)) is not None:
            configured = True
            if match.group("family") != "ipv4":
                continue
            identity = (interface, match.group("id"))
            if (version := match.group("version")) is not None:
                versions[identity] = int(version)
            else:
                versions.setdefault(identity, _VRRP_VERSION_2)
        elif (match := _VRRP_IP_AH_PATTERN.match(line)) is not None:
            ip_ah.add((interface, match.group("id")))
    exposed = any(identity in versions and versions[identity] == _VRRP_VERSION_2 for identity in ip_ah)
    return configured, exposed


@dataclass(frozen=True, slots=True)
class VrrpFact(FeatureFact, CommandsFactDefinition["VrrpFact"]):
    """Presence of at least one configured VRRPv2 or VRRPv3 virtual router."""

    feature: ClassVar[FeatureRef] = FeatureName.VRRP
    key: ClassVar[str] = "feature.vrrp"
    label: ClassVar[str] = "VRRP feature state"
    commands: ClassVar[tuple[AntaCommand, ...]] = (VRRP_CONFIG_COMMAND,)

    @classmethod
    def parse(cls, commands: tuple[AntaCommand, ...]) -> Fact[VrrpFact]:
        """Normalize VRRP presence from its configuration section."""
        (command,) = commands
        configured, _ = _vrrp_state(command.text_output)
        state = FeatureState.ENABLED if configured else FeatureState.DISABLED
        return cls(state).available(_source(command))


@dataclass(frozen=True, slots=True)
class VrrpV2IpAhFact(FeatureFact, CommandsFactDefinition["VrrpV2IpAhFact"]):
    """Presence of VRRPv2 IP-AH authentication on one virtual router."""

    feature: ClassVar[FeatureRef] = SubFeature(FeatureName.VRRP, "version 2 IP-AH authentication")
    key: ClassVar[str] = "feature.vrrp.v2_ip_ah"
    label: ClassVar[str] = "VRRPv2 IP-AH authentication state"
    commands: ClassVar[tuple[AntaCommand, ...]] = (VRRP_CONFIG_COMMAND,)

    @classmethod
    def parse(cls, commands: tuple[AntaCommand, ...]) -> Fact[VrrpV2IpAhFact]:
        """Correlate VRRP version and IP-AH authentication by interface and virtual-router ID."""
        (command,) = commands
        _, exposed = _vrrp_state(command.text_output)
        state = FeatureState.ENABLED if exposed else FeatureState.DISABLED
        return cls(state).available(_source(command))


@dataclass(frozen=True, slots=True)
class VrrpAntiReplayFact(FeatureFact, CommandsFactDefinition["VrrpAntiReplayFact"]):
    """Presence of the global VRRP authentication anti-replay setting."""

    feature: ClassVar[FeatureRef] = SubFeature(FeatureName.VRRP, "authentication anti-replay")
    key: ClassVar[str] = "feature.vrrp.authentication_anti_replay"
    label: ClassVar[str] = "VRRP authentication anti-replay state"
    commands: ClassVar[tuple[AntaCommand, ...]] = (VRRP_ANTI_REPLAY_COMMAND,)

    @classmethod
    def parse(cls, commands: tuple[AntaCommand, ...]) -> Fact[VrrpAntiReplayFact]:
        """Normalize the exact global configuration line."""
        (command,) = commands
        lines = tuple(line.strip() for line in command.text_output.splitlines() if line.strip())
        if any(line != "vrrp ipv4 authentication anti-replay" for line in lines):
            return cls.unavailable(FactProblemKind.MALFORMED, _source(command))
        state = FeatureState.ENABLED if lines else FeatureState.DISABLED
        return cls(state).available(_source(command))


@dataclass(frozen=True, slots=True)
class DhcpRelayActiveFact(FeatureFact, CommandsFactDefinition["DhcpRelayActiveFact"]):
    """Effective DHCP relay state with at least one helper address."""

    feature: ClassVar[FeatureRef] = SubFeature(FeatureName.DHCP, "relay")
    key: ClassVar[str] = "feature.dhcp.relay"
    label: ClassVar[str] = "DHCP relay state"
    commands: ClassVar[tuple[AntaCommand, ...]] = (DHCP_RELAY_COMMAND,)

    @classmethod
    def parse(cls, commands: tuple[AntaCommand, ...]) -> Fact[DhcpRelayActiveFact]:
        """Normalize the structured relay activity state."""
        (command,) = commands
        source = _source(command)
        if is_unsupported_optional_command(command):
            return cls(FeatureState.UNSUPPORTED).available(source)
        active = _required_bool(command.json_output, "activeState")
        if isinstance(active, FactProblemKind):
            return cls.unavailable(active, source)
        return cls(FeatureState.ENABLED if active else FeatureState.DISABLED).available(source)


def _parse_dhcp_relay_scope(output: str) -> DhcpRelayScope | None:
    """Deserialize relay interfaces and helper-address families from EOS text output."""
    interfaces: dict[str, set[IpAddressFamily]] = {}
    current_interface: str | None = None
    for line in output.splitlines():
        if (interface_match := _DHCP_RELAY_INTERFACE_PATTERN.match(line)) is not None:
            if (interface_name := interface_match.group("name")) is None:
                continue
            current_interface = interface_name
            interfaces.setdefault(interface_name, set())
            continue
        if current_interface is None or (servers_match := _DHCP_RELAY_SERVERS_PATTERN.match(line)) is None:
            continue
        if not servers_match.group("servers").strip():
            continue
        family = IpAddressFamily.IPV4 if servers_match.group("family") == "v4" else IpAddressFamily.IPV6
        interfaces[current_interface].add(family)

    populated = tuple(DhcpRelayInterface(name, frozenset(families)) for name, families in interfaces.items() if families)
    return DhcpRelayScope(populated) if populated else None


@dataclass(frozen=True, slots=True)
class DhcpRelayScopeFact(CommandsFactDefinition["DhcpRelayScopeFact"]):
    """Operational DHCP relay interfaces and helper-address families."""

    interfaces: tuple[DhcpRelayInterface, ...]
    key: ClassVar[str] = "feature.dhcp.relay.scope"
    label: ClassVar[str] = "DHCP relay interface and address-family scope"
    commands: ClassVar[tuple[AntaCommand, ...]] = (DHCP_RELAY_SCOPE_COMMAND,)

    @classmethod
    def parse(cls, commands: tuple[AntaCommand, ...]) -> Fact[DhcpRelayScopeFact]:
        """Normalize the interface and address-family blocks from relay output."""
        (command,) = commands
        source = _source(command)
        if is_unsupported_optional_command(command) or "DHCP relay is not active" in command.text_output:
            return cls(()).available(source)
        if "DHCP relay is active" not in command.text_output:
            problem = FactProblemKind.MISSING if not command.text_output.strip() else FactProblemKind.MALFORMED
            return cls.unavailable(problem, source)
        if (scope := _parse_dhcp_relay_scope(command.text_output)) is None:
            return cls.unavailable(FactProblemKind.MISSING, source)
        return cls(scope.interfaces).available(source)


def _parse_ip_locking_family(data: Mapping[str, object], family: IpAddressFamily, prefix: str) -> IpAddressFamily | FactProblemKind | None:
    """Deserialize one enabled IP address family from an IP-locking scope."""
    enabled = _required_bool(data, f"{prefix}Enabled")
    if isinstance(enabled, FactProblemKind):
        return enabled
    if not enabled:
        return None
    mode = data.get(f"{prefix}Mode")
    if mode is None:
        return FactProblemKind.MISSING
    if not isinstance(mode, str):
        return FactProblemKind.MALFORMED
    return family if mode == "enforcementDisabled" else None


def _parse_ip_locking_scopes(value: object) -> tuple[IpLockingScope, ...] | FactProblemKind:
    """Deserialize operational IP-locking scopes from one JSON mapping."""
    if value is None:
        return FactProblemKind.MISSING
    if not isinstance(value, Mapping):
        return FactProblemKind.MALFORMED
    scopes: list[IpLockingScope] = []
    for name, data in value.items():
        if not isinstance(name, (str, int)) or not isinstance(data, Mapping):
            return FactProblemKind.MALFORMED
        families: set[IpAddressFamily] = set()
        for family, prefix in ((IpAddressFamily.IPV4, "ipv4"), (IpAddressFamily.IPV6, "ipv6")):
            parsed_family = _parse_ip_locking_family(data, family, prefix)
            if isinstance(parsed_family, FactProblemKind):
                return parsed_family
            if parsed_family is not None:
                families.add(parsed_family)
        scopes.append(IpLockingScope(str(name), frozenset(families)))
    return tuple(scopes)


def _parse_ip_locking_coverage(output: Mapping[str, object]) -> tuple[bool, IpLockingCoverage] | FactProblemKind:
    """Deserialize IP-locking activity and enforcement-disabled scope."""
    active = _required_bool(output, "active")
    if isinstance(active, FactProblemKind):
        return active
    if not active:
        return False, IpLockingCoverage((), ())
    interfaces = _parse_ip_locking_scopes(output.get("enabledIntfs"))
    vlans = _parse_ip_locking_scopes(output.get("enabledVlans"))
    if isinstance(interfaces, FactProblemKind):
        return interfaces
    if isinstance(vlans, FactProblemKind):
        return vlans
    return True, IpLockingCoverage(interfaces, vlans)


@dataclass(frozen=True, slots=True)
class IpLockingMitigationFact(MitigationFact, CommandsFactDefinition["IpLockingMitigationFact"]):
    """Operational IP locking with locked-address enforcement disabled."""

    key: ClassVar[str] = "mitigation.ip_locking.enforcement_disabled"
    label: ClassVar[str] = "IP locking with locked-address enforcement disabled"
    commands: ClassVar[tuple[AntaCommand, ...]] = (IP_LOCKING_COMMAND,)

    @classmethod
    def parse(cls, commands: tuple[AntaCommand, ...]) -> Fact[IpLockingMitigationFact]:
        """Normalize whether any operational scope uses enforcement-disabled mode."""
        (command,) = commands
        source = _source(command)
        if is_unsupported_optional_command(command):
            return cls(MitigationState.INEFFECTIVE).available(source)
        if isinstance((parsed := _parse_ip_locking_coverage(command.json_output)), FactProblemKind):
            return cls.unavailable(parsed, source)
        active, coverage = parsed
        effective = active and any(scope.families for scope in (*coverage.interfaces, *coverage.vlans))
        state = MitigationState.EFFECTIVE if effective else MitigationState.INEFFECTIVE
        return cls(state).available(source)


@dataclass(frozen=True, slots=True)
class IpLockingCoverageFact(CommandsFactDefinition["IpLockingCoverageFact"]):
    """Operational interface and VLAN coverage of enforcement-disabled IP locking."""

    interfaces: tuple[IpLockingScope, ...]
    vlans: tuple[IpLockingScope, ...]
    key: ClassVar[str] = "feature.ip_locking.enforcement_disabled_scope"
    label: ClassVar[str] = "IP locking enforcement-disabled scope"
    commands: ClassVar[tuple[AntaCommand, ...]] = (IP_LOCKING_COMMAND,)

    @classmethod
    def parse(cls, commands: tuple[AntaCommand, ...]) -> Fact[IpLockingCoverageFact]:
        """Normalize enforcement-disabled interface and VLAN address families."""
        (command,) = commands
        source = _source(command)
        if is_unsupported_optional_command(command):
            return cls((), ()).available(source)
        if isinstance((parsed := _parse_ip_locking_coverage(command.json_output)), FactProblemKind):
            return cls.unavailable(parsed, source)
        _, coverage = parsed
        return cls(coverage.interfaces, coverage.vlans).available(source)


@dataclass(frozen=True, slots=True)
class DhcpReplySourceValidationFact(FeatureFact, CommandsFactDefinition["DhcpReplySourceValidationFact"]):
    """Presence of DHCP relay reply source-address validation."""

    feature: ClassVar[FeatureRef] = SubFeature(FeatureName.DHCP, "relay reply source-address validation")
    key: ClassVar[str] = "feature.dhcp.reply_source_validation"
    label: ClassVar[str] = "DHCP relay reply source-address validation state"
    commands: ClassVar[tuple[AntaCommand, ...]] = (DHCP_REPLY_VALIDATION_COMMAND,)

    @classmethod
    def parse(cls, commands: tuple[AntaCommand, ...]) -> Fact[DhcpReplySourceValidationFact]:
        """Normalize the exact configuration line."""
        (command,) = commands
        lines = tuple(line.strip() for line in command.text_output.splitlines() if line.strip())
        if any(line != "reply source-address validation" for line in lines):
            return cls.unavailable(FactProblemKind.MALFORMED, _source(command))
        state = FeatureState.ENABLED if lines else FeatureState.DISABLED
        return cls(state).available(_source(command))


def _dhcp_option82_config_exposed(config: str) -> bool:
    """Return whether a snooping or server Option 82 exposure path is configured."""
    snooping_enabled = False
    snooping_option = False
    snooping_vlan = False
    server_match = False
    for raw_line in config.splitlines():
        line = raw_line.strip()
        snooping_enabled |= line == "ip dhcp snooping"
        snooping_option |= line == "ip dhcp snooping information option"
        snooping_vlan |= line.startswith("ip dhcp snooping vlan ")
        server_match |= line.startswith("information option arista-switch ")
    return (snooping_enabled and snooping_option and snooping_vlan) or server_match


def _required_bool(output: Mapping[str, object], key: str) -> bool | FactProblemKind:
    """Return one required boolean field from structured command output."""
    value = output.get(key)
    if value is None:
        return FactProblemKind.MISSING
    if not isinstance(value, bool):
        return FactProblemKind.MALFORMED
    return value


@dataclass(frozen=True, slots=True)
class DhcpOption82Fact(FeatureFact, CommandsFactDefinition["DhcpOption82Fact"]):
    """Presence of any DHCP relay, snooping, or server Option 82 exposure path."""

    feature: ClassVar[FeatureRef] = SubFeature(FeatureName.DHCP, "Option 82 exposure")
    key: ClassVar[str] = "feature.dhcp.option82"
    label: ClassVar[str] = "DHCP Option 82 state"
    commands: ClassVar[tuple[AntaCommand, ...]] = (DHCP_CONFIG_COMMAND, DHCP_RELAY_COMMAND)

    @classmethod
    # pylint: disable-next=too-many-return-statements
    def parse(cls, commands: tuple[AntaCommand, ...]) -> Fact[DhcpOption82Fact]:  # noqa: PLR0911
        """Evaluate the three source-defined exposure alternatives."""
        config_command, relay_command = commands
        if _dhcp_option82_config_exposed(config_command.text_output):
            return cls(FeatureState.ENABLED).available(_source(config_command))
        if is_unsupported_optional_command(relay_command):
            return cls(FeatureState.DISABLED).available(_source(relay_command))

        output = relay_command.json_output
        active = _required_bool(output, "activeState")
        if isinstance(active, FactProblemKind):
            return cls.unavailable(active, _source(relay_command))
        if active is False:
            return cls(FeatureState.DISABLED).available(_source(relay_command))
        option82 = _required_bool(output, "option82")
        if isinstance(option82, FactProblemKind):
            return cls.unavailable(option82, _source(relay_command))
        if option82 is False:
            return cls(FeatureState.DISABLED).available(_source(relay_command))
        return cls(FeatureState.ENABLED).available(_source(relay_command))


@dataclass(frozen=True, slots=True)
class MlagDualPrimaryErrdisableFact(FeatureFact, CommandsFactDefinition["MlagDualPrimaryErrdisableFact"]):
    """MLAG dual-primary heartbeat configuration with errdisable-all action."""

    feature: ClassVar[FeatureRef] = SubFeature(FeatureName.MLAG, "dual-primary heartbeat with errdisable-all action")
    key: ClassVar[str] = "feature.mlag.dual_primary_errdisable"
    label: ClassVar[str] = "MLAG dual-primary errdisable exposure state"
    commands: ClassVar[tuple[AntaCommand, ...]] = (MLAG_COMMAND,)

    @classmethod
    # pylint: disable-next=too-many-return-statements
    def parse(cls, commands: tuple[AntaCommand, ...]) -> Fact[MlagDualPrimaryErrdisableFact]:  # noqa: PLR0911
        """Require the stable MLAG and dual-primary configuration prerequisites."""
        (command,) = commands
        source = _source(command)
        if is_unsupported_optional_command(command):
            return cls(FeatureState.UNSUPPORTED).available(source)
        output = command.json_output
        domain_id = output.get("domainId")
        peer_link = output.get("peerLink")
        heartbeat_peer = output.get("heartbeatPeerAddress")
        if any(value is not None and not isinstance(value, str) for value in (domain_id, peer_link, heartbeat_peer)):
            return cls.unavailable(FactProblemKind.MALFORMED, source)
        if not domain_id or not peer_link or heartbeat_peer in (None, "", "0.0.0.0"):  # noqa: S104 - EOS uses 0.0.0.0 for an unset heartbeat address
            return cls(FeatureState.DISABLED).available(source)
        detail = output.get("detail")
        if not isinstance(detail, Mapping):
            problem = FactProblemKind.MISSING if detail is None else FactProblemKind.MALFORMED
            return cls.unavailable(problem, source)
        detection_delay = detail.get("dualPrimaryDetectionDelay")
        action = detail.get("dualPrimaryAction")
        if detection_delay is None and action is None:
            return cls(FeatureState.DISABLED).available(source)
        if detection_delay is None or action is None:
            return cls.unavailable(FactProblemKind.MISSING, source)
        if isinstance(detection_delay, bool) or not isinstance(detection_delay, int) or not isinstance(action, str):
            return cls.unavailable(FactProblemKind.MALFORMED, source)
        errdisable_all = action == "errdisableAllInterfaces"
        state = FeatureState.ENABLED if errdisable_all else FeatureState.DISABLED
        return cls(state).available(source)


@dataclass(frozen=True, slots=True)
class MlagConfiguredFact(FeatureFact, CommandsFactDefinition["MlagConfiguredFact"]):
    """Complete persistent MLAG configuration."""

    feature: ClassVar[FeatureRef] = SubFeature(FeatureName.MLAG, "configuration")
    key: ClassVar[str] = "feature.mlag.configured"
    label: ClassVar[str] = "MLAG configuration state"
    commands: ClassVar[tuple[AntaCommand, ...]] = (MLAG_COMMAND,)

    @classmethod
    def parse(cls, commands: tuple[AntaCommand, ...]) -> Fact[MlagConfiguredFact]:
        """Require the MLAG domain, local interface, peer address, and peer link without considering operational state."""
        (command,) = commands
        source = _source(command)
        if is_unsupported_optional_command(command):
            return cls(FeatureState.UNSUPPORTED).available(source)
        configured_values = tuple(command.json_output.get(field) for field in ("domainId", "localInterface", "peerAddress", "peerLink"))
        if any(value is not None and not isinstance(value, str) for value in configured_values):
            return cls.unavailable(FactProblemKind.MALFORMED, source)
        configured = all(configured_values)
        state = FeatureState.ENABLED if configured else FeatureState.DISABLED
        return cls(state).available(source)
