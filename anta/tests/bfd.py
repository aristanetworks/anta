# Copyright (c) 2023-2025 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Module related to BFD tests."""

# Mypy does not understand AntaTest.Input typing
# mypy: disable-error-code=attr-defined
from __future__ import annotations

from datetime import datetime, timezone
from ipaddress import IPv4Address
from typing import TYPE_CHECKING, ClassVar, TypeVar

from pydantic import Field, field_validator

from anta.input_models.bfd import BFDPeer
from anta.models import AntaCommand, AntaTest
from anta.tools import get_value

if TYPE_CHECKING:
    from anta.models import AntaTemplate

# Using a TypeVar for the BFDPeer model since mypy thinks it's a ClassVar and not a valid type when used in field validators
T = TypeVar("T", bound=BFDPeer)


# TODO: Add IPv6 example
# TODO: Add a note about no support for SBFD
class VerifyBFDSpecificPeers(AntaTest):
    """Verifies the state of BFD peer sessions.

    Expected Results
    ----------------
    * Success: The test will pass if all specified BFD peers are `up` and the remote discriminators (disc) are non-zero.
    * Failure: The test will fail if any specified BFD peer is not found, not `up` or the remote disc is zero.

    Examples
    --------
    ```yaml
    anta.tests.bfd:
      - VerifyBFDSpecificPeers:
          bfd_peers:
            # Multi-hop session in VRF default
            - peer_address: 192.0.255.8
            # Multi-hop session in VRF DEV
            - peer_address: 192.0.255.7
              vrf: DEV
            # Single-hop session on local egress interface Ethernet3 in VRF PROD
            - peer_address: 192.168.10.2
              vrf: PROD
              l3_interface: Ethernet3
    ```
    """

    categories: ClassVar[list[str]] = ["bfd"]
    commands: ClassVar[list[AntaCommand | AntaTemplate]] = [AntaCommand(command="show bfd peers", revision=1)]
    inputs: VerifyBFDSpecificPeers.Input

    class Input(AntaTest.Input):
        """Input model for the VerifyBFDSpecificPeers test."""

        bfd_peers: list[BFDPeer]
        """List of BFD peers."""
        BFDPeer: ClassVar[type[BFDPeer]] = BFDPeer
        """To maintain backward compatibility."""

    @AntaTest.anta_test
    def test(self) -> None:
        """Main test function for VerifyBFDSpecificPeers."""
        self.result.is_success()

        for bfd_peer in self.inputs.bfd_peers:
            af = "ipv4Neighbors" if isinstance(bfd_peer.peer_address, IPv4Address) else "ipv6Neighbors"
            intf = "" if bfd_peer.interface is None else bfd_peer.interface
            peer_data = get_value(self.instance_commands[0].json_output, f"vrfs..{bfd_peer.vrf}..{af}..{bfd_peer.peer_address!s}..peerStats..{intf}", separator="..")

            # Check if BFD peer is found
            if not peer_data:
                self.result.is_failure(f"{bfd_peer} - Not found")
                continue

            # Check BFD peer status and remote disc
            state = peer_data.get("status")
            remote_disc = peer_data.get("remoteDisc")
            if not (state == "up" and remote_disc != 0):
                self.result.is_failure(f"{bfd_peer} - Session not properly established - State: {state} Remote Discriminator: {remote_disc}")


