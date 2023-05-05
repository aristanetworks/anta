"""
Test functions related to ASIC profiles
"""
import logging
from typing import Any, Dict, List, Optional, cast

from anta.decorators import skip_on_platforms
from anta.inventory.models import InventoryDevice
from anta.result_manager.models import TestResult
from anta.tests import anta_test

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
    def test(self, mode=None) -> None:
        if not mode:
            self.result.is_skipped("verify_unified_forwarding_table_mode was not run as no mode was given")
        else:
            command_output = cast(Dict[str, Dict[Any, Any]], self.instance_commands[0].output)
            if command_output['uftMode'] == mode:
                self.result.is_success()
            else:
                self.result.is_failure(f"Device is not running correct UFT mode (expected: {mode} / running: {command_output['uftMode']})")


@skip_on_platforms(["cEOSLab", "VEOS-LAB"])
@anta_test
async def verify_tcam_profile(device: InventoryDevice, result: TestResult, profile: str) -> TestResult:
    """
    Verifies the configured TCAM profile is the expected one.

    Args:
        device (InventoryDevice): InventoryDevice instance containing all devices information.
        profile (str): The expected TCAM profile.0

    Returns:
        TestResult instance with
        * result = "unset" if the test has not been executed
        * result = "mode" if the `profile` parameter is missing
        * result = "success" if TCAM profile is correct
        * result = "failure" otherwise.
        * result = "error" if any exception is caught
    """
    if not profile:
        result.is_skipped("verify_tcam_profile was not run as no profile was given")
        return result

    response = await device.session.cli(command="show hardware tcam profile", ofmt="json")
    logger.debug(f"query result is: {response}")
    if (response["pmfProfiles"]["FixedSystem"]["status"] == response["pmfProfiles"]["FixedSystem"]["config"]) and (
        response["pmfProfiles"]["FixedSystem"]["status"] == profile
    ):
        result.is_success()
    else:
        result.is_failure(f'Incorrect profile configured on device: {response["pmfProfiles"]["FixedSystem"]["status"]}')

    return result
