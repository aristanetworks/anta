"""
Test functions related to the device configuration
"""
import logging

from anta.inventory.models import InventoryDevice
from anta.result_manager.models import TestResult
from anta.tests import anta_test

logger = logging.getLogger(__name__)


@anta_test
async def verify_zerotouch(device: InventoryDevice, result: TestResult) -> TestResult:

    """
    Verifies ZeroTouch is disabled.

    Args:
        device (InventoryDevice): InventoryDevice instance containing all devices information.

    Returns:
        TestResult instance with
        * result = "unset" if the test has not been executed
        * result = "success" if ZTP is disabled
        * result = "failure" if ZTP is enabled
        * result = "error" if any exception is caught

    """
    response = await device.session.cli(command="show zerotouch", ofmt="json")
    logger.debug(f"query result is: {response}")

    if response["mode"] == "disabled":
        result.is_success()
    else:
        result.is_failure("ZTP is NOT disabled")

    return result


@anta_test
async def verify_running_config_diffs(
    device: InventoryDevice, result: TestResult
) -> TestResult:

    """
    Verifies there is no difference between the running-config and the startup-config.

    Args:
        device (InventoryDevice): InventoryDevice instance containing all devices information.

    Returns:
        TestResult instance with
        * result = "unset" if the test has not been executed
        * result = "success" if there is no difference between the running-config and the startup-config
        * result = "failure" if there are differences
        * result = "error" if any exception is caught

    """
    if device.enable_password is not None:
        enable_cmd = {"cmd": "enable", "input": str(device.enable_password)}
    else:
        enable_cmd = {"cmd": "enable"}
    commands = [enable_cmd, "show running-config diffs"]
    response = await device.session.cli(
        commands=commands,
        ofmt="text",
    )

    logger.debug(f"query result is: {response}")

    if len(response[1]) == 0:
        result.is_success()

    else:
        result.is_failure()
        for line in response[1].splitlines():
            result.is_failure(line)

    return result
