# Copyright (c) 2023-2025 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Module containing input models for logging tests."""

from __future__ import annotations

from pydantic import BaseModel, Field

from anta.custom_types import LogSeverityLevel, RegexString


class LoggingQuery(BaseModel):
    """Logging query model representing the logging details."""

    regex_match: RegexString
    """Log regex pattern to be searched in last log entries."""
    last_number_messages: int = Field(ge=1, le=9999)
    """Last number of messages to check in the logging buffers."""
    severity_level: LogSeverityLevel = "informational"
    """Log severity level."""
