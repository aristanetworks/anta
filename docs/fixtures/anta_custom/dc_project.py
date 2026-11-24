# Copyright (c) 2023-2026 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Runnable custom tests used to regenerate documentation output."""

# Pyright does not understand AntaTest.Input typing
# pyright: reportAttributeAccessIssue=false
from __future__ import annotations

from typing import ClassVar

from pydantic import PositiveInt

from anta.models import AntaCommand, AntaTemplate, AntaTest


class VerifyMinimumUptime(AntaTest):
    """Verifies the device uptime is greater than a minimum value.

    Expected Results
    ----------------
    * Success: The test passes when the device uptime exceeds the minimum.
    * Failure: The test fails when the device uptime does not exceed the minimum.

    Examples
    --------
    ```yaml
    anta_custom.dc_project:
      - VerifyMinimumUptime:
          minimum: 3600
    ```
    """

    categories: ClassVar[list[str]] = ["custom"]
    commands: ClassVar[list[AntaCommand | AntaTemplate]] = [AntaCommand(command="show uptime", revision=1)]

    class Input(AntaTest.Input):
        """Inputs for the VerifyMinimumUptime test."""

        minimum: PositiveInt
        """Minimum uptime in seconds."""

    @AntaTest.anta_test
    def test(self) -> None:
        """Main test function for VerifyMinimumUptime."""
        actual_uptime = self.instance_commands[0].json_output["upTime"]
        if actual_uptime > self.inputs.minimum:
            self.result.is_success()
        else:
            self.result.is_failure(f"Device uptime is too low - Expected: > {self.inputs.minimum}s Actual: {actual_uptime}s")
