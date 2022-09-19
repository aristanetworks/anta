"""
Test functions related to multicast
"""
import inspect
import logging
from typing import List
import socket

from jsonrpclib import jsonrpc
from anta.inventory.models import InventoryDevice
from anta.result_manager.models import TestResult

logger = logging.getLogger(__name__)


def verify_igmp_snooping_vlans(
    device: InventoryDevice, vlans: List[str], configuration: str
) -> TestResult:
    """
    Verifies the IGMP snooping configuration for some VLANs.

    Args:
        device (InventoryDevice): InventoryDevice instance containing all devices information.
        vlans (List[str]): A list of VLANs
        configuration (str): Expected IGMP snooping configuration (enabled or disabled) for these VLANs.

    Returns:
        TestResult instance with
        * result = "unset" if the test has not been executed
        * result = "success" if IGMP snooping is configured on these vlans
        * result = "failure" otherwise.
        * result = "error" if any exception is caught

    """
    function_name = inspect.stack()[0][3]
    logger.debug(f"Start {function_name} check for host {device.name}")
    result = TestResult(name=device.name, test=function_name)

    if not vlans or not configuration:
        result.result = "skipped"
        result.messages.append(
            "verify_igmp_snooping_vlans was not run as no "
            "vlans or configuration was given"
        )
        return result
    try:
        response = device.session.runCmds(1, ["show ip igmp snooping"], "json")
        logger.debug(f"query result is: {response}")

        result.is_success()
        for vlan in vlans:
            if vlan not in response[0]["vlans"]:
                result.is_failure(f"Supplied vlan {vlan} is not present on the device.")
                continue

            igmp_state = response[0]["vlans"][str(vlan)]["igmpSnoopingState"]
            if igmp_state != configuration:
                result.is_failure()
                result.messages.append(f"IGMP state for vlan {vlan} is {igmp_state}")

    except (jsonrpc.AppError, KeyError, socket.timeout) as e:
        logger.error(
            f"exception raised for {inspect.stack()[0][3]} -  {device.name}: {str(e)}"
        )
        result.is_error(str(e))

    return result


def verify_igmp_snooping_global(
    device: InventoryDevice, configuration: str
) -> TestResult:
    """
    Verifies the IGMP snooping global configuration.

    Args:
        device (InventoryDevice): InventoryDevice instance containing all devices information.
        configuration (str): Expected global IGMP snooping configuration (enabled or disabled).

    Returns:
        TestResult instance with
        * result = "unset" if the test has not been executed
        * result = "skipped" if the `configuration` parameter was missing
        * result = "success" if IGMP snooping is globally configured
        * result = "failure" otherwise.
        * result = "error" if any exception is caught
    """
    function_name = inspect.stack()[0][3]
    logger.debug(f"Start {function_name} check for host {device.name}")
    result = TestResult(name=device.name, test=function_name)

    if not configuration:
        result.is_skipped(
            "verify_igmp_snooping_global was not run as no configuration was given"
        )
        return result
    try:
        response = device.session.runCmds(1, ["show ip igmp snooping"], "json")
        logger.debug(f"query result is: {response}")

        igmp_state = response[0]["igmpSnoopingState"]
        if igmp_state == configuration:
            result.is_success()
        else:
            result.is_failure(f"IGMP state is not valid: {igmp_state}")

    except (jsonrpc.AppError, KeyError, socket.timeout) as e:
        logger.error(
            f"exception raised for {inspect.stack()[0][3]} -  {device.name}: {str(e)}"
        )
        result.is_error(str(e))

    return result
