# Copyright (c) 2026 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Unit tests for first-hop, discovery, and address-assignment facts."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from anta._advisory.facts.models import AvailableFact, FactProblemKind, FeatureState, MitigationState, UnavailableFact
from anta._advisory.facts.network_services import (
    DhcpOption82Fact,
    DhcpRelayActiveFact,
    DhcpRelayScopeFact,
    DhcpReplySourceValidationFact,
    IpAddressFamily,
    IpLockingCoverageFact,
    IpLockingMitigationFact,
    MlagConfiguredFact,
    MlagDualPrimaryErrdisableFact,
    VrrpAntiReplayFact,
    VrrpFact,
    VrrpV2IpAhFact,
)
from tests.units.anta_tests.advisories import OfflineAntaDevice

if TYPE_CHECKING:
    from typing import Any

    from anta._advisory.facts.models import CommandsFactDefinition, FeatureValue
    from anta.models import AntaCommand


@pytest.fixture(name="device")
def fact_device_fixture() -> OfflineAntaDevice:
    """Return an offline device suitable for fact derivation."""
    return OfflineAntaDevice("unit-test")


def command(definition: type[CommandsFactDefinition[Any]], output: dict[str, object] | str | None) -> AntaCommand:
    """Return one populated command declared by a fact."""
    populated = definition.commands[0].model_copy()
    populated.output = output
    return populated


def derive_state(
    device: OfflineAntaDevice,
    definition: type[CommandsFactDefinition[FeatureValue]],
    output: dict[str, object] | str,
) -> FeatureState:
    """Derive one feature fact and return its state."""
    fact = definition.derive(device, (command(definition, output),))
    assert isinstance(fact, AvailableFact)
    return fact.value.state


def derive_option82_state(device: OfflineAntaDevice, config_output: str, relay_output: dict[str, object]) -> FeatureState:
    """Derive the DHCP Option 82 fact from its configuration and operational commands."""
    config_command, relay_command = (declared.model_copy() for declared in DhcpOption82Fact.commands)
    config_command.output = config_output
    relay_command.output = relay_output
    fact = DhcpOption82Fact.derive(device, (config_command, relay_command))
    assert isinstance(fact, AvailableFact)
    return fact.value.state


VRRP_V2_IP_AH = """interface Ethernet1
   vrrp 1 ipv4 192.0.2.1
   vrrp 1 peer authentication ietf-md5 key-string 7 REDACTED
!"""
VRRP_V3_IP_AH = """interface Ethernet1
   vrrp 1 ipv4 version 3
   vrrp 1 ipv4 192.0.2.1
   vrrp 1 peer authentication ietf-md5 key-string 7 REDACTED
!"""
VRRP_V3_IPV6 = """interface Ethernet1
   vrrp 1 ipv6 2001:db8::1
!"""


@pytest.mark.parametrize(
    ("output", "vrrp_state", "ip_ah_state"),
    [
        ("", FeatureState.DISABLED, FeatureState.DISABLED),
        (VRRP_V2_IP_AH, FeatureState.ENABLED, FeatureState.ENABLED),
        (VRRP_V3_IP_AH, FeatureState.ENABLED, FeatureState.DISABLED),
        (VRRP_V3_IPV6, FeatureState.ENABLED, FeatureState.DISABLED),
        ("interface Ethernet1\n   vrrp 1 ipv4 192.0.2.1", FeatureState.ENABLED, FeatureState.DISABLED),
        (
            "interface Ethernet1\n   vrrp 1 ipv4 192.0.2.1\n   vrrp 2 peer authentication ietf-md5 key-string 7 REDACTED",
            FeatureState.ENABLED,
            FeatureState.DISABLED,
        ),
    ],
)
def test_vrrp_states(
    device: OfflineAntaDevice,
    output: str,
    vrrp_state: FeatureState,
    ip_ah_state: FeatureState,
) -> None:
    """Normalize VRRP presence and correlate version 2 IP-AH by virtual-router identity."""
    assert derive_state(device, VrrpFact, output) is vrrp_state
    assert derive_state(device, VrrpV2IpAhFact, output) is ip_ah_state


