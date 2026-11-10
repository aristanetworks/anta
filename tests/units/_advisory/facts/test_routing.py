# Copyright (c) 2026 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Unit tests for facts normalized from EOS routing output."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import pytest

from anta._advisory.facts.bfd import BfdAuthenticationFact
from anta._advisory.facts.models import AvailableFact, ConfigurationState, FactProblemKind, FeatureState, MitigationState, UnavailableFact
from anta._advisory.facts.routing import (
    IsisConfiguredFact,
    IsisGracefulRestartFact,
    IsisNonPassiveBroadcastInterfaceFact,
    LegacyOspfv3ConfiguredFact,
    LooseUrpfFact,
    Ospfv2BroadcastAuthenticationFact,
    Ospfv2ProcessConfiguredFact,
    Ospfv2SegmentRoutingFact,
    Ospfv3ConfiguredFact,
    Ospfv3IpsecAuthenticationFact,
    PimSparseModeFact,
    RipDhcpManagementInterfaceFact,
    RipDhcpMd5InterfaceFact,
    RipEnabledFact,
    RipManagementInterfaceFact,
    RipMd5AuthenticationFact,
)
from tests.units.anta_tests.advisories import OfflineAntaDevice

if TYPE_CHECKING:
    from collections.abc import Callable

    from anta.models import AntaCommand


@pytest.fixture(name="device")
def fact_device_fixture() -> OfflineAntaDevice:
    """Return an offline device suitable for fact derivation."""
    return OfflineAntaDevice("unit-test")


def ipsec_command(config: str) -> AntaCommand:
    """Return one populated OSPFv3 configuration command."""
    command = Ospfv3IpsecAuthenticationFact.commands[0].model_copy()
    command.output = config
    return command


def text_command(definition: type, output: str, index: int = 0) -> AntaCommand:
    """Return a populated text command declared by a fact definition."""
    command = definition.commands[index].model_copy()
    command.output = output
    return command


def json_command(definition: type, output: dict[str, Any], index: int = 0) -> AntaCommand:
    """Return a populated structured command declared by a fact definition."""
    command = definition.commands[index].model_copy()
    command.output = output
    return command


@pytest.mark.parametrize(
    ("definition", "output", "state"),
    [
        (Ospfv3ConfiguredFact, {"vrfs": {}}, FeatureState.DISABLED),
        (Ospfv3ConfiguredFact, {"vrfs": {"default": {}}}, FeatureState.DISABLED),
        (Ospfv3ConfiguredFact, {"vrfs": {"default": {"addressFamily": {}}}}, FeatureState.ENABLED),
        (Ospfv3ConfiguredFact, {"vrfs": {"TOTO": {"addressFamily": {"ipv6": {}}}}}, FeatureState.ENABLED),
        (LegacyOspfv3ConfiguredFact, {"vrfs": {}}, FeatureState.DISABLED),
        (LegacyOspfv3ConfiguredFact, {"vrfs": {"default": {}}}, FeatureState.DISABLED),
        (LegacyOspfv3ConfiguredFact, {"vrfs": {"default": {"instList": {}}}}, FeatureState.DISABLED),
        (LegacyOspfv3ConfiguredFact, {"vrfs": {"TOTO": {"instList": {"0": {}}}}}, FeatureState.ENABLED),
    ],
)
def test_ospfv3_configured_states(device: OfflineAntaDevice, definition: type, output: dict[str, Any], state: FeatureState) -> None:
    """Normalize current and legacy OSPFv3 process observations."""
    fact = definition.derive(device, (json_command(definition, output),))
    assert isinstance(fact, AvailableFact)
    assert fact.value.state is state


def test_ospfv3_configured_facts_collect_all_vrfs() -> None:
    """Collect current and legacy OSPFv3 presence from every configured VRF."""
    assert Ospfv3ConfiguredFact.commands[0].command == "show ospfv3 vrf all"
    assert LegacyOspfv3ConfiguredFact.commands[0].command == "show ipv6 ospf vrf all"
    assert Ospfv3ConfiguredFact.commands[0].revision == LegacyOspfv3ConfiguredFact.commands[0].revision == 1


@pytest.mark.parametrize("definition", [Ospfv3ConfiguredFact, LegacyOspfv3ConfiguredFact])
@pytest.mark.parametrize(("output", "problem"), [({}, FactProblemKind.MISSING), ({"vrfs": []}, FactProblemKind.MALFORMED)])
def test_ospfv3_configured_facts_reject_invalid_json(
    device: OfflineAntaDevice,
    definition: type,
    output: dict[str, Any],
    problem: FactProblemKind,
) -> None:
    """Reject missing or malformed structured all-VRF output."""
    fact = definition.derive(device, (json_command(definition, output),))

    assert isinstance(fact, UnavailableFact)
    assert fact.problem is problem


@pytest.mark.parametrize(
    ("definition", "output"),
    [
        (Ospfv3ConfiguredFact, {"vrfs": {"default": {"addressFamily": []}}}),
        (LegacyOspfv3ConfiguredFact, {"vrfs": {"default": {"instList": []}}}),
    ],
)
def test_ospfv3_configured_facts_reject_malformed_process_containers(device: OfflineAntaDevice, definition: type, output: dict[str, Any]) -> None:
    """Reject malformed process-bearing containers in structured all-VRF output."""
    fact = definition.derive(device, (json_command(definition, output),))

    assert isinstance(fact, UnavailableFact)
    assert fact.problem is FactProblemKind.MALFORMED


OSPFV2_INTERFACE = """Ethernet1 is up
  Interface Address 192.0.2.3/24, instance 1, VRF default, Area 0.0.0.0
  Network Type Broadcast, Cost: 10
  Neighbor Count is 0
  Message-digest authentication, using key id 1"""
OSPFV2_AREA_AUTHENTICATION = """OSPF instance 1 with ID 10.0.0.1 VRF default
  Area 0.0.0.0
    Area has MD5 authentication"""
OSPFV2_AREA_NO_AUTHENTICATION = """OSPF instance 1 with ID 10.0.0.1 VRF default
  Area 0.0.0.0
    Area has no authentication"""


@pytest.mark.parametrize(
    ("interface", "summary", "state"),
    [
        ("", "", FeatureState.DISABLED),
        (OSPFV2_INTERFACE, "", FeatureState.ENABLED),
        (
            OSPFV2_INTERFACE.replace("Message-digest authentication", "Message-digest sha256 authentication"),
            "",
            FeatureState.ENABLED,
        ),
        (
            OSPFV2_INTERFACE.replace("Message-digest authentication, using key id 1", "Simple authentication"),
            OSPFV2_AREA_AUTHENTICATION,
            FeatureState.ENABLED,
        ),
        (OSPFV2_INTERFACE.replace("Broadcast", "Point-To-Point"), "", FeatureState.DISABLED),
        (OSPFV2_INTERFACE.replace("Broadcast", "NBMA"), "", FeatureState.DISABLED),
        (
            OSPFV2_INTERFACE.replace("Message-digest authentication, using key id 1", "Simple authentication"),
            OSPFV2_AREA_NO_AUTHENTICATION,
            FeatureState.DISABLED,
        ),
    ],
)
def test_ospfv2_broadcast_authentication_states(
    device: OfflineAntaDevice,
    interface: str,
    summary: str,
    state: FeatureState,
) -> None:
    """Treat an authenticated active broadcast interface with zero neighbors as exposed."""
    command_tuple = (
        text_command(Ospfv2BroadcastAuthenticationFact, interface),
        text_command(Ospfv2BroadcastAuthenticationFact, summary, 1),
    )
    fact = Ospfv2BroadcastAuthenticationFact.derive(device, command_tuple)
    assert isinstance(fact, AvailableFact)
    assert fact.value.state is state


def test_ospfv2_broadcast_authentication_requires_candidate_area_output(device: OfflineAntaDevice) -> None:
    """Reject summary output that omits the active candidate interface's area."""
    command_tuple = (
        text_command(
            Ospfv2BroadcastAuthenticationFact,
            OSPFV2_INTERFACE.replace("Message-digest authentication, using key id 1", "Simple authentication"),
        ),
        text_command(Ospfv2BroadcastAuthenticationFact, "OSPF instance 1 with ID 10.0.0.1 VRF default", 1),
    )
    fact = Ospfv2BroadcastAuthenticationFact.derive(device, command_tuple)
    assert isinstance(fact, UnavailableFact)
    assert fact.problem is FactProblemKind.MISSING
    assert fact.source.name == "show ip ospf vrf all"


