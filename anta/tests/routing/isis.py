# Copyright (c) 2023-2025 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Module related to IS-IS tests."""

# Mypy does not understand AntaTest.Input typing
# mypy: disable-error-code=attr-defined
from __future__ import annotations

from ipaddress import IPv4Address, IPv4Network
from typing import Any, ClassVar, Literal

from pydantic import BaseModel, field_validator

from anta.custom_types import Interface
from anta.input_models.routing.isis import InterfaceCount, InterfaceState, ISISInstance, IsisInstance, ISISInterface
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
                interfaces = [adj["interfaceName"] for neighbor in neighbors.values() for adj in neighbor["adjacencies"] if adj["state"] != "up"]
                for interface in interfaces:
                    self.result.is_failure(f"Instance: {isis_instance} VRF: {vrf} Interface: {interface} - Adjacency down")

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

        entries: list[Entry]
        """List of tunnels to check on device."""

        class Entry(BaseModel):
            """Definition of a tunnel entry."""

            endpoint: IPv4Network
            """Endpoint IP of the tunnel."""
            vias: list[Vias] | None = None
            """Optional list of path to reach endpoint."""

            class Vias(BaseModel):
                """Definition of a tunnel path."""

                nexthop: IPv4Address | None = None
                """Nexthop of the tunnel. If None, then it is not tested. Default: None"""
                type: Literal["ip", "tunnel"] | None = None
                """Type of the tunnel. If None, then it is not tested. Default: None"""
                interface: Interface | None = None
                """Interface of the tunnel. If None, then it is not tested. Default: None"""
                tunnel_id: Literal["TI-LFA", "ti-lfa", "unset"] | None = None
                """Computation method of the tunnel. If None, then it is not tested. Default: None"""

    def _eos_entry_lookup(self, search_value: IPv4Network, entries: dict[str, Any], search_key: str = "endpoint") -> dict[str, Any] | None:
        return next(
            (entry_value for entry_id, entry_value in entries.items() if str(entry_value[search_key]) == str(search_value)),
            None,
        )

    @AntaTest.anta_test
    def test(self) -> None:
        """Main test function for VerifyISISSegmentRoutingTunnels.

        This method performs the main test logic for verifying ISIS Segment Routing tunnels.
        It checks the command output, initiates defaults, and performs various checks on the tunnels.
        """
        command_output = self.instance_commands[0].json_output
        self.result.is_success()

        # initiate defaults
        failure_message = []

        if len(command_output["entries"]) == 0:
            self.result.is_skipped("IS-IS-SR is not running on device.")
            return

        for input_entry in self.inputs.entries:
            eos_entry = self._eos_entry_lookup(search_value=input_entry.endpoint, entries=command_output["entries"])
            if eos_entry is None:
                failure_message.append(f"Tunnel to {input_entry} is not found.")
            elif input_entry.vias is not None:
                failure_src = []
                for via_input in input_entry.vias:
                    if not self._check_tunnel_type(via_input, eos_entry):
                        failure_src.append("incorrect tunnel type")
                    if not self._check_tunnel_nexthop(via_input, eos_entry):
                        failure_src.append("incorrect nexthop")
                    if not self._check_tunnel_interface(via_input, eos_entry):
                        failure_src.append("incorrect interface")
                    if not self._check_tunnel_id(via_input, eos_entry):
                        failure_src.append("incorrect tunnel ID")

                if failure_src:
                    failure_message.append(f"Tunnel to {input_entry.endpoint!s} is incorrect: {', '.join(failure_src)}")

        if failure_message:
            self.result.is_failure("\n".join(failure_message))

    def _check_tunnel_type(self, via_input: VerifyISISSegmentRoutingTunnels.Input.Entry.Vias, eos_entry: dict[str, Any]) -> bool:
        """Check if the tunnel type specified in `via_input` matches any of the tunnel types in `eos_entry`.

        Parameters
        ----------
        via_input : VerifyISISSegmentRoutingTunnels.Input.Entry.Vias
            The input tunnel type to check.
        eos_entry : dict[str, Any]
            The EOS entry containing the tunnel types.

        Returns
        -------
        bool
            True if the tunnel type matches any of the tunnel types in `eos_entry`, False otherwise.
        """
        if via_input.type is not None:
            return any(
                via_input.type
                == get_value(
                    dictionary=eos_via,
                    key="type",
                    default="undefined",
                )
                for eos_via in eos_entry["vias"]
            )
        return True

    def _check_tunnel_nexthop(self, via_input: VerifyISISSegmentRoutingTunnels.Input.Entry.Vias, eos_entry: dict[str, Any]) -> bool:
        """Check if the tunnel nexthop matches the given input.

        Parameters
        ----------
        via_input : VerifyISISSegmentRoutingTunnels.Input.Entry.Vias
            The input via object.
        eos_entry : dict[str, Any]
            The EOS entry dictionary.

        Returns
        -------
        bool
            True if the tunnel nexthop matches, False otherwise.
        """
        if via_input.nexthop is not None:
            return any(
                str(via_input.nexthop)
                == get_value(
                    dictionary=eos_via,
                    key="nexthop",
                    default="undefined",
                )
                for eos_via in eos_entry["vias"]
            )
        return True

    def _check_tunnel_interface(self, via_input: VerifyISISSegmentRoutingTunnels.Input.Entry.Vias, eos_entry: dict[str, Any]) -> bool:
        """Check if the tunnel interface exists in the given EOS entry.

        Parameters
        ----------
        via_input : VerifyISISSegmentRoutingTunnels.Input.Entry.Vias
            The input via object.
        eos_entry : dict[str, Any]
            The EOS entry dictionary.

        Returns
        -------
        bool
            True if the tunnel interface exists, False otherwise.
        """
        if via_input.interface is not None:
            return any(
                via_input.interface
                == get_value(
                    dictionary=eos_via,
                    key="interface",
                    default="undefined",
                )
                for eos_via in eos_entry["vias"]
            )
        return True

    def _check_tunnel_id(self, via_input: VerifyISISSegmentRoutingTunnels.Input.Entry.Vias, eos_entry: dict[str, Any]) -> bool:
        """Check if the tunnel ID matches any of the tunnel IDs in the EOS entry's vias.

        Parameters
        ----------
        via_input : VerifyISISSegmentRoutingTunnels.Input.Entry.Vias
            The input vias to check.
        eos_entry : dict[str, Any])
            The EOS entry to compare against.

        Returns
        -------
        bool
            True if the tunnel ID matches any of the tunnel IDs in the EOS entry's vias, False otherwise.
        """
        if via_input.tunnel_id is not None:
            return any(
                via_input.tunnel_id.upper()
                == get_value(
                    dictionary=eos_via,
                    key="tunnelId.type",
                    default="undefined",
                ).upper()
                for eos_via in eos_entry["vias"]
            )
        return True