# TODO: Update docstring
# TODO: Add a note about no support for SBFD
class VerifyBFDPeersIntervals(AntaTest):
    """Verifies the timers of BFD peer sessions.

    This test performs the following checks for each specified peer:

      1. Confirms that the specified VRF is configured.
      2. Verifies that the peer exists in the BFD configuration.
      3. Confirms that BFD peer is correctly configured with the `Transmit interval, Receive interval and Multiplier`.
      4. Verifies that BFD peer is correctly configured with the `Detection time`, if provided.

    Expected Results
    ----------------
    * Success: If all of the following conditions are met:
        - All specified peers are found in the BFD configuration within the specified VRF.
        - All BFD peers are correctly configured with the `Transmit interval, Receive interval and Multiplier`.
        - If provided, the `Detection time` is correctly configured.
    * Failure: If any of the following occur:
        - A specified peer is not found in the BFD configuration within the specified VRF.
        - Any BFD peer not correctly configured with the `Transmit interval, Receive interval and Multiplier`.
        - Any BFD peer is not correctly configured with `Detection time`, if provided.

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
              detection_time: 3600
    ```
    """

    categories: ClassVar[list[str]] = ["bfd"]
    commands: ClassVar[list[AntaCommand | AntaTemplate]] = [AntaCommand(command="show bfd peers detail", revision=1)]
    inputs: VerifyBFDPeersIntervals.Input

    class Input(AntaTest.Input):
        """Input model for the VerifyBFDPeersIntervals test."""

        bfd_peers: list[BFDPeer]
        """List of BFD peers."""
        BFDPeer: ClassVar[type[BFDPeer]] = BFDPeer
        """To maintain backward compatibility"""

        @field_validator("bfd_peers")
        @classmethod
        def validate_bfd_peers(cls, bfd_peers: list[T]) -> list[T]:
            """Validate that 'tx_interval', 'rx_interval' and 'multiplier' fields are provided in each BFD peer."""
            for peer in bfd_peers:
                missing_fileds = []
                if peer.tx_interval is None:
                    missing_fileds.append("tx_interval")
                if peer.rx_interval is None:
                    missing_fileds.append("rx_interval")
                if peer.multiplier is None:
                    missing_fileds.append("multiplier")
                if missing_fileds:
                    msg = f"{peer} {', '.join(missing_fileds)} field(s) are missing in the input"
                    raise ValueError(msg)
            return bfd_peers

    @AntaTest.anta_test
    def test(self) -> None:
        """Main test function for VerifyBFDPeersIntervals."""
        self.result.is_success()

        for bfd_peer in self.inputs.bfd_peers:
            af = "ipv4Neighbors" if isinstance(bfd_peer.peer_address, IPv4Address) else "ipv6Neighbors"
            intf = "" if bfd_peer.interface is None else bfd_peer.interface
            peer_data = get_value(self.instance_commands[0].json_output, f"vrfs..{bfd_peer.vrf}..{af}..{bfd_peer.peer_address!s}..peerStats..{intf}", separator="..")

            # Check if BFD peer is found
            if not peer_data:
                self.result.is_failure(f"{bfd_peer} - Not found")
                continue

            # Convert interval timers into milliseconds to be consistent with the inputs
            act_tx_interval = get_value(peer_data, "peerStatsDetail.operTxInterval") // 1000
            act_rx_interval = get_value(peer_data, "peerStatsDetail.operRxInterval") // 1000
            act_detect_time = get_value(peer_data, "peerStatsDetail.detectTime") // 1000
            act_detect_mult = get_value(peer_data, "peerStatsDetail.detectMult")

            if act_tx_interval != bfd_peer.tx_interval:
                self.result.is_failure(f"{bfd_peer} - Incorrect Transmit interval - Expected: {bfd_peer.tx_interval} Actual: {act_tx_interval}")

            if act_rx_interval != bfd_peer.rx_interval:
                self.result.is_failure(f"{bfd_peer} - Incorrect Receive interval - Expected: {bfd_peer.rx_interval} Actual: {act_rx_interval}")

            if act_detect_mult != bfd_peer.multiplier:
                self.result.is_failure(f"{bfd_peer} - Incorrect Multiplier - Expected: {bfd_peer.multiplier} Actual: {act_detect_mult}")

            if bfd_peer.detection_time and act_detect_time != bfd_peer.detection_time:
                self.result.is_failure(f"{bfd_peer} - Incorrect Detection Time - Expected: {bfd_peer.detection_time} Actual: {act_detect_time}")


