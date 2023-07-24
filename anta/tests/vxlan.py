"""
Test functions related to VXLAN
"""

from anta.models import AntaCommand, AntaTest


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
        """
        Run VerifyVxlan1Interface validation
        """

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
        """
        Run VerifyVxlanConfigSanity validation
        """

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