@pytest.mark.parametrize(
    ("output", "state"),
    [("", FeatureState.DISABLED), ("vrrp ipv4 authentication anti-replay", FeatureState.ENABLED)],
)
def test_vrrp_anti_replay_states(device: OfflineAntaDevice, output: str, state: FeatureState) -> None:
    """Normalize absent and configured VRRP anti-replay state."""
    assert derive_state(device, VrrpAntiReplayFact, output) is state


def test_vrrp_anti_replay_rejects_unexpected_output(device: OfflineAntaDevice) -> None:
    """Reject output outside the narrow anti-replay grammar."""
    populated = command(VrrpAntiReplayFact, "vrrp ipv4 authentication other")
    fact = VrrpAntiReplayFact.derive(device, (populated,))
    assert isinstance(fact, UnavailableFact)
    assert fact.problem is FactProblemKind.MALFORMED


@pytest.mark.parametrize(
    ("output", "state"),
    [({"activeState": True}, FeatureState.ENABLED), ({"activeState": False}, FeatureState.DISABLED)],
)
def test_dhcp_relay_states(device: OfflineAntaDevice, output: dict[str, object], state: FeatureState) -> None:
    """Normalize structured DHCP relay status."""
    assert derive_state(device, DhcpRelayActiveFact, output) is state


@pytest.mark.parametrize("output", [{}, {"activeState": "yes"}])
def test_dhcp_relay_rejects_incomplete_output(device: OfflineAntaDevice, output: dict[str, object]) -> None:
    """Reject missing or malformed structured relay status."""
    fact = DhcpRelayActiveFact.derive(device, (command(DhcpRelayActiveFact, output),))
    assert isinstance(fact, UnavailableFact)


def test_dhcp_relay_unsupported_proves_absence(device: OfflineAntaDevice) -> None:
    """Treat the feature-specific unsupported response as proven absence."""
    populated = command(DhcpRelayActiveFact, "")
    populated.output = None
    populated.errors = ["This command is not supported on this hardware platform"]
    fact = DhcpRelayActiveFact.derive(device, (populated,))
    assert isinstance(fact, AvailableFact)
    assert fact.value.state is FeatureState.UNSUPPORTED


DHCP_RELAY_DUAL_STACK = """DHCP relay is active
Interface: Vlan100
  DHCP all subnet relaying is disabled
  DHCPv4 servers: 192.0.2.10
  DHCPv6 servers: 2001:db8::10
Interface: Ethernet3
  DHCPv4 servers: 192.0.2.20
  DHCPv6 servers:"""


def test_dhcp_relay_scope(device: OfflineAntaDevice) -> None:
    """Normalize each active relay interface and its non-empty helper-address families."""
    fact = DhcpRelayScopeFact.derive(device, (command(DhcpRelayScopeFact, DHCP_RELAY_DUAL_STACK),))
    assert isinstance(fact, AvailableFact)
    assert tuple((interface.name, interface.families) for interface in fact.value.interfaces) == (
        ("Vlan100", frozenset((IpAddressFamily.IPV4, IpAddressFamily.IPV6))),
        ("Ethernet3", frozenset((IpAddressFamily.IPV4,))),
    )


@pytest.mark.parametrize("output", ["", "DHCP relay is active", "DHCP relay status unavailable"])
def test_dhcp_relay_scope_rejects_incomplete_active_output(device: OfflineAntaDevice, output: str) -> None:
    """Reject active relay output that does not identify its interfaces and families."""
    fact = DhcpRelayScopeFact.derive(device, (command(DhcpRelayScopeFact, output),))
    assert isinstance(fact, UnavailableFact)


def test_inactive_dhcp_relay_has_empty_scope(device: OfflineAntaDevice) -> None:
    """Normalize inactive relay output without requiring interface blocks."""
    fact = DhcpRelayScopeFact.derive(device, (command(DhcpRelayScopeFact, "DHCP relay is not active"),))
    assert isinstance(fact, AvailableFact)
    assert fact.value.interfaces == ()


