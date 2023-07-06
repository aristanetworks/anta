"""
Test functions related to ASIC profiles
"""

from typing import Optional

from anta.decorators import skip_on_platforms
from anta.models import AntaCommand, AntaTest


class VerifyUnifiedForwardingTableMode(AntaTest):
    """
    Verifies the device is using the expected Unified Forwarding Table mode.
    """

    name = "VerifyUnifiedForwardingTableMode"
    description = ""
    categories = ["profiles"]
    commands = [AntaCommand(command="show platform trident forwarding-table partition", ofmt="json")]

    @skip_on_platforms(["cEOSLab", "vEOS-lab"])
    @AntaTest.anta_test
    def test(self, mode: Optional[str] = None) -> None:
        """
        Run VerifyUnifiedForwardingTableMode validation

        Args:
            mode: Expected UFT mode.
        """
        if not mode:
            self.result.is_skipped("VerifyUnifiedForwardingTableMode was not run as no mode was given")
            return

        command_output = self.instance_commands[0].json_output
        if command_output["uftMode"] == mode:
            self.result.is_success()
        else:
            self.result.is_failure(f"Device is not running correct UFT mode (expected: {mode} / running: {command_output['uftMode']})")


class VerifyTcamProfile(AntaTest):
    """
    Verifies the device is using the configured TCAM profile.
    """

    name = "VerifyTcamProfile"
    description = "Verify that the assigned TCAM profile is actually running on the device"
    categories = ["profiles"]
    commands = [AntaCommand(command="show hardware tcam profile", ofmt="json")]

    @skip_on_platforms(["cEOSLab", "vEOS-lab"])
    @AntaTest.anta_test
    def test(self, profile: Optional[str] = None) -> None:
        """
        Run VerifyTcamProfile validation

        Args:
            profile: Expected TCAM profile.
        """
        if not profile:
            self.result.is_skipped("VerifyTcamProfile was not run as no profile was given")
            return

        command_output = self.instance_commands[0].json_output
        if command_output["pmfProfiles"]["FixedSystem"]["status"] == command_output["pmfProfiles"]["FixedSystem"]["config"] == profile:
            self.result.is_success()
        else:
            self.result.is_failure(f"Incorrect profile running on device: {command_output['pmfProfiles']['FixedSystem']['status']}")
