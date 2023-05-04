"""
Test functions related to Multi-Chassis LAG
"""
import logging

from anta.inventory.models import InventoryDevice
from anta.result_manager.models import TestResult
from anta.tests import anta_test

from anta.decorators import skip_on_platforms
from anta.models import AntaTest, AntaTestCommand
from typing import Any, Dict, List, cast

logger = logging.getLogger(__name__)


class VerifyMlagStatus(AntaTest):
    """
    Verifies if MLAG us running, and if the status is good
    state is active, negotiation status is connected, local int is up, peer link is up.
    """
    name = "verify_mlag_status"
    description = "Verifies MLAG status"
    categories = ["mlag"]
    commands = [AntaTestCommand(command="show mlag", ofmt="json")]

    @AntaTest.anta_test
    def test(self) -> None:
        """Run VerifyMlagStatus validation"""
        self.logger.debug(f"self.instance_commands is: {self.instance_commands}")
        command_output = cast(Dict[str, Dict[str, Any]], self.instance_commands[0].output)
        self.logger.debug(f"dataset is: {command_output}")

        if command_output["state"] == "disabled":
            self.result.is_skipped("MLAG is disabled")
        elif command_output["state"] != "active" or command_output["negStatus"] != "connected" or command_output["localIntfStatus"] != "up" or command_output["peerLinkStatus"] != "up":
            self.result.is_failure(f"MLAG status is not OK: {command_output}")
        else:
            self.result.is_success()


@anta_test
async def verify_mlag_interfaces(device: InventoryDevice, result: TestResult) -> TestResult:
    """
    Verifies there is no inactive or active-partial MLAG interfaces.

    Args:
        device (InventoryDevice): InventoryDevice instance containing all devices information.

    Returns:
        TestResult instance with
        * result = "unset" if the test has not been executed
        * result = "success" if there is no inactive or active-partial MLAG interfaces.
        * result = "failure" otherwise.
        * result = "error" if any exception is caught

    """
    response = await device.session.cli(command="show mlag", ofmt="json")

    if response["state"] == "disabled":
        result.is_skipped("MLAG is disabled")
    elif response["mlagPorts"]["Inactive"] != 0 or response["mlagPorts"]["Active-partial"] != 0:
        result.is_failure(f"MLAG status is not OK: {response['mlagPorts']}")
    else:
        result.is_success()

    return result


@anta_test
async def verify_mlag_config_sanity(device: InventoryDevice, result: TestResult) -> TestResult:
    """
    Verifies there is no MLAG config-sanity inconsistencies.

    Args:
        device (InventoryDevice): InventoryDevice instance containing all devices information.

    Returns:
        TestResult instance with
        * result = "unset" if the test has not been executed
        * result = "success" if there is no MLAG config-sanity inconsistencies
        * result = "failure" otherwise.
        * result = "error" if any exception is caught

    """
    response = await device.session.cli(command="show mlag config-sanity", ofmt="json")

    if "mlagActive" not in response.keys():
        result.is_error("incorrect JSON response")
    elif response["mlagActive"] is False:
        # MLAG is not running
        result.is_skipped("MLAG is disabled")
    elif len(response["globalConfiguration"]) > 0 or len(response["interfaceConfiguration"]) > 0:
        result.is_failure()
        if len(response["globalConfiguration"]) > 0:
            result.is_failure("MLAG config-sanity returned some Global inconsistencies: " f"{response['response']['globalConfiguration']}")
        if len(response["interfaceConfiguration"]) > 0:
            result.is_failure("MLAG config-sanity returned some Interface inconsistencies: " f"{response['response']['interfaceConfiguration']}")
    else:
        result.is_success()

    return result
