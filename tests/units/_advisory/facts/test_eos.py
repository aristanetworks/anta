# Copyright (c) 2026 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Unit tests for facts normalized from EOS inputs."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from anta._advisory.facts.eos import EosVersionFact, SecureBootFact
from anta._advisory.facts.models import AvailableFact, FactProblemKind, FeatureState, UnavailableFact
from anta._eos.version import parse_eos_version
from anta.models import AntaCommand
from tests.units.anta_tests.advisories import OfflineAntaDevice

if TYPE_CHECKING:
    from anta.device import AntaDevice


@pytest.fixture(name="device")
def fact_device_fixture() -> OfflineAntaDevice:
    """Return an offline device suitable for fact derivation."""
    return OfflineAntaDevice("unit-test")


def secure_boot_command(output: dict[str, object]) -> AntaCommand:
    """Return the fact definition's command populated with structured output."""
    command = SecureBootFact.command.model_copy()
    command.output = output
    return command


def test_eos_version_fact_from_device_metadata(device: OfflineAntaDevice) -> None:
    """Normalize available and missing device-version metadata."""
    version = parse_eos_version("4.35.1F")
    assert version is not None

    device.version = version
    available = EosVersionFact.derive(device)
    device.version = None
    missing = EosVersionFact.derive(device)

    assert isinstance(available, AvailableFact)
    assert available.definition is EosVersionFact
    assert available.value is version
    assert available.source.name == "device metadata"
    assert isinstance(missing, UnavailableFact)
    assert missing.definition is EosVersionFact
    assert missing.problem is FactProblemKind.MISSING
    assert missing.source.name == "device metadata"


def test_secure_boot_supported_and_enabled(device: AntaDevice) -> None:
    """Normalize supported and enabled Secure Boot as active."""
    fact = SecureBootFact.derive(device, secure_boot_command({"securebootSupported": True, "securebootEnabled": True}))

    assert isinstance(fact, AvailableFact)
    assert fact.definition is SecureBootFact
    assert fact.value.state is FeatureState.ENABLED
    assert fact.source.name == "show boot"


@pytest.mark.parametrize(
    ("output", "state"),
    [
        ({"securebootSupported": False, "securebootEnabled": False}, FeatureState.UNSUPPORTED),
        ({"securebootSupported": True, "securebootEnabled": False}, FeatureState.DISABLED),
        ({"securebootSupported": False}, FeatureState.UNSUPPORTED),
        ({"securebootEnabled": False}, FeatureState.DISABLED),
        ({}, FeatureState.UNSUPPORTED),
    ],
)
def test_secure_boot_false_prerequisite(device: AntaDevice, output: dict[str, object], state: FeatureState) -> None:
    """Normalize any decisive false prerequisite as unsupported or disabled."""
    fact = SecureBootFact.derive(device, secure_boot_command(output))

    assert isinstance(fact, AvailableFact)
    assert fact.value.state is state


@pytest.mark.parametrize(
    ("output", "problem"),
    [
        ({"securebootSupported": True}, FactProblemKind.MISSING),
        ({"securebootEnabled": True}, FactProblemKind.MISSING),
        ({"securebootSupported": "true", "securebootEnabled": True}, FactProblemKind.MALFORMED),
        ({"securebootSupported": True, "securebootEnabled": 1}, FactProblemKind.MALFORMED),
    ],
)
def test_secure_boot_unavailable_evidence(device: AntaDevice, output: dict[str, object], problem: FactProblemKind) -> None:
    """Classify incomplete and malformed Secure Boot evidence."""
    fact = SecureBootFact.derive(device, secure_boot_command(output))

    assert isinstance(fact, UnavailableFact)
    assert fact.problem is problem


def test_secure_boot_contradictory_evidence(device: AntaDevice) -> None:
    """Retain both observations when support and enabled state contradict."""
    fact = SecureBootFact.derive(device, secure_boot_command({"securebootSupported": False, "securebootEnabled": True}))

    assert isinstance(fact, UnavailableFact)
    assert fact.problem is FactProblemKind.CONTRADICTORY
    assert tuple(observation.state for observation in fact.observations) == (FeatureState.UNSUPPORTED, FeatureState.ENABLED)


def test_command_fact_rejects_the_wrong_command(device: AntaDevice) -> None:
    """Prevent a fact definition from parsing output collected for another command."""
    with pytest.raises(ValueError, match="cannot be derived"):
        SecureBootFact.derive(device, AntaCommand(command="show version", output={}))


def test_command_fact_without_collected_command(device: AntaDevice) -> None:
    """Represent a missing collected command as unavailable evidence."""
    fact = SecureBootFact.derive(device)

    assert isinstance(fact, UnavailableFact)
    assert fact.problem is FactProblemKind.COLLECTION_FAILED
