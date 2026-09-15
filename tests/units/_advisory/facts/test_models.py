# Copyright (c) 2026 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Unit tests for structured advisory fact models."""

from __future__ import annotations

import inspect
from dataclasses import MISSING, dataclass, field, fields
from typing import TYPE_CHECKING

import pytest

from anta._advisory.facts.models import (
    Fact,
    FactDefinition,
    FactProblemKind,
    FactsBase,
    FactSource,
    FactSourceKind,
    FeatureName,
    FeatureState,
    FeatureValue,
    fact_field,
    facts_dataclass,
)

if TYPE_CHECKING:
    from anta.device import AntaDevice
    from anta.models import AntaCommand


class ExampleFactDefinition(FactDefinition[FeatureValue]):
    """Concrete fact definition used to exercise the common model behavior."""

    key = "feature.example"
    label = "Example feature"

    @classmethod
    def derive(cls, device: AntaDevice, commands: tuple[AntaCommand, ...] = ()) -> Fact[FeatureValue]:
        """Return a stable value; derivation details are outside these model tests."""
        _ = device, commands
        return cls.available(ENABLED, SOURCE)


SOURCE = FactSource("show example", FactSourceKind.COMMAND)
DEFINITION = ExampleFactDefinition
ENABLED = FeatureValue(FeatureName.SECURE_BOOT, FeatureState.ENABLED)
DISABLED = FeatureValue(FeatureName.SECURE_BOOT, FeatureState.DISABLED)


def test_fact_field_retains_definition_and_declares_required_constructor_field() -> None:
    """Retain the typed definition while keeping the collected value required."""

    @facts_dataclass
    class DeclaredFacts(FactsBase):
        """Fact container with one required collected value."""

        value: Fact[FeatureValue] = fact_field(DEFINITION)

    declared_field = fields(DeclaredFacts)[0]
    available = DEFINITION.available(ENABLED, SOURCE)

    assert declared_field.default is MISSING
    assert declared_field.default_factory is MISSING
    assert inspect.signature(DeclaredFacts).parameters["value"].default is inspect.Parameter.empty
    assert DeclaredFacts.definitions() == {"value": DEFINITION}
    assert DeclaredFacts(value=available).value is available
    with pytest.raises(TypeError, match="missing 1 required positional argument: 'value'"):
        DeclaredFacts()  # pyright: ignore[reportCallIssue]


def test_facts_base_rejects_fields_without_fact_factory() -> None:
    """Reject fields that do not use the typed fact factory declaration."""

    @facts_dataclass
    class MissingFactoryFacts(FactsBase):
        """Fact container without a fact field specifier."""

        value: Fact[FeatureValue]

    @dataclass(frozen=True, slots=True)
    class OrdinaryFactoryFacts(FactsBase):
        """Fact container using an ordinary default factory."""

        value: Fact[FeatureValue] = field(default_factory=lambda: DEFINITION.available(ENABLED, SOURCE))

    for invalid_facts in (MissingFactoryFacts, OrdinaryFactoryFacts):
        with pytest.raises(TypeError, match=r"must use fact_field\(\.\.\.\)"):
            invalid_facts.definitions()


def test_facts_base_rejects_empty_and_non_init_fact_containers() -> None:
    """Require at least one fact field and constructor-compatible declarations."""

    @facts_dataclass
    class EmptyFacts(FactsBase):
        """Fact container without declared facts."""

    @dataclass(frozen=True, slots=True)
    class NonInitFacts(FactsBase):
        """Fact container whose declared fact cannot be initialized."""

        value: Fact[FeatureValue] = field(init=False, metadata={"anta.fact_definition": DEFINITION})

    with pytest.raises(TypeError, match="must declare one or more fact fields"):
        EmptyFacts.definitions()
    with pytest.raises(TypeError, match="must be included in the generated initializer"):
        NonInitFacts.definitions()


def test_facts_base_rejects_duplicate_definitions() -> None:
    """Reject duplicate definitions that collector.fact could not distinguish."""

    @facts_dataclass
    class DuplicateFacts(FactsBase):
        """Fact container that declares one definition under two names."""

        first: Fact[FeatureValue] = fact_field(DEFINITION)
        second: Fact[FeatureValue] = fact_field(DEFINITION)

    with pytest.raises(TypeError, match=r"fields 'first' and 'second'.*same fact definition 'ExampleFactDefinition'"):
        DuplicateFacts.definitions()


def test_fact_definition_constructs_available_and_unavailable_facts() -> None:
    """Retain typed identity, normalized values, provenance, and problem quality."""
    available = DEFINITION.available(ENABLED, SOURCE)
    unavailable = DEFINITION.unavailable(FactProblemKind.MISSING, SOURCE)

    assert available.definition is DEFINITION
    assert available.value is ENABLED
    assert available.source is SOURCE
    assert unavailable.definition is DEFINITION
    assert unavailable.problem is FactProblemKind.MISSING
    assert unavailable.source is SOURCE


def test_contradictory_fact_retains_observations() -> None:
    """Require contradictory evidence to retain at least two typed observations."""
    unavailable = DEFINITION.unavailable(
        FactProblemKind.CONTRADICTORY,
        SOURCE,
        observations=(ENABLED, DISABLED),
    )

    assert unavailable.observations == (ENABLED, DISABLED)

    with pytest.raises(ValueError, match="at least two observations"):
        DEFINITION.unavailable(FactProblemKind.CONTRADICTORY, SOURCE, observations=(ENABLED,))


def test_non_contradictory_fact_rejects_observations() -> None:
    """Prevent unrelated unavailable facts from carrying arbitrary observations."""
    with pytest.raises(ValueError, match="Only contradictory"):
        DEFINITION.unavailable(FactProblemKind.MALFORMED, SOURCE, observations=(ENABLED, DISABLED))


@pytest.mark.parametrize(
    ("key", "label"),
    [("", "label"), ("key", ""), ("bad\nkey", "label"), ("key", "bad\nlabel")],
)
def test_fact_definition_rejects_invalid_identity(key: str, label: str) -> None:
    """Require stable, renderable fact identities."""
    with pytest.raises(ValueError, match="non-empty and single-line"):
        type("InvalidFactDefinition", (ExampleFactDefinition,), {"key": key, "label": label})
