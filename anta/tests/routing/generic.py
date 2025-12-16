# Copyright (c) 2023-2025 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Module related to generic routing tests."""

# Mypy does not understand AntaTest.Input typing
# mypy: disable-error-code=attr-defined
from __future__ import annotations

from ipaddress import IPv4Address, ip_address, ip_network
from itertools import cycle
from typing import TYPE_CHECKING, Any, ClassVar, Literal

from pydantic import Field, field_validator, model_validator

from anta.custom_types import PositiveInteger
from anta.input_models.routing.generic import IPv4Routes, RoutingTableEntry
from anta.models import AntaCommand, AntaTemplate, AntaTest
from anta.tools import get_item, get_value

if TYPE_CHECKING:
    import sys

    if sys.version_info >= (3, 11):
        from typing import Self
    else:
        from typing_extensions import Self


class VerifyRoutingProtocolModel(AntaTest):
    """Verifies the configured routing protocol model.

    Expected Results
    ----------------
    * Success: The test will pass if the configured routing protocol model is the one we expect.
    * Failure: The test will fail if the configured routing protocol model is not the one we expect.

    Examples
    --------
    ```yaml
    anta.tests.routing:
      generic:
        - VerifyRoutingProtocolModel:
            model: multi-agent
    ```
    """

    categories: ClassVar[list[str]] = ["routing"]
    commands: ClassVar[list[AntaCommand | AntaTemplate]] = [AntaCommand(command="show ip route summary", revision=3)]

    class Input(AntaTest.Input):
        """Input model for the VerifyRoutingProtocolModel test."""

        model: Literal["multi-agent", "ribd"] = "multi-agent"
        """Expected routing protocol model. Defaults to `multi-agent`."""

    @AntaTest.anta_test
    def test(self) -> None:
        """Main test function for VerifyRoutingProtocolModel."""
        command_output = self.instance_commands[0].json_output
        configured_model = command_output["protoModelStatus"]["configuredProtoModel"]
        operating_model = command_output["protoModelStatus"]["operatingProtoModel"]
        if configured_model == operating_model == self.inputs.model:
            self.result.is_success()
        else:
            self.result.is_failure(f"Routing model is misconfigured - Expected: {self.inputs.model} Actual: {operating_model}")


class VerifyRoutingTableSize(AntaTest):
    """Verifies the size of the IP routing table of the default VRF.

    Expected Results
    ----------------
    * Success: The test will pass if the routing table size is between the provided minimum and maximum values.
    * Failure: The test will fail if the routing table size is not between the provided minimum and maximum values.

    Examples
    --------
    ```yaml
    anta.tests.routing:
      generic:
        - VerifyRoutingTableSize:
            minimum: 2
            maximum: 20
    ```
    """

    categories: ClassVar[list[str]] = ["routing"]
    commands: ClassVar[list[AntaCommand | AntaTemplate]] = [AntaCommand(command="show ip route summary", revision=3)]

    class Input(AntaTest.Input):
        """Input model for the VerifyRoutingTableSize test."""

        minimum: PositiveInteger
        """Expected minimum routing table size."""
        maximum: PositiveInteger
        """Expected maximum routing table size."""

        @model_validator(mode="after")
        def check_min_max(self) -> Self:
            """Validate that maximum is greater than minimum."""
            if self.minimum > self.maximum:
                msg = f"Minimum {self.minimum} is greater than maximum {self.maximum}"
                raise ValueError(msg)
            return self

    @AntaTest.anta_test
    def test(self) -> None:
        """Main test function for VerifyRoutingTableSize."""
        command_output = self.instance_commands[0].json_output
        total_routes = int(command_output["vrfs"]["default"]["totalRoutes"])
        if self.inputs.minimum <= total_routes <= self.inputs.maximum:
            self.result.is_success()
        else:
            self.result.is_failure(
                f"Routing table routes are outside the routes range - Expected: {self.inputs.minimum} <= to >= {self.inputs.maximum} Actual: {total_routes}"
            )


