"""
OSPF test functions
"""
import inspect
import socket
import logging

from jsonrpclib import jsonrpc
from anta.inventory.models import InventoryDevice
from anta.result_manager.models import TestResult

logger = logging.getLogger(__name__)


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
    function_name = inspect.stack()[0][3]
    logger.debug(f"Start {function_name} check for host {device.host}")
    result = TestResult(host=str(device.host), test=function_name)
    try:
        response = device.session.runCmds(
            1, ["show ip ospf neighbor | exclude FULL|Address"], "text"
        )
        logger.debug(f'query result is: {response}')
        if len(response[0]["output"]) == 0:
            result.is_skipped('no OSPF neighbor found')
            return result
        if response[0]["output"].count("\n") == 0:
            result.is_success()
        else:
            result.is_failure("Some neighbors are not correctly configured.")
    except (jsonrpc.AppError, KeyError, socket.timeout) as e:
        logger.error(
            f'exception raised for {inspect.stack()[0][3]} -  {device.host}: {str(e)}')

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
    function_name = inspect.stack()[0][3]
    logger.debug(f"Start {function_name} check for host {device.host}")
    result = TestResult(host=str(device.host), test=function_name)
    if not number:
        result.is_skipped(
            "verify_igmp_snooping_vlans was not run as no number was given"
        )
        return result
    try:
        response = device.session.runCmds(
            1, ["show ip ospf neighbor | exclude  Address"], "text"
        )
        logger.debug(f'query result is: {response}')
        if len(response[0]["output"]) == 0:
            result.is_skipped('no OSPF neighbor found')
            return result
        response_data = response[0]["output"].count("FULL")
        if response_data.count("FULL") == number:
            result.is_success()
        else:
            result.is_failure(
                f'device has {response_data.count("FULL")} neighbors (expected {number}'
            )
    except (jsonrpc.AppError, KeyError, socket.timeout) as e:
        logger.error(
            f'exception raised for {inspect.stack()[0][3]} -  {device.host}: {str(e)}')

        result.is_error(str(e))
    return result
