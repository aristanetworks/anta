# Copyright (c) 2026 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Persistent BGP-LS activation and captured revision-three DPS role evidence."""

from __future__ import annotations

from copy import deepcopy
from typing import Any, cast

import pytest

from anta._advisory.facts.bgp_link_state import BgpLinkStateDpsConsumerFact
from anta._advisory.facts.models import AvailableFact, ConfigurationState, Fact, FactProblemKind, UnavailableFact
from tests.units.anta_tests.advisories import OfflineAntaDevice

CONFIG = (
    "router bgp 65211\n"
    "   router-id 192.0.2.211\n"
    "   neighbor BGP_LS_PEERS peer group\n"
    "   neighbor BGP_LS_PEERS remote-as 65212\n"
    "   neighbor 192.0.2.212 peer group BGP_LS_PEERS\n"
    "   address-family link-state\n"
    "      neighbor BGP_LS_PEERS activate\n"
    "      path-selection role consumer propagator\n"
)
INSTANCE: dict[str, Any] = {
    "vrfs": {
        "default": {
            "localAs": 65211,
            "afiSafiConfig": {
                "linkState": {
                    "bgpLsProtoRoles": [
                        {"role": "propagator", "protocol": "dps"},
                        {"role": "consumer", "protocol": "dps"},
                    ]
                }
            },
        }
    }
}


def derive(config: str = CONFIG, instance: object | None = None) -> Fact[BgpLinkStateDpsConsumerFact]:
    """Derive the observation without runtime neighbors, router IDs, or peer ASNs."""
    commands = tuple(command.model_copy() for command in BgpLinkStateDpsConsumerFact.commands)
    commands[0].output = config
    commands[1].output = deepcopy(INSTANCE) if instance is None else cast("dict[str, Any] | str", instance)
    return BgpLinkStateDpsConsumerFact.derive(OfflineAntaDevice("unit-test"), commands)


@pytest.mark.parametrize("state", ["Active", "Connect", "Established", "Idle"])
def test_activation_does_not_depend_on_runtime_state(state: str) -> None:
    """Ignore transient state while preserving configured names and local role."""
    instance = deepcopy(INSTANCE)
    instance["vrfs"]["default"]["peers"] = {"totalPeers": 0, "establishedPeers": 0, "state": state}
    fact = derive(instance=instance)
    assert isinstance(fact, AvailableFact)
    assert fact.value.state is ConfigurationState.CONFIGURED
    scope = fact.value.scopes[0]
    assert (scope.instance, scope.vrf) == ("65211", "default")
    assert scope.consumer_dps
    assert scope.activated_neighbors == ("BGP_LS_PEERS",)
    assert fact.source.name == "show bgp instance vrf all"


@pytest.mark.parametrize(
    "config",
    [
        "",
        "router bgp 65211\n",
        CONFIG.replace("      neighbor BGP_LS_PEERS activate\n", ""),
        CONFIG.replace("   router-id", "   shutdown\n   router-id"),
    ],
)
def test_persistent_absence_short_circuits_failed_role(config: str) -> None:
    """AF absence and confirmed administrative shutdown remain decisive."""
    commands = tuple(command.model_copy() for command in BgpLinkStateDpsConsumerFact.commands)
    commands[0].output = config
    commands[1].errors = ["cannot run command"]
    fact = BgpLinkStateDpsConsumerFact.derive(OfflineAntaDevice("unit-test"), commands)
    assert isinstance(fact, AvailableFact)
    assert fact.value.state is ConfigurationState.NOT_CONFIGURED
    assert fact.source.name == "show running-config | section router bgp"


@pytest.mark.parametrize(
    "roles",
    [
        {},
        {"bgpLsProtoRoles": []},
        {"bgpLsProtoRoles": [{"role": "propagator", "protocol": "dps"}]},
        {"bgpLsProtoRoles": [{"role": "consumer", "protocol": "isis"}]},
    ],
)
def test_no_dps_consumer_is_decisive(roles: object) -> None:
    """Other protocols and valid absent roles do not satisfy DPS consumption."""
    instance = deepcopy(INSTANCE)
    instance["vrfs"]["default"]["afiSafiConfig"]["linkState"] = roles
    fact = derive(CONFIG.replace("      path-selection role consumer propagator\n", ""), instance)
    assert isinstance(fact, AvailableFact)
    assert fact.value.state is ConfigurationState.NOT_CONFIGURED


