# Copyright (c) 2025 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Module containing input models for hardware tests."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

# Field was not provided by the user.
NOTPROVIDED = object()


class AdverseDropThresholds(BaseModel):
    """Thresholds for adverse drop counters over various time periods."""

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


class PCIeThresholds(BaseModel):
    """Thresholds for PCIe device error counters."""

    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    correctable_errors: int = Field(default=0, alias="correctableErrors", description="Correctable errors")
    """Threshold for correctable errors."""
    non_fatal_errors: int = Field(default=0, alias="nonFatalErrors", description="Non-fatal errors")
    """Threshold for non-fatal errors."""
    fatal_errors: int = Field(default=0, alias="fatalErrors", description="Fatal errors")
    """Threshold for fatal errors."""


class HardwareInventory(BaseModel):
    """Represents the inventory of installed hardware components.

    The validation logic for each field depends on its value:

      - int: Verifies that AT LEAST that many units are installed.
      - null: The check for this specific component is SKIPPED.
      - Not Provided: A "strict" check is performed, requiring ALL available
      slots for that component to be filled.
    """

    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    power_supplies: int | None = Field(default=NOTPROVIDED, alias="powerSupplySlots", description="Power Supply Slot", exclude=True)  # type: ignore[assignment]
    """The count of installed power supplies."""
    fan_trays: int | None = Field(default=NOTPROVIDED, alias="fanTraySlots", description="Fan Tray", exclude=True)  # type: ignore[assignment]
    """The count of installed fan trays."""
    fabric_cards: int | None = Field(default=NOTPROVIDED, alias="cardSlots", description="Fabric", exclude=True)  # type: ignore[assignment]
    """The count of installed fabric cards."""
    line_cards: int | None = Field(default=NOTPROVIDED, alias="cardSlots", description="Linecard", exclude=True)  # type: ignore[assignment]
    """The count of installed line cards."""
    supervisors: int | None = Field(default=NOTPROVIDED, alias="cardSlots", description="Supervisor", exclude=True)  # type: ignore[assignment]
    """The count of installed supervisor modules."""
