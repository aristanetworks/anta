"""
Test functions related to the EOS various security settings
"""
from __future__ import annotations

from typing import Optional

from anta.models import AntaCommand, AntaTest


class VerifySSHStatus(AntaTest):
    """
    Verifies if the SSHD agent is disabled in the default VRF.

    Expected Results:
        * success: The test will pass if the SSHD agent is disabled in the default VRF.
        * failure: The test will fail if the SSHD agent is NOT disabled in the default VRF.
    """

    name = "VerifySSHStatus"
    description = "Verifies if the SSHD agent is disabled in the default VRF."
    categories = ["security"]
    commands = [AntaCommand(command="show management ssh", ofmt="text")]

    @AntaTest.anta_test
    def test(self) -> None:
        """
        Run VerifySSHStatus validation.
        """

        command_output = self.instance_commands[0].text_output

        line = [line for line in command_output.split("\n") if line.startswith("SSHD status")][0]
        status = line.split("is ")[1]

        if status == "disabled":
            self.result.is_success()
        else:
            self.result.is_failure(line)


class VerifySSHIPv4Acl(AntaTest):
    """
    Verifies if the SSHD agent has the right number IPv4 ACL(s) configured for a specified VRF.

    Expected results:
        * success: The test will pass if the SSHD agent has the provided number of IPv4 ACL(s) in the specified VRF.
        * failure: The test will fail if the SSHD agent has not the right number of IPv4 ACL(s) in the specified VRF.
        * skipped: The test will be skipped if the number of IPv4 ACL(s) or VRF parameter is not provided.
    """

    name = "VerifySSHIPv4Acl"
    description = "Verifies if the SSHD agent has IPv4 ACL(s) configured."
    categories = ["security"]
    commands = [AntaCommand(command="show management ssh ip access-list summary")]

    @AntaTest.anta_test
    def test(self, number: Optional[int] = None, vrf: str = "default") -> None:
        """
        Run VerifySSHIPv4Acl validation.

        Args:
            number: The number of expected IPv4 ACL(s).
            vrf: The name of the VRF in which to check for the SSHD agent. Defaults to 'default'.
        """
        if not number or not vrf:
            self.result.is_skipped(f"{self.__class__.name} did not run because number or vrf was not supplied")
            return

        command_output = self.instance_commands[0].json_output

        ipv4_acl_list = command_output["ipAclList"]["aclList"]
        ipv4_acl_number = len(ipv4_acl_list)
        not_configured_acl_list = []

        if ipv4_acl_number != number:
            self.result.is_failure(f"Expected {number} SSH IPv4 ACL(s) in vrf {vrf} but got {ipv4_acl_number}")
            return

        for ipv4_acl in ipv4_acl_list:
            if vrf not in ipv4_acl["configuredVrfs"] or vrf not in ipv4_acl["activeVrfs"]:
                not_configured_acl_list.append(ipv4_acl["name"])

        if not_configured_acl_list:
            self.result.is_failure(f"SSH IPv4 ACL(s) not configured or active in vrf {vrf}: {not_configured_acl_list}")
        else:
            self.result.is_success()


