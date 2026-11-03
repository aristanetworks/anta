# Copyright (c) 2024-2026 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Constants and Enums for the asynceapi package."""

from __future__ import annotations

from enum import StrEnum

EAPI_CONNECTIVITY_TIMEOUT = 5
"""Seconds to wait while establishing connectivity during refresh and session login."""


class EapiCommandFormat(StrEnum):
    """Enum for the eAPI command format."""

    JSON = "json"
    TEXT = "text"
