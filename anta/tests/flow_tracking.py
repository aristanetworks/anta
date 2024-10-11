# Copyright (c) 2023-2024 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Module related to the flow tracking tests."""

# Mypy does not understand AntaTest.Input typing
# mypy: disable-error-code=attr-defined
from __future__ import annotations

from typing import ClassVar

from pydantic import BaseModel

from anta.decorators import skip_on_platforms
from anta.models import AntaCommand, AntaTemplate, AntaTest
from anta.tools import get_failed_logs


def validate_record_export(record_export: dict[str, str], tracker_info: dict[str, str]) -> str:
    """
    Validate the record export configuration against the tracker info.

    Parameters
    ----------
    record_export
        The expected record export configuration.
    tracker_info
        The actual tracker info from the command output.

    Returns
    -------
    str
        A failure message if the record export configuration does not match, otherwise blank string.
    """
    failed_log = ""
    actual_export = {"inactive timeout": tracker_info.get("inactiveTimeout"), "interval": tracker_info.get("activeInterval")}
    expected_export = {"inactive timeout": record_export.get("on_inactive_timeout"), "interval": record_export.get("on_interval")}
    if actual_export != expected_export:
        failed_log = get_failed_logs(expected_export, actual_export)
    return failed_log


def validate_exporters(exporters: list[dict[str, str]], tracker_info: dict[str, str]) -> str:
    """
    Validate the exporter configurations against the tracker info.

    Parameters
    ----------
    exporters
        The list of expected exporter configurations.
    tracker_info
        The actual tracker info from the command output.

    Returns
    -------
    str
        Failure message if any exporter configuration does not match.
    """
    failed_log = ""
    for exporter in exporters:
        exporter_name = exporter["name"]
        actual_exporter_info = tracker_info["exporters"].get(exporter_name)
        if not actual_exporter_info:
            failed_log += f"\nExporter `{exporter_name}` is not configured."
            continue

        expected_exporter_data = {"local interface": exporter["local_interface"], "template interval": exporter["template_interval"]}
        actual_exporter_data = {"local interface": actual_exporter_info["localIntf"], "template interval": actual_exporter_info["templateInterval"]}

        if expected_exporter_data != actual_exporter_data:
            failed_msg = get_failed_logs(expected_exporter_data, actual_exporter_data)
            failed_log += f"\nExporter `{exporter_name}`: {failed_msg}"
    return failed_log


class VerifyHardwareFlowTrackerStatus(AntaTest):
    """
    Verifies if hardware flow tracking is running and an input tracker is active.

    This test optionally verifies the tracker interval/timeout and exporter configuration.

    Expected Results
    ----------------
    * Success: The test will pass if hardware flow tracking is running and an input tracker is active.
    * Failure: The test will fail if hardware flow tracking is not running, an input tracker is not active,
               or the tracker interval/timeout and exporter configuration does not match the expected values.

    Examples
    --------
    ```yaml
    anta.tests.flow_tracking:
      - VerifyFlowTrackingHardware:
          trackers:
            - name: FLOW-TRACKER
              record_export:
                on_inactive_timeout: 70000
                on_interval: 300000
              exporters:
                - name: CV-TELEMETRY
                  local_interface: Loopback0
                  template_interval: 3600000
    ```
    """

    name = "VerifyHardwareFlowTrackerStatus"
    description = (
        "Verifies if hardware flow tracking is running and an input tracker is active. Optionally verifies the tracker interval/timeout and exporter configuration."
    )
    categories: ClassVar[list[str]] = ["flow tracking"]
    commands: ClassVar[list[AntaCommand | AntaTemplate]] = [AntaTemplate(template="show flow tracking hardware tracker {name}", revision=1)]

    class Input(AntaTest.Input):
        """Input model for the VerifyHardwareFlowTrackerStatus test."""

        trackers: list[FlowTracker]
        """List of flow trackers to verify."""

        class FlowTracker(BaseModel):
            """Detail of a flow tracker."""

            name: str
            """Name of the flow tracker."""

            record_export: RecordExport | None = None
            """Record export configuration for the flow tracker."""

            exporters: list[Exporter] | None = None
            """List of exporters for the flow tracker."""

            class RecordExport(BaseModel):
                """Record export configuration."""

                on_inactive_timeout: int
                """Timeout in milliseconds for exporting records when inactive."""

                on_interval: int
                """Interval in milliseconds for exporting records."""

            class Exporter(BaseModel):
                """Detail of an exporter."""

                name: str
                """Name of the exporter."""

                local_interface: str
                """Local interface used by the exporter."""

                template_interval: int
                """Template interval in milliseconds for the exporter."""

    def render(self, template: AntaTemplate) -> list[AntaCommand]:
        """Render the template for each hardware tracker."""
        return [template.render(name=tracker.name) for tracker in self.inputs.trackers]

    @skip_on_platforms(["cEOSLab", "vEOS-lab"])
    @AntaTest.anta_test
    def test(self) -> None:
        """Main test function for VerifyHardwareFlowTrackerStatus."""
        self.result.is_success()
        for command, tracker_input in zip(self.instance_commands, self.inputs.trackers):
            hardware_tracker_name = command.params.name
            record_export = tracker_input.record_export.model_dump() if tracker_input.record_export else None
            exporters = [exporter.model_dump() for exporter in tracker_input.exporters] if tracker_input.exporters else None
            command_output = command.json_output

            # Check if hardware flow tracking is configured
            if not command_output.get("running"):
                self.result.is_failure("Hardware flow tracking is not running.")
                return

            # Check if the input hardware tracker is configured
            tracker_info = command_output["trackers"].get(hardware_tracker_name)
            if not tracker_info:
                self.result.is_failure(f"Hardware flow tracker `{hardware_tracker_name}` is not configured.")
                continue

            # Check if the input hardware tracker is active
            if not tracker_info.get("active"):
                self.result.is_failure(f"Hardware flow tracker `{hardware_tracker_name}` is not active.")
                continue

            # Check the input hardware tracker timeouts
            failure_msg = ""
            if record_export:
                record_export_failure = validate_record_export(record_export, tracker_info)
                if record_export_failure:
                    failure_msg += record_export_failure

            # Check the input hardware tracker exporters' configuration
            if exporters:
                exporters_failure = validate_exporters(exporters, tracker_info)
                if exporters_failure:
                    failure_msg += exporters_failure

            if failure_msg:
                self.result.is_failure(f"{hardware_tracker_name}: {failure_msg}\n")
