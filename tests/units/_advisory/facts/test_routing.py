# Copyright (c) 2026 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Unit tests for facts normalized from EOS routing output."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import pytest

from anta._advisory.facts.models import AvailableFact, ConfigurationState, FactProblemKind, FeatureState, MitigationState, UnavailableFact
from anta._advisory.facts.routing import (
    BfdAuthenticationFact,
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
)
from tests.units.anta_tests.advisories import OfflineAntaDevice

if TYPE_CHECKING:
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
        (bfd_commands(interface_config="bfd authentication mode simple shared-secret profile test"), FeatureState.ENABLED),
        (bfd_commands(interface_config="bfd authentication mode disabled"), FeatureState.DISABLED),
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
        (bfd_commands(admin_down=None), FactProblemKind.MISSING),
        (bfd_commands(admin_down="false"), FactProblemKind.MALFORMED),
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
