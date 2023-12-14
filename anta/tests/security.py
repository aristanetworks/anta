# Copyright (c) 2023-2024 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""
Test functions related to the EOS various security settings
"""
from __future__ import annotations

# Mypy does not understand AntaTest.Input typing
# mypy: disable-error-code=attr-defined
from datetime import datetime
from typing import Literal

from pydantic import conint

from anta.custom_types import EncryptionSize, EncryptionType
from anta.models import AntaCommand, AntaTest
from anta.tools.get_value import get_value
from anta.tools.utils import get_failed_logs


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
    """

    name = "VerifySSHIPv4Acl"
    description = "Verifies if the SSHD agent has IPv4 ACL(s) configured."
    categories = ["security"]
    commands = [AntaCommand(command="show management ssh ip access-list summary")]

    class Input(AntaTest.Input):  # pylint: disable=missing-class-docstring
        number: conint(ge=0)  # type:ignore
        """The number of expected IPv4 ACL(s)"""
        vrf: str = "default"
        """The name of the VRF in which to check for the SSHD agent"""

    @AntaTest.anta_test
    def test(self) -> None:
        command_output = self.instance_commands[0].json_output
        ipv4_acl_list = command_output["ipAclList"]["aclList"]
        ipv4_acl_number = len(ipv4_acl_list)
        not_configured_acl_list = []
        if ipv4_acl_number != self.inputs.number:
            self.result.is_failure(f"Expected {self.inputs.number} SSH IPv4 ACL(s) in vrf {self.inputs.vrf} but got {ipv4_acl_number}")
            return
        for ipv4_acl in ipv4_acl_list:
            if self.inputs.vrf not in ipv4_acl["configuredVrfs"] or self.inputs.vrf not in ipv4_acl["activeVrfs"]:
                not_configured_acl_list.append(ipv4_acl["name"])
        if not_configured_acl_list:
            self.result.is_failure(f"SSH IPv4 ACL(s) not configured or active in vrf {self.inputs.vrf}: {not_configured_acl_list}")
        else:
            self.result.is_success()


