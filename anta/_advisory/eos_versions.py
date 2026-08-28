# Copyright (c) 2026 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Affected EOS version helpers for security advisory tests."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import TYPE_CHECKING

from anta._eos.version import EOSVersion, parse_eos_version

if TYPE_CHECKING:
    from collections.abc import Sequence
    from typing import Any

    from anta.result_manager.models import TestResult


@dataclass(frozen=True)
class VersionRule:
    """Declarative affected-version rule for a security advisory."""

    major: int
    minor: int
    patch_eq: int | None = None
    patch_lt: int | None = None
    patch_gte: int | None = None
    exclude_suffixes: tuple[str, ...] = ()

    def matches(self, version: EOSVersion) -> bool:
        """Return True when the EOS version falls in this rule's affected range."""
        if version.major != self.major or version.minor != self.minor:
            return False
        if self.patch_eq is not None and version.patch != self.patch_eq:
            return False
        if self.patch_lt is not None and version.patch >= self.patch_lt:
            return False
        if self.patch_gte is not None and version.patch < self.patch_gte:
            return False
        return not self.exclude_suffixes or version.suffix not in self.exclude_suffixes


class AffectedStatus(Enum):
    """Result of evaluating an EOS version rule."""

    UNKNOWN = 0
    NOT_AFFECTED = 1
    AFFECTED = 2


@dataclass(frozen=True)
class VersionEvaluation:
    """Result of evaluating an EOS version against an affected-version matrix."""

    version: str | None
    affected_status: AffectedStatus


def evaluate_version(show_version_output: dict[str, Any], version_matrix: Sequence[VersionRule]) -> VersionEvaluation:
    """Evaluate whether the EOS version falls into an affected advisory range."""
    value = show_version_output.get("version")
    version_string = value.strip() if isinstance(value, str) and value.strip() else None
    if version_string is None:
        return VersionEvaluation(None, AffectedStatus.UNKNOWN)

    version = parse_eos_version(version_string)
    if version is None:
        return VersionEvaluation(version_string, AffectedStatus.UNKNOWN)
    if any(rule.matches(version) for rule in version_matrix):
        return VersionEvaluation(version_string, AffectedStatus.AFFECTED)
    return VersionEvaluation(version_string, AffectedStatus.NOT_AFFECTED)


def require_affected_version(
    result: TestResult,
    messages: list[str],
    show_version_output: dict[str, Any],
    version_matrix: Sequence[VersionRule],
) -> bool:
    """Continue only for an affected EOS version; otherwise set a terminal result."""
    evaluation = evaluate_version(show_version_output, version_matrix)

    if evaluation.affected_status is AffectedStatus.NOT_AFFECTED:
        messages.append(f"The EOS version '{evaluation.version}' is not affected by this advisory.")
        result.is_success("\n".join(messages))
        return False
    if evaluation.affected_status is AffectedStatus.UNKNOWN:
        messages.append("The EOS version could not be determined from the 'show version' command output.")
        result.is_error("\n".join(messages))
        return False

    messages.append(f"The EOS version '{evaluation.version}' is affected by this advisory.")
    return True
