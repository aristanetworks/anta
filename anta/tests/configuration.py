# Copyright (c) 2023-2024 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Module related to the device configuration tests."""

# Mypy does not understand AntaTest.Input typing
# mypy: disable-error-code=attr-defined
from __future__ import annotations

import re
from typing import TYPE_CHECKING, ClassVar, Literal

from anta.custom_types import RegexString
from anta.input_models.cvx import CVXPeers
from anta.models import AntaCommand, AntaTest

if TYPE_CHECKING:
    from anta.models import AntaTemplate


class VerifyZeroTouch(AntaTest):
    """Verifies ZeroTouch is disabled.

    Expected Results
    ----------------
    * Success: The test will pass if ZeroTouch is disabled.
    * Failure: The test will fail if ZeroTouch is enabled.

    Examples
    --------
    ```yaml
    anta.tests.configuration:
      - VerifyZeroTouch:
    ```
    """

    categories: ClassVar[list[str]] = ["configuration"]
    commands: ClassVar[list[AntaCommand | AntaTemplate]] = [AntaCommand(command="show zerotouch", revision=1)]

    @AntaTest.anta_test
    def test(self) -> None:
        """Main test function for VerifyZeroTouch."""
        command_output = self.instance_commands[0].json_output
        if command_output["mode"] == "disabled":
            self.result.is_success()
        else:
            self.result.is_failure("ZTP is NOT disabled")


class VerifyRunningConfigDiffs(AntaTest):
    """Verifies there is no difference between the running-config and the startup-config.

    Expected Results
    ----------------
    * Success: The test will pass if there is no difference between the running-config and the startup-config.
    * Failure: The test will fail if there is a difference between the running-config and the startup-config.

    Examples
    --------
    ```yaml
    anta.tests.configuration:
      - VerifyRunningConfigDiffs:
    ```
    """

    categories: ClassVar[list[str]] = ["configuration"]
    commands: ClassVar[list[AntaCommand | AntaTemplate]] = [AntaCommand(command="show running-config diffs", ofmt="text")]

    @AntaTest.anta_test
    def test(self) -> None:
        """Main test function for VerifyRunningConfigDiffs."""
        command_output = self.instance_commands[0].text_output
        if command_output == "":
            self.result.is_success()
        else:
            self.result.is_failure(command_output)


class VerifyRunningConfigLines(AntaTest):
    """Verifies the given regular expression patterns are present in the running-config.

    !!! warning
        Since this uses regular expression searches on the whole running-config, it can
        drastically impact performance and should only be used if no other test is available.

        If possible, try using another ANTA test that is more specific.

    Expected Results
    ----------------
    * Success: The test will pass if all the patterns are found in the running-config.
    * Failure: The test will fail if any of the patterns are NOT found in the running-config.

    Examples
    --------
    ```yaml
    anta.tests.configuration:
      - VerifyRunningConfigLines:
            regex_patterns:
                - "^enable password.*$"
                - "bla bla"
    ```
    """

    description = "Search the Running-Config for the given RegEx patterns."
    categories: ClassVar[list[str]] = ["configuration"]
    commands: ClassVar[list[AntaCommand | AntaTemplate]] = [AntaCommand(command="show running-config", ofmt="text")]

    class Input(AntaTest.Input):
        """Input model for the VerifyRunningConfigLines test."""

        regex_patterns: list[RegexString]
        """List of regular expressions."""

    @AntaTest.anta_test
    def test(self) -> None:
        """Main test function for VerifyRunningConfigLines."""
        failure_msgs = []
        command_output = self.instance_commands[0].text_output

        for pattern in self.inputs.regex_patterns:
            re_search = re.compile(pattern, flags=re.MULTILINE)

            if not re_search.search(command_output):
                failure_msgs.append(f"'{pattern}'")

        if not failure_msgs:
            self.result.is_success()
        else:
            self.result.is_failure("Following patterns were not found: " + ",".join(failure_msgs))


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

    name = "VerifyManagementCVX"
    description = "Verifies the management CVX global status."
    categories: ClassVar[list[str]] = ["configuration"]
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
          clusterMode: true
          role: Master
          peerStatus:
            registrationState: Registration ok
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
        cluster_status = command_output["clusterStatus"]
        if not command_output["enabled"]:
            self.result.is_failure("CVX Server status is not enabled")
        if not command_output["clusterMode"]:
            self.result.is_failure("CVX Server is not a cluster")
        if (cluster_state := cluster_status.get("role")) != self.inputs.role:
            self.result.is_failure(f"CVX Role is not valid: {cluster_state}")
