"""
Test functions related to VXLAN
"""
from jsonrpclib import jsonrpc
from anta.inventory.models import InventoryDevice
from anta.result_manager.models import TestResult


def verify_vxlan(device: InventoryDevice) -> TestResult:
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
    result = TestResult(host=str(device.host), test="verify_vxlan")
    try:
        response = device.session.runCmds(
            1, ["show interfaces description | include Vx1"], "text"
        )
        response_data = response[0]["output"]
        if response_data.count("up") == 2:
            result.is_success()
        else:
            result.is_failure()
            if response_data is not None:
                result.messages.append(f"Vxlan interface is {response_data}")
            else:
                result.messages.append("No interface VXLAN 1 detected")
    except (jsonrpc.AppError, KeyError) as e:
        result.is_error(str(e))
    return result


def verify_vxlan_config_sanity(device: InventoryDevice) -> TestResult:
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
    result = TestResult(host=str(device.host), test="verify_vxlan_config_sanity")
    try:
        response = device.session.runCmds(1, ["show vxlan config-sanity"], "json")
        response_data = response[0]["categories"]

        # TODO - is it really an error here? if there are no categories it just mean there
        # were no warning no?
        if len(response_data) == 0:
            result.result = "error"
            result.messages.append(f"error in device response {response_data}")

        result.is_success()

        for category in response[0]["categories"]:
            if category in ["localVtep", "mlag"]:
                if response_data["allCheckPass"] is not True:
                    result.is_failure(
                        f"Vxlan config sanity check is not passing: {response_data}"
                    )
    except (jsonrpc.AppError, KeyError) as e:
        result.is_error(str(e))
    return result
