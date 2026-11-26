# Copyright (c) 2026 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Native event-handler recognition without executing the configured action."""

from __future__ import annotations

from copy import deepcopy
from typing import Any, cast

import pytest

from anta._advisory.facts.management_queues import ManagementSingleQueueBootFact
from anta._advisory.facts.models import AvailableFact, Fact, FactProblemKind, FeatureState, UnavailableFact
from tests.units.anta_tests.advisories import OfflineAntaDevice
from tests.units.anta_tests.advisories.sa229_data import BOOT_ABSENT, BOOT_ENABLED


def boot(output: object, errors: list[str] | None = None) -> Fact[ManagementSingleQueueBootFact]:
    """Exercise the real command declaration and fact parser."""
    command = ManagementSingleQueueBootFact.commands[0].model_copy()
    command.output = cast("Any", output)
    command.errors = errors or []
    return ManagementSingleQueueBootFact.derive(OfflineAntaDevice("unit-test"), (command,))


def enabled_record() -> dict[str, Any]:
    """Return a private copy of the captured temporary handler."""
    return deepcopy(next(iter(BOOT_ENABLED["eventHandlers"].values())))


@pytest.mark.parametrize(("output", "expected"), [(BOOT_ABSENT, FeatureState.DISABLED), (BOOT_ENABLED, FeatureState.ENABLED)])
def test_captured_boot_control_presence(output: object, expected: FeatureState) -> None:
    fact = boot(output)
    assert isinstance(fact, AvailableFact)
    assert fact.value.state is expected


@pytest.mark.parametrize("name", ["MgmtIntf1Ch", "arbitrary-handler-name"])
def test_handler_name_and_action_counters_do_not_gate_presence(name: str) -> None:
    """Recognize configured control without claiming that it has run successfully."""
    record = enabled_record()
    record.update(actionCount=0, runUponConfig=False, delay=120)
    fact = boot({"eventHandlers": {name: record}})
    assert isinstance(fact, AvailableFact)
    assert fact.value.state is FeatureState.ENABLED


@pytest.mark.parametrize(
    "change",
    [{"disabledManually": True}, {"builtinHandlerDisabled": True}, {"actionKind": "cli"}, {"trigger": {"triggerType": "onCounters"}}, {"action": "echo unrelated"}],
)
def test_disabled_or_unrelated_action_is_not_recognized(change: dict[str, Any]) -> None:
    record = enabled_record()
    record.update(change)
    fact = boot({"eventHandlers": {"test": record}})
    assert isinstance(fact, AvailableFact)
    assert fact.value.state is FeatureState.DISABLED


@pytest.mark.parametrize("field", ["action", "actionKind", "trigger", "disabledManually", "builtinHandlerDisabled"])
def test_missing_matching_handler_input_is_unavailable(field: str) -> None:
    record = enabled_record()
    del record[field]
    fact = boot({"eventHandlers": {"test": record}})
    assert isinstance(fact, UnavailableFact)
    assert fact.problem is FactProblemKind.MISSING
    assert fact.source.name == "show event-handler"


@pytest.mark.parametrize(
    "change",
    [
        {"action": False},
        {"action": "'unterminated"},
        {"actionKind": False},
        {"trigger": []},
        {"trigger": {"triggerType": 1}},
        {"disabledManually": "false"},
        {"builtinHandlerDisabled": "false"},
    ],
)
def test_malformed_handler_data_is_unavailable(change: dict[str, Any]) -> None:
    record = enabled_record()
    record.update(change)
    fact = boot({"eventHandlers": {"test": record}})
    assert isinstance(fact, UnavailableFact)
    assert fact.problem is FactProblemKind.MALFORMED


@pytest.mark.parametrize("reverse", [False, True])
def test_complete_handler_survives_unrelated_bad_entries(reverse: bool) -> None:
    items = [("bad", None), ("valid", enabled_record())]
    fact = boot({"eventHandlers": dict(reversed(items) if reverse else items)})
    assert isinstance(fact, AvailableFact)
    assert fact.value.state is FeatureState.ENABLED


@pytest.mark.parametrize(
    ("output", "problem"),
    [(None, FactProblemKind.MISSING), ([], FactProblemKind.MALFORMED), ({}, FactProblemKind.MISSING), ({"eventHandlers": []}, FactProblemKind.MALFORMED)],
)
def test_missing_or_malformed_output(output: object, problem: FactProblemKind) -> None:
    fact = boot(output)
    assert isinstance(fact, UnavailableFact)
    assert fact.problem is problem


@pytest.mark.parametrize(
    ("errors", "problem"),
    [(["permission denied"], FactProblemKind.COLLECTION_FAILED), (["This command is not supported on this hardware platform"], FactProblemKind.UNSUPPORTED)],
)
def test_command_error_retains_native_source(errors: list[str], problem: FactProblemKind) -> None:
    fact = boot(None, errors)
    assert isinstance(fact, UnavailableFact)
    assert fact.problem is problem
    assert fact.source.name == "show event-handler"


def test_only_native_show_is_declared() -> None:
    """Action text is compared as data and is never declared as a command to execute."""
    assert [command.command for command in ManagementSingleQueueBootFact.required_commands()] == ["show event-handler"]
    assert ManagementSingleQueueBootFact.commands[0].revision == 1


def test_disabled_handler_is_decisive_despite_missing_action() -> None:
    fact = boot({"eventHandlers": {"disabled": {"disabledManually": True}}})
    assert isinstance(fact, AvailableFact)
    assert fact.value.state is FeatureState.DISABLED


def test_extra_command_does_not_match_canonical_action() -> None:
    record = enabled_record()
    record["action"] += "; echo another-command"
    fact = boot({"eventHandlers": {"modified": record}})
    assert isinstance(fact, AvailableFact)
    assert fact.value.state is FeatureState.DISABLED
