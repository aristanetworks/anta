# Copyright (c) 2026 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""BGP instance inventory, listen ports, address-family activation, and configured/operating routing-model facts."""

from __future__ import annotations

import pytest

from anta._advisory.facts.bgp import (
    BgpInstanceFact,
    BgpListenPort,
    BgpNonDefaultListenPortFact,
    BgpPathSelectionActivationFact,
    BgpSrTeActivationFact,
    MultiAgentRoutingFact,
)
from anta._advisory.facts.models import AvailableFact, ConfigurationState, FactProblemKind, FeatureState, UnavailableFact
from tests.units.anta_tests.advisories import OfflineAntaDevice
from tests.units.anta_tests.advisories.bgp_captures import BGP_CONFIG, bgp_instances

# Captured from vEOS-lab 4.31.0F; JSON returns "This is an unconverted command."
INSTANCE = """BGP instance information for VRF default
BGP Local AS:   123, Router ID: 1.1.1.1
Total peers:              0
  Static peers:           0
  Dynamic peers:          0
  Disabled peers:         0
  Established peers:      0
Four Octet ASN mode enabled
Graceful restart helper mode enabled
Graceful restart mode disabled
End of rib timer timeout: 00:05:00
Attributes of the reflected routes are not preserved
Number of Adj-RIB-Ins awaiting cleanup: 0
Maximum paths: 1 Maximum ECMP: 128
UCMP mode: disabled
Peer mac resolution timeout: 00:00:00
BGP Convergence timer is inactive
BGP Convergence based update synchronization is disabled
BGP Convergence slow-peer timeout: 00:01:30
BGP Listen Port Status: listening on port 179
BGP Convergence information:
    BGP has converged:   yes,   Time taken to converge: 00:00:30
    Outstanding EORs:    0,     Outstanding Keepalives: 0
    Convergence timeout: 00:05:00
Address family IPv4 Unicast:
  Additional-paths installation is disabled
  Extended next-hop capability is disabled
Address family IPv6 Unicast:
  Additional-paths installation is disabled
"""


@pytest.mark.parametrize(
    "output",
    [INSTANCE, INSTANCE.replace("VRF default", "VRF RED"), INSTANCE + INSTANCE.replace("VRF default", "VRF RED")],
)
def test_bgp_instance_presence(output: str) -> None:
    """Count any reported instance, including zero-peer default and named VRFs."""
    command = BgpInstanceFact.commands[0].model_copy()
    command.output = output
    fact = BgpInstanceFact.derive(OfflineAntaDevice("unit-test"), (command,))
    assert isinstance(fact, AvailableFact)
    assert fact.value.state is FeatureState.ENABLED
    assert fact.source.name == "show bgp instance vrf all"


@pytest.mark.parametrize(
    "output",
    [
        "",
        " \n\t",
        "BGP is disabled for VRF default (Missing Router ID)\n",
        "BGP is disabled for VRF RED (Missing Router ID)\n",
        "BGP is disabled for VRF default (Missing Router ID)\nBGP is disabled for VRF RED (Missing Router ID)\n",
    ],
)
def test_bgp_instance_absence(output: str) -> None:
    """Recognize older EOS empty inventory and newer EOS explicit disabled VRFs."""
    command = BgpInstanceFact.commands[0].model_copy()
    command.output = output
    fact = BgpInstanceFact.derive(OfflineAntaDevice("unit-test"), (command,))
    assert isinstance(fact, AvailableFact)
    assert fact.value.state is FeatureState.DISABLED


@pytest.mark.parametrize("disabled_first", [True, False])
def test_present_instance_survives_disabled_vrf(disabled_first: bool) -> None:
    """An absent instance in one VRF cannot hide a present instance in another."""
    disabled = "BGP is disabled for VRF RED (Missing Router ID)\n"
    command = BgpInstanceFact.commands[0].model_copy()
    command.output = disabled + INSTANCE if disabled_first else INSTANCE + disabled
    fact = BgpInstanceFact.derive(OfflineAntaDevice("unit-test"), (command,))
    assert isinstance(fact, AvailableFact)
    assert fact.value.state is FeatureState.ENABLED