def test_roles_cannot_cross_vrf_activations() -> None:
    """The default consumer cannot satisfy an activation in a different VRF."""
    instance = deepcopy(INSTANCE)
    instance["vrfs"]["OTHER"] = deepcopy(instance["vrfs"]["default"])
    instance["vrfs"]["OTHER"]["afiSafiConfig"]["linkState"]["bgpLsProtoRoles"] = []
    config = (
        "router bgp 65211\n"
        "   address-family link-state\n"
        "      path-selection role consumer propagator\n"
        "   vrf OTHER\n"
        "      address-family link-state\n"
        "         neighbor GROUP activate\n"
    )
    fact = derive(config, instance)
    assert isinstance(fact, AvailableFact)
    assert fact.value.state is ConfigurationState.NOT_CONFIGURED
    assert [(scope.instance, scope.vrf, scope.consumer_dps) for scope in fact.value.scopes] == [("65211", "OTHER", False)]


def test_only_activated_vrf_role_evidence_is_required() -> None:
    """An unrelated malformed VRF does not hide a qualified consumer scope."""
    instance = deepcopy(INSTANCE)
    instance["vrfs"]["UNRELATED"] = {}
    fact = derive(instance=instance)
    assert isinstance(fact, AvailableFact)
    assert fact.value.state is ConfigurationState.CONFIGURED


@pytest.mark.parametrize(("configured", "observed"), [("1.10", 65546), ("65546", "1.10"), ("1.10", "1.10"), ("65211", "65211")])
def test_configured_instance_asn_formats(configured: str, observed: str | int) -> None:
    """Equivalent numeric and asdot identities correlate without router-ID evidence."""
    instance = deepcopy(INSTANCE)
    instance["vrfs"]["default"]["localAs"] = observed
    fact = derive(CONFIG.replace("router bgp 65211", f"router bgp {configured}"), instance)
    assert isinstance(fact, AvailableFact)
    assert fact.value.state is ConfigurationState.CONFIGURED
    assert fact.value.scopes[0].instance == configured


def test_instance_identity_must_match() -> None:
    """A role from another configured local AS is contradictory, never absence."""
    instance = deepcopy(INSTANCE)
    instance["vrfs"]["default"]["localAs"] = 65213
    fact = derive(instance=instance)
    assert isinstance(fact, UnavailableFact)
    assert fact.problem is FactProblemKind.CONTRADICTORY
    assert fact.source.name == "show bgp instance vrf all"
    assert {item.scopes[0].instance for item in fact.observations} == {"65211", "65213"}


@pytest.mark.parametrize("asn", [True, "invalid", "1.65536", "65536.1", -1, 4294967296])
def test_invalid_role_instance_is_error(asn: object) -> None:
    """Malformed local AS cannot establish a safe association or absence."""
    instance = deepcopy(INSTANCE)
    instance["vrfs"]["default"]["localAs"] = asn
    fact = derive(instance=instance)
    assert isinstance(fact, UnavailableFact)
    assert fact.problem is FactProblemKind.MALFORMED


@pytest.mark.parametrize("instance", [{}, {"vrfs": {}}, {"vrfs": []}, {"vrfs": {"default": {}}}, {"vrfs": {"default": {"localAs": 65211, "afiSafiConfig": {}}}}])
def test_invalid_instance_is_not_role_absence(instance: object) -> None:
    """Missing configured instances and required fields are unavailable."""
    fact = derive(instance=instance)
    assert isinstance(fact, UnavailableFact)
    assert fact.source.name == "show bgp instance vrf all"


