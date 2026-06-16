# Copyright (c) 2023-2026 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Module containing input models for configuration tests."""

from __future__ import annotations

from typing import TYPE_CHECKING, Literal

from pydantic import BaseModel, ConfigDict, model_validator

if TYPE_CHECKING:
    import sys

    if sys.version_info >= (3, 11):
        from typing import Self
    else:
        from typing_extensions import Self


class Threshold(BaseModel):
    """Numeric threshold for a regex-mode rule entry."""

    model_config = ConfigDict(extra="forbid")
    value: int
    """The bound to compare the captured value against."""
    operator: Literal["le", "ge", "eq"] = "eq"
    """Comparison operator: `le` (<=), `ge` (>=), `eq` (==). Defaults to `eq`."""


class RuleEntry(BaseModel):
    """A single check to validate within a resolved stanza or across top-level commands."""

    model_config = ConfigDict(extra="forbid")
    match: str
    """The string or pattern to match against commands in the resolved scope.

    For `regex` mode, standard regex syntax applies.
    """
    mode: Literal["exact", "contains", "regex"] = "exact"
    """Match mode. Defaults to `exact`.

    - `exact`: `match` must equal a command verbatim.
    - `contains`: At least one command must contain `match` as a substring.
    - `regex`: At least one command must match the pattern.
    """
    absent: bool = False
    """When `True`, the match must NOT be found. Defaults to `False` (match must be present)."""
    threshold: Threshold | None = None
    """Optional numeric threshold for `mode: regex`. The first capture group in `match`
    is extracted and compared against `value` using `operator`.
    """
    context: str | None = None
    """Optional custom failure message. Replaces the default failure text when set."""

    @model_validator(mode="after")
    def validate_threshold(self) -> Self:
        """Validate that `threshold` is only used with `mode: regex`."""
        if self.threshold is not None and self.mode != "regex":
            msg = "'mode' must be 'regex' when 'threshold' is set"
            raise ValueError(msg)
        return self


class ConfigRule(BaseModel):
    """A rule defining a stanza scope and the entries to validate within it."""

    model_config = ConfigDict(extra="forbid")
    stanza: list[str] | None = None
    """Stanza path as a list of patterns, or `None` for top-level commands.

    - `None` (omitted): validate against top-level running-config commands.
    - Single element: one level deep (e.g. `["management api http-commands"]`).
    - Multiple elements: navigate nested stanzas level-by-level
      (e.g. `["router bgp 65101", "vrf DEV"]`).

    Each element is matched exactly first; a regex fallback enables wildcard patterns
    when no exact key is found. Multiple matches each produce an independent atomic result.
    """
    description: str | None = None
    """Optional label for test result output. For wildcard rules, the matched stanza key
    is appended as `"<description> [<stanza>]"`.
    """
    entries: list[RuleEntry]
    """Entries to validate within the resolved stanza."""
