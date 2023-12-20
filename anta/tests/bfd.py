# Copyright (c) 2023 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""
BFD test functions
"""
# Mypy does not understand AntaTest.Input typing
# mypy: disable-error-code=attr-defined
from __future__ import annotations

from ipaddress import IPv4Address, IPv6Address, ip_address
from typing import Any, List, Union, cast

from pydantic import BaseModel

from anta.models import AntaCommand, AntaTemplate, AntaTest
from anta.tools.get_value import get_value


class VerifyBFDPeers(AntaTest):
    """
    This class verifies if the BFD (Bidirectional Forwarding Detection) neighbor's sessions are UP and
    if the timers are correctly set in the specified VRF (Virtual Routing and Forwarding).

    Expected results:
        * success: The test will pass if BFD neighbors are UP and timers are correctly set in the specified VRF.
        * failure: The test will fail if BFD neighbors are not found, status is not UP, or timers are not as expected in the specified VRF.
    """

    name = "VerifyBFDPeers"
    description = "Verifies if BFD neighbor's sessions are UP and timers are correctly set in the specified VRF."
    categories = ["bfd"]
    commands = [AntaTemplate(template="show bfd peers dest-ip {neighbor} vrf {vrf} detail")]

    class Input(AntaTest.Input):
        """
        This class defines the input parameters of the testcase.
        """

        bfd_neighbors: List["BFDNeighbors"]
        """List of BFD neighbors"""

        class BFDNeighbors(BaseModel):
            """
            This class defines the details of a BFD neighbor.
            """

            neighbor: Union[IPv4Address, IPv6Address]
            """IPv4/IPv6 BFD neighbor"""
            vrf: str = "default"
            """VRF context"""
            loopback: Union[IPv4Address, IPv6Address]
            """Loopback IP address"""
            tx_interval: int
            """Tx interval of BFD neighbor"""
            rx_interval: int
            """Rx interval of BFD neighbor"""
            multiplier: int
            """Multiplier of BFD neighbor"""

    def render(self, template: AntaTemplate) -> List[AntaCommand]:
        """
        This method renders the template with the BFD neighbor details.
        """
        return [
            template.render(
                neighbor=bfd_neighbor.neighbor,
                vrf=bfd_neighbor.vrf,
                loopback=bfd_neighbor.loopback,
                tx_interval=bfd_neighbor.tx_interval,
                rx_interval=bfd_neighbor.rx_interval,
                multiplier=bfd_neighbor.multiplier,
            )
            for bfd_neighbor in self.inputs.bfd_neighbors
        ]

    def create_bfd_neighbor_key(self, vrf: str, neighbor: str) -> str:
        """
        Create a key for retrieving BFD neighbor information based on the VRF and neighbor's IP type.

        Parameters:
        - vrf (str): Virtual Routing and Forwarding context.
        - neighbor (str): IPv4 or IPv6 address of the BFD neighbor.

        Returns:
        str: Key used to retrieve BFD neighbor information from the command output.

        Example:
        >>> create_bfd_neighbor_key("default", "192.168.1.1")
        'vrfs..default..ipv4Neighbors..192.168.1.1..peers....types..multihop..peerStats'
        """
        ip_type = "ipv4" if isinstance(ip_address(neighbor), IPv4Address) else "ipv6"
        return f"vrfs..{vrf}..{ip_type}Neighbors..{neighbor}..peers....types..multihop..peerStats"

    @AntaTest.anta_test
    def test(self) -> None:
        failures: dict[str, Any] = {}

        # Iterating over command output for different neighbors
        for command in self.instance_commands:
            neighbor = cast(str, command.params.get("neighbor"))
            vrf = cast(str, command.params.get("vrf"))
            loopback = command.params.get("loopback")
            tx_interval = command.params.get("tx_interval")
            rx_interval = command.params.get("rx_interval")
            multiplier = command.params.get("multiplier")

            bfd_key = self.create_bfd_neighbor_key(vrf, neighbor)
            bfd_output = get_value(command.json_output, f"{bfd_key}..{loopback}", separator="..")

            # Verify BFD neighbor state and timers
            if not bfd_output:
                failures[str(neighbor)] = {vrf: "Not Configured"}
                continue

            bfd_details = bfd_output["peerStatsDetail"]
            status_up = bfd_output["status"] == "up"
            intervals_ok = bfd_details["operTxInterval"] == tx_interval and bfd_details["operRxInterval"] == rx_interval and bfd_details["detectMult"] == multiplier

            if not (status_up and intervals_ok):
                failures[str(neighbor)] = {
                    vrf: {
                        "status": bfd_output["status"],
                        "tx_interval": bfd_details["operTxInterval"],
                        "rx_interval": bfd_details["operRxInterval"],
                        "multiplier": bfd_details["detectMult"],
                    }
                }

        if not failures:
            self.result.is_success()
        else:
            message = f"Following BFD neighbors are not UP, not configured, or timers are not ok:\n{failures}"
            self.result.is_failure(message)
