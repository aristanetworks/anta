"""
Test functions related to the EOS various SNMP settings
"""
from __future__ import annotations

from typing import Optional

from anta.models import AntaCommand, AntaTest


class VerifySnmpStatus(AntaTest):
    """
    Verifies whether the SNMP agent is enabled in a specified VRF.

    Expected Results:
        * success: The test will pass if the SNMP agent is enabled in the specified VRF.
        * failure: The test will fail if the SNMP agent is disabled in the specified VRF.
        * skipped: The test will be skipped if the VRF parameter is not provided.
    """

    name = "VerifySnmpStatus"
    description = "Verifies if the SNMP agent is enabled."
    categories = ["snmp"]
    commands = [AntaCommand(command="show snmp")]

    @AntaTest.anta_test
    def test(self, vrf: str = "default") -> None:
        """
        Run VerifySnmpStatus validation.

        Args:
            vrf: The name of the VRF in which to check for the SNMP agent. Defaults to 'default'.
        """
        if not vrf:
            self.result.is_skipped(f"{self.__class__.name} did not run because vrf was not supplied")
        else:
            command_output = self.instance_commands[0].json_output

            if command_output["enabled"] and vrf in command_output["vrfs"]["snmpVrfs"]:
                self.result.is_success()
            else:
                self.result.is_failure(f"SNMP agent disabled in vrf {vrf}")


class VerifySnmpIPv4Acl(AntaTest):
    """
    Verifies if the SNMP agent has the right number IPv4 ACL(s) configured for a specified VRF.

    Expected results:
        * success: The test will pass if the SNMP agent has the provided number of IPv4 ACL(s) in the specified VRF.
        * failure: The test will fail if the SNMP agent has not the right number of IPv4 ACL(s) in the specified VRF.
        * skipped: The test will be skipped if the number of IPv4 ACL(s) or VRF parameter is not provided.
    """

    name = "VerifySnmpIPv4Acl"
    description = "Verifies if the SNMP agent has IPv4 ACL(s) configured."
    categories = ["snmp"]
    commands = [AntaCommand(command="show snmp ipv4 access-list summary")]

    @AntaTest.anta_test
    def test(self, number: Optional[int] = None, vrf: str = "default") -> None:
        """
        Run VerifySnmpIPv4Acl validation.

        Args:
            number: The number of expected IPv4 ACL(s).
            vrf: The name of the VRF in which to check for the SNMP agent. Defaults to 'default'.
        """
        if not number or not vrf:
            self.result.is_skipped(f"{self.__class__.name} did not run because number or vrf was not supplied")
            return

        command_output = self.instance_commands[0].json_output

        ipv4_acl_list = command_output["ipAclList"]["aclList"]
        ipv4_acl_number = len(ipv4_acl_list)
        not_configured_acl_list = []

        if ipv4_acl_number != number:
            self.result.is_failure(f"Expected {number} SNMP IPv4 ACL(s) in vrf {vrf} but got {ipv4_acl_number}")
            return

        for ipv4_acl in ipv4_acl_list:
            if vrf not in ipv4_acl["configuredVrfs"] or vrf not in ipv4_acl["activeVrfs"]:
                not_configured_acl_list.append(ipv4_acl["name"])

        if not_configured_acl_list:
            self.result.is_failure(f"SNMP IPv4 ACL(s) not configured or active in vrf {vrf}: {not_configured_acl_list}")
        else:
            self.result.is_success()


class VerifySnmpIPv6Acl(AntaTest):
    """
    Verifies if the SNMP agent has the right number IPv6 ACL(s) configured for a specified VRF.

    Expected results:
        * success: The test will pass if the SNMP agent has the provided number of IPv6 ACL(s) in the specified VRF.
        * failure: The test will fail if the SNMP agent has not the right number of IPv6 ACL(s) in the specified VRF.
        * skipped: The test will be skipped if the number of IPv6 ACL(s) or VRF parameter is not provided.
    """

    name = "VerifySnmpIPv6Acl"
    description = "Verifies if the SNMP agent has IPv6 ACL(s) configured."
    categories = ["snmp"]
    commands = [AntaCommand(command="show snmp ipv6 access-list summary")]

    @AntaTest.anta_test
    def test(self, number: Optional[int] = None, vrf: str = "default") -> None:
        """
        Run VerifySnmpIPv6Acl validation.

        Args:
            number: The number of expected IPv6 ACL(s).
            vrf: The name of the VRF in which to check for the SNMP agent. Defaults to 'default'.
        """
        if not number or not vrf:
            self.result.is_skipped(f"{self.__class__.name} did not run because number or vrf was not supplied")
            return

        command_output = self.instance_commands[0].json_output

        ipv6_acl_list = command_output["ipv6AclList"]["aclList"]
        ipv6_acl_number = len(ipv6_acl_list)
        not_configured_acl_list = []

        if ipv6_acl_number != number:
            self.result.is_failure(f"Expected {number} SNMP IPv6 ACL(s) in vrf {vrf} but got {ipv6_acl_number}")
            return

        for ipv6_acl in ipv6_acl_list:
            if vrf not in ipv6_acl["configuredVrfs"] or vrf not in ipv6_acl["activeVrfs"]:
                not_configured_acl_list.append(ipv6_acl["name"])

        if not_configured_acl_list:
            self.result.is_failure(f"SNMP IPv6 ACL(s) not configured or active in vrf {vrf}: {not_configured_acl_list}")
        else:
            self.result.is_success()
