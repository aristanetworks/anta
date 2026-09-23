# Copyright (c) 2026 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Unit tests for facts normalized from EOS platform output."""

from __future__ import annotations

from dataclasses import asdict
from typing import Any, cast

import pytest

from anta._advisory.facts.models import AvailableFact, FactProblemKind, UnavailableFact
from anta._advisory.facts.platform import PlatformIdentityFact, SwitchCardIdentityFact
from anta._eos.platform import PlatformComponentIdentity, PlatformComponentRole, PlatformFamily, PlatformIdentity, PlatformType
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


@pytest.mark.parametrize(
    ("model", "family"),
    [("7358X4-SC", PlatformFamily.SERIES_7358_X4), ("7368X4-SC", PlatformFamily.SERIES_7368_X4)],
)
def test_switch_card_identity(device: OfflineAntaDevice, model: str, family: PlatformFamily) -> None:
    """Normalize the switch-card model without retaining line-card details."""
    output = {"modules": {"1": {"modelName": "7368-SUP"}, "Switchcard1": {"modelName": model}, "2": {"modelName": "7368-16C"}}}

    device.platform = platform_with_modules(output)
    fact = SwitchCardIdentityFact.derive(device)

    assert isinstance(fact, AvailableFact)
    assert fact.definition is SwitchCardIdentityFact
    assert isinstance(fact.value, SwitchCardIdentityFact)
    assert fact.value.model == model
    assert fact.value.role is PlatformComponentRole.SWITCH_CARD
    assert fact.value.slot == "Switchcard1"
    assert fact.value.platform_families == frozenset({family})


def test_platform_identity_fact_from_identity_preserves_all_fields() -> None:
    """Copy the complete normalized platform identity into its nominal fact type."""
    module = PlatformComponentIdentity(
        model="7358X4-SC",
        role=PlatformComponentRole.SWITCH_CARD,
        slot="Switchcard1",
        platform_families=frozenset({PlatformFamily.SERIES_7358_X4}),
    )
    platform = PlatformIdentity(
        model="DCS-7358-CH",
        type=PlatformType.CHASSIS,
        modules=(module,),
        platform_families=frozenset({PlatformFamily.SERIES_7358_X4}),
    )

    fact = PlatformIdentityFact.from_identity(platform)

    assert fact.model == platform.model
    assert fact.type is platform.type
    assert fact.modules == platform.modules
    assert fact.platform_families == platform.platform_families
    assert fact.to_dict() == platform.to_dict()


def test_platform_identity_fact_derive_returns_nominal_value(device: OfflineAntaDevice) -> None:
    """Preserve the refreshed platform fields when deriving a nominal fact."""
    platform = platform_with_modules({"modules": {"Switchcard1": {"modelName": "7368X4-SC"}}})
    device.platform = platform

    fact = PlatformIdentityFact.derive(device)

    assert isinstance(fact, AvailableFact)
    assert fact.definition is PlatformIdentityFact
    assert isinstance(fact.value, PlatformIdentityFact)
    assert fact.value.model == platform.model
    assert fact.value.type is platform.type
    assert fact.value.modules == platform.modules
    assert fact.value.platform_families == platform.platform_families
    assert fact.value.to_dict() == platform.to_dict()


def test_switch_card_identity_fact_from_identity_preserves_all_fields() -> None:
    """Copy every normalized switch-card field into its nominal fact type."""
    card = PlatformComponentIdentity(
        model="7368X4-SC",
        role=PlatformComponentRole.SWITCH_CARD,
        slot="Switchcard2",
        platform_families=frozenset({PlatformFamily.SERIES_7368_X4}),
    )

    fact = SwitchCardIdentityFact.from_identity(card)

    assert fact.model == card.model
    assert fact.role is card.role
    assert fact.slot == card.slot
    assert fact.platform_families == card.platform_families
    assert asdict(fact) == asdict(card)


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
