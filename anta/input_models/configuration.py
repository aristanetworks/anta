# Copyright (c) 2023-2026 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Module containing input models for configuration tests."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict


class RunningConfigSection(BaseModel):
    """Model for validating configuration entries within a specific section or across the entire running-configuration."""

    model_config = ConfigDict(extra="forbid")
    section: str | None = None
    """The first line of the configuration section to match (e.g. router bgp 65101). Must uniquely identify a single section block.

    When None, the config entries are validated against the entire running-configuration instead of a specific section.
    """
    description: str | None = None
    """Optional metadata describing the section or scope. Used for reporting."""
    config_entries: list[ConfigEntries]
    """List of configuration entries to validate within the specified section or the entire running-configuration."""


class ConfigEntries(BaseModel):
    """Model for a configuration entry to validate within a running-config section or the entire running-configuration."""

    model_config = ConfigDict(extra="forbid")
    search_string: str
    """The string to search for within the configuration section."""
    validation_mode: Literal["exact_match", "contains", "absent"] = "exact_match"
    """Validation mode controlling how search_string is matched. Defaults to exact_match.

    Options:
    - exact_match: The search_string must be an exact key in the section's or entire running-configuration command list.
    - contains: At least one command in the section or entire running-configuration must contain search_string as a substring.
    - absent: No command in the section or entire running-configuration may contain search_string.
    """
    threshold: int | None = None
    """Optional numeric threshold compared against the value extracted from a matched command line. Used with threshold_operator."""
    threshold_operator: Literal["le", "ge", "eq"] = "eq"
    """Operator used to compare the extracted numeric value against threshold. Defaults to eq.

    Options:
    - le: The extracted value must be less than or equal to threshold.
    - ge: The extracted value must be greater than or equal to threshold.
    - eq: The extracted value must be equal to threshold.
    """
    context: str | None = None
    """Optional label used as the failure message instead of the default search_string text."""
