# Copyright (c) 2026 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Unit tests for the security advisory test base."""

from __future__ import annotations

import inspect
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, ClassVar

import pytest

from anta._advisory.base import _AntaAdvisoryTest
from anta._advisory.facts.eos import EosVersionFact
from anta._advisory.facts.models import (
    AvailableFact,
    CommandsFactDefinition,
    Fact,
    FactsBase,
    FactSource,
    FactSourceKind,
    fact_field,
    facts_dataclass,
)
from anta._advisory.optional_commands import OptionalAntaCommand
from anta._advisory.results import _AdvisoryTestResult, _get_advisory_metadata
from anta._eos.version import parse_eos_version
from anta.models import AntaCommand, AntaTest
from anta.result_manager.models import TestResult as AntaTestResult
from tests.units._advisory.conftest import ADVISORY

if TYPE_CHECKING:
    from anta._advisory.models import _AdvisoryMetadata
    from anta.device import AntaDevice


@dataclass(frozen=True, slots=True)
class FakeCommandFact(CommandsFactDefinition["FakeCommandFact"]):
    """Normalize one value from a fake JSON command."""

    value: str
    key: ClassVar[str] = "fake.value"
    label: ClassVar[str] = "Fake value"
    commands: ClassVar[tuple[AntaCommand, ...]] = (AntaCommand(command="show fake", revision=1),)

    @classmethod
    def parse(cls, commands: tuple[AntaCommand, ...]) -> Fact[FakeCommandFact]:
        """Return the fake value from the collected command."""
        (command,) = commands
        return cls(str(command.json_output["value"])).available(FactSource(command.command, FactSourceKind.COMMAND))


class FakeAdvisoryTest(_AntaAdvisoryTest):
    """Fake security advisory test."""

    @facts_dataclass
    class Facts(FactsBase):
        """Typed facts required by the fake advisory."""

        value: Fact[FakeCommandFact] = fact_field(FakeCommandFact)

    advisory: ClassVar[_AdvisoryMetadata] = ADVISORY

    @_AntaAdvisoryTest.anta_test
    def test(self) -> None:
        """Set the test result to success."""
        self.result.is_success()


class FactAdvisoryTest(_AntaAdvisoryTest):
    """Fake advisory test whose commands are derived from its typed fields."""

    @facts_dataclass
    class Facts(FactsBase):
        """Typed facts required by the fake advisory."""

        value: Fact[FakeCommandFact] = fact_field(FakeCommandFact)

    advisory: ClassVar[_AdvisoryMetadata] = ADVISORY

    @_AntaAdvisoryTest.anta_test
    def test(self) -> None:
        """Set the result from the normalized fact."""
        facts = self.Facts.collect(self)
        self.result.is_success(str(facts.value))


class FactsAdvisoryTest(_AntaAdvisoryTest):
    """Fake advisory test whose typed fields declare the facts to collect."""

    @facts_dataclass
    class Facts(FactsBase):
        """Typed facts required by the fake advisory."""

        value: Fact[FakeCommandFact] = fact_field(FakeCommandFact)

    advisory: ClassVar[_AdvisoryMetadata] = ADVISORY

    @_AntaAdvisoryTest.anta_test
    def test(self) -> None:
        """Set the result from the normalized fact."""
        facts = self.Facts.collect(self)
        self.result.is_success(str(facts.value))


@dataclass(frozen=True, slots=True)
class RequiredSharedCommandFact(CommandsFactDefinition["RequiredSharedCommandFact"]):
    """Normalize a required command that shares its UID with an optional command."""

    value: str
    key: ClassVar[str] = "fake.required"
    label: ClassVar[str] = "Required fake value"
    commands: ClassVar[tuple[AntaCommand, ...]] = (AntaCommand(command="show fake", revision=1),)

    @classmethod
    def parse(cls, commands: tuple[AntaCommand, ...]) -> Fact[RequiredSharedCommandFact]:
        """Return the required fake value."""
        (command,) = commands
        return cls(str(command.json_output["value"])).available(FactSource(command.command, FactSourceKind.COMMAND))


@dataclass(frozen=True, slots=True)
class OptionalSharedCommandFact(CommandsFactDefinition["OptionalSharedCommandFact"]):
    """Normalize an optional command that shares its UID with a required command."""

    value: str
    key: ClassVar[str] = "fake.optional"
    label: ClassVar[str] = "Optional fake value"
    commands: ClassVar[tuple[AntaCommand, ...]] = (OptionalAntaCommand(command="show fake", revision=1),)

    @classmethod
    def parse(cls, commands: tuple[AntaCommand, ...]) -> Fact[OptionalSharedCommandFact]:
        """Return the optional fake value."""
        (command,) = commands
        return cls(str(command.json_output["value"])).available(FactSource(command.command, FactSourceKind.COMMAND))


