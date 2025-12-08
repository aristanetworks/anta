# Copyright (c) 2023-2025 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Module related to VXLAN tests."""

# Pyright does not understand AntaTest.Input typing
# pyright: reportAttributeAccessIssue=false
from __future__ import annotations

from ipaddress import IPv4Address
from typing import TYPE_CHECKING, ClassVar

from pydantic import Field

from anta.custom_types import VlanId, Vni, VxlanSrcIntf
from anta.models import AntaCommand, AntaTest
from anta.tools import get_value

if TYPE_CHECKING:
    from anta.models import AntaTemplate


class VerifyVxlan1Interface(AntaTest):
    """Verifies the Vxlan1 interface status.

    Warnings
    --------
    The name of this test has been updated from 'VerifyVxlan' for better representation.

    Expected Results
    ----------------
    * Success: The test will pass if the Vxlan1 interface is configured with line protocol status and interface status 'up'.
    * Failure: The test will fail if the Vxlan1 interface line protocol status or interface status are not 'up'.
    * Skipped: The test will be skipped if the Vxlan1 interface is not configured.

    Examples
    --------
    ```yaml
    anta.tests.vxlan:
      - VerifyVxlan1Interface:
    ```
    """

    categories: ClassVar[list[str]] = ["vxlan"]
    commands: ClassVar[list[AntaCommand | AntaTemplate]] = [AntaCommand(command="show interfaces description", revision=1)]

    @AntaTest.anta_test
    def test(self) -> None:
        """Main test function for VerifyVxlan1Interface."""
        self.result.is_success()
        command_output = self.instance_commands[0].json_output

        # Skipping the test if the Vxlan1 interface is not configured
        if "Vxlan1" not in (interface_details := command_output["interfaceDescriptions"]):
            self.result.is_skipped("Interface: Vxlan1 - Not configured")
            return

        line_protocol_status = interface_details["Vxlan1"]["lineProtocolStatus"]
        interface_status = interface_details["Vxlan1"]["interfaceStatus"]

        # Checking against both status and line protocol status
        if interface_status != "up" or line_protocol_status != "up":
            self.result.is_failure(f"Interface: Vxlan1 - Incorrect Line protocol status/Status - Expected: up/up Actual: {line_protocol_status}/{interface_status}")


class VerifyVxlanConfigSanity(AntaTest):
    """Verifies there are no VXLAN config-sanity inconsistencies.

    Expected Results
    ----------------
    * Success: The test will pass if no issues are detected with the VXLAN configuration.
    * Failure: The test will fail if issues are detected with the VXLAN configuration.
    * Skipped: The test will be skipped if VXLAN is not configured on the device.

    Examples
    --------
    ```yaml
    anta.tests.vxlan:
      - VerifyVxlanConfigSanity:
    ```
    """

    categories: ClassVar[list[str]] = ["vxlan"]
    commands: ClassVar[list[AntaCommand | AntaTemplate]] = [AntaCommand(command="show vxlan config-sanity", revision=1)]

    @AntaTest.anta_test
    def test(self) -> None:
        """Main test function for VerifyVxlanConfigSanity."""
        self.result.is_success()
        command_output = self.instance_commands[0].json_output

        # Skipping the test if VXLAN is not configured
        if "categories" not in command_output or len(command_output["categories"]) == 0:
            self.result.is_skipped("VXLAN is not configured")
            return

        # Verifies the Vxlan config sanity
        categories_to_check = ["localVtep", "mlag", "pd"]
        for category in categories_to_check:
            if not get_value(command_output, f"categories.{category}.allCheckPass"):
                self.result.is_failure(f"Vxlan Category: {category} - Config sanity check is not passing")


class VerifyVxlanVniBinding(AntaTest):
    """Verifies the VNI-VLAN, VNI-VRF bindings of the Vxlan1 interface.

    Expected Results
    ----------------
    * Success: The test will pass if the VNI-VLAN and VNI-VRF bindings provided are properly configured.
    * Failure: The test will fail if any VNI lacks bindings or if any bindings are incorrect.
    * Skipped: The test will be skipped if the Vxlan1 interface is not configured.

    Examples
    --------
    ```yaml
    anta.tests.vxlan:
      - VerifyVxlanVniBinding:
          bindings:
            10010: 10
            10020: 20
            500: PROD
    ```
    """

    categories: ClassVar[list[str]] = ["vxlan"]
    commands: ClassVar[list[AntaCommand | AntaTemplate]] = [AntaCommand(command="show vxlan vni", revision=1)]

    class Input(AntaTest.Input):
        """Input model for the VerifyVxlanVniBinding test."""

        bindings: dict[Vni, VlanId | str]
        """VNI-VLAN or VNI-VRF bindings to verify."""

    @AntaTest.anta_test
    def test(self) -> None:
        """Main test function for VerifyVxlanVniBinding."""
        self.result.is_success()

        if (vxlan1 := get_value(self.instance_commands[0].json_output, "vxlanIntfs.Vxlan1")) is None:
            self.result.is_skipped("Interface: Vxlan1 - Not configured")
            return

        for vni, vlan_vrf in self.inputs.bindings.items():
            str_vni = str(vni)
            retrieved_vlan = ""
            retrieved_vrf = ""
            if all([str_vni in vxlan1["vniBindings"], isinstance(vlan_vrf, int)]):
                retrieved_vlan = get_value(vxlan1, f"vniBindings..{str_vni}..vlan", separator="..")
            elif str_vni in vxlan1["vniBindingsToVrf"]:
                if isinstance(vlan_vrf, int):
                    retrieved_vlan = get_value(vxlan1, f"vniBindingsToVrf..{str_vni}..vlan", separator="..")
                else:
                    retrieved_vrf = get_value(vxlan1, f"vniBindingsToVrf..{str_vni}..vrfName", separator="..")
            if not any([retrieved_vlan, retrieved_vrf]):
                self.result.is_failure(f"Interface: Vxlan1 VNI: {str_vni} - Binding not found")

            elif retrieved_vlan and vlan_vrf != retrieved_vlan:
                self.result.is_failure(f"Interface: Vxlan1 VNI: {str_vni} - Wrong VLAN binding - Expected: {vlan_vrf} Actual: {retrieved_vlan}")

            elif retrieved_vrf and vlan_vrf != retrieved_vrf:
                self.result.is_failure(f"Interface: Vxlan1 VNI: {str_vni} - Wrong VRF binding - Expected: {vlan_vrf} Actual: {retrieved_vrf}")