def test_ospfv2_broadcast_authentication_requires_network_type(device: OfflineAntaDevice) -> None:
    """Reject active interface output that does not identify whether the interface is broadcast."""
    command_tuple = (
        text_command(Ospfv2BroadcastAuthenticationFact, OSPFV2_INTERFACE.replace("  Network Type Broadcast, Cost: 10\n", "")),
        text_command(Ospfv2BroadcastAuthenticationFact, "", 1),
    )

    fact = Ospfv2BroadcastAuthenticationFact.derive(device, command_tuple)

    assert isinstance(fact, UnavailableFact)
    assert fact.problem is FactProblemKind.MALFORMED
    assert fact.source.name == "show ip ospf interface vrf all"


@pytest.mark.parametrize(
    ("output", "state"),
    [("", ConfigurationState.NOT_CONFIGURED), ("router ospf 1\n   max-lsa 12000", ConfigurationState.CONFIGURED)],
)
def test_ospfv2_process_configuration_states(device: OfflineAntaDevice, output: str, state: ConfigurationState) -> None:
    """Detect only the presence of an OSPFv2 routing process."""
    fact = Ospfv2ProcessConfiguredFact.derive(device, (text_command(Ospfv2ProcessConfiguredFact, output),))

    assert Ospfv2ProcessConfiguredFact.commands[0].command == r"show running-config section ^router\sospf\s"
    assert isinstance(fact, AvailableFact)
    assert fact.value.state is state


OSPFV2_SR_DISABLED = {"vrfs": {"default": {"instList": {}}}}
OSPFV2_SR_NO_VRFS = {"vrfs": {}}
OSPFV2_SR_SHUTDOWN = {
    "vrfs": {"default": {"instList": {}}},
    "warnings": ["OSPF (Instance Id: 1) Segment Routing has been administratively shutdown"],
}
OSPFV2_SR_ENABLED = {"vrfs": {"default": {"instList": {"1": {}}}}}


@pytest.mark.parametrize(
    ("output", "state"),
    [
        (OSPFV2_SR_DISABLED, FeatureState.DISABLED),
        (OSPFV2_SR_SHUTDOWN, FeatureState.DISABLED),
        (OSPFV2_SR_NO_VRFS, FeatureState.DISABLED),
        (OSPFV2_SR_ENABLED, FeatureState.ENABLED),
    ],
)
def test_ospfv2_segment_routing_states(device: OfflineAntaDevice, output: dict[str, Any], state: FeatureState) -> None:
    """Normalize OSPFv2 segment-routing instance presence, including empty and shutdown output."""
    fact = Ospfv2SegmentRoutingFact.derive(device, (json_command(Ospfv2SegmentRoutingFact, output),))
    assert isinstance(fact, AvailableFact)
    assert fact.value.state is state


@pytest.mark.parametrize(
    ("output", "problem"),
    [
        ({}, FactProblemKind.MISSING),
        ({"vrfs": []}, FactProblemKind.MALFORMED),
        ({"vrfs": {"default": {}}}, FactProblemKind.MISSING),
        ({"vrfs": {"default": {"instList": []}}}, FactProblemKind.MALFORMED),
    ],
)
def test_ospfv2_segment_routing_rejects_invalid_output(device: OfflineAntaDevice, output: dict[str, Any], problem: FactProblemKind) -> None:
    """Reject missing and malformed OSPFv2 segment-routing structures."""
    fact = Ospfv2SegmentRoutingFact.derive(device, (json_command(Ospfv2SegmentRoutingFact, output),))
    assert isinstance(fact, UnavailableFact)
    assert fact.problem is problem


EMPTY_ISIS = {"vrfs": {"default": {"isisInstances": {}}}}
ISIS_GRACEFUL_RESTART_NON_DEFAULT = {
    "vrfs": {
        "default": {"isisInstances": {"1": {"gracefulRestart": "disabled"}}},
        "TOTO": {"isisInstances": {"BLAH2": {"gracefulRestart": "enabled"}}},
    }
}
ISIS_CONFIGURED_NON_DEFAULT = {
    "vrfs": {
        "default": {"isisInstances": {}},
        "TOTO": {"isisInstances": {"BLAH2": {"enabled": True}}},
    }
}
ISIS_INTERFACE_OMITTED = {"vrfs": {"default": {"isisInstances": {"1": {"interfaces": {}}}}}}


def isis_interface_output(*, interface_type: str = "broadcast", enabled: bool = True, passive: bool = False, vrf: str = "default") -> dict[str, Any]:
    """Return the relevant portion of modeled IS-IS interface output."""
    return {
        "vrfs": {
            vrf: {
                "isisInstances": {
                    "1": {
                        "interfaces": {
                            "Ethernet1": {
                                "enabled": enabled,
                                "mtu": 1497,
                                "interfaceType": interface_type,
                                "intfLevels": {"1": {"numAdjacencies": 0, "passive": passive}},
                            }
                        }
                    }
                }
            }
        }
    }


@pytest.mark.parametrize(
    ("output", "state"),
    [
        (EMPTY_ISIS, FeatureState.DISABLED),
        (ISIS_INTERFACE_OMITTED, FeatureState.DISABLED),
        (isis_interface_output(), FeatureState.ENABLED),
        (isis_interface_output(vrf="TOTO"), FeatureState.ENABLED),
        (isis_interface_output(passive=True), FeatureState.DISABLED),
        (isis_interface_output(enabled=False), FeatureState.DISABLED),
        (isis_interface_output(interface_type="point-to-point"), FeatureState.DISABLED),
    ],
)
def test_isis_non_passive_broadcast_interface_states(device: OfflineAntaDevice, output: dict[str, Any], state: FeatureState) -> None:
    """Normalize modeled interface type and passive state without relying on current neighbors."""
    fact = IsisNonPassiveBroadcastInterfaceFact.derive(device, (json_command(IsisNonPassiveBroadcastInterfaceFact, output),))
    assert isinstance(fact, AvailableFact)
    assert fact.value.state is state


@pytest.mark.parametrize(
    ("definition", "output", "state"),
    [
        (IsisConfiguredFact, EMPTY_ISIS, FeatureState.DISABLED),
        (IsisConfiguredFact, {"vrfs": {"default": {"isisInstances": {"1": {"enabled": True}}}}}, FeatureState.ENABLED),
        (IsisConfiguredFact, ISIS_CONFIGURED_NON_DEFAULT, FeatureState.ENABLED),
        (IsisGracefulRestartFact, EMPTY_ISIS, FeatureState.DISABLED),
        (IsisGracefulRestartFact, {"vrfs": {"default": {"isisInstances": {"1": {"gracefulRestart": "enabled"}}}}}, FeatureState.ENABLED),
        (IsisGracefulRestartFact, {"vrfs": {"default": {"isisInstances": {"1": {"gracefulRestart": "disabled"}}}}}, FeatureState.DISABLED),
        (IsisGracefulRestartFact, ISIS_GRACEFUL_RESTART_NON_DEFAULT, FeatureState.ENABLED),
    ],
)
def test_isis_summary_states(device: OfflineAntaDevice, definition: type, output: dict[str, Any], state: FeatureState) -> None:
    """Normalize IS-IS instance and graceful-restart state."""
    fact = definition.derive(device, (json_command(definition, output),))
    assert isinstance(fact, AvailableFact)
    assert fact.value.state is state


@pytest.mark.parametrize(
    ("definition", "expected_command"),
    [
        (IsisNonPassiveBroadcastInterfaceFact, "show isis interface detail vrf all"),
        (IsisConfiguredFact, "show isis summary vrf all"),
        (IsisGracefulRestartFact, "show isis graceful-restart vrf all"),
    ],
)
def test_isis_facts_collect_all_vrfs(definition: type, expected_command: str) -> None:
    """Collect IS-IS instance and graceful-restart state from every configured VRF."""
    (command,) = definition.commands
    assert command.command == expected_command
    assert command.revision == 1


