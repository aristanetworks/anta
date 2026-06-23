# Copyright (c) 2023-2026 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""EOS version parsing and comparison for bug database matching."""

from __future__ import annotations

import logging
import re
from functools import total_ordering
from typing import ClassVar

logger = logging.getLogger(__name__)

NOFIXYET_SUFFIX = "nofixyet"


@total_ordering
class EOSVersion:
    """Parsed EOS version for comparison.

    Handles standard versions like ``4.30.1F``, ``4.23.3.1M``,
    and platform-specific versions like ``4.16.6FX-7060X``.
    """

    PATTERN: ClassVar[re.Pattern[str]] = re.compile(r"^(\d+)\.(\d+)\.(\d+)(?:\.(\d+))?(?:\.(\d+))?([A-Za-z]*)(?:-.*)?$")

    def __init__(self, version_str: str) -> None:
        self.raw = version_str
        m = self.PATTERN.match(version_str)
        if not m:
            msg = f"Cannot parse EOS version: {version_str}"
            raise ValueError(msg)
        self.major = int(m.group(1))
        self.minor = int(m.group(2))
        self.patch = int(m.group(3))
        self.hotfix1 = int(m.group(4)) if m.group(4) else 0
        self.hotfix2 = int(m.group(5)) if m.group(5) else 0

    @property
    def train(self) -> tuple[int, int]:
        """Version train (major, minor)."""
        return (self.major, self.minor)

    @property
    def _cmp_key(self) -> tuple[int, int, int, int, int]:
        return (self.major, self.minor, self.patch, self.hotfix1, self.hotfix2)

    def same_train(self, other: EOSVersion) -> bool:
        """Check if two versions are in the same train."""
        return self.train == other.train

    def __eq__(self, other: object) -> bool:
        """Return True if two EOSVersion instances have the same version components."""
        if not isinstance(other, EOSVersion):
            return NotImplemented
        return self._cmp_key == other._cmp_key

    def __lt__(self, other: object) -> bool:
        """Return True if this version is lower than the other."""
        if not isinstance(other, EOSVersion):
            return NotImplemented
        return self._cmp_key < other._cmp_key

    def __hash__(self) -> int:
        """Return hash based on the version components."""
        return hash(self._cmp_key)

    def __repr__(self) -> str:
        """Return a developer-friendly string representation."""
        return f"EOSVersion({self.raw!r})"

    def __str__(self) -> str:
        """Return the raw version string."""
        return self.raw


def _parse_version_safe(version_str: str) -> EOSVersion | None:
    """Parse a version string, returning None if unparseable."""
    try:
        return EOSVersion(version_str)
    except ValueError:
        return None


def _is_nofixyet(version_str: str) -> bool:
    """Check if a version string is a 'nofixyet' sentinel."""
    return NOFIXYET_SUFFIX in version_str


def _extract_train(version_str: str) -> tuple[int, int] | None:
    """Extract the train (major, minor) from a version string, even for nofixyet."""
    parts = version_str.split(".")
    if len(parts) >= 2:  # noqa: PLR2004
        try:
            return (int(parts[0]), int(parts[1]))
        except ValueError:
            return None
    return None


def is_version_affected(device_version: EOSVersion, version_introduced: list[str], version_fixed: list[str]) -> bool:  # noqa: C901, PLR0911, PLR0912
    """Determine if a device running a given EOS version is affected by a bug.

    Parameters
    ----------
    device_version
        The parsed EOS version running on the device.
    version_introduced
        List of version strings where the bug was introduced.
    version_fixed
        List of version strings where the bug was fixed.

    Returns
    -------
    bool
        True if the device version is in the affected range.
    """
    device_train = device_version.train

    # Group introduced versions by train
    introduced_by_train: dict[tuple[int, int], EOSVersion] = {}
    for v_str in version_introduced:
        v = _parse_version_safe(v_str)
        if v is not None:
            train = v.train
            if train not in introduced_by_train or v < introduced_by_train[train]:
                introduced_by_train[train] = v

    # Group fixed versions by train, track nofixyet trains
    fixed_by_train: dict[tuple[int, int], EOSVersion] = {}
    nofixyet_trains: set[tuple[int, int]] = set()
    for v_str in version_fixed:
        if _is_nofixyet(v_str):
            train = _extract_train(v_str)
            if train is not None:
                nofixyet_trains.add(train)
            continue
        v = _parse_version_safe(v_str)
        if v is not None:
            train = v.train
            if train not in fixed_by_train or v < fixed_by_train[train]:
                fixed_by_train[train] = v

    # Case 1: device train has a direct versionIntroduced entry
    if device_train in introduced_by_train:
        introduced_v = introduced_by_train[device_train]
        if device_version < introduced_v:
            return False

        if device_train in nofixyet_trains:
            return True

        if device_train in fixed_by_train:
            return device_version < fixed_by_train[device_train]

        # Introduced in this train, no fix listed -> affected
        return True

    # Case 2: device train does NOT have a direct versionIntroduced entry
    # Check if bug was introduced in an earlier train
    earlier_trains = [t for t in introduced_by_train if t < device_train]
    if not earlier_trains:
        return False

    # Bug was introduced in an earlier train. Check if there's a fix for the device's train.
    if device_train in nofixyet_trains:
        return True

    if device_train in fixed_by_train:
        return device_version < fixed_by_train[device_train]

    # No fix entry for this train. Check if any fix exists in a later train,
    # which would imply this train is still affected.
    # If no fix exists in any train >= device_train, the bug is still present.
    later_fixes = [t for t in fixed_by_train if t > device_train]
    if later_fixes:
        return True

    # No fix in any later train either — check if the latest introduced train
    # is before our train and there are no fixes anywhere after it
    latest_fix_train = max(fixed_by_train.keys()) if fixed_by_train else None

    if latest_fix_train is not None and latest_fix_train < device_train:
        # All fixes are in trains before ours — the fix has been applied
        return False

    # Bug was introduced before our train, no fix for our train or later — likely affected
    return bool(earlier_trains)
