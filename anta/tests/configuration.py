"""
Test functions related to the device configuration
"""

# pylint: disable = too-few-public-methods

from __future__ import annotations

from anta.models import AntaCommand, AntaTest


class VerifyZeroTouch(AntaTest):
    """
    Verifies ZeroTouch is disabled.
    """

    name = "VerifyZeroTouch"
    description = "Verifies ZeroTouch is disabled."
    categories = ["configuration"]
    commands = [AntaCommand(command="show zerotouch")]

    @AntaTest.anta_test
    def test(self) -> None:
        """Run VerifyZeroTouch validation"""

        command_output = self.instance_commands[0].output

        assert isinstance(command_output, dict)
        if command_output["mode"] == "disabled":
            self.result.is_success()
        else:
            self.result.is_failure("ZTP is NOT disabled")


class VerifyRunningConfigDiffs(AntaTest):
    """
    Verifies there is no difference between the running-config and the startup-config.
    """

    name = "VerifyRunningConfigDiffs"
    description = ""
    categories = ["configuration"]
    commands = [AntaCommand(command="show running-config diffs", ofmt="text")]

    @AntaTest.anta_test
    def test(self) -> None:
        """Run VerifyRunningConfigDiffs validation"""
        command_output = self.instance_commands[0].output
        if command_output is None or command_output == "":
            self.result.is_success()
        else:
            self.result.is_failure()
            self.result.is_failure(str(command_output))
