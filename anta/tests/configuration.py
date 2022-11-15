"""
Test functions related to the device configuration
"""
import logging

from anta.tests import anta_test
from anta.inventory.models import InventoryDevice
from anta.result_manager.models import TestResult

logger = logging.getLogger(__name__)


@anta_test
def verify_zerotouch(device: InventoryDevice, result: TestResult) -> TestResult:

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
    response = device.session.runCmds(1, ["show zerotouch"], "json")
    logger.debug(f"query result is: {response}")

    if response[0]["mode"] == "disabled":
        result.is_success()
    else:
        result.is_failure("ZTP is NOT disabled")

    return result


@anta_test
def verify_running_config_diffs(
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
    device.assert_enable_password_is_not_none("verify_running_config_diffs")

    response = device.session.runCmds(
        1,
        [
            {"cmd": "enable", "input": str(device.enable_password)},
            "show running-config diffs",
        ],
        "text",
    )
    logger.debug(f"query result is: {response}")

    if len(response[1]["output"]) == 0:
        result.is_success()

    else:
        result.is_failure()
        for line in response[1]["output"]:
            result.is_failure(line)

    return result
