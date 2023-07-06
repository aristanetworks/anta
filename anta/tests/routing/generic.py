"""
Generic routing test functions
"""

from typing import Optional

from anta.models import AntaCommand, AntaTest


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
    # "revision": 3
    commands = [AntaCommand(command="show ip route summary")]

    @AntaTest.anta_test
    def test(self, model: Optional[str] = "multi-agent") -> None:
        """Run VerifyRoutingProtocolModel validation"""

        if not model:
            self.result.is_skipped("VerifyRoutingProtocolModel was not run as no model was given")
            return
        command_output = self.instance_commands[0].json_output

        configured_model = command_output["protoModelStatus"]["configuredProtoModel"]
        operating_model = command_output["protoModelStatus"]["operatingProtoModel"]
        if configured_model == operating_model == model:
            self.result.is_success()
        else:
            self.result.is_failure(f"routing model is misconfigured: configured: {configured_model} - operating: {operating_model} - expected: {model}")


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
    # "revision": 3
    commands = [AntaCommand(command="show ip route summary")]

    @AntaTest.anta_test
    def test(self, minimum: Optional[int] = None, maximum: Optional[int] = None) -> None:
        """Run VerifyRoutingTableSize validation"""

        if not minimum or not maximum:
            self.result.is_skipped(f"VerifyRoutingTableSize was not run as either minimum {minimum} or maximum {maximum} was not provided")
            return
        if not isinstance(minimum, int) or not isinstance(maximum, int):
            self.result.is_error(f"VerifyRoutingTableSize was not run as either minimum {minimum} or maximum {maximum} is not a valid value (integer)")
            return
        if maximum < minimum:
            self.result.is_error(f"VerifyRoutingTableSize was not run as minimum {minimum} is greate than maximum {maximum}.")
            return

        command_output = self.instance_commands[0].json_output
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
    # revision 1 as later revision introduce additional nesting for type
    commands = [AntaCommand(command="show bfd peers", revision=1)]

    @AntaTest.anta_test
    def test(self) -> None:
        """Run VerifyBFD validation"""

        command_output = self.instance_commands[0].json_output

        self.result.is_success()

        for _, vrf_data in command_output["vrfs"].items():
            for _, neighbor_data in vrf_data["ipv4Neighbors"].items():
                for peer, peer_data in neighbor_data["peerStats"].items():
                    if (peer_status := peer_data["status"]) != "up":
                        failure_message = f"bfd state for peer '{peer}' is {peer_status} (expected up)."
                        if (peer_l3intf := peer_data.get("l3intf")) is not None and peer_l3intf != "":
                            failure_message += f" Interface: {peer_l3intf}."
                        self.result.is_failure(failure_message)
