# Copyright (c) 2023-2025 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Module related to the EOS various SNMP tests."""

# Mypy does not understand AntaTest.Input typing
# mypy: disable-error-code=attr-defined
from __future__ import annotations

from typing import TYPE_CHECKING, ClassVar, get_args

from pydantic import field_validator

from anta.custom_types import PositiveInteger, SnmpErrorCounter, SnmpPdu
from anta.input_models.snmp import SnmpHost, SnmpUser
from anta.models import AntaCommand, AntaTest
from anta.tools import get_value

if TYPE_CHECKING:
    from anta.models import AntaTemplate


class VerifySnmpStatus(AntaTest):
    """Verifies whether the SNMP agent is enabled in a specified VRF.

    Expected Results
    ----------------
    * Success: The test will pass if the SNMP agent is enabled in the specified VRF.
    * Failure: The test will fail if the SNMP agent is disabled in the specified VRF.

    Examples
    --------
    ```yaml
    anta.tests.snmp:
      - VerifySnmpStatus:
          vrf: default
    ```
    """

    description = "Verifies if the SNMP agent is enabled."
    categories: ClassVar[list[str]] = ["snmp"]
    commands: ClassVar[list[AntaCommand | AntaTemplate]] = [AntaCommand(command="show snmp", revision=1)]

    class Input(AntaTest.Input):
        """Input model for the VerifySnmpStatus test."""

        vrf: str = "default"
        """The name of the VRF in which to check for the SNMP agent. Defaults to `default` VRF."""

    @AntaTest.anta_test
    def test(self) -> None:
        """Main test function for VerifySnmpStatus."""
        command_output = self.instance_commands[0].json_output
        if command_output["enabled"] and self.inputs.vrf in command_output["vrfs"]["snmpVrfs"]:
            self.result.is_success()
        else:
            self.result.is_failure(f"SNMP agent disabled in vrf {self.inputs.vrf}")


class VerifySnmpIPv4Acl(AntaTest):
    """Verifies if the SNMP agent has the right number IPv4 ACL(s) configured for a specified VRF.

    Expected Results
    ----------------
    * Success: The test will pass if the SNMP agent has the provided number of IPv4 ACL(s) in the specified VRF.
    * Failure: The test will fail if the SNMP agent has not the right number of IPv4 ACL(s) in the specified VRF.

    Examples
    --------
    ```yaml
    anta.tests.snmp:
      - VerifySnmpIPv4Acl:
          number: 3
          vrf: default
    ```
    """

    description = "Verifies if the SNMP agent has IPv4 ACL(s) configured."
    categories: ClassVar[list[str]] = ["snmp"]
    commands: ClassVar[list[AntaCommand | AntaTemplate]] = [AntaCommand(command="show snmp ipv4 access-list summary", revision=1)]

    class Input(AntaTest.Input):
        """Input model for the VerifySnmpIPv4Acl test."""

        number: PositiveInteger
        """The number of expected IPv4 ACL(s)."""
        vrf: str = "default"
        """The name of the VRF in which to check for the SNMP agent. Defaults to `default` VRF."""

    @AntaTest.anta_test
    def test(self) -> None:
        """Main test function for VerifySnmpIPv4Acl."""
        command_output = self.instance_commands[0].json_output
        ipv4_acl_list = command_output["ipAclList"]["aclList"]
        ipv4_acl_number = len(ipv4_acl_list)
        if ipv4_acl_number != self.inputs.number:
            self.result.is_failure(f"Expected {self.inputs.number} SNMP IPv4 ACL(s) in vrf {self.inputs.vrf} but got {ipv4_acl_number}")
            return

        not_configured_acl = [acl["name"] for acl in ipv4_acl_list if self.inputs.vrf not in acl["configuredVrfs"] or self.inputs.vrf not in acl["activeVrfs"]]

        if not_configured_acl:
            self.result.is_failure(f"SNMP IPv4 ACL(s) not configured or active in vrf {self.inputs.vrf}: {not_configured_acl}")
        else:
            self.result.is_success()


