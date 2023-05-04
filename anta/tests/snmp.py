"""
Test functions related to the EOS various SNMP settings
"""
from __future__ import annotations

import logging
from typing import Any, Dict, Optional, cast

from anta.models import AntaTest, AntaTestCommand

logger = logging.getLogger(__name__)


class VerifySnmpStatus(AntaTest):
    """
    Verifies if the SNMP agent is enabled.
    """

    name = "VerifySnmpStatus"
    description = "Verifies if the SNMP agent is enabled."
    categories = ["snmp"]
    commands = [AntaTestCommand(command="show snmp")]

    @AntaTest.anta_test
    def test(self, vrf: str = "default") -> None:
        """Run VerifySnmpStatus validation"""
        if not vrf:
            self.result.is_skipped(f"{self.__class__.name} did not run because vrf was not supplied")
        else:
            self.logger.debug(f"self.instance_commands is: {self.instance_commands}")
            command_output = cast(Dict[str, Dict[str, Any]], self.instance_commands[0].output)
            self.logger.debug(f"dataset is: {command_output}")

            if command_output["enabled"] and vrf in command_output["vrfs"]["snmpVrfs"]:
                self.result.is_success()
            else:
                self.result.is_failure(f"SNMP agent disabled in vrf {vrf}")


class VerifySnmpIPv4Acl(AntaTest):
    """
    Verifies if the SNMP agent has IPv4 ACL(s) configured.
    """

    name = "VerifySnmpIPv4Acl"
    description = "Verifies if the SNMP agent has IPv4 ACL(s) configured."
    categories = ["snmp"]
    commands = [AntaTestCommand(command="show snmp ipv4 access-list summary")]

    @AntaTest.anta_test
    def test(self, number: Optional[int] = None, vrf: str = "default") -> None:
        """Run VerifySnmpIPv4Acl validation"""
        if not number or not vrf:
            self.result.is_skipped(f"{self.__class__.name} did not run because number or vrf was not supplied")
        else:
            self.logger.debug(f"self.instance_commands is: {self.instance_commands}")
            command_output = cast(Dict[str, Dict[str, Any]], self.instance_commands[0].output)
            self.logger.debug(f"dataset is: {command_output}")

            ipv4_acl_list = command_output["ipAclList"]["aclList"]
            ipv4_acl_number = len(ipv4_acl_list)
            not_configured_acl_list = []

            if ipv4_acl_number != number:
                self.result.is_failure(f"Expected {number} SNMP IPv4 ACL(s) in vrf {vrf} but got {ipv4_acl_number}")

            else:
                for ipv4_acl in ipv4_acl_list:
                    if vrf not in ipv4_acl["configuredVrfs"] or vrf not in ipv4_acl["activeVrfs"]:
                        not_configured_acl_list.append(ipv4_acl["name"])

                if not_configured_acl_list:
                    self.result.is_failure(f"SNMP IPv4 ACL(s) not configured or active in vrf {vrf}: {not_configured_acl_list}")
                else:
                    self.result.is_success()


class VerifySnmpIPv6Acl(AntaTest):
    """
    Verifies if the SNMP agent has IPv6 ACL(s) configured.
    """

    name = "VerifySnmpIPv6Acl"
    description = "Verifies if the SNMP agent has IPv6 ACL(s) configured."
    categories = ["snmp"]
    commands = [AntaTestCommand(command="show snmp ipv6 access-list summary")]

    @AntaTest.anta_test
    def test(self, number: Optional[int] = None, vrf: str = "default") -> None:
        """Run VerifySnmpIPv6Acl validation"""
        if not number or not vrf:
            self.result.is_skipped(f"{self.__class__.name} did not run because number or vrf was not supplied")
        else:
            self.logger.debug(f"self.instance_commands is: {self.instance_commands}")
            command_output = cast(Dict[str, Dict[str, Any]], self.instance_commands[0].output)
            self.logger.debug(f"dataset is: {command_output}")

            ipv6_acl_list = command_output["ipv6AclList"]["aclList"]
            ipv6_acl_number = len(ipv6_acl_list)
            not_configured_acl_list = []

            if ipv6_acl_number != number:
                self.result.is_failure(f"Expected {number} SNMP IPv6 ACL(s) in vrf {vrf} but got {ipv6_acl_number}")

            else:
                for ipv6_acl in ipv6_acl_list:
                    if vrf not in ipv6_acl["configuredVrfs"] or vrf not in ipv6_acl["activeVrfs"]:
                        not_configured_acl_list.append(ipv6_acl["name"])

                if not_configured_acl_list:
                    self.result.is_failure(f"SNMP IPv6 ACL(s) not configured or active in vrf {vrf}: {not_configured_acl_list}")
                else:
                    self.result.is_success()