class VerifyVxlanVtep(AntaTest):
    """Verifies Vxlan1 VTEP peers.

    Expected Results
    ----------------
    * Success: The test will pass if all provided VTEP peers are identified and matching.
    * Failure: The test will fail if any VTEP peer is missing or there are unexpected VTEP peers.
    * Skipped: The test will be skipped if the Vxlan1 interface is not configured.

    Examples
    --------
    ```yaml
    anta.tests.vxlan:
      - VerifyVxlanVtep:
          vteps:
            - 10.1.1.5
            - 10.1.1.6
    ```
    """

    categories: ClassVar[list[str]] = ["vxlan"]
    commands: ClassVar[list[AntaCommand | AntaTemplate]] = [AntaCommand(command="show vxlan vtep", revision=1)]

    class Input(AntaTest.Input):
        """Input model for the VerifyVxlanVtep test."""

        vteps: list[IPv4Address]
        """List of VTEP peers to verify."""

    @AntaTest.anta_test
    def test(self) -> None:
        """Main test function for VerifyVxlanVtep."""
        self.result.is_success()

        inputs_vteps = [str(input_vtep) for input_vtep in self.inputs.vteps]

        if (vxlan1 := get_value(self.instance_commands[0].json_output, "interfaces.Vxlan1")) is None:
            self.result.is_skipped("Interface: Vxlan1 - Not configured")
            return

        difference1 = set(inputs_vteps).difference(set(vxlan1["vteps"]))
        difference2 = set(vxlan1["vteps"]).difference(set(inputs_vteps))

        if difference1:
            self.result.is_failure(f"The following VTEP peer(s) are missing from the Vxlan1 interface: {', '.join(sorted(difference1))}")

        if difference2:
            self.result.is_failure(f"Unexpected VTEP peer(s) on Vxlan1 interface: {', '.join(sorted(difference2))}")


class VerifyVxlan1ConnSettings(AntaTest):
    """Verifies Vxlan1 source interface and UDP port.

    Expected Results
    ----------------
    * Success: Passes if the interface vxlan1 source interface and UDP port are correct.
    * Failure: Fails if the interface vxlan1 source interface or UDP port are incorrect.
    * Skipped: Skips if the Vxlan1 interface is not configured.

    Examples
    --------
    ```yaml
    anta.tests.vxlan:
      - VerifyVxlan1ConnSettings:
          source_interface: Loopback1
          udp_port: 4789
    ```
    """

    categories: ClassVar[list[str]] = ["vxlan"]
    commands: ClassVar[list[AntaCommand | AntaTemplate]] = [AntaCommand(command="show interfaces", revision=1)]

    class Input(AntaTest.Input):
        """Input model for the VerifyVxlan1ConnSettings test."""

        source_interface: VxlanSrcIntf
        """Source interface of vxlan1 interface."""
        udp_port: int = Field(ge=1024, le=65335)
        """UDP port used for vxlan1 interface."""

    @AntaTest.anta_test
    def test(self) -> None:
        """Main test function for VerifyVxlan1ConnSettings."""
        self.result.is_success()
        command_output = self.instance_commands[0].json_output

        # Skip the test case if vxlan1 interface is not configured
        vxlan_output = get_value(command_output, "interfaces.Vxlan1")
        if not vxlan_output:
            self.result.is_skipped("Interface: Vxlan1 - Not configured")
            return

        src_intf = vxlan_output.get("srcIpIntf")
        port = vxlan_output.get("udpPort")

        # Check vxlan1 source interface and udp port
        if src_intf != self.inputs.source_interface:
            self.result.is_failure(f"Interface: Vxlan1 - Incorrect Source interface - Expected: {self.inputs.source_interface} Actual: {src_intf}")
        if port != self.inputs.udp_port:
            self.result.is_failure(f"Interface: Vxlan1 - Incorrect UDP port - Expected: {self.inputs.udp_port} Actual: {port}")
