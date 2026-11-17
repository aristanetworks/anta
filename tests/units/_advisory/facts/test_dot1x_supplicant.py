# Copyright (c) 2026 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Configured supplicant inventory, independently of authentication progress."""

from __future__ import annotations

import pytest

from anta._advisory.facts.dot1x import Dot1xSupplicantInterface, Dot1xSupplicantInterfacesFact
from anta._advisory.facts.models import AvailableFact, Fact, FactProblemKind, UnavailableFact
from anta._advisory.optional_commands import OptionalAntaCommand
from tests.units.anta_tests.advisories import OfflineAntaDevice


def parse(output: object, *, errors: list[str] | None = None) -> Fact[Dot1xSupplicantInterfacesFact]:
    """Exercise the actual command and derivation contract."""
    command = Dot1xSupplicantInterfacesFact.commands[0].model_copy(update={"output": output, "errors": errors or []})
    return Dot1xSupplicantInterfacesFact.derive(OfflineAntaDevice("unit-test"), (command,))


def test_configured_unused_supplicant_is_retained_without_session_details() -> None:
    """The captured unused role with no SSL profile is still configured."""
    fact = parse({"interfaces": {"Ethernet3": {"identity": "DO-NOT-RETAIN", "eapMethod": "tls", "sslProfileName": "", "status": "unused"}}})
    assert isinstance(fact, AvailableFact)
    assert fact.value.interfaces == (Dot1xSupplicantInterface("Ethernet3"),)
    assert not fact.value.problems
    assert "DO-NOT-RETAIN" not in repr(fact)
    command = Dot1xSupplicantInterfacesFact.commands[0]
    assert isinstance(command, OptionalAntaCommand)
    assert (command.command, command.revision, command.defer_errors) == ("show dot1x supplicant", 1, True)


@pytest.mark.parametrize("reverse", [False, True])
@pytest.mark.parametrize("name", ["Ethernet2", ""])
def test_malformed_sibling_does_not_erase_valid_supplicant(reverse: bool, name: str) -> None:
    """Both traversal orders preserve a usable witness and its sibling problem."""
    entries = [("Ethernet3", {"status": "unused"}), (name, None)]
    fact = parse({"interfaces": dict(reversed(entries) if reverse else entries)})
    assert isinstance(fact, AvailableFact)
    assert fact.value.interfaces == (Dot1xSupplicantInterface("Ethernet3"),)
    assert len(fact.value.problems) == 1
    assert fact.value.problems[0].interface == (name or None)


def test_empty_inventory_proves_only_supplicant_absence() -> None:
    """An explicit empty map is a valid observation for this role."""
    fact = parse({"interfaces": {}})
    assert isinstance(fact, AvailableFact)
    assert not fact.value.interfaces
    assert not fact.value.problems


@pytest.mark.parametrize("output", [None, {}, [], {"interfaces": None}, {"interfaces": []}])
def test_required_inventory_shape_is_not_inferred_from_missing_data(output: object) -> None:
    """A missing inventory cannot establish safe role absence."""
    fact = parse(output)
    assert isinstance(fact, UnavailableFact)


@pytest.mark.parametrize("error", ["transport failure", "not supported on this hardware platform"])
def test_command_failures_are_not_role_absence(error: str) -> None:
    """Collection failures and unsupported commands retain the exact source."""
    fact = parse({}, errors=[error])
    assert isinstance(fact, UnavailableFact)
    assert fact.problem in {FactProblemKind.COLLECTION_FAILED, FactProblemKind.UNSUPPORTED}
    assert fact.source.name == "show dot1x supplicant"
