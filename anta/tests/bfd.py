# Copyright (c) 2023-2025 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Module related to BFD tests."""

# Pyright does not understand AntaTest.Input typing
# pyright: reportAttributeAccessIssue=false
from __future__ import annotations

from datetime import datetime, timezone
from ipaddress import IPv4Address
from typing import TYPE_CHECKING, Any, ClassVar, TypeVar

from pydantic import Field, field_validator

from anta.input_models.bfd import BFDPeer
from anta.models import AntaCommand, AntaTest
from anta.tools import get_value

if TYPE_CHECKING:
    from anta.models import AntaTemplate

T = TypeVar("T", bound=BFDPeer)


def _get_bfd_peer_stats(peer: BFDPeer, command_output: dict[str, Any]) -> dict[str, Any] | None:
    """Retrieve BFD peer stats for the given peer from the command output.

    Parameters
    ----------
    peer
        The BFDPeer object to look up.
    command_output
        Parsed output of the command.

    Returns
    -------
    dict | None
        The peer stats dictionary if found, otherwise None.
    """
    af = "ipv4Neighbors" if isinstance(peer.peer_address, IPv4Address) else "ipv6Neighbors"
    intf = "" if peer.interface is None else peer.interface
    return get_value(command_output, f"vrfs..{peer.vrf}..{af}..{peer.peer_address!s}..peerStats..{intf}", separator="..")


class VerifyBFDSpecificPeers(AntaTest):
    """Verifies the state of BFD peer sessions.

    !!! warning
        Seamless BFD (S-BFD) is **not** supported.

    Expected Results
    ----------------
    * Success: The test will pass if all specified BFD peers are `up` and remote discriminators (disc) are non-zero.
    * Failure: The test will fail if any specified BFD peer is not found, not `up` or remote disc is zero.

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
            # Single-hop session on local transport interface Ethernet3 in VRF PROD
            - peer_address: 192.168.10.2
              vrf: PROD
              interface: Ethernet3
            # IPv6 peers also supported
            - peer_address: fd00:dc:1::1
    ```
    """

    categories: ClassVar[list[str]] = ["bfd"]
    # Using revision 1 as latest revision introduces additional nesting for type
    commands: ClassVar[list[AntaCommand | AntaTemplate]] = [AntaCommand(command="show bfd peers", revision=1)]

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

        output = self.instance_commands[0].json_output

        for bfd_peer in self.inputs.bfd_peers:
            # Check if BFD peer is found
            if (peer_stats := _get_bfd_peer_stats(bfd_peer, output)) is None:
                self.result.is_failure(f"{bfd_peer} - Not found")
                continue

            # Check BFD peer status and remote disc
            state = peer_stats["status"]
            remote_disc = peer_stats["remoteDisc"]
            if not (state == "up" and remote_disc != 0):
                self.result.is_failure(f"{bfd_peer} - Session not properly established - State: {state} Remote Discriminator: {remote_disc}")


class VerifyBFDPeersIntervals(AntaTest):
    """Verifies the operational timers of BFD peer sessions.

    !!! warning
        Seamless BFD (S-BFD) is **not** supported.

    Expected Results
    ----------------
    * Success: The test will pass if all specified BFD peer sessions are operating with the proper timers.
    * Failure: The test will fail if any specified BFD peer session is not found or not operating with the proper timers.


    Examples
    --------
    ```yaml
    anta.tests.bfd:
      - VerifyBFDPeersIntervals:
          bfd_peers:
            # Multi-hop session in VRF default
            - peer_address: 192.0.255.8
              tx_interval: 3600
              rx_interval: 3600
              multiplier: 3
            # Multi-hop session in VRF DEV
            - peer_address: 192.0.255.7
              vrf: DEV
              tx_interval: 3600
              rx_interval: 3600
              multiplier: 3
            # Single-hop session on local transport interface Ethernet3 in VRF PROD
            - peer_address: 192.168.10.2
              vrf: PROD
              interface: Ethernet3
              tx_interval: 1200
              rx_interval: 1200
              multiplier: 3
              detection_time: 3600  # Optional
            # IPv6 peers also supported
            - peer_address: fd00:dc:1::1
              tx_interval: 1200
              rx_interval: 1200
              multiplier: 3
              detection_time: 3600  # Optional
    ```
    """

    categories: ClassVar[list[str]] = ["bfd"]
    # Using revision 1 as latest revision introduces additional nesting for type
    commands: ClassVar[list[AntaCommand | AntaTemplate]] = [AntaCommand(command="show bfd peers detail", revision=1)]

    class Input(AntaTest.Input):
        """Input model for the VerifyBFDPeersIntervals test."""

        bfd_peers: list[BFDPeer]
        """List of BFD peers."""
        BFDPeer: ClassVar[type[BFDPeer]] = BFDPeer
        """To maintain backward compatibility."""

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

        output = self.instance_commands[0].json_output

        for bfd_peer in self.inputs.bfd_peers:
            # Check if BFD peer is found
            if (peer_stats := _get_bfd_peer_stats(bfd_peer, output)) is None:
                self.result.is_failure(f"{bfd_peer} - Not found")
                continue

            # Convert interval timers into milliseconds to be consistent with the inputs
            act_tx_interval = get_value(peer_stats, "peerStatsDetail.operTxInterval") // 1000
            act_rx_interval = get_value(peer_stats, "peerStatsDetail.operRxInterval") // 1000
            act_detect_time = get_value(peer_stats, "peerStatsDetail.detectTime") // 1000
            act_detect_mult = get_value(peer_stats, "peerStatsDetail.detectMult")

            if act_tx_interval != bfd_peer.tx_interval:
                self.result.is_failure(f"{bfd_peer} - Incorrect Transmit interval - Expected: {bfd_peer.tx_interval} Actual: {act_tx_interval}")

            if act_rx_interval != bfd_peer.rx_interval:
                self.result.is_failure(f"{bfd_peer} - Incorrect Receive interval - Expected: {bfd_peer.rx_interval} Actual: {act_rx_interval}")

            if act_detect_mult != bfd_peer.multiplier:
                self.result.is_failure(f"{bfd_peer} - Incorrect Multiplier - Expected: {bfd_peer.multiplier} Actual: {act_detect_mult}")

            if bfd_peer.detection_time and act_detect_time != bfd_peer.detection_time:
                self.result.is_failure(f"{bfd_peer} - Incorrect Detection Time - Expected: {bfd_peer.detection_time} Actual: {act_detect_time}")


