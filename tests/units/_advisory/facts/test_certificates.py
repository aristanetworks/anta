# Copyright (c) 2026 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Tests for structured EST automatic CA certificate retrieval settings."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from anta._advisory.facts.certificates import EstCaCertificateAutoUpdateFact
from anta._advisory.facts.models import AvailableFact, FactProblemKind, FeatureState, UnavailableFact
from tests.units.anta_tests.advisories import OfflineAntaDevice

if TYPE_CHECKING:
    from anta.models import AntaCommand


def command_with(output: dict[str, object] | str | list[object] | None) -> AntaCommand:
    """Build the declared revision-one command with a simulated response."""
    return EstCaCertificateAutoUpdateFact.commands[0].model_copy(update={"output": output})


def test_command_contract() -> None:
    """Request the detail JSON command at explicit command-level revision one."""
    (command,) = EstCaCertificateAutoUpdateFact.required_commands()
    assert command.command == "show management security auto-certificate protocol est detail"
    assert command.revision == 1
    assert command.ofmt == "json"


@pytest.mark.parametrize(
    ("output", "state"),
    [
        ({"profiles": {}}, FeatureState.DISABLED),
        ({"profiles": {"MANUAL": {"caCertificates": "disabled", "currentState": "Invalid", "managedProfiles": []}}}, FeatureState.DISABLED),
        ({"profiles": {"EST1": {"caCertificates": "enabled", "currentState": "Valid", "lastCaRetrieved": 0.0, "managedProfiles": []}}}, FeatureState.ENABLED),
        ({"profiles": {"EST1": {"caCertificates": "enabled", "currentState": "Invalid", "managedProfiles": []}}}, FeatureState.ENABLED),
        (
            {
                "profiles": {
                    "EST1": {
                        "currentState": "Valid",
                        "caCertificates": "enabled",
                        "lastCaRetrieved": 0.0,
                        "managedProfiles": [{"certProfile": "CERT1", "certProfileState": "Enrolling"}],
                    },
                    "MANUAL": {
                        "currentState": "Invalid",
                        "caCertificates": "disabled",
                        "lastCaRetrieved": 0.0,
                        "lastError": {"errorMessage": "SSL profile not set", "errorTimestamp": 1794255311.489968},
                        "managedProfiles": [],
                    },
                    "UNUSED": {"currentState": "Valid", "caCertificates": "enabled", "lastCaRetrieved": 0.0, "managedProfiles": []},
                }
            },
            FeatureState.ENABLED,
        ),
    ],
)
def test_captured_ca_retrieval_settings(output: dict[str, object], state: FeatureState) -> None:
    """Use the CA setting rather than profile activity, validity, or last retrieval."""
    fact = EstCaCertificateAutoUpdateFact.derive(OfflineAntaDevice("unit-test"), (command_with(output),))
    assert isinstance(fact, AvailableFact)
    assert fact.value.state is state
    assert fact.source.name == "show management security auto-certificate protocol est detail"


@pytest.mark.parametrize(
    ("output", "problem"),
    [
        (None, FactProblemKind.MISSING),
        ({}, FactProblemKind.MISSING),
        ({"profiles": None}, FactProblemKind.MISSING),
        ("CA certificates: enabled", FactProblemKind.MALFORMED),
        ([], FactProblemKind.MALFORMED),
        ({"profiles": []}, FactProblemKind.MALFORMED),
        ({"profiles": "disabled"}, FactProblemKind.MALFORMED),
        ({"profiles": {"": {"caCertificates": "enabled"}}}, FactProblemKind.MALFORMED),
        ({"profiles": {"EST1": None}}, FactProblemKind.MISSING),
        ({"profiles": {"EST1": {}}}, FactProblemKind.MISSING),
        ({"profiles": {"EST1": {"caCertificates": None}}}, FactProblemKind.MISSING),
        ({"profiles": {"EST1": []}}, FactProblemKind.MALFORMED),
        ({"profiles": {"EST1": {"caCertificates": False}}}, FactProblemKind.MALFORMED),
        ({"profiles": {"EST1": {"caCertificates": ""}}}, FactProblemKind.INVALID),
        ({"profiles": {"EST1": {"caCertificates": "Enabled"}}}, FactProblemKind.INVALID),
        ({"profiles": {"EST1": {"caCertificates": "automatic"}}}, FactProblemKind.INVALID),
    ],
)
def test_incomplete_or_invalid_evidence(output: dict[str, object] | str | list[object] | None, problem: FactProblemKind) -> None:
    """Never default malformed, missing, or unknown CA settings to disabled."""
    fact = EstCaCertificateAutoUpdateFact.derive(OfflineAntaDevice("unit-test"), (command_with(output),))
    assert isinstance(fact, UnavailableFact)
    assert fact.problem is problem


