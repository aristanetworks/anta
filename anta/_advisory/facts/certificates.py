# Copyright (c) 2026 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Facts derived from EOS automatic certificate management settings."""

from __future__ import annotations

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


def _ca_update_setting(entry: object) -> FeatureState | FactProblemKind:
    """Read the configured CA retrieval flag independently of enrollment state."""
    if entry is None:
        return FactProblemKind.MISSING
    if not isinstance(entry, dict):
        return FactProblemKind.MALFORMED
    setting = entry.get("caCertificates")
    if setting is None:
        return FactProblemKind.MISSING
    if not isinstance(setting, str):
        return FactProblemKind.MALFORMED
    if setting in {"enabled", "disabled"}:
        return FeatureState(setting)
    return FactProblemKind.INVALID


def _any_ca_update(output: object) -> FeatureState | FactProblemKind:
    """Find any enabled EST setting without losing it to an unrelated entry error."""
    if output is None:
        return FactProblemKind.MISSING
    if not isinstance(output, dict):
        return FactProblemKind.MALFORMED
    profiles = output.get("profiles")
    if not isinstance(profiles, dict):
        return FactProblemKind.MISSING if profiles is None else FactProblemKind.MALFORMED
    settings = tuple(_ca_update_setting(entry) if isinstance(name, str) and name.strip() else FactProblemKind.MALFORMED for name, entry in profiles.items())
    if FeatureState.ENABLED in settings:
        return FeatureState.ENABLED
    for problem in (FactProblemKind.MALFORMED, FactProblemKind.INVALID, FactProblemKind.MISSING):
        if problem in settings:
            return problem
    return FeatureState.DISABLED


@dataclass(frozen=True, slots=True)
class EstCaCertificateAutoUpdateFact(FeatureFact, CommandsFactDefinition["EstCaCertificateAutoUpdateFact"]):
    """Whether any EST protocol instance has automatic CA retrieval enabled.

    This is an existential configuration property, not a report of successful
    CA retrieval or certificate enrollment. An enabled instance establishes it
    even when another instance has incomplete evidence. With no enabled witness,
    every instance must report disabled before the feature is known disabled.
    """

    feature: ClassVar[FeatureRef] = SubFeature(FeatureName.AUTO_CERTIFICATE, "EST CA certificate auto-update")
    key: ClassVar[str] = "feature.auto_certificate.est_ca_auto_update"
    label: ClassVar[str] = "EST CA certificate auto-update"
    commands: ClassVar[tuple[AntaCommand, ...]] = (
        OptionalAntaCommand(command="show management security auto-certificate protocol est detail", revision=1, defer_errors=True),
    )

    @classmethod
    def parse(cls, commands: tuple[AntaCommand, ...]) -> Fact[EstCaCertificateAutoUpdateFact]:
        """Normalize configured CA retrieval across the reported EST instances."""
        (command,) = commands
        source = FactSource(command.command, FactSourceKind.COMMAND)
        if is_unsupported_optional_command(command):
            return cls.unavailable(FactProblemKind.UNSUPPORTED, source)
        if command.errors:
            return cls.unavailable(FactProblemKind.COLLECTION_FAILED, source)
        setting = _any_ca_update(command.output)
        if isinstance(setting, FactProblemKind):
            return cls.unavailable(setting, source)
        return cls(setting).available(source)
