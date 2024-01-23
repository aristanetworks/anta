# Copyright (c) 2023-2024 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""
Test functions related to the EOS various service settings
"""

# Mypy does not understand AntaTest.Input typing
# mypy: disable-error-code=attr-defined
from __future__ import annotations

from typing import List

from pydantic import BaseModel

from anta.custom_types import ErrDisableInterval, ErrorDisableReasons
from anta.models import AntaCommand, AntaTest
from anta.tools.utils import get_failed_logs


class VerifyErrdisableRecovery(AntaTest):
    """
    This class verifies the error-disable recovery reason, status, and interval.

    Expected Results:
        * Success: The test will pass if the error-disable recovery reason status is enabled and the interval matches the input.
        * Failure: The test will fail if the error-disable recovery reason is not found, the status is not enabled, or the interval does not match the input.
    """

    name = "VerifyErrdisableRecovery"
    description = "Verifies the error-disable recovery reason, status, and interval."
    categories = ["services"]
    commands = [AntaCommand(command="show errdisable recovery", ofmt="text")]  # Command dose not support JSON output hence using text output

    class Input(AntaTest.Input):
        """Inputs for the VerifyErrdisableRecovery test."""

        reasons: List[ErrDisableReasons]
        """List of error-disable reasons"""

        class ErrDisableReasons(BaseModel):
            """Details of an error-disable reason"""

            reason: ErrorDisableReasons
            """Type or name of the error-disable reason"""
            interval: ErrDisableInterval
            """Interval of the reason in seconds"""

    @AntaTest.anta_test
    def test(self) -> None:
        command_output = self.instance_commands[0].text_output
        self.result.is_success()
        for error_reason in self.inputs.reasons:
            input_reason = error_reason.reason
            input_interval = error_reason.interval
            reason_found = False

            # Skip header and last empty line
            lines = command_output.split("\n")[2:-1]
            for line in lines:
                # Skip empty lines
                if not line.strip():
                    continue
                # Split by first two whitespaces
                reason, status, interval = line.split(None, 2)
                if reason != input_reason:
                    continue
                reason_found = True
                actual_reason_data = {"interval": interval, "status": status}
                expected_reason_data = {"interval": str(input_interval), "status": "Enabled"}
                if actual_reason_data != expected_reason_data:
                    failed_log = get_failed_logs(expected_reason_data, actual_reason_data)
                    self.result.is_failure(f"`{input_reason}`:{failed_log}\n")
                break

            if not reason_found:
                self.result.is_failure(f"`{input_reason}`: Not found.\n")
