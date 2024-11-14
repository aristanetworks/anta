# Copyright (c) 2023-2024 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Module related to BFD tests."""

# Mypy does not understand AntaTest.Input typing
# mypy: disable-error-code=attr-defined
from __future__ import annotations

from datetime import datetime, timezone
from typing import TYPE_CHECKING, ClassVar

from pydantic import Field

from anta.input_models.bfd import BFDPeer
from anta.models import AntaCommand, AntaTest
from anta.tools import get_value

if TYPE_CHECKING:
    from anta.models import AntaTemplate


class VerifyBFDSpecificPeers(AntaTest):
    """Verifies if the IPv4 BFD peer sessions are in the UP state and the remote discriminator (disc) is non-zero within the specified VRF.

    This test performs the following checks for each specified peer:

      1. Confirms that the specified VRF is configured.
      2. Verifies that the peer exists in the BFD configuration.
      3. For each specified BFD peer:
        - Validates that the state is up
        - Confirms that the remote discriminator identifier is non-zero.

    Expected Results
    ----------------
    * Success: If all of the following conditions are met:
        - All specified peers are found in the BFD configuration within the specified VRF.
        - All BFD peers are up and remote disc is non-zero.
    * Failure: If any of the following occur:
        - A specified peer is not found in the BFD configuration within the specified VRF.
        - Any BFD peer session is not up or the remote discriminator identifier is zero.

    Examples
    --------
    ```yaml
    anta.tests.bfd:
      - VerifyBFDSpecificPeers:
          bfd_peers:
            - peer_address: 192.0.255.8
              vrf: default
            - peer_address: 192.0.255.7
              vrf: default
    ```
    """

    description = "Verifies the IPv4 BFD peer's sessions and remote disc in the specified VRF."
    categories: ClassVar[list[str]] = ["bfd"]
    commands: ClassVar[list[AntaCommand | AntaTemplate]] = [AntaCommand(command="show bfd peers", revision=1)]

    class Input(AntaTest.Input):
        """Input model for the VerifyBFDSpecificPeers test."""

        bfd_peers: list[BFDPeer]
        """List of IPv4 BFD"""
        BFDPeer: ClassVar[type[BFDPeer]] = BFDPeer

    @AntaTest.anta_test
    def test(self) -> None:
        """Main test function for VerifyBFDSpecificPeers."""
        self.result.is_success()

        # Iterating over BFD peers
        for bfd_peer in self.inputs.bfd_peers:
            peer = str(bfd_peer.peer_address)
            vrf = bfd_peer.vrf
            bfd_output = get_value(
                self.instance_commands[0].json_output,
                f"vrfs..{vrf}..ipv4Neighbors..{peer}..peerStats..",
                separator="..",
            )

            # Check if BFD peer configured
            if not bfd_output:
                self.result.is_failure(f"{bfd_peer} - Not found")
                continue

            # Check BFD peer status and remote disc
            state = bfd_output.get("status")
            remote_disc = bfd_output.get("remoteDisc")
            if not (state == "up" and remote_disc != 0):
                self.result.is_failure(f"{bfd_peer} - Session not properly established; State: {state} Remote Discriminator: {remote_disc}")


