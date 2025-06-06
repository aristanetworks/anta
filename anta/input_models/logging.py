# Copyright (c) 2023-2025 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Module containing input models for logging tests."""

from __future__ import annotations

from typing import TYPE_CHECKING, Annotated, Literal

from pydantic import BaseModel, Field, model_validator

from anta.custom_types import LogSeverityLevel, RegexString

if TYPE_CHECKING:
    import sys

    if sys.version_info >= (3, 11):
        from typing import Self
    else:
        from typing_extensions import Self


class LoggingQuery(BaseModel):
    """Logging query model representing the logging details."""

    regex_match: RegexString | list[RegexString]
    """Log regex pattern(s) to be searched in last log entries."""
    last_number_messages: Annotated[int, Field(ge=1, le=9999)] | None = None
    """Last number of messages to check in the logging buffers. Takes precedence over `last_number_time_units`."""
    last_number_time_units: Annotated[int, Field(ge=1, le=9999)] | None = None
    """Number of time units to look in the logging buffers.

    The actual duration is determined based on the selected `time_unit` (e.g. 5 "days", 10 "minutes")."""
    time_unit: Literal["days", "hours", "minutes", "seconds"] = "days"
    """Unit of time to be used with `last_number_time_units`."""
    severity_level: LogSeverityLevel = "informational"
    """Log severity level."""
    fail_on_match: bool = False
    """If `True`, the test fails if regex patterns are found. Otherwise, the test fails if patterns are not found instead."""

    @model_validator(mode="after")
    def validate_inputs(self) -> Self:
        """Validate the inputs provided to the LoggingQuery class.

        Either `last_number_messages` or `last_number_time_units` must be provided, not both.
        """
        if (self.last_number_messages is None) == (self.last_number_time_units is None):
            msg = "Exactly one of 'last_number_messages' or 'last_number_time_units' must be provided"
            raise ValueError(msg)
        return self
