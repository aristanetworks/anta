# Copyright (c) 2026 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Comparable non-EOS software version models used by advisory data."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True, order=True, slots=True)
class SemanticVersion:
    """Comparable stable semantic version with an optional display prefix."""

    major: int
    minor: int
    patch: int
    prefix: str = field(default="", compare=False)

    def __post_init__(self) -> None:
        if min(self.major, self.minor, self.patch) < 0:
            msg = "Semantic version components must be non-negative"
            raise ValueError(msg)
        if "\n" in self.prefix or "\r" in self.prefix:
            msg = "Semantic version prefixes must be single-line"
            raise ValueError(msg)

    def __str__(self) -> str:
        """Return the normalized semantic version string."""
        return f"{self.prefix}{self.major}.{self.minor}.{self.patch}"
