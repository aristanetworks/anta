"""
Test functions related to ASIC profiles
"""
import inspect
import logging
import socket

from jsonrpclib import jsonrpc
from anta.inventory.models import InventoryDevice
from anta.result_manager.models import TestResult

logger = logging.getLogger(__name__)


def verify_unified_forwarding_table_mode(
    device: InventoryDevice, mode: str
) -> TestResult:

    """
    Verifies the device is using the expected Unified Forwarding Table mode.

    Args:
        device (InventoryDevice): InventoryDevice instance containing all devices information.
        mode (str): The expected Unified Forwarding Table mode.

    Returns:
        TestResult instance with
        * result = "unset" if the test has not been executed
        * result = "mode" if the `mode` parameter is missing
        * result = "success" if UFT mode is correct
        * result = "failure" otherwise.
        * result = "error" if any exception is caught
    """
    function_name = inspect.stack()[0][3]
    logger.debug(f"Start {function_name} check for host {device.host}")
    result = TestResult(host=str(device.host), test=function_name)
    if not mode:
        result.is_skipped(
            "verify_unified_forwarding_table_mode was not run as no mode was given"
        )
        return result
    if device.hw_model in ["cEOSLab", "VEOS-LAB"]:
        result.is_skipped(
            "verify_tcam_profile was not run as feature is not supported on this HW")
        return result
    try:
        response = device.session.runCmds(
            1, ["show platform trident forwarding-table partition"], "json"
        )
        logger.debug(f'query result is: {response}')
        response_data = response[0]["uftMode"]
        if response_data == mode:
            result.is_success()
        else:
            result.is_failure(
                f"device is not running correct UFT mode (expected: {mode} / running: {response_data})"
            )
    except (jsonrpc.AppError, KeyError, socket.timeout) as e:
        logger.error(
            f'exception raised for {inspect.stack()[0][3]} -  {device.host}: {str(e)}')
        result.is_error(str(e))
    return result


def verify_tcam_profile(device: InventoryDevice, profile: str) -> TestResult:

    """
    Verifies the configured TCAM profile is the expected one.

    Args:
        device (InventoryDevice): InventoryDevice instance containing all devices information.
        profile (str): The expected TCAM profile.0

    Returns:
        TestResult instance with
        * result = "unset" if the test has not been executed
        * result = "mode" if the `profile` parameter is missing
        * result = "success" if TCAM profile is correct
        * result = "failure" otherwise.
        * result = "error" if any exception is caught
    """
    function_name = inspect.stack()[0][3]
    logger.debug(f"Start {function_name} check for host {device.host}")
    result = TestResult(host=str(device.host), test=function_name)
    if not profile:
        result.is_skipped("verify_tcam_profile was not run as no profile was given")
        return result
    if device.hw_model in ["cEOSLab", "VEOS-LAB"]:
        result.is_skipped(
            "verify_tcam_profile was not run as feature is not supported on this HW")
        return result
    try:
        response = device.session.runCmds(1, ["show hardware tcam profile"], "json")
        logger.debug(f'query result is: {response}')
        if (
            response[0]["pmfProfiles"]["FixedSystem"]["status"]
            == response[0]["pmfProfiles"]["FixedSystem"]["config"]
        ) and (response[0]["pmfProfiles"]["FixedSystem"]["status"] == profile):
            result.is_success()
        else:
            result.is_failure(
                f'Incorrect profile configured on device: {response[0]["pmfProfiles"]["FixedSystem"]["status"]}'
            )
    except (jsonrpc.AppError, KeyError, socket.timeout) as e:
        logger.error(
            f'exception raised for {inspect.stack()[0][3]} -  {device.host}: {e.__class__.__name__} - {str(e)}')
        result.is_error(str(e))
    return result