class VerifySnmpIPv6Acl(AntaTest):
    """Verifies if the SNMP agent has the right number IPv6 ACL(s) configured for a specified VRF.

    Expected Results
    ----------------
    * Success: The test will pass if the SNMP agent has the provided number of IPv6 ACL(s) in the specified VRF.
    * Failure: The test will fail if the SNMP agent has not the right number of IPv6 ACL(s) in the specified VRF.

    Examples
    --------
    ```yaml
    anta.tests.snmp:
      - VerifySnmpIPv6Acl:
          number: 3
          vrf: default
    ```
    """

    description = "Verifies if the SNMP agent has IPv6 ACL(s) configured."
    categories: ClassVar[list[str]] = ["snmp"]
    commands: ClassVar[list[AntaCommand | AntaTemplate]] = [AntaCommand(command="show snmp ipv6 access-list summary", revision=1)]

    class Input(AntaTest.Input):
        """Input model for the VerifySnmpIPv6Acl test."""

        number: PositiveInteger
        """The number of expected IPv6 ACL(s)."""
        vrf: str = "default"
        """The name of the VRF in which to check for the SNMP agent. Defaults to `default` VRF."""

    @AntaTest.anta_test
    def test(self) -> None:
        """Main test function for VerifySnmpIPv6Acl."""
        command_output = self.instance_commands[0].json_output
        ipv6_acl_list = command_output["ipv6AclList"]["aclList"]
        ipv6_acl_number = len(ipv6_acl_list)
        if ipv6_acl_number != self.inputs.number:
            self.result.is_failure(f"Expected {self.inputs.number} SNMP IPv6 ACL(s) in vrf {self.inputs.vrf} but got {ipv6_acl_number}")
            return

        acl_not_configured = [acl["name"] for acl in ipv6_acl_list if self.inputs.vrf not in acl["configuredVrfs"] or self.inputs.vrf not in acl["activeVrfs"]]

        if acl_not_configured:
            self.result.is_failure(f"SNMP IPv6 ACL(s) not configured or active in vrf {self.inputs.vrf}: {acl_not_configured}")
        else:
            self.result.is_success()


class VerifySnmpLocation(AntaTest):
    """Verifies the SNMP location of a device.

    Expected Results
    ----------------
    * Success: The test will pass if the SNMP location matches the provided input.
    * Failure: The test will fail if the SNMP location does not match the provided input.

    Examples
    --------
    ```yaml
    anta.tests.snmp:
      - VerifySnmpLocation:
          location: New York
    ```
    """

    categories: ClassVar[list[str]] = ["snmp"]
    commands: ClassVar[list[AntaCommand | AntaTemplate]] = [AntaCommand(command="show snmp", revision=1)]

    class Input(AntaTest.Input):
        """Input model for the VerifySnmpLocation test."""

        location: str
        """Expected SNMP location of the device."""

    @AntaTest.anta_test
    def test(self) -> None:
        """Main test function for VerifySnmpLocation."""
        # Verifies the SNMP location is configured.
        if not (location := get_value(self.instance_commands[0].json_output, "location.location")):
            self.result.is_failure("SNMP location is not configured.")
            return

        # Verifies the expected SNMP location.
        if location != self.inputs.location:
            self.result.is_failure(f"Expected `{self.inputs.location}` as the location, but found `{location}` instead.")
        else:
            self.result.is_success()


class VerifySnmpContact(AntaTest):
    """Verifies the SNMP contact of a device.

    Expected Results
    ----------------
    * Success: The test will pass if the SNMP contact matches the provided input.
    * Failure: The test will fail if the SNMP contact does not match the provided input.

    Examples
    --------
    ```yaml
    anta.tests.snmp:
      - VerifySnmpContact:
          contact: Jon@example.com
    ```
    """

    categories: ClassVar[list[str]] = ["snmp"]
    commands: ClassVar[list[AntaCommand | AntaTemplate]] = [AntaCommand(command="show snmp", revision=1)]

    class Input(AntaTest.Input):
        """Input model for the VerifySnmpContact test."""

        contact: str
        """Expected SNMP contact details of the device."""

    @AntaTest.anta_test
    def test(self) -> None:
        """Main test function for VerifySnmpContact."""
        # Verifies the SNMP contact is configured.
        if not (contact := get_value(self.instance_commands[0].json_output, "contact.contact")):
            self.result.is_failure("SNMP contact is not configured.")
            return

        # Verifies the expected SNMP contact.
        if contact != self.inputs.contact:
            self.result.is_failure(f"Expected `{self.inputs.contact}` as the contact, but found `{contact}` instead.")
        else:
            self.result.is_success()


