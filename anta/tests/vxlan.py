# Copyright (c) 2023 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""
Test functions related to VXLAN
"""
# Mypy does not understand AntaTest.Input typing
# mypy: disable-error-code=attr-defined
from typing import Dict

from anta.custom_types import Vlan, Vni
from anta.models import AntaCommand, AntaMissingParamException, AntaTemplate, AntaTest


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
    """

    name = "VerifyVxlanVniBinding"
    description = "Verifies the VNI-VLAN bindings of the Vxlan1 interface"
    categories = ["vxlan"]
    commands = [AntaTemplate(template="show vxlan vni {vni}", ofmt="json")]

    class Input(AntaTest.Input):  # pylint: disable=missing-class-docstring
        bindings: Dict[Vni, Vlan]
        """VNI to VLAN bindings to verify"""

    def render(self, template: AntaTemplate) -> list[AntaCommand]:
        return [template.render(vni=vni, vlan=vlan) for vni, vlan in self.inputs.bindings.items()]

    @AntaTest.anta_test
    def test(self) -> None:
        self.result.is_success()

        no_bindings = []
        wrong_bindings = []

        for command in self.instance_commands:
            vni, vlan = command.params.get("vni"), command.params.get("vlan")

            if vni is None or vlan is None:
                raise AntaMissingParamException(f"A parameter is missing to execute the test for command {command}")

            vni_bindings = command.json_output["vxlanIntfs"]["Vxlan1"]["vniBindings"]
            vni_bindings_to_vrf = command.json_output["vxlanIntfs"]["Vxlan1"]["vniBindingsToVrf"]

            if (vni := str(vni)) in vni_bindings:
                vlan_ = vni_bindings[vni]["vlan"]
            elif vni in vni_bindings_to_vrf:
                vlan_ = vni_bindings_to_vrf[vni]["vlan"]
            else:
                no_bindings.append(vni)
                vlan_ = None

            if vlan_ and vlan != vlan_:
                wrong_bindings.append({vni: vlan_})

        if no_bindings:
            self.result.is_failure(f"The following VNI(s) have no bindings: {no_bindings}")

        if wrong_bindings:
            self.result.is_failure(f"The following VNI(s) have the wrong VLAN binding: {wrong_bindings}")