@pytest.mark.parametrize(
    ("output", "problem"),
    [
        (None, FactProblemKind.MISSING),
        ({"vrfs": {}}, FactProblemKind.MALFORMED),
        ({"errors": ["This is an unconverted command."]}, FactProblemKind.MALFORMED),
        ([], FactProblemKind.MALFORMED),
        ("BGP is not active", FactProblemKind.MALFORMED),
        ("BGP is disabled for VRF ", FactProblemKind.MALFORMED),
        ("BGP is disabled for VRF default (Missing Router ID)\nunrecognized output", FactProblemKind.MALFORMED),
        ("BGP instance information for VRF ", FactProblemKind.MALFORMED),
        ("description BGP instance information for VRF default", FactProblemKind.MALFORMED),
        ("BGP instance information for VRF default unexpected", FactProblemKind.MALFORMED),
    ],
)
def test_invalid_bgp_inventory(output: object, problem: FactProblemKind) -> None:
    """Incomplete or unrecognized text cannot prove BGP absent."""
    command = BgpInstanceFact.commands[0].model_copy()
    command.output = output  # type: ignore[assignment]
    fact = BgpInstanceFact.derive(OfflineAntaDevice("unit-test"), (command,))
    assert isinstance(fact, UnavailableFact)
    assert fact.problem is problem
    assert fact.source.name == command.command


@pytest.mark.parametrize(
    ("configured", "operating", "expected"),
    [
        ("multi-agent", "multi-agent", FeatureState.ENABLED),
        ("ribd", "multi-agent", FeatureState.ENABLED),
        ("multi-agent", "ribd", FeatureState.ENABLED),
        ("ribd", "ribd", FeatureState.DISABLED),
    ],
)
def test_routing_model(configured: str, operating: str, expected: FeatureState) -> None:
    """A pending model change cannot hide current or configured multi-agent routing."""
    command = MultiAgentRoutingFact.commands[0].model_copy()
    command.output = {
        "protoModelStatus": {"configuredProtoModel": configured, "operatingProtoModel": operating},
        "vrfs": {"default": {"connected": 1}},
    }
    fact = MultiAgentRoutingFact.derive(OfflineAntaDevice("unit-test"), (command,))
    assert isinstance(fact, AvailableFact)
    assert fact.value.state is expected
    assert fact.source.name == "show ip route summary"


@pytest.mark.parametrize("field", ["configuredProtoModel", "operatingProtoModel"])
@pytest.mark.parametrize("other", [None, "unknown", [], {}])
def test_known_multi_agent_survives_unavailable_companion(field: str, other: object) -> None:
    """One positive observation is sufficient even when the other field is unusable."""
    status = {"configuredProtoModel": other, "operatingProtoModel": other, field: "multi-agent"}
    command = MultiAgentRoutingFact.commands[0].model_copy()
    command.output = {"protoModelStatus": status}
    fact = MultiAgentRoutingFact.derive(OfflineAntaDevice("unit-test"), (command,))
    assert isinstance(fact, AvailableFact)
    assert fact.value.state is FeatureState.ENABLED


@pytest.mark.parametrize("field", ["configuredProtoModel", "operatingProtoModel"])
def test_known_multi_agent_survives_missing_companion(field: str) -> None:
    """A missing companion field cannot erase confirmed multi-agent routing."""
    command = MultiAgentRoutingFact.commands[0].model_copy()
    command.output = {"protoModelStatus": {field: "multi-agent"}}
    fact = MultiAgentRoutingFact.derive(OfflineAntaDevice("unit-test"), (command,))
    assert isinstance(fact, AvailableFact)
    assert fact.value.state is FeatureState.ENABLED


@pytest.mark.parametrize(
    ("output", "problem"),
    [
        (None, FactProblemKind.MISSING),
        ({}, FactProblemKind.MISSING),
        ("service routing protocols model ribd", FactProblemKind.MALFORMED),
        ({"protoModelStatus": None}, FactProblemKind.MALFORMED),
        ({"protoModelStatus": []}, FactProblemKind.MALFORMED),
        ({"protoModelStatus": {}}, FactProblemKind.MISSING),
        ({"protoModelStatus": {"configuredProtoModel": "ribd"}}, FactProblemKind.MISSING),
        ({"protoModelStatus": {"operatingProtoModel": "ribd"}}, FactProblemKind.MISSING),
        ({"protoModelStatus": {"configuredProtoModel": "ribd", "operatingProtoModel": None}}, FactProblemKind.MALFORMED),
        ({"protoModelStatus": {"configuredProtoModel": [], "operatingProtoModel": "ribd"}}, FactProblemKind.MALFORMED),
        ({"protoModelStatus": {"configuredProtoModel": "ribd", "operatingProtoModel": "unknown"}}, FactProblemKind.INVALID),
        ({"protoModelStatus": {"configuredProtoModel": "unknown", "operatingProtoModel": "ribd"}}, FactProblemKind.INVALID),
    ],
)
def test_invalid_routing_model(output: object, problem: FactProblemKind) -> None:
    """Without a positive model, incomplete or unrecognized evidence is an error."""
    command = MultiAgentRoutingFact.commands[0].model_copy()
    command.output = output  # type: ignore[assignment]
    fact = MultiAgentRoutingFact.derive(OfflineAntaDevice("unit-test"), (command,))
    assert isinstance(fact, UnavailableFact)
    assert fact.problem is problem
    assert fact.source.name == "show ip route summary"