IP_LOCKING_DUAL_STACK = {
    "active": True,
    "enabledIntfs": {
        "Ethernet48": {
            "ipv4Enabled": True,
            "ipv4Mode": "enforcementDisabled",
            "ipv6Enabled": True,
            "ipv6Mode": "enforcementDisabled",
            "assignedVlans": {},
        }
    },
    "enabledVlans": {
        "100": {
            "ipv4Enabled": True,
            "ipv4Mode": "enforcementDisabled",
            "ipv6Enabled": True,
            "ipv6Mode": "enforcementDisabled",
        }
    },
}


def test_ip_locking_operational_coverage(device: OfflineAntaDevice) -> None:
    """Normalize enforcement-disabled families for operational interfaces and VLANs."""
    mitigation = IpLockingMitigationFact.derive(device, (command(IpLockingMitigationFact, IP_LOCKING_DUAL_STACK),))
    coverage = IpLockingCoverageFact.derive(device, (command(IpLockingCoverageFact, IP_LOCKING_DUAL_STACK),))
    assert isinstance(mitigation, AvailableFact)
    assert mitigation.value.state is MitigationState.EFFECTIVE
    assert isinstance(coverage, AvailableFact)
    assert tuple((scope.name, scope.families) for scope in coverage.value.interfaces) == (("Ethernet48", frozenset((IpAddressFamily.IPV4, IpAddressFamily.IPV6))),)
    assert tuple((scope.name, scope.families) for scope in coverage.value.vlans) == (("100", frozenset((IpAddressFamily.IPV4, IpAddressFamily.IPV6))),)


@pytest.mark.parametrize(
    "output",
    [
        {"active": False, "inactiveReason": "No interface or VLAN configured"},
        {
            "active": True,
            "enabledIntfs": {"Ethernet48": {"ipv4Enabled": True, "ipv4Mode": "enforcementEnabled", "ipv6Enabled": False}},
            "enabledVlans": {},
        },
    ],
)
def test_ip_locking_without_enforcement_disabled_scope_is_ineffective(device: OfflineAntaDevice, output: dict[str, object]) -> None:
    """Treat inactive IP locking or enforcement-enabled-only scope as an absent mitigation."""
    fact = IpLockingMitigationFact.derive(device, (command(IpLockingMitigationFact, output),))
    assert isinstance(fact, AvailableFact)
    assert fact.value.state is MitigationState.INEFFECTIVE


@pytest.mark.parametrize("definition", [IpLockingMitigationFact, IpLockingCoverageFact])
def test_ip_locking_rejects_incomplete_json(device: OfflineAntaDevice, definition: type[IpLockingMitigationFact | IpLockingCoverageFact]) -> None:
    """Reject active IP-locking output without complete operational scope fields."""
    fact = definition.derive(device, (command(definition, {"active": True, "enabledIntfs": {}}),))
    assert isinstance(fact, UnavailableFact)


def test_unsupported_ip_locking_proves_absent_mitigation(device: OfflineAntaDevice) -> None:
    """Treat a feature-specific unsupported response as an ineffective mitigation."""
    populated = command(IpLockingMitigationFact, None)
    populated.errors = ["This command is not supported on this hardware platform"]
    fact = IpLockingMitigationFact.derive(device, (populated,))
    assert isinstance(fact, AvailableFact)
    assert fact.value.state is MitigationState.INEFFECTIVE


def test_unsupported_ip_locking_has_empty_coverage(device: OfflineAntaDevice) -> None:
    """Treat a feature-specific unsupported response as empty operational coverage."""
    populated = command(IpLockingCoverageFact, None)
    populated.errors = ["This command is not supported on this hardware platform"]
    fact = IpLockingCoverageFact.derive(device, (populated,))
    assert isinstance(fact, AvailableFact)
    assert fact.value.interfaces == ()
    assert fact.value.vlans == ()