class VerifyBFDPeersHealth(AntaTest):
    """Verifies the health of IPv4 BFD peers across all VRFs.

    This test performs the following checks for BFD peers across all VRFs:

      1. Validates that the state is `up`.
      2. Confirms that the remote discriminator identifier (disc) is non-zero.
      3. Optionally verifies that the peer have not been down before a specified threshold of hours.

    Expected Results
    ----------------
    * Success: If all of the following conditions are met:
        - All BFD peers across the VRFs are up and remote disc is non-zero.
        - Last downtime of each peer is above the defined threshold, if specified.
    * Failure: If any of the following occur:
        - Any BFD peer session is not up or the remote discriminator identifier is zero.
        - Last downtime of any peer is below the defined threshold, if specified.

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
        self.result.is_success()

        # Extract the current timestamp and command output
        clock_output = self.instance_commands[1].json_output
        current_timestamp = clock_output["utcTime"]
        bfd_output = self.instance_commands[0].json_output

        # Check if any IPv4 BFD peer is configured
        ipv4_neighbors_exist = any(vrf_data["ipv4Neighbors"] for vrf_data in bfd_output["vrfs"].values())
        if not ipv4_neighbors_exist:
            self.result.is_failure("No IPv4 BFD peers are configured for any VRF")
            return

        # Iterate over IPv4 BFD peers
        for vrf, vrf_data in bfd_output["vrfs"].items():
            for peer, neighbor_data in vrf_data["ipv4Neighbors"].items():
                for peer_data in neighbor_data["peerStats"].values():
                    peer_status = peer_data["status"]
                    remote_disc = peer_data["remoteDisc"]
                    last_down = peer_data["lastDown"]
                    hours_difference = (
                        datetime.fromtimestamp(current_timestamp, tz=timezone.utc) - datetime.fromtimestamp(last_down, tz=timezone.utc)
                    ).total_seconds() / 3600

                    if not (peer_status == "up" and remote_disc != 0):
                        self.result.is_failure(
                            f"Peer: {peer} VRF: {vrf} - Session not properly established - State: {peer_status} Remote Discriminator: {remote_disc}"
                        )

                    # Check if the last down is within the threshold
                    if self.inputs.down_threshold and hours_difference < self.inputs.down_threshold:
                        self.result.is_failure(
                            f"Peer: {peer} VRF: {vrf} - Session failure detected within the expected uptime threshold ({round(hours_difference)} hours ago)"
                        )


# TODO: Update docstring
# TODO: Add a note about no support for SBFD
class VerifyBFDPeersRegProtocols(AntaTest):
    """Verifies the registered routing protocol of IPv4 BFD peer sessions.

    This test performs the following checks for each specified peer:

      1. Confirms that the specified VRF is configured.
      2. Verifies that the peer exists in the BFD configuration.
      3. Confirms that BFD peer is correctly configured with the `routing protocol`.

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
    inputs: VerifyBFDPeersRegProtocols.Input

    class Input(AntaTest.Input):
        """Input model for the VerifyBFDPeersRegProtocols test."""

        bfd_peers: list[BFDPeer]
        """List of BFD peers."""
        BFDPeer: ClassVar[type[BFDPeer]] = BFDPeer
        """To maintain backward compatibility"""

        @field_validator("bfd_peers")
        @classmethod
        def validate_bfd_peers(cls, bfd_peers: list[T]) -> list[T]:
            """Validate that 'protocols' field is provided in each BFD peer."""
            for peer in bfd_peers:
                if peer.protocols is None:
                    msg = f"{peer} 'protocols' field missing in the input"
                    raise ValueError(msg)
            return bfd_peers

    @AntaTest.anta_test
    def test(self) -> None:
        """Main test function for VerifyBFDPeersRegProtocols."""
        self.result.is_success()

        for bfd_peer in self.inputs.bfd_peers:
            af = "ipv4Neighbors" if isinstance(bfd_peer.peer_address, IPv4Address) else "ipv6Neighbors"
            intf = "" if bfd_peer.interface is None else bfd_peer.interface
            peer_data = get_value(self.instance_commands[0].json_output, f"vrfs..{bfd_peer.vrf}..{af}..{bfd_peer.peer_address!s}..peerStats..{intf}", separator="..")

            # Check if BFD peer is found
            if not peer_data:
                self.result.is_failure(f"{bfd_peer} - Not found")
                continue

            # Check registered protocols
            difference = sorted(set(bfd_peer.protocols) - set(get_value(peer_data, "peerStatsDetail.apps", default=[])))
            if difference:
                self.result.is_failure(f"{bfd_peer} - {', '.join(difference)} protocol{'s' if len(difference) > 1 else ''} not registered")