@pytest.mark.parametrize(
    ("definition", "output", "problem"),
    [
        (IsisNonPassiveBroadcastInterfaceFact, {}, FactProblemKind.MISSING),
        (IsisNonPassiveBroadcastInterfaceFact, {"vrfs": []}, FactProblemKind.MALFORMED),
        (
            IsisNonPassiveBroadcastInterfaceFact,
            {"vrfs": {"default": {"isisInstances": {"1": {"interfaces": {"Ethernet1": {"enabled": True, "intfLevels": {}}}}}}}},
            FactProblemKind.MISSING,
        ),
        (
            IsisNonPassiveBroadcastInterfaceFact,
            {
                "vrfs": {
                    "default": {
                        "isisInstances": {
                            "1": {
                                "interfaces": {
                                    "Ethernet1": {
                                        "enabled": True,
                                        "interfaceType": "broadcast",
                                        "intfLevels": {"1": {"passive": "false"}},
                                    }
                                }
                            }
                        }
                    }
                }
            },
            FactProblemKind.MALFORMED,
        ),
        (IsisConfiguredFact, {"vrfs": {"default": {"isisInstances": {"1": {}}}}}, FactProblemKind.MISSING),
        (IsisGracefulRestartFact, {"vrfs": {"default": {"isisInstances": {"1": {"gracefulRestart": "on"}}}}}, FactProblemKind.MALFORMED),
    ],
)
def test_isis_structured_output_problems(
    device: OfflineAntaDevice,
    definition: type,
    output: dict[str, Any],
    problem: FactProblemKind,
) -> None:
    """Reject missing and malformed fields required by each structured IS-IS fact."""
    fact = definition.derive(device, (json_command(definition, output),))

    assert isinstance(fact, UnavailableFact)
    assert fact.problem is problem


@pytest.mark.parametrize(
    "config",
    [
        ("interface Ethernet1\n   ospfv3 ipv6 area 0.0.0.0\nrouter ospfv3\n   area 0.0.0.0 authentication ipsec spi 34 md5 passphrase 7 REDACTED"),
        ("interface Ethernet1\n   ospfv3 authentication ipsec spi 35 md5 passphrase 7 REDACTED\n   ospfv3 ipv6 area 0.0.0.0\nrouter ospfv3"),
        ("interface Ethernet1\n   ospfv3 encryption ipsec spi 35 esp aes-256-cbc sha1 passphrase 7 REDACTED\n   ospfv3 ipv6 area 0.0.0.0\nrouter ospfv3"),
        (
            "interface Ethernet1\n   ospfv3 ipv6 area 0.0.0.0\nrouter ospfv3\n   address-family ipv6\n"
            "      area 0.0.0.0 encryption ipsec spi 34 esp aes-256-cbc sha1 passphrase 7 REDACTED"
        ),
        ("interface Ethernet1\n   vrf tenant\n   ospfv3 ipv6 area 0.0.0.0\nrouter ospfv3 vrf tenant\n   area 0.0.0.0 authentication ipsec spi 34 sha1 7 REDACTED"),
    ],
)
def test_ospfv3_authentication_complete_coverage(device: OfflineAntaDevice, config: str) -> None:
    """Accept complete interface and address-family-specific area authentication."""
    fact = Ospfv3IpsecAuthenticationFact.derive(device, (ipsec_command(config),))

    assert isinstance(fact, AvailableFact)
    assert fact.value.state is MitigationState.EFFECTIVE
    assert fact.source.name == Ospfv3IpsecAuthenticationFact.commands[0].command


def test_ospfv3_authentication_requires_every_configured_scope(device: OfflineAntaDevice) -> None:
    """Reject mitigation coverage when any configured OSPFv3 scope is unprotected."""
    config = (
        "interface Ethernet1\n   ospfv3 authentication ipsec spi 35 md5 7 REDACTED\n   ospfv3 ipv6 area 0.0.0.0\ninterface Ethernet2\n   ospfv3 ipv6 area 0.0.0.1"
    )

    fact = Ospfv3IpsecAuthenticationFact.derive(device, (ipsec_command(config),))

    assert isinstance(fact, AvailableFact)
    assert fact.value.state is MitigationState.INEFFECTIVE
    assert fact.source.name == Ospfv3IpsecAuthenticationFact.commands[0].command


def test_ospfv3_area_authentication_does_not_cross_address_families(device: OfflineAntaDevice) -> None:
    """Do not apply IPv6 area authentication to an IPv4 scope with the same area ID."""
    config = (
        "interface Ethernet1\n   ospfv3 ipv4 area 0.0.0.0\nrouter ospfv3\n"
        "   address-family ipv6\n      area 0.0.0.0 authentication ipsec spi 34 md5 passphrase 7 REDACTED"
    )
    fact = Ospfv3IpsecAuthenticationFact.derive(device, (ipsec_command(config),))

    assert isinstance(fact, AvailableFact)
    assert fact.value.state is MitigationState.INEFFECTIVE


@pytest.mark.parametrize("config", ["", "router ospfv3\n   router-id 1.1.1.1", "interface Ethernet1\n   ospfv3 ipv6 area 0.0.0.0"])
def test_ospfv3_authentication_absent_is_ineffective(device: OfflineAntaDevice, config: str) -> None:
    """Normalize valid configuration without IPsec authentication as ineffective."""
    fact = Ospfv3IpsecAuthenticationFact.derive(device, (ipsec_command(config),))

    assert isinstance(fact, AvailableFact)
    assert fact.value.state is MitigationState.INEFFECTIVE


def test_ospfv3_authentication_malformed_config_is_unavailable(device: OfflineAntaDevice) -> None:
    """Reject unexpected output from the narrow OSPFv3 configuration command."""
    fact = Ospfv3IpsecAuthenticationFact.derive(device, (ipsec_command("router ospfv3 vrf"),))

    assert isinstance(fact, UnavailableFact)
    assert fact.problem is FactProblemKind.MALFORMED
    assert fact.source.name == Ospfv3IpsecAuthenticationFact.commands[0].command


def test_ospfv3_authentication_unsupported_config_is_unavailable(device: OfflineAntaDevice) -> None:
    """Do not infer mitigation coverage when the configuration command is unsupported."""
    command = ipsec_command("")
    command.output = None
    command.errors = ["This command is not supported on this hardware platform"]

    fact = Ospfv3IpsecAuthenticationFact.derive(device, (command,))

    assert isinstance(fact, UnavailableFact)
    assert fact.problem is FactProblemKind.UNSUPPORTED
    assert fact.source.name == Ospfv3IpsecAuthenticationFact.commands[0].command


@pytest.mark.parametrize(
    "config",
    ["pim ipv4 sparse-mode", "pim ipv6 sparse-mode", "ip pim sparse-mode", "ipv6 pim sparse-mode"],
)
def test_pim_sparse_mode_canonical_and_legacy_syntax(device: OfflineAntaDevice, config: str) -> None:
    """Recognize every observed PIM sparse-mode interface syntax."""
    pim_command = PimSparseModeFact.commands[0].model_copy()
    pim_command.output = config

    fact = PimSparseModeFact.derive(device, (pim_command,))

    assert isinstance(fact, AvailableFact)
    assert fact.value.state is FeatureState.ENABLED


def test_pim_sparse_mode_empty_output_is_disabled(device: OfflineAntaDevice) -> None:
    """Treat a successful empty narrow command as no sparse-mode interface."""
    pim_command = PimSparseModeFact.commands[0].model_copy()
    pim_command.output = ""

    fact = PimSparseModeFact.derive(device, (pim_command,))

    assert isinstance(fact, AvailableFact)
    assert fact.value.state is FeatureState.DISABLED


def test_pim_sparse_mode_unexpected_output_is_unavailable(device: OfflineAntaDevice) -> None:
    """Reject output not described by the narrow command grammar."""
    pim_command = PimSparseModeFact.commands[0].model_copy()
    pim_command.output = "pim ipv4 sparse-mode extra"

    fact = PimSparseModeFact.derive(device, (pim_command,))

    assert isinstance(fact, UnavailableFact)
    assert fact.problem is FactProblemKind.MALFORMED


def test_pim_sparse_mode_unsupported_is_unavailable(device: OfflineAntaDevice) -> None:
    """Do not infer PIM absence from an unsupported shared configuration command."""
    pim_command = PimSparseModeFact.commands[0].model_copy()
    pim_command.output = None
    pim_command.errors = ["This command is not supported on this hardware platform"]

    fact = PimSparseModeFact.derive(device, (pim_command,))

    assert isinstance(fact, UnavailableFact)
    assert fact.problem is FactProblemKind.UNSUPPORTED


@pytest.mark.parametrize(
    "config",
    ["ip verify unicast source reachable-via any", "ipv6 verify unicast source reachable-via any allow-default"],
)
def test_loose_urpf_enabled(device: OfflineAntaDevice, config: str) -> None:
    """Recognize loose IPv4 and IPv6 uRPF syntax."""
    urpf_command = LooseUrpfFact.commands[0].model_copy()
    urpf_command.output = config

    fact = LooseUrpfFact.derive(device, (urpf_command,))

    assert isinstance(fact, AvailableFact)
    assert fact.value.state is FeatureState.ENABLED