@pytest.mark.parametrize(
    ("output", "state"),
    [("", FeatureState.DISABLED), ("reply source-address validation", FeatureState.ENABLED)],
)
def test_dhcp_reply_validation_states(device: OfflineAntaDevice, output: str, state: FeatureState) -> None:
    """Normalize DHCP relay reply validation configuration."""
    assert derive_state(device, DhcpReplySourceValidationFact, output) is state


@pytest.mark.parametrize(
    ("config_output", "relay_output"),
    [
        (
            "ip dhcp relay information option\ninterface Management1\n   ip address dhcp",
            {"activeState": True, "option82": True},
        ),
        ("ip dhcp snooping\nip dhcp snooping information option\nip dhcp snooping vlan 100", {}),
        ("dhcp server\n   client class ipv4 definition client\n      match\n         information option arista-switch Ethernet1 vlan 100", {}),
    ],
)
def test_dhcp_option82_exposure_paths(device: OfflineAntaDevice, config_output: str, relay_output: dict[str, object]) -> None:
    """Recognize each source-defined DHCP Option 82 alternative."""
    assert derive_option82_state(device, config_output, relay_output) is FeatureState.ENABLED


@pytest.mark.parametrize(
    ("config_output", "relay_output"),
    [
        ("", {"activeState": False}),
        ("ip dhcp relay information option", {"activeState": False}),
        ("", {"activeState": True, "option82": False}),
        ("ip dhcp snooping information option", {"activeState": False}),
        ("ip dhcp snooping\nip dhcp snooping information option", {"activeState": False}),
        ("ip dhcp snooping information option\nip dhcp snooping vlan 100", {"activeState": False}),
    ],
)
def test_dhcp_option82_incomplete_paths_are_disabled(device: OfflineAntaDevice, config_output: str, relay_output: dict[str, object]) -> None:
    """Require every member of a selected Option 82 path."""
    assert derive_option82_state(device, config_output, relay_output) is FeatureState.DISABLED


def test_dhcp_option82_rejects_incomplete_relay_output(device: OfflineAntaDevice) -> None:
    """Reject an active relay response that omits the required Option 82 state."""
    config_command, relay_command = (declared.model_copy() for declared in DhcpOption82Fact.commands)
    config_command.output = ""
    relay_command.output = {"activeState": True}
    fact = DhcpOption82Fact.derive(device, (config_command, relay_command))
    assert isinstance(fact, UnavailableFact)
    assert fact.problem is FactProblemKind.MISSING


def test_dhcp_option82_rejects_invalid_relay_output(device: OfflineAntaDevice) -> None:
    """Reject a non-boolean structured Option 82 state."""
    config_command, relay_command = (declared.model_copy() for declared in DhcpOption82Fact.commands)
    config_command.output = ""
    relay_command.output = {"activeState": True, "option82": "enabled"}
    fact = DhcpOption82Fact.derive(device, (config_command, relay_command))
    assert isinstance(fact, UnavailableFact)
    assert fact.problem is FactProblemKind.MALFORMED


MLAG_EXPOSED = {
    "domainId": "mlagDomain",
    "localInterface": "Vlan4094",
    "peerAddress": "192.0.2.2",
    "peerLink": "Port-Channel10",
    "state": "inactive",
    "peerLinkStatus": "lowerLayerDown",
    "heartbeatPeerAddress": "192.0.2.2",
    "dualPrimaryDetectionState": "disabled",
    "detail": {"dualPrimaryDetectionDelay": 5, "dualPrimaryAction": "errdisableAllInterfaces"},
}


@pytest.mark.parametrize(
    ("output", "state"),
    [
        (MLAG_EXPOSED, FeatureState.ENABLED),
        ({key: value for key, value in MLAG_EXPOSED.items() if key != "domainId"}, FeatureState.DISABLED),
        ({**MLAG_EXPOSED, "peerLink": ""}, FeatureState.DISABLED),
        ({**MLAG_EXPOSED, "heartbeatPeerAddress": "0.0.0.0"}, FeatureState.DISABLED),  # noqa: S104 - EOS's unset MLAG heartbeat address
        ({**MLAG_EXPOSED, "detail": {}}, FeatureState.DISABLED),
        ({**MLAG_EXPOSED, "detail": {"dualPrimaryDetectionDelay": 5, "dualPrimaryAction": "none"}}, FeatureState.DISABLED),
    ],
)
def test_mlag_dual_primary_states(device: OfflineAntaDevice, output: dict[str, object], state: FeatureState) -> None:
    """Require all locally observable MLAG dual-primary prerequisites."""
    assert derive_state(device, MlagDualPrimaryErrdisableFact, output) is state


