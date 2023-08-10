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
from typing import TYPE_CHECKING, List

from pydantic import BaseModel

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
    commands = [AntaTemplate(template="ping vrf {vrf} {dst} source {src} repeat 2")]

    class Input(AntaTest.Input):
        """VerifyReachability inputs"""

        hosts: List[Host]
        """List of hosts to ping"""

        class Host(BaseModel):
            """Remote host to ping"""

            dst: IPv4Address
            """IPv4 address to ping"""
            src: IPv4Address
            """IPv4 address to use as source IP"""
            vrf: str = "default"
            """VRF context"""

    def render(self, template: AntaTemplate) -> list[AntaCommand]:
        return [template.render(dst=host.dst, src=host.src, vrf=host.vrf) for host in self.inputs.hosts]

    @AntaTest.anta_test
    def test(self) -> None:
        failures = []
        for command in self.instance_commands:
            if command.params and ("src" and "dst") in command.params:
                src, dst = command.params["src"], command.params["dst"]
            if "2 received" not in command.json_output["messages"][0]:
                failures.append((str(src), str(dst)))
        if not failures:
            self.result.is_success()
        else:
            self.result.is_failure(f"Connectivity test failed for the following source-destination pairs: {failures}")