def test_loose_urpf_empty_output_is_disabled(device: OfflineAntaDevice) -> None:
    """Treat a successful empty narrow output as no loose-uRPF interface."""
    urpf_command = LooseUrpfFact.commands[0].model_copy()
    urpf_command.output = ""

    fact = LooseUrpfFact.derive(device, (urpf_command,))

    assert isinstance(fact, AvailableFact)
    assert fact.value.state is FeatureState.DISABLED


def test_loose_urpf_malformed_output_is_unavailable(device: OfflineAntaDevice) -> None:
    """Reject output outside the narrow loose-uRPF grammar."""
    urpf_command = LooseUrpfFact.commands[0].model_copy()
    urpf_command.output = "ip verify unicast source reachable-via rx"

    fact = LooseUrpfFact.derive(device, (urpf_command,))

    assert isinstance(fact, UnavailableFact)
    assert fact.problem is FactProblemKind.MALFORMED


def bfd_commands(*, admin_down: object = False, global_config: str = "", interface_config: str = "") -> tuple[AntaCommand, ...]:
    """Return populated BFD summary and authentication-configuration commands."""
    summary = BfdAuthenticationFact.commands[0].model_copy()
    summary.output = {"adminDown": admin_down}
    global_authentication = BfdAuthenticationFact.commands[1].model_copy()
    global_authentication.output = global_config
    interface_authentication = BfdAuthenticationFact.commands[2].model_copy()
    interface_authentication.output = interface_config
    return summary, global_authentication, interface_authentication


@pytest.mark.parametrize(
    ("commands", "state"),
    [
        (bfd_commands(), FeatureState.DISABLED),
        (bfd_commands(admin_down=True, global_config="router bfd\n   authentication mode md5 shared-secret profile test"), FeatureState.DISABLED),
        (bfd_commands(global_config="router bfd\n   authentication mode md5 shared-secret profile test"), FeatureState.ENABLED),
        (
            bfd_commands(global_config="router bfd\n   peer 192.0.2.2\n      authentication mode sha1 shared-secret profile test"),
            FeatureState.ENABLED,
        ),
        (bfd_commands(interface_config="interface Ethernet1\n   bfd authentication mode simple shared-secret profile test"), FeatureState.ENABLED),
        (bfd_commands(interface_config="interface Ethernet1\n   bfd authentication mode disabled"), FeatureState.DISABLED),
    ],
)
def test_bfd_authentication_states(device: OfflineAntaDevice, commands: tuple[AntaCommand, ...], state: FeatureState) -> None:
    """Combine BFD administrative state with authentication configuration without requiring peers."""
    fact = BfdAuthenticationFact.derive(device, commands)

    assert isinstance(fact, AvailableFact)
    assert isinstance(fact.value, BfdAuthenticationFact)
    assert fact.value.state is state


@pytest.mark.parametrize(
    ("commands", "problem"),
    [
        (bfd_commands(admin_down=None, global_config="router bfd\n   authentication mode md5 shared-secret profile test"), FactProblemKind.MISSING),
        (bfd_commands(admin_down="false", global_config="router bfd\n   authentication mode md5 shared-secret profile test"), FactProblemKind.MALFORMED),
        (bfd_commands(global_config="not router bfd"), FactProblemKind.MALFORMED),
        (bfd_commands(interface_config="authentication mode md5 shared-secret profile test"), FactProblemKind.MALFORMED),
    ],
)
def test_bfd_authentication_invalid_output(
    device: OfflineAntaDevice,
    commands: tuple[AntaCommand, ...],
    problem: FactProblemKind,
) -> None:
    """Reject missing and malformed BFD administrative or authentication state."""
    fact = BfdAuthenticationFact.derive(device, commands)

    assert isinstance(fact, UnavailableFact)
    assert fact.problem is problem


def test_bfd_authentication_unsupported(device: OfflineAntaDevice) -> None:
    """Treat a feature-specific unsupported response as BFD absence."""
    summary, global_config, interface_config = bfd_commands()
    summary.output = None
    summary.errors = ["This command is not supported on this hardware platform"]

    fact = BfdAuthenticationFact.derive(device, (summary, global_config, interface_config))

    assert isinstance(fact, AvailableFact)
    assert fact.value.state is FeatureState.UNSUPPORTED


@pytest.mark.parametrize("index", [1, 2])
def test_bfd_authentication_requires_configuration_commands(device: OfflineAntaDevice, index: int) -> None:
    """Attribute an unsupported authentication-configuration query to that specific command."""
    commands = list(bfd_commands())
    commands[index].output = None
    commands[index].errors = ["This command is not supported on this hardware platform"]

    fact = BfdAuthenticationFact.derive(device, tuple(commands))

    assert isinstance(fact, UnavailableFact)
    assert fact.problem is FactProblemKind.UNSUPPORTED
    assert fact.source.name == BfdAuthenticationFact.commands[index].command


RIP_VRF_ENABLED = """router rip vrf SA_RIP_TEST
   metric default 1
   distance 120
   timers 30 180 120
   network 198.51.100.0/29
   no shutdown
   no ecmp
   no ip access-group
"""
RIP_DEFAULT_SHUTDOWN = """router rip
   network 192.0.2.0/24
   shutdown
"""
RIP_DEFAULT_ENABLED = """router rip
   metric default 1
   distance 120
   timers 30 180 120
   network 198.51.100.0/29
   no shutdown
   no ecmp
   no ip access-group
"""
RIP_MD5_TX = """interface Vlan3990
   rip authentication algorithm md5 tx key-id 10
   rip authentication algorithm md5 key-id 10 key 7 <removed>
"""
UNASSIGNED_IPV4 = "0.0.0.0"  # noqa: S104 - EOS reports an interface without an IPv4 address as 0.0.0.0/0


def ip_interface(
    vrf: str,
    primary: str,
    secondaries: tuple[str, ...] = (),
    *,
    dhcp: bool = False,
    mask_length: int = 29,
) -> dict[str, Any]:
    """Return one structured ``show ip interface`` entry with the shape observed on EOS 4.36.0F."""
    return {
        "interfaceStatus": "connected",
        "lineProtocolStatus": "up",
        "enabled": True,
        "interfaceAddress": {
            "primaryIp": {"address": primary, "maskLen": mask_length},
            "secondaryIps": {},
            "secondaryIpsOrderedList": [{"address": address, "maskLen": 28} for address in secondaries],
            "virtualIp": {"address": UNASSIGNED_IPV4, "maskLen": 0},
            "virtualSecondaryIps": {},
            "virtualSecondaryIpsOrderedList": [],
            "broadcastAddress": "255.255.255.255",
            "dhcp": dhcp,
        },
        "vrf": vrf,
    }


VLAN3990 = ip_interface("SA_RIP_TEST", "198.51.100.1")


def rip_md5_commands(
    rip_config: str = RIP_VRF_ENABLED,
    authentication_config: str = RIP_MD5_TX,
    interfaces: object = None,
) -> tuple[AntaCommand, ...]:
    """Return populated RIP, RIP-authentication, and IPv4 interface commands."""
    rip, authentication, ip_interfaces = (command.model_copy() for command in RipMd5AuthenticationFact.commands)
    rip.output = rip_config
    authentication.output = authentication_config
    ip_interfaces.output = {"interfaces": {"Vlan3990": VLAN3990} if interfaces is None else interfaces}
    return rip, authentication, ip_interfaces


def test_rip_facts_declare_configuration_commands() -> None:
    """Collect persistent RIP configuration, sanitized interface authentication, and structured IPv4 addressing."""
    assert [(command.command, command.ofmt) for command in RipEnabledFact.commands] == [(r"show running-config all section ^router\srip", "text")]
    assert [(command.command, command.ofmt, command.revision) for command in RipMd5AuthenticationFact.commands] == [
        (r"show running-config all section ^router\srip", "text", None),
        (r"show running-config sanitized section ^\s+rip\sauthentication", "text", None),
        ("show ip interface", "json", 2),
    ]


@pytest.mark.parametrize(
    ("config", "state"),
    [
        pytest.param("", FeatureState.DISABLED, id="not-configured"),
        pytest.param(RIP_DEFAULT_SHUTDOWN, FeatureState.DISABLED, id="shutdown"),
        pytest.param(RIP_VRF_ENABLED, FeatureState.ENABLED, id="vrf-enabled"),
        pytest.param(RIP_VRF_ENABLED + RIP_DEFAULT_SHUTDOWN, FeatureState.ENABLED, id="one-of-several-enabled"),
        pytest.param("router rip vrf default\n   no shutdown\n!\n", FeatureState.ENABLED, id="explicit-default-vrf"),
    ],
)
def test_rip_enabled_states(device: OfflineAntaDevice, config: str, state: FeatureState) -> None:
    """Normalize the explicitly rendered administrative state of every RIP instance."""
    fact = RipEnabledFact.derive(device, (text_command(RipEnabledFact, config),))

    assert isinstance(fact, AvailableFact)
    assert fact.value.state is state


