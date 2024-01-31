# Copyright (c) 2023-2024 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""
BFD test functions
"""
# Mypy does not understand AntaTest.Input typing
# mypy: disable-error-code=attr-defined
from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import Field

from anta.models import AntaCommand, AntaTest


class VerifyBFDPeersHealth(AntaTest):
    """
    This class verifies the health of IPv4 BFD peers across all VRFs.
    It checks that no BFD peer is in the down state and that the discriminator value of the remote system is not zero.

    Optionally, it can also verify that BFD peers have not been down before a specified threshold of hours.

    Expected results:
        * Success: The test will pass if all IPv4 BFD peers are up, the discriminator value of each remote system is non-zero,
                   and the last downtime of each peer is above the defined threshold.
        * Failure: The test will fail if any IPv4 BFD peer is down, the discriminator value of any remote system is zero,
                   or the last downtime of any peer is below the defined threshold.
    """

    name = "VerifyBFDPeersHealth"
    description = (
        "Verifies there is no IPv4 BFD peer in the down state and discriminator value of the remote system is not zero for all VRF. "
        "BFD peer last down in hours is optional check which should be above the threshold for all VRF."
    )
    categories = ["bfd"]

    commands = [AntaCommand(command="show bfd peers"), AntaCommand(command="show clock")]

    class Input(AntaTest.Input):
        """
        This class defines the input parameters of the test case.
        """

        down_threshold: Optional[int] = Field(default=None, gt=0)
        """Optional down threshold in hours to check if a BFD peer was down before those hours or not."""

    @AntaTest.anta_test
    def test(self) -> None:
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
                    hours_difference = (datetime.fromtimestamp(current_timestamp) - datetime.fromtimestamp(last_down)).total_seconds() / 3600

                    # Check if peer status is not up
                    if peer_status != "up":
                        down_failures.append(f"{peer} is {peer_status} in {vrf} VRF{remote_disc_info}.")

                    # Check if the last down is within the threshold
                    elif self.inputs.down_threshold and hours_difference > self.inputs.down_threshold:
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
