# Copyright (c) 2023-2024 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Module related to the CVX tests."""

# Mypy does not understand AntaTest.Input typing
# mypy: disable-error-code=attr-defined
from __future__ import annotations

from typing import TYPE_CHECKING, ClassVar

from anta.models import AntaCommand, AntaTest

if TYPE_CHECKING:
    from anta.models import AntaTemplate


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
