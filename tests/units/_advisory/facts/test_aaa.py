# Copyright (c) 2026 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Unit tests for facts normalized from EOS AAA output."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from anta._advisory.facts.aaa import LevelZeroCommandAuthorizationFact, LoginAuthenticationFact
from anta._advisory.facts.models import AvailableFact, FactProblemKind, FeatureState, MitigationState, UnavailableFact
from tests.units.anta_tests.advisories import OfflineAntaDevice

if TYPE_CHECKING:
    from anta.models import AntaCommand


def aaa_command(output: str) -> AntaCommand:
    """Return the narrow AAA command populated with text output."""
    command = LevelZeroCommandAuthorizationFact.commands[0].model_copy()
    command.output = output
    return command


@pytest.mark.parametrize(
    ("output", "state"),
    [
        ("", MitigationState.INEFFECTIVE),
        ("aaa authorization commands 0 default local none", MitigationState.INEFFECTIVE),
        ("aaa authorization commands 0 default local", MitigationState.EFFECTIVE),
        ("aaa authorization commands 0-2 default group tacacs+", MitigationState.EFFECTIVE),
        ("aaa authorization commands all default local group tacacs+", MitigationState.EFFECTIVE),
        ("aaa authorization commands 1-15 default none", MitigationState.INEFFECTIVE),
    ],
)
def test_level_zero_command_authorization_states(output: str, state: MitigationState) -> None:
    """Normalize implicit, explicit unsafe, safe, ranged, and all-level method lists."""
    fact = LevelZeroCommandAuthorizationFact.derive(OfflineAntaDevice("unit-test"), (aaa_command(output),))

    assert isinstance(fact, AvailableFact)
    assert fact.value.state is state


def test_level_zero_command_authorization_rejects_malformed_expression() -> None:
    """Reject an invalid level expression in an applicable command."""
    fact = LevelZeroCommandAuthorizationFact.derive(
        OfflineAntaDevice("unit-test"),
        (aaa_command("aaa authorization commands 2-0 default local"),),
    )

    assert isinstance(fact, UnavailableFact)
    assert fact.problem is FactProblemKind.MALFORMED


def test_level_zero_command_authorization_unsupported() -> None:
    """Keep unsupported AAA configuration unavailable."""
    command = aaa_command("")
    command.output = None
    command.errors = ["This command is not supported on this hardware platform"]

    fact = LevelZeroCommandAuthorizationFact.derive(OfflineAntaDevice("unit-test"), (command,))

    assert isinstance(fact, UnavailableFact)
    assert fact.problem is FactProblemKind.UNSUPPORTED


@pytest.mark.parametrize(
    ("methods", "state"),
    [
        (["local"], FeatureState.ENABLED),
        (["group tacacs+", "local"], FeatureState.ENABLED),
        (["none"], FeatureState.DISABLED),
        (["none", "local"], FeatureState.DISABLED),
    ],
)
def test_login_authentication_states(methods: list[str], state: FeatureState) -> None:
    """Normalize enabled and explicitly disabled default login method lists."""
    command = LoginAuthenticationFact.commands[0].model_copy()
    command.output = {"loginAuthenMethods": {"default": {"methods": methods}}}

    fact = LoginAuthenticationFact.derive(OfflineAntaDevice("unit-test"), (command,))

    assert isinstance(fact, AvailableFact)
    assert fact.value.state is state


def test_login_authentication_rejects_missing_default_list() -> None:
    """Reject missing default login methods."""
    command = LoginAuthenticationFact.commands[0].model_copy()
    command.output = {"loginAuthenMethods": {}}

    fact = LoginAuthenticationFact.derive(OfflineAntaDevice("unit-test"), (command,))

    assert isinstance(fact, UnavailableFact)
    assert fact.problem is FactProblemKind.MISSING


def test_login_authentication_unsupported() -> None:
    """Keep unsupported AAA method output unavailable."""
    command = LoginAuthenticationFact.commands[0].model_copy()
    command.output = None
    command.errors = ["This command is not supported on this hardware platform"]

    fact = LoginAuthenticationFact.derive(OfflineAntaDevice("unit-test"), (command,))

    assert isinstance(fact, UnavailableFact)
    assert fact.problem is FactProblemKind.UNSUPPORTED
