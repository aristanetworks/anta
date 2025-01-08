# Copyright (c) 2023-2025 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Module related to various connectivity tests."""

# Mypy does not understand AntaTest.Input typing
# mypy: disable-error-code=attr-defined
from __future__ import annotations

from typing import ClassVar

from anta.input_models.connectivity import Host, LLDPNeighbor, Neighbor
from anta.models import AntaCommand, AntaTemplate, AntaTest


class VerifyReachability(AntaTest):
    """Test network reachability to one or many destination IP(s).

    Expected Results
    ----------------
    * Success: The test will pass if all destination IP(s) are reachable.
    * Failure: The test will fail if one or many destination IP(s) are unreachable.

    Examples
    --------
    ```yaml
    anta.tests.connectivity:
      - VerifyReachability:
          hosts:
            - source: Management0
              destination: 1.1.1.1
              vrf: MGMT
              df_bit: True
              size: 100
            - source: Management0
              destination: 8.8.8.8
              vrf: MGMT
              df_bit: True
              size: 100
    ```
    """

    categories: ClassVar[list[str]] = ["connectivity"]
    # Template uses '{size}{df_bit}' without space since df_bit includes leading space when enabled
    commands: ClassVar[list[AntaCommand | AntaTemplate]] = [
        AntaTemplate(template="ping vrf {vrf} {destination} source {source} size {size}{df_bit} repeat {repeat}", revision=1)
    ]

    class Input(AntaTest.Input):
        """Input model for the VerifyReachability test."""

        hosts: list[Host]
        """List of host to ping."""
        Host: ClassVar[type[Host]] = Host
        """To maintain backward compatibility."""

    def render(self, template: AntaTemplate) -> list[AntaCommand]:
        """Render the template for each host in the input list."""
        return [
            template.render(
                destination=host.destination, source=host.source, vrf=host.vrf, repeat=host.repeat, size=host.size, df_bit=" df-bit" if host.df_bit else ""
            )
            for host in self.inputs.hosts
        ]

    @AntaTest.anta_test
    def test(self) -> None:
        """Main test function for VerifyReachability."""
        self.result.is_success()

        for command, host in zip(self.instance_commands, self.inputs.hosts):
            if f"{host.repeat} received" not in command.json_output["messages"][0]:
                self.result.is_failure(f"{host} - Unreachable")


class VerifyLLDPNeighbors(AntaTest):
    """Verifies the connection status of the specified LLDP (Link Layer Discovery Protocol) neighbors.

    This test performs the following checks for each specified LLDP neighbor:

      1. Confirming matching ports on both local and neighboring devices.
      2. Ensuring compatibility of device names and interface identifiers.
      3. Verifying neighbor configurations match expected values per interface; extra neighbors are ignored.

    Expected Results
    ----------------
    * Success: The test will pass if all the provided LLDP neighbors are present and correctly connected to the specified port and device.
    * Failure: The test will fail if any of the following conditions are met:
        - The provided LLDP neighbor is not found in the LLDP table.
        - The system name or port of the LLDP neighbor does not match the expected information.

    Examples
    --------
    ```yaml
    anta.tests.connectivity:
      - VerifyLLDPNeighbors:
          neighbors:
            - port: Ethernet1
              neighbor_device: DC1-SPINE1
              neighbor_port: Ethernet1
            - port: Ethernet2
              neighbor_device: DC1-SPINE2
              neighbor_port: Ethernet1
    ```
    """

    categories: ClassVar[list[str]] = ["connectivity"]
    commands: ClassVar[list[AntaCommand | AntaTemplate]] = [AntaCommand(command="show lldp neighbors detail", revision=1)]

    class Input(AntaTest.Input):
        """Input model for the VerifyLLDPNeighbors test."""

        neighbors: list[LLDPNeighbor]
        """List of LLDP neighbors."""
        Neighbor: ClassVar[type[Neighbor]] = Neighbor
        """To maintain backward compatibility."""

    @AntaTest.anta_test
    def test(self) -> None:
        """Main test function for VerifyLLDPNeighbors."""
        self.result.is_success()

        output = self.instance_commands[0].json_output["lldpNeighbors"]
        for neighbor in self.inputs.neighbors:
            if neighbor.port not in output:
                self.result.is_failure(f"{neighbor} - Port not found")
                continue

            if len(lldp_neighbor_info := output[neighbor.port]["lldpNeighborInfo"]) == 0:
                self.result.is_failure(f"{neighbor} - No LLDP neighbors")
                continue

            # Check if the system name and neighbor port matches
            match_found = any(
                info["systemName"] == neighbor.neighbor_device and info["neighborInterfaceInfo"]["interfaceId_v2"] == neighbor.neighbor_port
                for info in lldp_neighbor_info
            )
            if not match_found:
                failure_msg = [f"{info['systemName']}/{info['neighborInterfaceInfo']['interfaceId_v2']}" for info in lldp_neighbor_info]
                self.result.is_failure(f"{neighbor} - Wrong LLDP neighbors: {', '.join(failure_msg)}")
