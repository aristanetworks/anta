# Copyright (c) 2023-2024 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Module related to BFD tests."""

# Mypy does not understand AntaTest.Input typing
# mypy: disable-error-code=attr-defined
from __future__ import annotations

from datetime import datetime, timezone
from ipaddress import IPv4Address
from typing import TYPE_CHECKING, Any, ClassVar

from pydantic import BaseModel, Field

from anta.custom_types import BfdInterval, BfdMultiplier, BfdProtocol
from anta.models import AntaCommand, AntaTest
from anta.tools import get_value

if TYPE_CHECKING:
    from anta.models import AntaTemplate


class VerifyBFDSpecificPeers(AntaTest):
    """Verifies if the IPv4 BFD peer's sessions are UP and remote disc is non-zero in the specified VRF.

    Expected Results
    ----------------
    * Success: The test will pass if IPv4 BFD peers are up and remote disc is non-zero in the specified VRF.
    * Failure: The test will fail if IPv4 BFD peers are not found, the status is not UP or remote disc is zero in the specified VRF.

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

    name = "VerifyBFDSpecificPeers"
    description = "Verifies the IPv4 BFD peer's sessions and remote disc in the specified VRF."
    categories: ClassVar[list[str]] = ["bfd"]
    commands: ClassVar[list[AntaCommand | AntaTemplate]] = [AntaCommand(command="show bfd peers", revision=1)]

    class Input(AntaTest.Input):
        """Input model for the VerifyBFDSpecificPeers test."""

        bfd_peers: list[BFDPeer]
        """List of IPv4 BFD peers."""

        class BFDPeer(BaseModel):
            """Model for an IPv4 BFD peer."""

            peer_address: IPv4Address
            """IPv4 address of a BFD peer."""
            vrf: str = "default"
            """Optional VRF for BFD peer. If not provided, it defaults to `default`."""

    @AntaTest.anta_test
    def test(self) -> None:
        """Main test function for VerifyBFDSpecificPeers."""
        failures: dict[Any, Any] = {}

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
                failures[peer] = {vrf: "Not Configured"}
                continue

            # Check BFD peer status and remote disc
            if not (bfd_output.get("status") == "up" and bfd_output.get("remoteDisc") != 0):
                failures[peer] = {
                    vrf: {
                        "status": bfd_output.get("status"),
                        "remote_disc": bfd_output.get("remoteDisc"),
                    }
                }

        if not failures:
            self.result.is_success()
        else:
            self.result.is_failure(f"Following BFD peers are not configured, status is not up or remote disc is zero:\n{failures}")


class VerifyBFDPeersIntervals(AntaTest):
    """Verifies the timers of the IPv4 BFD peers in the specified VRF.

    Expected Results
    ----------------
    * Success: The test will pass if the timers of the IPv4 BFD peers are correct in the specified VRF.
    * Failure: The test will fail if the IPv4 BFD peers are not found or their timers are incorrect in the specified VRF.

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

    name = "VerifyBFDPeersIntervals"
    description = "Verifies the timers of the IPv4 BFD peers in the specified VRF."
    categories: ClassVar[list[str]] = ["bfd"]
    commands: ClassVar[list[AntaCommand | AntaTemplate]] = [AntaCommand(command="show bfd peers detail", revision=1)]

    class Input(AntaTest.Input):
        """Input model for the VerifyBFDPeersIntervals test."""

        bfd_peers: list[BFDPeer]
        """List of BFD peers."""

        class BFDPeer(BaseModel):
            """Model for an IPv4 BFD peer."""

            peer_address: IPv4Address
            """IPv4 address of a BFD peer."""
            vrf: str = "default"
            """Optional VRF for BFD peer. If not provided, it defaults to `default`."""
            tx_interval: BfdInterval
            """Tx interval of BFD peer in milliseconds."""
            rx_interval: BfdInterval
            """Rx interval of BFD peer in milliseconds."""
            multiplier: BfdMultiplier
            """Multiplier of BFD peer."""

    @AntaTest.anta_test
    def test(self) -> None:
        """Main test function for VerifyBFDPeersIntervals."""
        failures: dict[Any, Any] = {}

        # Iterating over BFD peers
        for bfd_peers in self.inputs.bfd_peers:
            peer = str(bfd_peers.peer_address)
            vrf = bfd_peers.vrf
            tx_interval = bfd_peers.tx_interval
            rx_interval = bfd_peers.rx_interval
            multiplier = bfd_peers.multiplier

            # Check if BFD peer configured
            bfd_output = get_value(
                self.instance_commands[0].json_output,
                f"vrfs..{vrf}..ipv4Neighbors..{peer}..peerStats..",
                separator="..",
            )
            if not bfd_output:
                failures[peer] = {vrf: "Not Configured"}
                continue

            # Convert interval timer(s) into milliseconds to be consistent with the inputs.
            bfd_details = bfd_output.get("peerStatsDetail", {})
            op_tx_interval = bfd_details.get("operTxInterval") // 1000
            op_rx_interval = bfd_details.get("operRxInterval") // 1000
            detect_multiplier = bfd_details.get("detectMult")
            intervals_ok = op_tx_interval == tx_interval and op_rx_interval == rx_interval and detect_multiplier == multiplier

            # Check timers of BFD peer
            if not intervals_ok:
                failures[peer] = {
                    vrf: {
                        "tx_interval": op_tx_interval,
                        "rx_interval": op_rx_interval,
                        "multiplier": detect_multiplier,
                    }
                }

        # Check if any failures
        if not failures:
            self.result.is_success()
        else:
            self.result.is_failure(f"Following BFD peers are not configured or timers are not correct:\n{failures}")


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

    name = "VerifyBFDPeersHealth"
    description = "Verifies the health of all IPv4 BFD peers."
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
    """Verifies that IPv4 BFD peer(s) have the specified protocol(s) registered.

    Expected Results
    ----------------
    * Success: The test will pass if IPv4 BFD peers are registered with the specified protocol(s).
    * Failure: The test will fail if IPv4 BFD peers are not found or the specified protocol(s) are not registered for the BFD peer(s).

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

    name = "VerifyBFDPeersRegProtocols"
    description = "Verifies that IPv4 BFD peer(s) have the specified protocol(s) registered."
    categories: ClassVar[list[str]] = ["bfd"]
    commands: ClassVar[list[AntaCommand | AntaTemplate]] = [AntaCommand(command="show bfd peers detail", revision=1)]

    class Input(AntaTest.Input):
        """Input model for the VerifyBFDPeersRegProtocols test."""

        bfd_peers: list[BFDPeer]
        """List of IPv4 BFD peers."""

        class BFDPeer(BaseModel):
            """Model for an IPv4 BFD peer."""

            peer_address: IPv4Address
            """IPv4 address of a BFD peer."""
            vrf: str = "default"
            """Optional VRF for BFD peer. If not provided, it defaults to `default`."""
            protocols: list[BfdProtocol]
            """List of protocols to be verified."""

    @AntaTest.anta_test
    def test(self) -> None:
        """Main test function for VerifyBFDPeersRegProtocols."""
        # Initialize failure messages
        failures: dict[Any, Any] = {}

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
                failures[peer] = {vrf: "Not Configured"}
                continue

            # Check registered protocols
            difference = set(protocols) - set(get_value(bfd_output, "peerStatsDetail.apps"))

            if difference:
                failures[peer] = {vrf: sorted(difference)}

        if not failures:
            self.result.is_success()
        else:
            self.result.is_failure(f"The following BFD peers are not configured or have non-registered protocol(s):\n{failures}")
