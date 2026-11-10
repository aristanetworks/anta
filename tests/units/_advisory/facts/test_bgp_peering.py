# Copyright (c) 2026 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Persistent Link-State AF activation, independent of runtime neighbor state."""

from __future__ import annotations

import pytest

from anta._advisory.facts.bgp_peering import BgpLinkStatePeeringFact, BgpLinkStatePeeringScope
from anta._advisory.facts.models import AvailableFact, ConfigurationState, Fact, FactProblemKind, UnavailableFact
from tests.units.anta_tests.advisories import OfflineAntaDevice

CONFIG = "router bgp 65000\n   neighbor 198.51.100.2 remote-as 65001\n   address-family link-state\n      neighbor 198.51.100.2 activate\n"
GROUP = "router bgp 65000\n   neighbor PATHFINDERS peer group\n   address-family link-state\n      neighbor PATHFINDERS activate\n"


def derive(config: str | dict[str, object] | None = CONFIG) -> Fact[BgpLinkStatePeeringFact]:
    """Derive configuration exposure without any operational summary input."""
    command = BgpLinkStatePeeringFact.commands[0].model_copy()
    command.output = config
    return BgpLinkStatePeeringFact.derive(OfflineAntaDevice("unit-test"), (command,))


@pytest.mark.parametrize(
    "config", [CONFIG, GROUP, GROUP.replace("   address-family", "   bgp listen range 198.51.100.0/24 peer-group PATHFINDERS\n   address-family")]
)
def test_activation_needs_no_current_neighbors_or_listener(config: str) -> None:
    """Static, dynamic, and unused activated groups all establish exposure."""
    fact = derive(config)
    assert isinstance(fact, AvailableFact)
    assert fact.value.state is ConfigurationState.CONFIGURED
    assert fact.value.scopes == (BgpLinkStatePeeringScope("65000", "default", ("198.51.100.2" if config == CONFIG else "PATHFINDERS",)),)
    assert fact.source.name == "show running-config | section router bgp"
    assert [command.command for command in BgpLinkStatePeeringFact.commands] == ["show running-config | section router bgp"]


@pytest.mark.parametrize(
    "config",
    [
        "",
        "!\n",
        "router bgp 65000\n",
        "router bgp 65000\n   address-family link-state\n      path-selection role consumer propagator\n",
        "router bgp 65000\n   address-family ipv4\n      neighbor 198.51.100.2 activate\n",
        "router bgp 65000\n   address-family link-state\n      no neighbor 198.51.100.2 activate\n",
        "router bgp 65000\n   address-family link-state\n   address-family ipv4\n      neighbor 198.51.100.2 activate\n",
        "router bgp 65000\n   vrf BLUE\n      address-family link-state\n   vrf RED\n      address-family ipv4\n         neighbor 198.51.100.2 activate\n",
    ],
)
def test_absent_activation_and_sibling_boundaries(config: str) -> None:
    """An AF and activation must share the exact parent and VRF hierarchy."""
    fact = derive(config)
    assert isinstance(fact, AvailableFact)
    assert fact.value.state is ConfigurationState.NOT_CONFIGURED
    assert not fact.value.scopes


