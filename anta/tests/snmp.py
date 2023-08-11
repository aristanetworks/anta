# Copyright (c) 2023 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""
Test functions related to the EOS various SNMP settings
"""
# Mypy does not understand AntaTest.Input typing
# mypy: disable-error-code=attr-defined
from __future__ import annotations

from pydantic import conint

from anta.models import AntaCommand, AntaTest


class VerifySnmpStatus(AntaTest):
    """
    Verifies whether the SNMP agent is enabled in a specified VRF.

    Expected Results:
        * success: The test will pass if the SNMP agent is enabled in the specified VRF.
        * failure: The test will fail if the SNMP agent is disabled in the specified VRF.
    """

    name = "VerifySnmpStatus"
    description = "Verifies if the SNMP agent is enabled."
    categories = ["snmp"]
    commands = [AntaCommand(command="show snmp")]

    class Input(AntaTest.Input):  # pylint: disable=missing-class-docstring
        vrf: str = "default"
        """The name of the VRF in which to check for the SNMP agent"""

    @AntaTest.anta_test
    def test(self) -> None:
        command_output = self.instance_commands[0].json_output
        if command_output["enabled"] and self.inputs.vrf in command_output["vrfs"]["snmpVrfs"]:
            self.result.is_success()
        else:
            self.result.is_failure(f"SNMP agent disabled in vrf {self.inputs.vrf}")


class VerifySnmpIPv4Acl(AntaTest):
    """
    Verifies if the SNMP agent has the right number IPv4 ACL(s) configured for a specified VRF.

    Expected results:
        * success: The test will pass if the SNMP agent has the provided number of IPv4 ACL(s) in the specified VRF.
        * failure: The test will fail if the SNMP agent has not the right number of IPv4 ACL(s) in the specified VRF.
    """

    name = "VerifySnmpIPv4Acl"
    description = "Verifies if the SNMP agent has IPv4 ACL(s) configured."
    categories = ["snmp"]
    commands = [AntaCommand(command="show snmp ipv4 access-list summary")]

    class Input(AntaTest.Input):  # pylint: disable=missing-class-docstring
        number: conint(ge=0)  # type:ignore
        """The number of expected IPv4 ACL(s)"""
        vrf: str = "default"
        """The name of the VRF in which to check for the SNMP agent"""

    @AntaTest.anta_test
    def test(self) -> None:
        command_output = self.instance_commands[0].json_output
        ipv4_acl_list = command_output["ipAclList"]["aclList"]
        ipv4_acl_number = len(ipv4_acl_list)
        not_configured_acl_list = []
        if ipv4_acl_number != self.inputs.number:
            self.result.is_failure(f"Expected {self.inputs.number} SNMP IPv4 ACL(s) in vrf {self.inputs.vrf} but got {ipv4_acl_number}")
            return
        for ipv4_acl in ipv4_acl_list:
            if self.inputs.vrf not in ipv4_acl["configuredVrfs"] or self.inputs.vrf not in ipv4_acl["activeVrfs"]:
                not_configured_acl_list.append(ipv4_acl["name"])
        if not_configured_acl_list:
            self.result.is_failure(f"SNMP IPv4 ACL(s) not configured or active in vrf {self.inputs.vrf}: {not_configured_acl_list}")
        else:
            self.result.is_success()


class VerifySnmpIPv6Acl(AntaTest):
    """
    Verifies if the SNMP agent has the right number IPv6 ACL(s) configured for a specified VRF.

    Expected results:
        * success: The test will pass if the SNMP agent has the provided number of IPv6 ACL(s) in the specified VRF.
        * failure: The test will fail if the SNMP agent has not the right number of IPv6 ACL(s) in the specified VRF.
    """

    name = "VerifySnmpIPv6Acl"
    description = "Verifies if the SNMP agent has IPv6 ACL(s) configured."
    categories = ["snmp"]
    commands = [AntaCommand(command="show snmp ipv6 access-list summary")]

    class Input(AntaTest.Input):  # pylint: disable=missing-class-docstring
        number: conint(ge=0)  # type:ignore
        """The number of expected IPv6 ACL(s)"""
        vrf: str = "default"
        """The name of the VRF in which to check for the SNMP agent"""

    @AntaTest.anta_test
    def test(self) -> None:
        command_output = self.instance_commands[0].json_output
        ipv6_acl_list = command_output["ipv6AclList"]["aclList"]
        ipv6_acl_number = len(ipv6_acl_list)
        not_configured_acl_list = []
        if ipv6_acl_number != self.inputs.number:
            self.result.is_failure(f"Expected {self.inputs.number} SNMP IPv6 ACL(s) in vrf {self.inputs.vrf} but got {ipv6_acl_number}")
            return
        for ipv6_acl in ipv6_acl_list:
            if self.inputs.vrf not in ipv6_acl["configuredVrfs"] or self.inputs.vrf not in ipv6_acl["activeVrfs"]:
                not_configured_acl_list.append(ipv6_acl["name"])
        if not_configured_acl_list:
            self.result.is_failure(f"SNMP IPv6 ACL(s) not configured or active in vrf {self.inputs.vrf}: {not_configured_acl_list}")
        else:
            self.result.is_success()
