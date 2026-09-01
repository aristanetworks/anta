# Copyright (c) 2026 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Unit tests for the security advisory test base."""

from __future__ import annotations

import inspect
from typing import TYPE_CHECKING, Any, ClassVar

import pytest

from anta._advisory.base import _AntaAdvisoryTest
from anta._advisory.facts.models import AvailableFact, CommandFactDefinition, Fact, FactDefinition, FactSource, FactSourceKind
from anta._advisory.results import _AdvisoryTestResult, _get_advisory_metadata
from anta.models import AntaCommand, AntaTemplate, AntaTest
from anta.result_manager.models import TestResult as AntaTestResult
from tests.units._advisory.conftest import ADVISORY

if TYPE_CHECKING:
    from anta._advisory.models import _AdvisoryMetadata
    from anta.device import AntaDevice


class FakeAdvisoryTest(_AntaAdvisoryTest):
    """Fake security advisory test."""

    advisory: ClassVar[_AdvisoryMetadata] = ADVISORY
    commands: ClassVar[list[AntaCommand | AntaTemplate]] = [AntaCommand(command="show version")]

    @_AntaAdvisoryTest.anta_test
    def test(self) -> None:
        """Set the test result to success."""
        self.result.is_success()


class FakeCommandFact(CommandFactDefinition[str]):
    """Normalize one value from a fake JSON command."""

    key = "fake.value"
    label = "Fake value"
    command = AntaCommand(command="show fake", revision=1)

    @classmethod
    def parse(cls, command: AntaCommand) -> Fact[str]:
        """Return the fake value from the collected command."""
        return cls.available(str(command.json_output["value"]), FactSource(command.command, FactSourceKind.COMMAND))


class FactAdvisoryTest(_AntaAdvisoryTest):
    """Fake advisory test whose commands are derived from its required facts."""

    advisory: ClassVar[_AdvisoryMetadata] = ADVISORY
    required_facts: ClassVar[tuple[type[FactDefinition[Any]], ...]] = (FakeCommandFact,)

    @_AntaAdvisoryTest.anta_test
    def test(self) -> None:
        """Set the result from the normalized fact."""
        fact = self.fact(FakeCommandFact)
        self.result.is_success(str(fact))


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


def test_advisory_required_facts_own_commands_and_derivation(device: AntaDevice) -> None:
    """Derive class commands and typed facts from locally declared required facts."""
    test_instance = FactAdvisoryTest(device=device, eos_data=[{"value": "normalized"}])

    fact = test_instance.fact(FakeCommandFact)

    assert FactAdvisoryTest.commands == [FakeCommandFact.command]
    assert isinstance(fact, AvailableFact)
    assert fact.value == "normalized"
    assert fact.source.name == "show fake"


def test_advisory_rejects_undeclared_fact(device: AntaDevice) -> None:
    """Prevent a test from deriving facts outside its required facts."""

    class UndeclaredFact(FakeCommandFact):
        """Fact intentionally omitted from the fake advisory declaration."""

        key = "fake.other"
        label = "Other fake value"
        command = AntaCommand(command="show other")

    test_instance = FactAdvisoryTest(device=device, eos_data=[{"value": "normalized"}])

    with pytest.raises(ValueError, match="is not listed in required_facts"):
        test_instance.fact(UndeclaredFact)


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

            commands: ClassVar[list[AntaCommand | AntaTemplate]] = [AntaCommand(command="show version")]

            @_AntaAdvisoryTest.anta_test
            def test(self) -> None:
                """Set the test result to success."""
                self.result.is_success()


def test_advisory_test_rejects_invalid_metadata() -> None:
    """Verify advisory metadata must use the private metadata model."""
    with pytest.raises(TypeError, match="must be an _AdvisoryMetadata instance"):

        class InvalidAdvisoryTest(_AntaAdvisoryTest):
            """Advisory test with invalid metadata."""

            advisory: ClassVar[_AdvisoryMetadata] = "invalid"  # type: ignore[assignment]
            commands: ClassVar[list[AntaCommand | AntaTemplate]] = [AntaCommand(command="show version")]

            @_AntaAdvisoryTest.anta_test
            def test(self) -> None:
                """Set the test result to success."""
                self.result.is_success()


def test_advisory_test_requires_commands() -> None:
    """Verify advisory tests must collect evidence."""
    with pytest.raises(AttributeError, match="must define at least one command"):

        class MissingCommandsAdvisoryTest(_AntaAdvisoryTest):
            """Advisory test without commands."""

            advisory: ClassVar[_AdvisoryMetadata] = ADVISORY

            @_AntaAdvisoryTest.anta_test
            def test(self) -> None:
                """Set the test result to success."""
                self.result.is_success()


def test_advisory_test_requires_description() -> None:
    """Verify advisory tests must declare a description or docstring."""
    with pytest.raises(AttributeError, match="Cannot set the description"):

        class MissingDescriptionAdvisoryTest(_AntaAdvisoryTest):  # pylint: disable=missing-class-docstring
            advisory: ClassVar[_AdvisoryMetadata] = ADVISORY
            commands: ClassVar[list[AntaCommand | AntaTemplate]] = [AntaCommand(command="show version")]

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
            "commands": [AntaCommand(command="show version")],
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
        advisory: ClassVar[_AdvisoryMetadata] = ADVISORY
        commands: ClassVar[list[AntaCommand | AntaTemplate]] = [AntaCommand(command="show version")]

        @_AntaAdvisoryTest.anta_test
        def test(self) -> None:
            """Set the test result to success."""
            self.result.is_success()

    assert CustomAdvisoryTest.name == "CustomAdvisoryName"
    assert CustomAdvisoryTest.description == "Custom advisory description."
    assert CustomAdvisoryTest.categories == ["overridden"]
