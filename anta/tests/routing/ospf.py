# Copyright (c) 2023-2025 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Module related to OSPF tests."""

# Mypy does not understand AntaTest.Input typing
# mypy: disable-error-code=attr-defined
from __future__ import annotations

from typing import TYPE_CHECKING, ClassVar

from anta.models import AntaCommand, AntaTest
from anta.tools import get_value

if TYPE_CHECKING:
    from anta.models import AntaTemplate


class VerifyOSPFNeighborState(AntaTest):
    """Verifies all OSPF neighbors are in FULL state.

    Expected Results
    ----------------
    * Success: The test will pass if all OSPF neighbors are in FULL state.
    * Failure: The test will fail if some OSPF neighbors are not in FULL state.
    * Skipped: The test will be skipped if no OSPF neighbor is found.

    Examples
    --------
    ```yaml
    anta.tests.routing:
      ospf:
        - VerifyOSPFNeighborState:
    ```
    """

    categories: ClassVar[list[str]] = ["ospf"]
    commands: ClassVar[list[AntaCommand | AntaTemplate]] = [AntaCommand(command="show ip ospf neighbor", revision=1)]

    @AntaTest.anta_test
    def test(self) -> None:
        """Main test function for VerifyOSPFNeighborState."""
        self.result.is_success()

        # If OSPF is not configured on device, test skipped.
        if not (command_output := get_value(self.instance_commands[0].json_output, "vrfs")):
            self.result.is_skipped("OSPF not configured")
            return

        no_neighbor = True
        for vrf, vrf_data in command_output.items():
            for instance, instance_data in vrf_data["instList"].items():
                neighbors = instance_data["ospfNeighborEntries"]
                if not neighbors:
                    continue
                no_neighbor = False
                interfaces = [(neighbor["routerId"], state) for neighbor in neighbors if (state := neighbor["adjacencyState"]) != "full"]
                for interface in interfaces:
                    self.result.is_failure(
                        f"Instance: {instance} VRF: {vrf} Interface: {interface[0]} - Incorrect adjacency state - Expected: Full Actual: {interface[1]}"
                    )

        # If OSPF neighbors are not configured on device, test skipped.
        if no_neighbor:
            self.result.is_skipped("No OSPF neighbor detected")


class VerifyOSPFNeighborCount(AntaTest):
    """Verifies the number of OSPF neighbors in FULL state is the one we expect.

    Expected Results
    ----------------
    * Success: The test will pass if the number of OSPF neighbors in FULL state is the one we expect.
    * Failure: The test will fail if the number of OSPF neighbors in FULL state is not the one we expect.
    * Skipped: The test will be skipped if no OSPF neighbor is found.

    Examples
    --------
    ```yaml
    anta.tests.routing:
      ospf:
        - VerifyOSPFNeighborCount:
            number: 3
    ```
    """

    categories: ClassVar[list[str]] = ["ospf"]
    commands: ClassVar[list[AntaCommand | AntaTemplate]] = [AntaCommand(command="show ip ospf neighbor", revision=1)]

    class Input(AntaTest.Input):
        """Input model for the VerifyOSPFNeighborCount test."""

        number: int
        """The expected number of OSPF neighbors in FULL state."""

    @AntaTest.anta_test
    def test(self) -> None:
        """Main test function for VerifyOSPFNeighborCount."""
        self.result.is_success()
        # If OSPF is not configured on device, test skipped.
        if not (command_output := get_value(self.instance_commands[0].json_output, "vrfs")):
            self.result.is_skipped("OSPF not configured")
            return

        no_neighbor = True
        interfaces = []
        for vrf_data in command_output.values():
            for instance_data in vrf_data["instList"].values():
                neighbors = instance_data["ospfNeighborEntries"]
                if not neighbors:
                    continue
                no_neighbor = False
                interfaces.extend([neighbor["routerId"] for neighbor in neighbors if neighbor["adjacencyState"] == "full"])

        # If OSPF neighbors are not configured on device, test skipped.
        if no_neighbor:
            self.result.is_skipped("No OSPF neighbor detected")
            return

        # If the number of OSPF neighbors expected to be in the FULL state does not match with actual one, test fails.
        if len(interfaces) != self.inputs.number:
            self.result.is_failure(f"Neighbor count mismatch - Expected: {self.inputs.number} Actual: {len(interfaces)}")


class VerifyOSPFMaxLSA(AntaTest):
    """Verifies all OSPF instances did not cross the maximum LSA threshold.

    Expected Results
    ----------------
    * Success: The test will pass if all OSPF instances did not cross the maximum LSA Threshold.
    * Failure: The test will fail if some OSPF instances crossed the maximum LSA Threshold.
    * Skipped: The test will be skipped if no OSPF instance is found.

    Examples
    --------
    ```yaml
    anta.tests.routing:
      ospf:
        - VerifyOSPFMaxLSA:
    ```
    """

    categories: ClassVar[list[str]] = ["ospf"]
    commands: ClassVar[list[AntaCommand | AntaTemplate]] = [AntaCommand(command="show ip ospf", revision=1)]

    @AntaTest.anta_test
    def test(self) -> None:
        """Main test function for VerifyOSPFMaxLSA."""
        self.result.is_success()

        # If OSPF is not configured on device, test skipped.
        if not (command_output := get_value(self.instance_commands[0].json_output, "vrfs")):
            self.result.is_skipped("OSPF not configured")
            return

        for vrf_data in command_output.values():
            for instance, instance_data in vrf_data.get("instList", {}).items():
                max_lsa = instance_data["maxLsaInformation"]["maxLsa"]
                max_lsa_threshold = instance_data["maxLsaInformation"]["maxLsaThreshold"]
                num_lsa = get_value(instance_data, "lsaInformation.numLsa")
                if num_lsa > (max_lsa_threshold := round(max_lsa * (max_lsa_threshold / 100))):
                    self.result.is_failure(f"Instance: {instance} - Crossed the maximum LSA threshold - Expected: < {max_lsa_threshold} Actual: {num_lsa}")
