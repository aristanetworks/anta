"""
Test functions related to Multi-Chassis LAG
"""
import logging
from typing import Any, Dict, cast

from anta.models import AntaTest, AntaTestCommand

logger = logging.getLogger(__name__)


class VerifyMlagStatus(AntaTest):
    """
    Verifies if MLAG us running, and if the status is good
    state is active, negotiation status is connected, local int is up, peer link is up.
    """

    name = "VerifyMlagStatus"
    description = "Verifies MLAG status"
    categories = ["mlag"]
    commands = [AntaTestCommand(command="show mlag", ofmt="json")]

    @AntaTest.anta_test
    def test(self) -> None:
        """Run VerifyMlagStatus validation"""

        command_output = cast(Dict[str, Dict[str, Any]], self.instance_commands[0].output)

        if command_output["state"] == "disabled":
            self.result.is_skipped("MLAG is disabled")
        elif (
            command_output["state"] != "active"
            or command_output["negStatus"] != "connected"
            or command_output["localIntfStatus"] != "up"
            or command_output["peerLinkStatus"] != "up"
        ):
            self.result.is_failure(f"MLAG status is not OK: {command_output}")
        else:
            self.result.is_success()


class VerifyMlagInterfaces(AntaTest):
    """
    Verifies there are no inactive or active-partial MLAG interfaces.
    """

    name = "VerifyMlagInterfaces"
    description = "Verifies there are no inactive or active-partial MLAG interfaces."
    categories = ["mlag"]
    commands = [AntaTestCommand(command="show mlag", ofmt="json")]

    @AntaTest.anta_test
    def test(self) -> None:
        """Run VerifyMlagInterfaces validation"""

        command_output = cast(Dict[str, Dict[str, Any]], self.instance_commands[0].output)

        if command_output["state"] == "disabled":
            self.result.is_skipped("MLAG is disabled")
        elif command_output["mlagPorts"]["Inactive"] != 0 or command_output["mlagPorts"]["Active-partial"] != 0:
            self.result.is_failure(f"MLAG status is not OK: {command_output['mlagPorts']}")
        else:
            self.result.is_success()


class VerifyMlagConfigSanity(AntaTest):
    """
    Verifies there are no MLAG config-sanity inconsistencies.
    """

    name = "VerifyMlagConfigSanity"
    description = "Verifies there are no MLAG config-sanity inconsistencies."
    categories = ["mlag"]
    commands = [AntaTestCommand(command="show mlag config-sanity", ofmt="json")]

    @AntaTest.anta_test
    def test(self) -> None:
        """Run VerifyMlagConfigSanity validation"""

        command_output = cast(Dict[str, Dict[str, Any]], self.instance_commands[0].output)

        if "mlagActive" not in command_output.keys():
            self.result.is_error("Incorrect JSON response - mlagActive state not found")
        elif command_output["mlagActive"] is False:
            self.result.is_skipped("MLAG is disabled")
        elif len(command_output["globalConfiguration"]) > 0 or len(command_output["interfaceConfiguration"]) > 0:
            self.result.is_failure()
            if len(command_output["globalConfiguration"]) > 0:
                self.result.is_failure("MLAG config-sanity returned Global inconsistancies: " f"{command_output['globalConfiguration']}")
            if len(command_output["interfaceConfiguration"]) > 0:
                self.result.is_failure("MLAG config-sanity returned Interface inconsistancies: " f"{command_output['interfaceConfiguration']}")
        else:
            self.result.is_success()
