"""
Test functions related to system-level features and protocols
"""
import logging
from typing import Optional

from anta.inventory.models import InventoryDevice
from anta.result_manager.models import TestResult
from anta.tests import anta_test

logger = logging.getLogger(__name__)


@anta_test
async def verify_uptime(
    device: InventoryDevice, result: TestResult, minimum: Optional[int] = None
) -> TestResult:
    """
    Verifies the device uptime is higher than a value.

    Args:
        device (InventoryDevice): InventoryDevice instance containing all devices information.
        minimum (int): Minimum uptime in seconds.

    Returns:
        TestResult instance with
        * result = "unset" if the test has not been executed
        * result = "skipped" if the `minimum` parameter is  missing
        * result = "success" if uptime is greater than minimun
        * result = "failure" otherwise.
        * result = "error" if any exception is caught

    """
    if not minimum:
        result.is_skipped("verify_uptime was not run as no minimum were given")
        return result

    response = await device.session.cli(command="show uptime", ofmt="json")
    logger.debug(f"query result is: {response}")
    if response["upTime"] > minimum:
        result.is_success()
    else:
        result.is_failure(f"Uptime is {response['upTime']}")

    return result


@anta_test
async def verify_reload_cause(
    device: InventoryDevice, result: TestResult
) -> TestResult:
    """
    Verifies the last reload of the device was requested by a user.

    Test considers the following messages as normal and will return success. Failure is for other messages
    * Reload requested by the user.
    * Reload requested after FPGA upgrade

    Args:
        device (InventoryDevice): InventoryDevice instance containing all devices information.

    Returns:
        TestResult instance with
        * result = "unset" if the test has not been executed
        * result = "success" if reload cause is standard
        * result = "failure" otherwise.
        * result = "error" if any exception is caught

    """
    response = await device.session.cli(command="show reload cause", ofmt="json")
    logger.debug(f"query result is: {response}")
    if "resetCauses" not in response.keys() or len(response["resetCauses"]) == 0:
        result.is_error("no reload cause available")
        return result

    response_data = response.get("resetCauses")[0].get("description")
    if response_data in [
        "Reload requested by the user.",
        "Reload requested after FPGA upgrade",
    ]:
        result.is_success()
    else:
        result.is_failure(f"Reload cause is {response_data}")

    return result


@anta_test
async def verify_coredump(device: InventoryDevice, result: TestResult) -> TestResult:
    """
    Verifies there is no core file.

    Args:
        device (InventoryDevice): InventoryDevice instance containing all devices information.

    Returns:
        TestResult instance with
        * result = "unset" if the test has not been executed
        * result = "success" if device has no core-dump
        * result = "failure" otherwise.
        * result = "error" if any exception is caught

    """
    device.assert_enable_password_is_not_none("verify_coredump")

    response = await device.session.cli(
        commands=[
            {"cmd": "enable", "input": str(device.enable_password)},
            "bash timeout 10 ls /var/core",
        ],
        ofmt="text",
    )
    logger.debug(f"query result is: {response}")
    response_data = response[1]
    if len(response_data) == 0:
        result.is_success()
    else:
        result.is_failure(f"Core-dump(s) have been found: {response_data}")

    return result


@anta_test
async def verify_agent_logs(device: InventoryDevice, result: TestResult) -> TestResult:
    """
    Verifies there is no agent crash reported on the device.

    Args:
        device (InventoryDevice): InventoryDevice instance containing all devices information.

    Returns:
        TestResult instance with
        * result = "unset" if the test has not been executed
        * result = "success" if there is no agent crash
        * result = "failure" otherwise.
        * result = "error" if any exception is caught

    """
    response = await device.session.cli(command="show agent logs crash", ofmt="text")
    logger.debug(f"query result is: {response}")
    if len(response) == 0:
        result.is_success()
    else:
        result.is_failure(f"device reported some agent crashes: {response}")

    return result