class VerifyRoutingTableEntry(AntaTest):
    """Verifies that the provided routes are present in the routing table of a specified VRF.

    Expected Results
    ----------------
    * Success: The test will pass if the provided routes are present in the routing table.
    * Failure: The test will fail if one or many provided routes are missing from the routing table.

    Examples
    --------
    ```yaml
    anta.tests.routing:
      generic:
        - VerifyRoutingTableEntry:
            routing_table_entries:
              - route: 10.1.0.1
                vrf: default
              - route: 10.1.0.2
                vrf: data
    ```
    """

    categories: ClassVar[list[str]] = ["routing"]
    commands: ClassVar[list[AntaCommand | AntaTemplate]] = [
        AntaTemplate(template="show ip route vrf {vrf} {route}", revision=4),
        AntaTemplate(template="show ip route vrf {vrf}", revision=4),
    ]

    class Input(AntaTest.Input):
        """Input model for the VerifyRoutingTableEntry test."""

        routing_table_entries: list[RoutingTableEntry] = Field(default_factory=list)
        """List of routes to verify."""
        vrf: str = Field(default="default", deprecated="This is deprecated. Consider using the `routing_table_entries` instead.")
        """VRF context. Defaults to `default` VRF."""
        routes: list[IPv4Address] = Field(default_factory=list, deprecated="This is deprecated. Consider using the `routing_table_entries` instead")
        """List of routes to verify."""
        collect: Literal["one", "all"] = Field(default="one", deprecated="This is deprecated. Consider using the `routing_table_entries` instead")
        """Route collect behavior: one=one route per command, all=all routes in vrf per command. Defaults to `one`"""

        @model_validator(mode="after")
        def validate_inputs(self) -> Self:
            """Validate the inputs provided to the VerifyRoutingTableEntry test.

            Either `routing_table_entries` or `routes` must be provided.
            """
            if not self.routing_table_entries and not self.routes:
                msg = "'routing_table_entries' or 'routes' must be provided"
                raise ValueError(msg)
            if self.routing_table_entries and self.routes:
                msg = "Either 'routing_table_entries' or 'routes' can be provided at the same time"
                raise ValueError(msg)
            if self.routing_table_entries and self.collect == "all":
                msg = "Field 'routing_table_entries' cannot be provided when 'collect' is 'all'."
                raise ValueError(msg)
            if self.routes:
                route_ips = {route_ip.route for route_ip in self.routing_table_entries}
                for route in self.routes:
                    if route not in route_ips:
                        self.routing_table_entries.append(RoutingTableEntry(route=route, vrf=self.vrf))
            return self

    def render(self, template: AntaTemplate) -> list[AntaCommand]:
        """Render the template for the input vrf."""
        if template == VerifyRoutingTableEntry.commands[0] and self.inputs.collect == "one":
            return [template.render(vrf=entry.vrf, route=entry.route) for entry in self.inputs.routing_table_entries]
        if self.inputs.collect == "all" and template == VerifyRoutingTableEntry.commands[1]:
            return [template.render(vrf=self.inputs.vrf)]
        return []

    @AntaTest.anta_test
    def test(self) -> None:
        """Main test function for VerifyRoutingTableEntry."""
        self.result.is_success()

        # lookup
        lookup_obj = zip(self.inputs.routing_table_entries, self.instance_commands, strict=False)
        if self.inputs.collect == "all":
            lookup_obj = zip(self.inputs.routing_table_entries, cycle(self.instance_commands), strict=False)
        for input_entry, command in lookup_obj:
            vrf = input_entry.vrf
            route = str(input_entry.route)
            command_output = command.json_output
            routes_details = get_value(command_output, f"vrfs.{vrf}.routes", [])

            # Verify that the expected IPv4 route is present
            prefixes = [ip_network(prefix) for prefix in routes_details]
            route_address = ip_address(route)
            if not any(route_address in prefix for prefix in prefixes):
                self.result.is_failure(f"{input_entry} - Not found")


