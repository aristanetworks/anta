# Copyright (c) 2023-2025 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Module related to the CVX tests."""

# Pyright does not understand AntaTest.Input typing
# pyright: reportAttributeAccessIssue=false
from __future__ import annotations

from typing import TYPE_CHECKING, Any, ClassVar, Literal

from anta.custom_types import PositiveInteger
from anta.models import AntaCommand, AntaTest
from anta.tools import get_value

if TYPE_CHECKING:
    from anta.models import AntaTemplate
from anta.input_models.cvx import CVXPeers


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
                self.result.is_failure(f"MCS Client mount states are not valid - Expected: mountStateMountComplete Actual: {state}")

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
    commands: ClassVar[list[AntaCommand | AntaTemplate]] = [AntaCommand(command="show management cvx", revision=3)]

    class Input(AntaTest.Input):
        """Input model for the VerifyManagementCVX test."""

        enabled: bool
        """Whether management CVX must be enabled (True) or disabled (False)."""

    @AntaTest.anta_test
    def test(self) -> None:
        """Main test function for VerifyManagementCVX."""
        command_output = self.instance_commands[0].json_output
        self.result.is_success()
        if (cluster_state := get_value(command_output, "clusterStatus.enabled")) != self.inputs.enabled:
            if cluster_state is None:
                self.result.is_failure("Management CVX status - Not configured")
                return
            cluster_state = "enabled" if cluster_state else "disabled"
            required_state = "enabled" if self.inputs.enabled else "disabled"
            self.result.is_failure(f"Management CVX status is not valid: Expected: {required_state} Actual: {cluster_state}")


class VerifyMcsServerMounts(AntaTest):
    """Verify if all MCS server mounts are in a MountComplete state.

    Expected Results
    ----------------
    * Success: The test will pass if all the MCS mount status on MCS server are mountStateMountComplete.
    * Failure: The test will fail even if any MCS server mount status is not mountStateMountComplete.

    Examples
    --------
    ```yaml
    anta.tests.cvx:

    - VerifyMcsServerMounts:
        connections_count: 100
    ```
    """

    categories: ClassVar[list[str]] = ["cvx"]
    commands: ClassVar[list[AntaCommand | AntaTemplate]] = [AntaCommand(command="show cvx mounts", revision=1)]

    mcs_path_types: ClassVar[list[str]] = ["Mcs::ApiConfigRedundancyStatus", "Mcs::ActiveFlows", "Mcs::Client::Status"]
    """The list of expected MCS path types to verify."""

    class Input(AntaTest.Input):
        """Input model for the VerifyMcsServerMounts test."""

        connections_count: int
        """The expected number of active CVX Connections with mountStateMountComplete"""

    def validate_mount_states(self, mount: dict[str, Any], hostname: str) -> None:
        """Validate the mount states of a given mount."""
        mount_states = mount["mountStates"][0]

        if (num_path_states := len(mount_states["pathStates"])) != (expected_num := len(self.mcs_path_types)):
            self.result.is_failure(f"Host: {hostname} - Incorrect number of mount path states - Expected: {expected_num} Actual: {num_path_states}")

        for path in mount_states["pathStates"]:
            if (path_type := path.get("type")) not in self.mcs_path_types:
                self.result.is_failure(f"Host: {hostname} - Unexpected MCS path type - Expected: {', '.join(self.mcs_path_types)} Actual: {path_type}")
            if (path_state := path.get("state")) != "mountStateMountComplete":
                self.result.is_failure(
                    f"Host: {hostname} Path Type: {path_type} - MCS server mount state is not valid - Expected: mountStateMountComplete Actual:{path_state}"
                )

    @AntaTest.anta_test
    def test(self) -> None:
        """Main test function for VerifyMcsServerMounts."""
        command_output = self.instance_commands[0].json_output
        self.result.is_success()
        active_count = 0

        if not (connections := command_output.get("connections")):
            self.result.is_failure("CVX connections are not available")
            return

        for connection in connections:
            mounts = connection.get("mounts", [])
            hostname = connection["hostname"]

            mcs_mounts = [mount for mount in mounts if mount["service"] == "Mcs"]

            if not mounts:
                self.result.is_failure(f"Host: {hostname} - No mount status found")
                continue

            if not mcs_mounts:
                self.result.is_failure(f"Host: {hostname} - MCS mount state not detected")
            else:
                for mount in mcs_mounts:
                    self.validate_mount_states(mount, hostname)
                    active_count += 1

        if active_count != self.inputs.connections_count:
            self.result.is_failure(f"Incorrect CVX successful connections count - Expected: {self.inputs.connections_count} Actual: {active_count}")


class VerifyActiveCVXConnections(AntaTest):
    """Verifies the number of active CVX Connections.

    Expected Results
    ----------------
    * Success: The test will pass if number of connections is equal to the expected number of connections.
    * Failure: The test will fail otherwise.

    Examples
    --------
    ```yaml
    anta.tests.cvx:
      - VerifyActiveCVXConnections:
          connections_count: 100
    ```
    """

    categories: ClassVar[list[str]] = ["cvx"]
    # TODO: @gmuloc - cover "% Unavailable command (controller not ready)"
    commands: ClassVar[list[AntaCommand | AntaTemplate]] = [AntaCommand(command="show cvx connections brief", revision=1)]

    class Input(AntaTest.Input):
        """Input model for the VerifyActiveCVXConnections test."""

        connections_count: PositiveInteger
        """The expected number of active CVX Connections."""

    @AntaTest.anta_test
    def test(self) -> None:
        """Main test function for VerifyActiveCVXConnections."""
        command_output = self.instance_commands[0].json_output
        self.result.is_success()

        if not (connections := command_output.get("connections")):
            self.result.is_failure("CVX connections are not available")
            return

        active_count = len([connection for connection in connections if connection.get("oobConnectionActive")])

        if self.inputs.connections_count != active_count:
            self.result.is_failure(f"Incorrect CVX active connections count - Expected: {self.inputs.connections_count} Actual: {active_count}")


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
            self.result.is_failure(f"CVX Role is not valid: Expected: {self.inputs.role} Actual: {cluster_role}")
            return

        # Validate peer status
        peer_cluster = cluster_status.get("peerStatus", {})

        # Check peer count
        if (num_of_peers := len(peer_cluster)) != (expected_num_of_peers := len(self.inputs.peer_status)):
            self.result.is_failure(f"Unexpected number of peers - Expected: {expected_num_of_peers} Actual: {num_of_peers}")

        # Check each peer
        for peer in self.inputs.peer_status:
            # Retrieve the peer status from the peer cluster
            if (eos_peer_status := get_value(peer_cluster, peer.peer_name, separator="..")) is None:
                self.result.is_failure(f"{peer.peer_name} - Not present")
                continue

            # Validate the registration state of the peer
            if (peer_reg_state := eos_peer_status.get("registrationState")) != peer.registration_state:
                self.result.is_failure(f"{peer.peer_name} - Invalid registration state - Expected: {peer.registration_state} Actual: {peer_reg_state}")
