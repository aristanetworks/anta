"""
Test functions related to VXLAN
"""
import logging
from typing import Any, Dict, cast

from anta.models import AntaTest, AntaTestCommand

from anta.inventory.models import InventoryDevice
from anta.result_manager.models import TestResult
from anta.tests import anta_test

logger = logging.getLogger(__name__)


class VerifyVxlan(AntaTest):
    """
    Verifies if Vxlan1 interface is configured, and is up/up
    """

    name = "verify_vxlan"
    description = "Verifies Vxlan1 status"
    categories = ["mlag"]
    commands = [AntaTestCommand(command="show interfaces description", ofmt="json")]

    @AntaTest.anta_test
    def test(self) -> None:
        """Run VerifyVxlan validation"""
        self.logger.debug(f"self.instance_commands is: {self.instance_commands}")
        command_output = cast(Dict[str, Dict[str, Any]], self.instance_commands[0].output)
        self.logger.debug(f"dataset is: {command_output}")

        if "Vxlan1" not in command_output['interfaceDescriptions']:
            self.result.is_skipped("Vxlan1 interface is not configured")
        elif (
            command_output['interfaceDescriptions']['Vxlan1']['lineProtocolStatus'] == "up"
            and command_output['interfaceDescriptions']['Vxlan1']['interfaceStatus'] == "up"
        ):
            self.result.is_success()
        else:
            self.result.is_failure(f"Vxlan1 interface is {command_output['interfaceDescriptions']['Vxlan1']['lineProtocolStatus']}/{command_output['interfaceDescriptions']['Vxlan1']['interfaceStatus']}")


@anta_test
async def verify_vxlan_config_sanity(device: InventoryDevice, result: TestResult) -> TestResult:
    """
    Verifies there is no VXLAN config-sanity warnings.

    Args:
        device (InventoryDevice): InventoryDevice instance containing all devices information.

    Returns:
        TestResult instance with
        * result = "unset" if the test has not been executed
        * result = "success" if VXLAN config sanity is OK
        * result = "failure" otherwise.
        * result = "error" if any exception is caught
    """
    response = await device.session.cli(command="show vxlan config-sanity", ofmt="json")
    logger.debug(f"query result is: {response}")
    response_data = response["categories"]

    if len(response_data) == 0:
        result.is_skipped("Vxlan is not enabled on this device")
        return result

    failed_categories = {
        category: content for category, content in response_data.items() if category in ["localVtep", "mlag"] and content["allCheckPass"] is not True
    }

    if len(failed_categories) > 0:
        result.is_failure(f"Vxlan config sanity check is not passing: {failed_categories}")
    else:
        result.is_success()

    return result
