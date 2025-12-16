# Copyright (c) 2023-2025 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Module related to IS-IS tests."""

# Pyright does not understand AntaTest.Input typing
# pyright: reportAttributeAccessIssue=false
from __future__ import annotations

from typing import Any, ClassVar

from pydantic import field_validator

from anta.input_models.routing.isis import Entry, InterfaceCount, InterfaceState, ISISInstance, IsisInstance, ISISInterface, Tunnel, TunnelPath
from anta.models import AntaCommand, AntaTemplate, AntaTest
from anta.tools import get_item, get_value


class VerifyISISNeighborState(AntaTest):
    """Verifies the health of IS-IS neighbors.

    Expected Results
    ----------------
    * Success: The test will pass if all IS-IS neighbors are in the `up` state.
    * Failure: The test will fail if any IS-IS neighbor adjacency is down.
    * Skipped: The test will be skipped if IS-IS is not configured or no IS-IS neighbor is found.

    Examples
    --------
    ```yaml
    anta.tests.routing:
      isis:
        - VerifyISISNeighborState:
            check_all_vrfs: true
    ```
    """

    categories: ClassVar[list[str]] = ["isis"]
    commands: ClassVar[list[AntaCommand | AntaTemplate]] = [AntaCommand(command="show isis neighbors vrf all", revision=1)]

    class Input(AntaTest.Input):
        """Input model for the VerifyISISNeighborState test."""

        check_all_vrfs: bool = False
        """If enabled, verifies IS-IS instances of all VRFs."""

    @AntaTest.anta_test
    def test(self) -> None:
        """Main test function for VerifyISISNeighborState."""
        self.result.is_success()

        # Verify if IS-IS is configured
        if not (command_output := self.instance_commands[0].json_output["vrfs"]):
            self.result.is_skipped("IS-IS not configured")
            return

        vrfs_to_check = command_output
        if not self.inputs.check_all_vrfs:
            vrfs_to_check = {"default": command_output["default"]}

        no_neighbor = True
        for vrf, vrf_data in vrfs_to_check.items():
            for isis_instance, instance_data in vrf_data["isisInstances"].items():
                neighbors = instance_data["neighbors"]
                if not neighbors:
                    continue
                no_neighbor = False
                interfaces = [(adj["interfaceName"], adj["state"]) for neighbor in neighbors.values() for adj in neighbor["adjacencies"] if adj["state"] != "up"]
                for interface in interfaces:
                    self.result.is_failure(
                        f"Instance: {isis_instance} VRF: {vrf} Interface: {interface[0]} - Incorrect adjacency state - Expected: up Actual: {interface[1]}"
                    )

        if no_neighbor:
            self.result.is_skipped("No IS-IS neighbor detected")


class VerifyISISNeighborCount(AntaTest):
    """Verifies the number of IS-IS neighbors per interface and level.

    Expected Results
    ----------------
    * Success: The test will pass if all provided IS-IS interfaces have the expected number of neighbors.
    * Failure: The test will fail if any of the provided IS-IS interfaces are not configured or have an incorrect number of neighbors.
    * Skipped: The test will be skipped if IS-IS is not configured.

    Examples
    --------
    ```yaml
    anta.tests.routing:
      isis:
        - VerifyISISNeighborCount:
            interfaces:
              - name: Ethernet1
                level: 1
                count: 2
              - name: Ethernet2
                level: 2
                count: 1
              - name: Ethernet3
                count: 2
    ```
    """

    categories: ClassVar[list[str]] = ["isis"]
    commands: ClassVar[list[AntaCommand | AntaTemplate]] = [AntaCommand(command="show isis interface brief vrf all", revision=1)]

    class Input(AntaTest.Input):
        """Input model for the VerifyISISNeighborCount test."""

        interfaces: list[ISISInterface]
        """List of IS-IS interfaces with their information."""
        InterfaceCount: ClassVar[type[InterfaceCount]] = InterfaceCount

    @AntaTest.anta_test
    def test(self) -> None:
        """Main test function for VerifyISISNeighborCount."""
        self.result.is_success()

        # Verify if IS-IS is configured
        if not (command_output := self.instance_commands[0].json_output["vrfs"]):
            self.result.is_skipped("IS-IS not configured")
            return

        for interface in self.inputs.interfaces:
            interface_detail = {}
            vrf_instances = get_value(command_output, f"{interface.vrf}..isisInstances", default={}, separator="..")
            for instance_data in vrf_instances.values():
                if interface_data := get_value(instance_data, f"interfaces..{interface.name}..intfLevels..{interface.level}", separator=".."):
                    interface_detail = interface_data
                    # An interface can only be configured in one IS-IS instance at a time
                    break

            if not interface_detail:
                self.result.is_failure(f"{interface} - Not configured")
                continue

            if interface_detail["passive"] is False and (act_count := interface_detail["numAdjacencies"]) != interface.count:
                self.result.is_failure(f"{interface} - Neighbor count mismatch - Expected: {interface.count} Actual: {act_count}")


