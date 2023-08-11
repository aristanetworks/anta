# Copyright (c) 2023 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""
Generic routing test functions
"""
# Mypy does not understand AntaTest.Input typing
# mypy: disable-error-code=attr-defined
from typing import Literal

from pydantic import model_validator

from anta.models import AntaCommand, AntaTest


class VerifyRoutingProtocolModel(AntaTest):
    """
    Verifies the configured routing protocol model is the one we expect.
    And if there is no mismatch between the configured and operating routing protocol model.
    """

    name = "VerifyRoutingProtocolModel"
    description = (
        "Verifies the configured routing protocol model is the expected one and if there is no mismatch between the configured and operating routing protocol model."
    )
    categories = ["routing", "generic"]
    commands = [AntaCommand(command="show ip route summary", revision=3)]

    class Input(AntaTest.Input):  # pylint: disable=missing-class-docstring
        model: Literal["multi-agent", "ribd"] = "multi-agent"
        """Expected routing protocol model"""

    @AntaTest.anta_test
    def test(self) -> None:
        command_output = self.instance_commands[0].json_output
        configured_model = command_output["protoModelStatus"]["configuredProtoModel"]
        operating_model = command_output["protoModelStatus"]["operatingProtoModel"]
        if configured_model == operating_model == self.inputs.model:
            self.result.is_success()
        else:
            self.result.is_failure(f"routing model is misconfigured: configured: {configured_model} - operating: {operating_model} - expected: {self.inputs.model}")


class VerifyRoutingTableSize(AntaTest):
    """
    Verifies the size of the IP routing table (default VRF).
    Should be between the two provided thresholds.
    """

    name = "VerifyRoutingTableSize"
    description = "Verifies the size of the IP routing table (default VRF). Should be between the two provided thresholds."
    categories = ["routing", "generic"]
    commands = [AntaCommand(command="show ip route summary", revision=3)]

    class Input(AntaTest.Input):  # pylint: disable=missing-class-docstring
        minimum: int
        """Expected minimum routing table (default VRF) size"""
        maximum: int
        """Expected maximum routing table (default VRF) size"""

        @model_validator(mode="after")
        def check_min_max(self) -> AntaTest.Input:
            """Validate that maximum is greater than minimum"""
            if self.minimum > self.maximum:
                raise ValueError(f"Minimum {self.minimum} is greater than maximum {self.maximum}")
            return self

    @AntaTest.anta_test
    def test(self) -> None:
        command_output = self.instance_commands[0].json_output
        total_routes = int(command_output["vrfs"]["default"]["totalRoutes"])
        if self.inputs.minimum <= total_routes <= self.inputs.maximum:
            self.result.is_success()
        else:
            self.result.is_failure(f"routing-table has {total_routes} routes and not between min ({self.inputs.minimum}) and maximum ({self.inputs.maximum})")


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
