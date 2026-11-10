# Copyright (c) 2026 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Facts derived from EOS Precision Time Protocol state."""

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
)
from anta._advisory.optional_commands import OptionalAntaCommand, is_unsupported_optional_command

if TYPE_CHECKING:
    from anta.models import AntaCommand

PTP_COMMAND = OptionalAntaCommand(command="show ptp", revision=2, defer_errors=True)


def _global_ptp_state(output: dict[str, object] | str | None) -> FeatureState | FactProblemKind:
    """Validate revision-2 JSON; every non-disabled mode establishes enablement."""
    if not isinstance(output, dict):
        return FactProblemKind.MISSING if output is None else FactProblemKind.MALFORMED
    summaries = output.get("ptpIntfSummaries")
    if not isinstance(summaries, Mapping):
        return FactProblemKind.MISSING if "ptpIntfSummaries" not in output else FactProblemKind.MALFORMED
    if "ptpMode" not in output and summaries:
        return FactProblemKind.MISSING
    mode = output.get("ptpMode", "ptpDisabled")
    if not isinstance(mode, str):
        return FactProblemKind.MALFORMED
    if not mode.strip():
        return FactProblemKind.INVALID
    return FeatureState.DISABLED if mode == "ptpDisabled" else FeatureState.ENABLED


@dataclass(frozen=True, slots=True)
class PtpGlobalFact(FeatureFact, CommandsFactDefinition["PtpGlobalFact"]):
    """Global PTP mode, independently of interface and clock operational state."""

    feature: ClassVar[FeatureRef] = FeatureName.PTP
    key: ClassVar[str] = "feature.ptp.global"
    label: ClassVar[str] = "global PTP state"
    commands: ClassVar[tuple[AntaCommand, ...]] = (PTP_COMMAND,)

    @classmethod
    def parse(cls, commands: tuple[AntaCommand, ...]) -> Fact[PtpGlobalFact]:
        """Normalize explicit and omitted disabled-mode variants of revision-2 JSON."""
        (command,) = commands
        source = FactSource(command.command, FactSourceKind.COMMAND)
        if is_unsupported_optional_command(command):
            return cls.unavailable(FactProblemKind.UNSUPPORTED, source)
        if command.errors:
            return cls.unavailable(FactProblemKind.COLLECTION_FAILED, source)
        state = _global_ptp_state(command.output)
        if isinstance(state, FactProblemKind):
            return cls.unavailable(state, source)
        return cls(state).available(source)
