# Copyright (c) 2026 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Unit tests for structured advisory fact models."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from anta._advisory.facts.models import Fact, FactDefinition, FactProblemKind, FactSource, FactSourceKind, FeatureName, FeatureState, FeatureValue

if TYPE_CHECKING:
    from anta.device import AntaDevice
    from anta.models import AntaCommand


class ExampleFactDefinition(FactDefinition[FeatureValue]):
    """Concrete fact definition used to exercise the common model behavior."""

    key = "feature.example"
    label = "Example feature"

    @classmethod
    def derive(cls, device: AntaDevice, command: AntaCommand | None = None) -> Fact[FeatureValue]:
        """Return a stable value; derivation details are outside these model tests."""
        _ = device, command
        return cls.available(ENABLED, SOURCE)


SOURCE = FactSource("show example", FactSourceKind.COMMAND)
DEFINITION = ExampleFactDefinition
ENABLED = FeatureValue(FeatureName.SECURE_BOOT, FeatureState.ENABLED)
DISABLED = FeatureValue(FeatureName.SECURE_BOOT, FeatureState.DISABLED)


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
