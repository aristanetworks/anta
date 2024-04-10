# Copyright (c) 2023-2024 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Module related to the EOS various services tests."""

from __future__ import annotations

# Mypy does not understand AntaTest.Input typing
# mypy: disable-error-code=attr-defined
from ipaddress import IPv4Address, IPv6Address
from typing import ClassVar

from pydantic import BaseModel, Field

from anta.custom_types import ErrDisableInterval, ErrDisableReasons
from anta.models import AntaCommand, AntaTemplate, AntaTest
from anta.tools import get_dict_superset, get_failed_logs, get_item


class VerifyHostname(AntaTest):
    """Verifies the hostname of a device.

    Expected Results
    ----------------
    * Success: The test will pass if the hostname matches the provided input.
    * Failure: The test will fail if the hostname does not match the provided input.

    Examples
    --------
    ```yaml
    anta.tests.services:
      - VerifyHostname:
          hostname: s1-spine1
    ```
    """

    name = "VerifyHostname"
    description = "Verifies the hostname of a device."
    categories: ClassVar[list[str]] = ["services"]
    commands: ClassVar[list[AntaCommand | AntaTemplate]] = [AntaCommand(command="show hostname", revision=1)]

    class Input(AntaTest.Input):
        """Input model for the VerifyHostname test."""

        hostname: str
        """Expected hostname of the device."""

    @AntaTest.anta_test
    def test(self) -> None:
        """Main test function for VerifyHostname."""
        hostname = self.instance_commands[0].json_output["hostname"]

        if hostname != self.inputs.hostname:
            self.result.is_failure(f"Expected `{self.inputs.hostname}` as the hostname, but found `{hostname}` instead.")
        else:
            self.result.is_success()


class VerifyDNSLookup(AntaTest):
    """Verifies the DNS (Domain Name Service) name to IP address resolution.

    Expected Results
    ----------------
    * Success: The test will pass if a domain name is resolved to an IP address.
    * Failure: The test will fail if a domain name does not resolve to an IP address.
    * Error: This test will error out if a domain name is invalid.

    Examples
    --------
    ```yaml
    anta.tests.services:
      - VerifyDNSLookup:
          domain_names:
            - arista.com
            - www.google.com
            - arista.ca
    ```
    """

    name = "VerifyDNSLookup"
    description = "Verifies the DNS name to IP address resolution."
    categories: ClassVar[list[str]] = ["services"]
    commands: ClassVar[list[AntaCommand | AntaTemplate]] = [AntaTemplate(template="bash timeout 10 nslookup {domain}", revision=1)]

    class Input(AntaTest.Input):
        """Input model for the VerifyDNSLookup test."""

        domain_names: list[str]
        """List of domain names."""

    def render(self, template: AntaTemplate) -> list[AntaCommand]:
        """Render the template for each domain name in the input list."""
        return [template.render(domain=domain_name) for domain_name in self.inputs.domain_names]

    @AntaTest.anta_test
    def test(self) -> None:
        """Main test function for VerifyDNSLookup."""
        self.result.is_success()
        failed_domains = []
        for command in self.instance_commands:
            domain = command.params.domain
            output = command.json_output["messages"][0]
            if f"Can't find {domain}: No answer" in output:
                failed_domains.append(domain)
        if failed_domains:
            self.result.is_failure(f"The following domain(s) are not resolved to an IP address: {', '.join(failed_domains)}")


class VerifyDNSServers(AntaTest):
    """Verifies if the DNS (Domain Name Service) servers are correctly configured.

    Expected Results
    ----------------
    * Success: The test will pass if the DNS server specified in the input is configured with the correct VRF and priority.
    * Failure: The test will fail if the DNS server is not configured or if the VRF and priority of the DNS server do not match the input.

    Examples
    --------
    ```yaml
    anta.tests.services:
      - VerifyDNSServers:
          dns_servers:
            - server_address: 10.14.0.1
              vrf: default
              priority: 1
            - server_address: 10.14.0.11
              vrf: MGMT
              priority: 0
    ```
    """

    name = "VerifyDNSServers"
    description = "Verifies if the DNS servers are correctly configured."
    categories: ClassVar[list[str]] = ["services"]
    commands: ClassVar[list[AntaCommand | AntaTemplate]] = [AntaCommand(command="show ip name-server", revision=1)]

    class Input(AntaTest.Input):
        """Input model for the VerifyDNSServers test."""

        dns_servers: list[DnsServer]
        """List of DNS servers to verify."""

        class DnsServer(BaseModel):
            """Model for a DNS server."""

            server_address: IPv4Address | IPv6Address
            """The IPv4/IPv6 address of the DNS server."""
            vrf: str = "default"
            """The VRF for the DNS server. Defaults to 'default' if not provided."""
            priority: int = Field(ge=0, le=4)
            """The priority of the DNS server from 0 to 4, lower is first."""

    @AntaTest.anta_test
    def test(self) -> None:
        """Main test function for VerifyDNSServers."""
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


class VerifyErrdisableRecovery(AntaTest):
    """Verifies the errdisable recovery reason, status, and interval.

    Expected Results
    ----------------
    * Success: The test will pass if the errdisable recovery reason status is enabled and the interval matches the input.
    * Failure: The test will fail if the errdisable recovery reason is not found, the status is not enabled, or the interval does not match the input.

    Examples
    --------
    ```yaml
    anta.tests.services:
      - VerifyErrdisableRecovery:
          reasons:
            - reason: acl
              interval: 30
            - reason: bpduguard
              interval: 30
    ```
    """

    name = "VerifyErrdisableRecovery"
    description = "Verifies the errdisable recovery reason, status, and interval."
    categories: ClassVar[list[str]] = ["services"]
    # NOTE: Only `text` output format is supported for this command
    commands: ClassVar[list[AntaCommand | AntaTemplate]] = [AntaCommand(command="show errdisable recovery", ofmt="text")]

    class Input(AntaTest.Input):
        """Input model for the VerifyErrdisableRecovery test."""

        reasons: list[ErrDisableReason]
        """List of errdisable reasons."""

        class ErrDisableReason(BaseModel):
            """Model for an errdisable reason."""

            reason: ErrDisableReasons
            """Type or name of the errdisable reason."""
            interval: ErrDisableInterval
            """Interval of the reason in seconds."""

    @AntaTest.anta_test
    def test(self) -> None:
        """Main test function for VerifyErrdisableRecovery."""
        command_output = self.instance_commands[0].text_output
        self.result.is_success()
        for error_reason in self.inputs.reasons:
            input_reason = error_reason.reason
            input_interval = error_reason.interval
            reason_found = False

            # Skip header and last empty line
            lines = command_output.split("\n")[2:-1]
            for line in lines:
                # Skip empty lines
                if not line.strip():
                    continue
                # Split by first two whitespaces
                reason, status, interval = line.split(None, 2)
                if reason != input_reason:
                    continue
                reason_found = True
                actual_reason_data = {"interval": interval, "status": status}
                expected_reason_data = {"interval": str(input_interval), "status": "Enabled"}
                if actual_reason_data != expected_reason_data:
                    failed_log = get_failed_logs(expected_reason_data, actual_reason_data)
                    self.result.is_failure(f"`{input_reason}`:{failed_log}\n")
                break

            if not reason_found:
                self.result.is_failure(f"`{input_reason}`: Not found.\n")
