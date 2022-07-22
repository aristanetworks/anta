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
        * result = "unset" if test has not been executed
        * result = "success" if all OSPF neighbors are FULL.
        * result = "failure" otherwise.
        * result = "error" if any exception is caught
    """
    result = TestResult(host=str(device.host),
                        test="verify_ospf_state")
    try:
        response = device.session.runCmds(1, ['show ip ospf neighbor | exclude FULL|Address'], 'text')
        if response[0]['output'].count('\n') == 0:
            result.result = 'success'
        else:
            result.result = 'failure'
    except (jsonrpc.AppError, KeyError) as e:
        result.messages.append(str(e))
        result.result = 'error'
    return result


def verify_ospf_count(device: InventoryDevice, number : int) -> TestResult:
    """
    Verifies the number of OSPF neighbors in FULL state is the one we expect.

    Args:
        device (InventoryDevice): InventoryDevice instance containing all devices information.
        number (int): The expected number of OSPF neighbors in FULL state.

    Returns:
        TestResult instance with
        * result = "unset" if test has not been executed
        * result = "success" if device has correct number of devices
        * result = "failure" otherwise.
        * result = "error" if any exception is caught
    """
    result = TestResult(host=str(device.host),
                        test="verify_ospf_count")
    if not number:
        result.result = "unset"
        result.messages.append(
            "verify_igmp_snooping_vlans was not run as no "
            "number was givem"
        )
        return result
    try:
        response = device.session.runCmds(1, ['show ip ospf neighbor | exclude  Address'], 'text')
        response_data = response[0]['output'].count('FULL')
        if response_data.count('FULL') == number:
            result.result = 'success'
        else:
            result.result = 'failure'
            result.messages.append(f'device has {response_data.count("FULL")} neighbors (expected {number}')
    except (jsonrpc.AppError, KeyError) as e:
        result.messages.append(str(e))
        result.result = 'error'
    return result