class VerifyBFDPeersIntervals(AntaTest):
    """Verifies the timers of the IPv4 BFD peers in the specified VRF.

    This test performs the following checks for each specified peer:

      1. Confirms that the specified VRF is configured.
      2. Verifies that the peer exists in the BFD configuration.
      3. Confirms that BFD peer is correctly configured with the `Transmit interval, Receive interval and Multiplier`.

    Expected Results
    ----------------
    * Success: If all of the following conditions are met:
        - All specified peers are found in the BFD configuration within the specified VRF.
        - All BFD peers are correctly configured with the `Transmit interval, Receive interval and Multiplier`.
    * Failure: If any of the following occur:
        - A specified peer is not found in the BFD configuration within the specified VRF.
        - Any BFD peer not correctly configured with the `Transmit interval, Receive interval and Multiplier`.

    Examples
    --------
    ```yaml
    anta.tests.bfd:
      - VerifyBFDPeersIntervals:
          bfd_peers:
            - peer_address: 192.0.255.8
              vrf: default
              tx_interval: 1200
              rx_interval: 1200
              multiplier: 3
            - peer_address: 192.0.255.7
              vrf: default
              tx_interval: 1200
              rx_interval: 1200
              multiplier: 3
    ```
    """

    categories: ClassVar[list[str]] = ["bfd"]
    commands: ClassVar[list[AntaCommand | AntaTemplate]] = [AntaCommand(command="show bfd peers detail", revision=1)]

    class Input(AntaTest.Input):
        """Input model for the VerifyBFDPeersIntervals test."""

        bfd_peers: list[BFDPeer]
        """List of IPv4 BFD"""
        BFDPeer: ClassVar[type[BFDPeer]] = BFDPeer

    @AntaTest.anta_test
    def test(self) -> None:
        """Main test function for VerifyBFDPeersIntervals."""
        self.result.is_success()

        # Iterating over BFD peers
        for bfd_peer in self.inputs.bfd_peers:
            peer = str(bfd_peer.peer_address)
            vrf = bfd_peer.vrf
            tx_interval = bfd_peer.tx_interval
            rx_interval = bfd_peer.rx_interval
            multiplier = bfd_peer.multiplier

            # Check if BFD peer configured
            bfd_output = get_value(
                self.instance_commands[0].json_output,
                f"vrfs..{vrf}..ipv4Neighbors..{peer}..peerStats..",
                separator="..",
            )
            if not bfd_output:
                self.result.is_failure(f"{bfd_peer} - Not found")
                continue

            # Convert interval timer(s) into milliseconds to be consistent with the inputs.
            bfd_details = bfd_output.get("peerStatsDetail", {})
            op_tx_interval = bfd_details.get("operTxInterval") // 1000
            op_rx_interval = bfd_details.get("operRxInterval") // 1000
            detect_multiplier = bfd_details.get("detectMult")

            # Check timers of BFD peer
            intervals_ok = op_tx_interval == tx_interval and op_rx_interval == rx_interval and detect_multiplier == multiplier
            if not intervals_ok:
                self.result.is_failure(
                    f"{bfd_peer} - Incorrect timers; Transmit interval: {op_tx_interval}, Receive interval: {op_rx_interval}, Multiplier: {detect_multiplier}"
                )


class VerifyBFDPeersHealth(AntaTest):
    """Verifies the health of IPv4 BFD peers across all VRFs.

    It checks that no BFD peer is in the down state and that the discriminator value of the remote system is not zero.

    Optionally, it can also verify that BFD peers have not been down before a specified threshold of hours.

    Expected Results
    ----------------
    * Success: The test will pass if all IPv4 BFD peers are up, the discriminator value of each remote system is non-zero,
               and the last downtime of each peer is above the defined threshold.
    * Failure: The test will fail if any IPv4 BFD peer is down, the discriminator value of any remote system is zero,
               or the last downtime of any peer is below the defined threshold.

    Examples
    --------
    ```yaml
    anta.tests.bfd:
      - VerifyBFDPeersHealth:
          down_threshold: 2
    ```
    """

    categories: ClassVar[list[str]] = ["bfd"]
    # revision 1 as later revision introduces additional nesting for type
    commands: ClassVar[list[AntaCommand | AntaTemplate]] = [
        AntaCommand(command="show bfd peers", revision=1),
        AntaCommand(command="show clock", revision=1),
    ]

    class Input(AntaTest.Input):
        """Input model for the VerifyBFDPeersHealth test."""

        down_threshold: int | None = Field(default=None, gt=0)
        """Optional down threshold in hours to check if a BFD peer was down before those hours or not."""

    @AntaTest.anta_test
    def test(self) -> None:
        """Main test function for VerifyBFDPeersHealth."""
        # Initialize failure strings
        down_failures = []
        up_failures = []

        # Extract the current timestamp and command output
        clock_output = self.instance_commands[1].json_output
        current_timestamp = clock_output["utcTime"]
        bfd_output = self.instance_commands[0].json_output

        # set the initial result
        self.result.is_success()

        # Check if any IPv4 BFD peer is configured
        ipv4_neighbors_exist = any(vrf_data["ipv4Neighbors"] for vrf_data in bfd_output["vrfs"].values())
        if not ipv4_neighbors_exist:
            self.result.is_failure("No IPv4 BFD peers are configured for any VRF.")
            return

        # Iterate over IPv4 BFD peers
        for vrf, vrf_data in bfd_output["vrfs"].items():
            for peer, neighbor_data in vrf_data["ipv4Neighbors"].items():
                for peer_data in neighbor_data["peerStats"].values():
                    peer_status = peer_data["status"]
                    remote_disc = peer_data["remoteDisc"]
                    remote_disc_info = f" with remote disc {remote_disc}" if remote_disc == 0 else ""
                    last_down = peer_data["lastDown"]
                    hours_difference = (
                        datetime.fromtimestamp(current_timestamp, tz=timezone.utc) - datetime.fromtimestamp(last_down, tz=timezone.utc)
                    ).total_seconds() / 3600

                    # Check if peer status is not up
                    if peer_status != "up":
                        down_failures.append(f"{peer} is {peer_status} in {vrf} VRF{remote_disc_info}.")

                    # Check if the last down is within the threshold
                    elif self.inputs.down_threshold and hours_difference < self.inputs.down_threshold:
                        up_failures.append(f"{peer} in {vrf} VRF was down {round(hours_difference)} hours ago{remote_disc_info}.")

                    # Check if remote disc is 0
                    elif remote_disc == 0:
                        up_failures.append(f"{peer} in {vrf} VRF has remote disc {remote_disc}.")

        # Check if there are any failures
        if down_failures:
            down_failures_str = "\n".join(down_failures)
            self.result.is_failure(f"Following BFD peers are not up:\n{down_failures_str}")
        if up_failures:
            up_failures_str = "\n".join(up_failures)
            self.result.is_failure(f"\nFollowing BFD peers were down:\n{up_failures_str}")


