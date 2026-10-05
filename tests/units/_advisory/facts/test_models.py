# Copyright (c) 2026 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Unit tests for structured advisory fact models."""

from __future__ import annotations

from dataclasses import MISSING, dataclass, field, fields
from typing import TYPE_CHECKING, Any, ClassVar, cast

import pytest

from anta._advisory.eos_versions import VersionRule
from anta._advisory.facts.models import (
    AvailableFact,
    CommandsFactDefinition,
    Fact,
    FactDefinition,
    FactProblemKind,
    FactsBase,
    FactSource,
    FactSourceKind,
    FeatureFact,
    FeatureName,
    FeatureRef,
    FeatureState,
    UnavailableFact,
    fact_field,
    facts_dataclass,
)
from anta._eos.version import EOSVersion
from anta.models import AntaCommand

if TYPE_CHECKING:
    from anta.device import AntaDevice


@dataclass(frozen=True, slots=True)
class ExampleFactDefinition(FeatureFact, FactDefinition["ExampleFactDefinition"]):
    """Concrete fact definition used to exercise the common model behavior."""

    feature: ClassVar[FeatureRef] = FeatureName.SECURE_BOOT
    key: ClassVar[str] = "feature.example"
    label: ClassVar[str] = "Example feature"

    @classmethod
    def derive(cls, device: AntaDevice, commands: tuple[AntaCommand, ...] = ()) -> Fact[ExampleFactDefinition]:
        """Return a stable value; derivation details are outside these model tests."""
        _ = device, commands
        return ENABLED.available(SOURCE)


@dataclass(frozen=True, slots=True)
class ExampleCommandsFactDefinition(FeatureFact, CommandsFactDefinition["ExampleCommandsFactDefinition"]):
    """Command-derived feature fact restricted to selected EOS releases."""

    feature: ClassVar[FeatureRef] = FeatureName.SECURE_BOOT
    key: ClassVar[str] = "feature.example.commands"
    label: ClassVar[str] = "Example command feature"
    commands: ClassVar[tuple[AntaCommand, ...]] = (AntaCommand(command="show example", revision=1),)
    supported_versions: ClassVar[tuple[VersionRule, ...]] = (
        VersionRule(major=4, minor=33, patch_gte=2),
        VersionRule(major=4, minor_gt=33, minor_lt=39),
    )

    @classmethod
    def parse(cls, commands: tuple[AntaCommand, ...]) -> Fact[ExampleCommandsFactDefinition]:
        """Return an enabled feature after the base class validates the command."""
        return cls(FeatureState.ENABLED).available(FactSource(commands[0].command, FactSourceKind.COMMAND))


@dataclass(frozen=True, slots=True)
class ExampleNonFeatureCommandsFactDefinition(CommandsFactDefinition["ExampleNonFeatureCommandsFactDefinition"]):
    """Command-derived non-feature fact used to exercise the default unsupported result."""

    value: str
    key: ClassVar[str] = "example.commands"
    label: ClassVar[str] = "Example command value"
    commands: ClassVar[tuple[AntaCommand, ...]] = (AntaCommand(command="show example", revision=1),)
    supported_versions: ClassVar[tuple[VersionRule, ...]] = (VersionRule(major=4, minor=33, patch_gte=2),)

    @classmethod
    def parse(cls, commands: tuple[AntaCommand, ...]) -> Fact[ExampleNonFeatureCommandsFactDefinition]:
        """Return a stable value after the base class validates the command."""
        return cls("available").available(FactSource(commands[0].command, FactSourceKind.COMMAND))


class InvalidDeviceVersion:
    """Device-version protocol implementation with a non-EOS string representation."""

    def __str__(self) -> str:
        return "not-an-eos-version"

    def to_dict(self) -> dict[str, str | int]:
        """Return the protocol representation expected by device metadata consumers."""
        return {"version": str(self)}


SOURCE = FactSource("show example", FactSourceKind.COMMAND)
DEFINITION = ExampleFactDefinition
ENABLED = ExampleFactDefinition(FeatureState.ENABLED)
DISABLED = ExampleFactDefinition(FeatureState.DISABLED)


def test_fact_field_retains_definition_and_declares_required_constructor_field() -> None:
    """Retain the typed definition while keeping the collected value required."""

    @facts_dataclass
    class DeclaredFacts(FactsBase):
        """Fact container with one required collected value."""

        value: Fact[ExampleFactDefinition] = fact_field(DEFINITION)

    declared_field = fields(DeclaredFacts)[0]
    available = ENABLED.available(SOURCE)

    assert declared_field.default is MISSING
    assert declared_field.default_factory is MISSING
    assert DeclaredFacts.definitions() is DeclaredFacts.definitions()
    assert DeclaredFacts.definitions() == {"value": DEFINITION}
    assert DeclaredFacts(value=available).value is available


def test_facts_base_rejects_fields_without_fact_declaration() -> None:
    """Reject fields that do not carry a valid runtime fact declaration."""
    with pytest.raises(TypeError, match=r"must use fact_field\(\.\.\.\)"):

        @facts_dataclass
        class MissingDeclarationFacts(FactsBase):
            """Fact container without a fact field specifier."""

            value: Fact[ExampleFactDefinition]

    @dataclass(frozen=True, slots=True)
    class OrdinaryDataclassFacts(FactsBase):
        """Fact container using an ordinary dataclass field declaration."""

        value: Fact[ExampleFactDefinition] = field(default_factory=lambda: ENABLED.available(SOURCE))

    with pytest.raises(TypeError, match="must use @facts_dataclass"):
        OrdinaryDataclassFacts.definitions()


