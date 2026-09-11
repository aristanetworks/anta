# Copyright (c) 2026 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Unit tests for facts normalized from EOS platform output."""

from __future__ import annotations

from typing import Any, cast

import pytest

from anta._advisory.facts.models import AvailableFact, FactProblemKind, UnavailableFact
from anta._advisory.facts.platform import SwitchCardIdentityFact
from anta._eos.platform import PlatformComponentRole, PlatformIdentity
from tests.units.anta_tests import build_eos_platform
from tests.units.anta_tests.advisories import OfflineAntaDevice


@pytest.fixture(name="device")
def fact_device_fixture() -> OfflineAntaDevice:
    """Return an offline device suitable for fact derivation."""
    return OfflineAntaDevice("unit-test")


def platform_with_modules(output: dict[str, Any]) -> PlatformIdentity:
    """Build refreshed chassis metadata containing the supplied module inventory."""
    platform = build_eos_platform("7368-F", output)
    assert platform is not None
    return platform


@pytest.mark.parametrize("model", ["7358X4-SC", "7368X4-SC"])
def test_switch_card_identity(device: OfflineAntaDevice, model: str) -> None:
    """Normalize the switch-card model without retaining line-card details."""
    output = {"modules": {"1": {"modelName": "7368-SUP"}, "Switchcard1": {"modelName": model}, "2": {"modelName": "7368-16C"}}}

    device.platform = platform_with_modules(output)
    fact = SwitchCardIdentityFact.derive(device)

    assert isinstance(fact, AvailableFact)
    assert fact.value.model == model
    assert fact.value.role is PlatformComponentRole.SWITCH_CARD


def test_switch_card_missing(device: OfflineAntaDevice) -> None:
    """Report missing switch-card metadata when inventory has no switch card."""
    device.platform = platform_with_modules({"modules": {"1": {"modelName": "7368-SUP"}}})
    fact = SwitchCardIdentityFact.derive(device)

    assert isinstance(fact, UnavailableFact)
    assert fact.problem is FactProblemKind.MISSING


def test_switch_card_conflicting_models(device: OfflineAntaDevice) -> None:
    """Retain distinct switch-card identities as contradictory observations."""
    output = {"modules": {"Switchcard1": {"modelName": "7358X4-SC"}, "Switchcard2": {"modelName": "7368X4-SC"}}}

    device.platform = platform_with_modules(output)
    fact = SwitchCardIdentityFact.derive(device)

    assert isinstance(fact, UnavailableFact)
    assert fact.problem is FactProblemKind.CONTRADICTORY


def test_duplicate_switch_cards_in_different_slots_are_consistent(device: OfflineAntaDevice) -> None:
    """Ignore physical slot identity when identical switch cards establish the same assessment identity."""
    output = {"modules": {"Switchcard1": {"modelName": "7358X4-SC"}, "Switchcard2": {"modelName": "7358X4-SC"}}}

    device.platform = platform_with_modules(output)
    fact = SwitchCardIdentityFact.derive(device)

    assert isinstance(fact, AvailableFact)
    assert fact.value.model == "7358X4-SC"


def test_switch_card_invalid_platform_metadata(device: OfflineAntaDevice) -> None:
    """Reject device platform metadata with the wrong runtime type."""
    device.platform = cast("Any", "7368-F")
    fact = SwitchCardIdentityFact.derive(device)

    assert isinstance(fact, UnavailableFact)
    assert fact.problem is FactProblemKind.INVALID