class VerifySSHIPv6Acl(AntaTest):
    """
    Verifies if the SSHD agent has the right number IPv6 ACL(s) configured for a specified VRF.

    Expected results:
        * success: The test will pass if the SSHD agent has the provided number of IPv6 ACL(s) in the specified VRF.
        * failure: The test will fail if the SSHD agent has not the right number of IPv6 ACL(s) in the specified VRF.
        * skipped: The test will be skipped if the number of IPv6 ACL(s) or VRF parameter is not provided.
    """

    name = "VerifySSHIPv6Acl"
    description = "Verifies if the SSHD agent has IPv6 ACL(s) configured."
    categories = ["security"]
    commands = [AntaCommand(command="show management ssh ipv6 access-list summary")]

    @AntaTest.anta_test
    def test(self, number: Optional[int] = None, vrf: str = "default") -> None:
        """
        Run VerifySSHIPv6Acl validation.

        Args:
            number: The number of expected IPv6 ACL(s).
            vrf: The name of the VRF in which to check for the SSHD agent. Defaults to 'default'.
        """
        if not number or not vrf:
            self.result.is_skipped(f"{self.__class__.name} did not run because number or vrf was not supplied")
            return

        command_output = self.instance_commands[0].json_output

        ipv6_acl_list = command_output["ipv6AclList"]["aclList"]
        ipv6_acl_number = len(ipv6_acl_list)
        not_configured_acl_list = []

        if ipv6_acl_number != number:
            self.result.is_failure(f"Expected {number} SSH IPv6 ACL(s) in vrf {vrf} but got {ipv6_acl_number}")
            return

        for ipv6_acl in ipv6_acl_list:
            if vrf not in ipv6_acl["configuredVrfs"] or vrf not in ipv6_acl["activeVrfs"]:
                not_configured_acl_list.append(ipv6_acl["name"])

        if not_configured_acl_list:
            self.result.is_failure(f"SSH IPv6 ACL(s) not configured or active in vrf {vrf}: {not_configured_acl_list}")
        else:
            self.result.is_success()


class VerifyTelnetStatus(AntaTest):
    """
    Verifies if Telnet is disabled in the default VRF.

    Expected Results:
        * success: The test will pass if Telnet is disabled in the default VRF.
        * failure: The test will fail if Telnet is NOT disabled in the default VRF.
    """

    name = "VerifyTelnetStatus"
    description = "Verifies if Telnet is disabled in the default VRF."
    categories = ["security"]
    commands = [AntaCommand(command="show management telnet")]

    @AntaTest.anta_test
    def test(self) -> None:
        """
        Run VerifyTelnetStatus validation.
        """

        command_output = self.instance_commands[0].json_output

        if command_output["serverState"] == "disabled":
            self.result.is_success()
        else:
            self.result.is_failure("Telnet status for Default VRF is enabled")


class VerifyAPIHttpStatus(AntaTest):
    """
    Verifies if eAPI HTTP server is disabled globally.

    Expected Results:
        * success: The test will pass if eAPI HTTP server is disabled globally.
        * failure: The test will fail if eAPI HTTP server is NOT disabled globally.
    """

    name = "VerifyAPIHttpStatus"
    description = "Verifies if eAPI HTTP server is disabled globally."
    categories = ["security"]
    commands = [AntaCommand(command="show management api http-commands")]

    @AntaTest.anta_test
    def test(self) -> None:
        """
        Run VerifyAPIHTTPStatus validation.
        """

        command_output = self.instance_commands[0].json_output

        if command_output["enabled"] and not command_output["httpServer"]["running"]:
            self.result.is_success()
        else:
            self.result.is_failure("eAPI HTTP server is enabled globally")


class VerifyAPIHttpsSSL(AntaTest):
    """
    Verifies if eAPI HTTPS server SSL profile is configured and valid.

    Expected results:
        * success: The test will pass if the eAPI HTTPS server SSL profile is configured and valid.
        * failure: The test will fail if the eAPI HTTPS server SSL profile is NOT configured, misconfigured or invalid.
        * skipped: The test will be skipped if the SSL profile is not provided.
    """

    name = "VerifyAPIHttpsSSL"
    description = "Verifies if eAPI HTTPS server SSL profile is configured and valid."
    categories = ["security"]
    commands = [AntaCommand(command="show management api http-commands")]

    @AntaTest.anta_test
    def test(self, profile: Optional[str] = None) -> None:
        """
        Run VerifyAPIHttpsSSL validation.

        Args:
            profile: SSL profile to verify.
        """
        if not profile:
            self.result.is_skipped(f"{self.__class__.name} did not run because profile was not supplied")
            return

        command_output = self.instance_commands[0].json_output

        try:
            if command_output["sslProfile"]["name"] == profile and command_output["sslProfile"]["state"] == "valid":
                self.result.is_success()
            else:
                self.result.is_failure(f"eAPI HTTPS server SSL profile ({profile}) is misconfigured or invalid")

        except KeyError:
            self.result.is_failure(f"eAPI HTTPS server SSL profile ({profile}) is not configured")


