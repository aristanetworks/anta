# Copyright (c) 2024-2025 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Constants and Enums for the asynceapi package."""

from __future__ import annotations

from enum import Enum


class EapiCommandFormat(str, Enum):
    """Enum for the eAPI command format.

    NOTE: This could be updated to StrEnum when Python 3.11 is the minimum supported version in ANTA.
    """

    JSON = "json"
    TEXT = "text"

    def __str__(self) -> str:
        """Override the __str__ method to return the value of the Enum, mimicking the behavior of StrEnum."""
        return self.value