class VerifyBFDPeersHealth(AntaTest):
    """Verifies the health of BFD peers across all VRFs.

    !!! warning
        Seamless BFD (S-BFD) is **not** supported.

    Expected Results
    ----------------
    * Success: The test will pass if all BFD peers are `up`, remote discriminators (disc) are non-zero
                and last downtime is above `down_threshold` (if provided).
    * Failure: The test will fail if any BFD peer is not `up`, remote disc is zero or last downtime is below `down_threshold` (if provided).

    Examples
    --------
    ```yaml
    anta.tests.bfd:
      - VerifyBFDPeersHealth:
          down_threshold: 2
    ```
    """

    categories: ClassVar[list[str]] = ["bfd"]
    # Using revision 1 as latest revision introduces additional nesting for type
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

        # Check if any IPv4 or IPv6 BFD peer is configured
        if not any(vrf_data["ipv4Neighbors"] | vrf_data["ipv6Neighbors"] for vrf_data in bfd_output["vrfs"].values()):
            self.result.is_failure("No IPv4 or IPv6 BFD peers configured for any VRF")
            return

        for vrf, vrf_data in bfd_output["vrfs"].items():
            # Merging the IPv4 and IPv6 peers into a single dict
            all_peers = vrf_data["ipv4Neighbors"] | vrf_data["ipv6Neighbors"]
            for peer_ip, peer_data in all_peers.items():
                for interface, peer_stats in peer_data["peerStats"].items():
                    identifier = f"Peer: {peer_ip} VRF: {vrf} Interface: {interface}" if interface else f"Peer: {peer_ip} VRF: {vrf}"
                    peer_status = peer_stats["status"]
                    remote_disc = peer_stats["remoteDisc"]

                    if not (peer_status == "up" and remote_disc != 0):
                        self.result.is_failure(f"{identifier} - Session not properly established - State: {peer_status} Remote Discriminator: {remote_disc}")

                    # Check if the last down is within the threshold
                    if self.inputs.down_threshold is not None:
                        last_down = peer_stats["lastDown"]
                        hours_difference = (
                            datetime.fromtimestamp(current_timestamp, tz=timezone.utc) - datetime.fromtimestamp(last_down, tz=timezone.utc)
                        ).total_seconds() / 3600
                        if hours_difference < self.inputs.down_threshold:
                            self.result.is_failure(
                                f"{identifier} - Session failure detected within the expected uptime threshold ({round(hours_difference)} hours ago)"
                            )


class VerifyBFDPeersRegProtocols(AntaTest):
    """Verifies the registered protocols of BFD peer sessions.

    !!! warning
        Seamless BFD (S-BFD) is **not** supported.

    Expected Results
    ----------------
    * Success: The test will pass if all specified BFD peers have the proper registered protocols.
    * Failure: The test will fail if any specified BFD peer is not found or doesn't have the proper registered protocols.

    Examples
    --------
    ```yaml
    anta.tests.bfd:
      - VerifyBFDPeersRegProtocols:
          bfd_peers:
            # Multi-hop session in VRF default
            - peer_address: 192.0.255.8
              protocols: [ bgp ]
            # Multi-hop session in VRF DEV
            - peer_address: 192.0.255.7
              vrf: DEV
              protocols: [ bgp, vxlan ]
            # Single-hop session on local transport interface Ethernet3 in VRF PROD
            - peer_address: 192.168.10.2
              vrf: PROD
              interface: Ethernet3
              protocols: [ ospf ]
              detection_time: 3600  # Optional
            # IPv6 peers also supported
            - peer_address: fd00:dc:1::1
              protocols: [ isis ]
    ```
    """

    categories: ClassVar[list[str]] = ["bfd"]
    # Using revision 1 as latest revision introduces additional nesting for type
    commands: ClassVar[list[AntaCommand | AntaTemplate]] = [AntaCommand(command="show bfd peers detail", revision=1)]

    class Input(AntaTest.Input):
        """Input model for the VerifyBFDPeersRegProtocols test."""

        bfd_peers: list[BFDPeer]
        """List of BFD peers."""
        BFDPeer: ClassVar[type[BFDPeer]] = BFDPeer
        """To maintain backward compatibility."""

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

        output = self.instance_commands[0].json_output

        for bfd_peer in self.inputs.bfd_peers:
            # Check if BFD peer is found
            if (peer_stats := _get_bfd_peer_stats(bfd_peer, output)) is None:
                self.result.is_failure(f"{bfd_peer} - Not found")
                continue

            # Check registered protocols
            difference = sorted(set(bfd_peer.protocols) - set(get_value(peer_stats, "peerStatsDetail.apps", default=[])))
            if difference:
                self.result.is_failure(f"{bfd_peer} - {', '.join(difference)} protocol{'s' if len(difference) > 1 else ''} not registered")
