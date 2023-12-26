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
from typing import Any, Dict, List, Union

from pydantic import BaseModel

from anta.models import AntaCommand, AntaTemplate, AntaTest
from anta.tools.get_value import get_value


def get_bfd_output(command: Any) -> Dict[str, Any] | None:
    """
    This function extracts the BFD output for a given command.

    Parameters:
    command: The command object which contains parameters and json_output.

    Returns:
    Dict or None: The BFD output if it exists, otherwise None.
    """
    peer = command.params.get("peer")
    vrf = command.params.get("vrf")
    source_address = command.params.get("source_address")
    bfd_key = create_bfd_peer_key(vrf, peer)
    bfd_output = get_value(command.json_output, f"{bfd_key}", separator="..")
    if not bfd_output:
        return None

    bfd_output = bfd_output.get("normal", bfd_output.get("multihop", {})).get("peerStats", {}).get(str(source_address), {})
    return bfd_output


def create_bfd_peer_key(vrf: str, peer: str) -> str:
    """
    Create a key for retrieving BFD peer information based on the VRF and peer's IP type.

    Parameters:
    - vrf (str): Virtual Routing and Forwarding context.
    - peer (str): IPv4 or IPv6 address of the BFD peer.

    Returns:
    str: Key used to retrieve BFD peer information from the command output.

    Example:
    >>> create_bfd_peer_key("default", "192.168.1.1")
    'vrfs..default..ipv4Neighbors..192.168.1.1..peers....types..multihop..peerStats'
    """
    ip_type = "ipv4" if isinstance(ip_address(peer), IPv4Address) else "ipv6"
    return f"vrfs..{vrf}..{ip_type}Neighbors..{peer}..peers....types"


class VerifyBFDSpecificPeers(AntaTest):
    """
    This class verifies if the BFD peer's sessions are UP and remote disc is non-zero in the specified VRF.
    Session types are supported as normal and multihop. Default it will check for normal, if not exist then will check for multihop.

    Expected results:
        * success: The test will pass if BFD peers are up and remote disc is non-zero in the specified VRF.
        * failure: The test will fail if BFD peers are not found, the status is not UP or remote disc is zero in the specified VRF.
    """

    name = "VerifyBFDSpecificPeers"
    description = "Verifies if the BFD peer's sessions are UP and remote disc is non-zero in the specified VRF."
    categories = ["bfd"]
    commands = [AntaTemplate(template="show bfd peers dest-ip {peer} vrf {vrf}")]

    class Input(AntaTest.Input):
        """
        This class defines the input parameters of the testcase.
        """

        bfd_peers: List[BFDPeers]
        """List of BFD peers"""

        class BFDPeers(BaseModel):
            """
            This class defines the details of a BFD peer.
            """

            peer: Union[IPv4Address, IPv6Address]
            """IPv4/IPv6 BFD peer"""
            vrf: str = "default"
            """VRF context"""
            source_address: Union[IPv4Address, IPv6Address]
            """Source IP address of BFD peer"""

    def render(self, template: AntaTemplate) -> List[AntaCommand]:
        """
        This method renders the template with the BFD peer details.
        """
        return [
            template.render(
                peer=bfd_peer.peer,
                vrf=bfd_peer.vrf,
                source_address=bfd_peer.source_address,
            )
            for bfd_peer in self.inputs.bfd_peers
        ]

    @AntaTest.anta_test
    def test(self) -> None:
        failures: dict[str, Any] = {}

        # Iterating over command output for different peers
        for command in self.instance_commands:
            peer = command.params.get("peer")
            vrf = command.params.get("vrf")
            bfd_output = get_bfd_output(command)
            if not bfd_output:
                failures[str(peer)] = {vrf: "Not Configured"}
                continue

            # Verify BFD peer status and remote disc
            if not (bfd_output.get("status") == "up" and bfd_output.get("remoteDisc") != 0):
                failures[str(peer)] = {vrf: {"status": bfd_output.get("status"), "remote_disc": bfd_output.get("remoteDisc")}}

        if not failures:
            self.result.is_success()
        else:
            self.result.is_failure(f"Following BFD peers are not configured, status is not up or remote disc is zero:\n{failures}")


class VerifyBFDPeersIntervals(AntaTest):
    """
    This class verifies the timers of the BFD peers in the specified VRF.
    Session types are supported as normal and multihop. Default it will check for normal, if not exist then will check for multihop.

    Expected results:
        * success: The test will pass if the timers of the BFD peers are correct in the specified VRF.
        * failure: The test will fail if the BFD peers are not found or their timers are incorrect in the specified VRF.
    """

    name = "VerifyBFDPeersIntervals"
    description = "Verifies the timers of the BFD peers in the specified VRF."
    categories = ["bfd"]
    commands = [AntaTemplate(template="show bfd peers dest-ip {peer} vrf {vrf} detail")]

    class Input(AntaTest.Input):
        """
        This class defines the input parameters of the testcase.
        """

        bfd_peers: List[BFDPeers]
        """List of BFD peers"""

        class BFDPeers(BaseModel):
            """
            This class defines the details of a BFD peer.
            """

            peer: Union[IPv4Address, IPv6Address]
            """IPv4/IPv6 BFD peer"""
            vrf: str = "default"
            """VRF context"""
            source_address: Union[IPv4Address, IPv6Address]
            """Source IP address of BFD peer"""
            tx_interval: int
            """Tx interval of BFD peer"""
            rx_interval: int
            """Rx interval of BFD peer"""
            multiplier: int
            """Multiplier of BFD peer"""

    def render(self, template: AntaTemplate) -> List[AntaCommand]:
        """
        This method renders the template with the BFD peer details.
        """
        return [
            template.render(
                peer=bfd_peer.peer,
                vrf=bfd_peer.vrf,
                source_address=bfd_peer.source_address,
                tx_interval=bfd_peer.tx_interval,
                rx_interval=bfd_peer.rx_interval,
                multiplier=bfd_peer.multiplier,
            )
            for bfd_peer in self.inputs.bfd_peers
        ]

    @AntaTest.anta_test
    def test(self) -> None:
        failures: dict[str, Any] = {}

        # Iterating over command output for different peers
        for command in self.instance_commands:
            peer = command.params.get("peer")
            vrf = command.params.get("vrf")
            tx_interval = command.params.get("tx_interval")
            rx_interval = command.params.get("rx_interval")
            multiplier = command.params.get("multiplier")
            bfd_output = get_bfd_output(command)
            if not bfd_output:
                failures[str(peer)] = {vrf: "Not Configured"}
                continue

            bfd_details = bfd_output.get("peerStatsDetail", {})
            intervals_ok = (
                bfd_details.get("operTxInterval") == tx_interval and bfd_details.get("operRxInterval") == rx_interval and bfd_details.get("detectMult") == multiplier
            )

            # Verify timers of BFD peer
            if not intervals_ok:
                failures[str(peer)] = {
                    vrf: {
                        "tx_interval": bfd_details.get("operTxInterval"),
                        "rx_interval": bfd_details.get("operRxInterval"),
                        "multiplier": bfd_details.get("detectMult"),
                    }
                }

        if not failures:
            self.result.is_success()
        else:
            self.result.is_failure(f"Following BFD peers are not configured or timers are not correct:\n{failures}")
