"""
Test functions related to the EOS various management settings
"""
import logging

from anta.inventory.models import InventoryDevice
from anta.result_manager.models import TestResult
from anta.tests import anta_test

logger = logging.getLogger(__name__)


@anta_test
async def verify_banner_motd(device: InventoryDevice, result: TestResult, banner: str) -> TestResult:
    """
    Verifies if the device is running the correct banner motd.

    Args:
        device (InventoryDevice): InventoryDevice instance containing all devices information.
        banner (str): Required banner motd to test against.

    Returns:
        TestResult instance with
        * result = "unset" if the test has not been executed
        * result = "success" if banner motd matches
        * result = "failure" otherwise
        * result = "error" if any exception is caught
    """
    if not banner:
        result.is_skipped(
            "verify_banner_motd was not run as no banner was given"
        )
        return result

    device.assert_enable_password_is_not_none("verify_banner_motd")

    banner = banner.rstrip("\n") if banner.endswith("\n") else banner

    enable_cmd = {"cmd": "enable", "input": str(device.enable_password)}
    commands = [enable_cmd, "show banner motd"]
    response = await device.session.cli(commands=commands, ofmt="json")
    logger.debug(f"query result is: {response}")

    motd = response[1]["motd"].rstrip("\n")

    if motd == banner:
        result.is_success()
    elif motd == "":
        result.is_failure(
            "Device has no banner motd configured"
        )
    else:
        result.is_failure(
            "Device has a different banner motd configured"
        )
    return result


@anta_test
async def verify_banner_login(device: InventoryDevice, result: TestResult, banner: str) -> TestResult:
    """
    Verifies if the device is running the correct banner login.

    Args:
        device (InventoryDevice): InventoryDevice instance containing all devices information.
        banner (str): Required banner login to test against.

    Returns:
        TestResult instance with
        * result = "unset" if the test has not been executed
        * result = "success" if banner login matches
        * result = "failure" otherwise
        * result = "error" if any exception is caught
    """
    if not banner:
        result.is_skipped(
            "verify_banner_login was not run as no banner was given"
        )
        return result

    device.assert_enable_password_is_not_none("verify_banner_login")

    banner = banner.rstrip("\n") if banner.endswith("\n") else banner

    enable_cmd = {"cmd": "enable", "input": str(device.enable_password)}
    commands = [enable_cmd, "show banner login"]
    response = await device.session.cli(commands=commands, ofmt="json")
    logger.debug(f"query result is: {response}")

    motd = response[1]["loginBanner"].rstrip("\n")

    if motd == banner:
        result.is_success()
    elif motd == "":
        result.is_failure(
            "Device has no banner login configured"
        )
    else:
        result.is_failure(
            "Device has a different banner login configured"
        )
        result.is_failure()
    return result


@anta_test
async def verify_hostname(device: InventoryDevice, result: TestResult) -> TestResult:
    """
    Verifies if the device is running the correct hostname.

    Args:
        device (InventoryDevice): InventoryDevice instance containing all devices information.

    Returns:
        TestResult instance with
        * result = "unset" if the test has not been executed
        * result = "success" if hostname matches
        * result = "failure" otherwise
        * result = "error" if any exception is caught
    """
    # TODO: device_name should come from AVD facts instead of ANTA inventory
    device_name = device.name
    response = await device.session.cli(command="show hostname", ofmt="json")
    logger.debug(f"query result is: {response}")
    hostname = response["hostname"]
    if hostname == device_name:
        result.is_success()
    else:
        result.is_failure(
            f"Device hostname ({hostname}) is not matching"
        )
    return result
