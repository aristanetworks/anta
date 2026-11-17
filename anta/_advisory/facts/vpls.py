# Copyright (c) 2026 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Presence of local BGP VPLS signaling instances."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
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


def _instance_state(output: Mapping[str, object]) -> FeatureState | FactProblemKind:
    """Read only the local instance identities, leaving their contents opaque."""
    instances = output.get("instances")
    if instances is None:
        return FactProblemKind.MISSING
    if not isinstance(instances, Mapping):
        return FactProblemKind.MALFORMED
    if any(isinstance(name, str) and name and isinstance(instance, Mapping) for name, instance in instances.items()):
        return FeatureState.ENABLED
    return FactProblemKind.MALFORMED if instances else FeatureState.DISABLED


@dataclass(frozen=True, slots=True)
class BgpVplsSignalingInstanceFact(FeatureFact, CommandsFactDefinition["BgpVplsSignalingInstanceFact"]):
    """Whether EOS reports any local BGP VPLS signaling instance.

    This is a point-in-time observation, independent of remote peers and labels.
    Successful empty instance output means disabled, including during convergence;
    persistent configuration is not collected or inferred.
    """

    feature: ClassVar[FeatureRef] = SubFeature(FeatureName.BGP, "VPLS signaling")
    key: ClassVar[str] = "feature.bgp.vpls_signaling.instances"
    label: ClassVar[str] = "BGP VPLS signaling instance presence"
    commands: ClassVar[tuple[AntaCommand, ...]] = (OptionalAntaCommand(command="show bgp vpls signaling", revision=1, defer_errors=True),)

    @classmethod
    def parse(cls, commands: tuple[AntaCommand, ...]) -> Fact[BgpVplsSignalingInstanceFact]:
        """Observe instance presence without discarding valid independent entries."""
        (command,) = commands
        source = FactSource(command.command, FactSourceKind.COMMAND)
        if command.error:
            problem = FactProblemKind.UNSUPPORTED if is_unsupported_optional_command(command) else FactProblemKind.COLLECTION_FAILED
            return cls.unavailable(problem, source)
        if command.output is None:
            return cls.unavailable(FactProblemKind.MISSING, source)
        if not isinstance(command.output, dict):
            return cls.unavailable(FactProblemKind.MALFORMED, source)
        state = _instance_state(command.output)
        return cls.unavailable(state, source) if isinstance(state, FactProblemKind) else cls(state).available(source)
