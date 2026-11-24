# Copyright (c) 2026 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Persistent Ethernet interface speed configuration, including EOS defaults."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import TYPE_CHECKING, ClassVar

from anta._advisory.facts.models import (
    CommandsFactDefinition,
    Fact,
    FactProblemKind,
    FactSource,
    FactSourceKind,
    UnavailableFact,
)
from anta._advisory.optional_commands import OptionalAntaCommand, is_unsupported_optional_command

if TYPE_CHECKING:
    from anta.models import AntaCommand

_ETHERNET = re.compile(r"Ethernet\d+(?:/\d+){0,2}")
_SUBINTERFACE = re.compile(r"Ethernet\d+(?:/\d+){0,2}\.\d+")
_SPEED = r"(?:[1-9]\d*(?:\.\d+)?[gm](?:full|half)?(?:-[1-9]\d*)?|[1-9]\d*(?:full|half))"
_CONSTRAINED = re.compile(rf"speed (?:(?:auto|forced) )?{_SPEED}(?:[ ,]+{_SPEED})*")


@dataclass(frozen=True, slots=True)
class InterfaceSpeed:
    """One physical Ethernet interface's literal effective configured speed."""

    interface: str
    configuration: str

    @property
    def slot(self) -> str | None:
        """Return the modular slot, leaving fixed-system ports uncorrelated."""
        return self.interface.split("/", 1)[0].removeprefix("Ethernet") if "/" in self.interface else None


@dataclass(frozen=True, slots=True)
class InterfaceSpeedProblem:
    """One representative unavailable speed observation in a known slot."""

    slot: str | None
    fact: UnavailableFact[InterfaceSpeedFact]


@dataclass(frozen=True, slots=True)
class InterfaceSpeedFact(CommandsFactDefinition["InterfaceSpeedFact"]):
    """Scoped observations, retaining one interface per slot and distinct speed setting.

    Problems retain incomplete evidence; availability does not establish coverage
    or classify any speed setting as an exposure condition.
    """

    key: ClassVar[str] = "configuration.interfaces.speed"
    label: ClassVar[str] = "Ethernet interface speed configuration"
    # Interpret all failures as unavailable observations so an independently fixed
    # version or excluded platform can still establish absence of exposure.
    # EOS rejects "all sanitized section"; "sanitized" must precede "all" here.
    commands: ClassVar[tuple[AntaCommand, ...]] = (
        OptionalAntaCommand(command="show running-config sanitized all section ^interface", ofmt="text", defer_errors=True),
    )
    interfaces: tuple[InterfaceSpeed, ...]
    problems: tuple[InterfaceSpeedProblem, ...] = ()

    @classmethod
    def from_interfaces(cls, interfaces: tuple[InterfaceSpeed, ...]) -> InterfaceSpeedFact:
        """Keep a representative of each literal speed setting within each slot."""
        settings: dict[tuple[str | None, str], InterfaceSpeed] = {}
        for item in interfaces:
            settings.setdefault((item.slot, item.configuration), item)
        return cls(interfaces=tuple(settings.values()))

    @classmethod
    def parse(cls, commands: tuple[AntaCommand, ...]) -> Fact[InterfaceSpeedFact]:
        """Read exact speed lines under physical Ethernet interface sections."""
        command = commands[0]
        source = FactSource(command.command, FactSourceKind.COMMAND)
        if is_unsupported_optional_command(command):
            return cls.unavailable(FactProblemKind.UNSUPPORTED, source)
        if command.errors:
            return cls.unavailable(FactProblemKind.COLLECTION_FAILED, source)
        if not isinstance(command.output, str):
            return cls.unavailable(FactProblemKind.MALFORMED, source)
        return _parse_output(command.output, source)


def _interface_sections(output: str, source: FactSource) -> dict[str, list[str]] | UnavailableFact[InterfaceSpeedFact]:
    """Keep direct configuration lines grouped by physical Ethernet interface."""
    sections: dict[str, list[str]] = {}
    current: str | None = None
    for line in output.splitlines():
        if line.startswith("interface "):
            name = line.removeprefix("interface ").strip()
            if name.startswith("Ethernet") and not (_ETHERNET.fullmatch(name) or _SUBINTERFACE.fullmatch(name)):
                return InterfaceSpeedFact.unavailable(FactProblemKind.MALFORMED, source)
            current = name if _ETHERNET.fullmatch(name) else None
            if current is not None:
                if current in sections:
                    return InterfaceSpeedFact.unavailable(FactProblemKind.MALFORMED, source)
                sections[current] = []
        elif current is not None and line.startswith("   ") and not line.startswith("    "):
            if line.strip().startswith(("no speed", "speed ")):
                sections[current].append(line.strip())
        elif line and not line[0].isspace() and line != "!":
            current = None
    return sections


def _section_speed(name: str, lines: list[str], source: FactSource) -> InterfaceSpeed | UnavailableFact[InterfaceSpeedFact]:
    """Validate the complete speed observation in one physical interface section."""
    speeds: list[str] = [line for line in lines if line.startswith(("no speed", "speed "))]
    if not speeds:
        return InterfaceSpeedFact.unavailable(FactProblemKind.MISSING, source)
    if any(speed not in {"no speed", "speed auto"} and not _CONSTRAINED.fullmatch(speed) for speed in speeds):
        return InterfaceSpeedFact.unavailable(FactProblemKind.MALFORMED, source)
    if len(speeds) > 1:
        if speeds[0] == speeds[1]:
            return InterfaceSpeedFact.unavailable(FactProblemKind.MALFORMED, source)
        observations = tuple(InterfaceSpeedFact.from_interfaces((InterfaceSpeed(name, speed),)) for speed in speeds[:2])
        return InterfaceSpeedFact.unavailable(FactProblemKind.CONTRADICTORY, source, observations=observations)
    return InterfaceSpeed(name, speeds[0])


def _parse_output(output: str, source: FactSource) -> Fact[InterfaceSpeedFact]:
    """Normalize validated interface sections into the nominal speed fact."""
    sections = _interface_sections(output, source)
    if isinstance(sections, UnavailableFact):
        return sections
    if not sections:
        return InterfaceSpeedFact.unavailable(FactProblemKind.MISSING, source)
    interfaces: dict[tuple[str | None, str], InterfaceSpeed] = {}
    problems: dict[str | None, InterfaceSpeedProblem] = {}
    for name, lines in sections.items():
        slot = InterfaceSpeed(name, "").slot
        speed = _section_speed(name, lines, source)
        if isinstance(speed, UnavailableFact):
            problems.setdefault(slot, InterfaceSpeedProblem(slot, speed))
        else:
            interfaces.setdefault((slot, speed.configuration), speed)
    return InterfaceSpeedFact(tuple(interfaces.values()), tuple(problems.values())).available(source)