class VerifyIPv4RouteType(AntaTest):
    """Verifies the route-type of the IPv4 prefixes.

    This test performs the following checks for each IPv4 route:

      1. Verifies that the specified VRF is configured.
      2. Verifies that the specified IPv4 route is exists in the configuration.
      3. Verifies that the the specified IPv4 route is of the expected type.

    Expected Results
    ----------------
    * Success: If all of the following conditions are met:
        - All the specified VRFs are configured.
        - All the specified IPv4 routes are found.
        - All the specified IPv4 routes are of the expected type.
    * Failure: If any of the following occur:
        - A specified VRF is not configured.
        - A specified IPv4 route is not found.
        - Any specified IPv4 route is not of the expected type.

    Examples
    --------
    ```yaml
    anta.tests.routing:
      generic:
        - VerifyIPv4RouteType:
            routes_entries:
              - prefix: 10.10.0.1/32
                vrf: default
                route_type: eBGP
              - prefix: 10.100.0.12/31
                vrf: default
                route_type: connected
              - prefix: 10.100.1.5/32
                vrf: default
                route_type: iBGP
    ```
    """

    categories: ClassVar[list[str]] = ["routing"]
    commands: ClassVar[list[AntaCommand | AntaTemplate]] = [AntaCommand(command="show ip route vrf all", revision=4)]

    class Input(AntaTest.Input):
        """Input model for the VerifyIPv4RouteType test."""

        routes_entries: list[IPv4Routes]
        """List of IPv4 route(s)."""

        @field_validator("routes_entries")
        @classmethod
        def validate_routes_entries(cls, routes_entries: list[IPv4Routes]) -> list[IPv4Routes]:
            """Validate that 'route_type' field is provided in each BGP route entry."""
            for entry in routes_entries:
                if entry.route_type is None:
                    msg = f"{entry} 'route_type' field missing in the input"
                    raise ValueError(msg)
            return routes_entries

    @AntaTest.anta_test
    def test(self) -> None:
        """Main test function for VerifyIPv4RouteType."""
        self.result.is_success()
        output = self.instance_commands[0].json_output

        # Iterating over the all routes entries mentioned in the inputs.
        for entry in self.inputs.routes_entries:
            prefix = str(entry.prefix)
            vrf = entry.vrf
            expected_route_type = entry.route_type

            # Verifying that on device, expected VRF is configured.
            if (routes_details := get_value(output, f"vrfs.{vrf}.routes")) is None:
                self.result.is_failure(f"{entry} - VRF not configured")
                continue

            # Verifying that the expected IPv4 route is present or not on the device
            if (route_data := routes_details.get(prefix)) is None:
                self.result.is_failure(f"{entry} - Route not found")
                continue

            # Verifying that the specified IPv4 routes are of the expected type.
            if expected_route_type != (actual_route_type := route_data.get("routeType")):
                self.result.is_failure(f"{entry} - Incorrect route type - Expected: {expected_route_type} Actual: {actual_route_type}")


