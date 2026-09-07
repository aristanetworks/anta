# Copyright (c) 2026 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Base class for ANTA security advisory tests."""

from __future__ import annotations

import sys
from typing import TYPE_CHECKING, Any, ClassVar, TypeVar

from anta._advisory.models import _AdvisoryMetadata
from anta._advisory.results import _AdvisoryTestResult
from anta.models import AntaCommand, AntaTemplate, AntaTest, _description_from_docstring

if sys.version_info >= (3, 12):
    from typing import override
else:
    from typing_extensions import override

if TYPE_CHECKING:
    from anta._advisory.facts.models import Fact, FactDefinition

T = TypeVar("T")


class _AntaAdvisoryTest(AntaTest):
    """Base class for ANTA security advisory tests."""

    # `_create_result` guarantees this narrower runtime type. Pyright cannot infer
    # an instance attribute's type from an overridden factory method.
    result: _AdvisoryTestResult  # pyright: ignore[reportIncompatibleVariableOverride]
    categories: ClassVar[list[str]] = ["advisories"]
    commands: ClassVar[list[AntaCommand | AntaTemplate]] = []
    required_facts: ClassVar[tuple[type[FactDefinition[Any]], ...]] = ()
    advisory: ClassVar[_AdvisoryMetadata]

    @override
    def _create_result(self) -> _AdvisoryTestResult:
        """Create a result with this test's advisory metadata."""
        return _AdvisoryTestResult(
            name=self.device.name,
            test=self.name,
            categories=self.categories,
            description=self.description,
            advisory=self.advisory,
        )

    def __init_subclass__(cls) -> None:
        """Derive commands, set subclass identity, and validate advisory attributes."""
        has_own_name = "name" in cls.__dict__
        has_own_description = "description" in cls.__dict__
        required_facts = cls.__dict__.get("required_facts", ())
        if required_facts:
            if "commands" in cls.__dict__:
                msg = f"Class {cls.__module__}.{cls.__name__} cannot define both 'required_facts' and 'commands'"
                raise AttributeError(msg)
            cls.commands = cls._commands_from_required_facts(required_facts)

        super().__init_subclass__()

        # AntaTest uses inherited attributes when resolving these values. Reset
        # them so each advisory subclass reflects its own class declaration.
        if not has_own_name:
            cls.name = cls.__name__
        if not has_own_description:
            cls.description = _description_from_docstring(cls.__doc__, cls.name)

        if "advisory" not in cls.__dict__:
            msg = f"Class {cls.__module__}.{cls.__name__} is missing required class attribute: advisory"
            raise AttributeError(msg)
        if not isinstance(cls.advisory, _AdvisoryMetadata):
            msg = f"Class {cls.__module__}.{cls.__name__} class attribute 'advisory' must be an _AdvisoryMetadata instance"
            raise TypeError(msg)
        if not cls.commands and not required_facts:
            msg = f"Class {cls.__module__}.{cls.__name__} must define at least one command or required fact"
            raise AttributeError(msg)

    @classmethod
    def _commands_from_required_facts(cls, required_facts: tuple[type[FactDefinition[Any]], ...]) -> list[AntaCommand | AntaTemplate]:
        """Return the commands needed by the required facts in declaration order."""
        return [command for definition in required_facts for command in definition.required_commands()]

    def fact(self, definition: type[FactDefinition[T]]) -> Fact[T]:
        """Derive one required fact from device metadata or collected command data."""
        command_offset = 0
        for candidate in self.required_facts:
            command_count = len(candidate.required_commands())
            if candidate is definition:
                commands = tuple(self.instance_commands[command_offset : command_offset + command_count])
                return definition.derive(self.device, commands)
            command_offset += command_count

        msg = f"Fact '{definition.key}' is not listed in required_facts for {self.__class__.__name__}"
        raise ValueError(msg)
