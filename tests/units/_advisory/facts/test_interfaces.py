# Copyright (c) 2026 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Persistent speed parser tests using physical default and source syntax examples."""

from __future__ import annotations

from typing import Any, cast

import pytest

from anta._advisory.facts.interfaces import InterfaceSpeed, InterfaceSpeedFact
from anta._advisory.facts.models import AvailableFact, ConfigurationFact, Fact, FactProblemKind, UnavailableFact
from tests.units.anta_tests.advisories import OfflineAntaDevice


def parse(output: object) -> Fact[InterfaceSpeedFact]:
    """Populate a declared command and exercise the real derivation contract."""
    command = InterfaceSpeedFact.commands[0].model_copy()
    command.output = cast("Any", output)
    return InterfaceSpeedFact.derive(OfflineAntaDevice("unit-test"), (command,))


@pytest.mark.parametrize(
    "speed",
    [
        "no speed",
        "speed auto",
        "speed auto 1g",
        "speed auto 2.5g",
        "speed auto 5g",
        "speed auto 10g",
        "speed auto 100full",
        "speed forced 10000full",
        "speed forced 1000full",
        "speed 1g",
        "speed 10g",
        "speed 100g-4",
    ],
)
def test_literal_speed(speed: str) -> None:
    """Preserve exact configured constraints, distinguishing bounded auto syntax."""
    fact = parse(f"interface Ethernet3/1\n   {speed}\n   no shutdown\n")
    assert isinstance(fact, AvailableFact)
    assert fact.value.interfaces == (InterfaceSpeed("Ethernet3/1", speed),)
    assert not isinstance(fact.value, ConfigurationFact)
    assert not fact.value.problems
    assert fact.source.name == "show running-config sanitized all section ^interface"


def test_scoped_hierarchy_and_powered_off_ports() -> None:
    """Retain slot correlation, ignoring other interface types and nested queues."""
    # Physical full-default capture includes powered-off slots 4/6 as well as active 3/5.
    fact = parse("""interface defaults
   mtu 1500
interface Ethernet3/1
   no speed
   !
   tx-queue 0
      speed invalid-nested-token
interface Ethernet4/1
   speed auto 1g
interface Ethernet5/1
   speed auto
interface Ethernet6/1
   no speed
interface Ethernet3/1.100
   encapsulation dot1q vlan 100
interface Management1/1
   no speed
interface Port-Channel10
   description no speed
""")
    assert isinstance(fact, AvailableFact)
    assert fact.value.interfaces == (
        InterfaceSpeed("Ethernet3/1", "no speed"),
        InterfaceSpeed("Ethernet4/1", "speed auto 1g"),
        InterfaceSpeed("Ethernet5/1", "speed auto"),
        InterfaceSpeed("Ethernet6/1", "no speed"),
    )


@pytest.mark.parametrize(
    ("output", "problem"),
    [
        ({}, FactProblemKind.MALFORMED),
        (None, FactProblemKind.MALFORMED),
        ("", FactProblemKind.MISSING),
        ("interface Management1\n   no speed", FactProblemKind.MISSING),
        ("interface Ethernetbad\n   no speed\ninterface Ethernet3/1\n   speed auto 1g", FactProblemKind.MALFORMED),
        ("interface Ethernet3/1\n   speed auto\ninterface Ethernet3/1\n   no speed", FactProblemKind.MALFORMED),
    ],
)
def test_invalid_or_incomplete_output(output: object, problem: FactProblemKind) -> None:
    """Incomplete full-default data cannot establish constrained speed."""
    fact = parse(output)
    assert isinstance(fact, UnavailableFact)
    assert fact.problem is problem


def test_contradictory_speed() -> None:
    """Retain both disagreeing speed observations for an interface."""
    fact = parse("interface Ethernet3/1\n   no speed\n   speed auto 1g")
    assert isinstance(fact, AvailableFact)
    assert not fact.value.interfaces
    (problem,) = fact.value.problems
    assert problem.slot == "3"
    assert problem.fact.problem is FactProblemKind.CONTRADICTORY
    assert tuple(item.interfaces[0].configuration for item in problem.fact.observations) == ("no speed", "speed auto 1g")


