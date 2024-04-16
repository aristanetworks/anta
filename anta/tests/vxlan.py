# Copyright (c) 2023-2024 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Module related to VXLAN tests."""

# Mypy does not understand AntaTest.Input typing
# mypy: disable-error-code=attr-defined
from __future__ import annotations

from ipaddress import IPv4Address
from typing import TYPE_CHECKING, ClassVar

from pydantic import Field

from anta.custom_types import Vlan, Vni, VxlanSrcIntf
from anta.models import AntaCommand, AntaTest
from anta.tools import get_value

if TYPE_CHECKING:
    from anta.models import AntaTemplate


class VerifyVxlan1Interface(AntaTest):
    """Verifies if the Vxlan1 interface is configured and 'up/up'.

    Warning
    -------
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

    name = "VerifyVxlan1Interface"
    description = "Verifies the Vxlan1 interface status."
    categories: ClassVar[list[str]] = ["vxlan"]
    commands: ClassVar[list[AntaCommand | AntaTemplate]] = [AntaCommand(command="show interfaces description", revision=1)]

    @AntaTest.anta_test
    def test(self) -> None:
        """Main test function for VerifyVxlan1Interface."""
        command_output = self.instance_commands[0].json_output
        if "Vxlan1" not in command_output["interfaceDescriptions"]:
            self.result.is_skipped("Vxlan1 interface is not configured")
        elif (
            command_output["interfaceDescriptions"]["Vxlan1"]["lineProtocolStatus"] == "up"
            and command_output["interfaceDescriptions"]["Vxlan1"]["interfaceStatus"] == "up"
        ):
            self.result.is_success()
        else:
            self.result.is_failure(
                f"Vxlan1 interface is {command_output['interfaceDescriptions']['Vxlan1']['lineProtocolStatus']}"
                f"/{command_output['interfaceDescriptions']['Vxlan1']['interfaceStatus']}",
            )


class VerifyVxlanConfigSanity(AntaTest):
    """Verifies that no issues are detected with the VXLAN configuration.

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

    name = "VerifyVxlanConfigSanity"
    description = "Verifies there are no VXLAN config-sanity inconsistencies."
    categories: ClassVar[list[str]] = ["vxlan"]
    commands: ClassVar[list[AntaCommand | AntaTemplate]] = [AntaCommand(command="show vxlan config-sanity", revision=1)]

    @AntaTest.anta_test
    def test(self) -> None:
        """Main test function for VerifyVxlanConfigSanity."""
        command_output = self.instance_commands[0].json_output
        if "categories" not in command_output or len(command_output["categories"]) == 0:
            self.result.is_skipped("VXLAN is not configured")
            return
        failed_categories = {
            category: content
            for category, content in command_output["categories"].items()
            if category in ["localVtep", "mlag", "pd"] and content["allCheckPass"] is not True
        }
        if len(failed_categories) > 0:
            self.result.is_failure(f"VXLAN config sanity check is not passing: {failed_categories}")
        else:
            self.result.is_success()


class VerifyVxlanVniBinding(AntaTest):
    """Verifies the VNI-VLAN bindings of the Vxlan1 interface.

    Expected Results
    ----------------
    * Success: The test will pass if the VNI-VLAN bindings provided are properly configured.
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
    ```
    """

    name = "VerifyVxlanVniBinding"
    description = "Verifies the VNI-VLAN bindings of the Vxlan1 interface."
    categories: ClassVar[list[str]] = ["vxlan"]
    commands: ClassVar[list[AntaCommand | AntaTemplate]] = [AntaCommand(command="show vxlan vni", revision=1)]

    class Input(AntaTest.Input):
        """Input model for the VerifyVxlanVniBinding test."""

        bindings: dict[Vni, Vlan]
        """VNI to VLAN bindings to verify."""

    @AntaTest.anta_test
    def test(self) -> None:
        """Main test function for VerifyVxlanVniBinding."""
        self.result.is_success()

        no_binding = []
        wrong_binding = []

        if (vxlan1 := get_value(self.instance_commands[0].json_output, "vxlanIntfs.Vxlan1")) is None:
            self.result.is_skipped("Vxlan1 interface is not configured")
            return

        for vni, vlan in self.inputs.bindings.items():
            str_vni = str(vni)
            if str_vni in vxlan1["vniBindings"]:
                retrieved_vlan = vxlan1["vniBindings"][str_vni]["vlan"]
            elif str_vni in vxlan1["vniBindingsToVrf"]:
                retrieved_vlan = vxlan1["vniBindingsToVrf"][str_vni]["vlan"]
            else:
                no_binding.append(str_vni)
                retrieved_vlan = None

            if retrieved_vlan and vlan != retrieved_vlan:
                wrong_binding.append({str_vni: retrieved_vlan})

        if no_binding:
            self.result.is_failure(f"The following VNI(s) have no binding: {no_binding}")

        if wrong_binding:
            self.result.is_failure(f"The following VNI(s) have the wrong VLAN binding: {wrong_binding}")


class VerifyVxlanVtep(AntaTest):
    """Verifies the VTEP peers of the Vxlan1 interface.

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

    name = "VerifyVxlanVtep"
    description = "Verifies the VTEP peers of the Vxlan1 interface"
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
            self.result.is_skipped("Vxlan1 interface is not configured")
            return

        difference1 = set(inputs_vteps).difference(set(vxlan1["vteps"]))
        difference2 = set(vxlan1["vteps"]).difference(set(inputs_vteps))

        if difference1:
            self.result.is_failure(f"The following VTEP peer(s) are missing from the Vxlan1 interface: {sorted(difference1)}")

        if difference2:
            self.result.is_failure(f"Unexpected VTEP peer(s) on Vxlan1 interface: {sorted(difference2)}")


class VerifyVxlan1ConnSettings(AntaTest):
    """Verifies the interface vxlan1 source interface and UDP port.

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

    name = "VerifyVxlan1ConnSettings"
    description = "Verifies the interface vxlan1 source interface and UDP port."
    categories: ClassVar[list[str]] = ["vxlan"]
    commands: ClassVar[list[AntaCommand | AntaTemplate]] = [AntaCommand(command="show interfaces", revision=1)]

    class Input(AntaTest.Input):
        """Input model for the VerifyVxlan1ConnSettings test."""

        source_interface: VxlanSrcIntf
        """Source loopback interface of vxlan1 interface."""
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
            self.result.is_skipped("Vxlan1 interface is not configured.")
            return

        src_intf = vxlan_output.get("srcIpIntf")
        port = vxlan_output.get("udpPort")

        # Check vxlan1 source interface and udp port
        if src_intf != self.inputs.source_interface:
            self.result.is_failure(f"Source interface is not correct. Expected `{self.inputs.source_interface}` as source interface but found `{src_intf}` instead.")
        if port != self.inputs.udp_port:
            self.result.is_failure(f"UDP port is not correct. Expected `{self.inputs.udp_port}` as UDP port but found `{port}` instead.")
