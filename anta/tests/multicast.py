"""
Test functions related to multicast
"""
import logging
from typing import List

from anta.inventory.models import InventoryDevice
from anta.result_manager.models import TestResult
from anta.tests import anta_test

logger = logging.getLogger(__name__)


@anta_test
async def verify_igmp_snooping_vlans(
    device: InventoryDevice, result: TestResult, vlans: List[str], configuration: str
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
    if not vlans or not configuration:
        result.result = "skipped"
        result.messages.append(
            "verify_igmp_snooping_vlans was not run as no "
            "vlans or configuration was given"
        )
        return result
    response = await device.session.cli(command="show ip igmp snooping", ofmt="json")
    logger.debug(f"query result is: {response}")

    result.is_success()
    for vlan in vlans:
        if vlan not in response["vlans"]:
            result.is_failure(f"Supplied vlan {vlan} is not present on the device.")
            continue

        igmp_state = response["vlans"][str(vlan)]["igmpSnoopingState"]
        if igmp_state != configuration:
            result.is_failure()
            result.messages.append(f"IGMP state for vlan {vlan} is {igmp_state}")

    return result


@anta_test
async def verify_igmp_snooping_global(
    device: InventoryDevice, result: TestResult, configuration: str
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
    if not configuration:
        result.is_skipped(
            "verify_igmp_snooping_global was not run as no configuration was given"
        )
        return result

    response = await device.session.cli(command="show ip igmp snooping", ofmt="json")
    logger.debug(f"query result is: {response}")

    igmp_state = response["igmpSnoopingState"]
    if igmp_state == configuration:
        result.is_success()
    else:
        result.is_failure(f"IGMP state is not valid: {igmp_state}")

    return result
