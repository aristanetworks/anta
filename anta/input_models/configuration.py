# Copyright (c) 2023-2025 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Module containing input models for configuration tests."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict

from anta.custom_types import RegexString


class RunningConfigSection(BaseModel):
    """class RunningConfigSection model representing the section details."""

    model_config = ConfigDict(extra="forbid")
    section_matcher: RegexString
    """A unique regex pattern to extract specific config entries from the running output."""
    match_patterns: list[RegexString]
    """Regex to validate matching patterns within selected configuration entries."""
