"""
Test functions related to the device configuration
"""

# pylint: disable = too-few-public-methods

from __future__ import annotations

import logging

from anta.models import AntaTest, AntaTestCommand

logger = logging.getLogger(__name__)


class VerifyZeroTouch(AntaTest):
    """
    Verifies ZeroTouch is disabled.
    """

    name = "verify_zerotouch"
    description = "Verifies ZeroTouch is disabled."
    categories = ["configuration"]
    commands = [AntaTestCommand(command="show zerotouch")]

    @AntaTest.anta_test
    def test(self) -> None:
        """Run VerifyZeroTouch validation"""
        self.logger.setLevel(logging.DEBUG)
        # TODO - easier way to access output ?
        self.logger.debug(f"self.instance_commands is: {self.instance_commands}")
        command_output = self.instance_commands[0].output
        self.logger.debug(f"dataset is: {command_output}")
        assert isinstance(command_output, dict)
        if command_output["mode"] == "disabled":
            self.result.is_success()
        else:
            self.result.is_failure("ZTP is NOT disabled")


class VerifyRunningConfigDiffs(AntaTest):
    """
    Verifies there is no difference between the running-config and the startup-config.
    """

    name = "verify_running_config_diffs"
    description = ""
    categories = ["configuration"]
    commands = [AntaTestCommand(command="show running-config diffs", ofmt="text")]

    @AntaTest.anta_test
    def test(self) -> None:
        """Run VerifyRunningConfigDiffs validation"""
        self.logger.setLevel(logging.DEBUG)
        self.logger.debug(f"self.instance_commands is {self.instance_commands}")
        command_output = self.instance_commands[0].output
        self.logger.debug(f"command_output is {command_output}")
        if command_output is None or command_output == "":
            self.result.is_success()
        else:
            self.result.is_failure()
            self.result.is_failure(str(command_output))
        self.logger.debug(f"result is {self.result}")
