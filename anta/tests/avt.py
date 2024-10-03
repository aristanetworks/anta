# Copyright (c) 2023-2024 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Module related to Adaptive virtual topology tests."""

# Mypy does not understand AntaTest.Input typing
# mypy: disable-error-code=attr-defined
from __future__ import annotations

from ipaddress import IPv4Address
from typing import ClassVar

from pydantic import BaseModel

from anta.decorators import skip_on_platforms
from anta.models import AntaCommand, AntaTemplate, AntaTest
from anta.tools import get_value


class VerifyAVTPathHealth(AntaTest):
    """
    Verifies the status of all Adaptive Virtual Topology (AVT) paths for all VRFs.

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

    name = "VerifyAVTPathHealth"
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
            self.result.is_failure("Adaptive virtual topology paths are not configured.")
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
                        self.result.is_failure(f"AVT path {path} for profile {profile} in VRF {vrf} is invalid and not active.")
                    elif not valid:
                        self.result.is_failure(f"AVT path {path} for profile {profile} in VRF {vrf} is invalid.")
                    elif not active:
                        self.result.is_failure(f"AVT path {path} for profile {profile} in VRF {vrf} is not active.")


class VerifyAVTSpecificPath(AntaTest):
    """
    Verifies the status and type of an Adaptive Virtual Topology (AVT) path for a specified VRF.

    Expected Results
    ----------------
    * Success: The test will pass if all AVT paths for the specified VRF are active, valid, and match the specified type (direct/multihop) if provided.
               If multiple paths are configured, the test will pass only if all the paths are valid and active.
    * Failure: The test will fail if no AVT paths are configured for the specified VRF, or if any configured path is not active, valid,
               or does not match the specified type.

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

    name = "VerifyAVTSpecificPath"
    description = "Verifies the status and type of an AVT path for a specified VRF."
    categories: ClassVar[list[str]] = ["avt"]
    commands: ClassVar[list[AntaCommand | AntaTemplate]] = [
        AntaTemplate(template="show adaptive-virtual-topology path vrf {vrf} avt {avt_name} destination {destination}")
    ]

    class Input(AntaTest.Input):
        """Input model for the VerifyAVTSpecificPath test."""

        avt_paths: list[AVTPaths]
        """List of AVT paths to verify."""

        class AVTPaths(BaseModel):
            """Model for the details of AVT paths."""

            vrf: str = "default"
            """The VRF for the AVT path. Defaults to 'default' if not provided."""
            avt_name: str
            """Name of the adaptive virtual topology."""
            destination: IPv4Address
            """The IPv4 address of the AVT peer."""
            next_hop: IPv4Address
            """The IPv4 address of the next hop for the AVT peer."""
            path_type: str | None = None
            """The type of the AVT path. If not provided, both 'direct' and 'multihop' paths are considered."""

    def render(self, template: AntaTemplate) -> list[AntaCommand]:
        """Render the template for each input AVT path/peer."""
        return [template.render(vrf=path.vrf, avt_name=path.avt_name, destination=path.destination) for path in self.inputs.avt_paths]

    @skip_on_platforms(["cEOSLab", "vEOS-lab"])
    @AntaTest.anta_test
    def test(self) -> None:
        """Main test function for VerifyAVTSpecificPath."""
        # Assume the test is successful until a failure is detected
        self.result.is_success()

        # Process each command in the instance
        for command, input_avt in zip(self.instance_commands, self.inputs.avt_paths):
            # Extract the command output and parameters
            vrf = command.params.vrf
            avt_name = command.params.avt_name
            peer = str(command.params.destination)

            command_output = command.json_output.get("vrfs", {})

            # If no AVT is configured, mark the test as failed and skip to the next command
            if not command_output:
                self.result.is_failure(f"AVT configuration for peer '{peer}' under topology '{avt_name}' in VRF '{vrf}' is not found.")
                continue

            # Extract the AVT paths
            avt_paths = get_value(command_output, f"{vrf}.avts.{avt_name}.avtPaths")
            next_hop, input_path_type = str(input_avt.next_hop), input_avt.path_type

            nexthop_path_found = path_type_found = False

            # Check each AVT path
            for path, path_data in avt_paths.items():
                # If the path does not match the expected next hop, skip to the next path
                if path_data.get("nexthopAddr") != next_hop:
                    continue

                nexthop_path_found = True
                path_type = "direct" if get_value(path_data, "flags.directPath") else "multihop"

                # If the path type does not match the expected path type, skip to the next path
                if input_path_type and path_type != input_path_type:
                    continue

                path_type_found = True
                valid = get_value(path_data, "flags.valid")
                active = get_value(path_data, "flags.active")

                # Check the path status and type against the expected values
                if not all([valid, active]):
                    failure_reasons = []
                    if not get_value(path_data, "flags.active"):
                        failure_reasons.append("inactive")
                    if not get_value(path_data, "flags.valid"):
                        failure_reasons.append("invalid")
                    # Construct the failure message prefix
                    failed_log = f"AVT path '{path}' for topology '{avt_name}' in VRF '{vrf}'"
                    self.result.is_failure(f"{failed_log} is {', '.join(failure_reasons)}.")

            # If no matching next hop or path type was found, mark the test as failed
            if not nexthop_path_found or not path_type_found:
                self.result.is_failure(
                    f"No '{input_path_type}' path found with next-hop address '{next_hop}' for AVT peer '{peer}' under topology '{avt_name}' in VRF '{vrf}'."
                )


class VerifyAVTRole(AntaTest):
    """
    Verifies the Adaptive Virtual Topology (AVT) role of a device.

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

    name = "VerifyAVTRole"
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
            self.result.is_failure(f"Expected AVT role as `{self.inputs.role}`, but found `{command_output.get('role')}` instead.")
