# Copyright (c) 2023-2025 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Module containing input models for flow tracking tests."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict


class FlowTracker(BaseModel):
    """Flow Tracking model representing the tracker details."""

    model_config = ConfigDict(extra="forbid")
    name: str
    """The name of the flow tracker."""
    record_export: RecordExport | None = None
    """Configuration for record export, specifying details about timeouts."""
    exporters: list[Exporter] | None = None
    """A list of exporters associated with the flow tracker."""

    def __str__(self) -> str:
        """Return a human-readable string representation of the FlowTracker for reporting.

        Examples
        --------
        Flow Tracker: FLOW-TRACKER

        """
        return f"Flow Tracker: {self.name}"


class RecordExport(BaseModel):
    """Model representing the record export configuration for a flow tracker."""

    model_config = ConfigDict(extra="forbid")
    on_inactive_timeout: int
    """The timeout in milliseconds for exporting flow records when the flow becomes inactive."""
    on_interval: int
    """The interval in milliseconds for exporting flow records."""

    def __str__(self) -> str:
        """Return a human-readable string representation of the RecordExport for reporting.

        Examples
        --------
        Inactive Timeout: 60000, Active Interval: 300000

        """
        return f"Inactive Timeout: {self.on_inactive_timeout} Active Interval: {self.on_interval}"


class Exporter(BaseModel):
    """Model representing the exporter used for flow record export."""

    model_config = ConfigDict(extra="forbid")
    name: str
    """The name of the exporter."""
    local_interface: str
    """The local interface used by the exporter to send flow records."""
    template_interval: int
    """The template interval, in milliseconds, for the exporter to refresh the flow template."""

    def __str__(self) -> str:
        """Return a human-readable string representation of the Exporter for reporting.

        Examples
        --------
        Exporter: CVP-TELEMETRY

        """
        return f"Exporter: {self.name}"