class VerifyIPv4RouteNextHops(AntaTest):
    """Verifies the next-hops of the IPv4 prefixes.

    This test performs the following checks for each IPv4 prefix:

      1. Verifies the specified IPv4 route exists in the routing table.
      2. For each specified next-hop:
          - Verifies a path with matching next-hop exists.
          - Supports `strict: True` to verify that routes must be learned exclusively via the exact next-hops specified.

    Expected Results
    ----------------
    * Success: The test will pass if routes exist with paths matching the expected next-hops.
    * Failure: The test will fail if:
        - A route entry is not found for given IPv4 prefixes.
        - A path with specified next-hop is not found.

    Examples
    --------
    ```yaml
    anta.tests.routing:
      generic:
        - VerifyIPv4RouteNextHops:
            route_entries:
                - prefix: 10.10.0.1/32
                  vrf: default
                  strict: false
                  nexthops:
                    - 10.100.0.8
                    - 10.100.0.10
    ```
    """

    categories: ClassVar[list[str]] = ["routing"]
    commands: ClassVar[list[AntaCommand | AntaTemplate]] = [AntaCommand(command="show ip route vrf all", revision=4)]

    class Input(AntaTest.Input):
        """Input model for the VerifyIPv4RouteNextHops test."""

        route_entries: list[IPv4Routes]
        """List of IPv4 route(s)."""

        @field_validator("route_entries")
        @classmethod
        def validate_route_entries(cls, route_entries: list[IPv4Routes]) -> list[IPv4Routes]:
            """Validate that 'nexthops' field is provided in each route entry."""
            for entry in route_entries:
                if entry.nexthops is None:
                    msg = f"{entry} 'nexthops' field missing in the input"
                    raise ValueError(msg)
            return route_entries

    @AntaTest.anta_test
    def test(self) -> None:
        """Main test function for VerifyIPv4RouteNextHops."""
        self.result.is_success()

        output = self.instance_commands[0].json_output

        for entry in self.inputs.route_entries:
            # Verify if the prefix exists in route table
            if (route_data := get_value(output, f"vrfs..{entry.vrf}..routes..{entry.prefix}", separator="..")) is None:
                self.result.is_failure(f"{entry} - prefix not found")
                continue

            # Verify the nexthop addresses
            actual_nexthops = sorted(["Directly connected" if (next_hop := route.get("nexthopAddr")) == "" else next_hop for route in route_data["vias"]])
            expected_nexthops = sorted([str(nexthop) for nexthop in entry.nexthops])

            if entry.strict and expected_nexthops != actual_nexthops:
                exp_nexthops = ", ".join(expected_nexthops)
                self.result.is_failure(f"{entry} - List of next-hops not matching - Expected: {exp_nexthops} Actual: {', '.join(actual_nexthops)}")
                continue

            for nexthop in entry.nexthops:
                if not get_item(route_data["vias"], "nexthopAddr", str(nexthop)):
                    self.result.is_failure(f"{entry} Nexthop: {nexthop} - Route not found")


class VerifyRoutingStatus(AntaTest):
    """Verifies the routing status for IPv4/IPv6 unicast, multicast, and IPv6 interfaces (RFC5549).

    Expected Results
    ----------------
    * Success: The test will pass if the routing status is correct.
    * Failure: The test will fail if the routing status doesn't match the expected configuration.

    Examples
    --------
    ```yaml
    anta.tests.routing:
      generic:
        - VerifyRoutingStatus:
           ipv4_unicast: True
           ipv6_unicast: True
    ```
    """

    categories: ClassVar[list[str]] = ["routing"]
    commands: ClassVar[list[AntaCommand | AntaTemplate]] = [AntaCommand(command="show ip", revision=1)]

    class Input(AntaTest.Input):
        """Input model for the VerifyRoutingStatus test."""

        ipv4_unicast: bool = False
        """IPv4 unicast routing status."""
        ipv6_unicast: bool = False
        """IPv6 unicast routing status."""
        ipv4_multicast: bool = False
        """IPv4 multicast routing status."""
        ipv6_multicast: bool = False
        """IPv6 multicast routing status."""
        ipv6_interfaces: bool = False
        """IPv6 interface forwarding status."""

    @AntaTest.anta_test
    def test(self) -> None:
        """Main test function for VerifyRoutingStatus."""
        self.result.is_success()
        command_output = self.instance_commands[0].json_output
        actual_routing_status: dict[str, Any] = {
            "ipv4_unicast": command_output["v4RoutingEnabled"],
            "ipv6_unicast": command_output["v6RoutingEnabled"],
            "ipv4_multicast": get_value(command_output, "multicastRouting.ipMulticastEnabled", default=False),
            "ipv6_multicast": get_value(command_output, "multicastRouting.ip6MulticastEnabled", default=False),
            "ipv6_interfaces": command_output.get("v6IntfForwarding", False),
        }

        for input_key, value in self.inputs:
            if input_key in actual_routing_status and value != actual_routing_status[input_key]:
                route_type = " ".join([{"ipv4": "IPv4", "ipv6": "IPv6"}.get(part, part) for part in input_key.split("_")])
                self.result.is_failure(f"{route_type} routing enabled status mismatch - Expected: {value} Actual: {actual_routing_status[input_key]}")
