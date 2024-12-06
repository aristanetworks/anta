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
from anta.input_models.routing.isis import ISISInstance
from anta.models import AntaCommand, AntaTemplate, AntaTest
from anta.tools import get_item, get_value


def _get_isis_neighbor_details(isis_neighbor_json: dict[str, Any], neighbor_state: Literal["up", "down"] | None = None) -> list[dict[str, Any]]:
    """Return the list of isis neighbors.

    Parameters
    ----------
    isis_neighbor_json
        The JSON output of the `show isis neighbors` command.
    neighbor_state
        Value of the neihbor state we are looking for. Defaults to `None`.

    Returns
    -------
    list[dict[str, Any]]
        A list of isis neighbors.

    """
    return [
        {
            "vrf": vrf,
            "instance": instance,
            "neighbor": adjacency["hostname"],
            "neighbor_address": adjacency["routerIdV4"],
            "interface": adjacency["interfaceName"],
            "state": adjacency["state"],
        }
        for vrf, vrf_data in isis_neighbor_json["vrfs"].items()
        for instance, instance_data in vrf_data.get("isisInstances", {}).items()
        for neighbor, neighbor_data in instance_data.get("neighbors", {}).items()
        for adjacency in neighbor_data.get("adjacencies", [])
        if neighbor_state is None or adjacency["state"] == neighbor_state
    ]


def _get_isis_interface_details(isis_neighbor_json: dict[str, Any]) -> list[dict[str, Any]]:
    """Return the isis interface details.

    Parameters
    ----------
    isis_neighbor_json
        The JSON output of the `show isis interface brief` command.

    Returns
    -------
    dict[str, Any]]
        A dict of isis interfaces.

    """
    result = {}
    for vrf, vrf_data in isis_neighbor_json["vrfs"].items():
        result[vrf] = {
            instance: {
                interface: {
                    level: {
                        "passive": level_data.get("passive"),
                        "count": int(level_data.get("numAdjacencies", 0)),
                    }
                    for level, level_data in interface_data.get("intfLevels", {}).items()
                }
                | {"mode": interface_data.get("interfaceType", "unset")}
                for interface, interface_data in instance_data.get("interfaces", {}).items()
            }
            for instance, instance_data in vrf_data.get("isisInstances", {}).items()
        }
    return result


