# Copyright (c) 2023-2024 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Module related to the EOS various SNMP tests."""

# Mypy does not understand AntaTest.Input typing
# mypy: disable-error-code=attr-defined
from __future__ import annotations

from typing import TYPE_CHECKING, ClassVar

from pydantic import BaseModel, model_validator

from anta.custom_types import PositiveInteger
from anta.models import AntaCommand, AntaTest
from anta.tools import get_value

if TYPE_CHECKING:
    from anta.models import AntaTemplate

# Define the valid PDUs as a list
SNMP_PDUS: list[str] = ["inGetPdus", "inGetNextPdus", "inSetPdus", "outGetResponsePdus", "outTrapPdus"]


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

    name = "VerifySnmpStatus"
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

    name = "VerifySnmpIPv4Acl"
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

    name = "VerifySnmpIPv6Acl"
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

    name = "VerifySnmpLocation"
    description = "Verifies the SNMP location of a device."
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

    name = "VerifySnmpContact"
    description = "Verifies the SNMP contact of a device."
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


class VerifySnmpPDUs(AntaTest):
    """Verifies the number of SNMP PDU(s) (Protocol Data Units) processed.

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
      - VerifySnmpPDUs:
          pdus:
            - outTrapPdus
            - inGetNextPdus
    ```
    """

    name = "VerifySnmpPDUs"
    description = "Verifies the number of SNMP PDU(s) (Protocol Data Units) processed."
    categories: ClassVar[list[str]] = ["snmp"]
    commands: ClassVar[list[AntaCommand | AntaTemplate]] = [AntaCommand(command="show snmp", revision=1)]

    class Input(AntaTest.Input):
        """Input model for the VerifySnmpPDUs test."""

        pdus: list[str] | None = None
        """Optional list of SNMP PDU counters to be verified. If not provided, test will verifies all the PDUs."""

        @model_validator(mode="after")
        def validate_inputs(self: BaseModel) -> BaseModel:
            """Validate the inputs provided to the VerifySnmpPDUs test.

            The valid SNMP PDU counter must be provided.
            """
            if self.pdus:
                for pdu in self.pdus:
                    if pdu not in SNMP_PDUS:
                        msg = f"Invalid PDU counter {pdu}. Must be one of {SNMP_PDUS}."
                        raise ValueError(msg)
            return self

    @AntaTest.anta_test
    def test(self) -> None:
        """Main test function for VerifySnmpPDUs."""
        snmp_pdus = self.inputs.pdus
        command_output = self.instance_commands[0].json_output

        # Verify SNMP PDU counters.
        if not (pdu_counters := get_value(command_output, "counters")):
            self.result.is_failure("SNMP counter details are not found.")
            return

        # In case SNMP PDUs not provided, It will check all the update error counters.
        if not snmp_pdus:
            snmp_pdus = SNMP_PDUS

        failures = {pdu: value for pdu in snmp_pdus if (value := pdu_counters.get(pdu, "Not Found")) == "Not Found" or value == 0}

        # Check if any failures
        if not failures:
            self.result.is_success()
        else:
            self.result.is_failure(f"The following SNMP PDU(s) are not found or have zero PDU counter:\n{failures}")
