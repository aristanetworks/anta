# Copyright (c) 2023-2025 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Module related to the EOS various SNMP tests."""

# Pyright does not understand AntaTest.Input typing
# pyright: reportAttributeAccessIssue=false
from __future__ import annotations

from typing import TYPE_CHECKING, ClassVar, get_args

from pydantic import field_validator

from anta.custom_types import PositiveInteger, SnmpErrorCounter, SnmpPdu
from anta.input_models.snmp import SnmpGroup, SnmpHost, SnmpSourceInterface, SnmpUser
from anta.models import AntaCommand, AntaTest
from anta.tools import get_value

if TYPE_CHECKING:
    from anta.models import AntaTemplate


class VerifySnmpStatus(AntaTest):
    """Verifies if the SNMP agent is enabled.

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

    categories: ClassVar[list[str]] = ["snmp"]
    commands: ClassVar[list[AntaCommand | AntaTemplate]] = [AntaCommand(command="show snmp", revision=1)]

    class Input(AntaTest.Input):
        """Input model for the VerifySnmpStatus test."""

        vrf: str = "default"
        """The name of the VRF in which to check for the SNMP agent. Defaults to `default` VRF."""

    @AntaTest.anta_test
    def test(self) -> None:
        """Main test function for VerifySnmpStatus."""
        self.result.is_success()
        command_output = self.instance_commands[0].json_output
        if not (command_output["enabled"] and self.inputs.vrf in command_output["vrfs"]["snmpVrfs"]):
            self.result.is_failure(f"VRF: {self.inputs.vrf} - SNMP agent disabled")


class VerifySnmpIPv4Acl(AntaTest):
    """Verifies if the SNMP agent has IPv4 ACL(s) configured.

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
        self.result.is_success()
        command_output = self.instance_commands[0].json_output
        ipv4_acl_list = command_output["ipAclList"]["aclList"]
        ipv4_acl_number = len(ipv4_acl_list)
        if ipv4_acl_number != self.inputs.number:
            self.result.is_failure(f"VRF: {self.inputs.vrf} - Incorrect SNMP IPv4 ACL(s) - Expected: {self.inputs.number} Actual: {ipv4_acl_number}")
            return

        not_configured_acl = [acl["name"] for acl in ipv4_acl_list if self.inputs.vrf not in acl["configuredVrfs"] or self.inputs.vrf not in acl["activeVrfs"]]

        if not_configured_acl:
            self.result.is_failure(f"VRF: {self.inputs.vrf} - Following SNMP IPv4 ACL(s) not configured or active: {', '.join(not_configured_acl)}")


