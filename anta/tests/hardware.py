"""
Test functions related to the hardware or environement
"""
import logging
from typing import List, Optional

from anta.decorators import skip_on_platforms
from anta.inventory.models import InventoryDevice
from anta.result_manager.models import TestResult
from anta.tests import anta_test

logger = logging.getLogger(__name__)


@skip_on_platforms(["cEOSLab", "vEOS-lab"])
@anta_test
async def verify_transceivers_manufacturers(
    device: InventoryDevice,
    result: TestResult,
    manufacturers: Optional[List[str]] = None,
) -> TestResult:
    """
    Verifies the device is only using transceivers from supported manufacturers.

    Args:
        device (InventoryDevice): InventoryDevice instance containing all devices information.
        manufacturers (list): List of allowed transceivers manufacturers.

    Returns:
        TestResult instance with
        * result = "unset" if the test has not been executed
        * result = "skipped" if the test was not executed because no manufacturers were given
        * result = "success" if the device is only using transceivers from supported manufacturers.
        * result = "failure" otherwise.
        * result = "error" if any exception is caught

    """

    if not manufacturers:
        result.is_skipped(
            "verify_transceivers_manufacturers was not run as no "
            "manufacturers were given"
        )
        return result

    response = await device.session.cli(command="show inventory", ofmt="json")
    logger.debug(f"query result is: {response}")

    wrong_manufacturers = {
        interface: value["mfgName"]
        for interface, value in response["xcvrSlots"].items()
        if value["mfgName"] not in manufacturers
    }

    if not wrong_manufacturers:
        result.is_success()
    else:
        result.is_failure(
            "The following interfaces have transceivers from unauthorized manufacturers"
        )
        result.messages.append(str(wrong_manufacturers))

    return result


@skip_on_platforms(["cEOSLab", "vEOS-lab"])
@anta_test
async def verify_system_temperature(
    device: InventoryDevice, result: TestResult
) -> TestResult:

    """
    Verifies the device temperature is currently OK
    and the device did not report any temperature alarm in the past.

    Args:
        device (InventoryDevice): InventoryDevice instance containing all devices information.

    Returns:
        TestResult instance with
        * result = "unset" if the test has not been executed
        * result = "success" if the device temperature is OK.
        * result = "failure" otherwise.
        * result = "error" if any exception is caught

    """
    response = await device.session.cli(
        command="show system environment temperature", ofmt="json"
    )
    logger.debug(f"query result is: {response}")

    if response["systemStatus"] == "temperatureOk":
        result.is_success()
    else:
        result.is_failure(
            f"Device temperature is not OK, systemStatus: {response['systemStatus'] }"
        )

    return result


@skip_on_platforms(["cEOSLab", "vEOS-lab"])
@anta_test
async def verify_transceiver_temperature(
    device: InventoryDevice, result: TestResult
) -> TestResult:

    """
    Verifies the transceivers temperature is currently OK
    and the device did not report any alarm in the past for its transceivers temperature.

    Args:
        device (InventoryDevice): InventoryDevice instance containing all devices information.

    Returns:
        TestResult instance with
        * result = "unset" if the test has not been executed
        * result = "success" if the device transceivers temperature of the device is currently OK
                             AND the device did not report any alarm in the past for its transceivers temperature.
        * result = "failure" otherwise,
        * result = "error" if any exception is caught

    """
    response = await device.session.cli(
        command="show system environment temperature transceiver", ofmt="json"
    )
    logger.debug(f"query result is: {response}")

    # Get the list of sensors
    sensors = response["tempSensors"]

    wrong_sensors = {
        sensor["name"]: {
            "hwStatus": sensor["hwStatus"],
            "alertCount": sensor["alertCount"],
        }
        for sensor in sensors
        if sensor["hwStatus"] != "ok" or sensor["alertCount"] != 0
    }
    if not wrong_sensors:
        result.is_success()
    else:
        result.is_failure(
            "The following sensors do not have the correct temperature or had alarms in the past:"
        )
        result.messages.append(str(wrong_sensors))

    return result


@skip_on_platforms(["cEOSLab", "vEOS-lab"])
@anta_test
async def verify_environment_cooling(
    device: InventoryDevice, result: TestResult
) -> TestResult:

    """
    Verifies the fans status is OK.

    Args:
        device (InventoryDevice): InventoryDevice instance containing all devices information.

    Returns:
        TestResult instance with
        * result = "unset" if the test has not been executed
        * result = "success" if the fans status is OK.
        * result = "failure" otherwise.
        * result = "error" if any exception is caught

    """
    response = await device.session.cli(command="show system environment cooling", ofmt="json")
    logger.debug(f"query result is: {response}")

    if response["systemStatus"] == "coolingOk":
        result.is_success()
    else:
        result.is_failure(
            f"Device cooling is not OK, systemStatus: {response['systemStatus'] }"
        )

    return result


@skip_on_platforms(["cEOSLab", "vEOS-lab"])
@anta_test
async def verify_environment_power(device: InventoryDevice, result: TestResult) -> TestResult:

    """
    Verifies the power supplies status is OK.

    Args:
        device (InventoryDevice): InventoryDevice instance containing all devices information.

    Returns:
        TestResult instance with
        * result = "unset" if the test has not been executed
        * result = "success" if the power supplies status is OK.
        * result = "failure" otherwise.
        * result = "error" if any exception is caught

    """
    response = await device.session.cli(command="show system environment power", ofmt="json")
    logger.debug(f"query result is: {response}")

    wrong_power_supplies = {
        powersupply: {"state": value["state"]}
        for powersupply, value in response["powerSupplies"].items()
        if value["state"] != "ok"
    }
    if not wrong_power_supplies:
        result.is_success()
    else:
        result.is_failure("The following power suppliers are not ok:")
        result.messages.append(str(wrong_power_supplies))

    return result


@skip_on_platforms(["cEOSLab", "vEOS-lab"])
@anta_test
async def verify_adverse_drops(device: InventoryDevice, result: TestResult) -> TestResult:

    """
    Verifies there is no adverse drops on DCS-7280E and DCS-7500E switches.

    Args:
        device (InventoryDevice): InventoryDevice instance containing all devices information.

    Returns:
        TestResult instance with
        * result = "unset" if the test has not been executed
        * result = "success" if the device (DCS-7280E and DCS-7500E) doesnt reports adverse drops.
        * result = "failure" if the device (DCS-7280E and DCS-7500E) report adverse drops.
        * result = "error" if any exception is caught

    """
    response = await device.session.cli(command="show hardware counter drop", ofmt="json")
    logger.debug(f"query result is: {response}")

    if response["totalAdverseDrops"] == 0:
        result.is_success()
    else:
        result.is_failure(
            f"Device TotalAdverseDrops counter is {response['totalAdverseDrops']}."
        )

    return result
