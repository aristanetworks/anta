"""
Test functions related to the EOS various SNMP settings
"""
import logging

from anta.inventory.models import InventoryDevice
from anta.result_manager.models import TestResult
from anta.tests import anta_test

logger = logging.getLogger(__name__)


@anta_test
async def verify_snmp_status(device: InventoryDevice, result: TestResult, vrf: str = "default") -> TestResult:
    """
    Verifies if the SNMP agent is enabled.

    Args:
        device (InventoryDevice): InventoryDevice instance containing all devices information.
        vrf(str): VRF to verify. Default is "default".

    Returns:
        TestResult instance with
        * result = "unset" if the test has not been executed
        * result = "success" if SNMP agent is enabled in the specified VRF
        * result = "failure" otherwise
        * result = "error" if any exception is caught
    """
    if not vrf:
        result.is_skipped(
            "verify_snmp_status did not run because vrf was not supplied"
        )
        return result

    response = await device.session.cli(command="show snmp", ofmt="json")
    logger.debug(f"query result is: {response}")

    if response["enabled"] and vrf in response["vrfs"]["snmpVrfs"]:
        result.is_success()
    else:
        result.is_failure(
            "SNMP agent disabled: Either no communities and no users are configured, or no VRFs are configured."
        )
    return result


@anta_test
async def verify_snmp_ipv4_acl(device: InventoryDevice, result: TestResult, number: int, vrf: str = "default") -> TestResult:
    """
    Verifies if the SNMP agent has IPv4 ACL(s) configured.

    Args:
        device (InventoryDevice): InventoryDevice instance containing all devices information.
        number(int): Expected number of SNMP IPv4 ACL(s).
        vrf(str): VRF to verify. Default is "default".

    Returns:
        TestResult instance with
        * result = "unset" if the test has not been executed
        * result = "success" if SNMP agent has IPv4 ACL(s) configured
        * result = "failure" otherwise
        * result = "error" if any exception is caught
    """
    if not number or not vrf:
        result.is_skipped(
            "verify_snmp_ipv4_acl did not run because number or vrf was not supplied"
        )
        return result

    response = await device.session.cli(command="show snmp ipv4 access-list summary", ofmt="json")
    logger.debug(f"query result is: {response}")

    ipv4_acl_list = response["ipAclList"]["aclList"]
    ipv4_acl_number = len(ipv4_acl_list)
    not_configured_acl_list = []

    if ipv4_acl_number != number:
        result.is_failure(
            f"Expected {number} SNMP IPv4 ACL(s) and got {ipv4_acl_number}"
        )
        return result

    for ipv4_acl in ipv4_acl_list:
        if vrf not in ipv4_acl["configuredVrfs"] or vrf not in ipv4_acl["activeVrfs"]:
            not_configured_acl_list.append(ipv4_acl["name"])

    if not_configured_acl_list:
        result.is_failure(
            f"SNMP IPv4 ACL(s) not configured or active in vrf {vrf}: {not_configured_acl_list}"
        )

    else:
        result.is_success()
    return result


@anta_test
async def verify_snmp_ipv6_acl(device: InventoryDevice, result: TestResult, number: int, vrf: str = "default") -> TestResult:
    """
    Verifies if the SNMP agent has IPv6 ACL(s) configured.

    Args:
        device (InventoryDevice): InventoryDevice instance containing all devices information.
        number(int): Expected number of SNMP IPv6 ACL(s).
        vrf(str): VRF to verify. Default is "default".

    Returns:
        TestResult instance with
        * result = "unset" if the test has not been executed
        * result = "success" if SNMP agent has IPv6 ACL(s) configured
        * result = "failure" otherwise
        * result = "error" if any exception is caught
    """
    if not number or not vrf:
        result.is_skipped(
            "verify_snmp_ipv6_acl did not run because number or vrf was not supplied"
        )
        return result

    response = await device.session.cli(command="show snmp ipv6 access-list summary", ofmt="json")
    logger.debug(f"query result is: {response}")

    ipv6_acl_list = response["ipv6AclList"]["aclList"]
    ipv6_acl_number = len(ipv6_acl_list)
    not_configured_acl_list = []

    if ipv6_acl_number != number:
        result.is_failure(
            f"Expected {number} SNMP IPv6 ACL(s) and got {ipv6_acl_number}"
        )
        return result

    for ipv6_acl in ipv6_acl_list:
        if vrf not in ipv6_acl["configuredVrfs"] or vrf not in ipv6_acl["activeVrfs"]:
            not_configured_acl_list.append(ipv6_acl["name"])

    if not_configured_acl_list:
        result.is_failure(
            f"SNMP IPv6 ACL(s) not configured or active in vrf {vrf}: {not_configured_acl_list}"
        )

    else:
        result.is_success()
    return result
