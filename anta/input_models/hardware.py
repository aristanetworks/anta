# Copyright (c) 2025 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Module containing input models for hardware tests."""

from pydantic import BaseModel, ConfigDict, Field


class Thresholds(BaseModel):
    """Thresholds for hardware drop counters over various time periods."""

    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    minute: int = Field(default=0, alias="dropInLastMinute", description="Last minute")
    """Threshold for the last minute."""
    ten_minute: int = Field(default=0, alias="dropInLastTenMinute", description="Last 10 minutes")
    """Threshold for the last ten minutes."""
    hour: int = Field(default=0, alias="dropInLastOneHour", description="Last hour")
    """Threshold for the last hour."""
    day: int = Field(default=0, alias="dropInLastOneDay", description="Last day")
    """Threshold for the last day."""
    week: int = Field(default=0, alias="dropInLastOneWeek", description="Last week")
    """Threshold for the last week."""
