# Copyright (c) 2023-2024 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Module related to generic routing tests."""

# Mypy does not understand AntaTest.Input typing
# mypy: disable-error-code=attr-defined
from __future__ import annotations

from functools import cache
from ipaddress import IPv4Address, IPv4Interface
from typing import TYPE_CHECKING, ClassVar, Literal

from pydantic import model_validator

from anta.custom_types import PositiveInteger
from anta.models import AntaCommand, AntaTemplate, AntaTest

if TYPE_CHECKING:
    import sys

    if sys.version_info >= (3, 11):
        from typing import Self
    else:
        from typing_extensions import Self


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