@pytest.mark.parametrize(
    "config",
    [
        pytest.param("router rip\n   network 192.0.2.0/24\n", id="missing-shutdown-state"),
        pytest.param("router rip\n   shutdown\n   no shutdown\n", id="contradictory-shutdown-state"),
        pytest.param("router rip\n   shutdown\nrouter rip vrf default\n   shutdown\n", id="duplicate-vrf"),
        pytest.param("   no shutdown\n", id="child-without-instance"),
        pytest.param("interface Loopback0\n   description ROUTER_ID\n", id="unrelated-section"),
        pytest.param("router rip\n   network 192.0.2.300/24\n   no shutdown\n", id="invalid-network"),
        pytest.param("router rip\n   network 10.0.0.0 255.0.0.0\n   no shutdown\n", id="unexpected-network-syntax"),
    ],
)
def test_rip_enabled_rejects_malformed_configuration(device: OfflineAntaDevice, config: str) -> None:
    """Reject RIP configuration whose instances or networks cannot be established."""
    fact = RipEnabledFact.derive(device, (text_command(RipEnabledFact, config),))

    assert isinstance(fact, UnavailableFact)
    assert fact.problem is FactProblemKind.MALFORMED
    assert fact.source.name == RipEnabledFact.commands[0].command


@pytest.mark.parametrize(
    ("commands", "state"),
    [
        pytest.param(rip_md5_commands(), FeatureState.ENABLED, id="transmit-key-in-network"),
        pytest.param(
            rip_md5_commands(authentication_config="interface Vlan3990\n   rip authentication algorithm md5 key-id 10 key 7 <removed>\n"),
            FeatureState.ENABLED,
            id="key-without-transmit-key",
        ),
        pytest.param(
            rip_md5_commands(authentication_config="interface Vlan3990\n   rip authentication algorithm md5 tx key-id 10 rx-disabled\n"),
            FeatureState.ENABLED,
            id="receive-checks-disabled",
        ),
        pytest.param(
            rip_md5_commands(rip_config=RIP_VRF_ENABLED.replace("198.51.100.0/29", "198.51.100.0/31")),
            FeatureState.ENABLED,
            id="narrower-network-contains-address",
        ),
        pytest.param(
            rip_md5_commands(rip_config=RIP_VRF_ENABLED.replace("198.51.100.0/29", "198.51.100.4/30")),
            FeatureState.DISABLED,
            id="network-overlaps-subnet-but-not-address",
        ),
        pytest.param(
            rip_md5_commands(rip_config=RIP_VRF_ENABLED.replace("198.51.100.0/29", "203.0.113.0/28")),
            FeatureState.DISABLED,
            id="network-excludes-primary-address",
        ),
        pytest.param(
            rip_md5_commands(
                rip_config=RIP_VRF_ENABLED.replace("198.51.100.0/29", "203.0.113.0/28"),
                interfaces={"Vlan3990": ip_interface("SA_RIP_TEST", "198.51.100.1", ("203.0.113.1",))},
            ),
            FeatureState.ENABLED,
            id="network-contains-secondary-address",
        ),
        pytest.param(
            rip_md5_commands(rip_config=RIP_VRF_ENABLED.replace("SA_RIP_TEST", "OTHER") + RIP_DEFAULT_ENABLED),
            FeatureState.DISABLED,
            id="matching-networks-in-other-vrfs",
        ),
        pytest.param(
            rip_md5_commands(rip_config=RIP_DEFAULT_ENABLED, interfaces={"Vlan3990": ip_interface("default", "198.51.100.1")}),
            FeatureState.ENABLED,
            id="default-vrf",
        ),
        pytest.param(
            rip_md5_commands(interfaces={"Vlan3990": ip_interface("SA_RIP_TEST", "198.51.100.1", dhcp=True)}), FeatureState.ENABLED, id="dhcp-lease-in-network"
        ),
        pytest.param(
            rip_md5_commands(interfaces={"Vlan3990": ip_interface("SA_RIP_TEST", "203.0.113.1", dhcp=True)}), FeatureState.DISABLED, id="dhcp-lease-outside-network"
        ),
        pytest.param(
            rip_md5_commands(interfaces={"Vlan3990": ip_interface("SA_RIP_TEST", UNASSIGNED_IPV4, dhcp=True)}), FeatureState.DISABLED, id="dhcp-without-lease"
        ),
        pytest.param(rip_md5_commands(interfaces={"Vlan3990": ip_interface("SA_RIP_TEST", UNASSIGNED_IPV4)}), FeatureState.DISABLED, id="no-ipv4-address"),
        pytest.param(rip_md5_commands(interfaces={}), FeatureState.DISABLED, id="not-an-ipv4-interface"),
        pytest.param(rip_md5_commands(rip_config=RIP_VRF_ENABLED.replace("   no shutdown", "   shutdown")), FeatureState.DISABLED, id="instance-shutdown"),
        pytest.param(rip_md5_commands(rip_config="router rip vrf SA_RIP_TEST\n   no shutdown\n"), FeatureState.DISABLED, id="instance-without-network"),
    ],
)
def test_rip_md5_authentication_states(device: OfflineAntaDevice, commands: tuple[AntaCommand, ...], state: FeatureState) -> None:
    """Correlate RIP MD5 interfaces with enabled RIP networks in the interface VRF."""
    fact = RipMd5AuthenticationFact.derive(device, commands)

    assert isinstance(fact, AvailableFact)
    assert fact.value.state is state


def test_rip_md5_authentication_enabled_source_is_the_authentication_configuration(device: OfflineAntaDevice) -> None:
    """Attribute confirmed MD5 exposure to the interface authentication configuration."""
    fact = RipMd5AuthenticationFact.derive(device, rip_md5_commands())

    assert isinstance(fact, AvailableFact)
    assert fact.source.name == RipMd5AuthenticationFact.commands[1].command


@pytest.mark.parametrize(
    ("commands", "source_index"),
    [
        pytest.param(rip_md5_commands(rip_config="not router rip", authentication_config="", interfaces=[]), 1, id="no-md5-ignores-other-inputs"),
        pytest.param(
            rip_md5_commands(rip_config=RIP_DEFAULT_SHUTDOWN, authentication_config="not an interface", interfaces=[]), 0, id="no-enabled-rip-ignores-other-inputs"
        ),
    ],
)
def test_rip_md5_authentication_decisive_absence(device: OfflineAntaDevice, commands: tuple[AntaCommand, ...], source_index: int) -> None:
    """Return a disabled state from either independent absence without requiring unrelated inputs."""
    fact = RipMd5AuthenticationFact.derive(device, commands)

    assert isinstance(fact, AvailableFact)
    assert fact.value.state is FeatureState.DISABLED
    assert fact.source.name == RipMd5AuthenticationFact.commands[source_index].command


@pytest.mark.parametrize(
    ("commands", "problem", "source_index"),
    [
        pytest.param(rip_md5_commands(rip_config="router rip\n   network 192.0.2.0/24\n"), FactProblemKind.MALFORMED, 0, id="rip-missing-shutdown-state"),
        pytest.param(
            rip_md5_commands(authentication_config="interface Vlan3990\n   description rip authentication\n"), FactProblemKind.MALFORMED, 1, id="unexpected-child"
        ),
        pytest.param(
            rip_md5_commands(authentication_config="router rip\n   rip authentication algorithm md5 tx key-id 10\n"),
            FactProblemKind.MALFORMED,
            1,
            id="non-interface-parent",
        ),
        pytest.param(rip_md5_commands(authentication_config="interface Vlan3990\n"), FactProblemKind.MALFORMED, 1, id="interface-without-authentication"),
        pytest.param(rip_md5_commands(interfaces=[]), FactProblemKind.MALFORMED, 2, id="interfaces-not-mapping"),
        pytest.param(rip_md5_commands(interfaces={"Vlan3990": {"interfaceAddress": VLAN3990["interfaceAddress"]}}), FactProblemKind.MISSING, 2, id="missing-vrf"),
        pytest.param(
            rip_md5_commands(interfaces={"Vlan3990": {**VLAN3990, "interfaceAddress": {**VLAN3990["interfaceAddress"], "secondaryIpsOrderedList": None}}}),
            FactProblemKind.MISSING,
            2,
            id="missing-secondaries",
        ),
        pytest.param(
            rip_md5_commands(interfaces={"Vlan3990": {**VLAN3990, "interfaceAddress": {**VLAN3990["interfaceAddress"], "secondaryIpsOrderedList": {}}}}),
            FactProblemKind.MALFORMED,
            2,
            id="malformed-secondaries",
        ),
        pytest.param(rip_md5_commands(interfaces={"Vlan3990": ip_interface("SA_RIP_TEST", "198.51.100.300")}), FactProblemKind.MALFORMED, 2, id="invalid-address"),
        pytest.param(
            rip_md5_commands(interfaces={"Vlan3990": {**VLAN3990, "interfaceAddress": {**VLAN3990["interfaceAddress"], "primaryIp": {"maskLen": 29}}}}),
            FactProblemKind.MISSING,
            2,
            id="missing-primary-address",
        ),
    ],
)
def test_rip_md5_authentication_unavailable(
    device: OfflineAntaDevice,
    commands: tuple[AntaCommand, ...],
    problem: FactProblemKind,
    source_index: int,
) -> None:
    """Retain the exact failing command when RIP MD5 exposure cannot be established."""
    fact = RipMd5AuthenticationFact.derive(device, commands)

    assert isinstance(fact, UnavailableFact)
    assert fact.problem is problem
    assert fact.source.name == RipMd5AuthenticationFact.commands[source_index].command


