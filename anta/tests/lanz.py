# Copyright (c) 2023-2024 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""
Test functions related to LANZ
"""

from __future__ import annotations

from anta.models import AntaCommand, AntaTest


class VerifyLANZ(AntaTest):
    """
    Verifies if LANZ is enabled

    Expected results:
        * success: the test will pass if lanz is enabled
        * failure: the test will fail if lanz is disabled
    """

    name = "VerifyLANZ"
    description = "Verifies if LANZ is enabled."
    categories = ["lanz"]
    commands = [AntaCommand(command="show queue-monitor length status")]

    @AntaTest.anta_test
    def test(self) -> None:
        command_output = self.instance_commands[0].json_output

        if command_output["lanzEnabled"] is not True:
            self.result.is_failure("LANZ is not enabled")
        else:
            self.result.is_success("LANZ is enabled")