class VerifyBFDPeersRegProtocols(AntaTest):
    """Verifies the registered routing protocol of the IPv4 BFD peers in the specified VRF.

    This test performs the following checks for each specified peer:

      1. Confirms that the specified VRF is configured.
      2. Verifies that the peer exists in the BFD configuration.
      3. Confirms that BFD peer is correctly configured with the routing protocol.

    Expected Results
    ----------------
    * Success: If all of the following conditions are met:
        - All specified peers are found in the BFD configuration within the specified VRF.
        - All BFD peers are correctly configured with the `routing protocol`.
    * Failure: If any of the following occur:
        - A specified peer is not found in the BFD configuration within the specified VRF.
        - Any BFD peer not correctly configured with the `routing protocol`.

    Examples
    --------
    ```yaml
    anta.tests.bfd:
      - VerifyBFDPeersRegProtocols:
          bfd_peers:
            - peer_address: 192.0.255.7
              vrf: default
              protocols:
                - bgp
    ```
    """

    categories: ClassVar[list[str]] = ["bfd"]
    commands: ClassVar[list[AntaCommand | AntaTemplate]] = [AntaCommand(command="show bfd peers detail", revision=1)]

    class Input(AntaTest.Input):
        """Input model for the VerifyBFDPeersRegProtocols test."""

        bfd_peers: list[BFDPeer]
        """List of IPv4 BFD"""
        BFDPeer: ClassVar[type[BFDPeer]] = BFDPeer

    @AntaTest.anta_test
    def test(self) -> None:
        """Main test function for VerifyBFDPeersRegProtocols."""
        self.result.is_success()

        # Iterating over BFD peers, extract the parameters and command output
        for bfd_peer in self.inputs.bfd_peers:
            peer = str(bfd_peer.peer_address)
            vrf = bfd_peer.vrf
            protocols = bfd_peer.protocols
            bfd_output = get_value(
                self.instance_commands[0].json_output,
                f"vrfs..{vrf}..ipv4Neighbors..{peer}..peerStats..",
                separator="..",
            )

            # Check if BFD peer configured
            if not bfd_output:
                self.result.is_failure(f"{bfd_peer} - Not found")
                continue

            # Check registered protocols
            difference = set(protocols) - set(get_value(bfd_output, "peerStatsDetail.apps"))
            if difference:
                self.result.is_failure(f"{bfd_peer} - `{','.join(difference)}` routing protocols not configured")