class VerifyISISNeighborState(AntaTest):
    """Verifies all IS-IS neighbors are in UP state.

    Expected Results
    ----------------
    * Success: The test will pass if all IS-IS neighbors are in UP state.
    * Failure: The test will fail if any IS-IS neighbor adjance session is down.
    * Skipped: The test will be skipped if no IS-IS neighbor is found.

    Examples
    --------
    ```yaml
    anta.tests.routing:
      isis:
        - VerifyISISNeighborState:
    ```
    """

    categories: ClassVar[list[str]] = ["isis"]
    commands: ClassVar[list[AntaCommand | AntaTemplate]] = [AntaCommand(command="show isis neighbors", revision=1)]

    @AntaTest.anta_test
    def test(self) -> None:
        """Main test function for VerifyISISNeighborState."""
        self.result.is_success()

        # Verify the ISIS neighbor configure. If not then skip the test.
        command_output = self.instance_commands[0].json_output
        neighbor_details = _get_isis_neighbor_details(command_output)
        if not neighbor_details:
            self.result.is_skipped("No IS-IS neighbor detected")
            return

        # Verify that no neighbor has a session in the down state
        not_full_neighbors = _get_isis_neighbor_details(command_output, neighbor_state="down")
        for neighbor in not_full_neighbors:
            self.result.is_failure(f"Instance: {neighbor['instance']} VRF: {neighbor['vrf']} Neighbor: {neighbor['neighbor']} - Session (adjacency) down")


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
            instances:
                - name: TEST
                  vrf: default
                  interfaces:
                    - name: Ethernet1
                      level: 1
                      neighbor_count: 2
    ```
    """

    categories: ClassVar[list[str]] = ["isis"]
    commands: ClassVar[list[AntaCommand | AntaTemplate]] = [AntaCommand(command="show isis interface brief", revision=1)]

    class Input(AntaTest.Input):
        """Input model for the VerifyISISNeighborCount test."""

        instances: list[ISISInstance]
        """list of interfaces with their information."""

    @AntaTest.anta_test
    def test(self) -> None:
        """Main test function for VerifyISISNeighborCount."""
        command_output = self.instance_commands[0].json_output
        self.result.is_success()
        neighbor_details = _get_isis_interface_details(command_output)

        if all(len(neighbor) == 0 for instance in neighbor_details.values() for neighbor in instance.values()):
            self.result.is_skipped("No IS-IS neighbor detected")
            return

        for instance in self.inputs.instances:
            if not (instance_detail := get_value(neighbor_details, f"{instance.vrf}.{instance.name}")):
                self.result.is_failure(f"{instance} - No IS-IS neighbor detected")
                continue

            for interface in instance.interfaces:
                if not (interface_detail := get_value(instance_detail, interface.name, separator="..")):
                    self.result.is_failure(f"{instance} {interface} - No neighbor detected")
                    continue

                if interface.level and (count := interface_detail[str(interface.level)]["count"]) != interface.neighbor_count:
                    self.result.is_failure(f"{instance} {interface} - Neighbor count mismatch - Expected: {interface.neighbor_count} Actual: {count}")
                # verifying the both level-1 and level-2 (is-type level-1-2)
                elif not ("1" in interface_detail or "2" in interface_detail or all(level["count"] == interface.neighbor_count for level in interface_detail)):
                    self.result.is_failure(f"{instance} {interface} - Level(1-2) not correctly configured")


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
            instances:
                - name: TEST
                  vrf: default
                  interfaces:
                    - name: Ethernet1
                      level: 1
                      mode: passive
    ```
    """

    description = "Verifies interface mode for IS-IS"
    categories: ClassVar[list[str]] = ["isis"]
    commands: ClassVar[list[AntaCommand | AntaTemplate]] = [AntaCommand(command="show isis interface brief", revision=1)]

    class Input(AntaTest.Input):
        """Input model for the VerifyISISNeighborCount test."""

        instances: list[ISISInstance]
        """list of interfaces with their information."""

    @AntaTest.anta_test
    def test(self) -> None:
        """Main test function for VerifyISISInterfaceMode."""
        command_output = self.instance_commands[0].json_output
        self.result.is_success()
        neighbor_details = _get_isis_interface_details(command_output)

        if all(len(neighbor) == 0 for instance in neighbor_details.values() for neighbor in instance.values()):
            self.result.is_skipped("No IS-IS neighbor detected")
            return

        for instance in self.inputs.instances:
            if not (instance_detail := get_value(neighbor_details, f"{instance.vrf}.{instance.name}")):
                self.result.is_failure(f"{instance} - No IS-IS neighbor detected")
                continue

            for interface in instance.interfaces:
                if not (interface_detail := get_value(instance_detail, interface.name, separator="..")):
                    self.result.is_failure(f"{instance} {interface} - No neighbor detected")
                    continue

                mode = interface.mode
                actual_mode = interface_detail["mode"]
                if mode == "passive" and interface_detail[str(interface.level)]["passive"]:
                    actual_mode = "passive"
                if mode != actual_mode:
                    self.result.is_failure(f"{instance} {interface} - Incorrect mode - Expected: {mode} Actual: {actual_mode}")


class VerifyISISSegmentRoutingAdjacencySegments(AntaTest):
    """Verify that all expected Adjacency segments are correctly visible for each interface.

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
                - name: TEST
                  vrf: default
                  interfaces:
                    - name: Ethernet1
                      level: 1
                      segment:
                        sid_origin: dynamic
                        address: "10.0.12.2"
    ```
    """

    categories: ClassVar[list[str]] = ["isis", "segment-routing"]
    commands: ClassVar[list[AntaCommand | AntaTemplate]] = [AntaCommand(command="show isis segment-routing adjacency-segments", ofmt="json")]

    class Input(AntaTest.Input):
        """Input model for the VerifyISISSegmentRoutingAdjacencySegments test."""

        instances: list[ISISInstance]
        """list of interfaces with their information."""

    @AntaTest.anta_test
    def test(self) -> None:
        """Main test function for VerifyISISSegmentRoutingAdjacencySegments."""
        self.result.is_success()

        if not (command_output := self.instance_commands[0].json_output["vrfs"]):
            self.result.is_skipped("No IS-IS neighbor detected")
            return

        # Check if VRFs and instances are present in output.
        for instance in self.inputs.instances:
            if not (instance_data := get_value(command_output, f"{instance.vrf}..isisInstances..{instance.name}", separator="..")):
                self.result.is_failure(f"{instance} - Not configured")
                continue

            for interface in instance.interfaces:
                if interface.level:
                    if not (adjancency_data := get_item(instance_data["adjacencySegments"], "localIntf", interface.name)):
                        self.result.is_failure(f"{instance} {interface} - Not configured")
                        continue

                    if not all(
                        [
                            (act_origin := adjancency_data["sidOrigin"]) == interface.segment.sid_origin,
                            (endpoint := adjancency_data["ipAddress"]) == str(interface.segment.address),
                            (actual_level := adjancency_data["level"]) == interface.level,
                        ]
                    ):
                        self.result.is_failure(
                            f"{instance} {interface} {interface.segment} - Not correctly configured - Origin: {act_origin} Endpoint: {endpoint} Level: {actual_level}"
                        )

                # level_check = Counter(data["localIntf"] for data in instance_data["adjacencySegments"])
                # elif not level_check.interface == 2:
                #     self.result.is_failure(f"{instance} {interface} - Level (1-2) not correctly configure.")
                #     continue
                #     # Need to check to verify the level-1-2


class VerifyISISSegmentRoutingDataplane(AntaTest):
    """Verify dataplane of a list of ISIS-SR instances.

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
                - name: TEST
                  vrf: default
                  dataplane: unset
    ```
    """

    categories: ClassVar[list[str]] = ["isis", "segment-routing"]
    commands: ClassVar[list[AntaCommand | AntaTemplate]] = [AntaCommand(command="show isis segment-routing", ofmt="json")]

    class Input(AntaTest.Input):
        """Input model for the VerifyISISSegmentRoutingDataplane test."""

        instances: list[ISISInstance]
        """list of interfaces with their information."""

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
