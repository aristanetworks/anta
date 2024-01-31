# Copyright (c) 2023-2024 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""
Test functions related to the EOS various service settings
"""

# Mypy does not understand AntaTest.Input typing
# mypy: disable-error-code=attr-defined
from __future__ import annotations

from ipaddress import IPv4Address, IPv6Address
from typing import List, Union

from pydantic import BaseModel, Field

from anta.models import AntaCommand, AntaTest
from anta.tools.get_dict_superset import get_dict_superset
from anta.tools.get_item import get_item


class VerifyDNSServers(AntaTest):
    """
    This class checks if the DNS (Domain Name Service) is correctly configured and enabled.

    Expected Results:
        * success: The test will pass if the DNS server specified in the input is configured with the correct VRF and priority.
        * failure: The test will fail if the DNS server is not configured or if the VRF and priority of the DNS server do not match the input.
    """

    name = "VerifyDNSServers"
    description = "Checks if the DNS (Domain Name Service) is correctly configured and enabled."
    categories = ["services"]
    commands = [AntaCommand(command="show ip name-server")]

    class Input(AntaTest.Input):
        """Inputs for the VerifyDNSServers test."""

        dns_servers: List[DnsServers]
        """List of DNS servers to verify."""

        class DnsServers(BaseModel):
            """DNS server details"""

            server_address: Union[IPv4Address, IPv6Address]
            """The IPv4/IPv6 address of the DNS server."""
            vrf: str = "default"
            """The VRF for the DNS server. Defaults to 'default' if not provided."""
            priority: int = Field(ge=0, le=4)
            """The priority of the DNS server from 0 to 4, lower is first."""

    @AntaTest.anta_test
    def test(self) -> None:
        command_output = self.instance_commands[0].json_output["nameServerConfigs"]
        self.result.is_success()
        for server in self.inputs.dns_servers:
            address = str(server.server_address)
            vrf = server.vrf
            priority = server.priority
            input_dict = {"ipAddr": address, "vrf": vrf}

            if get_item(command_output, "ipAddr", address) is None:
                self.result.is_failure(f"DNS server `{address}` is not configured with any VRF.")
                continue

            if (output := get_dict_superset(command_output, input_dict)) is None:
                self.result.is_failure(f"DNS server `{address}` is not configured with VRF `{vrf}`.")
                continue

            if output["priority"] != priority:
                self.result.is_failure(f"For DNS server `{address}`, the expected priority is `{priority}`, but `{output['priority']}` was found instead.")
