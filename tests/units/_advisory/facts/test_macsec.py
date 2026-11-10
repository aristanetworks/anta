# Copyright (c) 2026 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Revision-one MACsec profile identities, defaults, and scoped parsing failures."""

from __future__ import annotations

import pytest

from anta._advisory.facts.macsec import MacsecProfile, MacsecProfilesFact
from anta._advisory.facts.models import AvailableFact, Fact, FactProblemKind, UnavailableFact
from anta._advisory.optional_commands import OptionalAntaCommand
from tests.units.anta_tests.advisories import OfflineAntaDevice


def parse(output: object, *, errors: list[str] | None = None) -> Fact[MacsecProfilesFact]:
    """Exercise the real declared command and derivation path."""
    command = MacsecProfilesFact.required_commands()[0].model_copy(update={"output": output, "errors": errors or []})
    return MacsecProfilesFact.derive(OfflineAntaDevice("unit-test"), (command,))


def test_command_contract() -> None:
    """Use the singular profile command and explicit revision one."""
    (command,) = MacsecProfilesFact.required_commands()
    assert isinstance(command, OptionalAntaCommand)
    assert (command.command, command.ofmt, command.revision, command.defer_errors) == ("show mac security profile", "json", 1, True)


def test_profile_identity_keys_and_binding_are_neutral() -> None:
    """Keep identical names under separate sources without copying cryptographic data."""
    fact = parse(
        {
            "sources": {
                "cli": {"profiles": {"PROFILE": {"primaryKeySource": "dot1x", "interfaces": ["Ethernet3"], "cakSha256Hash": "DO-NOT-RETAIN"}}},
                "dmf": {"profiles": {"PROFILE": {"primaryKeySource": "cli", "interfaces": ["Ethernet2"]}}},
            }
        }
    )
    assert isinstance(fact, AvailableFact)
    assert fact.value.profiles == (MacsecProfile("cli", "PROFILE", "dot1x", ("Ethernet3",)), MacsecProfile("dmf", "PROFILE", "cli", ("Ethernet2",)))
    assert "DO-NOT-RETAIN" not in repr(fact)
    assert "cakSha256Hash" not in repr(fact)
    assert not fact.value.problems
    assert fact.source.name == "show mac security profile"


@pytest.mark.parametrize("interfaces", [[], ["Ethernet3"]])
def test_captured_default_profile_omits_key_source(interfaces: list[str]) -> None:
    """Missing primaryKeySource is the captured unconfigured-default shape, not null."""
    fact = parse({"sources": {"cli": {"profiles": {"DEFAULT": {"interfaces": interfaces}}}}})
    assert isinstance(fact, AvailableFact)
    assert fact.value.profiles == (MacsecProfile("cli", "DEFAULT", None, tuple(interfaces)),)
    assert not fact.value.problems


@pytest.mark.parametrize("sources", [{}, {"cli": {"profiles": {}}, "dmf": {"profiles": {}}}])
def test_empty_profiles(sources: dict[str, object]) -> None:
    """An explicit complete empty profile inventory is usable absence evidence."""
    fact = parse({"sources": sources})
    assert isinstance(fact, AvailableFact)
    assert fact.value.profiles == fact.value.problems == ()


@pytest.mark.parametrize(
    ("output", "problem"),
    [
        (None, FactProblemKind.MISSING),
        ({}, FactProblemKind.MISSING),
        ([], FactProblemKind.MALFORMED),
        ({"sources": None}, FactProblemKind.MALFORMED),
        ({"sources": []}, FactProblemKind.MALFORMED),
    ],
)
def test_broken_top_level_identity(output: object, problem: FactProblemKind) -> None:
    """A malformed scope identity invalidates the command-level observation."""
    fact = parse(output)
    assert isinstance(fact, UnavailableFact)
    assert fact.problem is problem


@pytest.mark.parametrize("scope", ["source", "profile"])
@pytest.mark.parametrize("reverse", [False, True])
def test_invalid_sibling_identity_preserves_valid_profile(scope: str, reverse: bool) -> None:
    """Invalid sibling identifiers retain unknown-scope problems beside valid evidence."""
    valid = {"VALID": {"primaryKeySource": "dot1x", "interfaces": ["Ethernet3"]}}
    if scope == "source":
        entries = [("cli", {"profiles": valid}), ("", {"profiles": {}})]
        sources = dict(reversed(entries) if reverse else entries)
    else:
        entries = [("VALID", valid["VALID"]), ("", {"interfaces": []})]
        sources = {"cli": {"profiles": dict(reversed(entries) if reverse else entries)}}
    fact = parse({"sources": sources})
    assert isinstance(fact, AvailableFact)
    assert fact.value.profiles == (MacsecProfile("cli", "VALID", "dot1x", ("Ethernet3",)),)
    assert len(fact.value.problems) == 1
    assert fact.value.problems[0].interfaces is None
    assert fact.value.problems[0].fact.problem is FactProblemKind.MALFORMED


