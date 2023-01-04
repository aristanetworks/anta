"""
OSPF test functions
"""
import logging

from anta.inventory.models import InventoryDevice
from anta.result_manager.models import TestResult
from anta.tests import anta_test

logger = logging.getLogger(__name__)


@anta_test
async def verify_ospf_state(device: InventoryDevice, result: TestResult) -> TestResult:
    """
    Verifies all OSPF neighbors are in FULL state.

    Args:
        device (InventoryDevice): InventoryDevice instance containing all devices information.

    Returns:
        TestResult instance with
        * result = "unset" if the test has not been executed
        * result = "success" if all OSPF neighbors are FULL.
        * result = "failure" otherwise.
        * result = "error" if any exception is caught
    """
    response = await device.session.cli(
        command="show ip ospf neighbor | exclude FULL|Address", ofmt="text"
    )
    logger.debug(f"query result is: {response}")
    if len(response) == 0:
        result.is_skipped("no OSPF neighbor found")
        return result
    if response.count("\n") == 0:
        result.is_success()
    else:
        result.is_failure("Some neighbors are not correctly configured.")

    return result


@anta_test
async def verify_ospf_count(
    device: InventoryDevice, result: TestResult, number: int
) -> TestResult:
    """
    Verifies the number of OSPF neighbors in FULL state is the one we expect.

    Args:
        device (InventoryDevice): InventoryDevice instance containing all devices information.
        number (int): The expected number of OSPF neighbors in FULL state.

    Returns:
        TestResult instance with
        * result = "unset" if the test has not been executed
        * result = "skipeed" if the `number` parameter is missing
        * result = "success" if device has correct number of devices
        * result = "failure" otherwise.
        * result = "error" if any exception is caught
    """
    if not number:
        result.is_skipped(
            "verify_igmp_snooping_vlans was not run as no number was given"
        )
        return result

    response = await device.session.cli(
        command="show ip ospf neighbor | exclude  Address", ofmt="text"
    )
    logger.debug(f"query result is: {response}")
    if len(response) == 0:
        result.is_skipped("no OSPF neighbor found")
        return result
    response_data = response.count("FULL")
    if response_data.count("FULL") == number:
        result.is_success()
    else:
        result.is_failure(
            f'device has {response_data.count("FULL")} neighbors (expected {number}'
        )

    return result
