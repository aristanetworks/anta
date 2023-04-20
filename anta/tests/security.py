"""
Test functions related to the EOS various security settings
"""
import logging

from anta.inventory.models import InventoryDevice
from anta.result_manager.models import TestResult
from anta.tests import anta_test

logger = logging.getLogger(__name__)


@anta_test
async def verify_ssh_default_vrf(device: InventoryDevice, result: TestResult) -> TestResult:
    """
    Verifies if the SSHD agent is disabled in the default vrf.

    Args:
        device (InventoryDevice): InventoryDevice instance containing all devices information.

    Returns:
        TestResult instance with
        * result = "unset" if the test has not been executed
        * result = "success" if SSHD agent is disabled in the default VRF
        * result = "failure" otherwise
        * result = "error" if any exception is caught
    """
    response = await device.session.cli(command="show management ssh", ofmt="text")
    logger.debug(f"query result is: {response}")

    line = [line for line in response.split('\n') if line.startswith('SSHD status')][0]
    status = line.split('is ')[1]
    if status == "disabled":
        result.is_success()
    else:
        result.is_failure(line)
    return result


@anta_test
async def verify_ssh_ipv4_acl(device: InventoryDevice, result: TestResult, number: int, vrf: str = "default") -> TestResult:
    """
    Verifies if the SSHD agent has IPv4 ACL(s) configured.

    Args:
        device (InventoryDevice): InventoryDevice instance containing all devices information.
        number(int): Expected number of SSHD IPv4 ACL(s).
        vrf(str): VRF to verify. Default is "default".

    Returns:
        TestResult instance with
        * result = "unset" if the test has not been executed
        * result = "success" if SSH agent has IPv4 ACL(s) configured
        * result = "failure" otherwise
        * result = "error" if any exception is caught
    """
    if not number or not vrf:
        result.is_skipped(
            "verify_ssh_ipv4_acl did not run because number or vrf was not supplied"
        )
        return result

    device.assert_enable_password_is_not_none("verify_ssh_ipv4_acl")

    enable_cmd = {"cmd": "enable", "input": str(device.enable_password)}
    commands = [enable_cmd, "show management ssh ip access-list summary"]
    response = await device.session.cli(commands=commands, ofmt="json")
    logger.debug(f"query result is: {response}")

    ipv4_acl_list = response[1]["ipAclList"]["aclList"]
    ipv4_acl_number = len(ipv4_acl_list)
    not_configured_acl_list = []

    if ipv4_acl_number != number:
        result.is_failure(
            f"Expected {number} SSH IPv4 ACL(s) and got {ipv4_acl_number}"
        )
        return result

    for ipv4_acl in ipv4_acl_list:
        if vrf not in ipv4_acl["activeVrfs"]:
            not_configured_acl_list.append(ipv4_acl["name"])

    if not_configured_acl_list:
        result.is_failure(
            f"SSH IPv4 ACL(s) not configured or active in vrf {vrf}: {not_configured_acl_list}"
        )

    else:
        result.is_success()
    return result


@anta_test
async def verify_ssh_ipv6_acl(device: InventoryDevice, result: TestResult, number: int, vrf: str = "default") -> TestResult:
    """
    Verifies if the SSHD agent has IPv6 ACL(s) configured.

    Args:
        device (InventoryDevice): InventoryDevice instance containing all devices information.
        number(int): Expected number of SSHD IPv6 ACL(s).
        vrf(str): VRF to verify. Default is "default".

    Returns:
        TestResult instance with
        * result = "unset" if the test has not been executed
        * result = "success" if SSH agent has IPv6 ACL(s) configured
        * result = "failure" otherwise
        * result = "error" if any exception is caught
    """
    if not number or not vrf:
        result.is_skipped(
            "verify_ssh_ipv6_acl did not run because number or vrf was not supplied"
        )
        return result

    device.assert_enable_password_is_not_none("verify_ssh_ipv6_acl")

    enable_cmd = {"cmd": "enable", "input": str(device.enable_password)}
    commands = [enable_cmd, "show management ssh ipv6 access-list summary"]
    response = await device.session.cli(commands=commands, ofmt="json")
    logger.debug(f"query result is: {response}")

    ipv6_acl_list = response[1]["ipv6AclList"]["aclList"]
    ipv6_acl_number = len(ipv6_acl_list)
    not_configured_acl_list = []

    if ipv6_acl_number != number:
        result.is_failure(
            f"Expected {number} SSH IPv6 ACL(s) and got {ipv6_acl_number}"
        )
        return result

    for ipv6_acl in ipv6_acl_list:
        if vrf not in ipv6_acl["activeVrfs"]:
            not_configured_acl_list.append(ipv6_acl["name"])

    if not_configured_acl_list:
        result.is_failure(
            f"SSH IPv6 ACL(s) not configured or active in vrf {vrf}: {not_configured_acl_list}"
        )

    else:
        result.is_success()
    return result
