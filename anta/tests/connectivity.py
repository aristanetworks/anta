# Copyright (c) 2023 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""
Test functions related to various connectivity checks
"""
# Mypy does not understand AntaTest.Input typing
# mypy: disable-error-code=attr-defined
from __future__ import annotations

from ipaddress import IPv4Address
from typing import TYPE_CHECKING, List, Optional

from pydantic import BaseModel, model_validator

from anta.custom_types import Interface
from anta.models import AntaTemplate, AntaTest

if TYPE_CHECKING:
    from anta.models import AntaCommand


class VerifyReachability(AntaTest):
    """
    Test network reachability to one or many destination IP(s).

    Expected Results:
        * success: The test will pass if all destination IP(s) are reachable.
        * failure: The test will fail if one or many destination IP(s) are unreachable.
    """

    name = "VerifyReachability"
    description = "Test the network reachability to one or many destination IP(s)."
    categories = ["connectivity"]
    commands = [
        AntaTemplate(template="ping vrf {vrf} {destination} source {source} repeat 2"),
        AntaTemplate(template="ping vrf {vrf} {destination} interface {interface} repeat 2"),
    ]

    class Input(AntaTest.Input):  # pylint: disable=missing-class-docstring
        hosts: List[Host]
        """List of hosts to ping"""

        class Host(BaseModel):
            """Remote host to ping"""

            destination: IPv4Address
            """IPv4 address to ping"""
            source: Optional[IPv4Address] = None
            """IPv4 address to use as source IP"""
            interface: Optional[Interface] = None
            """Egress interface to use"""
            vrf: str = "default"
            """VRF context"""

            @model_validator(mode="after")
            def check_source_or_interface(self: BaseModel) -> BaseModel:
                """Ensure either source or interface is provided but not both fields"""
                if not self.source and not self.interface:
                    raise ValueError("either source or interface is required")
                if self.source and self.interface:
                    raise ValueError("source and interface cannot be provided simultaneously")
                return self

    def render(self, template: AntaTemplate) -> list[AntaCommand]:
        commands = []
        for host in self.inputs.hosts:
            if template == VerifyReachability.commands[0] and host.source:
                # We are rendering a ping command with source IP
                commands.append(template.render(destination=host.destination, source=host.source, vrf=host.vrf))
            elif template == VerifyReachability.commands[1] and host.interface:
                # We are rendering a ping command with source interface
                commands.append(template.render(destination=host.destination, interface=host.interface, vrf=host.vrf))
        return commands

    @AntaTest.anta_test
    def test(self) -> None:
        failures = []
        for command in self.instance_commands:
            if command.params:
                if "source" in command.params and "destination" in command.params:
                    src, dst = command.params["source"], command.params["destination"]
                elif "interface" in command.params and "destination" in command.params:
                    src, dst = command.params["interface"], command.params["destination"]
                if "2 received" not in command.json_output["messages"][0]:
                    failures.append((str(src), str(dst)))
        if not failures:
            self.result.is_success()
        else:
            self.result.is_failure(f"Connectivity test failed for the following source-destination pairs: {failures}")
