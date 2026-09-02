# Copyright (c) 2026 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Typed results shared by defensive EOS parsers."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Generic, TypeAlias, TypeVar

T = TypeVar("T")


class ParseFailureReason(str, Enum):
    """Reason an EOS value could not be collected or parsed."""

    COLLECTION_FAILED = "collection failed"
    MISSING = "missing"
    MALFORMED = "malformed"
    INVALID = "invalid"
    UNSUPPORTED = "unsupported"
    CONTRADICTORY = "contradictory"


@dataclass(frozen=True, slots=True)
class ParseSuccessful(Generic[T]):
    """A successfully parsed EOS value."""

    value: T


@dataclass(frozen=True, slots=True)
class ParseFail:
    """An EOS value that could not be collected or parsed."""

    reason: ParseFailureReason
    detail: str


ParseResult: TypeAlias = ParseSuccessful[T] | ParseFail