@pytest.mark.parametrize(
    "config",
    [
        CONFIG.replace("   neighbor 198", "   shutdown\n   neighbor 198", 1),
        CONFIG.replace("   neighbor 198", "   neighbor 198.51.100.2 shutdown\n   neighbor 198", 1),
        CONFIG.replace("      neighbor 198", "      shutdown\n      neighbor 198"),
        "router bgp 65000\n   vrf BLUE\n      shutdown\n      address-family link-state\n         neighbor P activate\n",
        GROUP.replace("   address-family", "   neighbor PATHFINDERS shutdown\n   address-family"),
        (
            "router bgp 65000\n"
            "   neighbor G peer group\n"
            "   neighbor G shutdown\n"
            "   neighbor P peer group G\n"
            "   address-family link-state\n"
            "      neighbor P activate\n"
        ),
        (
            "router bgp 65000\n"
            "   neighbor G peer group\n"
            "   neighbor G shutdown\n"
            "   vrf BLUE\n"
            "      neighbor P peer group G\n"
            "      address-family link-state\n"
            "         neighbor P activate\n"
        ),
        (
            "router bgp 65000\n"
            "   neighbor G peer group\n"
            "   neighbor G shutdown\n"
            "   neighbor P peer group G\n"
            "   no neighbor P shutdown\n"
            "   address-family link-state\n"
            "      neighbor G activate\n"
            "      no neighbor P activate\n"
        ),
    ],
)
def test_persistent_shutdown_disables_the_only_activation(config: str) -> None:
    """Honor process, VRF, AF, direct neighbor, and inherited group shutdown."""
    fact = derive(config)
    assert isinstance(fact, AvailableFact)
    assert fact.value.state is ConfigurationState.NOT_CONFIGURED


@pytest.mark.parametrize(
    "config",
    [
        CONFIG.replace("   neighbor 198", "   no shutdown\n   neighbor 198", 1),
        CONFIG.replace("   neighbor 198", "   no neighbor 198.51.100.2 shutdown\n   neighbor 198", 1),
        CONFIG.replace("      neighbor 198", "      no shutdown\n      neighbor 198"),
        (
            "router bgp 65000\n"
            "   neighbor G peer group\n"
            "   neighbor G shutdown\n"
            "   neighbor P peer group G\n"
            "   no neighbor P shutdown\n"
            "   address-family link-state\n"
            "      neighbor P activate\n"
        ),
        (
            "router bgp 65000\n"
            "   neighbor G peer group\n"
            "   neighbor G shutdown\n"
            "   neighbor P peer group G\n"
            "   no neighbor P shutdown\n"
            "   address-family link-state\n"
            "      neighbor G activate\n"
        ),
        (
            "router bgp 65000\n"
            "   neighbor G peer group\n"
            "   neighbor G shutdown\n"
            "   vrf BLUE\n"
            "      neighbor P peer group G\n"
            "      no neighbor P shutdown\n"
            "      address-family link-state\n"
            "         neighbor P activate\n"
        ),
        (
            "router bgp 65000\n"
            "   neighbor G peer group\n"
            "   neighbor G shutdown\n"
            "   vrf BLUE\n"
            "      no neighbor G shutdown\n"
            "      address-family link-state\n"
            "         neighbor G activate\n"
        ),
        CONFIG.replace("   neighbor 198", "   neighbor OTHER shutdown\n   neighbor 198", 1),
        ("router bgp 65000\n   neighbor P shutdown\n   vrf BLUE\n      address-family link-state\n         neighbor P activate\n"),
        (
            "router bgp 65000\n"
            "   vrf RED\n"
            "      shutdown\n"
            "      address-family link-state\n"
            "         neighbor P activate\n"
            "   vrf BLUE\n"
            "      address-family link-state\n"
            "         neighbor P activate\n"
        ),
    ],
)
def test_enabled_activation_survives_unrelated_shutdown_or_override(config: str) -> None:
    """An enabled path or explicit no-shutdown defeats inherited disablement."""
    fact = derive(config)
    assert isinstance(fact, AvailableFact)
    assert fact.value.state is ConfigurationState.CONFIGURED


def test_mixed_disabled_and_enabled_neighbors() -> None:
    """One disabled neighbor cannot hide another configured exposure."""
    config = CONFIG.replace("   neighbor 198", "   neighbor OTHER shutdown\n   neighbor 198", 1).replace(
        "      neighbor 198", "      neighbor OTHER activate\n      neighbor 198"
    )
    fact = derive(config)
    assert isinstance(fact, AvailableFact)
    assert fact.value.scopes == (BgpLinkStatePeeringScope("65000", "default", ("198.51.100.2",)),)


