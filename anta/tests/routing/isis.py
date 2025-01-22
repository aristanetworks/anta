# Copyright (c) 2023-2025 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Module related to IS-IS tests."""

# Mypy does not understand AntaTest.Input typing
# mypy: disable-error-code=attr-defined
from __future__ import annotations

from ipaddress import IPv4Address, IPv4Network
from typing import Any, ClassVar, Literal

from pydantic import BaseModel

from anta.custom_types import Interface
from anta.input_models.routing.isis import ISISInstance, ISISInterface
from anta.models import AntaCommand, AntaTemplate, AntaTest
from anta.tools import get_value


def _get_adjacency_segment_data_by_neighbor(neighbor: str, instance: str, vrf: str, command_output: dict[str, Any]) -> dict[str, Any] | None:
    """Extract data related to an IS-IS interface for testing."""
    search_path = f"vrfs.{vrf}.isisInstances.{instance}.adjacencySegments"
    if get_value(dictionary=command_output, key=search_path, default=None) is None:
        return None

    isis_instance = get_value(dictionary=command_output, key=search_path, default=None)

    return next(
        (segment_data for segment_data in isis_instance if neighbor == segment_data["ipAddress"]),
        None,
    )


class VerifyISISNeighborState(AntaTest):
    """Verifies the health of all the IS-IS neighbors.

    Expected Results
    ----------------
    * Success: The test will pass if all IS-IS neighbors are in UP state.
    * Failure: The test will fail if any IS-IS neighbor adjacency is down.
    * Skipped: The test will be skipped if no IS-IS neighbor is found.

    Examples
    --------
    ```yaml
    anta.tests.routing:
      isis:
        - VerifyISISNeighborState:
            check_all_vrfs: bool = False
    ```
    """

    categories: ClassVar[list[str]] = ["isis"]
    commands: ClassVar[list[AntaCommand | AntaTemplate]] = [AntaCommand(command="show isis neighbors vrf all", revision=1)]

    class Input(AntaTest.Input):
        """Input model for the VerifyISISNeighborCount test."""

        check_all_vrfs: bool = False
        """If enabled it verifies the all ISIS instances in all the configured vrfs. Defaults to `False` and verified the `default` vrf only."""

    @AntaTest.anta_test
    def test(self) -> None:
        """Main test function for VerifyISISNeighborState."""
        self.result.is_success()

        # Verify if ISIS neighbors are configured. Skip the test if none are found.
        if not (command_output := self.instance_commands[0].json_output["vrfs"]):
            self.result.is_skipped("IS-IS is not configured on device")
            return

        vrfs_to_check = command_output
        if not self.inputs.check_all_vrfs:
            vrfs_to_check = {"default": command_output["default"]}

        for vrf, vrf_data in vrfs_to_check.items():
            for isis_instance, instace_data in vrf_data["isisInstances"].items():
                neighbors = instace_data.get("neighbors", {})
                for neighbor in neighbors.values():
                    for adjacencies in neighbor["adjacencies"]:
                        if adjacencies["state"] != "up":
                            self.result.is_failure(f"Instance: {isis_instance} VRF: {vrf} Interface: {adjacencies['interfaceName']} - Session (adjacency) down")