class SharedCommandAdvisoryTest(_AntaAdvisoryTest):
    """Fake advisory test requiring distinct wrappers for the same EOS command."""

    @facts_dataclass
    class Facts(FactsBase):
        """Typed facts requiring distinct wrappers for one EOS command."""

        required: Fact[RequiredSharedCommandFact] = fact_field(RequiredSharedCommandFact)
        optional: Fact[OptionalSharedCommandFact] = fact_field(OptionalSharedCommandFact)

    advisory: ClassVar[_AdvisoryMetadata] = ADVISORY

    @_AntaAdvisoryTest.anta_test
    def test(self) -> None:
        """Set the result to success."""
        self.result.is_success()


class MetadataFactAdvisoryTest(_AntaAdvisoryTest):
    """Fake advisory test requiring only a device-metadata fact."""

    @facts_dataclass
    class Facts(FactsBase):
        """Typed metadata facts required by the fake advisory."""

        version: Fact[EosVersionFact] = fact_field(EosVersionFact)

    advisory: ClassVar[_AdvisoryMetadata] = ADVISORY

    @_AntaAdvisoryTest.anta_test
    def test(self) -> None:
        """Set the result from the metadata-derived fact."""
        facts = self.Facts.collect(self)
        self.result.is_success(str(facts.version))


def test_advisory_base_is_abstract() -> None:
    """Verify the advisory base inherits the abstract test contract."""
    assert inspect.isabstract(_AntaAdvisoryTest)
    assert _AntaAdvisoryTest.test is AntaTest.test
    assert not _AntaAdvisoryTest.commands


def test_advisory_result(device: AntaDevice) -> None:
    """Verify advisory metadata is attached to results but kept off serialized output."""
    test_instance = FakeAdvisoryTest(
        device=device,
        inputs={
            "result_overwrite": {
                "categories": ["overridden"],
                "description": "Overridden description.",
                "custom_field": "Overridden custom field.",
            }
        },
        eos_data=[{"version": "4.36.1F"}],
    )

    assert test_instance.categories == ["advisories"]
    assert test_instance.result.categories == ["overridden"]
    assert test_instance.result.description == "Overridden description."
    assert test_instance.result.custom_field == "Overridden custom field."
    assert isinstance(test_instance.result, _AdvisoryTestResult)
    assert _get_advisory_metadata(test_instance.result) is ADVISORY
    dumped_result = test_instance.result.model_dump(mode="json", exclude_none=True)
    assert "metadata" not in dumped_result
    assert "advisory" not in dumped_result


def test_advisory_fact_container_owns_commands_and_derivation(device: AntaDevice) -> None:
    """Derive class commands and nominal values from locally declared fact fields."""
    test_instance = FactAdvisoryTest(device=device, eos_data=[{"value": "normalized"}])

    fact = FactAdvisoryTest.Facts.collect(test_instance).value

    assert FactAdvisoryTest.commands == [FakeCommandFact.commands[0]]
    assert isinstance(fact, AvailableFact)
    assert fact.value == FakeCommandFact("normalized")
    assert fact.source.name == "show fake"


def test_advisory_fact_fields_own_commands_and_collection(device: AntaDevice) -> None:
    """Derive commands and collect a field from its typed runtime declaration."""
    test_instance = FactsAdvisoryTest(device=device, eos_data=[{"value": "normalized"}])
    facts = FactsAdvisoryTest.Facts.collect(test_instance)

    assert FactsAdvisoryTest.commands == [FakeCommandFact.commands[0]]
    assert FactsAdvisoryTest.Facts.definitions() is FactsAdvisoryTest.Facts.definitions()
    assert FactsAdvisoryTest.Facts.definitions() == {"value": FakeCommandFact}
    collected = facts.value
    assert isinstance(collected, AvailableFact)
    assert collected == AvailableFact(value=FakeCommandFact("normalized"), source=FactSource("show fake", FactSourceKind.COMMAND))


def test_advisory_preserves_same_uid_commands_and_fact_association(device: AntaDevice) -> None:
    """Keep each fact's command wrapper and collected output when command UIDs match."""
    test_instance = SharedCommandAdvisoryTest(device=device, eos_data=[{"value": "required"}, {"value": "optional"}])

    facts = SharedCommandAdvisoryTest.Facts.collect(test_instance)
    required_fact = facts.required
    optional_fact = facts.optional

    assert len(SharedCommandAdvisoryTest.commands) == 2
    assert isinstance(SharedCommandAdvisoryTest.commands[0], AntaCommand)
    assert not isinstance(SharedCommandAdvisoryTest.commands[0], OptionalAntaCommand)
    assert isinstance(SharedCommandAdvisoryTest.commands[1], OptionalAntaCommand)
    assert isinstance(required_fact, AvailableFact)
    assert required_fact.value == RequiredSharedCommandFact("required")
    assert isinstance(optional_fact, AvailableFact)
    assert optional_fact.value == OptionalSharedCommandFact("optional")


