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
    * Success: The test will pass if the CVX Server Cluster is enabled.
    * Failure: The test will fail if any of the following conditions are met:
        - If the CVX Status is disabled
        - If the peers are not in "Registration ok" state

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
        CVXPeers: ClassVar[type[CVXPeers]] = CVXPeers

    @AntaTest.anta_test
    def test(self) -> None:
        """Main test function for VerifyCVXClusterStatus."""
        command_output = self.instance_commands[0].json_output
        self.result.is_success()
        cluster_status = command_output.get("clusterStatus")
        if not cluster_status:
            self.result.is_failure("CVX Server is not a cluster")
        else:
            if not command_output["enabled"]:
                self.result.is_failure("CVX Server status is not enabled")
            if not (command_output["clusterMode"] and cluster_status):
                self.result.is_failure("CVX Server is not a cluster")
            if (cluster_state := cluster_status.get("role")) != self.inputs.role:
                self.result.is_failure(f"CVX Role is not valid: {cluster_state}")
            peer_cluster = cluster_status.get("peerStatus")
            for peer in self.inputs.peer_status:
                if (eos_peer_status := get_value(peer_cluster, peer.peer_name, separator="..")) is None:
                    self.result.is_failure(f"{peer.peer_name} is not present")
                    continue
                peer_reg_state = eos_peer_status["registrationState"]
                if peer_reg_state != peer.registration_state:
                    self.result.is_failure(f"{peer.peer_name} registration state is not complete {peer_reg_state}")
