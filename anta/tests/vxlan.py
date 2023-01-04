"""
Test functions related to VXLAN
"""
import logging

from anta.inventory.models import InventoryDevice
from anta.result_manager.models import TestResult
from anta.tests import anta_test

logger = logging.getLogger(__name__)


@anta_test
async def verify_vxlan(device: InventoryDevice, result: TestResult) -> TestResult:
    """
    Verifies the interface vxlan 1 status is up/up.

    Args:
        device (InventoryDevice): InventoryDevice instance containing all devices information.

    Returns:
        TestResult instance with
        * result = "unset" if the test has not been executed
        * result = "success" if vxlan1 interface is UP UP
        * result = "failure" otherwise.
        * result = "error" if any exception is caught

    """
    response = await device.session.cli(command="show interfaces description", ofmt="json")
    logger.debug(f"query result is: {response}")

    response_data = response["interfaceDescriptions"]

    if "Vxlan1" not in response_data:
        result.is_failure("No interface VXLAN 1 detected.")
    else:
        protocol_status = response_data["Vxlan1"]["lineProtocolStatus"]
        interface_status = response_data["Vxlan1"]["interfaceStatus"]
        if protocol_status == "up" and interface_status == "up":
            result.is_success()
        else:
            result.messages.append(
                f"Vxlan interface is {protocol_status}/{interface_status}."
            )

    return result


@anta_test
async def verify_vxlan_config_sanity(
    device: InventoryDevice, result: TestResult
) -> TestResult:
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
        category: content
        for category, content in response_data.items()
        if category in ["localVtep", "mlag"] and content["allCheckPass"] is not True
    }

    if len(failed_categories) > 0:
        result.is_failure(
            f"Vxlan config sanity check is not passing: {failed_categories}"
        )
    else:
        result.is_success()

    return result
