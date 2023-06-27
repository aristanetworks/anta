"""
Test functions related to ASIC profiles
"""
import logging
from typing import Any, Dict, Optional, cast

from anta.models import AntaTest, AntaTestCommand
from anta.test_filters import SkipPlatformsFilter

logger = logging.getLogger(__name__)


class VerifyUnifiedForwardingTableMode(AntaTest):
    """
    Verifies the device is using the expected Unified Forwarding Table mode.
    """

    name = "VerifyUnifiedForwardingTableMode"
    description = ""
    categories = ["profiles"]
    commands = [AntaTestCommand(command="show platform trident forwarding-table partition", ofmt="json")]
    test_filters = [SkipPlatformsFilter(platforms_to_skip=["cEOSLab", "vEOS-lab"])]

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

        command_output = cast(Dict[str, Dict[Any, Any]], self.instance_commands[0].output)
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
    commands = [AntaTestCommand(command="show hardware tcam profile", ofmt="json")]
    test_filters = [SkipPlatformsFilter(platforms_to_skip=["cEOSLab", "vEOS-lab"])]

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

        command_output = cast(Dict[str, Dict[Any, Any]], self.instance_commands[0].output)
        if command_output["pmfProfiles"]["FixedSystem"]["status"] == command_output["pmfProfiles"]["FixedSystem"]["config"] == profile:
            self.result.is_success()
        else:
            self.result.is_failure(f"Incorrect profile running on device: {command_output['pmfProfiles']['FixedSystem']['status']}")