class VerifyISISNeighborCount(AntaTest):
    """Verifies the number of IS-IS neighbors.

    This test performs the following checks for each specified interface:

      1. Validates the IS-IS neighbors configured on specified interface.
      2. Validates the number of IS-IS neighbors for each interface at specified level.

    !! Warning
        Test supports the `default` vrf only.

    Expected Results
    ----------------
    * Success: If all of the following occur:
        - The IS-IS neighbors configured on specified interface.
        - The number of IS-IS neighbors for each interface at specified level matches the given input.
    * Failure: If any of the following occur:
        - The IS-IS neighbors are not configured on specified interface.
        - The number of IS-IS neighbors for each interface at specified level does not matches the given input.
    * Skipped: The test will be skipped if no IS-IS neighbor is found.

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
                # level is set to 2 by default
    ```
    """

    categories: ClassVar[list[str]] = ["isis"]
    commands: ClassVar[list[AntaCommand | AntaTemplate]] = [AntaCommand(command="show isis interface brief", revision=1)]

    class Input(AntaTest.Input):
        """Input model for the VerifyISISNeighborCount test."""

        interfaces: list[ISISInterface]
        """List of IS-IS interfaces with their information."""
        InterfaceCount: ClassVar[type[ISISInterface]] = ISISInterface

    @AntaTest.anta_test
    def test(self) -> None:
        """Main test function for VerifyISISNeighborCount."""
        self.result.is_success()

        command_output = self.instance_commands[0].json_output

        # Verify if ISIS neighbors are configured. Skip the test if none are found.
        if not (instance_detail := get_value(command_output, "vrfs..default..isisInstances", separator="..")):
            self.result.is_skipped("IS-IS is not configured on device")
            return

        for interface in self.inputs.interfaces:
            interface_detail = {}
            for instance_data in instance_detail.values():
                if interface_data := get_value(instance_data, f"interfaces..{interface.name}..intfLevels..{interface.level}", separator=".."):
                    interface_detail = interface_data
                    break

            if not interface_detail:
                self.result.is_failure(f"{interface} - Not configured")
                continue

            if (act_count := interface_detail.get("numAdjacencies", 0)) != interface.count:
                self.result.is_failure(f"{interface} - Neighbor count mismatch - Expected: {interface.count} Actual: {act_count}")


class VerifyISISInterfaceMode(AntaTest):
    """Verifies the operational mode of IS-IS Interfaces.

    This test performs the following checks:

      1. Validates that all specified IS-IS interfaces are configured.
      2. Validates the operational mode of each IS-IS interface (e.g., "active," "passive," or "unset").

    Expected Results
    ----------------
    * Success: The test will pass if all listed interfaces are running in correct mode.
    * Failure: The test will fail if any of the listed interfaces is not running in correct mode.
    * Skipped: The test will be skipped if no ISIS neighbor is found.

    Examples
    --------
    ```yaml
    anta.tests.routing:
      isis:
        - VerifyISISInterfaceMode:
            interfaces:
              - name: Loopback0
                mode: passive
                # vrf is set to default by default
              - name: Ethernet2
                mode: passive
                level: 2
                # vrf is set to default by default
              - name: Ethernet1
                mode: point-to-point
                vrf: default
                # level is set to 2 by default
    ```
    """

    categories: ClassVar[list[str]] = ["isis"]
    commands: ClassVar[list[AntaCommand | AntaTemplate]] = [AntaCommand(command="show isis interface brief vrf all", revision=1)]

    class Input(AntaTest.Input):
        """Input model for the VerifyISISNeighborCount test."""

        interfaces: list[ISISInterface]
        """list of interfaces with their information."""
        InterfaceState: ClassVar[type[ISISInterface]] = ISISInterface

    @AntaTest.anta_test
    def test(self) -> None:
        """Main test function for VerifyISISInterfaceMode."""
        self.result.is_success()

        command_output = self.instance_commands[0].json_output

        # Verify if ISIS neighbors are configured. Skip the test if none are found.
        if len(command_output["vrfs"]) == 0:
            self.result.is_skipped("No IS-IS neighbor detected")
            return

        for interface in self.inputs.interfaces:
            interface_detail = {}
            instance_detail = get_value(command_output, f"vrfs..{interface.vrf}..isisInstances", separator="..", default={})
            for instance_data in instance_detail.values():
                if interface_data := get_value(instance_data, f"interfaces..{interface.name}", separator=".."):
                    interface_detail = interface_data
                    break

            if not interface_detail:
                self.result.is_failure(f"{interface} - Not configured")
                continue

            # Check for passive
            if interface.mode == "passive" and get_value(interface_detail, f"intfLevels.{interface.level}.passive", default=False) is False:
                self.result.is_failure(f"{interface} - Not running in passive mode")

            elif interface.mode != (interface_type := get_value(interface_detail, "interfaceType", default="unset")):
                self.result.is_failure(f"{interface} - Incorrect circuit type - Expected: {interface.mode} Actual: {interface_type}")


