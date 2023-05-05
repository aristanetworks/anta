"""
Test functions related to ASIC profiles
"""
import logging
from typing import Any, Dict, cast

from anta.decorators import skip_on_platforms
from anta.models import AntaTest, AntaTestCommand

logger = logging.getLogger(__name__)


class VerifyUnifiedForwardingTableMode(AntaTest):
    """
    Verifies the device is using the expected Unified Forwarding Table mode.
    """

    name = "verify_unified_forwarding_table_mode"
    description = ""
    categories = ["profiles"]
    commands = [AntaTestCommand(command="show platform trident forwarding-table partition", ofmt="json")]

    @skip_on_platforms(["cEOSLab", "vEOS-lab"])
    @AntaTest.anta_test
    def test(self, mode: Any = None) -> None:
        if not mode:
            self.result.is_skipped("verify_unified_forwarding_table_mode was not run as no mode was given")
        else:
            command_output = cast(Dict[str, Dict[Any, Any]], self.instance_commands[0].output)
            if command_output["uftMode"] == mode:
                self.result.is_success()
            else:
                self.result.is_failure(f"Device is not running correct UFT mode (expected: {mode} / running: {command_output['uftMode']})")


class VerifyTcamProfile(AntaTest):
    """
    Verifies the device is using the configured TCAM profile.
    """

    name = "verify_tcam_profile"
    description = "Verify that the assigned TCAM profile is actually running on the device"
    categories = ["profiles"]
    commands = [AntaTestCommand(command="show hardware tcam profile", ofmt="json")]

    @skip_on_platforms(["cEOSLab", "vEOS-lab"])
    @AntaTest.anta_test
    def test(self, profile: Any = None) -> None:
        if not profile:
            self.result.is_skipped("verify_tcam_profile was not run as no profile was given")
        else:
            command_output = cast(Dict[str, Dict[Any, Any]], self.instance_commands[0].output)
            if (
                command_output["pmfProfiles"]["FixedSystem"]["status"] == command_output["pmfProfiles"]["FixedSystem"]["config"]
                and command_output["pmfProfiles"]["FixedSystem"]["status"] == profile
            ):
                self.result.is_success()
            else:
                self.result.is_failure(f"Incorrect profile running on device: {command_output['pmfProfiles']['FixedSystem']['status']}")
