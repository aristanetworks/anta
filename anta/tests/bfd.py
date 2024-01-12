# Copyright (c) 2023-2024 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""
BFD test functions
"""
# Mypy does not understand AntaTest.Input typing
# mypy: disable-error-code=attr-defined
from __future__ import annotations

from ipaddress import IPv4Address
from typing import Any, List

from pydantic import BaseModel

from anta.models import AntaCommand, AntaTest
from anta.tools.get_value import get_value


class VerifyBFDSpecificPeers(AntaTest):
    """
    This class verifies if the BFD peer's sessions are UP and remote disc is non-zero in the specified VRF.

    Expected results:
        * success: The test will pass if BFD peers are up and remote disc is non-zero in the specified VRF.
        * failure: The test will fail if BFD peers are not found, the status is not UP or remote disc is zero in the specified VRF.
    """

    name = "VerifyBFDSpecificPeers"
    description = "Verifies the BFD peer's sessions and remote disc in the specified VRF."
    categories = ["bfd"]
    commands = [AntaCommand(command="show bfd peers")]

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

            peer_address: IPv4Address
            """IPv4 address of a BFD peer"""
            vrf: str = "default"
            """Optional VRF for BGP peer. If not provided, it defaults to `default`."""

    @AntaTest.anta_test
    def test(self) -> None:
        failures: dict[Any, Any] = {}

        # Iterating over BFD peers
        for bfd_peer in self.inputs.bfd_peers:
            peer = str(bfd_peer.peer_address)
            vrf = bfd_peer.vrf
            bfd_output = get_value(self.instance_commands[0].json_output, f"vrfs..{vrf}..ipv4Neighbors..{peer}..peerStats..", separator="..")

            # Check if BFD peer configured
            if not bfd_output:
                failures[peer] = {vrf: "Not Configured"}
                continue

            # Check BFD peer status and remote disc
            if not (bfd_output.get("status") == "up" and bfd_output.get("remoteDisc") != 0):
                failures[peer] = {vrf: {"status": bfd_output.get("status"), "remote_disc": bfd_output.get("remoteDisc")}}

        if not failures:
            self.result.is_success()
        else:
            self.result.is_failure(f"Following BFD peers are not configured, status is not up or remote disc is zero:\n{failures}")


class VerifyBFDPeersIntervals(AntaTest):
    """
    This class verifies the timers of the BFD peers in the specified VRF.

    Expected results:
        * success: The test will pass if the timers of the BFD peers are correct in the specified VRF.
        * failure: The test will fail if the BFD peers are not found or their timers are incorrect in the specified VRF.
    """

    name = "VerifyBFDPeersIntervals"
    description = "Verifies the timers of the BFD peers in the specified VRF."
    categories = ["bfd"]
    commands = [AntaCommand(command="show bfd peers detail")]

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

            peer_address: IPv4Address
            """IPv4 address of a BFD peer"""
            vrf: str = "default"
            """Optional VRF for BGP peer. If not provided, it defaults to `default`."""
            tx_interval: int
            """Tx interval of BFD peer"""
            rx_interval: int
            """Rx interval of BFD peer"""
            multiplier: int
            """Multiplier of BFD peer"""

    @AntaTest.anta_test
    def test(self) -> None:
        failures: dict[Any, Any] = {}

        # Iterating over BFD peers
        for bfd_peers in self.inputs.bfd_peers:
            peer = str(bfd_peers.peer_address)
            vrf = bfd_peers.vrf
            tx_interval = bfd_peers.tx_interval
            rx_interval = bfd_peers.rx_interval
            multiplier = bfd_peers.multiplier
            bfd_output = get_value(self.instance_commands[0].json_output, f"vrfs..{vrf}..ipv4Neighbors..{peer}..peerStats..", separator="..")

            # Check if BFD peer configured
            if not bfd_output:
                failures[peer] = {vrf: "Not Configured"}
                continue

            bfd_details = bfd_output.get("peerStatsDetail", {})
            intervals_ok = (
                bfd_details.get("operTxInterval") == tx_interval and bfd_details.get("operRxInterval") == rx_interval and bfd_details.get("detectMult") == multiplier
            )

            # Check timers of BFD peer
            if not intervals_ok:
                failures[peer] = {
                    vrf: {
                        "tx_interval": bfd_details.get("operTxInterval"),
                        "rx_interval": bfd_details.get("operRxInterval"),
                        "multiplier": bfd_details.get("detectMult"),
                    }
                }

        # Check if any failures
        if not failures:
            self.result.is_success()
        else:
            self.result.is_failure(f"Following BFD peers are not configured or timers are not correct:\n{failures}")
