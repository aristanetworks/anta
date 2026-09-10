# Copyright (c) 2026 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Unit tests for facts normalized from EOS management-access state."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from anta._advisory.facts.management_access import PasswordManagementServiceFact
from anta._advisory.facts.models import AvailableFact, FactProblemKind, FeatureState, UnavailableFact
from tests.units.anta_tests.advisories import OfflineAntaDevice

if TYPE_CHECKING:
    from anta.models import AntaCommand


def commands(ssh: str, telnet: str) -> tuple[AntaCommand, ...]:
    """Return populated commands for the composite management-service fact."""
    values: list[AntaCommand] = []
    for declared, output in zip(PasswordManagementServiceFact.commands, (ssh, telnet), strict=True):
        command = declared.model_copy()
        command.output = output
        values.append(command)
    return tuple(values)


def test_password_management_service_ignores_transient_operational_vrf_state() -> None:
    """Keep configured VRF exposure identical while its operational state is up or down."""
    assert tuple(command.command for command in PasswordManagementServiceFact.commands) == (
        "show running-config section management ssh",
        "show running-config section management telnet",
    )

    fact = PasswordManagementServiceFact.derive(
        OfflineAntaDevice("unit-test"),
        commands("management ssh\n   vrf MGMT", ""),
    )

    assert isinstance(fact, AvailableFact)
    assert fact.value.state is FeatureState.ENABLED


@pytest.mark.parametrize(
    ("ssh", "telnet", "state"),
    [
        ("", "", FeatureState.ENABLED),
        ("management ssh\n   authentication protocol public-key", "", FeatureState.DISABLED),
        ("management ssh\n   shutdown", "", FeatureState.DISABLED),
        ("management ssh\n   vrf default\n      shutdown", "", FeatureState.DISABLED),
        (
            "management ssh\n   authentication protocol public-key",
            "management telnet\n   vrf MGMT\n      no shutdown",
            FeatureState.ENABLED,
        ),
        (
            "management ssh\n   authentication protocol public-key",
            "management telnet\n   no shutdown\n   vrf MGMT\n      shutdown",
            FeatureState.ENABLED,
        ),
    ],
)
def test_password_management_service_states(ssh: str, telnet: str, state: FeatureState) -> None:
    """Normalize implicit defaults, protocols, shutdown, VRF allowlists, and Telnet."""
    fact = PasswordManagementServiceFact.derive(
        OfflineAntaDevice("unit-test"),
        commands(ssh, telnet),
    )

    assert isinstance(fact, AvailableFact)
    assert fact.value.state is state
    assert fact.source.name == ", ".join(command.command for command in PasswordManagementServiceFact.commands)


@pytest.mark.parametrize(
    ("ssh", "telnet", "source_index"),
    [
        ("management ssh\n   no shutdown\n   shutdown", "", 0),
        ("", "management telnet\n   no shutdown\n   shutdown", 1),
    ],
)
def test_password_management_service_rejects_incomplete_state(
    ssh: str,
    telnet: str,
    source_index: int,
) -> None:
    """Reject malformed management-service configuration."""
    fact = PasswordManagementServiceFact.derive(OfflineAntaDevice("unit-test"), commands(ssh, telnet))

    assert isinstance(fact, UnavailableFact)
    assert fact.problem is FactProblemKind.MALFORMED
    assert fact.source.name == PasswordManagementServiceFact.commands[source_index].command


def test_password_management_service_unsupported() -> None:
    """Keep unsupported management-access input unavailable."""
    values = list(commands("", ""))
    values[0].output = None
    values[0].errors = ["This command is not supported on this hardware platform"]

    fact = PasswordManagementServiceFact.derive(OfflineAntaDevice("unit-test"), tuple(values))

    assert isinstance(fact, UnavailableFact)
    assert fact.problem is FactProblemKind.UNSUPPORTED
    assert fact.source.name == PasswordManagementServiceFact.commands[0].command