class VerifyISISInterfaceMode(AntaTest):
    """Verifies IS-IS interfaces are running in the correct mode.

    Expected Results
    ----------------
    * Success: The test will pass if all provided IS-IS interfaces are running in the correct mode.
    * Failure: The test will fail if any of the provided IS-IS interfaces are not configured or running in the incorrect mode.
    * Skipped: The test will be skipped if IS-IS is not configured.

    Examples
    --------
    ```yaml
    anta.tests.routing:
      isis:
        - VerifyISISInterfaceMode:
            interfaces:
              - name: Loopback0
                mode: passive
              - name: Ethernet2
                mode: passive
                level: 2
              - name: Ethernet1
                mode: point-to-point
                vrf: PROD
    ```
    """

    categories: ClassVar[list[str]] = ["isis"]
    commands: ClassVar[list[AntaCommand | AntaTemplate]] = [AntaCommand(command="show isis interface brief vrf all", revision=1)]

    class Input(AntaTest.Input):
        """Input model for the VerifyISISInterfaceMode test."""

        interfaces: list[ISISInterface]
        """List of IS-IS interfaces with their information."""
        InterfaceState: ClassVar[type[InterfaceState]] = InterfaceState

    @AntaTest.anta_test
    def test(self) -> None:
        """Main test function for VerifyISISInterfaceMode."""
        self.result.is_success()

        # Verify if IS-IS is configured
        if not (command_output := self.instance_commands[0].json_output["vrfs"]):
            self.result.is_skipped("IS-IS not configured")
            return

        for interface in self.inputs.interfaces:
            interface_detail = {}
            vrf_instances = get_value(command_output, f"{interface.vrf}..isisInstances", default={}, separator="..")
            for instance_data in vrf_instances.values():
                if interface_data := get_value(instance_data, f"interfaces..{interface.name}", separator=".."):
                    interface_detail = interface_data
                    # An interface can only be configured in one IS-IS instance at a time
                    break

            if not interface_detail:
                self.result.is_failure(f"{interface} - Not configured")
                continue

            # Check for passive
            if interface.mode == "passive":
                if get_value(interface_detail, f"intfLevels.{interface.level}.passive", default=False) is False:
                    self.result.is_failure(f"{interface} - Not running in passive mode")

            # Check for point-to-point or broadcast
            elif interface.mode != (interface_type := get_value(interface_detail, "interfaceType", default="unset")):
                self.result.is_failure(f"{interface} - Incorrect interface mode - Expected: {interface.mode} Actual: {interface_type}")