@pytest.mark.parametrize("fact_type", [BgpInstanceFact, MultiAgentRoutingFact])
@pytest.mark.parametrize(
    ("error", "problem"),
    [
        ("could not run command", FactProblemKind.COLLECTION_FAILED),
        ("This is an unconverted command.", FactProblemKind.COLLECTION_FAILED),
        ("This command is not supported on this hardware platform", FactProblemKind.UNSUPPORTED),
    ],
)
def test_collection_failures_keep_exact_source(fact_type: type[BgpInstanceFact | MultiAgentRoutingFact], error: str, problem: FactProblemKind) -> None:
    """Each required command retains its own collection error."""
    command = fact_type.commands[0].model_copy()
    command.output = ""
    command.errors = [error]
    fact = fact_type.derive(OfflineAntaDevice("unit-test"), (command,))
    assert isinstance(fact, UnavailableFact)
    assert fact.problem is problem
    assert fact.source.name == command.command


@pytest.mark.parametrize("error", ["BGP inactive", "% BGP inactive"])
def test_inactive_bgp_error_establishes_absence(error: str) -> None:
    """Treat the specific EOS inactive response as absence rather than collection failure."""
    command = BgpInstanceFact.commands[0].model_copy()
    command.errors = [error]
    fact = BgpInstanceFact.derive(OfflineAntaDevice("unit-test"), (command,))
    assert isinstance(fact, AvailableFact)
    assert fact.value.state is FeatureState.DISABLED
    assert fact.source.name == "show bgp instance vrf all"


@pytest.mark.parametrize(
    "errors",
    [
        ["BGP inactive", "permission denied"],
        ["BGP inactive while command collection failed"],
        ["unexpected BGP inactive"],
    ],
)
def test_inactive_marker_cannot_hide_collection_failure(errors: list[str]) -> None:
    """Require every error to be the exact inactive response before establishing absence."""
    command = BgpInstanceFact.commands[0].model_copy()
    command.errors = errors
    fact = BgpInstanceFact.derive(OfflineAntaDevice("unit-test"), (command,))
    assert isinstance(fact, UnavailableFact)
    assert fact.problem is FactProblemKind.COLLECTION_FAILED
    assert fact.source.name == "show bgp instance vrf all"


def derive_listen_ports(
    output: object, errors: list[str] | None = None
) -> AvailableFact[BgpNonDefaultListenPortFact] | UnavailableFact[BgpNonDefaultListenPortFact]:
    """Derive listen ports from one `show bgp instance vrf all` JSON observation."""
    command = BgpNonDefaultListenPortFact.commands[0].model_copy()
    command.output = output  # type: ignore[assignment]
    command.errors = errors or []
    return BgpNonDefaultListenPortFact.derive(OfflineAntaDevice("unit-test"), (command,))


@pytest.mark.parametrize(
    ("output", "ports"),
    [
        (bgp_instances(), ()),
        (bgp_instances(("default", 179, 179), ("RED", 179, 179)), ()),
        ({"vrfs": {}}, ()),
        (bgp_instances(("default", 1179, 179)), (BgpListenPort("default", "IPv4", 1179),)),
        (
            bgp_instances(("default", 179, 179), ("RED", 2179, 2179)),
            (BgpListenPort("RED", "IPv4", 2179), BgpListenPort("RED", "IPv6", 2179)),
        ),
    ],
)
def test_listen_ports(output: object, ports: tuple[BgpListenPort, ...]) -> None:
    """Only ports other than TCP 179 are retained, in any VRF and either address family."""
    fact = derive_listen_ports(output)
    assert isinstance(fact, AvailableFact)
    assert fact.value.state is (ConfigurationState.CONFIGURED if ports else ConfigurationState.NOT_CONFIGURED)
    assert fact.value.ports == ports
    assert fact.value.problem is None
    assert fact.source.name == "show bgp instance vrf all"


