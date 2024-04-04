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
    * Success: The test will pass if the AVT path is active, valid, and matches the specified type (direct/multihop) for the given VRF.
    * Failure: The test will fail if the AVT path is not configured or if the AVT path is not active, valid, or does not match the specified type for the given VRF.

    Examples
    --------
    ```yaml
    anta.tests.avt:
      - VerifyAVTSpecificPath:
          avt_paths:
            - avt_name: CONTROL-PLANE-PROFILE
              destination: 10.101.255.2
              next_hop: 10.101.255.1
              direct_path: False
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
            direct_path: bool = True
            """The type of the AVT path. True indicates a direct path and False indicates a multihop path."""

    def render(self, template: AntaTemplate) -> list[AntaCommand]:
        """Render the template for each input AVT path/peer."""
        return [
            template.render(vrf=path.vrf, avt_name=path.avt_name, destination=path.destination, next_hop=path.next_hop, direct_path=path.direct_path)
            for path in self.inputs.avt_paths
        ]

    @AntaTest.anta_test
    def test(self) -> None:
        """Main test function for VerifyAVTSpecificPath."""
        # Assume the test is successful until a failure is detected
        self.result.is_success()

        # Process each command in the instance
        for command in self.instance_commands:
            # Extract the command output and parameters
            command_output = command.json_output.get("vrfs", {})
            vrf, avt_name, peer, nexthop, direct_path = map(command.params.get, ["vrf", "avt_name", "destination", "next_hop", "direct_path"])
            peer, nexthop = map(str, [peer, nexthop])

            # If no AVT is configured, mark the test as failed and skip to the next command
            if not command_output:
                self.result.is_failure(f"No AVT configuration found for peer {peer} under topology {avt_name} in VRF {vrf}.")
                continue

            # Extract the AVT paths
            avt_paths = get_value(command_output, f"{vrf}.avts.{avt_name}.avtPaths")
            nexthop_path_found = False

            # Check each AVT path
            for path, path_data in avt_paths.items():
                # Extract the path status and type

                # If the path does not match the expected next hop, skip to the next path
                if path_data.get("nexthopAddr") != nexthop:
                    continue
                valid = get_value(path_data, "flags.valid")
                active = get_value(path_data, "flags.active")
                actual_path = get_value(path_data, "flags.directPath")
                path_type = f"{'direct' if actual_path else 'multihop'}"
                nexthop_path_found = True
                # Construct the failure message prefix
                failed_log = f"AVT path {path} for topology {avt_name} in VRF {vrf}"

                # Check the path status and type against the expected values
                path_match = actual_path == direct_path
                if not all([valid, active, path_match]):
                    failure_reasons = []
                    if not active:
                        failure_reasons.append("inactive")
                    if not valid:
                        failure_reasons.append("invalid")
                    if not path_match:
                        failure_reasons.append(path_type)
                    self.result.is_failure(f"{failed_log} is {', '.join(failure_reasons)}.")

            # If no matching next hop was found, mark the test as failed
            if not nexthop_path_found:
                self.result.is_failure(f"No path found with next-hop address {nexthop} for AVT peer {peer} under topology {avt_name} in VRF {vrf}.")


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


class VerifyAVTPathReachability(AntaTest):
    """
    Verifies the reachability of Adaptive Virtual Topology (AVT) paths.

    Expected Results
    ----------------
    * Success: The test will pass if the AVT path is reachable with 0% packet loss.
    * Failure: The test will fail if the AVT path is not configured or there is packet loss to the destination IP for the given VRF.

    Examples
    --------
    ```yaml
    anta.tests.avt:
      - VerifyAVTPathReachability:
          avt_paths:
            - avt_name: DEFAULT-AVT-POLICY-DEFAULT
              dst_ip: 10.255.0.1
              vrf: default
    ```
    """

    name = "VerifyAVTPathReachability"
    description = "Verifies the Adaptive Virtual Topology (AVT) path reachability."
    categories: ClassVar[list[str]] = ["avt"]
    commands: ClassVar[list[AntaCommand | AntaTemplate]] = [AntaTemplate(template="ping adaptive-virtual-topology vrf {vrf} avt {avt_name} destination {dst_ip}")]

    class Input(AntaTest.Input):
        """Input model for the VerifyAVTPathReachability test."""

        avt_paths: list[AVTPaths]
        """List of AVT paths to verify."""

        class AVTPaths(BaseModel):
            """Model representing the details of AVT paths."""

            avt_name: str
            """Name of the adaptive virtual topology."""
            vrf: str = "default"
            """The VRF for the AVT path. Defaults to 'default' if not provided."""
            dst_ip: IPv4Address
            """The destination IPv4 address."""

    def render(self, template: AntaTemplate) -> list[AntaCommand]:
        """Render the template for each input AVT path/peer."""
        return [template.render(vrf=path.vrf, avt_name=path.avt_name, dst_ip=path.dst_ip) for path in self.inputs.avt_paths]

    @AntaTest.anta_test
    def test(self) -> None:
        """Main test function for VerifyAVTPathReachability."""
        # Initialize the test result as success
        self.result.is_success()

        # Iterate over the commands and get the output
        for command in self.instance_commands:
            command_output = command.json_output

            dst_ip = str(command.params["dst_ip"])
            vrf = command.params["vrf"]

            # Check for any error messages
            if command_output.get("errorMessage"):
                self.result.is_failure(command_output.get("errorMessage"))
                return

            # Check for packet loss in the summary
            for path, loss_rate in command_output["summary"].items():
                if loss_rate["lossRate"] != 0:
                    self.result.is_failure(f"For destination `{dst_ip}` and path `{path}` in vrf {vrf}, packet loss was found: `{loss_rate['lossRate']}%`")
                    return
