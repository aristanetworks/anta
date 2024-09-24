# Copyright (c) 2023-2024 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Module related to generic routing tests."""

# Mypy does not understand AntaTest.Input typing
# mypy: disable-error-code=attr-defined
from __future__ import annotations

from functools import cache
from ipaddress import IPv4Address, IPv4Interface, IPv4Network
from typing import Any, ClassVar, Literal

from pydantic import BaseModel, model_validator

from anta.models import AntaCommand, AntaTemplate, AntaTest
from anta.tools import get_item, get_value


class VerifyRoutingProtocolModel(AntaTest):
    """Verifies the configured routing protocol model is the one we expect.

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

    name = "VerifyRoutingProtocolModel"
    description = "Verifies the configured routing protocol model."
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
            self.result.is_failure(f"routing model is misconfigured: configured: {configured_model} - operating: {operating_model} - expected: {self.inputs.model}")


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

    name = "VerifyRoutingTableSize"
    description = "Verifies the size of the IP routing table of the default VRF."
    categories: ClassVar[list[str]] = ["routing"]
    commands: ClassVar[list[AntaCommand | AntaTemplate]] = [AntaCommand(command="show ip route summary", revision=3)]

    class Input(AntaTest.Input):
        """Input model for the VerifyRoutingTableSize test."""

        minimum: int
        """Expected minimum routing table size."""
        maximum: int
        """Expected maximum routing table size."""

        @model_validator(mode="after")  # type: ignore[misc]
        def check_min_max(self) -> AntaTest.Input:
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
            self.result.is_failure(f"routing-table has {total_routes} routes and not between min ({self.inputs.minimum}) and maximum ({self.inputs.maximum})")


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
            vrf: default
            routes:
              - 10.1.0.1
              - 10.1.0.2
    ```
    """

    name = "VerifyRoutingTableEntry"
    description = "Verifies that the provided routes are present in the routing table of a specified VRF."
    categories: ClassVar[list[str]] = ["routing"]
    commands: ClassVar[list[AntaCommand | AntaTemplate]] = [
        AntaTemplate(template="show ip route vrf {vrf} {route}", revision=4),
        AntaTemplate(template="show ip route vrf {vrf}", revision=4),
    ]

    class Input(AntaTest.Input):
        """Input model for the VerifyRoutingTableEntry test."""

        vrf: str = "default"
        """VRF context. Defaults to `default` VRF."""
        routes: list[IPv4Address]
        """List of routes to verify."""
        collect: Literal["one", "all"] = "one"
        """Route collect behavior: one=one route per command, all=all routes in vrf per command. Defaults to `one`"""

    def render(self, template: AntaTemplate) -> list[AntaCommand]:
        """Render the template for the input vrf."""
        if template == VerifyRoutingTableEntry.commands[0] and self.inputs.collect == "one":
            return [template.render(vrf=self.inputs.vrf, route=route) for route in self.inputs.routes]

        if template == VerifyRoutingTableEntry.commands[1] and self.inputs.collect == "all":
            return [template.render(vrf=self.inputs.vrf)]

        return []

    @staticmethod
    @cache
    def ip_interface_ip(route: str) -> IPv4Address:
        """Return the IP address of the provided ip route with mask."""
        return IPv4Interface(route).ip

    @AntaTest.anta_test
    def test(self) -> None:
        """Main test function for VerifyRoutingTableEntry."""
        commands_output_route_ips = set()

        for command in self.instance_commands:
            command_output_vrf = command.json_output["vrfs"][self.inputs.vrf]
            commands_output_route_ips |= {self.ip_interface_ip(route) for route in command_output_vrf["routes"]}

        missing_routes = [str(route) for route in self.inputs.routes if route not in commands_output_route_ips]

        if not missing_routes:
            self.result.is_success()
        else:
            self.result.is_failure(f"The following route(s) are missing from the routing table of VRF {self.inputs.vrf}: {missing_routes}")


class VerifyRouteEntry(AntaTest):
    """Verifies the route entries of given IPv4 network(s).

    Supports `strict: True` to verify that only the specified nexthops by which routes are learned, requiring an exact match.

    Expected Results
    ----------------
    * Success: The test will pass if the route entry with given nexthop(s) present for given network(s).
    * Failure: The test will fail if the routes not found or route entry with given nexthop(s) not present for given network(s).

    Examples
    --------
    ```yaml
    anta.tests.routing:
      generic:
        - VerifyRouteEntry:
            route_entries:
                - prefix: 10.10.0.1/32
                  vrf: default
                  nexthops:
                    - 10.100.0.8
                    - 10.100.0.10
    ```
    """

    name = "VerifyRouteEntry"
    description = "Verifies the route entry(s) for the provided IPv4 Network(s)."
    categories: ClassVar[list[str]] = ["routing"]
    commands: ClassVar[list[AntaCommand | AntaTemplate]] = [AntaTemplate(template="show ip route {prefix}", revision=4)]

    class Input(AntaTest.Input):
        """Input model for the VerifyRouteEntry test."""

        route_entries: list[Route]
        """List of route(s)"""

        class Route(BaseModel):
            """Model for a route(s)."""

            prefix: IPv4Network
            """IPv4 network address"""
            vrf: str = "default"
            """Optional VRF. If not provided, it defaults to `default`."""
            nexthops: list[IPv4Address]
            """A list of the next-hop IP address for the path."""
            strict: bool = False
            """If True, requires exact matching of provided nexthop(s). Defaults to False."""

    def render(self, template: AntaTemplate) -> list[AntaCommand]:
        """Render the template for each route entry in the input list."""
        return [template.render(prefix=route.prefix) for route in self.inputs.route_entries]

    @AntaTest.anta_test
    def test(self) -> None:
        """Main test function for VerifyRouteEntry."""
        failures: dict[Any, Any] = {}

        for command, input_entry in zip(self.instance_commands, self.inputs.route_entries):
            prefix = str(input_entry.prefix)
            vrf = input_entry.vrf
            nexthops = input_entry.nexthops
            strict = input_entry.strict

            # Verify if a BGP peer is configured with the provided vrf
            if not (routes := get_value(command.json_output, f"vrfs..{vrf}..routes..{prefix}..vias", separator="..")):
                failures[prefix] = {vrf: "Not configured"}
                continue

            # Verify the nexthop addresses.
            actual_nexthops = [route.get("nexthopAddr") for route in routes]

            if strict and len(nexthops) != len(actual_nexthops):
                exp_nexthops = ", ".join([str(nexthop) for nexthop in nexthops])
                failures[prefix] = {vrf: f"Expected only `{exp_nexthops}` nexthops should be listed but found `{', '.join(actual_nexthops)}` instead."}

            else:
                nexthop_not_ok = [str(nexthop) for nexthop in nexthops if not get_item(routes, "nexthopAddr", str(nexthop))]
                if nexthop_not_ok:
                    failures[prefix] = {vrf: nexthop_not_ok}

        # Check if any failures
        if not failures:
            self.result.is_success()
        else:
            self.result.is_failure(f"Following route entry(s) or nexthop path(s) not found or not correct:\n{failures}")