def test_rip_md5_authentication_missing_interfaces_key(device: OfflineAntaDevice) -> None:
    """Treat structured output without the interface collection as incomplete."""
    rip, authentication, ip_interfaces = rip_md5_commands()
    ip_interfaces.output = {}

    fact = RipMd5AuthenticationFact.derive(device, (rip, authentication, ip_interfaces))

    assert isinstance(fact, UnavailableFact)
    assert fact.problem is FactProblemKind.MISSING
    assert fact.source.name == "show ip interface"


def test_rip_md5_authentication_exposed_interface_outweighs_unrelated_invalid_interface(device: OfflineAntaDevice) -> None:
    """Confirm exposure from one interface even when another MD5 interface has invalid addressing."""
    authentication_config = RIP_MD5_TX + "interface Ethernet1\n   rip authentication algorithm md5 tx key-id 1\n"
    invalid = {"Ethernet1": {"vrf": "SA_RIP_TEST"}, "Vlan3990": VLAN3990}

    exposed = RipMd5AuthenticationFact.derive(device, rip_md5_commands(authentication_config=authentication_config, interfaces=invalid))
    unresolved = RipMd5AuthenticationFact.derive(
        device,
        rip_md5_commands(authentication_config=authentication_config, interfaces={**invalid, "Vlan3990": ip_interface("SA_RIP_TEST", "203.0.113.1")}),
    )

    assert isinstance(exposed, AvailableFact)
    assert exposed.value.state is FeatureState.ENABLED
    assert isinstance(unresolved, UnavailableFact)
    assert unresolved.problem is FactProblemKind.MISSING


RIP_MGMT_ENABLED = """router rip vrf MGMT
   metric default 1
   distance 120
   timers 30 180 120
   network 192.0.2.0/24
   no shutdown
   no ecmp
   no ip access-group
"""
MANAGEMENT1 = ip_interface("MGMT", "192.0.2.122", mask_length=24)


def rip_management_commands(rip_config: str = RIP_MGMT_ENABLED, interfaces: object = None) -> tuple[AntaCommand, ...]:
    """Return populated RIP and IPv4 interface commands for management interface exposure."""
    rip, ip_interfaces = (command.model_copy() for command in RipManagementInterfaceFact.commands)
    rip.output = rip_config
    ip_interfaces.output = {"interfaces": {"Management1": MANAGEMENT1, "Vlan3990": VLAN3990} if interfaces is None else interfaces}
    return rip, ip_interfaces


def test_rip_management_interface_declares_commands() -> None:
    """Collect persistent RIP configuration and structured IPv4 addressing, including management VRFs."""
    assert [(command.command, command.ofmt, command.revision) for command in RipManagementInterfaceFact.commands] == [
        (r"show running-config all section ^router\srip", "text", None),
        ("show ip interface", "json", 2),
    ]


@pytest.mark.parametrize(
    ("commands", "state"),
    [
        pytest.param(rip_management_commands(), FeatureState.ENABLED, id="network-equals-management-subnet"),
        pytest.param(rip_management_commands(RIP_MGMT_ENABLED.replace("192.0.2.0/24", "192.0.0.0/16")), FeatureState.ENABLED, id="supernet"),
        pytest.param(
            rip_management_commands(RIP_MGMT_ENABLED.replace("192.0.2.0/24", "192.0.2.120/30")), FeatureState.ENABLED, id="narrower-prefix-contains-address"
        ),
        pytest.param(rip_management_commands(RIP_MGMT_ENABLED.replace("192.0.2.0/24", "192.0.2.122/32")), FeatureState.ENABLED, id="host-prefix"),
        pytest.param(rip_management_commands(RIP_MGMT_ENABLED.replace("192.0.2.0/24", "192.0.2.128/25")), FeatureState.DISABLED, id="overlap-excludes-address"),
        pytest.param(
            rip_management_commands(RIP_MGMT_ENABLED.replace("router rip vrf MGMT", "router rip")), FeatureState.DISABLED, id="matching-network-in-other-vrf"
        ),
        pytest.param(
            rip_management_commands(
                RIP_MGMT_ENABLED.replace("router rip vrf MGMT", "router rip"), interfaces={"Management1": ip_interface("default", "192.0.2.122", mask_length=24)}
            ),
            FeatureState.ENABLED,
            id="default-vrf-management",
        ),
        pytest.param(rip_management_commands(interfaces={"Management1/1": MANAGEMENT1}), FeatureState.ENABLED, id="modular-management-interface"),
        pytest.param(
            rip_management_commands(interfaces={"Management0": ip_interface("MGMT", "203.0.113.10", ("192.0.2.10",), mask_length=24)}),
            FeatureState.ENABLED,
            id="secondary-address",
        ),
        pytest.param(
            rip_management_commands(interfaces={"Management1": ip_interface("MGMT", "192.0.2.122", dhcp=True, mask_length=24)}),
            FeatureState.ENABLED,
            id="dhcp-lease",
        ),
        pytest.param(rip_management_commands(RIP_VRF_ENABLED), FeatureState.DISABLED, id="only-data-interface-selected"),
        pytest.param(
            rip_management_commands(interfaces={"Management1": ip_interface("MGMT", UNASSIGNED_IPV4, mask_length=0)}), FeatureState.DISABLED, id="no-ipv4-address"
        ),
        pytest.param(rip_management_commands(interfaces={"Vlan3990": VLAN3990}), FeatureState.DISABLED, id="no-management-interface"),
        pytest.param(
            rip_management_commands(interfaces={"Management1": MANAGEMENT1, "Ethernet1": {"vrf": "MGMT"}}),
            FeatureState.ENABLED,
            id="invalid-data-interface-ignored",
        ),
    ],
)
def test_rip_management_interface_states(device: OfflineAntaDevice, commands: tuple[AntaCommand, ...], state: FeatureState) -> None:
    """Correlate management interface addresses with enabled RIP networks in the interface VRF."""
    fact = RipManagementInterfaceFact.derive(device, commands)

    assert isinstance(fact, AvailableFact)
    assert fact.value.state is state
    assert fact.source.name == RipManagementInterfaceFact.commands[1].command


@pytest.mark.parametrize(
    "rip_config",
    [
        pytest.param("", id="not-configured"),
        pytest.param(RIP_DEFAULT_SHUTDOWN, id="other-instance-shutdown"),
        pytest.param(RIP_MGMT_ENABLED.replace("   no shutdown", "   shutdown"), id="matching-instance-shutdown"),
        pytest.param("router rip vrf MGMT\n   no shutdown\n", id="instance-without-network"),
    ],
)
def test_rip_management_interface_without_enabled_rip_ignores_interfaces(device: OfflineAntaDevice, rip_config: str) -> None:
    """Return a disabled state from the RIP configuration without requiring interface addressing."""
    fact = RipManagementInterfaceFact.derive(device, rip_management_commands(rip_config, interfaces=[]))

    assert isinstance(fact, AvailableFact)
    assert fact.value.state is FeatureState.DISABLED
    assert fact.source.name == RipManagementInterfaceFact.commands[0].command


