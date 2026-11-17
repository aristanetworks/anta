# Copyright (c) 2026 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Tests for persistent adaptive virtual topology role observations."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from anta._advisory.facts.avt import AvtRole, PathfinderRoleFact
from anta._advisory.facts.models import AvailableFact, FactProblemKind, FeatureState, UnavailableFact
from tests.units.anta_tests.advisories import OfflineAntaDevice

if TYPE_CHECKING:
    from anta.models import AntaCommand


def role_command(output: dict[str, object] | str | None) -> AntaCommand:
    """Copy the role command with one test response."""
    command = PathfinderRoleFact.commands[0].model_copy()
    command.output = output
    return command


@pytest.mark.parametrize(
    ("role", "state"),
    [
        ("pathfinder", FeatureState.ENABLED),
        ("edge", FeatureState.DISABLED),
        ("zone transit", FeatureState.DISABLED),
        ("region transit", FeatureState.DISABLED),
        ("unknown", FeatureState.DISABLED),
    ],
)
def test_role_without_paths_or_router_id(role: str, state: FeatureState) -> None:
    """Preserve the captured top-level role even when no paths exist.

    CloudEOS 4.35.0F returns this shape for every listed role, including
    Pathfinder without any BGP process and with down configured peers.
    """
    command = role_command(
        {
            "routerId": "0.0.0.0",  # noqa: S104
            "role": role,
            "regionName": "",
            "regionId": 0,
            "zoneName": "",
            "zoneId": 0,
            "siteName": "",
            "siteId": 0,
            "vrfs": {},
        }
    )
    fact = PathfinderRoleFact.derive(OfflineAntaDevice("unit-test"), (command,))
    assert isinstance(fact, AvailableFact)
    assert fact.value.role == AvtRole(role)
    assert fact.value.state is state
    assert fact.source.name == "show adaptive-virtual-topology path"


@pytest.mark.parametrize(
    ("output", "problem"),
    [
        ({}, FactProblemKind.MISSING),
        ({"vrfs": {}}, FactProblemKind.MISSING),
        ({"role": None}, FactProblemKind.MISSING),
        ({"role": []}, FactProblemKind.MALFORMED),
        ({"role": True}, FactProblemKind.MALFORMED),
        ({"role": ""}, FactProblemKind.INVALID),
        ({"role": "new-role"}, FactProblemKind.INVALID),
        (None, FactProblemKind.MISSING),
        ("Role: pathfinder", FactProblemKind.MALFORMED),
    ],
)
def test_invalid_or_missing_role(output: dict[str, object] | str | None, problem: FactProblemKind) -> None:
    """Never replace absent or unrecognized role evidence with valid unknown."""
    fact = PathfinderRoleFact.derive(OfflineAntaDevice("unit-test"), (role_command(output),))
    assert isinstance(fact, UnavailableFact)
    assert fact.problem is problem


@pytest.mark.parametrize(
    ("errors", "problem"),
    [
        (["could not run command"], FactProblemKind.COLLECTION_FAILED),
        (["% Adaptive virtual topology is not configured at line 1"], FactProblemKind.COLLECTION_FAILED),
        (["This command is not supported on this hardware platform"], FactProblemKind.UNSUPPORTED),
        (["This command is not supported on this hardware platform", "could not run command"], FactProblemKind.COLLECTION_FAILED),
    ],
)
def test_role_collection_errors(errors: list[str], problem: FactProblemKind) -> None:
    """Keep unconfigured-agent and unsupported responses unavailable."""
    command = role_command(None)
    command.errors = errors
    fact = PathfinderRoleFact.derive(OfflineAntaDevice("unit-test"), (command,))
    assert isinstance(fact, UnavailableFact)
    assert fact.problem is problem
    assert fact.source.name == "show adaptive-virtual-topology path"
