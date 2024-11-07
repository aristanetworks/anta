# Copyright (c) 2023-2024 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Module related to various connectivity tests."""

# Mypy does not understand AntaTest.Input typing
# mypy: disable-error-code=attr-defined
from __future__ import annotations

from typing import ClassVar

from pydantic import BaseModel

from anta.custom_types import Interface
from anta.input_models.connectivity import Host
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

    def render(self, template: AntaTemplate) -> list[AntaCommand]:
        """Render the template for each host in the input list."""
        commands = []
        for host in self.inputs.hosts:
            # df_bit includes leading space when enabled, empty string when disabled
            df_bit = " df-bit" if host.df_bit else ""
            command = template.render(destination=host.destination, source=host.source, vrf=host.vrf, repeat=host.repeat, size=host.size, df_bit=df_bit)
            commands.append(command)
        return commands

    @AntaTest.anta_test
    def test(self) -> None:
        """Main test function for VerifyReachability."""
        self.result.is_success()

        for command, host in zip(self.instance_commands, self.inputs.hosts):
            if f"{host.repeat} received" not in command.json_output["messages"][0]:
                self.result.is_failure(f"{host} - Unreachable")


class VerifyLLDPNeighbors(AntaTest):
    """Verifies that the provided LLDP neighbors are present and connected with the correct configuration.

    Expected Results
    ----------------
    * Success: The test will pass if each of the provided LLDP neighbors is present and connected to the specified port and device.
    * Failure: The test will fail if any of the following conditions are met:
        - The provided LLDP neighbor is not found.
        - The system name or port of the LLDP neighbor does not match the provided information.

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

    description = "Verifies that the provided LLDP neighbors are connected properly."
    categories: ClassVar[list[str]] = ["connectivity"]
    commands: ClassVar[list[AntaCommand | AntaTemplate]] = [AntaCommand(command="show lldp neighbors detail", revision=1)]

    class Input(AntaTest.Input):
        """Input model for the VerifyLLDPNeighbors test."""

        neighbors: list[Neighbor]
        """List of LLDP neighbors."""

        class Neighbor(BaseModel):
            """Model for an LLDP neighbor."""

            port: Interface
            """LLDP port."""
            neighbor_device: str
            """LLDP neighbor device."""
            neighbor_port: Interface
            """LLDP neighbor port."""

    @AntaTest.anta_test
    def test(self) -> None:
        """Main test function for VerifyLLDPNeighbors."""
        failures: dict[str, list[str]] = {}

        output = self.instance_commands[0].json_output["lldpNeighbors"]

        for neighbor in self.inputs.neighbors:
            if neighbor.port not in output:
                failures.setdefault("Port(s) not configured", []).append(neighbor.port)
                continue

            if len(lldp_neighbor_info := output[neighbor.port]["lldpNeighborInfo"]) == 0:
                failures.setdefault("No LLDP neighbor(s) on port(s)", []).append(neighbor.port)
                continue

            if not any(
                info["systemName"] == neighbor.neighbor_device and info["neighborInterfaceInfo"]["interfaceId_v2"] == neighbor.neighbor_port
                for info in lldp_neighbor_info
            ):
                neighbors = "\n      ".join(
                    [
                        f"{neighbor[0]}_{neighbor[1]}"
                        for neighbor in [(info["systemName"], info["neighborInterfaceInfo"]["interfaceId_v2"]) for info in lldp_neighbor_info]
                    ]
                )
                failures.setdefault("Wrong LLDP neighbor(s) on port(s)", []).append(f"{neighbor.port}\n      {neighbors}")

        if not failures:
            self.result.is_success()
        else:
            failure_messages = []
            for failure_type, ports in failures.items():
                ports_str = "\n   ".join(ports)
                failure_messages.append(f"{failure_type}:\n   {ports_str}")
            self.result.is_failure("\n".join(failure_messages))
