# Copyright (c) 2023-2026 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Module containing input models for configuration tests."""

from __future__ import annotations

import re
from typing import TYPE_CHECKING, Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

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
    def validate_entry(self) -> Self:
        """Validate regex syntax for regex mode entries and all threshold constraints."""
        if self.threshold is not None:
            if self.absent:
                msg = "'absent' must be 'false' when 'threshold' is set"
                raise ValueError(msg)
            if self.mode != "regex":
                msg = "'mode' must be 'regex' when 'threshold' is set"
                raise ValueError(msg)
        if self.mode == "regex":
            try:
                compiled = re.compile(self.match)
            except re.error as e:
                msg = f"'match' is not a valid regular expression: {e}"
                raise ValueError(msg) from e
            if self.threshold is not None and compiled.groups == 0:
                msg = "'match' must have a capture group when 'threshold' is set"
                raise ValueError(msg)
        return self


class ConfigRule(BaseModel):
    """A rule defining a stanza scope and the entries to validate within it."""

    model_config = ConfigDict(extra="forbid")
    stanza: Annotated[list[Annotated[str, Field(min_length=1)]], Field(min_length=1)] | None = None
    """Stanza path as a list of patterns, or `None` for top-level commands.

    - `None` (omitted): validate against top-level running-config commands. Note that
      top-level keys include both flat commands (e.g. `"ip routing"`) and stanza header
      lines (e.g. `"router bgp 65101"`), so a `contains` match for `"bgp"` will match
      the stanza header itself.
    - Single element: one level deep (e.g. `["management api http-commands"]`).
    - Multiple elements: navigate nested stanzas level-by-level
      (e.g. `["router bgp 65101", "vrf DEV"]`).

    Each element is matched exactly first; if no exact key exists, the element is treated
    as a regex and matched against all keys using full-string matching (both ends anchored).
    Multiple matches each produce an independent atomic result.
    """
    description: str | None = None
    """Optional label for test result output. For wildcard rules, the matched stanza key
    is appended as `"<description> [<stanza>]"`.
    """
    entries: list[RuleEntry]
    """Entries to validate within the resolved stanza."""

    @field_validator("stanza", mode="after")
    @classmethod
    def validate_stanza_regex(cls, value: list[str] | None) -> list[str] | None:
        """Validate each stanza pattern is a valid regular expression."""
        try:
            for pattern in value or []:
                re.compile(pattern)
        except re.error as e:
            msg = f"Stanza pattern '{e.pattern}' is not a valid regular expression: {e}"
            raise ValueError(msg) from e
        return value
