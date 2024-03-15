# Copyright (c) 2023-2024 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Module related to OSPF tests."""

# Mypy does not understand AntaTest.Input typing
# mypy: disable-error-code=attr-defined
from __future__ import annotations

from typing import TYPE_CHECKING, Any, ClassVar

from anta.models import AntaCommand, AntaTest

if TYPE_CHECKING:
    from anta.models import AntaTemplate


def _count_ospf_neighbor(ospf_neighbor_json: dict[str, Any]) -> int:
    """Count the number of OSPF neighbors.

    Args:
    ----
      ospf_neighbor_json (dict[str, Any]): The JSON output of the `show ip ospf neighbor` command.

    Returns
    -------
      int: The number of OSPF neighbors.

    """
    count = 0
    for vrf_data in ospf_neighbor_json["vrfs"].values():
        for instance_data in vrf_data["instList"].values():
            count += len(instance_data.get("ospfNeighborEntries", []))
    return count


def _get_not_full_ospf_neighbors(ospf_neighbor_json: dict[str, Any]) -> list[dict[str, Any]]:
    """Return the OSPF neighbors whose adjacency state is not `full`.

    Args:
    ----
      ospf_neighbor_json (dict[str, Any]): The JSON output of the `show ip ospf neighbor` command.

    Returns
    -------
      list[dict[str, Any]]: A list of OSPF neighbors whose adjacency state is not `full`.

    """
    return [
        {
            "vrf": vrf,
            "instance": instance,
            "neighbor": neighbor_data["routerId"],
            "state": state,
        }
        for vrf, vrf_data in ospf_neighbor_json["vrfs"].items()
        for instance, instance_data in vrf_data["instList"].items()
        for neighbor_data in instance_data.get("ospfNeighborEntries", [])
        if (state := neighbor_data["adjacencyState"]) != "full"
    ]


class VerifyOSPFNeighborState(AntaTest):
    """Verifies all OSPF neighbors are in FULL state.

    Expected Results
    ----------------
    * Success: The test will pass if all OSPF neighbors are in FULL state.
    * Failure: The test will fail if some OSPF neighbors are not in FULL state.
    * Skipped: The test will be skipped if no OSPF neighbor is found.
    """

    name = "VerifyOSPFNeighborState"
    description = "Verifies all OSPF neighbors are in FULL state."
    categories: ClassVar[list[str]] = ["ospf"]
    commands: ClassVar[list[AntaCommand | AntaTemplate]] = [AntaCommand(command="show ip ospf neighbor")]

    @AntaTest.anta_test
    def test(self) -> None:
        """Main test function for VerifyOSPFNeighborState."""
        command_output = self.instance_commands[0].json_output
        if _count_ospf_neighbor(command_output) == 0:
            self.result.is_skipped("no OSPF neighbor found")
            return
        self.result.is_success()
        not_full_neighbors = _get_not_full_ospf_neighbors(command_output)
        if not_full_neighbors:
            self.result.is_failure(f"Some neighbors are not correctly configured: {not_full_neighbors}.")


class VerifyOSPFNeighborCount(AntaTest):
    """Verifies the number of OSPF neighbors in FULL state is the one we expect.

    Expected Results
    ----------------
    * Success: The test will pass if the number of OSPF neighbors in FULL state is the one we expect.
    * Failure: The test will fail if the number of OSPF neighbors in FULL state is not the one we expect.
    * Skipped: The test will be skipped if no OSPF neighbor is found.
    """

    name = "VerifyOSPFNeighborCount"
    description = "Verifies the number of OSPF neighbors in FULL state is the one we expect."
    categories: ClassVar[list[str]] = ["ospf"]
    commands: ClassVar[list[AntaCommand | AntaTemplate]] = [AntaCommand(command="show ip ospf neighbor")]

    class Input(AntaTest.Input):
        """Input model for the VerifyOSPFNeighborCount test."""

        number: int
        """The expected number of OSPF neighbors in FULL state."""

    @AntaTest.anta_test
    def test(self) -> None:
        """Main test function for VerifyOSPFNeighborCount."""
        command_output = self.instance_commands[0].json_output
        if (neighbor_count := _count_ospf_neighbor(command_output)) == 0:
            self.result.is_skipped("no OSPF neighbor found")
            return
        self.result.is_success()
        if neighbor_count != self.inputs.number:
            self.result.is_failure(f"device has {neighbor_count} neighbors (expected {self.inputs.number})")
        not_full_neighbors = _get_not_full_ospf_neighbors(command_output)
        if not_full_neighbors:
            self.result.is_failure(f"Some neighbors are not correctly configured: {not_full_neighbors}.")