@pytest.mark.parametrize(
    "roles",
    [
        {"unknown": []},
        {"bgpLsProtoRoles": "consumer"},
        {"bgpLsProtoRoles": [None]},
        {"bgpLsProtoRoles": [{"role": "consumer"}]},
        {"bgpLsProtoRoles": [{"role": 5, "protocol": "dps"}]},
    ],
)
def test_malformed_role_is_not_absent(roles: object) -> None:
    """Keep malformed role/protocol evidence separate from valid empty roles."""
    instance = deepcopy(INSTANCE)
    instance["vrfs"]["default"]["afiSafiConfig"]["linkState"] = roles
    fact = derive(instance=instance)
    assert isinstance(fact, UnavailableFact)
    assert fact.source.name == "show bgp instance vrf all"


def test_persistent_role_omission_is_contradictory() -> None:
    """A configured consumer cannot be erased by an empty role snapshot."""
    instance = deepcopy(INSTANCE)
    instance["vrfs"]["default"]["afiSafiConfig"]["linkState"]["bgpLsProtoRoles"] = []
    fact = derive(instance=instance)
    assert isinstance(fact, UnavailableFact)
    assert fact.problem is FactProblemKind.CONTRADICTORY
    assert {item.scopes[0].consumer_dps for item in fact.observations} == {False, True}
    assert {item.state for item in fact.observations} == {ConfigurationState.NOT_CONFIGURED, ConfigurationState.CONFIGURED}


@pytest.mark.parametrize("dynamic", [False, True])
def test_unused_and_dynamic_groups_are_conservative_exposure(dynamic: bool) -> None:
    """Activated group exposure does not require any instantiated neighbor."""
    replacement = "   bgp listen range 198.51.100.0/24 peer-group BGP_LS_PEERS remote-as 65212\n" if dynamic else ""
    config = CONFIG.replace("   neighbor 192.0.2.212 peer group BGP_LS_PEERS\n", replacement)
    fact = derive(config)
    assert isinstance(fact, AvailableFact)
    assert fact.value.state is ConfigurationState.CONFIGURED
    assert fact.value.scopes[0].activated_neighbors == ("BGP_LS_PEERS",)


@pytest.mark.parametrize("index", [0, 1])
def test_collection_failure_retains_exact_command(index: int) -> None:
    """The two-command observation preserves the exact failed command."""
    commands = tuple(command.model_copy() for command in BgpLinkStateDpsConsumerFact.commands)
    commands[0].output = CONFIG
    commands[1].output = deepcopy(INSTANCE)
    commands[index].errors = ["Collection failed"]
    fact = BgpLinkStateDpsConsumerFact.derive(OfflineAntaDevice("unit-test"), commands)
    assert isinstance(fact, UnavailableFact)
    assert fact.problem is FactProblemKind.COLLECTION_FAILED
    assert fact.source.name == commands[index].command


def test_command_contract_has_no_summary() -> None:
    """Collection needs persistent activation and local processing role only."""
    assert [(command.command, command.revision, command.ofmt) for command in BgpLinkStateDpsConsumerFact.commands] == [
        ("show running-config | section router bgp", 1, "text"),
        ("show bgp instance vrf all", 3, "json"),
    ]


def test_unsupported_role_retains_its_source() -> None:
    """Unsupported required role collection is Error evidence, not role absence."""
    commands = tuple(command.model_copy() for command in BgpLinkStateDpsConsumerFact.commands)
    commands[0].output = CONFIG
    commands[1].errors = ["This command is not supported on this hardware platform"]
    fact = BgpLinkStateDpsConsumerFact.derive(OfflineAntaDevice("unit-test"), commands)
    assert isinstance(fact, UnavailableFact)
    assert fact.problem is FactProblemKind.UNSUPPORTED
    assert fact.source.name == "show bgp instance vrf all"


def test_missing_role_output_is_not_absence() -> None:
    """A missing payload cannot disable a persistently activated consumer scope."""
    commands = tuple(command.model_copy() for command in BgpLinkStateDpsConsumerFact.commands)
    commands[0].output = CONFIG
    fact = BgpLinkStateDpsConsumerFact.derive(OfflineAntaDevice("unit-test"), commands)
    assert isinstance(fact, UnavailableFact)
    assert fact.problem is FactProblemKind.MISSING
    assert fact.source.name == "show bgp instance vrf all"
