"""
OSPF test functions
"""
from jsonrpclib import jsonrpc
from anta.inventory.models import InventoryDevice
from anta.result_manager.models import TestResult


def verify_ospf_state(device: InventoryDevice) -> TestResult:
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
    result = TestResult(host=str(device.host), test="verify_ospf_state")
    try:
        response = device.session.runCmds(
            1, ["show ip ospf neighbor | exclude FULL|Address"], "text"
        )
        if response[0]["output"].count("\n") == 0:
            result.is_success()
        else:
            result.is_failure("Some neighbors are not correctly configured.")
    except (jsonrpc.AppError, KeyError) as e:
        result.is_error(str(e))
    return result


def verify_ospf_count(device: InventoryDevice, number: int) -> TestResult:
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
    result = TestResult(host=str(device.host), test="verify_ospf_count")
    if not number:
        result.is_skipped(
            "verify_igmp_snooping_vlans was not run as no number was given"
        )
        return result
    try:
        response = device.session.runCmds(
            1, ["show ip ospf neighbor | exclude  Address"], "text"
        )
        response_data = response[0]["output"].count("FULL")
        if response_data.count("FULL") == number:
            result.is_success()
        else:
            result.is_failure(
                f'device has {response_data.count("FULL")} neighbors (expected {number}'
            )
    except (jsonrpc.AppError, KeyError) as e:
        result.is_error(str(e))
    return result
