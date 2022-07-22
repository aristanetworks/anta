"""
Test functions related to the device configuration
"""
import sys
from jsonrpclib import jsonrpc
from anta.inventory.models import InventoryDevice
from anta.result_manager.models import TestResult


def verify_zerotouch(device: InventoryDevice) -> TestResult:

    """
    Verifies ZeroTouch is disabled.

    Args:
        device (InventoryDevice): InventoryDevice instance containing all devices information.

    Returns:
        TestResult instance with
        * result = "success" if ZTP is disabled
        * result = "failure" if ZTP is enabled
        * result = "error" if any exception is caught

    """
    result = TestResult(host=str(device.host), test=sys._getframe().f_code.co_name)
    try:
        response = device.session.runCmds(1, ["show zerotouch"], "json")

        if response[0]["mode"] == "disabled":
            result.result = "success"
            result.messages.append("ZTP is disabled")
        else:
            result.result = "failure"
            result.messages.append("ZTP is NOT disabled")

    except (jsonrpc.AppError, KeyError) as e:
        result.result = "error"
        result.messages.append(str(e))

    return result


def verify_running_config_diffs(device: InventoryDevice) -> TestResult:

    """
    Verifies there is no difference between the running-config and the startup-config.

    Args:
        device (InventoryDevice): InventoryDevice instance containing all devices information.

    Returns:
        TestResult instance with
        * result = "success" if there is no difference between the running-config and the startup-config
        * result = "failure" if there are differences
        * result = "error" if any exception is caught

    """
    result = TestResult(host=str(device.host), test=sys._getframe().f_code.co_name)
    try:
        if not device.enable_password:
            raise ValueError(
                "verify_running_config_diff requires the device to"
                "have the `enable_password` configured"
            )

        response = device.session.runCmds(
            1,
            [
                {"cmd": "enable", "input": device.enable_password},
                "show running-config diffs",
            ],
            "text",
        )

        if len(response[1]["output"]) == 0:
            result.result = "success"
            result.messages.append(
                "The is no difference between the running-config and the startup-config"
            )

        else:
            result.result = "failure"
            for line in response[1]["output"]:
                result.messages.append(line)

    except (jsonrpc.AppError, KeyError, ValueError) as e:
        result.result = "error"
        result.messages.append(str(e))

    return result
