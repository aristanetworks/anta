# Copyright (c) 2026 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Arista EOS version parsing helpers."""

from __future__ import annotations

import re
from dataclasses import asdict, dataclass

EOS_VERSION_PATTERN = re.compile(
    r"^(?P<major>\d+)\.(?P<minor>\d+)\.(?P<patch>\d+)"
    r"(?:\.(?P<hotfix>\d+))?(?P<suffix>.*)$"
)


@dataclass(frozen=True)
class EOSVersion:
    """Normalized representation of an EOS release string."""

    major: int
    minor: int
    patch: int
    suffix: str = ""
    hotfix: int = 0

    def __str__(self) -> str:
        """Return the normalized EOS version string."""
        hotfix = f".{self.hotfix}" if self.hotfix else ""
        return f"{self.major}.{self.minor}.{self.patch}{hotfix}{self.suffix}"

    def to_dict(self) -> dict[str, str | int]:
        """Return the EOS version components as a JSON-compatible dictionary."""
        return asdict(self)


def parse_eos_version(version_string: str) -> EOSVersion | None:
    """Parse an EOS version into its numeric components and suffix."""
    match = EOS_VERSION_PATTERN.match(version_string.strip())
    if match is None:
        return None

    return EOSVersion(
        major=int(match.group("major")),
        minor=int(match.group("minor")),
        patch=int(match.group("patch")),
        suffix=match.group("suffix").strip(),
        hotfix=int(match.group("hotfix") or 0),
    )