class VerifySnmpIPv6Acl(AntaTest):
    """Verifies if the SNMP agent has IPv6 ACL(s) configured.

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
        self.result.is_success()
        ipv6_acl_list = command_output["ipv6AclList"]["aclList"]
        ipv6_acl_number = len(ipv6_acl_list)
        if ipv6_acl_number != self.inputs.number:
            self.result.is_failure(f"VRF: {self.inputs.vrf} - Incorrect SNMP IPv6 ACL(s) - Expected: {self.inputs.number} Actual: {ipv6_acl_number}")
            return

        acl_not_configured = [acl["name"] for acl in ipv6_acl_list if self.inputs.vrf not in acl["configuredVrfs"] or self.inputs.vrf not in acl["activeVrfs"]]

        if acl_not_configured:
            self.result.is_failure(f"VRF: {self.inputs.vrf} - Following SNMP IPv6 ACL(s) not configured or active: {', '.join(acl_not_configured)}")


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
        self.result.is_success()
        # Verifies the SNMP location is configured.
        if not (location := get_value(self.instance_commands[0].json_output, "location.location")):
            self.result.is_failure("SNMP location is not configured")
            return

        # Verifies the expected SNMP location.
        if location != self.inputs.location:
            self.result.is_failure(f"Incorrect SNMP location - Expected: {self.inputs.location} Actual: {location}")


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
        self.result.is_success()
        # Verifies the SNMP contact is configured.
        if not (contact := get_value(self.instance_commands[0].json_output, "contact.contact")):
            self.result.is_failure("SNMP contact is not configured")
            return

        # Verifies the expected SNMP contact.
        if contact != self.inputs.contact:
            self.result.is_failure(f"Incorrect SNMP contact - Expected: {self.inputs.contact} Actual: {contact}")


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
        self.result.is_success()
        snmp_pdus = self.inputs.pdus
        command_output = self.instance_commands[0].json_output

        # Verify SNMP PDU counters.
        if not (pdu_counters := get_value(command_output, "counters")):
            self.result.is_failure("SNMP counters not found")
            return

        # In case SNMP PDUs not provided, It will check all the update error counters.
        if not snmp_pdus:
            snmp_pdus = list(get_args(SnmpPdu))

        failures = {pdu for pdu in snmp_pdus if (value := pdu_counters.get(pdu, "Not Found")) == "Not Found" or value == 0}

        # Check if any failures
        if failures:
            self.result.is_failure(f"The following SNMP PDU counters are not found or have zero PDU counters: {', '.join(sorted(failures))}")


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
    ```
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
        self.result.is_success()
        error_counters = self.inputs.error_counters
        command_output = self.instance_commands[0].json_output

        # Verify SNMP PDU counters.
        if not (snmp_counters := get_value(command_output, "counters")):
            self.result.is_failure("SNMP counters not found")
            return

        # In case SNMP error counters not provided, It will check all the error counters.
        if not error_counters:
            error_counters = list(get_args(SnmpErrorCounter))

        error_counters_not_ok = {counter for counter in error_counters if snmp_counters.get(counter)}

        # Check if any failures
        if error_counters_not_ok:
            self.result.is_failure(f"The following SNMP error counters are not found or have non-zero error counters: {', '.join(sorted(error_counters_not_ok))}")


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


class VerifySnmpNotificationHost(AntaTest):
    """Verifies the SNMP notification host(s) (SNMP manager) configurations.

    This test performs the following checks for each specified host:

     1. Verifies that the SNMP host(s) is configured on the device.
     2. Verifies that the notification type ("trap" or "inform") matches the expected value.
     3. Ensures that UDP port provided matches the expected value.
     4. Ensures the following depending on SNMP version:
        - For SNMP version v1/v2c, a valid community string is set and matches the expected value.
        - For SNMP version v3, a valid user field is set and matches the expected value.

    Expected Results
    ----------------
    * Success: The test will pass if all of the following conditions are met:
        - The SNMP host(s) is configured on the device.
        - The notification type ("trap" or "inform") and UDP port match the expected value.
        - Ensures the following depending on SNMP version:
            - For SNMP version v1/v2c, a community string is set and it matches the expected value.
            - For SNMP version v3, a valid user field is set and matches the expected value.
    * Failure: The test will fail if any of the following conditions is met:
        - The SNMP host(s) is not configured on the device.
        - The notification type ("trap" or "inform") or UDP port do not matches the expected value.
        - Ensures the following depending on SNMP version:
            - For SNMP version v1/v2c, a community string is not matches the expected value.
            - For SNMP version v3, an user field is not matches the expected value.

    Examples
    --------
    ```yaml
    anta.tests.snmp:
      - VerifySnmpNotificationHost:
          notification_hosts:
            - hostname: spine
              vrf: default
              notification_type: trap
              version: v1
              udp_port: 162
              community_string: public
            - hostname: 192.168.1.100
              vrf: default
              notification_type: trap
              version: v3
              udp_port: 162
              user: public
    ```
    """

    categories: ClassVar[list[str]] = ["snmp"]
    commands: ClassVar[list[AntaCommand | AntaTemplate]] = [AntaCommand(command="show snmp notification host", revision=1)]

    class Input(AntaTest.Input):
        """Input model for the VerifySnmpNotificationHost test."""

        notification_hosts: list[SnmpHost]
        """List of SNMP host(s)."""

        @field_validator("notification_hosts")
        @classmethod
        def validate_notification_hosts(cls, notification_hosts: list[SnmpHost]) -> list[SnmpHost]:
            """Validate that all required fields are provided in each SNMP Notification Host."""
            for host in notification_hosts:
                if host.version is None:
                    msg = f"{host}; 'version' field missing in the input"
                    raise ValueError(msg)
                if host.version in ["v1", "v2c"] and host.community_string is None:
                    msg = f"{host} Version: {host.version}; 'community_string' field missing in the input"
                    raise ValueError(msg)
                if host.version == "v3" and host.user is None:
                    msg = f"{host} Version: {host.version}; 'user' field missing in the input"
                    raise ValueError(msg)
            return notification_hosts

    @AntaTest.anta_test
    def test(self) -> None:
        """Main test function for VerifySnmpNotificationHost."""
        self.result.is_success()

        # If SNMP is not configured, test fails.
        if not (snmp_hosts := get_value(self.instance_commands[0].json_output, "hosts")):
            self.result.is_failure("No SNMP host is configured")
            return

        for host in self.inputs.notification_hosts:
            vrf = "" if host.vrf == "default" else host.vrf
            hostname = str(host.hostname)
            notification_type = host.notification_type
            version = host.version
            udp_port = host.udp_port
            community_string = host.community_string
            user = host.user
            default_value = "Not Found"

            host_details = next(
                (host for host in snmp_hosts if (host.get("hostname") == hostname and host.get("protocolVersion") == version and host.get("vrf") == vrf)), None
            )
            # If expected SNMP host is not configured with the specified protocol version, test fails.
            if not host_details:
                self.result.is_failure(f"{host} Version: {version} - Not configured")
                continue

            # If actual notification type does not match the expected value, test fails.
            if notification_type != (actual_notification_type := get_value(host_details, "notificationType", default_value)):
                self.result.is_failure(f"{host} - Incorrect notification type - Expected: {notification_type} Actual: {actual_notification_type}")

            # If actual UDP port does not match the expected value, test fails.
            if udp_port != (actual_udp_port := get_value(host_details, "port", default_value)):
                self.result.is_failure(f"{host} - Incorrect UDP port - Expected: {udp_port} Actual: {actual_udp_port}")

            user_found = user != (actual_user := get_value(host_details, "v3Params.user", default_value))
            version_user_check = (version == "v3", user_found)

            # If SNMP protocol version is v1 or v2c and actual community string does not match the expected value, test fails.
            if version in ["v1", "v2c"] and community_string != (actual_community_string := get_value(host_details, "v1v2cParams.communityString", default_value)):
                self.result.is_failure(f"{host} Version: {version} - Incorrect community string - Expected: {community_string} Actual: {actual_community_string}")

            # If SNMP protocol version is v3 and actual user does not match the expected value, test fails.
            elif all(version_user_check):
                self.result.is_failure(f"{host} Version: {version} - Incorrect user - Expected: {user} Actual: {actual_user}")


class VerifySnmpSourceInterface(AntaTest):
    """Verifies SNMP source interfaces.

    This test performs the following checks:

      1. Verifies that source interface(s) are configured for SNMP.
      2. For each specified source interface:
          - Interface is configured in the specified VRF.

    Expected Results
    ----------------
    * Success: The test will pass if the provided SNMP source interface(s) are configured in their specified VRF.
    * Failure: The test will fail if any of the provided SNMP source interface(s) are NOT configured in their specified VRF.

    Examples
    --------
    ```yaml
    anta.tests.snmp:
      - VerifySnmpSourceInterface:
          interfaces:
            - interface: Ethernet1
              vrf: default
            - interface: Management0
              vrf: MGMT
    ```
    """

    categories: ClassVar[list[str]] = ["snmp"]
    commands: ClassVar[list[AntaCommand | AntaTemplate]] = [AntaCommand(command="show snmp", revision=1)]

    class Input(AntaTest.Input):
        """Input model for the VerifySnmpSourceInterface test."""

        interfaces: list[SnmpSourceInterface]
        """List of source interfaces."""

    @AntaTest.anta_test
    def test(self) -> None:
        """Main test function for VerifySnmpSourceInterface."""
        self.result.is_success()
        command_output = self.instance_commands[0].json_output.get("srcIntf", {})

        if not (interface_output := command_output.get("sourceInterfaces")):
            self.result.is_failure("SNMP source interface(s) not configured")
            return

        for interface_details in self.inputs.interfaces:
            # If the source interface is not configured, or if it does not match the expected value, the test fails.
            if not (actual_interface := interface_output.get(interface_details.vrf)):
                self.result.is_failure(f"{interface_details} - Not configured")
            elif actual_interface != interface_details.interface:
                self.result.is_failure(f"{interface_details} - Incorrect source interface - Actual: {actual_interface}")


class VerifySnmpGroup(AntaTest):
    """Verifies the SNMP group configurations for specified version(s).

    This test performs the following checks:

      1. Verifies that the SNMP group is configured for the specified version.
      2. For SNMP version 3, verify that the security model matches the expected value.
      3. Ensures that SNMP group configurations, including read, write, and notify views, align with version-specific requirements.

    Expected Results
    ----------------
    * Success: The test will pass if the provided SNMP group and all specified parameters are correctly configured.
    * Failure: The test will fail if the provided SNMP group is not configured or if any specified parameter is not correctly configured.

    Examples
    --------
    ```yaml
    anta.tests.snmp:
      - VerifySnmpGroup:
          snmp_groups:
            - group_name: Group1
              version: v1
              read_view: group_read_1
              write_view: group_write_1
              notify_view: group_notify_1
            - group_name: Group2
              version: v3
              read_view: group_read_2
              write_view: group_write_2
              notify_view: group_notify_2
              authentication: priv
    ```
    """

    categories: ClassVar[list[str]] = ["snmp"]
    commands: ClassVar[list[AntaCommand | AntaTemplate]] = [AntaCommand(command="show snmp group", revision=1)]

    class Input(AntaTest.Input):
        """Input model for the VerifySnmpGroup test."""

        snmp_groups: list[SnmpGroup]
        """List of SNMP groups."""

    @AntaTest.anta_test
    def test(self) -> None:
        """Main test function for VerifySnmpGroup."""
        self.result.is_success()
        for group in self.inputs.snmp_groups:
            # Verify SNMP group details.
            if not (group_details := get_value(self.instance_commands[0].json_output, f"groups.{group.group_name}.versions.{group.version}")):
                self.result.is_failure(f"{group} - Not configured")
                continue

            view_types = [view_type for view_type in ["read", "write", "notify"] if getattr(group, f"{view_type}_view")]
            # Verify SNMP views, the read, write and notify settings aligning with version-specific requirements.
            for view_type in view_types:
                expected_view = getattr(group, f"{view_type}_view")
                # Verify actual view is configured.
                if group_details.get(f"{view_type}View") == "":
                    self.result.is_failure(f"{group} View: {view_type} - Not configured")
                elif (act_view := group_details.get(f"{view_type}View")) != expected_view:
                    self.result.is_failure(f"{group} - Incorrect {view_type.title()} view - Expected: {expected_view} Actual: {act_view}")
                elif not group_details.get(f"{view_type}ViewConfig"):
                    self.result.is_failure(f"{group} {view_type.title()} View: {expected_view} - Not configured")

            # For version v3, verify that the security model aligns with the expected value.
            if group.version == "v3" and (actual_auth := group_details.get("secModel")) != group.authentication:
                self.result.is_failure(f"{group} - Incorrect security model - Expected: {group.authentication} Actual: {actual_auth}")
