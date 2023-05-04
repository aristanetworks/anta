"""
Generic routing test functions
"""
import logging

from typing import Any, Dict, Optional, cast

from anta.models import AntaTest, AntaTestCommand

logger = logging.getLogger(__name__)


class VerifyRoutingProtocolModel(AntaTest):
    """
    Verifies the configured routing protocol model is the one we expect.
    And if there is no mismatch between the configured and operating routing protocol model.

        model(str): Expected routing protocol model (multi-agent or ribd). Default is multi-agent
    """

    name = "VerifyRoutingProtocolModel"
    description = (
        "Verifies the configured routing protocol model is the expected one and if there is no mismatch between the configured and operating routing protocol model."
    )
    categories = ["routing", "generic"]
    commands = [AntaTestCommand(command="show ip route summary")]
    # TODO - revision
    # command_output = await device.session.cli(command={"cmd": "show ip route summary", "revision": 3}, ofmt="json")

    @AntaTest.anta_test
    def test(self, model: Optional[str] = "multi-agent") -> None:
        """Run VerifyRoutingProtocolModel validation"""

        if not model:
            self.result.is_skipped("VerifyRoutingProtocolModel was not run as no model was given")
            return
        command_output = cast(Dict[str, Dict[Any, Any]], self.instance_commands[0].output)

        configured_model = command_output["protoModelStatus"]["configuredProtoModel"]
        operating_model = command_output["protoModelStatus"]["operatingProtoModel"]
        if configured_model == operating_model == model:
            self.result.is_success()
        else:
            self.result.is_failure(f"routing model is misconfigured: configured:{configured_model} - " f"operating:{operating_model} - expected:{model} ")


class VerifyRoutingTableSize(AntaTest):
    """
    Verifies the size of the IP routing table (default VRF).
    Should be between the two provided thresholds.

    Args:
        minimum(int): Expected minimum routing table (default VRF) size.
        maximum(int): Expected maximum routing table (default VRF) size.
    """

    name = "VerifyRoutingTableSize"
    description = "Verifies the size of the IP routing table (default VRF). Should be between the two provided thresholds."
    categories = ["routing", "generic"]
    commands = [AntaTestCommand(command="show ip route summary")]
    # command_output = await device.session.cli(command={"cmd": "show ip route summary", "revision": 3}, ofmt="json")

    @AntaTest.anta_test
    def test(self, minimum: Optional[int] = None, maximum: Optional[int] = None) -> None:
        """Run VerifyRoutingTableSize validation"""

        # TODO - extra checks on min < max?
        if not minimum or not maximum:
            self.result.is_skipped("VerifyRoutingTableSize was not run as no minimum or maximum were given")
            return
        command_output = cast(Dict[str, Dict[Any, Any]], self.instance_commands[0].output)
        total_routes = int(command_output["vrfs"]["default"]["totalRoutes"])
        if minimum <= total_routes <= maximum:
            self.result.is_success()
        else:
            self.result.is_failure(f"routing-table has {total_routes} routes and not between min ({minimum}) and maximum ({maximum})")


class VerifyBFD(AntaTest):
    """
    Verifies there is no BFD peer in down state (all VRF, IPv4 neighbors).
    """

    name = "VerifyBFD"
    description = "Verifies there is no BFD peer in down state (all VRF, IPv4 neighbors)."
    categories = ["routing", "generic"]
    commands = [AntaTestCommand(command="show bfd peers")]

    @AntaTest.anta_test
    def test(self) -> None:
        """Run VerifyBFD validation"""

        command_output = cast(Dict[str, Dict[Any, Any]], self.instance_commands[0].output)

        has_failed: bool = False
        for vrf in command_output["vrfs"]:
            for neighbor in command_output["vrfs"][vrf]["ipv4Neighbors"]:
                for interface in command_output["vrfs"][vrf]["ipv4Neighbors"][neighbor]["peerStats"]:
                    if command_output["vrfs"][vrf]["ipv4Neighbors"][neighbor]["peerStats"][interface]["status"] != "up":
                        intf_state = command_output["vrfs"][vrf]["ipv4Neighbors"][neighbor]["peerStats"][interface]["status"]
                        intf_name = command_output["vrfs"][vrf]["ipv4Neighbors"][neighbor]["peerStats"][interface]
                        has_failed = True
                        self.result.is_failure(f"bfd state on interface {intf_name} is {intf_state} (expected up)")
        if has_failed is False:
            self.result.is_success()