class VerifySnmpPDUCounters(AntaTest):
    """Verifies the SNMP PDU counters.

    By default, all SNMP PDU counters will be checked for any non-zero values.
    An optional list of specific SNMP PDU(s) can be provided for granular testing.

    Expected Results
    ----------------
    * Success: The test will pass if the SNMP PDU counter(s) are non-zero/greater than zero.
    * Failure: The test will fail if the SNMP PDU counter(s) are zero/None/Not Found.

    Examples
    --------
    ```yaml
    anta.tests.snmp:
      - VerifySnmpPDUCounters:
          pdus:
            - outTrapPdus
            - inGetNextPdus
    ```
    """

    categories: ClassVar[list[str]] = ["snmp"]
    commands: ClassVar[list[AntaCommand | AntaTemplate]] = [AntaCommand(command="show snmp", revision=1)]

    class Input(AntaTest.Input):
        """Input model for the VerifySnmpPDUCounters test."""

        pdus: list[SnmpPdu] | None = None
        """Optional list of SNMP PDU counters to be verified. If not provided, test will verifies all PDU counters."""

    @AntaTest.anta_test
    def test(self) -> None:
        """Main test function for VerifySnmpPDUCounters."""
        snmp_pdus = self.inputs.pdus
        command_output = self.instance_commands[0].json_output

        # Verify SNMP PDU counters.
        if not (pdu_counters := get_value(command_output, "counters")):
            self.result.is_failure("SNMP counters not found.")
            return

        # In case SNMP PDUs not provided, It will check all the update error counters.
        if not snmp_pdus:
            snmp_pdus = list(get_args(SnmpPdu))

        failures = {pdu: value for pdu in snmp_pdus if (value := pdu_counters.get(pdu, "Not Found")) == "Not Found" or value == 0}

        # Check if any failures
        if not failures:
            self.result.is_success()
        else:
            self.result.is_failure(f"The following SNMP PDU counters are not found or have zero PDU counters:\n{failures}")


class VerifySnmpErrorCounters(AntaTest):
    """Verifies the SNMP error counters.

    By default, all  error counters will be checked for any non-zero values.
    An optional list of specific error counters can be provided for granular testing.

    Expected Results
    ----------------
    * Success: The test will pass if the SNMP error counter(s) are zero/None.
    * Failure: The test will fail if the SNMP error counter(s) are non-zero/not None/Not Found or is not configured.

    Examples
    --------
    ```yaml
    anta.tests.snmp:
      - VerifySnmpErrorCounters:
          error_counters:
            - inVersionErrs
            - inBadCommunityNames
    """

    categories: ClassVar[list[str]] = ["snmp"]
    commands: ClassVar[list[AntaCommand | AntaTemplate]] = [AntaCommand(command="show snmp", revision=1)]

    class Input(AntaTest.Input):
        """Input model for the VerifySnmpErrorCounters test."""

        error_counters: list[SnmpErrorCounter] | None = None
        """Optional list of SNMP error counters to be verified. If not provided, test will verifies all error counters."""

    @AntaTest.anta_test
    def test(self) -> None:
        """Main test function for VerifySnmpErrorCounters."""
        error_counters = self.inputs.error_counters
        command_output = self.instance_commands[0].json_output

        # Verify SNMP PDU counters.
        if not (snmp_counters := get_value(command_output, "counters")):
            self.result.is_failure("SNMP counters not found.")
            return

        # In case SNMP error counters not provided, It will check all the error counters.
        if not error_counters:
            error_counters = list(get_args(SnmpErrorCounter))

        error_counters_not_ok = {counter: value for counter in error_counters if (value := snmp_counters.get(counter))}

        # Check if any failures
        if not error_counters_not_ok:
            self.result.is_success()
        else:
            self.result.is_failure(f"The following SNMP error counters are not found or have non-zero error counters:\n{error_counters_not_ok}")


