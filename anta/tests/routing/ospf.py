# Copyright (c) 2023 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""
OSPF test functions
"""
# Mypy does not understand AntaTest.Input typing
# mypy: disable-error-code=attr-defined
from __future__ import annotations

from typing import Any

from anta.models import AntaCommand, AntaTest


def _count_ospf_neighbor(ospf_neighbor_json: dict[str, Any]) -> int:
    """
    Count the number of OSPF neighbors
    """
    count = 0
    for _, vrf_data in ospf_neighbor_json["vrfs"].items():
        for _, instance_data in vrf_data["instList"].items():
            count += len(instance_data.get("ospfNeighborEntries", []))
    return count


def _get_not_full_ospf_neighbors(ospf_neighbor_json: dict[str, Any]) -> list[dict[str, Any]]:
    """
    Return the OSPF neighbors whose adjacency state is not "full"
    """
    not_full_neighbors = []
    for vrf, vrf_data in ospf_neighbor_json["vrfs"].items():
        for instance, instance_data in vrf_data["instList"].items():
            for neighbor_data in instance_data.get("ospfNeighborEntries", []):
                if (state := neighbor_data["adjacencyState"]) != "full":
                    not_full_neighbors.append(
                        {
                            "vrf": vrf,
                            "instance": instance,
                            "neighbor": neighbor_data["routerId"],
                            "state": state,
                        }
                    )
    return not_full_neighbors


class VerifyOSPFNeighborState(AntaTest):
    """
    Verifies all OSPF neighbors are in FULL state.
    """

    name = "VerifyOSPFNeighborState"
    description = "Verifies all OSPF neighbors are in FULL state."
    categories = ["routing", "ospf"]
    commands = [AntaCommand(command="show ip ospf neighbor")]

    @AntaTest.anta_test
    def test(self) -> None:
        command_output = self.instance_commands[0].json_output
        if _count_ospf_neighbor(command_output) == 0:
            self.result.is_skipped("no OSPF neighbor found")
            return
        self.result.is_success()
        not_full_neighbors = _get_not_full_ospf_neighbors(command_output)
        if not_full_neighbors:
            self.result.is_failure(f"Some neighbors are not correctly configured: {not_full_neighbors}.")


class VerifyOSPFNeighborCount(AntaTest):
    """
    Verifies the number of OSPF neighbors in FULL state is the one we expect.
    """

    name = "VerifyOSPFNeighborCount"
    description = "Verifies the number of OSPF neighbors in FULL state is the one we expect."
    categories = ["routing", "ospf"]
    commands = [AntaCommand(command="show ip ospf neighbor")]

    class Input(AntaTest.Input):  # pylint: disable=missing-class-docstring
        number: int
        """The expected number of OSPF neighbors in FULL state"""

    @AntaTest.anta_test
    def test(self) -> None:
        command_output = self.instance_commands[0].json_output
        if (neighbor_count := _count_ospf_neighbor(command_output)) == 0:
            self.result.is_skipped("no OSPF neighbor found")
            return
        self.result.is_success()
        if neighbor_count != self.inputs.number:
            self.result.is_failure(f"device has {neighbor_count} neighbors (expected {self.inputs.number})")
        not_full_neighbors = _get_not_full_ospf_neighbors(command_output)
        print(not_full_neighbors)
        if not_full_neighbors:
            self.result.is_failure(f"Some neighbors are not correctly configured: {not_full_neighbors}.")