class VerifyAPIIPv4Acl(AntaTest):
    """
    Verifies if eAPI has the right number IPv4 ACL(s) configured for a specified VRF.

    Expected results:
        * success: The test will pass if eAPI has the provided number of IPv4 ACL(s) in the specified VRF.
        * failure: The test will fail if eAPI has not the right number of IPv4 ACL(s) in the specified VRF.
        * skipped: The test will be skipped if the number of IPv4 ACL(s) or VRF parameter is not provided.
    """

    name = "VerifyAPIIPv4Acl"
    description = "Verifies if eAPI has the right number IPv4 ACL(s) configured for a specified VRF."
    categories = ["security"]
    commands = [AntaCommand(command="show management api http-commands ip access-list summary")]

    @AntaTest.anta_test
    def test(self, number: Optional[int] = None, vrf: str = "default") -> None:
        """
        Run VerifyAPIIPv4Acl validation.

        Args:
            number: The number of expected IPv4 ACL(s).
            vrf: The name of the VRF in which to check for eAPI. Defaults to 'default'.
        """
        if not number or not vrf:
            self.result.is_skipped(f"{self.__class__.name} did not run because number or vrf was not supplied")
            return

        command_output = self.instance_commands[0].json_output

        ipv4_acl_list = command_output["ipAclList"]["aclList"]
        ipv4_acl_number = len(ipv4_acl_list)
        not_configured_acl_list = []

        if ipv4_acl_number != number:
            self.result.is_failure(f"Expected {number} eAPI IPv4 ACL(s) in vrf {vrf} but got {ipv4_acl_number}")
            return

        for ipv4_acl in ipv4_acl_list:
            if vrf not in ipv4_acl["configuredVrfs"] or vrf not in ipv4_acl["activeVrfs"]:
                not_configured_acl_list.append(ipv4_acl["name"])

        if not_configured_acl_list:
            self.result.is_failure(f"eAPI IPv4 ACL(s) not configured or active in vrf {vrf}: {not_configured_acl_list}")
        else:
            self.result.is_success()


class VerifyAPIIPv6Acl(AntaTest):
    """
    Verifies if eAPI has the right number IPv6 ACL(s) configured for a specified VRF.

    Expected results:
        * success: The test will pass if eAPI has the provided number of IPv6 ACL(s) in the specified VRF.
        * failure: The test will fail if eAPI has not the right number of IPv6 ACL(s) in the specified VRF.
        * skipped: The test will be skipped if the number of IPv6 ACL(s) or VRF parameter is not provided.
    """

    name = "VerifyAPIIPv6Acl"
    description = "Verifies if eAPI has the right number IPv6 ACL(s) configured for a specified VRF."
    categories = ["security"]
    commands = [AntaCommand(command="show management api http-commands ipv6 access-list summary")]

    @AntaTest.anta_test
    def test(self, number: Optional[int] = None, vrf: str = "default") -> None:
        """
        Run VerifyAPIIPv6Acl validation.

        Args:
            number: The number of expected IPv6 ACL(s).
            vrf: The name of the VRF in which to check for eAPI. Defaults to 'default'.
        """
        if not number or not vrf:
            self.result.is_skipped(f"{self.__class__.name} did not run because number or vrf was not supplied")
            return

        command_output = self.instance_commands[0].json_output

        ipv6_acl_list = command_output["ipv6AclList"]["aclList"]
        ipv6_acl_number = len(ipv6_acl_list)
        not_configured_acl_list = []

        if ipv6_acl_number != number:
            self.result.is_failure(f"Expected {number} eAPI IPv6 ACL(s) in vrf {vrf} but got {ipv6_acl_number}")
            return

        for ipv6_acl in ipv6_acl_list:
            if vrf not in ipv6_acl["configuredVrfs"] or vrf not in ipv6_acl["activeVrfs"]:
                not_configured_acl_list.append(ipv6_acl["name"])

        if not_configured_acl_list:
            self.result.is_failure(f"eAPI IPv6 ACL(s) not configured or active in vrf {vrf}: {not_configured_acl_list}")
        else:
            self.result.is_success()
