# Copyright (c) 2023-2024 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Module related to the CVX tests."""

# Mypy does not understand AntaTest.Input typing
# mypy: disable-error-code=attr-defined
from __future__ import annotations

from typing import TYPE_CHECKING, ClassVar, Literal

from anta.models import AntaCommand, AntaTest

if TYPE_CHECKING:
    from anta.models import AntaTemplate
from anta.input_models.cvx import CVXPeers
from anta.tools import get_value


class VerifyMcsClientMounts(AntaTest):
    """Verify if all MCS client mounts are in mountStateMountComplete.

    Expected Results
    ----------------
    * Success: The test will pass if the MCS mount status on MCS Clients are mountStateMountComplete.
    * Failure: The test will fail even if one switch's MCS client mount status is not  mountStateMountComplete.

    Examples
    --------
    ```yaml
    anta.tests.cvx:
    - VerifyMcsClientMounts:
    ```
    """

    categories: ClassVar[list[str]] = ["cvx"]
    commands: ClassVar[list[AntaCommand | AntaTemplate]] = [AntaCommand(command="show management cvx mounts", revision=1)]

    @AntaTest.anta_test
    def test(self) -> None:
        """Main test function for VerifyMcsClientMounts."""
        command_output = self.instance_commands[0].json_output
        self.result.is_success()
        mount_states = command_output["mountStates"]
        mcs_mount_state_detected = False
        for mount_state in mount_states:
            if not mount_state["type"].startswith("Mcs"):
                continue
            mcs_mount_state_detected = True
            if (state := mount_state["state"]) != "mountStateMountComplete":
                self.result.is_failure(f"MCS Client mount states are not valid: {state}")

        if not mcs_mount_state_detected:
            self.result.is_failure("MCS Client mount states are not present")


class VerifyManagementCVX(AntaTest):
    """Verifies the management CVX global status.

    Expected Results
    ----------------
    * Success: The test will pass if the management CVX global status matches the expected status.
    * Failure: The test will fail if the management CVX global status does not match the expected status.


    Examples
    --------
    ```yaml
    anta.tests.cvx:
      - VerifyManagementCVX:
          enabled: true
    ```
    """

    categories: ClassVar[list[str]] = ["cvx"]
    commands: ClassVar[list[AntaCommand | AntaTemplate]] = [AntaCommand(command="show management cvx", revision=1)]

    class Input(AntaTest.Input):
        """Input model for the VerifyManagementCVX test."""

        enabled: bool
        """Whether management CVX must be enabled (True) or disabled (False)."""

    @AntaTest.anta_test
    def test(self) -> None:
        """Main test function for VerifyManagementCVX."""
        command_output = self.instance_commands[0].json_output
        self.result.is_success()
        cluster_status = command_output["clusterStatus"]
        if (cluster_state := cluster_status.get("enabled")) != self.inputs.enabled:
            self.result.is_failure(f"Management CVX status is not valid: {cluster_state}")


class VerifyCVXClusterStatus(AntaTest):
    """Verifies the CVX Server Cluster status.

    Expected Results
    ----------------
    * Success: The test will pass if all of the following conditions is met:
        - CVX Enabled state is true
        - Cluster Mode is true
        - Role is either Master or Standby.
        - peer_status matches defined state
    * Failure: The test will fail if any of the success conditions is not met.

    Examples
    --------
    ```yaml
    anta.tests.cvx:
      - VerifyCVXClusterStatus:
          role: Master
          peer_status:
            - peer_name : cvx-red-2
              registration_state: Registration complete
            - peer_name: cvx-red-3
              registration_state: Registration error
    ```
    """

    categories: ClassVar[list[str]] = ["cvx"]
    commands: ClassVar[list[AntaCommand | AntaTemplate]] = [AntaCommand(command="show cvx", revision=1)]

    class Input(AntaTest.Input):
        """Input model for the VerifyCVXClusterStatus test."""

        role: Literal["Master", "Standby", "Disconnected"] = "Master"
        peer_status: list[CVXPeers]

    @AntaTest.anta_test
    def test(self) -> None:
        """Run the main test for VerifyCVXClusterStatus."""
        command_output = self.instance_commands[0].json_output
        self.result.is_success()

        # Validate Server enabled status
        if not command_output.get("enabled"):
            self.result.is_failure("CVX Server status is not enabled")

        # Validate cluster status and mode
        if not (cluster_status := command_output.get("clusterStatus")) or not command_output.get("clusterMode"):
            self.result.is_failure("CVX Server is not a cluster")
            return

        # Check cluster role
        if (cluster_role := cluster_status.get("role")) != self.inputs.role:
            self.result.is_failure(f"CVX Role is not valid: {cluster_role}")
            return

        # Validate peer status
        peer_cluster = cluster_status.get("peerStatus", {})

        # Check peer count
        if (num_of_peers := len(peer_cluster)) != (expected_num_of_peers := len(self.inputs.peer_status)):
            self.result.is_failure(f"Unexpected number of peers {num_of_peers} vs {expected_num_of_peers}")

        # Check each peer
        for peer in self.inputs.peer_status:
            # Retrieve the peer status from the peer cluster
            if (eos_peer_status := get_value(peer_cluster, peer.peer_name, separator="..")) is None:
                self.result.is_failure(f"{peer.peer_name} is not present")
                continue

            # Validate the registration state of the peer
            if (peer_reg_state := eos_peer_status.get("registrationState")) != peer.registration_state:
                self.result.is_failure(f"{peer.peer_name} registration state is not complete: {peer_reg_state}")