@anta_test
async def verify_syslog(device: InventoryDevice, result: TestResult) -> TestResult:
    """
    Verifies the device had no syslog message with a severity of warning (or a more severe message)
    during the last 7 days.

    Args:
        device (InventoryDevice): InventoryDevice instance containing all devices information.

    Returns:
        TestResult instance with
        * result = "unset" if the test has not been executed
        * result = "success" if syslog has no WARNING message
        * result = "failure" otherwise.
        * result = "error" if any exception is caught
    """
    response = await device.session.cli(
        command="show logging last 7 days threshold warnings", ofmt="text"
    )
    logger.debug(f"query result is: {response}")
    if len(response) == 0:
        result.is_success()
    else:
        result.is_failure(
            "Device has some log messages with a severity WARNING or higher"
        )

    return result


@anta_test
async def verify_cpu_utilization(
    device: InventoryDevice, result: TestResult
) -> TestResult:
    """
    Verifies the CPU utilization is less than 75%.

    Args:
        device (InventoryDevice): InventoryDevice instance containing all devices information.

    Returns:
        TestResult instance with
        * result = "unset" if the test has not been executed
        * result = "success" if CPU usage is lower than 75%
        * result = "failure" otherwise.
        * result = "error" if any exception is caught
    """
    response = await device.session.cli(command="show processes top once", ofmt="json")
    logger.debug(f"query result is: {response}")
    response_data = response["cpuInfo"]["%Cpu(s)"]["idle"]
    if response_data > 25:
        result.is_success()
    else:
        result.is_failure(f"device reported a high CPU utilization ({response_data}%)")

    return result


@anta_test
async def verify_memory_utilization(
    device: InventoryDevice, result: TestResult
) -> TestResult:
    """
    Verifies the memory utilization is less than 75%.

    Args:
        device (InventoryDevice): InventoryDevice instance containing all devices information.

    Returns:
        TestResult instance with
        * result = "unset" if the test has not been executed
        * result = "success" if memory usage is lower than 75%
        * result = "failure" otherwise.
        * result = "error" if any exception is caught
    """
    response = await device.session.cli(command="show version", ofmt="json")
    logger.debug(f"query result is: {response}")
    memory_usage = float(response["memFree"]) / float(response["memTotal"])
    if memory_usage > 0.25:
        result.is_success()
    else:
        result.is_failure(f"device report a high memory usage: {memory_usage*100}%")

    return result


@anta_test
async def verify_filesystem_utilization(
    device: InventoryDevice, result: TestResult
) -> TestResult:

    """
    Verifies each partition on the disk is used less than 75%.

    Args:
        device (InventoryDevice): InventoryDevice instance containing all devices information.

    Returns:
        TestResult instance with
        * result = "unset" if the test has not been executed
        * result = "success" if disk is used less than 75%
        * result = "failure" otherwise.
        * result = "error" if any exception is caught
    """
    response = await device.session.cli(
        commands=[
            {"cmd": "enable", "input": device.enable_password},
            "bash timeout 10 df -h",
        ],
        ofmt="text",
    )
    logger.debug(f"query result is: {response}")
    result.is_success()
    for line in response[1].split("\n")[1:]:
        if (
            "loop" not in line
            and len(line) > 0
            and int(line.split()[4].replace("%", "")) > 75
        ):
            result.is_failure(
                f'mount point {line} is higher than 75% (reprted {int(line.split()[4].replace(" % ", ""))})'
            )

    return result


@anta_test
async def verify_ntp(device: InventoryDevice, result: TestResult) -> TestResult:

    """
    Verifies NTP is synchronised.

    Args:
        device (InventoryDevice): InventoryDevice instance containing all devices information.

    Returns:
        TestResult instance with
        * result = "unset" if the test has not been executed
        * result = "success" if synchronized with NTP server
        * result = "failure" otherwise.
        * result = "error" if any exception is caught
    """
    response = await device.session.cli(command="show ntp status", ofmt="text")
    logger.debug(f"query result is: {response}")
    if response.split("\n")[0].split(" ")[0] == "synchronised":
        result.is_success()
    else:
        data = response.split("\n")[0]
        result.is_failure(f"not sync with NTP server ({data})")

    return result
