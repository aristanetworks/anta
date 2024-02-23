# Copyright (c) 2023-2024 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""
Test functions related to the EOS various services settings
"""
from __future__ import annotations

from typing import List

from anta.models import AntaCommand, AntaTemplate, AntaTest

# Mypy does not understand AntaTest.Input typing
# mypy: disable-error-code=attr-defined


class VerifyHostname(AntaTest):
    """
    This class verifies the hostname of a device.
    Expected results:
        * success: The test will pass if the hostname matches the provided input.
        * failure: The test will fail if the hostname does not match the provided input.
    """

    name = "VerifyHostname"
    description = "Verifies the hostname of a device."
    categories = ["services"]
    commands = [AntaCommand(command="show hostname")]

    class Input(AntaTest.Input):
        """Defines the input parameters for this test case."""

        hostname: str
        """Expected hostname of the device."""

    @AntaTest.anta_test
    def test(self) -> None:
        hostname = self.instance_commands[0].json_output["hostname"]

        if hostname != self.inputs.hostname:
            self.result.is_failure(f"Expected `{self.inputs.hostname}` as the hostname, but found `{hostname}` instead.")
        else:
            self.result.is_success()


class VerifyDNSLookup(AntaTest):
    """
    This class verifies the DNS (Domain name service) name to IP address translation.
    Expected Results:
        * success: The test will pass if a domain name is resolved to an IP address.
        * failure: The test will fail if a domain name does not resolve to an IP address.
        * error: This test will error out if a domain name is not correct.
    """

    name = "VerifyDNSLookup"
    description = "Verifies the DNS (Domain name service) name to IP address translation."
    categories = ["services"]
    commands = [AntaTemplate(template="bash timeout 10 nslookup {domain}")]

    class Input(AntaTest.Input):
        """Inputs for the VerifyDNSLookup test."""

        domain_names: List[str]
        """List of domain names"""

    def render(self, template: AntaTemplate) -> list[AntaCommand]:
        return [template.render(domain=domain_name) for domain_name in self.inputs.domain_names]

    @AntaTest.anta_test
    def test(self) -> None:
        self.result.is_success()
        failed_domains = []
        for command in self.instance_commands:
            domain = command.params["domain"]
            output = command.json_output["messages"][0]
            if f"Can't find {domain}: No answer" in output:
                failed_domains.append(domain)
        if failed_domains:
            self.result.is_failure(f"The following domain(s) are not resolved to an IP address: {', '.join(failed_domains)}")
