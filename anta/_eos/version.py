# Copyright (c) 2026 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Arista EOS version parsing helpers."""

from __future__ import annotations

import re
from dataclasses import asdict, dataclass
from functools import total_ordering

from anta._eos.parsing import ParseFail, ParseFailureReason, ParseResult, ParseSuccessful

EOS_VERSION_PATTERN = re.compile(
    r"^(?P<major>\d+)\.(?P<minor>\d+)\.(?P<patch>\d+)"
    r"(?:\.(?P<hotfix>\d+))?(?P<suffix>.*)$"
)


@total_ordering
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

    def __lt__(self, other: object) -> bool:
        """Order EOS versions by numeric release components and then suffix."""
        if not isinstance(other, EOSVersion):
            return NotImplemented
        return (self.major, self.minor, self.patch, self.hotfix, self.suffix) < (
            other.major,
            other.minor,
            other.patch,
            other.hotfix,
            other.suffix,
        )

    def to_dict(self) -> dict[str, str | int]:
        """Return the EOS version components as a JSON-compatible dictionary."""
        return asdict(self)


def parse_eos_version(version_value: object) -> ParseResult[EOSVersion]:
    """Parse an EOS version into its numeric components and suffix.

    Parameters
    ----------
    version_value : object
        Raw EOS version value.

    Returns
    -------
    ParseResult[EOSVersion]
        The normalized EOS version or a typed parsing failure.
    """
    if version_value is None:
        return ParseFail(ParseFailureReason.MISSING, "EOS version is missing")
    if not isinstance(version_value, str):
        return ParseFail(ParseFailureReason.MALFORMED, "EOS version is not a string")

    version_string = version_value.strip()
    if not version_string:
        return ParseFail(ParseFailureReason.INVALID, "EOS version is empty")

    match = EOS_VERSION_PATTERN.match(version_string)
    if match is None:
        return ParseFail(ParseFailureReason.INVALID, "EOS version has an invalid format")

    return ParseSuccessful(
        EOSVersion(
            major=int(match.group("major")),
            minor=int(match.group("minor")),
            patch=int(match.group("patch")),
            suffix=match.group("suffix").strip(),
            hotfix=int(match.group("hotfix") or 0),
        )
    )
