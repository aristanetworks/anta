# Copyright (c) 2023 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""
Test functions related to various connectivity checks
"""
# Mypy does not understand AntaTest.Input typing
# mypy: disable-error-code=attr-defined
from __future__ import annotations

from ipaddress import IPv4Address

# Need to keep List for pydantic in python 3.8
from typing import List, Union

from pydantic import BaseModel

from anta.custom_types import Interface
from anta.models import AntaCommand, AntaMissingParamException, AntaTemplate, AntaTest


class VerifyReachability(AntaTest):
    """
    Test network reachability to one or many destination IP(s).

    Expected Results:
        * success: The test will pass if all destination IP(s) are reachable.
        * failure: The test will fail if one or many destination IP(s) are unreachable.
    """

    name = "VerifyReachability"
    description = "Test the network reachability to one or many destination IP(s)."
    categories = ["connectivity"]
    commands = [AntaTemplate(template="ping vrf {vrf} {destination} source {source} repeat {repeat}")]

    class Input(AntaTest.Input):  # pylint: disable=missing-class-docstring
        hosts: List[Host]
        """List of hosts to ping"""

        class Host(BaseModel):
            """Remote host to ping"""

            destination: IPv4Address
            """IPv4 address to ping"""
            source: Union[IPv4Address, Interface]
            """IPv4 address source IP or Egress interface to use"""
            vrf: str = "default"
            """VRF context"""
            repeat: int = 2
            """Number of ping repetition (default=2)"""

    def render(self, template: AntaTemplate) -> list[AntaCommand]:
        return [template.render(destination=host.destination, source=host.source, vrf=host.vrf, repeat=host.repeat) for host in self.inputs.hosts]

    @AntaTest.anta_test
    def test(self) -> None:
        failures = []
        for command in self.instance_commands:
            src = command.params.get("source")
            dst = command.params.get("destination")
            repeat = command.params.get("repeat")

            if any(elem is None for elem in (src, dst, repeat)):
                raise AntaMissingParamException(f"A parameter is missing to execute the test for command {command}")

            if f"{repeat} received" not in command.json_output["messages"][0]:
                failures.append((str(src), str(dst)))

        if not failures:
            self.result.is_success()
        else:
            self.result.is_failure(f"Connectivity test failed for the following source-destination pairs: {failures}")


class VerifyLLDPNeighbors(AntaTest):
    """
    This test verifies that the provided LLDP neighbors are present and connected with the correct configuration.

    Expected Results:
        * success: The test will pass if each of the provided LLDP neighbors is present and connected to the specified port and device.
        * failure: The test will fail if any of the following conditions are met:
            - The provided LLDP neighbor is not found.
            - The system name or port of the LLDP neighbor does not match the provided information.
    """

    name = "VerifyLLDPNeighbors"
    description = "Verifies that the provided LLDP neighbors are present and connected with the correct configuration."
    categories = ["connectivity"]
    commands = [AntaCommand(command="show lldp neighbors detail")]

    class Input(AntaTest.Input):  # pylint: disable=missing-class-docstring
        neighbors: List[Neighbor]
        """List of LLDP neighbors"""

        class Neighbor(BaseModel):
            """LLDP neighbor"""

            port: Interface
            """LLDP port"""
            neighbor_device: str
            """LLDP neighbor device"""
            neighbor_port: Interface
            """LLDP neighbor port"""

    @AntaTest.anta_test
    def test(self) -> None:
        command_output = self.instance_commands[0].json_output

        self.result.is_success()

        no_lldp_neighbor = []
        wrong_lldp_neighbor = []

        for neighbor in self.inputs.neighbors:
            if len(lldp_neighbor_info := command_output["lldpNeighbors"][neighbor.port]["lldpNeighborInfo"]) == 0:
                no_lldp_neighbor.append(neighbor.port)

            elif (
                lldp_neighbor_info[0]["systemName"] != neighbor.neighbor_device
                or lldp_neighbor_info[0]["neighborInterfaceInfo"]["interfaceId_v2"] != neighbor.neighbor_port
            ):
                wrong_lldp_neighbor.append(neighbor.port)

        if no_lldp_neighbor:
            self.result.is_failure(f"The following port(s) have no LLDP neighbor: {no_lldp_neighbor}")

        if wrong_lldp_neighbor:
            self.result.is_failure(f"The following port(s) have the wrong LLDP neighbor: {wrong_lldp_neighbor}")
