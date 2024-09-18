# Copyright (c) 2023-2024 Arista Networks, Inc.
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
from anta.models import AntaCommand, AntaTemplate, AntaTest
from anta.tools import get_value


def _count_isis_neighbor(isis_neighbor_json: dict[str, Any]) -> int:
    """Count the number of isis neighbors.

    Parameters
    ----------
    isis_neighbor_json
        The JSON output of the `show isis neighbors` command.

    Returns
    -------
    int
        The number of isis neighbors.

    """
    count = 0
    for vrf_data in isis_neighbor_json["vrfs"].values():
        for instance_data in vrf_data["isisInstances"].values():
            count += len(instance_data.get("neighbors", {}))
    return count


def _get_not_full_isis_neighbors(isis_neighbor_json: dict[str, Any]) -> list[dict[str, Any]]:
    """Return the isis neighbors whose adjacency state is not `up`.

    Parameters
    ----------
    isis_neighbor_json
        The JSON output of the `show isis neighbors` command.

    Returns
    -------
    list[dict[str, Any]]
        A list of isis neighbors whose adjacency state is not `UP`.

    """
    return [
        {
            "vrf": vrf,
            "instance": instance,
            "neighbor": adjacency["hostname"],
            "state": state,
        }
        for vrf, vrf_data in isis_neighbor_json["vrfs"].items()
        for instance, instance_data in vrf_data.get("isisInstances").items()
        for neighbor, neighbor_data in instance_data.get("neighbors").items()
        for adjacency in neighbor_data.get("adjacencies")
        if (state := adjacency["state"]) != "up"
    ]


def _get_full_isis_neighbors(isis_neighbor_json: dict[str, Any], neighbor_state: Literal["up", "down"] = "up") -> list[dict[str, Any]]:
    """Return the isis neighbors whose adjacency state is `up`.

    Parameters
    ----------
    isis_neighbor_json
        The JSON output of the `show isis neighbors` command.
    neighbor_state
        Value of the neihbor state we are looking for. Defaults to `up`.

    Returns
    -------
    list[dict[str, Any]]
        A list of isis neighbors whose adjacency state is not `UP`.

    """
    return [
        {
            "vrf": vrf,
            "instance": instance,
            "neighbor": adjacency["hostname"],
            "neighbor_address": adjacency["routerIdV4"],
            "interface": adjacency["interfaceName"],
            "state": state,
        }
        for vrf, vrf_data in isis_neighbor_json["vrfs"].items()
        for instance, instance_data in vrf_data.get("isisInstances").items()
        for neighbor, neighbor_data in instance_data.get("neighbors").items()
        for adjacency in neighbor_data.get("adjacencies")
        if (state := adjacency["state"]) == neighbor_state
    ]


def _get_isis_neighbors_count(isis_neighbor_json: dict[str, Any]) -> list[dict[str, Any]]:
    """Count number of IS-IS neighbor of the device."""
    return [
        {"vrf": vrf, "interface": interface, "mode": mode, "count": int(level_data["numAdjacencies"]), "level": int(level)}
        for vrf, vrf_data in isis_neighbor_json["vrfs"].items()
        for instance, instance_data in vrf_data.get("isisInstances").items()
        for interface, interface_data in instance_data.get("interfaces").items()
        for level, level_data in interface_data.get("intfLevels").items()
        if (mode := level_data["passive"]) is not True
    ]


