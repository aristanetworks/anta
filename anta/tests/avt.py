# Copyright (c) 2023-2025 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Module related to Adaptive virtual topology tests."""

# Pyright does not understand AntaTest.Input typing
# pyright: reportAttributeAccessIssue=false
from __future__ import annotations

from typing import ClassVar

from anta.decorators import skip_on_platforms
from anta.input_models.avt import AVTPath
from anta.models import AntaCommand, AntaTemplate, AntaTest
from anta.result_manager.models import AntaTestStatus
from anta.tools import get_value


class VerifyAVTPathHealth(AntaTest):
    """Verifies the status of all Adaptive Virtual Topology (AVT) paths for all VRFs.

    Expected Results
    ----------------
    * Success: The test will pass if all AVT paths for all VRFs are active and valid.
    * Failure: The test will fail if the AVT path is not configured or if any AVT path under any VRF is either inactive or invalid.

    Examples
    --------
    ```yaml
    anta.tests.avt:
      - VerifyAVTPathHealth:
    ```
    """

    description = "Verifies the status of all AVT paths for all VRFs."
    categories: ClassVar[list[str]] = ["avt"]
    commands: ClassVar[list[AntaCommand | AntaTemplate]] = [AntaCommand(command="show adaptive-virtual-topology path")]

    @skip_on_platforms(["cEOSLab", "vEOS-lab"])
    @AntaTest.anta_test
    def test(self) -> None:
        """Main test function for VerifyAVTPathHealth."""
        # Initialize the test result as success
        self.result.is_success()

        # Get the command output
        command_output = self.instance_commands[0].json_output.get("vrfs", {})

        # Check if AVT is configured
        if not command_output:
            self.result.is_failure("Adaptive virtual topology paths are not configured")
            return

        # Iterate over each VRF
        for vrf, vrf_data in command_output.items():
            # Iterate over each AVT path
            for profile, avt_path in vrf_data.get("avts", {}).items():
                for path, flags in avt_path.get("avtPaths", {}).items():
                    # Get the status of the AVT path
                    valid = flags["flags"]["valid"]
                    active = flags["flags"]["active"]

                    # Check the status of the AVT path
                    if not valid and not active:
                        self.result.is_failure(f"VRF: {vrf} Profile: {profile} AVT path: {path} - Invalid and not active")
                    elif not valid:
                        self.result.is_failure(f"VRF: {vrf} Profile: {profile} AVT path: {path} - Invalid")
                    elif not active:
                        self.result.is_failure(f"VRF: {vrf} Profile: {profile} AVT path: {path} - Not active")


class VerifyAVTSpecificPath(AntaTest):
    """Verifies the Adaptive Virtual Topology (AVT) path.

    This test performs the following checks for each specified AVT path:

      1. Confirming that the AVT paths are associated with the specified VRF.
      2. Verifying that each AVT path is active and valid.
      3. Ensuring that the AVT path matches the specified type (direct/multihop) if provided.

    Expected Results
    ----------------
    * Success: The test will pass if all of the following conditions are met:
        - All AVT paths for the specified VRF are active, valid, and match the specified path type (direct/multihop), if provided.
        - If multiple paths are configured, the test will pass only if all paths meet these criteria.
    * Failure: The test will fail if any of the following conditions are met:
        - No AVT paths are configured for the specified VRF.
        - Any configured path is inactive, invalid, or does not match the specified type.

    Examples
    --------
    ```yaml
    anta.tests.avt:
      - VerifyAVTSpecificPath:
          avt_paths:
            - avt_name: CONTROL-PLANE-PROFILE
              vrf: default
              destination: 10.101.255.2
              next_hop: 10.101.255.1
              path_type: direct
    ```
    """

    categories: ClassVar[list[str]] = ["avt"]
    commands: ClassVar[list[AntaCommand | AntaTemplate]] = [AntaCommand(command="show adaptive-virtual-topology path", revision=1)]
    _atomic_support: ClassVar[bool] = True

    class Input(AntaTest.Input):
        """Input model for the VerifyAVTSpecificPath test."""

        avt_paths: list[AVTPath]
        """List of AVT paths to verify."""
        AVTPaths: ClassVar[type[AVTPath]] = AVTPath
        """To maintain backward compatibility."""

    @skip_on_platforms(["cEOSLab", "vEOS-lab"])
    @AntaTest.anta_test
    def test(self) -> None:
        """Main test function for VerifyAVTSpecificPath."""
        # Assume the test is successful until a failure is detected
        self.result.is_success()

        command_output = self.instance_commands[0].json_output
        for avt_path in self.inputs.avt_paths:
            # Atomic result
            result = self.result.add(description=str(avt_path), status=AntaTestStatus.SUCCESS)

            if (path_output := get_value(command_output, f"vrfs.{avt_path.vrf}.avts.{avt_path.avt_name}.avtPaths")) is None:
                result.is_failure("No AVT path configured")
                continue

            path_found = False

            # Check each AVT path
            for path, path_data in path_output.items():
                dest = path_data.get("destination")
                nexthop = path_data.get("nexthopAddr")
                path_type = "direct" if get_value(path_data, "flags.directPath") else "multihop"

                if not avt_path.path_type:
                    path_found = all([dest == str(avt_path.destination), nexthop == str(avt_path.next_hop)])

                elif all([dest == str(avt_path.destination), nexthop == str(avt_path.next_hop), path_type == avt_path.path_type]):
                    path_found = True
                    # Check the path status and type against the expected values
                    valid = get_value(path_data, "flags.valid")
                    active = get_value(path_data, "flags.active")
                    if not all([valid, active]):
                        result.is_failure(f"Incorrect path {path} - Valid: {valid} Active: {active}")

            # If no matching path found, mark the test as failed
            if not path_found:
                result.is_failure("Path not found")


class VerifyAVTRole(AntaTest):
    """Verifies the Adaptive Virtual Topology (AVT) role of a device.

    Expected Results
    ----------------
    * Success: The test will pass if the AVT role of the device matches the expected role.
    * Failure: The test will fail if the AVT is not configured or if the AVT role does not match the expected role.

    Examples
    --------
    ```yaml
    anta.tests.avt:
      - VerifyAVTRole:
          role: edge
    ```
    """

    description = "Verifies the AVT role of a device."
    categories: ClassVar[list[str]] = ["avt"]
    commands: ClassVar[list[AntaCommand | AntaTemplate]] = [AntaCommand(command="show adaptive-virtual-topology path")]

    class Input(AntaTest.Input):
        """Input model for the VerifyAVTRole test."""

        role: str
        """Expected AVT role of the device."""

    @skip_on_platforms(["cEOSLab", "vEOS-lab"])
    @AntaTest.anta_test
    def test(self) -> None:
        """Main test function for VerifyAVTRole."""
        # Initialize the test result as success
        self.result.is_success()

        # Get the command output
        command_output = self.instance_commands[0].json_output

        # Check if the AVT role matches the expected role
        if self.inputs.role != command_output.get("role"):
            self.result.is_failure(f"AVT role mismatch - Expected: {self.inputs.role} Actual: {command_output.get('role')}")