class VerifyISISSegmentRoutingAdjacencySegments(AntaTest):
    """Verifies IS-IS segment routing adjacency segments.

    !!! warning "IS-IS SR Limitation"
        As of EOS 4.33.1F, IS-IS SR is supported only in the default VRF.
        Please refer to the IS-IS Segment Routing [documentation](https://www.arista.com/en/support/toi/eos-4-17-0f/13789-isis-segment-routing)
        for more information.

    Expected Results
    ----------------
    * Success: The test will pass if all provided IS-IS instances have the correct adjacency segments.
    * Failure: The test will fail if any of the provided IS-IS instances have no adjacency segments or incorrect segments.
    * Skipped: The test will be skipped if IS-IS is not configured.

    Examples
    --------
    ```yaml
    anta.tests.routing:
      isis:
        - VerifyISISSegmentRoutingAdjacencySegments:
            instances:
              - name: CORE-ISIS
                vrf: default
                segments:
                  - interface: Ethernet2
                    address: 10.0.1.3
                    sid_origin: dynamic
    ```
    """

    categories: ClassVar[list[str]] = ["isis", "segment-routing"]
    commands: ClassVar[list[AntaCommand | AntaTemplate]] = [AntaCommand(command="show isis segment-routing adjacency-segments", ofmt="json")]

    class Input(AntaTest.Input):
        """Input model for the VerifyISISSegmentRoutingAdjacencySegments test."""

        instances: list[ISISInstance]
        """List of IS-IS instances with their information."""
        IsisInstance: ClassVar[type[IsisInstance]] = IsisInstance

        @field_validator("instances")
        @classmethod
        def validate_instances(cls, instances: list[ISISInstance]) -> list[ISISInstance]:
            """Validate that 'vrf' field is 'default' in each IS-IS instance."""
            for instance in instances:
                if instance.vrf != "default":
                    msg = f"{instance} 'vrf' field must be 'default'"
                    raise ValueError(msg)
            return instances

    @AntaTest.anta_test
    def test(self) -> None:
        """Main test function for VerifyISISSegmentRoutingAdjacencySegments."""
        self.result.is_success()

        # Verify if IS-IS is configured
        if not (command_output := self.instance_commands[0].json_output["vrfs"]):
            self.result.is_skipped("IS-IS not configured")
            return

        for instance in self.inputs.instances:
            if not (act_segments := get_value(command_output, f"{instance.vrf}..isisInstances..{instance.name}..adjacencySegments", default=[], separator="..")):
                self.result.is_failure(f"{instance} - No adjacency segments found")
                continue

            for segment in instance.segments:
                if (act_segment := get_item(act_segments, "ipAddress", str(segment.address))) is None:
                    self.result.is_failure(f"{instance} {segment} - Adjacency segment not found")
                    continue

                # Check SID origin
                if (act_origin := act_segment["sidOrigin"]) != segment.sid_origin:
                    self.result.is_failure(f"{instance} {segment} - Incorrect SID origin - Expected: {segment.sid_origin} Actual: {act_origin}")

                # Check IS-IS level
                if (actual_level := act_segment["level"]) != segment.level:
                    self.result.is_failure(f"{instance} {segment} - Incorrect IS-IS level - Expected: {segment.level} Actual: {actual_level}")