class VerifyISISSegmentRoutingAdjacencySegments(AntaTest):
    """Verifies the ISIS SR Adjacency Segments.

    Expected Results
    ----------------
    * Success: The test will pass if all listed interfaces have correct adjacencies.
    * Failure: The test will fail if any of the listed interfaces has not expected list of adjacencies.
    * Skipped: The test will be skipped if no ISIS SR Adjacency is found.

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
        """list of ISIS instances with their information."""
        IsisInstance: ClassVar[type[ISISInstance]] = ISISInstance

    @AntaTest.anta_test
    def test(self) -> None:
        """Main test function for VerifyISISSegmentRoutingAdjacencySegments."""
        self.result.is_success()

        command_output = self.instance_commands[0].json_output
        if len(command_output["vrfs"]) == 0:
            self.result.is_skipped("No IS-IS neighbor detected")
            return

        # Check if VRFs and instances are present in output.
        for instance in self.inputs.instances:
            vrf_data = get_value(
                dictionary=command_output,
                key=f"vrfs.{instance.vrf}",
                default=None,
            )
            if vrf_data is None:
                self.result.is_failure(f"{instance} - VRF not configured")
                continue

            if get_value(dictionary=vrf_data, key=f"isisInstances.{instance.name}", default=None) is None:
                self.result.is_failure(f"{instance} - Not configured")
                continue

            for input_segment in instance.segments:
                eos_segment = _get_adjacency_segment_data_by_neighbor(
                    neighbor=str(input_segment.address),
                    instance=instance.name,
                    vrf=instance.vrf,
                    command_output=command_output,
                )
                if eos_segment is None:
                    self.result.is_failure(f"{instance} {input_segment} - Segment not configured")
                    continue

                if (act_origin := eos_segment["sidOrigin"]) != input_segment.sid_origin:
                    self.result.is_failure(
                        f"{instance} {input_segment} - Incorrect Segment Identifier origin - Expected: {input_segment.sid_origin} Actual: {act_origin}"
                    )

                if (actual_level := eos_segment["level"]) != input_segment.level:
                    self.result.is_failure(f"{instance} {input_segment} - Incorrect IS-IS level - Expected: {input_segment.level} Actual: {actual_level}")


class VerifyISISSegmentRoutingDataplane(AntaTest):
    """Verifies the Dataplane of ISIS-SR Instances.

    This test performs the following checks:

      1. Validates that listed ISIS-SR instance exists.
      2. Validates the configured dataplane matches the expected value for each instance.

    Expected Results
    ----------------
    * Success: If all of the following occur:
        - All specified ISIS-SR instances are configured.
        - Each instance has the correct dataplane.
    * Failure: If any of the following occur:
        - Any specified ISIS-SR instance is not configured.
        - Any instance has an incorrect dataplane configuration.
    * Skipped: The test will be skipped if no IS-IS neighbor is found.

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
        """list of ISIS instances with their information."""
        IsisInstance: ClassVar[type[ISISInstance]] = ISISInstance

    @AntaTest.anta_test
    def test(self) -> None:
        """Main test function for VerifyISISSegmentRoutingDataplane."""
        self.result.is_success()

        if not (command_output := self.instance_commands[0].json_output["vrfs"]):
            self.result.is_skipped("No IS-IS neighbor detected")
            return

        # Check if VRFs and instances are present in output.
        for instance in self.inputs.instances:
            if not (instance_data := get_value(command_output, f"{instance.vrf}..isisInstances..{instance.name}", separator="..")):
                self.result.is_failure(f"{instance} - Not configured")
                continue

            if instance.dataplane.upper() != (plane := instance_data["dataPlane"]):
                self.result.is_failure(f"{instance} - Dataplane not correctly configured - Expected: {instance.dataplane.upper()} Actual: {plane}")


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
