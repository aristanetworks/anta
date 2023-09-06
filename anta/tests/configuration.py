# Copyright (c) 2023 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""
Test functions related to the device configuration
"""
# Mypy does not understand AntaTest.Input typing
# mypy: disable-error-code=attr-defined
from __future__ import annotations

from anta.models import AntaCommand, AntaTest


class VerifyZeroTouch(AntaTest):
    """
    Verifies ZeroTouch is disabled
    """

    name = "VerifyZeroTouch"
    description = "Verifies ZeroTouch is disabled"
    categories = ["configuration"]
    commands = [AntaCommand(command="show zerotouch")]

    @AntaTest.anta_test
    def test(self) -> None:
        command_output = self.instance_commands[0].output
        assert isinstance(command_output, dict)
        if command_output["mode"] == "disabled":
            self.result.is_success()
        else:
            self.result.is_failure("ZTP is NOT disabled")


class VerifyRunningConfigDiffs(AntaTest):
    """
    Verifies there is no difference between the running-config and the startup-config
    """

    name = "VerifyRunningConfigDiffs"
    description = "Verifies there is no difference between the running-config and the startup-config"
    categories = ["configuration"]
    commands = [AntaCommand(command="show running-config diffs", ofmt="text")]

    @AntaTest.anta_test
    def test(self) -> None:
        command_output = self.instance_commands[0].output
        if command_output is None or command_output == "":
            self.result.is_success()
        else:
            self.result.is_failure()
            self.result.is_failure(str(command_output))