def _get_interface_data(interface: str, vrf: str, command_output: dict[str, Any]) -> dict[str, Any] | None:
    """Extract data related to an IS-IS interface for testing."""
    if (vrf_data := get_value(command_output, f"vrfs.{vrf}")) is None:
        return None

    for instance_data in vrf_data.get("isisInstances").values():
        if (intf_dict := get_value(dictionary=instance_data, key="interfaces")) is not None:
            try:
                return next(ifl_data for ifl, ifl_data in intf_dict.items() if ifl == interface)
            except StopIteration:
                return None
    return None


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
    """Verifies all IS-IS neighbors are in UP state.

    Expected Results
    ----------------
    * Success: The test will pass if all IS-IS neighbors are in UP state.
    * Failure: The test will fail if some IS-IS neighbors are not in UP state.
    * Skipped: The test will be skipped if no IS-IS neighbor is found.

    Examples
    --------
    ```yaml
    anta.tests.routing:
      isis:
        - VerifyISISNeighborState:
    ```
    """

    name = "VerifyISISNeighborState"
    description = "Verifies all IS-IS neighbors are in UP state."
    categories: ClassVar[list[str]] = ["isis"]
    commands: ClassVar[list[AntaCommand | AntaTemplate]] = [AntaCommand(command="show isis neighbors", revision=1)]

    @AntaTest.anta_test
    def test(self) -> None:
        """Main test function for VerifyISISNeighborState."""
        command_output = self.instance_commands[0].json_output
        if _count_isis_neighbor(command_output) == 0:
            self.result.is_skipped("No IS-IS neighbor detected")
            return
        self.result.is_success()
        not_full_neighbors = _get_not_full_isis_neighbors(command_output)
        if not_full_neighbors:
            self.result.is_failure(f"Some neighbors are not in the correct state (UP): {not_full_neighbors}.")


class VerifyISISNeighborCount(AntaTest):
    """Verifies number of IS-IS neighbors per level and per interface.

    Expected Results
    ----------------
    * Success: The test will pass if the number of neighbors is correct.
    * Failure: The test will fail if the number of neighbors is incorrect.
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

    name = "VerifyISISNeighborCount"
    description = "Verifies count of IS-IS interface per level"
    categories: ClassVar[list[str]] = ["isis"]
    commands: ClassVar[list[AntaCommand | AntaTemplate]] = [AntaCommand(command="show isis interface brief", revision=1)]

    class Input(AntaTest.Input):
        """Input model for the VerifyISISNeighborCount test."""

        interfaces: list[InterfaceCount]
        """list of interfaces with their information."""

        class InterfaceCount(BaseModel):
            """Input model for the VerifyISISNeighborCount test."""

            name: Interface
            """Interface name to check."""
            level: int = 2
            """IS-IS level to check."""
            count: int
            """Number of IS-IS neighbors."""

    @AntaTest.anta_test
    def test(self) -> None:
        """Main test function for VerifyISISNeighborCount."""
        command_output = self.instance_commands[0].json_output
        self.result.is_success()
        isis_neighbor_count = _get_isis_neighbors_count(command_output)
        if len(isis_neighbor_count) == 0:
            self.result.is_skipped("No IS-IS neighbor detected")
            return
        for interface in self.inputs.interfaces:
            eos_data = [ifl_data for ifl_data in isis_neighbor_count if ifl_data["interface"] == interface.name and ifl_data["level"] == interface.level]
            if not eos_data:
                self.result.is_failure(f"No neighbor detected for interface {interface.name}")
                continue
            if eos_data[0]["count"] != interface.count:
                self.result.is_failure(
                    f"Interface {interface.name}: "
                    f"expected Level {interface.level}: count {interface.count}, "
                    f"got Level {eos_data[0]['level']}: count {eos_data[0]['count']}"
                )


class VerifyISISInterfaceMode(AntaTest):
    """Verifies ISIS Interfaces are running in correct mode.

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

    name = "VerifyISISInterfaceMode"
    description = "Verifies interface mode for IS-IS"
    categories: ClassVar[list[str]] = ["isis"]
    commands: ClassVar[list[AntaCommand | AntaTemplate]] = [AntaCommand(command="show isis interface brief", revision=1)]

    class Input(AntaTest.Input):
        """Input model for the VerifyISISNeighborCount test."""

        interfaces: list[InterfaceState]
        """list of interfaces with their information."""

        class InterfaceState(BaseModel):
            """Input model for the VerifyISISNeighborCount test."""

            name: Interface
            """Interface name to check."""
            level: Literal[1, 2] = 2
            """ISIS level configured for interface. Default is 2."""
            mode: Literal["point-to-point", "broadcast", "passive"]
            """Number of IS-IS neighbors."""
            vrf: str = "default"
            """VRF where the interface should be configured"""

    @AntaTest.anta_test
    def test(self) -> None:
        """Main test function for VerifyISISInterfaceMode."""
        command_output = self.instance_commands[0].json_output
        self.result.is_success()

        if len(command_output["vrfs"]) == 0:
            self.result.is_skipped("IS-IS is not configured on device")
            return

        # Check for p2p interfaces
        for interface in self.inputs.interfaces:
            interface_data = _get_interface_data(
                interface=interface.name,
                vrf=interface.vrf,
                command_output=command_output,
            )
            # Check for correct VRF
            if interface_data is not None:
                interface_type = get_value(dictionary=interface_data, key="interfaceType", default="unset")
                # Check for interfaceType
                if interface.mode == "point-to-point" and interface.mode != interface_type:
                    self.result.is_failure(f"Interface {interface.name} in VRF {interface.vrf} is not running in {interface.mode} reporting {interface_type}")
                # Check for passive
                elif interface.mode == "passive":
                    json_path = f"intfLevels.{interface.level}.passive"
                    if interface_data is None or get_value(dictionary=interface_data, key=json_path, default=False) is False:
                        self.result.is_failure(f"Interface {interface.name} in VRF {interface.vrf} is not running in passive mode")
            else:
                self.result.is_failure(f"Interface {interface.name} not found in VRF {interface.vrf}")