def test_collection_failures() -> None:
    """Required command failures and unsupported platforms remain unavailable."""
    device = OfflineAntaDevice("unit-test")
    fact = InterfaceSpeedFact.derive(device)
    assert isinstance(fact, UnavailableFact)
    assert fact.problem is FactProblemKind.COLLECTION_FAILED
    for error, problem in [("not supported on this hardware platform", FactProblemKind.UNSUPPORTED), ("timed out", FactProblemKind.COLLECTION_FAILED)]:
        command = InterfaceSpeedFact.commands[0].model_copy()
        command.errors = [error]
        fact = InterfaceSpeedFact.derive(device, (command,))
        assert isinstance(fact, UnavailableFact)
        assert fact.problem is problem


@pytest.mark.parametrize(
    ("lines", "problem"),
    [
        ("description no speed", FactProblemKind.MISSING),
        ("default speed", FactProblemKind.MISSING),
        ("speed auto invalid", FactProblemKind.MALFORMED),
        ("speed invalid", FactProblemKind.MALFORMED),
        ("speed 100g-", FactProblemKind.MALFORMED),
        ("speed 100g-0", FactProblemKind.MALFORMED),
        ("speed 100g-abc", FactProblemKind.MALFORMED),
        ("speed 100g-4garbage", FactProblemKind.MALFORMED),
        ("no speed invalid", FactProblemKind.MALFORMED),
        ("no speed\n   no speed", FactProblemKind.MALFORMED),
    ],
)
def test_interface_errors_keep_their_slot(lines: str, problem: FactProblemKind) -> None:
    """A known interface scope retains uncertainty without losing other slots."""
    fact = parse(f"interface Ethernet3/1\n   {lines}\ninterface Ethernet5/1\n   no speed\n")
    assert isinstance(fact, AvailableFact)
    assert fact.value.interfaces == (InterfaceSpeed("Ethernet5/1", "no speed"),)
    (error,) = fact.value.problems
    assert error.slot == "3"
    assert error.fact.problem is problem
    assert error.fact.source == fact.source


@pytest.mark.parametrize("reverse", [False, True])
def test_slot_summary_is_bounded_and_preserves_exposure(reverse: bool) -> None:
    """Hundreds of ports retain distinct settings and one problem per slot."""
    sections = [f"interface Ethernet3/{port}\n   speed auto 1g\n" for port in range(1, 401)]
    sections += ["interface Ethernet3/401\n   no speed\n"]
    sections += [f"interface Ethernet3/{port}\n   description missing speed\n" for port in range(402, 501)]
    fact = parse("".join(reversed(sections) if reverse else sections))
    assert isinstance(fact, AvailableFact)
    assert {item.configuration for item in fact.value.interfaces} == {"speed auto 1g", "no speed"}
    assert len(fact.value.interfaces) == 2
    assert InterfaceSpeed("Ethernet3/401", "no speed") in fact.value.interfaces
    assert len(fact.value.problems) == 1
    assert fact.value.problems[0].slot == "3"
    assert fact.value.problems[0].fact.problem is FactProblemKind.MISSING


def test_distinct_settings_are_not_classified_or_discarded() -> None:
    """Preserve different explicit speeds and incomplete evidence without a safe state."""
    fact = parse("""interface Ethernet3/1
   speed auto 1g
interface Ethernet3/2
   speed forced 10000full
interface Ethernet3/3
   speed auto
interface Ethernet3/4
   description missing speed
""")
    assert isinstance(fact, AvailableFact)
    assert not isinstance(fact.value, ConfigurationFact)
    assert not hasattr(fact.value, "state")
    assert fact.value.interfaces == (
        InterfaceSpeed("Ethernet3/1", "speed auto 1g"),
        InterfaceSpeed("Ethernet3/2", "speed forced 10000full"),
        InterfaceSpeed("Ethernet3/3", "speed auto"),
    )
    assert fact.value.problems[0].fact.problem is FactProblemKind.MISSING


@pytest.mark.parametrize("speed", ["no speed", "speed auto", "speed auto 1g", "speed 100g-4"])
def test_phy_negotiation_setting_is_not_interface_speed(speed: str) -> None:
    """Ignore the full-default PHY negotiation line emitted alongside speed settings."""
    fact = parse(f"interface Ethernet3/1\n   no phy media base-t negotiation unsupported speed\n   {speed}\n")
    assert isinstance(fact, AvailableFact)
    assert fact.value.interfaces == (InterfaceSpeed("Ethernet3/1", speed),)
    assert not fact.value.problems
