"""
Test functions related to multicast
"""
from typing import List
from jsonrpclib import jsonrpc
from anta.inventory.models import InventoryDevice
from anta.result_manager.models import TestResult


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
    result = TestResult(host=str(device.host), test="verify_igmp_snooping_vlans")
    if not vlans or not configuration:
        result.result = "skipped"
        result.messages.append(
            "verify_igmp_snooping_vlans was not run as no "
            "vlans or configuration was given"
        )
        return result
    try:
        response = device.session.runCmds(1, ["show ip igmp snooping"], "json")
        result.is_success()
        for vlan in vlans:
            igmp_state = response[0]["vlans"][str(vlan)]["igmpSnoopingState"]
            if igmp_state != configuration:
                result.is_failure()
                result.messages.append(f"IGMP state for vlan {vlan} is {igmp_state}")
    except (jsonrpc.AppError, KeyError) as e:
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
    result = TestResult(host=str(device.host), test="verify_igmp_snooping_global")
    if not configuration:
        result.is_skipped(
            "verify_igmp_snooping_global was not run as no configuration was given"
        )
        return result
    try:
        response = device.session.runCmds(1, ["show ip igmp snooping"], "json")
        igmp_state = response[0]["igmpSnoopingState"]
        if igmp_state == configuration:
            result.is_success()
        else:
            result.is_failure(f"IGMP state is not valid: {igmp_state}")
    except (jsonrpc.AppError, KeyError) as e:
        result.is_error(str(e))
    return result
