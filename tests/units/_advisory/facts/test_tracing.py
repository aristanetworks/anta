# Copyright (c) 2026 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Unit tests for facts normalized from EOS agent tracing."""

from __future__ import annotations

from typing import TYPE_CHECKING, TypeVar

import pytest

from anta._advisory.facts.models import AvailableFact, FactProblemKind, FeatureState, UnavailableFact
from anta._advisory.facts.tracing import (
    AaaPasswordTraceFact,
    AaaTacacsKeyTraceFact,
    ConfigAgentPrivateKeyTraceFact,
    _level_expression_includes,
)
from tests.units.anta_tests.advisories import OfflineAntaDevice

if TYPE_CHECKING:
    from anta._advisory.facts.models import CommandsFactDefinition, FeatureValue
    from anta.models import AntaCommand

T = TypeVar("T")


@pytest.fixture(name="device")
def fact_device_fixture() -> OfflineAntaDevice:
    """Return an offline device suitable for fact derivation."""
    return OfflineAntaDevice("unit-test")


def command(definition: type[CommandsFactDefinition[T]], output: str) -> AntaCommand:
    """Return one populated command owned by a tracing fact."""
    instance = definition.commands[0].model_copy()
    instance.output = output
    return instance


@pytest.mark.parametrize(
    ("expression", "target", "expected"),
    [
        ("*", 4, True),
        ("4", 4, True),
        ("034", 4, True),
        ("034", 6, False),
        ("0-5", 4, True),
        ("0-5", 6, False),
        ("0-10", 6, True),
        ("7-3", 4, None),
        ("bad", 4, None),
    ],
)
def test_trace_level_expressions(expression: str, target: int, expected: bool | None) -> None:
    """Interpret EOS wildcard, compact, range, and invalid level expressions."""
    assert _level_expression_includes(expression, target) is expected


@pytest.mark.parametrize(
    ("definition", "config"),
    [
        (ConfigAgentPrivateKeyTraceFact, "trace ConfigAgent setting MgmtSecuritySslCertKey/034"),
        (AaaPasswordTraceFact, "trace Aaa setting Py*/0-5"),
        (AaaTacacsKeyTraceFact, "trace Aaa setting Tacacs*/0-7"),
        (AaaPasswordTraceFact, "trace Aaa setting */0-7"),
        (AaaTacacsKeyTraceFact, "trace Aaa setting */0-7"),
    ],
)
def test_risky_agent_trace_is_enabled(
    device: OfflineAntaDevice,
    definition: type[CommandsFactDefinition[FeatureValue]],
    config: str,
) -> None:
    """Recognize every source-documented risky selector form."""
    fact = definition.derive(device, (command(definition, config),))

    assert isinstance(fact, AvailableFact)
    assert fact.value.state is FeatureState.ENABLED


@pytest.mark.parametrize(
    ("definition", "config"),
    [
        (ConfigAgentPrivateKeyTraceFact, ""),
        (AaaPasswordTraceFact, "trace Aaa setting Radius*/0-7"),
        (AaaPasswordTraceFact, "trace Aaa setting Py*/0-5,-PyServer/4"),
        (AaaTacacsKeyTraceFact, "trace Aaa setting Tacacs*/0-7,-Tacacs/6"),
    ],
)
def test_safe_agent_trace_is_disabled(
    device: OfflineAntaDevice,
    definition: type[CommandsFactDefinition[FeatureValue]],
    config: str,
) -> None:
    """Recognize absent, unrelated, and explicitly disabled risky levels."""
    fact = definition.derive(device, (command(definition, config),))

    assert isinstance(fact, AvailableFact)
    assert fact.value.state is FeatureState.DISABLED


@pytest.mark.parametrize("config", ["trace Aaa enable PyServer levels 4", "trace Aaa setting [/4", "trace Aaa setting PyServer/7-3"])
def test_malformed_agent_trace_is_unavailable(device: OfflineAntaDevice, config: str) -> None:
    """Reject noncanonical commands, invalid regexes, and reversed ranges."""
    fact = AaaPasswordTraceFact.derive(device, (command(AaaPasswordTraceFact, config),))

    assert isinstance(fact, UnavailableFact)
    assert fact.problem is FactProblemKind.MALFORMED


def test_unsupported_trace_command_is_unavailable(device: OfflineAntaDevice) -> None:
    """Do not infer trace absence from a generic unsupported configuration command."""
    trace_command = command(AaaPasswordTraceFact, "")
    trace_command.output = None
    trace_command.errors = ["This command is not supported on this hardware platform"]

    fact = AaaPasswordTraceFact.derive(device, (trace_command,))

    assert isinstance(fact, UnavailableFact)
    assert fact.problem is FactProblemKind.UNSUPPORTED