def test_facts_base_rejects_empty_and_non_init_fact_containers() -> None:
    """Require at least one fact field and constructor-compatible declarations."""
    with pytest.raises(TypeError, match="must declare one or more fact fields"):

        @facts_dataclass
        class EmptyFacts(FactsBase):
            """Fact container without declared facts."""

    with pytest.raises(TypeError, match="must be included in the generated initializer"):

        @facts_dataclass
        class NonInitFacts(FactsBase):
            """Malformed container bypassing the helper with a non-init field."""

            # Valid raw metadata deliberately bypasses the public helper so validation
            # reaches the independent generated-initializer check.
            value: Fact[ExampleFactDefinition] = field(init=False, metadata={"definition": DEFINITION})  # pylint: disable=invalid-field-call


def test_facts_base_rejects_duplicate_definitions() -> None:
    """Require one uniquely identified collected fact per container field."""

    class DuplicateFacts(FactsBase):
        """Fact container that declares one definition under two names."""

        first: Fact[ExampleFactDefinition] = fact_field(DEFINITION)
        second: Fact[ExampleFactDefinition] = fact_field(DEFINITION)

    with pytest.raises(TypeError, match=r"fields 'first' and 'second'.*same fact definition 'ExampleFactDefinition'"):
        facts_dataclass(DuplicateFacts)


def test_fact_definition_constructs_available_and_unavailable_facts() -> None:
    """Retain typed identity, normalized values, provenance, and problem quality."""
    available = ENABLED.available(SOURCE)
    unavailable = DEFINITION.unavailable(FactProblemKind.MISSING, SOURCE)

    assert available.definition is DEFINITION
    assert available.value is ENABLED
    assert available.source is SOURCE
    assert unavailable.definition is DEFINITION
    assert unavailable.problem is FactProblemKind.MISSING
    assert unavailable.source is SOURCE


def test_fact_wrappers_reject_non_nominal_values() -> None:
    """Reject manual wrappers and contradictory observations that bypass nominal construction."""
    non_nominal_value = cast("Any", "not a nominal fact")
    with pytest.raises(TypeError, match="must be FactDefinition instances"):
        AvailableFact(value=non_nominal_value, source=SOURCE)

    observations = cast("tuple[ExampleFactDefinition, ...]", ("first", "second"))
    with pytest.raises(TypeError, match="must be instances of ExampleFactDefinition"):
        DEFINITION.unavailable(FactProblemKind.CONTRADICTORY, SOURCE, observations=observations)


def test_feature_fact_requires_feature_identity() -> None:
    """Reject nominal feature facts without a runtime feature identity."""
    with pytest.raises(TypeError, match="must define 'feature' as a FeatureName or SubFeature"):

        class MissingFeatureFact(FeatureFact):  # pylint: disable=too-few-public-methods
            """Feature fact missing its required class-level identity."""


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


@pytest.mark.parametrize("version", [EOSVersion(4, 33, 2), EOSVersion(4, 34, 0), EOSVersion(4, 38, 99)])
def test_commands_fact_definition_parses_supported_eos_versions(device: AntaDevice, version: EOSVersion) -> None:
    """Parse command-derived facts on every declared supported range."""
    device.version = version

    fact = ExampleCommandsFactDefinition.derive(device, ExampleCommandsFactDefinition.commands)

    assert isinstance(fact, AvailableFact)
    assert fact.value.state is FeatureState.ENABLED


@pytest.mark.parametrize("version", [EOSVersion(4, 33, 1), EOSVersion(4, 39, 0)])
def test_commands_fact_definition_returns_known_unsupported_feature_before_command_validation(device: AntaDevice, version: EOSVersion) -> None:
    """Return a known unsupported feature without requiring or parsing collected commands."""
    device.version = version

    fact = ExampleCommandsFactDefinition.derive(device)

    assert isinstance(fact, AvailableFact)
    assert fact.value.state is FeatureState.UNSUPPORTED
    assert fact.source == FactSource("show example", FactSourceKind.COMMAND)


def test_commands_fact_definition_returns_unavailable_unsupported_for_other_fact_kinds(device: AntaDevice) -> None:
    """Use the generic unavailable result when an unsupported fact has no known feature state."""
    device.version = EOSVersion(4, 33, 1)

    fact = ExampleNonFeatureCommandsFactDefinition.derive(device)

    assert isinstance(fact, UnavailableFact)
    assert fact.problem is FactProblemKind.UNSUPPORTED


def test_commands_fact_definition_validates_commands_when_eos_version_is_unknown(device: AntaDevice) -> None:
    """Preserve command-driven derivation when EOS version metadata is unavailable."""
    device.version = None

    fact = ExampleCommandsFactDefinition.derive(device)

    assert isinstance(fact, UnavailableFact)
    assert fact.problem is FactProblemKind.COLLECTION_FAILED


def test_commands_fact_definition_rejects_invalid_device_version(device: AntaDevice) -> None:
    """Report non-EOS device-version metadata as invalid instead of bypassing the version filter."""
    device.version = InvalidDeviceVersion()

    fact = ExampleCommandsFactDefinition.derive(device)

    assert isinstance(fact, UnavailableFact)
    assert fact.problem is FactProblemKind.INVALID
    assert fact.source == FactSource("device metadata", FactSourceKind.DEVICE_METADATA)
