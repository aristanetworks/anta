"""
OSPF test functions
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from anta.models import AntaCommand, AntaTest


def _count_ospf_neighbor(ospf_neighbor_json: Dict[str, Any]) -> int:
    """
    Count the number of OSPF neighbors
    """
    count = 0
    for _, vrf_data in ospf_neighbor_json["vrfs"].items():
        for _, instance_data in vrf_data["instList"].items():
            count += len(instance_data.get("ospfNeighborEntries", []))
    return count


def _get_not_full_ospf_neighbors(ospf_neighbor_json: Dict[str, Any]) -> List[Dict[str, Any]]:
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
        """Run VerifyOSPFNeighborState validation"""

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

    Args:
        number (int): The expected number of OSPF neighbors in FULL state.
    """

    name = "VerifyOSPFNeighborCount"
    description = "Verifies the number of OSPF neighbors in FULL state is the one we expect."
    categories = ["routing", "ospf"]
    commands = [AntaCommand(command="show ip ospf neighbor")]

    @AntaTest.anta_test
    def test(self, number: Optional[int] = None) -> None:
        """Run VerifyOSPFNeighborCount validation"""
        if not (isinstance(number, int) and number >= 0):
            self.result.is_skipped(f"VerifyOSPFNeighborCount was not run as the number given '{number}' is not a valid value.")
            return

        command_output = self.instance_commands[0].json_output

        if (neighbor_count := _count_ospf_neighbor(command_output)) == 0:
            self.result.is_skipped("no OSPF neighbor found")
            return

        self.result.is_success()

        if neighbor_count != number:
            self.result.is_failure(f"device has {neighbor_count} neighbors (expected {number})")

        not_full_neighbors = _get_not_full_ospf_neighbors(command_output)
        print(not_full_neighbors)
        if not_full_neighbors:
            self.result.is_failure(f"Some neighbors are not correctly configured: {not_full_neighbors}.")