class VerifyISISSegmentRoutingDataplane(AntaTest):
    """Verifies IS-IS segment routing data-plane configuration.

    !!! warning "IS-IS SR Limitation"
        As of EOS 4.33.1F, IS-IS SR is supported only in the default VRF.
        Please refer to the IS-IS Segment Routing [documentation](https://www.arista.com/en/support/toi/eos-4-17-0f/13789-isis-segment-routing)
        for more information.

    Expected Results
    ----------------
    * Success: The test will pass if all provided IS-IS instances have the correct data-plane configured.
    * Failure: The test will fail if any of the provided IS-IS instances have an incorrect data-plane configured.
    * Skipped: The test will be skipped if IS-IS is not configured.

    Examples
    --------
    ```yaml
    anta.tests.routing:
      isis:
        - VerifyISISSegmentRoutingDataplane:
            instances:
              - name: CORE-ISIS
                vrf: default
                dataplane: MPLS
    ```
    """

    categories: ClassVar[list[str]] = ["isis", "segment-routing"]
    commands: ClassVar[list[AntaCommand | AntaTemplate]] = [AntaCommand(command="show isis segment-routing", ofmt="json")]

    class Input(AntaTest.Input):
        """Input model for the VerifyISISSegmentRoutingDataplane test."""

        instances: list[ISISInstance]
        """List of IS-IS instances with their information."""
        IsisInstance: ClassVar[type[IsisInstance]] = IsisInstance

        @field_validator("instances")
        @classmethod
        def validate_instances(cls, instances: list[ISISInstance]) -> list[ISISInstance]:
            """Validate that 'vrf' field is 'default' in each IS-IS instance."""
            for instance in instances:
                if instance.vrf != "default":
                    msg = f"{instance} 'vrf' field must be 'default'"
                    raise ValueError(msg)
            return instances

    @AntaTest.anta_test
    def test(self) -> None:
        """Main test function for VerifyISISSegmentRoutingDataplane."""
        self.result.is_success()

        # Verify if IS-IS is configured
        if not (command_output := self.instance_commands[0].json_output["vrfs"]):
            self.result.is_skipped("IS-IS not configured")
            return

        for instance in self.inputs.instances:
            if not (instance_data := get_value(command_output, f"{instance.vrf}..isisInstances..{instance.name}", separator="..")):
                self.result.is_failure(f"{instance} - Not configured")
                continue

            if instance.dataplane.upper() != (dataplane := instance_data["dataPlane"]):
                self.result.is_failure(f"{instance} - Data-plane not correctly configured - Expected: {instance.dataplane.upper()} Actual: {dataplane}")


class VerifyISISSegmentRoutingTunnels(AntaTest):
    """Verify ISIS-SR tunnels computed by device.

    Expected Results
    ----------------
    * Success: The test will pass if all listed tunnels are computed on device.
    * Failure: The test will fail if one of the listed tunnels is missing.
    * Skipped: The test will be skipped if ISIS-SR is not configured.

    Examples
    --------
    ```yaml
    anta.tests.routing:
      isis:
        - VerifyISISSegmentRoutingTunnels:
            entries:
              # Check only endpoint
              - endpoint: 1.0.0.122/32
              # Check endpoint and via TI-LFA
              - endpoint: 1.0.0.13/32
                vias:
                  - type: tunnel
                    tunnel_id: ti-lfa
              # Check endpoint and via IP routers
              - endpoint: 1.0.0.14/32
                vias:
                  - type: ip
                    nexthop: 1.1.1.1
    ```
    """

    categories: ClassVar[list[str]] = ["isis", "segment-routing"]
    commands: ClassVar[list[AntaCommand | AntaTemplate]] = [AntaCommand(command="show isis segment-routing tunnel", ofmt="json")]

    class Input(AntaTest.Input):
        """Input model for the VerifyISISSegmentRoutingTunnels test."""

        entries: list[Tunnel]
        """List of tunnels to check on device."""
        Entry: ClassVar[type[Entry]] = Entry

    @AntaTest.anta_test
    def test(self) -> None:
        """Main test function for VerifyISISSegmentRoutingTunnels.

        This method performs the main test logic for verifying ISIS Segment Routing tunnels.
        It checks the command output, initiates defaults, and performs various checks on the tunnels.
        """
        self.result.is_success()

        command_output = self.instance_commands[0].json_output
        if len(command_output["entries"]) == 0:
            self.result.is_skipped("IS-IS-SR not configured")
            return

        for input_entry in self.inputs.entries:
            entries = list(command_output["entries"].values())
            if (eos_entry := get_item(entries, "endpoint", str(input_entry.endpoint))) is None:
                self.result.is_failure(f"{input_entry} - Tunnel not found")
                continue

            if input_entry.vias is not None:
                for via_input in input_entry.vias:
                    via_search_result = any(self._via_matches(via_input, eos_via) for eos_via in eos_entry["vias"])
                    if not via_search_result:
                        self.result.is_failure(f"{input_entry} {via_input} - Tunnel is incorrect")

    def _via_matches(self, via_input: TunnelPath, eos_via: dict[str, Any]) -> bool:
        """Check if the via input matches the eos via.

        Parameters
        ----------
        via_input : TunnelPath
            The input via to check.
        eos_via : dict[str, Any]
            The EOS via to compare against.

        Returns
        -------
        bool
            True if the via input matches the eos via, False otherwise.
        """
        return (
            (via_input.type is None or via_input.type == eos_via.get("type"))
            and (via_input.nexthop is None or str(via_input.nexthop) == eos_via.get("nexthop"))
            and (via_input.interface is None or via_input.interface == eos_via.get("interface"))
            and (via_input.tunnel_id is None or via_input.tunnel_id.upper() == get_value(eos_via, "tunnelId.type", default="").upper())
        )