class VerifySSHIPv6Acl(AntaTest):
    """
    Verifies if the SSHD agent has the right number IPv6 ACL(s) configured for a specified VRF.

    Expected results:
        * success: The test will pass if the SSHD agent has the provided number of IPv6 ACL(s) in the specified VRF.
        * failure: The test will fail if the SSHD agent has not the right number of IPv6 ACL(s) in the specified VRF.
    """

    name = "VerifySSHIPv6Acl"
    description = "Verifies if the SSHD agent has IPv6 ACL(s) configured."
    categories = ["security"]
    commands = [AntaCommand(command="show management ssh ipv6 access-list summary")]

    class Input(AntaTest.Input):  # pylint: disable=missing-class-docstring
        number: conint(ge=0)  # type:ignore
        """The number of expected IPv6 ACL(s)"""
        vrf: str = "default"
        """The name of the VRF in which to check for the SSHD agent"""

    @AntaTest.anta_test
    def test(self) -> None:
        command_output = self.instance_commands[0].json_output
        ipv6_acl_list = command_output["ipv6AclList"]["aclList"]
        ipv6_acl_number = len(ipv6_acl_list)
        not_configured_acl_list = []
        if ipv6_acl_number != self.inputs.number:
            self.result.is_failure(f"Expected {self.inputs.number} SSH IPv6 ACL(s) in vrf {self.inputs.vrf} but got {ipv6_acl_number}")
            return
        for ipv6_acl in ipv6_acl_list:
            if self.inputs.vrf not in ipv6_acl["configuredVrfs"] or self.inputs.vrf not in ipv6_acl["activeVrfs"]:
                not_configured_acl_list.append(ipv6_acl["name"])
        if not_configured_acl_list:
            self.result.is_failure(f"SSH IPv6 ACL(s) not configured or active in vrf {self.inputs.vrf}: {not_configured_acl_list}")
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
    """

    name = "VerifyAPIHttpsSSL"
    description = "Verifies if eAPI HTTPS server SSL profile is configured and valid."
    categories = ["security"]
    commands = [AntaCommand(command="show management api http-commands")]

    class Input(AntaTest.Input):  # pylint: disable=missing-class-docstring
        profile: str
        """SSL profile to verify"""

    @AntaTest.anta_test
    def test(self) -> None:
        command_output = self.instance_commands[0].json_output
        try:
            if command_output["sslProfile"]["name"] == self.inputs.profile and command_output["sslProfile"]["state"] == "valid":
                self.result.is_success()
            else:
                self.result.is_failure(f"eAPI HTTPS server SSL profile ({self.inputs.profile}) is misconfigured or invalid")

        except KeyError:
            self.result.is_failure(f"eAPI HTTPS server SSL profile ({self.inputs.profile}) is not configured")


class VerifyAPIIPv4Acl(AntaTest):
    """
    Verifies if eAPI has the right number IPv4 ACL(s) configured for a specified VRF.

    Expected results:
        * success: The test will pass if eAPI has the provided number of IPv4 ACL(s) in the specified VRF.
        * failure: The test will fail if eAPI has not the right number of IPv4 ACL(s) in the specified VRF.
    """

    name = "VerifyAPIIPv4Acl"
    description = "Verifies if eAPI has the right number IPv4 ACL(s) configured for a specified VRF."
    categories = ["security"]
    commands = [AntaCommand(command="show management api http-commands ip access-list summary")]

    class Input(AntaTest.Input):  # pylint: disable=missing-class-docstring
        number: conint(ge=0)  # type:ignore
        """The number of expected IPv4 ACL(s)"""
        vrf: str = "default"
        """The name of the VRF in which to check for eAPI"""

    @AntaTest.anta_test
    def test(self) -> None:
        command_output = self.instance_commands[0].json_output
        ipv4_acl_list = command_output["ipAclList"]["aclList"]
        ipv4_acl_number = len(ipv4_acl_list)
        not_configured_acl_list = []
        if ipv4_acl_number != self.inputs.number:
            self.result.is_failure(f"Expected {self.inputs.number} eAPI IPv4 ACL(s) in vrf {self.inputs.vrf} but got {ipv4_acl_number}")
            return
        for ipv4_acl in ipv4_acl_list:
            if self.inputs.vrf not in ipv4_acl["configuredVrfs"] or self.inputs.vrf not in ipv4_acl["activeVrfs"]:
                not_configured_acl_list.append(ipv4_acl["name"])
        if not_configured_acl_list:
            self.result.is_failure(f"eAPI IPv4 ACL(s) not configured or active in vrf {self.inputs.vrf}: {not_configured_acl_list}")
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

    class Input(AntaTest.Input):  # pylint: disable=missing-class-docstring
        number: conint(ge=0)  # type:ignore
        """The number of expected IPv6 ACL(s)"""
        vrf: str = "default"
        """The name of the VRF in which to check for eAPI"""

    @AntaTest.anta_test
    def test(self) -> None:
        command_output = self.instance_commands[0].json_output
        ipv6_acl_list = command_output["ipv6AclList"]["aclList"]
        ipv6_acl_number = len(ipv6_acl_list)
        not_configured_acl_list = []
        if ipv6_acl_number != self.inputs.number:
            self.result.is_failure(f"Expected {self.inputs.number} eAPI IPv6 ACL(s) in vrf {self.inputs.vrf} but got {ipv6_acl_number}")
            return
        for ipv6_acl in ipv6_acl_list:
            if self.inputs.vrf not in ipv6_acl["configuredVrfs"] or self.inputs.vrf not in ipv6_acl["activeVrfs"]:
                not_configured_acl_list.append(ipv6_acl["name"])
        if not_configured_acl_list:
            self.result.is_failure(f"eAPI IPv6 ACL(s) not configured or active in vrf {self.inputs.vrf}: {not_configured_acl_list}")
        else:
            self.result.is_success()


class VerifyAPISSLCertificate(AntaTest):
    """
    Verifies SSL certificate expiry, common subject name, encryption type and size.

    Expected Results:
        * success: The test will pass if the expiry limit of the certificate is greater than the threshold, and has the correct name, encryption type and size.
        * failure: The test will fail if the certificate is expired or going to expire, and has an incorrect name, encryption type and size.
    """

    name = "VerifyAPISSLCertificate"
    description = "Verifies the eAPI SSL certificate status."
    categories = ["security"]
    commands = [AntaCommand(command="show management security ssl certificate"), AntaCommand(command="show clock")]

    class Input(AntaTest.Input):  # pylint: disable=missing-class-docstring
        certificate: str
        """Certificate name which going to be verified"""
        expiry_limit: int
        """Certificate expiry limit in days"""
        subject_name: str
        """Certificate common subject name"""
        encryption: Literal[EncryptionType] = None  # type: ignore
        """Certificate encryption type"""
        size: Literal[EncryptionSize] = None  # type: ignore
        """Certificate encryption size"""

    @AntaTest.anta_test
    def test(self) -> None:
        certificate_output = self.instance_commands[0].json_output
        clock_output = self.instance_commands[1].json_output

        # Collecting certificate expiry time and current EOS time.
        certificate_data = get_value(certificate_output, f"certificates..{self.inputs.certificate}", separator="..")
        if certificate_data is None:
            self.result.is_failure(f"SSL certificate '{self.inputs.certificate}', is not configured.")
            return

        expiry_time = certificate_data["notAfter"]
        current_timestamp = clock_output["utcTime"]
        day_difference = (datetime.fromtimestamp(expiry_time) - datetime.fromtimestamp(current_timestamp)).days

        # Verify certificate expiry
        if self.inputs.expiry_limit > day_difference > 0:
            self.result.is_failure(f"SSL certificate `{self.inputs.certificate}` is about to expire in {day_difference} days.")
            return
        if day_difference < 0:
            self.result.is_failure(f"SSL certificate `{self.inputs.certificate}` is expired.")
            return

        # Verify certificate common name, encryption type and size
        keys_to_verify = ["subject.commonName", "publicKey.encryptionAlgorithm", "publicKey.size"]
        verified_output = {key: get_value(certificate_data, key) for key in keys_to_verify}

        expected_output = {
            "subject.commonName": self.inputs.subject_name,
            "publicKey.encryptionAlgorithm": self.inputs.encryption if self.inputs.encryption else verified_output["publicKey.encryptionAlgorithm"],
            "publicKey.size": self.inputs.size if self.inputs.size else verified_output["publicKey.size"],
        }

        if verified_output != expected_output:
            failed_log = f"The SSL certificate `{self.inputs.certificate}` is not configured properly:"
            failed_log += get_failed_logs(expected_output, verified_output)
            self.result.is_failure(f"{failed_log}")
        else:
            self.result.is_success()
