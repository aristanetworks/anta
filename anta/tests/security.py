"""
Test functions related to the EOS various security settings
"""
import logging

from anta.inventory.models import InventoryDevice
from anta.result_manager.models import TestResult
from anta.tests import anta_test

logger = logging.getLogger(__name__)


@anta_test
async def verify_ssh_status(device: InventoryDevice, result: TestResult) -> TestResult:
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
    # TODO: Might want to check if it's enabled and a provided VRF (bypass eAPI ERROR)
    response = await device.session.cli(command="show management ssh", ofmt="text")
    logger.debug(f"query result is: {response}")

    line = [line for line in response.split('\n') if line.startswith("SSHD status")][0]
    status = line.split("is ")[1]
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


@anta_test
async def verify_telnet_status(device: InventoryDevice, result: TestResult) -> TestResult:
    """
    Verifies if telnet is disabled in the default vrf.

    Args:
        device (InventoryDevice): InventoryDevice instance containing all devices information.

    Returns:
        TestResult instance with
        * result = "unset" if the test has not been executed
        * result = "success" if telnet is disabled in the default VRF
        * result = "failure" otherwise
        * result = "error" if any exception is caught
    """
    response = await device.session.cli(command="show management telnet", ofmt="json")
    logger.debug(f"query result is: {response}")

    if response["serverState"] == "disabled":
        result.is_success()
    else:
        result.is_failure("Telnet status for Default VRF is enabled")
    return result


@anta_test
async def verify_eapi_http_status(device: InventoryDevice, result: TestResult) -> TestResult:
    """
    Verifies if eAPI HTTP server is disabled.

    Args:
        device (InventoryDevice): InventoryDevice instance containing all devices information.

    Returns:
        TestResult instance with
        * result = "unset" if the test has not been executed
        * result = "success" if eAPI HTTP server is disabled
        * result = "failure" otherwise
        * result = "error" if any exception is caught
    """
    response = await device.session.cli(command="show management api http-commands", ofmt="json")
    logger.debug(f"query result is: {response}")

    if response["enabled"] and not response["httpServer"]["running"]:
        result.is_success()
    else:
        result.is_failure(
            "eAPI HTTP server is enabled"
        )
    return result


@anta_test
async def verify_eapi_https_ssl(device: InventoryDevice, result: TestResult, profile: str) -> TestResult:
    """
    Verifies if eAPI HTTPS server SSL profile is configured and valid.

    Args:
        device (InventoryDevice): InventoryDevice instance containing all devices information.
        profile(str): SSL profile to verify.

    Returns:
        TestResult instance with
        * result = "unset" if the test has not been executed
        * result = "success" if eAPI HTTPS server SSL profile is configured and valid
        * result = "failure" otherwise
        * result = "error" if any exception is caught
    """
    if not profile:
        result.is_skipped(
            "verify_eapi_https_ssl did not run because profile was not supplied"
        )
        return result

    response = await device.session.cli(command="show management api http-commands", ofmt="json")
    logger.debug(f"query result is: {response}")

    try:
        if response["sslProfile"]["name"] == profile and response["sslProfile"]["state"] == "valid":
            result.is_success()
        else:
            result.is_failure(
                f"eAPI HTTPS server SSL profile ({profile}) is misconfigured or not valid"
            )

    except KeyError:
        result.is_failure(
            f"eAPI HTTPS server SSL profile ({profile}) is not configured"
        )
    return result


@anta_test
async def verify_eapi_ipv4_acl(device: InventoryDevice, result: TestResult, number: int, vrf: str = "default") -> TestResult:
    """
    Verifies if eAPI has IPv4 ACL(s) configured.

    Args:
        device (InventoryDevice): InventoryDevice instance containing all devices information.
        number(int): Expected number of eAPI IPv4 ACL(s).
        vrf(str): VRF to verify. Default is "default".

    Returns:
        TestResult instance with
        * result = "unset" if the test has not been executed
        * result = "success" if eAPI has IPv4 ACL(s) configured
        * result = "failure" otherwise
        * result = "error" if any exception is caught
    """
    if not number or not vrf:
        result.is_skipped(
            "verify_eapi_ipv4_acl did not run because number or vrf was not supplied"
        )
        return result

    device.assert_enable_password_is_not_none("verify_eapi_ipv4_acl")

    enable_cmd = {"cmd": "enable", "input": str(device.enable_password)}
    commands = [enable_cmd, "show management api http-commands ip access-list summary"]
    response = await device.session.cli(commands=commands, ofmt="json")
    logger.debug(f"query result is: {response}")

    ipv4_acl_list = response[1]["ipAclList"]["aclList"]
    ipv4_acl_number = len(ipv4_acl_list)
    not_configured_acl_list = []

    if ipv4_acl_number != number:
        result.is_failure(
            f"Expected {number} eAPI IPv4 ACL(s) and got {ipv4_acl_number}"
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
async def verify_eapi_ipv6_acl(device: InventoryDevice, result: TestResult, number: int, vrf: str = "default") -> TestResult:
    """
    Verifies if eAPI has IPv6 ACL(s) configured.

    Args:
        device (InventoryDevice): InventoryDevice instance containing all devices information.
        number(int): Expected number of eAPI IPv6 ACL(s).
        vrf(str): VRF to verify. Default is "default".

    Returns:
        TestResult instance with
        * result = "unset" if the test has not been executed
        * result = "success" if eAPI has IPv6 ACL(s) configured
        * result = "failure" otherwise
        * result = "error" if any exception is caught
    """
    if not number or not vrf:
        result.is_skipped(
            "verify_eapi_ipv6_acl did not run because number or vrf was not supplied"
        )
        return result

    device.assert_enable_password_is_not_none("verify_eapi_ipv6_acl")

    enable_cmd = {"cmd": "enable", "input": str(device.enable_password)}
    commands = [enable_cmd, "show management api http-commands ipv6 access-list summary"]
    response = await device.session.cli(commands=commands, ofmt="json")
    logger.debug(f"query result is: {response}")

    ipv6_acl_list = response[1]["ipv6AclList"]["aclList"]
    ipv6_acl_number = len(ipv6_acl_list)
    not_configured_acl_list = []

    if ipv6_acl_number != number:
        result.is_failure(
            f"Expected {number} eAPI IPv6 ACL(s) and got {ipv6_acl_number}"
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
