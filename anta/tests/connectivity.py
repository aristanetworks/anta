# Copyright (c) 2023-2025 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Module related to various connectivity tests."""

# Pyright does not understand AntaTest.Input typing
# pyright: reportAttributeAccessIssue=false
from __future__ import annotations

import re
from typing import TYPE_CHECKING, ClassVar, TypeVar

from pydantic import field_validator

from anta.input_models.connectivity import Host, LLDPNeighbor, Neighbor
from anta.models import AntaCommand, AntaTemplate, AntaTest
from anta.result_manager.models import AntaTestStatus

if TYPE_CHECKING:
    from anta.result_manager.models import AtomicTestResult

T = TypeVar("T", bound=Host)


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
              reachable: true
            - destination: 8.8.8.8
              vrf: MGMT
              df_bit: True
              size: 100
            - source: fd12:3456:789a:1::1
              destination: fd12:3456:789a:1::2
              vrf: default
              df_bit: True
              size: 100
              reachable: false
    ```
    """

    categories: ClassVar[list[str]] = ["connectivity"]
    # Template uses '{size}{df_bit}' without space since df_bit includes leading space when enabled
    commands: ClassVar[list[AntaCommand | AntaTemplate]] = [
        AntaTemplate(template="ping vrf {vrf} {destination}{source} size {size}{df_bit} repeat {repeat}", revision=1)
    ]

    _PING_PATTERN = re.compile(r"(\d{1,20})\s+received")
    """Regex pattern to retrieve ping received packet count, limiting the number of digits to avoid ReDoS vulnerability."""
    _atomic_support: ClassVar[bool] = True

    class Input(AntaTest.Input):
        """Input model for the VerifyReachability test."""

        hosts: list[Host]
        """List of host to ping."""
        Host: ClassVar[type[Host]] = Host
        """To maintain backward compatibility."""

        @field_validator("hosts")
        @classmethod
        def validate_hosts(cls, hosts: list[T]) -> list[T]:
            """Validate the 'destination' and 'source' IP address family in each host."""
            for host in hosts:
                if host.source and not isinstance(host.source, str) and host.destination.version != host.source.version:
                    msg = f"{host} IP address family for destination does not match source"
                    raise ValueError(msg)
            return hosts

    def render(self, template: AntaTemplate) -> list[AntaCommand]:
        """Render the template for each host in the input list."""
        return [
            template.render(
                destination=host.destination,
                source=f" source {host.source}" if host.source else "",
                vrf=host.vrf,
                repeat=host.repeat,
                size=host.size,
                df_bit=" df-bit" if host.df_bit else "",
            )
            for host in self.inputs.hosts
        ]

    def _validate_host_reachability(self, host: Host, message: str, result: AtomicTestResult) -> None:
        """Validate a single host reachability result."""
        # Handle "Network is unreachable" edge case
        if "Network is unreachable" in message:
            if host.reachable:
                result.is_failure("Unreachable")
            else:
                # If the network is unreachable and the host is expected to be unreachable, the test passes
                result.is_success()
            return

        # Parse packet count
        received_packets = self._get_received_packets(message)
        if received_packets is None:
            result.is_failure(f"Error when executing ping: '{message.rstrip()}'")
            return

        # Validate based on expectation
        if host.reachable:
            if received_packets == host.repeat:
                result.is_success()
            else:
                result.is_failure(f"Packet loss detected - Transmitted: {host.repeat} Received: {received_packets}")
        elif received_packets != 0:
            result.is_failure("Destination is expected to be unreachable but found reachable")
        else:
            # If we reach this point, the host is unreachable and there are no received packet as expected
            result.is_success()

    def _get_received_packets(self, message: str) -> int | None:
        """Extract received packet count from ping output."""
        match = self._PING_PATTERN.search(message)
        return int(match.group(1)) if match else None

    @AntaTest.anta_test
    def test(self) -> None:
        """Main test function for VerifyReachability."""
        for command, host in zip(self.instance_commands, self.inputs.hosts, strict=True):
            message = command.json_output["messages"][0]

            # Create an atomic result for each host
            host_result = self.result.add(description=str(host))

            self._validate_host_reachability(host, message, host_result)


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
          require_fqdn: False
          neighbors:
            - port: Ethernet1
              neighbor_device: DC1-SPINE1
              neighbor_port: Ethernet1
            - port: Ethernet2
              neighbor_device: dc1-leaf2-server1
              neighbor_port: iLO
      - VerifyLLDPNeighbors:
          require_fqdn: True
          neighbors:
            - port: Ethernet1
              neighbor_device: DC1-SPINE1.local.com
              neighbor_port: Ethernet1
    ```
    """

    categories: ClassVar[list[str]] = ["connectivity"]
    commands: ClassVar[list[AntaCommand | AntaTemplate]] = [AntaCommand(command="show lldp neighbors detail", revision=1)]
    _atomic_support: ClassVar[bool] = True

    class Input(AntaTest.Input):
        """Input model for the VerifyLLDPNeighbors test."""

        neighbors: list[LLDPNeighbor]
        """List of LLDP neighbors."""
        require_fqdn: bool = True
        """If True (default), neighbor_device must exactly match the neighbor FQDN system name. If False, the match is performed using only the hostname portion,
        it can either exactly match or start with the specified hostname."""
        Neighbor: ClassVar[type[Neighbor]] = Neighbor
        """To maintain backward compatibility."""

    @AntaTest.anta_test
    def test(self) -> None:
        """Main test function for VerifyLLDPNeighbors."""
        output = self.instance_commands[0].json_output["lldpNeighbors"]
        for neighbor in self.inputs.neighbors:
            # Atomic result
            result = self.result.add(description=str(neighbor), status=AntaTestStatus.SUCCESS)
            if neighbor.port not in output:
                result.is_failure("Port not found")
                continue

            if len(lldp_neighbor_info := output[neighbor.port]["lldpNeighborInfo"]) == 0:
                result.is_failure("No LLDP neighbors")
                continue

            # Check if the system name and neighbor port matches
            match_found = any(
                (
                    info["systemName"] == neighbor.neighbor_device
                    if self.inputs.require_fqdn
                    else info["systemName"].startswith(f"{neighbor.neighbor_device}.") or info["systemName"] == neighbor.neighbor_device
                )
                and info["neighborInterfaceInfo"]["interfaceId_v2"] == neighbor.neighbor_port
                for info in lldp_neighbor_info
            )
            if not match_found:
                failure_msg = [f"{info['systemName']}/{info['neighborInterfaceInfo']['interfaceId_v2']}" for info in lldp_neighbor_info]
                result.is_failure(f"Wrong LLDP neighbors: {', '.join(failure_msg)}")
