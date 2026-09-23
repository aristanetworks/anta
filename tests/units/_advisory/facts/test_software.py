# Copyright (c) 2026 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Unit tests for facts normalized from EOS software output."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from anta._advisory.facts.models import AvailableFact, FactProblemKind, MitigationState, UnavailableFact
from anta._advisory.facts.software import SA171HotfixFact, SA173HotfixFact
from tests.units.anta_tests.advisories import OfflineAntaDevice

if TYPE_CHECKING:
    from anta.models import AntaCommand


@pytest.fixture(name="device")
def fact_device_fixture() -> OfflineAntaDevice:
    """Return an offline device suitable for fact derivation."""
    return OfflineAntaDevice("unit-test")


def commands(definition: type[SA171HotfixFact | SA173HotfixFact], extensions: object, boot_extensions: object) -> tuple[AntaCommand, AntaCommand]:
    """Return populated extension commands."""
    extension_command, boot_command = (command.model_copy() for command in definition.commands)
    extension_command.output = {"extensions": extensions}
    boot_command.output = {"extensions": boot_extensions}
    return extension_command, boot_command


HOTFIX_FACTS = (
    (SA173HotfixFact, "sa173-SecurityAdvisory173_CVE-2026-73455.swix"),
    (SA171HotfixFact, "sa171-SecurityAdvisory171_CVE-2026-73435.swix"),
)


@pytest.mark.parametrize(
    ("status", "persistent", "state", "source_index"),
    [
        ("installed", True, MitigationState.EFFECTIVE, 1),
        ("installed", False, MitigationState.INEFFECTIVE, 1),
        ("notInstalled", True, MitigationState.INEFFECTIVE, 0),
    ],
)
@pytest.mark.parametrize(("definition", "extension_name"), HOTFIX_FACTS)
def test_persistent_hotfix_state(
    device: OfflineAntaDevice,
    definition: type[SA171HotfixFact | SA173HotfixFact],
    extension_name: str,
    status: str,
    persistent: bool,
    state: MitigationState,
    source_index: int,
) -> None:
    """Require the SWIX to be installed and boot-persistent."""
    persistent_extensions = [extension_name] if persistent else []
    fact = definition.derive(device, commands(definition, {extension_name: {"status": status, "boot": persistent}}, persistent_extensions))

    assert isinstance(fact, AvailableFact)
    assert fact.value.state is state
    assert fact.source.name == definition.commands[source_index].command


def test_persistent_hotfix_shared_device_output(device: OfflineAntaDevice) -> None:
    """Distinguish installed and incompatible hotfixes using both EOS extension outputs."""
    extensions = {
        SA171HotfixFact.extension_name: {"status": "notInstalled", "boot": True},
        SA173HotfixFact.extension_name: {"status": "installed", "boot": True},
    }
    boot_extensions = [SA173HotfixFact.extension_name, SA171HotfixFact.extension_name]

    sa171 = SA171HotfixFact.derive(device, commands(SA171HotfixFact, extensions, boot_extensions))
    sa173 = SA173HotfixFact.derive(device, commands(SA173HotfixFact, extensions, boot_extensions))

    assert isinstance(sa171, AvailableFact)
    assert sa171.value.state is MitigationState.INEFFECTIVE
    assert sa171.source.name == "show extensions"
    assert isinstance(sa173, AvailableFact)
    assert sa173.value.state is MitigationState.EFFECTIVE
    assert sa173.source.name == "show boot-extensions"


@pytest.mark.parametrize(("definition", "extension_name"), HOTFIX_FACTS)
def test_persistent_hotfix_absent(device: OfflineAntaDevice, definition: type[SA171HotfixFact | SA173HotfixFact], extension_name: str) -> None:
    """Treat an absent SWIX as an ineffective mitigation."""
    assert definition.extension_name == extension_name
    fact = definition.derive(device, commands(definition, {}, []))

    assert isinstance(fact, AvailableFact)
    assert fact.value.state is MitigationState.INEFFECTIVE
    assert fact.source.name == definition.commands[0].command


@pytest.mark.parametrize(
    ("extensions", "boot_extensions", "problem", "source_index"),
    [
        (None, [], FactProblemKind.MISSING, 0),
        ([], [], FactProblemKind.MALFORMED, 0),
        ({"hotfix": {}}, [], FactProblemKind.MALFORMED, 0),
        ({"hotfix": {"status": "installed"}}, {}, FactProblemKind.MALFORMED, 1),
    ],
)
@pytest.mark.parametrize(("definition", "extension_name"), HOTFIX_FACTS)
def test_persistent_hotfix_invalid(
    device: OfflineAntaDevice,
    definition: type[SA171HotfixFact | SA173HotfixFact],
    extension_name: str,
    extensions: object,
    boot_extensions: object,
    problem: FactProblemKind,
    source_index: int,
) -> None:
    """Reject missing and malformed extension output."""
    normalized_extensions = {extension_name: next(iter(extensions.values()), {})} if isinstance(extensions, dict) else extensions
    normalized_boot_extensions = [extension_name] if isinstance(boot_extensions, list) and boot_extensions else boot_extensions
    extension_command, boot_command = commands(definition, normalized_extensions, normalized_boot_extensions)
    if extensions is None:
        extension_command.output = {}

    fact = definition.derive(device, (extension_command, boot_command))

    assert isinstance(fact, UnavailableFact)
    assert fact.problem is problem
    assert fact.source.name == definition.commands[source_index].command


@pytest.mark.parametrize(("definition", "extension_name"), HOTFIX_FACTS)
def test_persistent_hotfix_unsupported(device: OfflineAntaDevice, definition: type[SA171HotfixFact | SA173HotfixFact], extension_name: str) -> None:
    """Retain unsupported extension collection as unavailable."""
    assert definition.extension_name == extension_name
    extension_command, boot_command = commands(definition, {}, [])
    extension_command.output = None
    extension_command.errors = ["This command is not supported on this hardware platform"]

    fact = definition.derive(device, (extension_command, boot_command))

    assert isinstance(fact, UnavailableFact)
    assert fact.problem is FactProblemKind.UNSUPPORTED
    assert fact.source.name == definition.commands[0].command