@pytest.mark.parametrize("reverse", [False, True])
@pytest.mark.parametrize("bad_entry", [None, {}, [], {"caCertificates": False}, {"caCertificates": "unknown"}])
def test_enabled_witness_survives_unrelated_problem(bad_entry: object, reverse: bool) -> None:
    """An enabled protocol is not erased by another incomplete protocol in either order."""
    entries = [("ENABLED", {"caCertificates": "enabled"}), ("INCOMPLETE", bad_entry)]
    if reverse:
        entries.reverse()
    fact = EstCaCertificateAutoUpdateFact.derive(OfflineAntaDevice("unit-test"), (command_with({"profiles": dict(entries)}),))
    assert isinstance(fact, AvailableFact)
    assert fact.value.state is FeatureState.ENABLED


@pytest.mark.parametrize("reverse", [False, True])
def test_disabled_and_incomplete_cannot_prove_absence(reverse: bool) -> None:
    """Every protocol needs a reliable negative setting when there is no positive."""
    entries = [("DISABLED", {"caCertificates": "disabled"}), ("INCOMPLETE", {})]
    if reverse:
        entries.reverse()
    fact = EstCaCertificateAutoUpdateFact.derive(OfflineAntaDevice("unit-test"), (command_with({"profiles": dict(entries)}),))
    assert isinstance(fact, UnavailableFact)
    assert fact.problem is FactProblemKind.MISSING


@pytest.mark.parametrize("reverse", [False, True])
def test_enabled_named_protocol_survives_unrelated_invalid_name(reverse: bool) -> None:
    """A malformed sibling identity cannot erase a trustworthy named witness."""
    entries = [("ENABLED", {"caCertificates": "enabled"}), ("", {})]
    if reverse:
        entries.reverse()
    fact = EstCaCertificateAutoUpdateFact.derive(OfflineAntaDevice("unit-test"), (command_with({"profiles": dict(entries)}),))
    assert isinstance(fact, AvailableFact)
    assert fact.value.state is FeatureState.ENABLED


@pytest.mark.parametrize(
    ("errors", "problem"),
    [
        (["could not run command"], FactProblemKind.COLLECTION_FAILED),
        (["This command is not supported on this hardware platform"], FactProblemKind.UNSUPPORTED),
        (["This command is not supported on this hardware platform", "could not run command"], FactProblemKind.COLLECTION_FAILED),
    ],
)
def test_command_failures(errors: list[str], problem: FactProblemKind) -> None:
    """Failed collection is unavailable evidence even beside a stale enabled payload."""
    command = command_with({"profiles": {"EST1": {"caCertificates": "enabled"}}})
    command.errors = errors
    fact = EstCaCertificateAutoUpdateFact.derive(OfflineAntaDevice("unit-test"), (command,))
    assert isinstance(fact, UnavailableFact)
    assert fact.problem is problem


def test_missing_command_is_collection_failure() -> None:
    """A missing response cannot be interpreted as an empty protocol inventory."""
    fact = EstCaCertificateAutoUpdateFact.derive(OfflineAntaDevice("unit-test"))
    assert isinstance(fact, UnavailableFact)
    assert fact.problem is FactProblemKind.COLLECTION_FAILED
