# Copyright (c) 2025 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Module containing input models for hardware tests."""

from pydantic import BaseModel, ConfigDict
from pydantic.alias_generators import to_camel


class DropThresholds(BaseModel):
    """Thresholds for drop counters over various time periods."""

    model_config = ConfigDict(extra="forbid", alias_generator=to_camel, populate_by_name=True)

    drop_in_last_minute: int = 0
    """Drop counter thresholds for the last minute."""
    drop_in_last_ten_minute: int = 0
    """Drop counter thresholds for the last ten minute."""
    drop_in_last_one_hour: int = 0
    """Drop counter thresholds for the last one hour."""
    drop_in_last_one_day: int = 0
    """Drop counter thresholds for the last one day."""
    drop_in_last_one_week: int = 0
    """Drop counter thresholds for the last one week."""