class VerifyISISGracefulRestart(AntaTest):
    """Verifies the IS-IS graceful restart feature.

    This test performs the following checks for each IS-IS instance:

      1. Verifies that the specified IS-IS instance is configured on the device.
      2. Verifies the statuses of the graceful restart and graceful restart helper functionalities.

    Expected Results
    ----------------
    * Success: The test will pass if all of the following conditions are met:
        - The specified IS-IS instance is configured on the device.
        - Expected and actual IS-IS graceful restart and graceful restart helper values match.
    * Failure: The test will fail if any of the following conditions is met:
        - The specified IS-IS instance is not configured on the device.
        - Expected and actual IS-IS graceful restart and graceful restart helper values do not match.
    * Skipped: The test will skip if IS-IS is not configured on the device.

    Examples
    --------
    ```yaml
    anta.tests.routing:
      isis:
        - VerifyISISGracefulRestart:
            instances:
              - name: '1'
                vrf: default
                graceful_restart: True
                graceful_restart_helper: False
              - name: '2'
                vrf: default
              - name: '11'
                vrf: test
                graceful_restart: True
              - name: '12'
                vrf: test
                graceful_restart_helper: False
    ```
    """

    categories: ClassVar[list[str]] = ["isis"]
    commands: ClassVar[list[AntaCommand | AntaTemplate]] = [AntaCommand(command="show isis graceful-restart vrf all", revision=1)]

    class Input(AntaTest.Input):
        """Input model for the VerifyISISGracefulRestart test."""

        instances: list[ISISInstance]
        """List of IS-IS instance entries."""

    @AntaTest.anta_test
    def test(self) -> None:
        """Main test function for VerifyISISGracefulRestart."""
        self.result.is_success()

        # Verify if IS-IS is configured
        if not (command_output := self.instance_commands[0].json_output["vrfs"]):
            self.result.is_skipped("IS-IS not configured")
            return

        # If IS-IS instance is not found or GR and GR helpers are not matching with the expected values, test fails.
        for instance in self.inputs.instances:
            graceful_restart = "enabled" if instance.graceful_restart else "disabled"
            graceful_restart_helper = "enabled" if instance.graceful_restart_helper else "disabled"

            if (instance_details := get_value(command_output, f"{instance.vrf}..isisInstances..{instance.name}", separator="..")) is None:
                self.result.is_failure(f"{instance} - Not configured")
                continue

            if (act_state := instance_details.get("gracefulRestart")) != graceful_restart:
                self.result.is_failure(f"{instance} - Incorrect graceful restart state - Expected: {graceful_restart} Actual: {act_state}")

            if (act_helper_state := instance_details.get("gracefulRestartHelper")) != graceful_restart_helper:
                self.result.is_failure(f"{instance} - Incorrect graceful restart helper state - Expected: {graceful_restart_helper} Actual: {act_helper_state}")