@pytest.mark.parametrize(
    ("commands", "problem", "source_index"),
    [
        pytest.param(rip_management_commands("router rip vrf MGMT\n   network 192.0.2.0/24\n"), FactProblemKind.MALFORMED, 0, id="rip-missing-shutdown-state"),
        pytest.param(rip_management_commands(interfaces=[]), FactProblemKind.MALFORMED, 1, id="interfaces-not-mapping"),
        pytest.param(
            rip_management_commands(interfaces={"Management1": {"interfaceAddress": MANAGEMENT1["interfaceAddress"]}}), FactProblemKind.MISSING, 1, id="missing-vrf"
        ),
        pytest.param(
            rip_management_commands(interfaces={"Management1": ip_interface("MGMT", "192.0.2.300", mask_length=24)}),
            FactProblemKind.MALFORMED,
            1,
            id="invalid-address",
        ),
    ],
)
def test_rip_management_interface_unavailable(device: OfflineAntaDevice, commands: tuple[AntaCommand, ...], problem: FactProblemKind, source_index: int) -> None:
    """Retain the exact failing command when management interface exposure cannot be established."""
    fact = RipManagementInterfaceFact.derive(device, commands)

    assert isinstance(fact, UnavailableFact)
    assert fact.problem is problem
    assert fact.source.name == RipManagementInterfaceFact.commands[source_index].command


def test_rip_management_interface_missing_interfaces_key(device: OfflineAntaDevice) -> None:
    """Treat structured output without the interface collection as incomplete."""
    rip, ip_interfaces = rip_management_commands()
    ip_interfaces.output = {}

    fact = RipManagementInterfaceFact.derive(device, (rip, ip_interfaces))

    assert isinstance(fact, UnavailableFact)
    assert fact.problem is FactProblemKind.MISSING
    assert fact.source.name == "show ip interface"


def without_dhcp_key(interface: dict[str, Any]) -> dict[str, Any]:
    """Return one structured interface whose addressing omits the DHCP flag."""
    return {**interface, "interfaceAddress": {key: value for key, value in interface["interfaceAddress"].items() if key != "dhcp"}}


def dhcp_md5_commands(rip_config: str = RIP_VRF_ENABLED, authentication_config: str = RIP_MD5_TX, interfaces: object = None) -> tuple[AntaCommand, ...]:
    """Return populated commands for the DHCP MD5 interface fact."""
    rip, authentication, ip_interfaces = (command.model_copy() for command in RipDhcpMd5InterfaceFact.commands)
    rip.output = rip_config
    authentication.output = authentication_config
    ip_interfaces.output = {"interfaces": {"Vlan3990": VLAN3990} if interfaces is None else interfaces}
    return rip, authentication, ip_interfaces


def dhcp_management_commands(rip_config: str = RIP_MGMT_ENABLED, interfaces: object = None) -> tuple[AntaCommand, ...]:
    """Return populated commands for the DHCP management interface fact."""
    rip, ip_interfaces = (command.model_copy() for command in RipDhcpManagementInterfaceFact.commands)
    rip.output = rip_config
    ip_interfaces.output = {"interfaces": {"Management1": MANAGEMENT1, "Vlan3990": VLAN3990} if interfaces is None else interfaces}
    return rip, ip_interfaces


def test_rip_dhcp_facts_declare_commands() -> None:
    """Collect the same persistent RIP configuration, authentication, and structured addressing as the matching exposure facts."""
    assert RipDhcpMd5InterfaceFact.commands == RipMd5AuthenticationFact.commands
    assert RipDhcpManagementInterfaceFact.commands == RipManagementInterfaceFact.commands


@pytest.mark.parametrize(
    ("commands", "state"),
    [
        pytest.param(
            dhcp_md5_commands(interfaces={"Vlan3990": ip_interface("SA_RIP_TEST", UNASSIGNED_IPV4, dhcp=True)}),
            ConfigurationState.CONFIGURED,
            id="dhcp-without-lease",
        ),
        pytest.param(
            dhcp_md5_commands(interfaces={"Vlan3990": ip_interface("SA_RIP_TEST", "203.0.113.1", dhcp=True)}),
            ConfigurationState.CONFIGURED,
            id="dhcp-lease-outside-network",
        ),
        pytest.param(
            dhcp_md5_commands(interfaces={"Vlan3990": ip_interface("SA_RIP_TEST", "198.51.100.1", dhcp=True)}),
            ConfigurationState.CONFIGURED,
            id="dhcp-lease-in-network",
        ),
        pytest.param(dhcp_md5_commands(), ConfigurationState.NOT_CONFIGURED, id="static-address"),
        pytest.param(
            dhcp_md5_commands(rip_config=RIP_DEFAULT_ENABLED, interfaces={"Vlan3990": ip_interface("SA_RIP_TEST", UNASSIGNED_IPV4, dhcp=True)}),
            ConfigurationState.NOT_CONFIGURED,
            id="no-enabled-rip-in-interface-vrf",
        ),
        pytest.param(
            dhcp_md5_commands(interfaces={"Vlan3990": VLAN3990, "Ethernet1": ip_interface("SA_RIP_TEST", UNASSIGNED_IPV4, dhcp=True)}),
            ConfigurationState.NOT_CONFIGURED,
            id="dhcp-interface-without-md5",
        ),
        pytest.param(dhcp_md5_commands(interfaces={}), ConfigurationState.NOT_CONFIGURED, id="not-an-ipv4-interface"),
    ],
)
def test_rip_dhcp_md5_interface_states(device: OfflineAntaDevice, commands: tuple[AntaCommand, ...], state: ConfigurationState) -> None:
    """Report DHCP addressing of MD5 interfaces in an enabled RIP VRF regardless of the current lease."""
    fact = RipDhcpMd5InterfaceFact.derive(device, commands)

    assert isinstance(fact, AvailableFact)
    assert fact.value.state is state
    assert fact.source.name == RipDhcpMd5InterfaceFact.commands[2].command


@pytest.mark.parametrize(
    ("commands", "source_index"),
    [
        pytest.param(dhcp_md5_commands(rip_config="not router rip", authentication_config="", interfaces=[]), 1, id="no-md5-ignores-other-inputs"),
        pytest.param(
            dhcp_md5_commands(rip_config=RIP_DEFAULT_SHUTDOWN, authentication_config="not an interface", interfaces=[]), 0, id="no-enabled-rip-ignores-other-inputs"
        ),
    ],
)
def test_rip_dhcp_md5_interface_decisive_absence(device: OfflineAntaDevice, commands: tuple[AntaCommand, ...], source_index: int) -> None:
    """Return a not-configured state from either independent absence without requiring unrelated inputs."""
    fact = RipDhcpMd5InterfaceFact.derive(device, commands)

    assert isinstance(fact, AvailableFact)
    assert fact.value.state is ConfigurationState.NOT_CONFIGURED
    assert fact.source.name == RipDhcpMd5InterfaceFact.commands[source_index].command


@pytest.mark.parametrize(
    ("commands", "problem", "source_index"),
    [
        pytest.param(dhcp_md5_commands(rip_config="router rip\n   network 192.0.2.0/24\n"), FactProblemKind.MALFORMED, 0, id="rip-missing-shutdown-state"),
        pytest.param(dhcp_md5_commands(authentication_config="interface Vlan3990\n"), FactProblemKind.MALFORMED, 1, id="interface-without-authentication"),
        pytest.param(dhcp_md5_commands(interfaces=[]), FactProblemKind.MALFORMED, 2, id="interfaces-not-mapping"),
        pytest.param(dhcp_md5_commands(interfaces={"Vlan3990": without_dhcp_key(VLAN3990)}), FactProblemKind.MISSING, 2, id="missing-dhcp-flag"),
        pytest.param(
            dhcp_md5_commands(interfaces={"Vlan3990": {**VLAN3990, "interfaceAddress": {**VLAN3990["interfaceAddress"], "dhcp": "yes"}}}),
            FactProblemKind.MALFORMED,
            2,
            id="malformed-dhcp-flag",
        ),
        pytest.param(dhcp_md5_commands(interfaces={"Vlan3990": {"interfaceAddress": VLAN3990["interfaceAddress"]}}), FactProblemKind.MISSING, 2, id="missing-vrf"),
        pytest.param(dhcp_md5_commands(interfaces={"Vlan3990": {"vrf": "SA_RIP_TEST"}}), FactProblemKind.MISSING, 2, id="missing-addressing"),
        pytest.param(dhcp_md5_commands(interfaces={"Vlan3990": "Vlan3990"}), FactProblemKind.MALFORMED, 2, id="interface-not-mapping"),
    ],
)
def test_rip_dhcp_md5_interface_unavailable(
    device: OfflineAntaDevice,
    commands: tuple[AntaCommand, ...],
    problem: FactProblemKind,
    source_index: int,
) -> None:
    """Retain the exact failing command when DHCP addressing of MD5 interfaces cannot be established."""
    fact = RipDhcpMd5InterfaceFact.derive(device, commands)

    assert isinstance(fact, UnavailableFact)
    assert fact.problem is problem
    assert fact.source.name == RipDhcpMd5InterfaceFact.commands[source_index].command


