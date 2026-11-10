# Copyright (c) 2026 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Facts derived from EOS adaptive virtual topology configuration state."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import TYPE_CHECKING, ClassVar

from anta._advisory.facts.models import (
    CommandsFactDefinition,
    Fact,
    FactProblemKind,
    FactSource,
    FactSourceKind,
    FeatureFact,
    FeatureName,
    FeatureRef,
    FeatureState,
    SubFeature,
)
from anta._advisory.optional_commands import OptionalAntaCommand, is_unsupported_optional_command

if TYPE_CHECKING:
    from anta.models import AntaCommand


class AvtRole(str, Enum):
    """Roles reported by the adaptive virtual topology path command."""

    PATHFINDER = "pathfinder"
    EDGE = "edge"
    ZONE_TRANSIT = "zone transit"
    REGION_TRANSIT = "region transit"
    UNKNOWN = "unknown"


def _parse_role(output: object) -> AvtRole | FactProblemKind:
    """Validate a successful JSON response without defaulting an absent role."""
    if output is None:
        return FactProblemKind.MISSING
    if not isinstance(output, dict):
        return FactProblemKind.MALFORMED
    role = output.get("role")
    if role is None:
        return FactProblemKind.MISSING
    if not isinstance(role, str):
        return FactProblemKind.MALFORMED
    try:
        return AvtRole(role)
    except ValueError:
        return FactProblemKind.INVALID


@dataclass(frozen=True, slots=True)
class PathfinderRoleFact(FeatureFact, CommandsFactDefinition["PathfinderRoleFact"]):
    """Device-wide Pathfinder role, independent of live paths or BGP sessions.

    A successfully reported ``unknown`` is a valid non-Pathfinder role. An
    unconfigured AVT command error is unavailable evidence, not that role.
    """

    role: AvtRole
    state: FeatureState = field(init=False)
    feature: ClassVar[FeatureRef] = SubFeature(FeatureName.PATHFINDER, "role")
    key: ClassVar[str] = "feature.avt.pathfinder_role"
    label: ClassVar[str] = "Pathfinder role"
    commands: ClassVar[tuple[AntaCommand, ...]] = (OptionalAntaCommand(command="show adaptive-virtual-topology path", revision=1, defer_errors=True),)

    def __post_init__(self) -> None:
        """Derive role membership without consulting transient path state."""
        object.__setattr__(self, "state", FeatureState.ENABLED if self.role is AvtRole.PATHFINDER else FeatureState.DISABLED)

    @classmethod
    def parse(cls, commands: tuple[AntaCommand, ...]) -> Fact[PathfinderRoleFact]:
        """Normalize the required top-level role field from structured output."""
        (command,) = commands
        source = FactSource(command.command, FactSourceKind.COMMAND)
        if is_unsupported_optional_command(command):
            return cls.unavailable(FactProblemKind.UNSUPPORTED, source)
        if command.errors:
            return cls.unavailable(FactProblemKind.COLLECTION_FAILED, source)
        parsed = _parse_role(command.output)
        if isinstance(parsed, FactProblemKind):
            return cls.unavailable(parsed, source)
        return cls(parsed).available(source)
