# Copyright (c) 2023-2024 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""
Test functions related to PTP (Precision Time Protocol) in EOS
"""
from __future__ import annotations

from anta.models import AntaCommand, AntaTest


class VerifyPtpStatus(AntaTest):
    """
    Verifies whether the PTP agent is enabled globally.

    Expected Results:
        * success: The test will pass if the PTP agent is enabled globally.
        * failure: The test will fail if the PTP agent is enabled globally.
    """

    name = "VerifyPtpStatus"
    description = "Verifies if the PTP agent is enabled."
    categories = ["ptp"]
    commands = [AntaCommand(command="show ptp")]

    @AntaTest.anta_test
    def test(self) -> None:
        command_output = self.instance_commands[0].json_output

        if "ptpMode" in command_output.keys():
            self.result.is_success()
        else:
            self.result.is_failure("PTP agent disabled")