def test_rip_dhcp_md5_interface_configured_outweighs_unrelated_invalid_interface(device: OfflineAntaDevice) -> None:
    """Confirm DHCP addressing from one MD5 interface even when another MD5 interface has incomplete addressing."""
    authentication_config = RIP_MD5_TX + "interface Ethernet1\n   rip authentication algorithm md5 tx key-id 1\n"
    interfaces = {"Ethernet1": {"vrf": "SA_RIP_TEST"}, "Vlan3990": ip_interface("SA_RIP_TEST", UNASSIGNED_IPV4, dhcp=True)}

    configured = RipDhcpMd5InterfaceFact.derive(device, dhcp_md5_commands(authentication_config=authentication_config, interfaces=interfaces))
    unresolved = RipDhcpMd5InterfaceFact.derive(
        device, dhcp_md5_commands(authentication_config=authentication_config, interfaces={**interfaces, "Vlan3990": VLAN3990})
    )

    assert isinstance(configured, AvailableFact)
    assert configured.value.state is ConfigurationState.CONFIGURED
    assert isinstance(unresolved, UnavailableFact)
    assert unresolved.problem is FactProblemKind.MISSING


@pytest.mark.parametrize(
    ("commands", "state"),
    [
        pytest.param(
            dhcp_management_commands(interfaces={"Management1": ip_interface("MGMT", UNASSIGNED_IPV4, dhcp=True, mask_length=0)}),
            ConfigurationState.CONFIGURED,
            id="dhcp-without-lease",
        ),
        pytest.param(
            dhcp_management_commands(interfaces={"Management1": ip_interface("MGMT", "203.0.113.10", dhcp=True, mask_length=24)}),
            ConfigurationState.CONFIGURED,
            id="dhcp-lease-outside-network",
        ),
        pytest.param(
            dhcp_management_commands(interfaces={"Management1/1": ip_interface("MGMT", UNASSIGNED_IPV4, dhcp=True, mask_length=0)}),
            ConfigurationState.CONFIGURED,
            id="modular-management-interface",
        ),
        pytest.param(dhcp_management_commands(), ConfigurationState.NOT_CONFIGURED, id="static-address"),
        pytest.param(
            dhcp_management_commands(RIP_VRF_ENABLED, interfaces={"Management1": ip_interface("MGMT", UNASSIGNED_IPV4, dhcp=True, mask_length=0)}),
            ConfigurationState.NOT_CONFIGURED,
            id="no-enabled-rip-in-management-vrf",
        ),
        pytest.param(
            dhcp_management_commands(interfaces={"Management1": MANAGEMENT1, "Vlan3990": ip_interface("MGMT", UNASSIGNED_IPV4, dhcp=True)}),
            ConfigurationState.NOT_CONFIGURED,
            id="dhcp-data-interface-ignored",
        ),
        pytest.param(
            dhcp_management_commands(interfaces={"Management1": MANAGEMENT1, "Ethernet1": {"vrf": "MGMT"}}),
            ConfigurationState.NOT_CONFIGURED,
            id="invalid-data-interface-ignored",
        ),
    ],
)
def test_rip_dhcp_management_interface_states(device: OfflineAntaDevice, commands: tuple[AntaCommand, ...], state: ConfigurationState) -> None:
    """Report DHCP addressing of management interfaces in an enabled RIP VRF regardless of the current lease."""
    fact = RipDhcpManagementInterfaceFact.derive(device, commands)

    assert isinstance(fact, AvailableFact)
    assert fact.value.state is state
    assert fact.source.name == RipDhcpManagementInterfaceFact.commands[1].command


@pytest.mark.parametrize("rip_config", [pytest.param("", id="not-configured"), pytest.param(RIP_DEFAULT_SHUTDOWN, id="shutdown")])
def test_rip_dhcp_management_interface_without_enabled_rip_ignores_interfaces(device: OfflineAntaDevice, rip_config: str) -> None:
    """Return a not-configured state from the RIP configuration without requiring interface addressing."""
    fact = RipDhcpManagementInterfaceFact.derive(device, dhcp_management_commands(rip_config, interfaces=[]))

    assert isinstance(fact, AvailableFact)
    assert fact.value.state is ConfigurationState.NOT_CONFIGURED
    assert fact.source.name == RipDhcpManagementInterfaceFact.commands[0].command


@pytest.mark.parametrize(
    ("commands", "problem", "source_index"),
    [
        pytest.param(dhcp_management_commands("router rip vrf MGMT\n   network 192.0.2.0/24\n"), FactProblemKind.MALFORMED, 0, id="rip-missing-shutdown-state"),
        pytest.param(dhcp_management_commands(interfaces=[]), FactProblemKind.MALFORMED, 1, id="interfaces-not-mapping"),
        pytest.param(dhcp_management_commands(interfaces={"Management1": without_dhcp_key(MANAGEMENT1)}), FactProblemKind.MISSING, 1, id="missing-dhcp-flag"),
        pytest.param(
            dhcp_management_commands(interfaces={"Management1": {"interfaceAddress": MANAGEMENT1["interfaceAddress"]}}),
            FactProblemKind.MISSING,
            1,
            id="missing-vrf",
        ),
        pytest.param(
            dhcp_management_commands(interfaces={"Management1": {**MANAGEMENT1, "vrf": ""}}),
            FactProblemKind.MALFORMED,
            1,
            id="empty-vrf",
        ),
        pytest.param(
            dhcp_management_commands(interfaces={"Management1": {**MANAGEMENT1, "interfaceAddress": []}}),
            FactProblemKind.MALFORMED,
            1,
            id="malformed-addressing",
        ),
    ],
)
def test_rip_dhcp_management_interface_unavailable(
    device: OfflineAntaDevice,
    commands: tuple[AntaCommand, ...],
    problem: FactProblemKind,
    source_index: int,
) -> None:
    """Retain the exact failing command when DHCP addressing of management interfaces cannot be established."""
    fact = RipDhcpManagementInterfaceFact.derive(device, commands)

    assert isinstance(fact, UnavailableFact)
    assert fact.problem is problem
    assert fact.source.name == RipDhcpManagementInterfaceFact.commands[source_index].command


@pytest.mark.parametrize("definition", [RipDhcpMd5InterfaceFact, RipDhcpManagementInterfaceFact])
def test_rip_dhcp_facts_missing_interfaces_key(device: OfflineAntaDevice, definition: type[RipDhcpMd5InterfaceFact | RipDhcpManagementInterfaceFact]) -> None:
    """Treat structured output without the interface collection as incomplete."""
    commands = dhcp_md5_commands() if definition is RipDhcpMd5InterfaceFact else dhcp_management_commands()
    commands[-1].output = {}

    fact = definition.derive(device, commands)

    assert isinstance(fact, UnavailableFact)
    assert fact.problem is FactProblemKind.MISSING
    assert fact.source.name == "show ip interface"


@pytest.mark.parametrize(
    ("definition", "commands", "index"),
    [
        pytest.param(RipEnabledFact, lambda: (text_command(RipEnabledFact, RIP_VRF_ENABLED),), 0, id="enabled-rip-config"),
        *(
            pytest.param(definition, factory, index, id=f"{name}-{source}")
            for definition, factory, name, sources in (
                (RipMd5AuthenticationFact, rip_md5_commands, "md5", ("rip-config", "authentication-config", "ip-interface")),
                (RipDhcpMd5InterfaceFact, dhcp_md5_commands, "dhcp-md5", ("rip-config", "authentication-config", "ip-interface")),
                (RipManagementInterfaceFact, rip_management_commands, "management", ("rip-config", "ip-interface")),
                (RipDhcpManagementInterfaceFact, dhcp_management_commands, "dhcp-management", ("rip-config", "ip-interface")),
            )
            for index, source in enumerate(sources)
        ),
    ],
)
def test_rip_facts_failed_collection(device: OfflineAntaDevice, definition: type, commands: Callable[[], tuple[AntaCommand, ...]], index: int) -> None:
    """Report a deferred collection failure against the failing command without reading its output."""
    collected = commands()
    collected[index].output = None
    collected[index].errors = ["permission denied"]

    fact = definition.derive(device, collected)

    assert isinstance(fact, UnavailableFact)
    assert fact.problem is FactProblemKind.COLLECTION_FAILED
    assert fact.source.name == definition.commands[index].command