@pytest.mark.parametrize("reverse", [False, True])
@pytest.mark.parametrize(
    ("broken", "interfaces", "known", "problem"),
    [
        ({"primaryKeySource": None, "interfaces": ["Ethernet2"]}, ("Ethernet2",), False, FactProblemKind.MALFORMED),
        ({"primaryKeySource": 1, "interfaces": ["Ethernet2"]}, ("Ethernet2",), False, FactProblemKind.MALFORMED),
        ({"primaryKeySource": "", "interfaces": ["Ethernet2"]}, ("Ethernet2",), False, FactProblemKind.MALFORMED),
        ({"primaryKeySource": "dot1x"}, None, True, FactProblemKind.MISSING),
        ({"primaryKeySource": "cli", "interfaces": None}, None, True, FactProblemKind.MALFORMED),
        ({"primaryKeySource": "dot1x", "interfaces": ["Ethernet2", "Ethernet2"]}, None, True, FactProblemKind.MALFORMED),
    ],
)
def test_profile_problem_does_not_discard_other_profiles(
    reverse: bool, broken: object, interfaces: tuple[str, ...] | None, known: bool, problem: FactProblemKind
) -> None:
    """Retain both a valid binding and the other profile's exact known scope."""
    entries = [("VALID", {"primaryKeySource": "dot1x", "interfaces": ["Ethernet3"]}), ("BROKEN", broken)]
    fact = parse({"sources": {"cli": {"profiles": dict(reversed(entries) if reverse else entries)}}})
    assert isinstance(fact, AvailableFact)
    assert fact.value.profiles == (MacsecProfile("cli", "VALID", "dot1x", ("Ethernet3",)),)
    assert len(fact.value.problems) == 1
    issue = fact.value.problems[0]
    assert (issue.source, issue.name, issue.interfaces, issue.key_source_known, issue.fact.problem) == ("cli", "BROKEN", interfaces, known, problem)


@pytest.mark.parametrize("source", [None, {}, {"profiles": None}, {"profiles": []}])
def test_missing_source_inventory_keeps_other_source(source: object) -> None:
    """A source-level problem retains its source identity and unknown interface scope."""
    fact = parse({"sources": {"cli": {"profiles": {"VALID": {"primaryKeySource": "dot1x", "interfaces": ["Ethernet3"]}}}, "dmf": source}})
    assert isinstance(fact, AvailableFact)
    assert fact.value.profiles[0].name == "VALID"
    assert fact.value.problems[0].source == "dmf"
    assert fact.value.problems[0].interfaces is None


def test_failed_collection_and_unsupported_are_not_empty_profiles() -> None:
    """Command failures cannot prove that the device lacks configured profiles."""
    failed = parse({"sources": {}}, errors=["transport failure"])
    assert isinstance(failed, UnavailableFact)
    assert failed.problem is FactProblemKind.COLLECTION_FAILED
    command = MacsecProfilesFact.required_commands()[0].model_copy(update={"errors": ["not supported on this hardware platform"]})
    unsupported = MacsecProfilesFact.derive(OfflineAntaDevice("unit-test"), (command,))
    assert isinstance(unsupported, UnavailableFact)
    assert unsupported.problem is FactProblemKind.UNSUPPORTED


@pytest.mark.parametrize("reverse", [False, True])
@pytest.mark.parametrize("invalid", [None, 3, "", " Ethernet2", {}, []])
@pytest.mark.parametrize("key_source", ["dot1x", "cli", None])
def test_valid_binding_survives_malformed_entry(reverse: bool, invalid: object, key_source: str | None) -> None:
    """A bad sibling name does not erase a known profile binding or its coverage error."""
    entries = ["Ethernet3", invalid]
    profile: dict[str, object] = {"interfaces": list(reversed(entries)) if reverse else entries}
    if key_source is not None:
        profile["primaryKeySource"] = key_source
    fact = parse({"sources": {"cli": {"profiles": {"PROFILE": profile}}}})
    assert isinstance(fact, AvailableFact)
    assert fact.value.profiles == (MacsecProfile("cli", "PROFILE", key_source, ("Ethernet3",)),)
    assert len(fact.value.problems) == 1
    issue = fact.value.problems[0]
    assert (issue.source, issue.name, issue.interfaces, issue.key_source_known, issue.key_source) == ("cli", "PROFILE", None, True, key_source)
    assert issue.fact.problem is FactProblemKind.MALFORMED
    assert issue.fact.source.name == "show mac security profile"


@pytest.mark.parametrize("reverse", [False, True])
def test_unknown_key_source_retains_known_and_unknown_binding_problems(reverse: bool) -> None:
    """Malformed key source cannot establish a binding, and known scope remains explicit."""
    entries = ["Ethernet3", None]
    profile = {"primaryKeySource": None, "interfaces": list(reversed(entries)) if reverse else entries}
    fact = parse({"sources": {"cli": {"profiles": {"PROFILE": profile}}}})
    assert isinstance(fact, AvailableFact)
    assert not fact.value.profiles
    assert tuple(issue.interfaces for issue in fact.value.problems) == (("Ethernet3",), None)
    assert all(not issue.key_source_known and issue.fact.problem is FactProblemKind.MALFORMED for issue in fact.value.problems)
