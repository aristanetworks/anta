# Copyright (c) 2026 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Typed results shared by defensive EOS parsers."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import TYPE_CHECKING, Generic, TypeAlias, TypeVar

if TYPE_CHECKING:
    from typing_extensions import Never

T = TypeVar("T")


class ParseFailureReason(str, Enum):
    """Reason an EOS value could not be collected or parsed."""

    COLLECTION_FAILED = "collection failed"
    MISSING = "missing"
    MALFORMED = "malformed"
    INVALID = "invalid"
    UNSUPPORTED = "unsupported"
    CONTRADICTORY = "contradictory"


class _ParseResult(Generic[T]):  # pylint: disable=too-few-public-methods
    """Base class for typed parser results."""

    __slots__ = ()

    @property
    def _value_or_none(self) -> T | None:
        """Return the parsed value held by the result, if any."""
        return None

    def unwrap_or_none(self) -> T | None:
        """Return the parsed value, or `None` for a parsing failure."""
        return self._value_or_none


@dataclass(frozen=True, slots=True)
class ParseSuccessful(_ParseResult[T], Generic[T]):
    """A successfully parsed EOS value."""

    value: T

    @property
    def _value_or_none(self) -> T:
        """Return the parsed value held by the result."""
        return self.value

    def unwrap(self) -> T:
        """Return the parsed value."""
        return self.value


@dataclass(frozen=True, slots=True)
class ParseFail(_ParseResult[None]):
    """An EOS value that could not be collected or parsed."""

    reason: ParseFailureReason
    detail: str

    def unwrap(self) -> Never:
        """Raise an error describing the parsing failure."""
        msg = f"{self.reason.value}: {self.detail}"
        raise ValueError(msg)


ParseResult: TypeAlias = ParseSuccessful[T] | ParseFail