@pytest.mark.parametrize(
    ("output", "problem"),
    [
        (None, FactProblemKind.MISSING),
        ({}, FactProblemKind.MISSING),
        ({"vrfs": {"default": {"localAs": 65010}}}, FactProblemKind.MISSING),
        ({"vrfs": {"default": {"bgpIpv4ListenPort": 179}}}, FactProblemKind.MISSING),
        ({"vrfs": {"default": {"bgpIpv4ListenPort": 179, "bgpIpv6ListenPort": None}}}, FactProblemKind.MISSING),
        ({"vrfs": {"default": {"localAs": 65010}, "RED": None}}, FactProblemKind.MALFORMED),
        ({"vrfs": {"RED": None, "default": {"localAs": 65010}}}, FactProblemKind.MALFORMED),
        (bgp_instances() | {"vrfs": {**bgp_instances()["vrfs"], "RED": {"localAs": 65010}}}, FactProblemKind.MISSING),
        ("BGP instance information for VRF default", FactProblemKind.MALFORMED),
        ({"vrfs": []}, FactProblemKind.MALFORMED),
        ({"vrfs": {"default": None}}, FactProblemKind.MALFORMED),
        ({"vrfs": {"default": {"bgpIpv4ListenPort": "179"}}}, FactProblemKind.MALFORMED),
        ({"vrfs": {"default": {"bgpIpv4ListenPort": True}}}, FactProblemKind.MALFORMED),
    ],
)
def test_invalid_listen_ports(output: object, problem: FactProblemKind) -> None:
    """Without a non-default port, any unreadable listen port prevents absence; malformed outranks missing in any order."""
    fact = derive_listen_ports(output)
    assert isinstance(fact, UnavailableFact)
    assert fact.problem is problem


VALID_1179 = {"bgpIpv4ListenPort": 1179, "bgpIpv6ListenPort": 1179}


@pytest.mark.parametrize("reverse", [False, True], ids=["witness-first", "witness-last"])
@pytest.mark.parametrize(
    ("witness", "unreadable", "ports", "problem"),
    [
        (VALID_1179, {"localAs": 65010}, ("IPv4", "IPv6"), FactProblemKind.MISSING),
        (VALID_1179, None, ("IPv4", "IPv6"), FactProblemKind.MALFORMED),
        (VALID_1179, {"bgpIpv4ListenPort": "179", "bgpIpv6ListenPort": 179}, ("IPv4", "IPv6"), FactProblemKind.MALFORMED),
        ({"bgpIpv4ListenPort": 1179, "bgpIpv6ListenPort": True}, {"bgpIpv4ListenPort": 179, "bgpIpv6ListenPort": 179}, ("IPv4",), FactProblemKind.MALFORMED),
        ({"bgpIpv4ListenPort": 1179}, {"bgpIpv4ListenPort": 179, "bgpIpv6ListenPort": 179}, ("IPv4",), FactProblemKind.MISSING),
        ({"bgpIpv6ListenPort": 1179, "bgpIpv4ListenPort": [179]}, {"bgpIpv4ListenPort": 179, "bgpIpv6ListenPort": 179}, ("IPv6",), FactProblemKind.MALFORMED),
    ],
)
def test_non_default_port_survives_unreadable_siblings(
    witness: dict[str, object], unreadable: object, ports: tuple[str, ...], problem: FactProblemKind, *, reverse: bool
) -> None:
    """A valid non-default port is retained despite another VRF or address family being unreadable, in either VRF order."""
    vrfs = [("default", witness), ("RED", unreadable)]
    fact = derive_listen_ports({"vrfs": dict(reversed(vrfs) if reverse else vrfs)})
    assert isinstance(fact, AvailableFact)
    assert fact.value.state is ConfigurationState.CONFIGURED
    assert fact.value.ports == tuple(BgpListenPort("default", family, 1179) for family in ports)
    assert fact.value.problem is problem


