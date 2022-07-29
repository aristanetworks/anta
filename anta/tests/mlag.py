"""
Test functions related to Multi-Chassis LAG
"""
import inspect
import socket
import logging

from jsonrpclib import jsonrpc
from anta.inventory.models import InventoryDevice
from anta.result_manager.models import TestResult

logger = logging.getLogger(__name__)


def verify_mlag_status(device: InventoryDevice) -> TestResult:
    """
    Verifies the MLAG status:
    state is active, negotiation status is connected, local int is up, peer link is up.

    Args:
        device (InventoryDevice): InventoryDevice instance containing all devices information.

    Returns:
        TestResult instance with
        * result = "unset" if the test has not been executed
        * result = "success" if the MLAG status is OK
        * result = "failure" otherwise.
        * result = "error" if any exception is caught

    """
    function_name = inspect.stack()[0][3]
    logger.debug(f"Start {function_name} check for host {device.host}")
    result = TestResult(host=str(device.host), test=function_name)

    try:
        response = device.session.runCmds(1, ["show mlag"], "json")

        if response[0]["state"] == "disabled":
            result.is_skipped("MLAG is disabled")
        elif (
            response[0]["state"] != "active"
            or response[0]["negStatus"] != "connected"
            or response[0]["localIntfStatus"] != "up"
            or response[0]["peerLinkStatus"] != "up"
        ):
            result.is_failure(f"MLAG status is not OK: {response[0]}")
        else:
            result.is_success()

    except (jsonrpc.AppError, KeyError, socket.timeout) as e:
        logger.error(
            f'exception raised for {inspect.stack()[0][3]} -  {device.host}: {str(e)}')

        result.is_error(str(e))
    return result


def verify_mlag_interfaces(device: InventoryDevice) -> TestResult:
    """
    Verifies there is no inactive or active-partial MLAG interfaces.

    Args:
        device (InventoryDevice): InventoryDevice instance containing all devices information.

    Returns:
        TestResult instance with
        * result = "unset" if the test has not been executed
        * result = "success" if there is no inactive or active-partial MLAG interfaces.
        * result = "failure" otherwise.
        * result = "error" if any exception is caught

    """
    function_name = inspect.stack()[0][3]
    logger.debug(f"Start {function_name} check for host {device.host}")
    result = TestResult(host=str(device.host), test=function_name)

    try:
        response = device.session.runCmds(1, ["show mlag"], "json")

        if response[0]["state"] == "disabled":
            result.is_skipped("MLAG is disabled")
        elif (
            response[0]["mlagPorts"]["Inactive"] != 0
            or response[0]["mlagPorts"]["Active-partial"] != 0
        ):
            result.is_failure(f"MLAG status is not OK: {response[0]['mlagPorts']}")
        else:
            result.is_success()

    except (jsonrpc.AppError, KeyError, socket.timeout) as e:
        logger.error(
            f'exception raised for {inspect.stack()[0][3]} -  {device.host}: {str(e)}')

        result.is_error(str(e))
    return result


def verify_mlag_config_sanity(device: InventoryDevice) -> TestResult:
    """
    Verifies there is no MLAG config-sanity inconsistencies.

    Args:
        device (InventoryDevice): InventoryDevice instance containing all devices information.

    Returns:
        TestResult instance with
        * result = "unset" if the test has not been executed
        * result = "success" if there is no MLAG config-sanity inconsistencies
        * result = "failure" otherwise.
        * result = "error" if any exception is caught

    """
    function_name = inspect.stack()[0][3]
    logger.debug(f"Start {function_name} check for host {device.host}")
    result = TestResult(host=str(device.host), test=function_name)

    try:
        response = device.session.runCmds(1, ["show mlag config-sanity"], "json")

        if "mlagActive" not in response[0].keys():
            result.is_error('incorrect JSON response')
        elif response[0]["mlagActive"] is False:
            # MLAG is not running
            result.is_skipped("MLAG is disabled")
        elif (
            len(response[0]["globalConfiguration"]) > 0
            or len(response[0]["interfaceConfiguration"]) > 0
        ):
            result.is_failure()
            if len(response[0]["globalConfiguration"]) > 0:
                result.is_failure(
                    "MLAG config-sanity returned some Global inconsistencies: "
                    f"{response[0]['response']['globalConfiguration']}"
                )
            if len(response[0]["interfaceConfiguration"]) > 0:
                result.is_failure(
                    "MLAG config-sanity returned some Interface inconsistencies: "
                    f"{response[0]['response']['interfaceConfiguration']}"
                )
        else:
            result.is_success()

    except (jsonrpc.AppError, KeyError, socket.timeout) as e:
        logger.error(
            f'exception raised for {inspect.stack()[0][3]} -  {device.host}: {str(e)}')

        result.is_error(str(e))
    return result
