"""
Test functions related to VXLAN
"""

from anta.models import AntaCommand, AntaTest


class VerifyVxlan(AntaTest):
    """
    Verifies if Vxlan1 interface is configured, and is up/up
    """

    name = "VerifyVxlan"
    description = "Verifies Vxlan1 status"
    categories = ["vxlan"]
    commands = [AntaCommand(command="show interfaces description", ofmt="json")]

    @AntaTest.anta_test
    def test(self) -> None:
        """Run VerifyVxlan validation"""

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
    Verifies that there are no VXLAN config-sanity issues flagged
    """

    name = "VerifyVxlanConfigSanity"
    description = "Verifies VXLAN config-sanity"
    categories = ["vxlan"]
    commands = [AntaCommand(command="show vxlan config-sanity", ofmt="json")]

    @AntaTest.anta_test
    def test(self) -> None:
        """Run VerifyVxlanConfigSanity validation"""

        command_output = self.instance_commands[0].json_output

        if "categories" not in command_output or len(command_output["categories"]) == 0:
            self.result.is_skipped("VXLAN is not configured on this device")
            return

        failed_categories = {
            category: content
            for category, content in command_output["categories"].items()
            if category in ["localVtep", "mlag", "pd"] and content["allCheckPass"] is not True
        }

        if len(failed_categories) > 0:
            self.result.is_failure(f"Vxlan config sanity check is not passing: {failed_categories}")
        else:
            self.result.is_success()