class VerifySnmpHostLogging(AntaTest):
    """Verifies SNMP logging configurations.

    This test performs the following checks:

     1. SNMP logging is enabled globally.
     2. For each specified SNMP host:
         - Host exists in configuration.
         - Host's VRF assignment matches expected value.

    Expected Results
    ----------------
    * Success: The test will pass if all of the following conditions are met:
        - SNMP logging is enabled on the device.
        - All specified hosts are configured with correct VRF assignments.
    * Failure: The test will fail if any of the following conditions is met:
        - SNMP logging is disabled on the device.
        - SNMP host not found in configuration.
        - Host's VRF assignment doesn't match expected value.

    Examples
    --------
    ```yaml
    anta.tests.snmp:
      - VerifySnmpHostLogging:
          hosts:
            - hostname: 192.168.1.100
              vrf: default
            - hostname: 192.168.1.103
              vrf: MGMT
    ```
    """

    categories: ClassVar[list[str]] = ["snmp"]
    commands: ClassVar[list[AntaCommand | AntaTemplate]] = [AntaCommand(command="show snmp", revision=1)]

    class Input(AntaTest.Input):
        """Input model for the VerifySnmpHostLogging test."""

        hosts: list[SnmpHost]
        """List of SNMP hosts."""

    @AntaTest.anta_test
    def test(self) -> None:
        """Main test function for VerifySnmpHostLogging."""
        self.result.is_success()

        command_output = self.instance_commands[0].json_output.get("logging", {})
        # If SNMP logging is disabled, test fails.
        if not command_output.get("loggingEnabled"):
            self.result.is_failure("SNMP logging is disabled")
            return

        host_details = command_output.get("hosts", {})

        for host in self.inputs.hosts:
            hostname = str(host.hostname)
            vrf = host.vrf
            actual_snmp_host = host_details.get(hostname, {})

            # If SNMP host is not configured on the device, test fails.
            if not actual_snmp_host:
                self.result.is_failure(f"{host} - Not configured")
                continue

            # If VRF is not matches the expected value, test fails.
            actual_vrf = "default" if (vrf_name := actual_snmp_host.get("vrf")) == "" else vrf_name
            if actual_vrf != vrf:
                self.result.is_failure(f"{host} - Incorrect VRF - Actual: {actual_vrf}")


class VerifySnmpUser(AntaTest):
    """Verifies the SNMP user configurations.

    This test performs the following checks for each specified user:

      1. User exists in SNMP configuration.
      2. Group assignment is correct.
      3. For SNMPv3 users only:
          - Authentication type matches (if specified)
          - Privacy type matches (if specified)

    Expected Results
    ----------------
    * Success: If all of the following conditions are met:
        - All users exist with correct group assignments.
        - SNMPv3 authentication and privacy types match specified values.
    * Failure: If any of the following occur:
        - User not found in SNMP configuration.
        - Incorrect group assignment.
        - For SNMPv3: Mismatched authentication or privacy types.

    Examples
    --------
    ```yaml
    anta.tests.snmp:
      - VerifySnmpUser:
          snmp_users:
            - username: test
              group_name: test_group
              version: v3
              auth_type: MD5
              priv_type: AES-128
    ```
    """

    categories: ClassVar[list[str]] = ["snmp"]
    commands: ClassVar[list[AntaCommand | AntaTemplate]] = [AntaCommand(command="show snmp user", revision=1)]

    class Input(AntaTest.Input):
        """Input model for the VerifySnmpUser test."""

        snmp_users: list[SnmpUser]
        """List of SNMP users."""

        @field_validator("snmp_users")
        @classmethod
        def validate_snmp_users(cls, snmp_users: list[SnmpUser]) -> list[SnmpUser]:
            """Validate that 'auth_type' or 'priv_type' field is provided in each SNMPv3 user."""
            for user in snmp_users:
                if user.version == "v3" and not (user.auth_type or user.priv_type):
                    msg = f"{user} 'auth_type' or 'priv_type' field is required with 'version: v3'"
                    raise ValueError(msg)
            return snmp_users

    @AntaTest.anta_test
    def test(self) -> None:
        """Main test function for VerifySnmpUser."""
        self.result.is_success()

        for user in self.inputs.snmp_users:
            # Verify SNMP user details.
            if not (user_details := get_value(self.instance_commands[0].json_output, f"usersByVersion.{user.version}.users.{user.username}")):
                self.result.is_failure(f"{user} - Not found")
                continue

            if user.group_name != (act_group := user_details.get("groupName", "Not Found")):
                self.result.is_failure(f"{user} - Incorrect user group - Actual: {act_group}")

            if user.version == "v3":
                if user.auth_type and (act_auth_type := get_value(user_details, "v3Params.authType", "Not Found")) != user.auth_type:
                    self.result.is_failure(f"{user} - Incorrect authentication type - Expected: {user.auth_type} Actual: {act_auth_type}")

                if user.priv_type and (act_encryption := get_value(user_details, "v3Params.privType", "Not Found")) != user.priv_type:
                    self.result.is_failure(f"{user} - Incorrect privacy type - Expected: {user.priv_type} Actual: {act_encryption}")
