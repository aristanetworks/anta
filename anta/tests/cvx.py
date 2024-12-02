# Copyright (c) 2023-2024 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Module related to the CVX tests."""

# Mypy does not understand AntaTest.Input typing
# mypy: disable-error-code=attr-defined
from __future__ import annotations

from typing import TYPE_CHECKING, Any, ClassVar, Literal

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
    * Success: The test will pass if the CVX Server Cluster is enabled.
    * Failure: The test will fail if any of the following conditions are met:
        - If the CVX Status is disabled
        - If the peers are not in the expected state

    Examples
    --------
    ```yaml
    anta.tests.cvx:
      - VerifyCVXClusterStatus:
          enabled: true
          cluster_mode: true
          role: Master
          peer_status:
            - peer_name : cvx-red-2
              registration_state: Registration complete
            - peer_name: cvx-red-3
              registration_state: Registration complete
    ```
    """

    name = "VerifyCVXClusterStatus"
    description = "Verifies the CVX Cluster Status."
    categories: ClassVar[list[str]] = ["cvx"]
    commands: ClassVar[list[AntaCommand | AntaTemplate]] = [AntaCommand(command="show cvx", revision=1)]

    class Input(AntaTest.Input):
        """Input model for the VerifyCVXClusterStatus test."""

        enabled: bool
        """Whether management CVX must be enabled (True) or disabled (False)."""
        cluster_mode: bool
        role: Literal["Master", "Standby", "Disconnected"] = "Master"
        peer_status: list[CVXPeers]

    @AntaTest.anta_test
    def test(self) -> None:
        """Run the main test for VerifyCVXClusterStatus."""
        command_output = self.instance_commands[0].json_output
        self.result.is_success()

        # Validate cluster status
        if not self._validate_cluster_status(command_output):
            return

        # Validate cluster mode and enabled status
        if not self._validate_cluster_mode_and_enabled(command_output):
            return

        # Validate peer status
       self._validate_peer_status(command_output.get("clusterStatus"))

    def _validate_cluster_status(self, command_output: dict[str, Any]) -> bool:
        """Check if the cluster status is available."""
        cluster_status = command_output.get("clusterStatus")
        if not cluster_status:
            self.result.is_failure("CVX Server is not a cluster")
            return False
        return True

    def _validate_cluster_mode_and_enabled(self, command_output: dict[str, Any]) -> bool:
        """Check if the cluster mode and enabled status are correct."""
        if not command_output.get("enabled"):
            self.result.is_failure("CVX Server status is not enabled")
            return False

        cluster_status = command_output.get("clusterStatus")
        if not (command_output.get("clusterMode") and cluster_status):
            self.result.is_failure("CVX Server is not a cluster")
            return False

        # Check cluster role
        if (cluster_role := cluster_status.get("role")) != self.inputs.role:
            self.result.is_failure(f"CVX Role is not valid: {cluster_role}")
            return False

        return True

    def _validate_peer_status(self, cluster_status: dict[str, Any] | None) -> bool:
        """Check peer statuses in the cluster."""
        if cluster_status is None:
            self.result.is_failure("Cluster status is missing")
            return False

        peer_cluster = cluster_status.get("peerStatus", {})

        # Check peer count
        if len(peer_cluster) != len(self.inputs.peer_status):
            self.result.is_failure("Unexpected number of peers")

        # Check each peer
        return all(self._validate_individual_peer(peer, peer_cluster) for peer in self.inputs.peer_status)

    def _validate_individual_peer(self, peer: CVXPeers, peer_cluster: dict[str, Any]) -> bool:
        """Check an individual peer in the cluster."""
        # Retrieve the peer status from the peer cluster
        eos_peer_status = get_value(peer_cluster, peer.peer_name, separator="..")
        if eos_peer_status is None:
            self.result.is_failure(f"{peer.peer_name} is not present")
            return False

        # Validate the registration state of the peer
        peer_reg_state = eos_peer_status.get("registrationState")
        if peer_reg_state != peer.registration_state:
            self.result.is_failure(f"{peer.peer_name} registration state is not complete: {peer_reg_state}")
            return False

        return True
