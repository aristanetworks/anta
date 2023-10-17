# Copyright (c) 2023 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""
Test functions related to VXLAN
"""
# Mypy does not understand AntaTest.Input typing
# mypy: disable-error-code=attr-defined

from ipaddress import IPv4Address

# Need to keep List and Dict for pydantic in python 3.8
from typing import Dict, List

from anta.custom_types import Vlan, Vni
from anta.models import AntaCommand, AntaTest
from anta.tools.get_value import get_value


class VerifyVxlan1Interface(AntaTest):
    """
    This test verifies if the Vxlan1 interface is configured and 'up/up'.

    !!! warning
        The name of this test has been updated from 'VerifyVxlan' for better representation.

    Expected Results:
      * success: The test will pass if the Vxlan1 interface is configured with line protocol status and interface status 'up'.
      * failure: The test will fail if the Vxlan1 interface line protocol status or interface status are not 'up'.
      * skipped: The test will be skipped if the Vxlan1 interface is not configured.
    """

    name = "VerifyVxlan1Interface"
    description = "This test verifies if the Vxlan1 interface is configured and 'up/up'."
    categories = ["vxlan"]
    commands = [AntaCommand(command="show interfaces description", ofmt="json")]

    @AntaTest.anta_test
    def test(self) -> None:
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
                f"/{command_output['interfaceDescriptions']['Vxlan1']['interfaceStatus']}"
            )


class VerifyVxlanConfigSanity(AntaTest):
    """
    This test verifies that no issues are detected with the VXLAN configuration.

    Expected Results:
      * success: The test will pass if no issues are detected with the VXLAN configuration.
      * failure: The test will fail if issues are detected with the VXLAN configuration.
      * skipped: The test will be skipped if VXLAN is not configured on the device.
    """

    name = "VerifyVxlanConfigSanity"
    description = "This test verifies that no issues are detected with the VXLAN configuration."
    categories = ["vxlan"]
    commands = [AntaCommand(command="show vxlan config-sanity", ofmt="json")]

    @AntaTest.anta_test
    def test(self) -> None:
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
    """
    This test verifies the VNI-VLAN bindings of the Vxlan1 interface.

    Expected Results:
      * success: The test will pass if the VNI-VLAN bindings provided are properly configured.
      * failure: The test will fail if any VNI lacks bindings or if any bindings are incorrect.
      * skipped: The test will be skipped if the Vxlan1 interface is not configured.
    """

    name = "VerifyVxlanVniBinding"
    description = "Verifies the VNI-VLAN bindings of the Vxlan1 interface"
    categories = ["vxlan"]
    commands = [AntaCommand(command="show vxlan vni", ofmt="json")]

    class Input(AntaTest.Input):  # pylint: disable=missing-class-docstring
        bindings: Dict[Vni, Vlan]
        """VNI to VLAN bindings to verify"""

    @AntaTest.anta_test
    def test(self) -> None:
        self.result.is_success()

        no_binding = []
        wrong_binding = []

        if (vxlan1 := get_value(self.instance_commands[0].json_output, "vxlanIntfs.Vxlan1")) is None:
            self.result.is_skipped("Vxlan1 interface is not configured")
            return

        for vni, vlan in self.inputs.bindings.items():
            vni = str(vni)
            if vni in vxlan1["vniBindings"]:
                retrieved_vlan = vxlan1["vniBindings"][vni]["vlan"]
            elif vni in vxlan1["vniBindingsToVrf"]:
                retrieved_vlan = vxlan1["vniBindingsToVrf"][vni]["vlan"]
            else:
                no_binding.append(vni)
                retrieved_vlan = None

            if retrieved_vlan and vlan != retrieved_vlan:
                wrong_binding.append({vni: retrieved_vlan})

        if no_binding:
            self.result.is_failure(f"The following VNI(s) have no binding: {no_binding}")

        if wrong_binding:
            self.result.is_failure(f"The following VNI(s) have the wrong VLAN binding: {wrong_binding}")


class VerifyVxlanVtep(AntaTest):
    """
    This test verifies the VTEP peers of the Vxlan1 interface.

    Expected Results:
      * success: The test will pass if all provided VTEP peers are identified and matching.
      * failure: The test will fail if any VTEP peer is missing or there are unexpected VTEP peers.
      * skipped: The test will be skipped if the Vxlan1 interface is not configured.
    """

    name = "VerifyVxlanVtep"
    description = "Verifies the VTEP peers of the Vxlan1 interface"
    categories = ["vxlan"]
    commands = [AntaCommand(command="show vxlan vtep", ofmt="json")]

    class Input(AntaTest.Input):  # pylint: disable=missing-class-docstring
        vteps: List[IPv4Address]
        """List of VTEP peers to verify"""

    @AntaTest.anta_test
    def test(self) -> None:
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
