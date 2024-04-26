# Copyright (c) 2023-2024 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Module related to IS-IS tests."""

# Mypy does not understand AntaTest.Input typing
# mypy: disable-error-code=attr-defined
from __future__ import annotations

from typing import Any, ClassVar, Literal

from pydantic import BaseModel

from anta.custom_types import Interface
from anta.models import AntaCommand, AntaTemplate, AntaTest
from anta.tools import get_value


def _count_isis_neighbor(isis_neighbor_json: dict[str, Any]) -> int:
    """Count the number of isis neighbors.

    Args
    ----
      isis_neighbor_json: The JSON output of the `show isis neighbors` command.

    Returns
    -------
      int: The number of isis neighbors.

    """
    count = 0
    for vrf_data in isis_neighbor_json["vrfs"].values():
        for instance_data in vrf_data["isisInstances"].values():
            count += len(instance_data.get("neighbors", {}))
    return count


def _get_not_full_isis_neighbors(isis_neighbor_json: dict[str, Any]) -> list[dict[str, Any]]:
    """Return the isis neighbors whose adjacency state is not `up`.

    Args
    ----
      isis_neighbor_json: The JSON output of the `show isis neighbors` command.

    Returns
    -------
      list[dict[str, Any]]: A list of isis neighbors whose adjacency state is not `UP`.

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

    Args
    ----
      isis_neighbor_json: The JSON output of the `show isis neighbors` command.
      neighbor_state: Value of the neihbor state we are looking for. Default up

    Returns
    -------
      list[dict[str, Any]]: A list of isis neighbors whose adjacency state is not `UP`.

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
        for interface in self.inputs.interfaces:
            eos_data = [ifl_data for ifl_data in isis_neighbor_count if ifl_data["interface"] == interface.name and ifl_data["level"] == interface.level]
            if not eos_data:
                self.result.is_failure(f"No neighbor detected for interface {interface.name}")
                return
            if eos_data[0]["count"] != interface.count:
                self.result.is_failure(
                    f"Interface {interface.name}:"
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
            self.result.is_failure("IS-IS is not configured on device")

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