@pytest.mark.parametrize(
    ("output", "problem"),
    [
        ({**MLAG_EXPOSED, "domainId": True}, FactProblemKind.MALFORMED),
        ({**MLAG_EXPOSED, "detail": None}, FactProblemKind.MISSING),
        ({**MLAG_EXPOSED, "detail": {"dualPrimaryDetectionDelay": 5}}, FactProblemKind.MISSING),
        ({**MLAG_EXPOSED, "detail": {"dualPrimaryDetectionDelay": "5", "dualPrimaryAction": "errdisableAllInterfaces"}}, FactProblemKind.MALFORMED),
    ],
)
def test_mlag_dual_primary_rejects_partial_output(device: OfflineAntaDevice, output: dict[str, object], problem: FactProblemKind) -> None:
    """Do not treat malformed or partial MLAG output as safe configuration."""
    fact = MlagDualPrimaryErrdisableFact.derive(device, (command(MlagDualPrimaryErrdisableFact, output),))
    assert isinstance(fact, UnavailableFact)
    assert fact.problem is problem


@pytest.mark.parametrize(
    ("output", "state"),
    [
        (MLAG_EXPOSED, FeatureState.ENABLED),
        ({**MLAG_EXPOSED, "state": "active"}, FeatureState.ENABLED),
        ({}, FeatureState.DISABLED),
        ({key: value for key, value in MLAG_EXPOSED.items() if key != "domainId"}, FeatureState.DISABLED),
        ({key: value for key, value in MLAG_EXPOSED.items() if key != "localInterface"}, FeatureState.DISABLED),
        ({key: value for key, value in MLAG_EXPOSED.items() if key != "peerAddress"}, FeatureState.DISABLED),
        ({key: value for key, value in MLAG_EXPOSED.items() if key != "peerLink"}, FeatureState.DISABLED),
        ({**MLAG_EXPOSED, "domainId": ""}, FeatureState.DISABLED),
        ({**MLAG_EXPOSED, "localInterface": ""}, FeatureState.DISABLED),
        ({**MLAG_EXPOSED, "peerAddress": ""}, FeatureState.DISABLED),
        ({**MLAG_EXPOSED, "peerLink": ""}, FeatureState.DISABLED),
    ],
)
def test_mlag_configured_states(device: OfflineAntaDevice, output: dict[str, object], state: FeatureState) -> None:
    """Require all persistent MLAG configuration fields and ignore operational state."""
    assert derive_state(device, MlagConfiguredFact, output) is state


@pytest.mark.parametrize(
    "output",
    [
        {**MLAG_EXPOSED, "domainId": True},
        {**MLAG_EXPOSED, "localInterface": []},
        {**MLAG_EXPOSED, "peerAddress": True},
        {**MLAG_EXPOSED, "peerLink": []},
    ],
)
def test_mlag_configured_rejects_invalid_output(device: OfflineAntaDevice, output: dict[str, object]) -> None:
    """Reject malformed MLAG configuration fields."""
    fact = MlagConfiguredFact.derive(device, (command(MlagConfiguredFact, output),))
    assert isinstance(fact, UnavailableFact)
    assert fact.problem is FactProblemKind.MALFORMED


def test_mlag_configured_unsupported(device: OfflineAntaDevice) -> None:
    """Represent unsupported MLAG configuration distinctly from an absent domain."""
    populated = command(MlagConfiguredFact, {})
    populated.output = None
    populated.errors = ["This command is not supported on this hardware platform"]
    fact = MlagConfiguredFact.derive(device, (populated,))
    assert isinstance(fact, AvailableFact)
    assert fact.value.state is FeatureState.UNSUPPORTED
