# Copyright (c) 2023-2024 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Module related to ISIS tests."""

# Mypy does not understand AntaTest.Input typing
# mypy: disable-error-code=attr-defined
from __future__ import annotations

from typing import Any, ClassVar

from anta.models import AntaCommand, AntaTemplate, AntaTest


def _count_isis_neighbor(isis_neighbor_json: dict[str, Any]) -> int:
    """Count the number of isis neighbors.

    Args:
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
    """Return the isis neighbors whose adjacency state is not `full`.

    Args:
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


class VerifyISISNeighborState(AntaTest):
    """Verifies all ISIS neighbors are in UP state.

    Expected Results
    ----------------
    * Success: The test will pass if all ISIS neighbors are in UP state.
    * Failure: The test will fail if some ISIS neighbors are not in UP state.
    * Skipped: The test will be skipped if no ISIS neighbor is found.

    Examples
    --------
    ```yaml
    anta.tests.routing:
      isis:
        - VerifyISISNeighborState:
    ```
    """

    name = "VerifyISISNeighborState"
    description = "Verifies all ISIS neighbors are in UP state."
    categories: ClassVar[list[str]] = ["isis"]
    commands: ClassVar[list[AntaCommand | AntaTemplate]] = [AntaCommand(command="show isis neighbors", revision=1)]

    @AntaTest.anta_test
    def test(self) -> None:
        """Main test function for VerifyISISNeighborState."""
        command_output = self.instance_commands[0].json_output
        if _count_isis_neighbor(command_output) == 0:
            self.result.is_skipped("no isis neighbor found")
            return
        self.result.is_success()
        not_full_neighbors = _get_not_full_isis_neighbors(command_output)
        if not_full_neighbors:
            self.result.is_failure(f"Some neighbors are not correctly configured: {not_full_neighbors}.")