@pytest.mark.parametrize(
    ("errors", "available"),
    [
        (["BGP inactive"], True),
        (["% BGP inactive"], True),
        (["BGP inactive", "permission denied"], False),
        (["This is an unconverted command."], False),
    ],
)
def test_listen_port_command_errors(errors: list[str], available: bool) -> None:
    """Only the exact EOS inactive response establishes that no listen port exists."""
    fact = derive_listen_ports(None, errors)
    assert isinstance(fact, AvailableFact) is available
    if isinstance(fact, AvailableFact):
        assert fact.value.state is ConfigurationState.NOT_CONFIGURED
    else:
        assert fact.problem is FactProblemKind.COLLECTION_FAILED


PATH_SELECTION = "   address-family path-selection\n      neighbor PS activate\n      neighbor 192.0.2.1 activate\n      no neighbor 192.0.2.4 activate\n"
IPV4_SR_TE = "   address-family ipv4 sr-te\n      neighbor 192.0.2.3 activate\n"
IPV6_SR_TE = "   address-family ipv6 sr-te\n      neighbor 2001:db8::1 activate\n"


@pytest.mark.parametrize(
    ("fact_type", "config", "activated"),
    [
        (BgpPathSelectionActivationFact, BGP_CONFIG, ("path-selection",)),
        (BgpPathSelectionActivationFact, BGP_CONFIG.replace(PATH_SELECTION, ""), ()),
        (BgpPathSelectionActivationFact, BGP_CONFIG.replace(PATH_SELECTION, "   address-family path-selection\n      no neighbor PS activate\n"), ()),
        (
            BgpPathSelectionActivationFact,
            BGP_CONFIG.replace(PATH_SELECTION, "") + "      address-family path-selection\n         neighbor PS activate\n",
            ("path-selection",),
        ),
        (BgpPathSelectionActivationFact, "", ()),
        (BgpSrTeActivationFact, BGP_CONFIG, ("ipv4 sr-te", "ipv6 sr-te")),
        (BgpSrTeActivationFact, BGP_CONFIG.replace(IPV6_SR_TE, ""), ("ipv4 sr-te",)),
        (BgpSrTeActivationFact, BGP_CONFIG.replace(IPV4_SR_TE, ""), ("ipv6 sr-te",)),
        (BgpSrTeActivationFact, BGP_CONFIG.replace(IPV4_SR_TE, "").replace(IPV6_SR_TE, ""), ()),
        (BgpSrTeActivationFact, BGP_CONFIG.replace(IPV4_SR_TE, "   address-family ipv4\n      neighbor 192.0.2.3 activate\n").replace(IPV6_SR_TE, ""), ()),
        (BgpSrTeActivationFact, BGP_CONFIG.replace(IPV4_SR_TE, "   address-family ipv4 sr-te\n   neighbor 192.0.2.3 activate\n").replace(IPV6_SR_TE, ""), ()),
    ],
)
def test_address_family_activation(fact_type: type[BgpPathSelectionActivationFact | BgpSrTeActivationFact], config: str, activated: tuple[str, ...]) -> None:
    """Any activate line beneath the target address family counts at any depth; other families do not."""
    command = fact_type.commands[0].model_copy()
    command.output = config
    fact = fact_type.derive(OfflineAntaDevice("unit-test"), (command,))
    assert isinstance(fact, AvailableFact)
    assert fact.value.state is (ConfigurationState.CONFIGURED if activated else ConfigurationState.NOT_CONFIGURED)
    assert fact.value.activated == activated
    assert fact.source.name == "show running-config | section router bgp"


@pytest.mark.parametrize("fact_type", [BgpPathSelectionActivationFact, BgpSrTeActivationFact])
@pytest.mark.parametrize(
    ("output", "errors", "problem"),
    [
        (None, [], FactProblemKind.MISSING),
        ({}, [], FactProblemKind.MALFORMED),
        ("", ["could not run command"], FactProblemKind.COLLECTION_FAILED),
    ],
)
def test_invalid_address_family_configuration(
    fact_type: type[BgpPathSelectionActivationFact | BgpSrTeActivationFact], output: object, errors: list[str], problem: FactProblemKind
) -> None:
    """Failed or unreadable collection never establishes absence."""
    command = fact_type.commands[0].model_copy()
    command.output = output  # type: ignore[assignment]
    command.errors = errors
    fact = fact_type.derive(OfflineAntaDevice("unit-test"), (command,))
    assert isinstance(fact, UnavailableFact)
    assert fact.problem is problem
