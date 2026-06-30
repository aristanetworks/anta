# Copyright (c) 2023-2026 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Module containing input models for configuration tests."""

from __future__ import annotations

import re
from typing import TYPE_CHECKING, Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from anta.custom_types import RegexString

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
    """Comparison operator."""

    def evaluate(self, captured: int) -> bool:
        """Return True if `captured` satisfies this threshold constraint."""
        if self.operator == "le":
            return captured <= self.value
        if self.operator == "ge":
            return captured >= self.value
        return captured == self.value

    def __str__(self) -> str:
        """Return a human-readable string representation of the Threshold for reporting."""
        operators = {"le": f"<= {self.value}", "ge": f">= {self.value}", "eq": f"== {self.value}"}
        return operators[self.operator]


class ConfigEntry(BaseModel):
    """A single check to validate within a resolved stanza or across top-level commands."""

    model_config = ConfigDict(extra="forbid")
    description: str | None = None
    """Optional metadata describing the configuration entry. Used for reporting."""
    match: str
    """The string or pattern to match against commands in the resolved scope.

    For `regex` mode, standard regex syntax applies.
    """
    mode: Literal["exact", "contains", "regex"] = "exact"
    """Match mode.

    - `exact`: `match` must equal a command verbatim.
    - `contains`: At least one command must contain `match` as a substring.
    - `regex`: At least one command must match the pattern.
    """
    absent: bool = False
    """When `True`, the match must NOT be found."""
    threshold: Threshold | None = None
    """Optional Threshold for `mode: regex`. The first capture group in `match` is extracted and compared against this Threshold."""

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

    def matches(self, commands: list[str]) -> list[str]:
        """Return the subset of `commands` that satisfy this entry's match criteria."""
        if self.mode == "exact":
            return [cmd for cmd in commands if cmd == self.match]
        if self.mode == "contains":
            return [cmd for cmd in commands if self.match in cmd]
        # re.search (not fullmatch) — the pattern may appear anywhere within the command string.
        return [cmd for cmd in commands if re.search(self.match, cmd)]

    def build_description(self, stanza_path: str | None = None) -> str:
        """Build the description from this entry fields and an optional resolved stanza path."""
        location = f"'{stanza_path}'" if stanza_path else "the running-config"

        if self.threshold is not None:
            auto = f"Captured value of '{self.match}' {self.threshold} in {location}"
        elif self.mode == "exact":
            verb = "is absent from" if self.absent else "is present in"
            auto = f"Command '{self.match}' {verb} {location}"
        elif self.mode == "contains":
            verb = "is absent from" if self.absent else "is present in"
            auto = f"Substring '{self.match}' {verb} {location}"
        else:
            verb = "does not match in" if self.absent else "matches in"
            auto = f"Pattern '{self.match}' {verb} {location}"

        return f"{self.description} - {auto}" if self.description else auto


class ConfigRule(BaseModel):
    """A rule targeting a scope in the running-config and the entries to validate within it."""

    model_config = ConfigDict(extra="forbid")
    stanza: Annotated[list[Annotated[RegexString, Field(min_length=1)]], Field(min_length=1)] | None = None
    """Optional stanza path to navigate into the config tree before validating entries.

    - `None` (default): validate against top-level running-config commands.
    - Single element: one level deep (e.g. `["management api http-commands"]`).
    - Multiple elements: nested stanzas (e.g. `["router bgp 65101", "vrf DEV"]`).

    Each element uses exact key lookup first, falling back to `re.fullmatch` as a regex.
    """
    entries: list[ConfigEntry]
    """Entries to validate within the resolved scope."""
