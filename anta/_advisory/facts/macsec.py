# Copyright (c) 2026 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""MACsec profile key-source and interface-binding observations without key material."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import TYPE_CHECKING, ClassVar

from anta._advisory.facts.models import CommandsFactDefinition, Fact, FactProblemKind, FactSource, FactSourceKind, UnavailableFact
from anta._advisory.optional_commands import OptionalAntaCommand, is_unsupported_optional_command

if TYPE_CHECKING:
    from anta.models import AntaCommand


@dataclass(frozen=True, slots=True)
class MacsecProfile:
    """A profile's source-qualified identity, configured key source, and bindings.

    ``None`` means EOS omitted the key-source field for an unconfigured key
    source. Explicit JSON null is malformed, rather than that default shape.
    """

    source: str
    name: str
    key_source: str | None
    interfaces: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class MacsecProfileProblem:
    """Incomplete profile evidence, retaining independently known scope."""

    source: str | None
    name: str | None
    interfaces: tuple[str, ...] | None
    key_source_known: bool
    key_source: str | None
    fact: UnavailableFact[MacsecProfilesFact]


@dataclass(frozen=True, slots=True)
class MacsecProfilesFact(CommandsFactDefinition["MacsecProfilesFact"]):
    """MACsec configuration observations from all reported profile sources.

    No cryptographic keys, key identifiers, hashes, session state, or assumed
    precedence between configuration sources are retained.
    """

    key: ClassVar[str] = "configuration.macsec.profiles"
    label: ClassVar[str] = "MACsec profile key sources and interface bindings"
    commands: ClassVar[tuple[AntaCommand, ...]] = (OptionalAntaCommand(command="show mac security profile", revision=1, defer_errors=True),)
    profiles: tuple[MacsecProfile, ...] = ()
    problems: tuple[MacsecProfileProblem, ...] = ()

    @classmethod
    # Keep individual source/profile failures scoped instead of failing the inventory.
    # pylint: disable-next=too-many-return-statements,too-many-branches
    def parse(cls, commands: tuple[AntaCommand, ...]) -> Fact[MacsecProfilesFact]:  # noqa: C901, PLR0911
        """Deserialize only the identity, key-source token, and interface list."""
        (command,) = commands
        source = FactSource(command.command, FactSourceKind.COMMAND)
        if is_unsupported_optional_command(command):
            return cls.unavailable(FactProblemKind.UNSUPPORTED, source)
        if command.errors:
            return cls.unavailable(FactProblemKind.COLLECTION_FAILED, source)
        output = command.output
        if output is None:
            return cls.unavailable(FactProblemKind.MISSING, source)
        if not isinstance(output, Mapping):
            return cls.unavailable(FactProblemKind.MALFORMED, source)
        if "sources" not in output:
            return cls.unavailable(FactProblemKind.MISSING, source)
        if not isinstance(output["sources"], Mapping):
            return cls.unavailable(FactProblemKind.MALFORMED, source)
        profiles: list[MacsecProfile] = []
        problems: list[MacsecProfileProblem] = []
        for origin, data in output["sources"].items():
            if not _name(origin):
                problems.append(
                    MacsecProfileProblem(
                        source=None,
                        name=None,
                        interfaces=None,
                        key_source_known=False,
                        key_source=None,
                        fact=cls.unavailable(FactProblemKind.MALFORMED, source),
                    )
                )
                continue
            if not isinstance(data, Mapping) or not isinstance(data.get("profiles"), Mapping):
                kind = FactProblemKind.MISSING if isinstance(data, Mapping) and "profiles" not in data else FactProblemKind.MALFORMED
                problems.append(
                    MacsecProfileProblem(
                        source=origin,
                        name=None,
                        interfaces=None,
                        key_source_known=False,
                        key_source=None,
                        fact=cls.unavailable(kind, source),
                    )
                )
                continue
            for name, data_profile in data["profiles"].items():
                if not _name(name):
                    problems.append(
                        MacsecProfileProblem(
                            source=origin,
                            name=None,
                            interfaces=None,
                            key_source_known=False,
                            key_source=None,
                            fact=cls.unavailable(FactProblemKind.MALFORMED, source),
                        )
                    )
                    continue
                profile, profile_problems = _profile(origin, name, data_profile, source)
                if profile is not None:
                    profiles.append(profile)
                problems.extend(profile_problems)
        return cls(tuple(profiles), tuple(problems)).available(source)


def _name(value: object) -> bool:
    """Require a nonempty, unpadded source/profile/interface identifier."""
    return isinstance(value, str) and bool(value) and value.strip() == value


def _profile(origin: str, name: str, data: object, source: FactSource) -> tuple[MacsecProfile | None, tuple[MacsecProfileProblem, ...]]:
    """Preserve valid bindings alongside incomplete coverage of one profile."""
    if not isinstance(data, Mapping):
        problem = MacsecProfileProblem(
            source=origin,
            name=name,
            interfaces=None,
            key_source_known=False,
            key_source=None,
            fact=MacsecProfilesFact.unavailable(FactProblemKind.MALFORMED, source),
        )
        return None, (problem,)
    key_source = data.get("primaryKeySource")
    key_known = "primaryKeySource" not in data or (isinstance(key_source, str) and bool(key_source) and key_source.strip() == key_source)
    entries = data.get("interfaces")
    interfaces = tuple(item for item in entries if _name(item)) if isinstance(entries, list) else None
    # Duplicate bindings retain their existing malformed-list interpretation.
    if interfaces is not None and len(set(interfaces)) != len(interfaces):
        interfaces = None
    partial = isinstance(entries, list) and interfaces is not None and len(interfaces) != len(entries)
    kind = FactProblemKind.MISSING if "interfaces" not in data else FactProblemKind.MALFORMED
    problem = MacsecProfileProblem(
        origin, name, None if partial else interfaces, key_known, key_source if key_known else None, MacsecProfilesFact.unavailable(kind, source)
    )
    if interfaces is None:
        return None, (problem,)
    if not key_known:
        if partial and interfaces:
            # Unknown coverage must not hide contradictory evidence at a known binding.
            scoped = MacsecProfileProblem(origin, name, interfaces, key_source_known=False, key_source=None, fact=problem.fact)
            return None, (scoped, problem)
        return None, (problem,)
    profile = MacsecProfile(origin, name, key_source, interfaces)
    return profile, (problem,) if partial else ()
