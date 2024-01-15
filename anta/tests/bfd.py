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

from anta.models import AntaCommand, AntaTest


class VerifyBFDPeersHealth(AntaTest):
    """
    Verifies there is no IPv4 BFD peer in the down state, remote disc is not zero and last down should be above the threshold for all VRF.
    Expected results:
        * success: The test will pass if IPv4 BFD peers are not down, remote disc is not zero and last down above the defined threshold for all VRF.
        * failure: The test will fail if IPv4 BFD peers are down, remote disc is zero and last down below the defined threshold for all VRF.
    """

    name = "VerifyBFDPeersHealth"
    description = "Verifies there is no IPv4 BFD peer in the down state, remote disc is not zero and last down should be above the threshold for all VRF."
    categories = ["bfd"]

    # revision 1 as later revision introduces additional nesting for type
    commands = [AntaCommand(command="show bfd peers", revision=1), AntaCommand(command="show clock")]

    class Input(AntaTest.Input):
        """
        This class defines the input parameters of the testcase.
        """

        last_down: Optional[int] = None
        """Optional last down threshold in hours"""

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

        # Iterate over IPv4 BFD peers
        for vrf, vrf_data in bfd_output["vrfs"].items():
            for peer, neighbor_data in vrf_data["ipv4Neighbors"].items():
                for peer_data in neighbor_data["peerStats"].values():
                    peer_status = peer_data["status"]
                    remote_disc = peer_data["remoteDisc"]
                    peer_l3intf = peer_data.get("l3intf", "")
                    l3intf_info = f" with peer layer3 interface {peer_l3intf}" if peer_l3intf else ""
                    remote_disc_info = f" with remote disc {remote_disc}" if remote_disc == 0 else ""
                    remote_disc_info = f" and remote disc {remote_disc}" if remote_disc == 0 and peer_l3intf else remote_disc_info
                    last_down = peer_data["lastDown"]
                    hours_difference = (datetime.fromtimestamp(current_timestamp) - datetime.fromtimestamp(last_down)).total_seconds() / 3600
                    # Check if peer status is not up
                    if peer_status != "up":
                        down_failures.append(f"{peer} is {peer_status} in {vrf} VRF{l3intf_info}{remote_disc_info}.")
                    # Check if the last down is within the threshold
                    elif self.inputs.last_down and hours_difference > self.inputs.last_down:
                        up_failures.append(f"{peer} in {vrf} VRF was down {round(hours_difference)} hours ago{l3intf_info}{remote_disc_info}.")
                    # Check if remote disc is 0
                    elif remote_disc == 0:
                        up_failures.append(f"{peer} in {vrf} VRF has remote disc {remote_disc}{l3intf_info}.")

        # Check if there are any failures
        if down_failures:
            down_failures_str = "\n".join(down_failures)
            self.result.is_failure(f"Following BFD peers are not up:\n{down_failures_str}")
        if up_failures:
            up_failures_str = "\n".join(up_failures)
            self.result.is_failure(f"\nFollowing BFD peers were down:\n{up_failures_str}")
