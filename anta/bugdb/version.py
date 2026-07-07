# Copyright (c) 2023-2026 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Version parsing and comparison for bug database matching.

Supports both EOS versions (``4.30.1F``) and TerminAttr versions
(``TerminAttr-v1.31.16`` from AlertBase, ``v1.17.0`` from device).
"""

from __future__ import annotations

import logging
import re
from functools import total_ordering
from typing import TYPE_CHECKING, ClassVar

if TYPE_CHECKING:
    from collections.abc import Callable

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


@total_ordering
class TerminAttrVersion:
    """Parsed TerminAttr version for comparison.

    Handles AlertBase format ``TerminAttr-v1.31.16`` and device
    format ``v1.17.0``. Train-based matching follows the same logic
    as EOS versions.
    """

    PATTERN: ClassVar[re.Pattern[str]] = re.compile(r"^(?:TerminAttr-)?[Vv]?(\d+)\.(\d+)(?:\.(\d+))?$")

    def __init__(self, version_str: str) -> None:
        self.raw = version_str
        m = self.PATTERN.match(version_str)
        if not m:
            msg = f"Cannot parse TerminAttr version: {version_str}"
            raise ValueError(msg)
        self.major = int(m.group(1))
        self.minor = int(m.group(2))
        self.patch = int(m.group(3)) if m.group(3) else 0

    @property
    def train(self) -> tuple[int, int]:
        """Version train (major, minor)."""
        return (self.major, self.minor)

    @property
    def _cmp_key(self) -> tuple[int, int, int]:
        return (self.major, self.minor, self.patch)

    def __eq__(self, other: object) -> bool:
        """Return True if two TerminAttrVersion instances have the same version components."""
        if not isinstance(other, TerminAttrVersion):
            return NotImplemented
        return self._cmp_key == other._cmp_key

    def __lt__(self, other: object) -> bool:
        """Return True if this version is lower than the other."""
        if not isinstance(other, TerminAttrVersion):
            return NotImplemented
        return self._cmp_key < other._cmp_key

    def __hash__(self) -> int:
        """Return hash based on the version components."""
        return hash(self._cmp_key)

    def __repr__(self) -> str:
        """Return a developer-friendly string representation."""
        return f"TerminAttrVersion({self.raw!r})"

    def __str__(self) -> str:
        """Return the raw version string."""
        return self.raw


def _parse_version_safe(version_str: str) -> EOSVersion | None:
    """Parse an EOS version string, returning None if unparsable."""
    try:
        return EOSVersion(version_str)
    except ValueError:
        return None


def _parse_terminattr_version_safe(version_str: str) -> TerminAttrVersion | None:
    """Parse a TerminAttr version string, returning None if unparsable."""
    try:
        return TerminAttrVersion(version_str)
    except ValueError:
        return None


def _is_nofixyet(version_str: str) -> bool:
    """Check if a version string is a 'nofixyet' sentinel (e.g. ``4.26.nofixyet``)."""
    return version_str.strip().endswith(f".{NOFIXYET_SUFFIX}")


def _extract_train(version_str: str) -> tuple[int, int] | None:
    """Extract the train (major, minor) from an EOS version string, even for nofixyet."""
    parts = version_str.split(".")
    if len(parts) >= 2:  # noqa: PLR2004
        try:
            return (int(parts[0]), int(parts[1]))
        except ValueError:
            return None
    return None


def _extract_terminattr_train(version_str: str) -> tuple[int, int] | None:
    """Extract the train (major, minor) from a TerminAttr version string, even for nofixyet."""
    stripped = re.sub(r"^(?:TerminAttr-)?[Vv]?", "", version_str)
    return _extract_train(stripped)


def _group_introduced_by_train(
    version_introduced: list[str],
    *,
    parser: Callable[[str], EOSVersion | TerminAttrVersion | None] = _parse_version_safe,
) -> dict[tuple[int, int], EOSVersion | TerminAttrVersion]:
    """Group introduced versions by train, keeping the earliest per train."""
    result: dict[tuple[int, int], EOSVersion | TerminAttrVersion] = {}
    for v_str in version_introduced:
        v = parser(v_str)
        if v is not None:
            train = v.train
            if train not in result or v < result[train]:
                result[train] = v
    return result


def _group_fixed_by_train(
    version_fixed: list[str],
    *,
    parser: Callable[[str], EOSVersion | TerminAttrVersion | None] = _parse_version_safe,
    train_extractor: Callable[[str], tuple[int, int] | None] = _extract_train,
) -> tuple[dict[tuple[int, int], EOSVersion | TerminAttrVersion], set[tuple[int, int]]]:
    """Group fixed versions by train and collect nofixyet trains."""
    fixed: dict[tuple[int, int], EOSVersion | TerminAttrVersion] = {}
    nofixyet: set[tuple[int, int]] = set()
    for v_str in version_fixed:
        if _is_nofixyet(v_str):
            train = train_extractor(v_str)
            if train is not None:
                nofixyet.add(train)
            continue
        v = parser(v_str)
        if v is not None:
            train = v.train
            if train not in fixed or v < fixed[train]:
                fixed[train] = v
    return fixed, nofixyet


def _check_direct_train(
    device_version: EOSVersion | TerminAttrVersion,
    device_train: tuple[int, int],
    introduced_v: EOSVersion | TerminAttrVersion,
    fixed_by_train: dict[tuple[int, int], EOSVersion | TerminAttrVersion],
    nofixyet_trains: set[tuple[int, int]],
) -> bool:
    """Check if affected when device train has a direct versionIntroduced entry."""
    if device_version < introduced_v:
        return False
    if device_train in nofixyet_trains:
        return True
    if device_train in fixed_by_train:
        return device_version < fixed_by_train[device_train]
    return True


def _check_earlier_train(
    device_version: EOSVersion | TerminAttrVersion,
    device_train: tuple[int, int],
    fixed_by_train: dict[tuple[int, int], EOSVersion | TerminAttrVersion],
    nofixyet_trains: set[tuple[int, int]],
) -> bool:
    """Check if affected when bug was introduced in an earlier train."""
    if device_train in nofixyet_trains:
        return True
    if device_train in fixed_by_train:
        return device_version < fixed_by_train[device_train]
    if any(t > device_train for t in fixed_by_train):
        return True
    latest_fix_train = max(fixed_by_train.keys()) if fixed_by_train else None
    return not (latest_fix_train is not None and latest_fix_train < device_train)


def is_version_affected(
    device_version: EOSVersion | TerminAttrVersion,
    version_introduced: list[str],
    version_fixed: list[str],
    *,
    version_parser: Callable[[str], EOSVersion | TerminAttrVersion | None] = _parse_version_safe,
    train_extractor: Callable[[str], tuple[int, int] | None] = _extract_train,
) -> bool:
    """Determine if a device running a given version is affected by a bug.

    Parameters
    ----------
    device_version
        The parsed version running on the device.
    version_introduced
        List of version strings where the bug was introduced.
    version_fixed
        List of version strings where the bug was fixed.
    version_parser
        Parser for version strings (defaults to EOS).
    train_extractor
        Train extractor for nofixyet versions (defaults to EOS).

    Returns
    -------
    bool
        True if the device version is in the affected range.
    """
    device_train = device_version.train
    introduced_by_train = _group_introduced_by_train(version_introduced, parser=version_parser)
    fixed_by_train, nofixyet_trains = _group_fixed_by_train(version_fixed, parser=version_parser, train_extractor=train_extractor)

    if device_train in introduced_by_train:
        return _check_direct_train(device_version, device_train, introduced_by_train[device_train], fixed_by_train, nofixyet_trains)

    if not any(t < device_train for t in introduced_by_train):
        return False

    return _check_earlier_train(device_version, device_train, fixed_by_train, nofixyet_trains)
