# Copyright (c) 2023-2024 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Module related to the EOS various SNMP tests."""

# Mypy does not understand AntaTest.Input typing
# mypy: disable-error-code=attr-defined
from __future__ import annotations

from typing import TYPE_CHECKING, Any, ClassVar, Literal, get_args

from pydantic import BaseModel, model_validator

from anta.custom_types import PositiveInteger, SnmpErrorCounter, SnmpPdu, SnmpVersion
from anta.models import AntaCommand, AntaTest
from anta.tools import get_value

if TYPE_CHECKING:
    from anta.models import AntaTemplate


def _get_snmp_group_failures(
    version: SnmpVersion,
    read_view: str | None,
    write_view: str | None,
    notify_view: str | None,
    authentication: Literal["v3Auth", "v3Priv", "v3NoAuth"] | None,
    group_details: dict[str, Any],
) -> str:
    """
    Validate SNMP group configurations and return failure messages if issues are found.

    Parameters
    ----------
    version
        SNMP protocol version.
    read_view
        View to restrict read access.
    write_view
        View to restrict write access.
    notify_view
        View to restrict notifications.
    authentication
        Advanced authentication in v3 SNMP version
    group_details
        The SNMP group output from device.

    Returns
    -------
    str
        Failed log of a group details.

    """
    failure: str = ""

    def check_view(view_name: str, expected_view: str, default_message: str) -> str:
        """Check actual view and return failure log if any."""
        failure_log: str = ""
        actual_view = "Not Found" if (view := group_details.get(view_name)) is None else view or default_message
        config_view = group_details.get(f"{view_name}Config")

        if not config_view:
            failure_log += f"\nThe '{expected_view}' view is not configured."
        if expected_view != actual_view:
            failure_log += f"\nExpected '{expected_view}' as '{view_name}' but found '{actual_view}' instead."
        return failure_log

    # Check views (read, write, notify)
    if read_view:
        failure += check_view("readView", read_view, "default: all included")
    if write_view:
        failure += check_view("writeView", write_view, "no write view specified")
    if notify_view:
        failure += check_view("notifyView", notify_view, "no notify view specified")

    # Check version-specific authentication
    if version == "v3" and (actual_auth := group_details.get("secModel")) != authentication:
        failure += f"\nExpected '{authentication}' as security model but found '{actual_auth}' instead."

    return failure


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


class VerifySnmpGroup(AntaTest):
    """Verifies the SNMP group configurations for specified version(s).

    - Verifies that the valid group name and security model version.
    - Ensures that the SNMP views, the read, write and notify settings aligning with version-specific requirements.

    Expected Results
    ----------------
    * Success: The test will pass if the provided SNMP group and all specified parameters are correctly configured.
    * Failure: The test will fail if the provided SNMP group is not configured or specified parameters are not correctly configured.

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
    ```
    """

    name = "VerifySnmpGroup"
    description = "Verifies the SNMP group configurations for specified version(s)."
    categories: ClassVar[list[str]] = ["snmp"]
    commands: ClassVar[list[AntaCommand | AntaTemplate]] = [AntaCommand(command="show snmp group", revision=1)]

    class Input(AntaTest.Input):
        """Input model for the VerifySnmpGroup test."""

        snmp_groups: list[SnmpGroup]
        """List of SNMP groups."""

        class SnmpGroup(BaseModel):
            """Model for a SNMP group."""

            group_name: str
            """SNMP group for the user."""
            version: SnmpVersion
            """SNMP protocol version."""
            read_view: str | None = None
            """View to restrict read access."""
            write_view: str | None = None
            """View to restrict write access."""
            notify_view: str | None = None
            """View to restrict notifications."""
            authentication: Literal["v3Auth", "v3Priv", "v3NoAuth"] | None = None
            """Advanced authentication in v3 SNMP version. Defaults to None.
            - v3Auth: Group using authentication but not privacy
            - v3Priv: Group using both authentication and privacy
            - v3NoAuth: Group using neither authentication nor privacy
            """

            @model_validator(mode="after")
            def validate_inputs(self: BaseModel) -> BaseModel:
                """Validate the inputs provided to the SnmpGroup class."""
                if self.version == "v3" and self.authentication is None:
                    msg = "SNMP versions v3, advanced authentication is required."
                    raise ValueError(msg)
                return self

    @AntaTest.anta_test
    def test(self) -> None:
        """Main test function for VerifySnmpGroup."""
        self.result.is_success()
        failures: str = ""

        for group in self.inputs.snmp_groups:
            group_name = group.group_name
            version = group.version
            read_view = group.read_view
            write_view = group.write_view
            notify_view = group.notify_view
            authentication = group.authentication

            # Verify SNMP group details.
            if not (group_details := get_value(self.instance_commands[0].json_output, f"groups.{group_name}.versions.{version}")):
                failures += f"SNMP group '{group_name}' is not configured with security model '{version}'.\n"
                continue

            # Collecting failures logs if any.
            failure_logs = _get_snmp_group_failures(version, read_view, write_view, notify_view, authentication, group_details)
            if failure_logs:
                failures += f"For SNMP group {group_name} with SNMP version {version}:{failure_logs}\n"

        # Check if there are any failures.
        if failures:
            self.result.is_failure(failures)
