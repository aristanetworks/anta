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

    from anta.device import DeviceVersion


def _matches_bounds(
    value: int,
    *,
    exact: int | None = None,
    less_than: int | None = None,
    less_than_or_equal: int | None = None,
    greater_than: int | None = None,
    greater_than_or_equal: int | None = None,
) -> bool:
    """Return whether one numeric version component satisfies every bound."""
    return (
        (exact is None or value == exact)
        and (less_than is None or value < less_than)
        and (less_than_or_equal is None or value <= less_than_or_equal)
        and (greater_than is None or value > greater_than)
        and (greater_than_or_equal is None or value >= greater_than_or_equal)
    )


@dataclass(frozen=True)
class VersionRule:  # pylint: disable=too-many-instance-attributes
    """Declarative affected-version rule for a security advisory."""

    major: int
    minor: int | None = None
    minor_lt: int | None = None
    minor_lte: int | None = None
    minor_gt: int | None = None
    minor_gte: int | None = None
    patch_eq: int | None = None
    patch_lt: int | None = None
    patch_lte: int | None = None
    patch_gt: int | None = None
    patch_gte: int | None = None
    hotfix_eq: int | None = None
    hotfix_lt: int | None = None
    hotfix_lte: int | None = None
    hotfix_gt: int | None = None
    hotfix_gte: int | None = None
    require_suffixes: tuple[str, ...] = ()
    exclude_suffixes: tuple[str, ...] = ()

    def matches(self, version: EOSVersion) -> bool:
        """Return True when the EOS version falls in this rule's affected range."""
        return (
            version.major == self.major
            and _matches_bounds(
                version.minor,
                exact=self.minor,
                less_than=self.minor_lt,
                less_than_or_equal=self.minor_lte,
                greater_than=self.minor_gt,
                greater_than_or_equal=self.minor_gte,
            )
            and _matches_bounds(
                version.patch,
                exact=self.patch_eq,
                less_than=self.patch_lt,
                less_than_or_equal=self.patch_lte,
                greater_than=self.patch_gt,
                greater_than_or_equal=self.patch_gte,
            )
            and _matches_bounds(
                version.hotfix,
                exact=self.hotfix_eq,
                less_than=self.hotfix_lt,
                less_than_or_equal=self.hotfix_lte,
                greater_than=self.hotfix_gt,
                greater_than_or_equal=self.hotfix_gte,
            )
            and (not self.require_suffixes or version.suffix in self.require_suffixes)
            and (not self.exclude_suffixes or version.suffix not in self.exclude_suffixes)
        )


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


def evaluate_version(
    device_version: DeviceVersion | None,
    version_matrix: Sequence[VersionRule],
) -> VersionEvaluation:
    """Evaluate the EOS version from refreshed device metadata."""
    if device_version is None:
        return VersionEvaluation(None, AffectedStatus.UNKNOWN)

    version_string = str(device_version)
    version = device_version if isinstance(device_version, EOSVersion) else parse_eos_version(version_string).unwrap_or_none()
    if version is None:
        return VersionEvaluation(version_string, AffectedStatus.UNKNOWN)
    if any(rule.matches(version) for rule in version_matrix):
        return VersionEvaluation(version_string, AffectedStatus.AFFECTED)
    return VersionEvaluation(version_string, AffectedStatus.NOT_AFFECTED)