@pytest.mark.asyncio
async def test_advisory_allows_metadata_only_facts(device: AntaDevice) -> None:
    """Run an advisory whose required fact is derived without collecting commands."""
    device.version = parse_eos_version("4.36.1F").unwrap()
    test_instance = MetadataFactAdvisoryTest(device=device, eos_data=[])

    await test_instance.test()

    assert not MetadataFactAdvisoryTest.commands
    assert isinstance(MetadataFactAdvisoryTest.Facts.collect(test_instance).version, AvailableFact)
    assert test_instance.result.result == "success"


def test_advisory_rejects_commands_outside_fact_fields() -> None:
    """Prevent advisory authors from bypassing fact-owned command declarations."""

    @facts_dataclass
    class Facts(FactsBase):
        """Typed facts required by the invalid advisory."""

        value: Fact[FakeCommandFact] = fact_field(FakeCommandFact)

    class_namespace: dict[str, Any] = {
        "__doc__": "Advisory that declares a command outside its fact container.",
        "Facts": Facts,
        "advisory": ADVISORY,
        "commands": [AntaCommand(command="show other")],
    }
    with pytest.raises(AttributeError, match="must declare commands through its nested Facts fields"):
        type("CommandsOutsideFactsAdvisoryTest", (_AntaAdvisoryTest,), class_namespace)


def test_non_advisory_result_has_no_metadata() -> None:
    """Verify advisory metadata remains optional for ordinary test results."""
    result = AntaTestResult(name="device", test="test", categories=["test"], description="Test description.")

    assert _get_advisory_metadata(result) is None
    assert "metadata" not in result.model_dump(mode="json", exclude_none=True)


def test_advisory_test_requires_metadata() -> None:
    """Verify each advisory test must declare its own metadata."""
    with pytest.raises(AttributeError, match="missing required class attribute: advisory"):

        class MissingAdvisoryTest(_AntaAdvisoryTest):
            """Advisory test without metadata."""

            Facts = FactAdvisoryTest.Facts

            @_AntaAdvisoryTest.anta_test
            def test(self) -> None:
                """Set the test result to success."""
                self.result.is_success()


def test_advisory_test_rejects_invalid_metadata() -> None:
    """Verify advisory metadata must use the private metadata model."""
    with pytest.raises(TypeError, match="must be an _AdvisoryMetadata instance"):

        class InvalidAdvisoryTest(_AntaAdvisoryTest):
            """Advisory test with invalid metadata."""

            Facts = FactAdvisoryTest.Facts
            advisory: ClassVar[_AdvisoryMetadata] = "invalid"  # type: ignore[assignment]

            @_AntaAdvisoryTest.anta_test
            def test(self) -> None:
                """Set the test result to success."""
                self.result.is_success()


def test_advisory_test_requires_fact_container() -> None:
    """Verify every advisory test declares a nested typed fact container."""
    with pytest.raises(TypeError, match="must define a nested Facts subclass of FactsBase"):

        class MissingFactsAdvisoryTest(_AntaAdvisoryTest):
            """Advisory test without a fact container."""

            advisory: ClassVar[_AdvisoryMetadata] = ADVISORY

            @_AntaAdvisoryTest.anta_test
            def test(self) -> None:
                """Set the test result to success."""
                self.result.is_success()


def test_advisory_test_requires_description() -> None:
    """Verify advisory tests must declare a description or docstring."""
    with pytest.raises(AttributeError, match="Cannot set the description"):

        class MissingDescriptionAdvisoryTest(_AntaAdvisoryTest):  # pylint: disable=missing-class-docstring
            Facts = FactAdvisoryTest.Facts
            advisory: ClassVar[_AdvisoryMetadata] = ADVISORY

            @_AntaAdvisoryTest.anta_test
            def test(self) -> None:
                """Set the test result to success."""
                self.result.is_success()


def test_advisory_test_normalizes_docstring_description() -> None:
    """Verify advisory descriptions use the first normalized docstring line."""
    normalized_description_test = type(
        "NormalizedDescriptionAdvisoryTest",
        (_AntaAdvisoryTest,),
        {
            "__doc__": "\n        Advisory description on the next line.\n\n            Additional indented details.\n        ",
            "advisory": ADVISORY,
            "Facts": FactAdvisoryTest.Facts,
        },
    )

    assert normalized_description_test.description == "Advisory description on the next line."


def test_advisory_test_preserves_explicit_identity() -> None:
    """Verify explicit names, descriptions, and categories are preserved."""

    class CustomAdvisoryTest(_AntaAdvisoryTest):
        """Advisory test with an explicit identity."""

        name: ClassVar[str] = "CustomAdvisoryName"
        description: ClassVar[str] = "Custom advisory description."
        categories: ClassVar[list[str]] = ["overridden"]
        Facts = FactAdvisoryTest.Facts
        advisory: ClassVar[_AdvisoryMetadata] = ADVISORY

        @_AntaAdvisoryTest.anta_test
        def test(self) -> None:
            """Set the test result to success."""
            self.result.is_success()

    assert CustomAdvisoryTest.name == "CustomAdvisoryName"
    assert CustomAdvisoryTest.description == "Custom advisory description."
    assert CustomAdvisoryTest.categories == ["overridden"]
