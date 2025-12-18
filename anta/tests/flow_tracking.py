# Copyright (c) 2023-2025 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Module related to the flow tracking tests."""

# Pyright does not understand AntaTest.Input typing
# pyright: reportAttributeAccessIssue=false
from __future__ import annotations

from typing import ClassVar

from anta.decorators import skip_on_platforms
from anta.input_models.flow_tracking import FlowTracker
from anta.models import AntaCommand, AntaTemplate, AntaTest
from anta.tools import get_value


def validate_exporters(exporters: list[dict[str, str]], tracker_info: dict[str, str]) -> list[str]:
    """Validate the exporter configurations against the tracker info.

    Parameters
    ----------
    exporters
        The list of expected exporter configurations.
    tracker_info
        The actual tracker info from the command output.

    Returns
    -------
    list
        List of failure messages for any exporter configuration that does not match.
    """
    failure_messages = []
    for exporter in exporters:
        exporter_name = exporter.name
        actual_exporter_info = tracker_info["exporters"].get(exporter_name)
        if not actual_exporter_info:
            failure_messages.append(f"{exporter} - Not configured")
            continue
        local_interface = actual_exporter_info["localIntf"]
        template_interval = actual_exporter_info["templateInterval"]

        if local_interface != exporter.local_interface:
            failure_messages.append(f"{exporter} - Incorrect local interface - Expected: {exporter.local_interface} Actual: {local_interface}")

        if template_interval != exporter.template_interval:
            failure_messages.append(f"{exporter} - Incorrect template interval - Expected: {exporter.template_interval} Actual: {template_interval}")
    return failure_messages


class VerifyHardwareFlowTrackerStatus(AntaTest):
    """Verifies the hardware flow tracking state.

    This test performs the following checks:

      1. Confirms that hardware flow tracking is running.
      2. For each specified flow tracker:
        - Confirms that the tracker is active.
        - Optionally, checks the tracker interval/timeout configuration.
        - Optionally, verifies the tracker exporter configuration

    Expected Results
    ----------------
    * Success: The test will pass if all of the following conditions are met:
        - Hardware flow tracking is running.
        - For each specified flow tracker:
            - The flow tracker is active.
            - The tracker interval/timeout matches the expected values, if provided.
            - The exporter configuration matches the expected values, if provided.
    * Failure: The test will fail if any of the following conditions are met:
        - Hardware flow tracking is not running.
        - For any specified flow tracker:
            - The flow tracker is not active.
            - The tracker interval/timeout does not match the expected values, if provided.
            - The exporter configuration does not match the expected values, if provided.

    Examples
    --------
    ```yaml
    anta.tests.flow_tracking:
      - VerifyHardwareFlowTrackerStatus:
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

    categories: ClassVar[list[str]] = ["flow tracking"]
    commands: ClassVar[list[AntaCommand | AntaTemplate]] = [AntaCommand(command="show flow tracking hardware", revision=1)]

    class Input(AntaTest.Input):
        """Input model for the VerifyHardwareFlowTrackerStatus test."""

        trackers: list[FlowTracker]
        """List of flow trackers to verify."""

    @skip_on_platforms(["cEOSLab", "vEOS-lab"])
    @AntaTest.anta_test
    def test(self) -> None:
        """Main test function for VerifyHardwareFlowTrackerStatus."""
        self.result.is_success()

        command_output = self.instance_commands[0].json_output
        # Check if hardware flow tracking is configured
        if not command_output.get("running"):
            self.result.is_failure("Hardware flow tracking is not running")
            return

        for tracker in self.inputs.trackers:
            # Check if the input hardware tracker is configured
            if not (tracker_info := get_value(command_output["trackers"], f"{tracker.name}")):
                self.result.is_failure(f"{tracker} - Not found")
                continue

            # Check if the input hardware tracker is active
            if not tracker_info.get("active"):
                self.result.is_failure(f"{tracker} - Disabled")
                continue

            # Check the input hardware tracker timeouts
            if tracker.record_export:
                inactive_interval = tracker.record_export.on_inactive_timeout
                on_interval = tracker.record_export.on_interval
                act_inactive = tracker_info.get("inactiveTimeout")
                act_interval = tracker_info.get("activeInterval")
                if not all([inactive_interval == act_inactive, on_interval == act_interval]):
                    self.result.is_failure(
                        f"{tracker} {tracker.record_export} - Incorrect timers - Inactive Timeout: {act_inactive} OnActive Interval: {act_interval}"
                    )

            # Check the input hardware tracker exporters configuration
            if tracker.exporters:
                failure_messages = validate_exporters(tracker.exporters, tracker_info)
                for message in failure_messages:
                    self.result.is_failure(f"{tracker} {message}")