def test_scopes_preserve_configured_instance_and_vrf() -> None:
    """No runtime ASN, router ID, or peer identity is manufactured."""
    config = CONFIG + (
        "   vrf TENANT\n"
        "      address-family link-state\n"
        "         neighbor GROUP activate\n"
        "router bgp 65002\n"
        "   address-family link-state\n"
        "      neighbor 2001:db8::1 activate\n"
    )
    fact = derive(config)
    assert isinstance(fact, AvailableFact)
    assert fact.value.scopes == (
        BgpLinkStatePeeringScope("65000", "default", ("198.51.100.2",)),
        BgpLinkStatePeeringScope("65000", "TENANT", ("GROUP",)),
        BgpLinkStatePeeringScope("65002", "default", ("2001:db8::1",)),
    )


def test_vrf_group_redeclaration_does_not_inherit_unrelated_shutdown() -> None:
    """A local group declaration cannot prove inheritance from a namesake."""
    fact = derive(
        "router bgp 65000\n"
        "   neighbor G peer group\n"
        "   neighbor G shutdown\n"
        "   vrf BLUE\n"
        "      neighbor G peer group\n"
        "      address-family link-state\n"
        "         neighbor G activate\n"
    )
    assert isinstance(fact, AvailableFact)
    assert fact.value.scopes == (BgpLinkStatePeeringScope("65000", "BLUE", ("G",)),)


def test_unresolved_inheritance_cycle_remains_conservatively_enabled() -> None:
    """A cycle does not prove administrative disablement."""
    fact = derive("router bgp 65000\n   neighbor A peer group B\n   neighbor B peer group A\n   address-family link-state\n      neighbor A activate\n")
    assert isinstance(fact, AvailableFact)
    assert fact.value.state is ConfigurationState.CONFIGURED


@pytest.mark.parametrize(
    "config",
    [
        None,
        {},
        "neighbor P activate",
        "router ospf 1\n",
        "   address-family link-state\n",
        "router bgp 65000\n      address-family link-state\n",
        "router bgp 65000\n  address-family link-state\n",
        "router bgp 65000\n\taddress-family link-state\n",
        "router bgp 65000\n   vrf\n",
        "router bgp 65000\n   vrf RED extra\n",
        "router bgp 65000\n   address-family link-state extra\n",
        "router bgp 65000\n   address-family link-state extra more\n",
        "router bgp 65000\n   address-family link-state\n      vrf RED\n",
        "router bgp 65000\n   neighbor P description\n      address-family link-state\n",
        "router bgp 65000\n   address-family ipv4\n      address-family link-state\n",
        "router bgp 65000\n   address-family link-state\n      neighbor P activate extra\n",
        "router bgp 65000\n   address-family link-state\n      neighbor activate\n",
        "router bgp 65000\n   neighbor P shutdown extra\n",
    ],
)
def test_missing_or_malformed_configuration(config: str | dict[str, object] | None) -> None:
    """Malformed boundaries or required settings cannot prove absence."""
    fact = derive(config)
    assert isinstance(fact, UnavailableFact)
    assert fact.problem is (FactProblemKind.MISSING if config is None else FactProblemKind.MALFORMED)
    assert fact.source.name == "show running-config | section router bgp"


@pytest.mark.parametrize(
    ("error", "problem"),
    [("could not run command", FactProblemKind.COLLECTION_FAILED), ("This command is not supported on this hardware platform", FactProblemKind.UNSUPPORTED)],
)
def test_collection_failure_preserves_source(error: str, problem: FactProblemKind) -> None:
    """The single persistent command owns unavailable evidence."""
    command = BgpLinkStatePeeringFact.commands[0].model_copy()
    command.errors = [error]
    fact = BgpLinkStatePeeringFact.derive(OfflineAntaDevice("unit-test"), (command,))
    assert isinstance(fact, UnavailableFact)
    assert fact.problem is problem
    assert fact.source.name == "show running-config | section router bgp"
