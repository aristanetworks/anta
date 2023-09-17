# Copyright (c) 2023 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""
Generic routing test functions
"""
from __future__ import annotations

from ipaddress import IPv4Address, ip_interface

# Need to keep List for pydantic in python 3.8
from typing import List, Literal

from pydantic import model_validator

from anta.models import AntaCommand, AntaTemplate, AntaTest

# Mypy does not understand AntaTest.Input typing
# mypy: disable-error-code=attr-defined


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

        @model_validator(mode="after")  # type: ignore
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


class VerifyRoutingTableEntry(AntaTest):
    """
    This test verifies that the provided routes are present in the routing table of a specified VRF.

    Expected Results:
        * success: The test will pass if the provided routes are present in the routing table.
        * failure: The test will fail if one or many provided routes are missing from the routing table.
    """

    name = "VerifyRoutingTableEntry"
    description = "Verifies that the provided routes are present in the routing table of a specified VRF."
    categories = ["routing", "generic"]
    commands = [AntaTemplate(template="show ip route vrf {vrf} {route}")]

    class Input(AntaTest.Input):  # pylint: disable=missing-class-docstring
        vrf: str = "default"
        """VRF context"""
        routes: List[IPv4Address]
        """Routes to verify"""

    def render(self, template: AntaTemplate) -> list[AntaCommand]:
        return [template.render(vrf=self.inputs.vrf, route=route) for route in self.inputs.routes]

    @AntaTest.anta_test
    def test(self) -> None:
        missing_routes = []

        for command in self.instance_commands:
            if "vrf" in command.params and "route" in command.params:
                vrf, route = command.params["vrf"], command.params["route"]
                if len(routes := command.json_output["vrfs"][vrf]["routes"]) == 0 or route != ip_interface(list(routes)[0]).ip:
                    missing_routes.append(str(route))

        if not missing_routes:
            self.result.is_success()
        else:
            self.result.is_failure(f"The following route(s) are missing from the routing table of VRF {self.inputs.vrf}: {missing_routes}")
