"""
Test functions related to the hardware or environement
"""
from typing import List
from jsonrpclib import jsonrpc
from anta.inventory.models import InventoryDevice
from anta.result_manager.models import TestResult


def verify_transceivers_manufacturers(
    device: InventoryDevice, manufacturers: List[str] = None
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
    result = TestResult(host=str(device.host), test="verify_transceivers_manufacturers")
    if not manufacturers:
        result.is_skipped(
            "verify_transceivers_manufacturers was not run as no "
            "manufacturers were given"
        )
        return result
    try:
        response = device.session.runCmds(1, ["show inventory"], "json")

        wrong_manufacturers = {
            interface: value["mfgName"]
            for interface, value in response[0]["xcvrSlots"].items()
            if value["mfgName"] not in manufacturers
        }
        if len(wrong_manufacturers) == 0:
            result.is_success()
        else:
            result.is_failure(
                "The following interfaces have transceivers from unauthorized manufacturers"
            )
            result.messages.append(str(wrong_manufacturers))

    except (jsonrpc.AppError, KeyError) as e:
        result.is_error(str(e))

    return result


def verify_system_temperature(device: InventoryDevice) -> TestResult:

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
    result = TestResult(host=str(device.host), test="verify_system_temperature")

    try:
        response = device.session.runCmds(
            1, ["show system environment temperature"], "json"
        )

        if response[0]["systemStatus"] == "temperatureOk":
            result.is_success()
        else:
            result.is_failure(
                f"Device temperature is not OK, systemStatus: {response[0]['systemStatus'] }"
            )

    except (jsonrpc.AppError, KeyError) as e:
        result.is_error(str(e))

    return result


def verify_transceiver_temperature(device: InventoryDevice) -> TestResult:

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
    result = TestResult(host=str(device.host), test="verify_transceiver_temperature")

    try:
        response = device.session.runCmds(
            1, ["show system environment temperature transceiver"], "json"
        )

        wrong_sensors = {
            sensor["name"]: {
                "hwStatus": value["hwStatus"],
                "alertCount": value["alertCount"],
            }
            for sensor, value in response[0]["tempSensors"].items()
            if value["hwStatus"] != "ok" or value["alertCount"] != 0
        }
        if len(wrong_sensors) == 0:
            result.is_success()
        else:
            result.is_failure(
                "The following sensors do not have the correct temperature or had alarms in the past:"
            )
            result.messages.append(str(wrong_sensors))

    except (jsonrpc.AppError, KeyError) as e:
        result.is_error(str(e))

    return result


def verify_environment_cooling(device: InventoryDevice) -> TestResult:

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
    result = TestResult(host=str(device.host), test="verify_environment_cooling")

    try:
        response = device.session.runCmds(
            1, ["show system environment cooling"], "json"
        )

        if response[0]["systemStatus"] == "coolingOk":
            result.is_success()
        else:
            result.is_failure(
                f"Device cooling is not OK, systemStatus: {response[0]['systemStatus'] }"
            )

    except (jsonrpc.AppError, KeyError) as e:
        result.is_error(str(e))

    return result


def verify_environment_power(device: InventoryDevice) -> TestResult:

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
    result = TestResult(host=str(device.host), test="verify_environment_power")

    try:
        response = device.session.runCmds(1, ["show system environment power"], "json")

        wrong_power_supplies = {
            powersupply: {"state": value["state"]}
            for powersupply, value in response[0]["powerSupplies"].items()
            if value["state"] != "ok"
        }
        if len(wrong_power_supplies) == 0:
            result.is_success()
        else:
            result.is_failure("The following power suppliers are not ok:")
            result.messages.append(str(wrong_power_supplies))

    except (jsonrpc.AppError, KeyError) as e:
        result.is_error(str(e))

    return result


def verify_adverse_drops(device: InventoryDevice) -> TestResult:

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
    result = TestResult(host=str(device.host), test="verify_adverse_drops")

    try:
        response = device.session.runCmds(1, ["show hardware counter drop"], "json")

        if response[0]["totalAdverseDrops"] == 0:
            result.is_success()
        else:
            result.is_failure(
                f"Device TotalAdverseDrops counter is {response[0]['totalAdverseDrops']}."
            )

    except (jsonrpc.AppError, KeyError) as e:
        result.is_error(str(e))

    return result