class VerifyISISSegmentRoutingAdjacencySegments(AntaTest):
    """Verifies ISIS Segment Routing Adjacency Segments.

    Verify that all expected Adjacency segments are correctly visible for each interface.

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

    name = "VerifyISISSegmentRoutingAdjacencySegments"
    description = "Verify expected Adjacency segments are correctly visible for each interface."
    categories: ClassVar[list[str]] = ["isis", "segment-routing"]
    commands: ClassVar[list[AntaCommand | AntaTemplate]] = [AntaCommand(command="show isis segment-routing adjacency-segments", ofmt="json")]

    class Input(AntaTest.Input):
        """Input model for the VerifyISISSegmentRoutingAdjacencySegments test."""

        instances: list[IsisInstance]

        class IsisInstance(BaseModel):
            """ISIS Instance model definition."""

            name: str
            """ISIS instance name."""
            vrf: str = "default"
            """VRF name where ISIS instance is configured."""
            segments: list[Segment]
            """List of Adjacency segments configured in this instance."""

            class Segment(BaseModel):
                """Segment model definition."""

                interface: Interface
                """Interface name to check."""
                level: Literal[1, 2] = 2
                """ISIS level configured for interface. Default is 2."""
                sid_origin: Literal["dynamic"] = "dynamic"
                """Adjacency type"""
                address: IPv4Address
                """IP address of remote end of segment."""

    @AntaTest.anta_test
    def test(self) -> None:
        """Main test function for VerifyISISSegmentRoutingAdjacencySegments."""
        command_output = self.instance_commands[0].json_output
        self.result.is_success()

        if len(command_output["vrfs"]) == 0:
            self.result.is_skipped("IS-IS is not configured on device")
            return

        # initiate defaults
        failure_message = []
        skip_vrfs = []
        skip_instances = []

        # Check if VRFs and instances are present in output.
        for instance in self.inputs.instances:
            vrf_data = get_value(
                dictionary=command_output,
                key=f"vrfs.{instance.vrf}",
                default=None,
            )
            if vrf_data is None:
                skip_vrfs.append(instance.vrf)
                failure_message.append(f"VRF {instance.vrf} is not configured to run segment routging.")

            elif get_value(dictionary=vrf_data, key=f"isisInstances.{instance.name}", default=None) is None:
                skip_instances.append(instance.name)
                failure_message.append(f"Instance {instance.name} is not found in vrf {instance.vrf}.")

        # Check Adjacency segments
        for instance in self.inputs.instances:
            if instance.vrf not in skip_vrfs and instance.name not in skip_instances:
                for input_segment in instance.segments:
                    eos_segment = _get_adjacency_segment_data_by_neighbor(
                        neighbor=str(input_segment.address),
                        instance=instance.name,
                        vrf=instance.vrf,
                        command_output=command_output,
                    )
                    if eos_segment is None:
                        failure_message.append(f"Your segment has not been found: {input_segment}.")

                    elif (
                        eos_segment["localIntf"] != input_segment.interface
                        or eos_segment["level"] != input_segment.level
                        or eos_segment["sidOrigin"] != input_segment.sid_origin
                    ):
                        failure_message.append(f"Your segment is not correct: Expected: {input_segment} - Found: {eos_segment}.")
        if failure_message:
            self.result.is_failure("\n".join(failure_message))


class VerifyISISSegmentRoutingDataplane(AntaTest):
    """
    Verify dataplane of a list of ISIS-SR instances.

    Expected Results
    ----------------
    * Success: The test will pass if all instances have correct dataplane configured
    * Failure: The test will fail if one of the instances has incorrect dataplane configured
    * Skipped: The test will be skipped if ISIS is not running

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

    name = "VerifyISISSegmentRoutingDataplane"
    description = "Verify dataplane of a list of ISIS-SR instances"
    categories: ClassVar[list[str]] = ["isis", "segment-routing"]
    commands: ClassVar[list[AntaCommand | AntaTemplate]] = [AntaCommand(command="show isis segment-routing", ofmt="json")]

    class Input(AntaTest.Input):
        """Input model for the VerifyISISSegmentRoutingDataplane test."""

        instances: list[IsisInstance]

        class IsisInstance(BaseModel):
            """ISIS Instance model definition."""

            name: str
            """ISIS instance name."""
            vrf: str = "default"
            """VRF name where ISIS instance is configured."""
            dataplane: Literal["MPLS", "mpls", "unset"] = "MPLS"
            """Configured dataplane for the instance."""

    @AntaTest.anta_test
    def test(self) -> None:
        """Main test function for VerifyISISSegmentRoutingDataplane."""
        command_output = self.instance_commands[0].json_output
        self.result.is_success()

        if len(command_output["vrfs"]) == 0:
            self.result.is_skipped("IS-IS-SR is not running on device.")
            return

        # initiate defaults
        failure_message = []
        skip_vrfs = []
        skip_instances = []

        # Check if VRFs and instances are present in output.
        for instance in self.inputs.instances:
            vrf_data = get_value(
                dictionary=command_output,
                key=f"vrfs.{instance.vrf}",
                default=None,
            )
            if vrf_data is None:
                skip_vrfs.append(instance.vrf)
                failure_message.append(f"VRF {instance.vrf} is not configured to run segment routing.")

            elif get_value(dictionary=vrf_data, key=f"isisInstances.{instance.name}", default=None) is None:
                skip_instances.append(instance.name)
                failure_message.append(f"Instance {instance.name} is not found in vrf {instance.vrf}.")

        # Check Adjacency segments
        for instance in self.inputs.instances:
            if instance.vrf not in skip_vrfs and instance.name not in skip_instances:
                eos_dataplane = get_value(dictionary=command_output, key=f"vrfs.{instance.vrf}.isisInstances.{instance.name}.dataPlane", default=None)
                if instance.dataplane.upper() != eos_dataplane:
                    failure_message.append(f"ISIS instance {instance.name} is not running dataplane {instance.dataplane} ({eos_dataplane})")

        if failure_message:
            self.result.is_failure("\n".join(failure_message))


class VerifyISISSegmentRoutingTunnels(AntaTest):
    """
    Verify ISIS-SR tunnels computed by device.

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

    name = "VerifyISISSegmentRoutingTunnels"
    description = "Verify ISIS-SR tunnels computed by device"
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
        """
        Check if the tunnel type specified in `via_input` matches any of the tunnel types in `eos_entry`.

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
        """
        Check if the tunnel nexthop matches the given input.

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
        """
        Check if the tunnel interface exists in the given EOS entry.

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
        """
        Check if the tunnel ID matches any of the tunnel IDs in the EOS entry's vias.

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
