# Copyright (c) 2023-2025 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Module related to the EOS various services tests."""

from __future__ import annotations

# Mypy does not understand AntaTest.Input typing
# mypy: disable-error-code=attr-defined
from typing import ClassVar

from pydantic import BaseModel

from anta.custom_types import ErrDisableInterval, ErrDisableReasons
from anta.input_models.services import DnsServer
from anta.models import AntaCommand, AntaTemplate, AntaTest
from anta.tools import get_dict_superset, get_failed_logs


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

    This test performs the following checks for each specified DNS Server:

      1. Confirming correctly registered with a valid IPv4 or IPv6 address with the designated VRF.
      2. Ensuring an appropriate priority level.

    Expected Results
    ----------------
    * Success: The test will pass if the DNS server specified in the input is configured with the correct VRF and priority.
    * Failure: The test will fail if any of the following conditions are met:
        - The provided DNS server is not configured.
        - The provided DNS server with designated VRF and priority does not match the expected information.

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

    categories: ClassVar[list[str]] = ["services"]
    commands: ClassVar[list[AntaCommand | AntaTemplate]] = [AntaCommand(command="show ip name-server", revision=1)]

    class Input(AntaTest.Input):
        """Input model for the VerifyDNSServers test."""

        dns_servers: list[DnsServer]
        """List of DNS servers to verify."""
        DnsServer: ClassVar[type[DnsServer]] = DnsServer

    @AntaTest.anta_test
    def test(self) -> None:
        """Main test function for VerifyDNSServers."""
        self.result.is_success()

        command_output = self.instance_commands[0].json_output["nameServerConfigs"]
        for server in self.inputs.dns_servers:
            address = str(server.server_address)
            vrf = server.vrf
            priority = server.priority
            input_dict = {"ipAddr": address, "vrf": vrf}

            # Check if the DNS server is configured with specified VRF.
            if (output := get_dict_superset(command_output, input_dict)) is None:
                self.result.is_failure(f"{server} - Not configured")
                continue

            # Check if the DNS server priority matches with expected.
            if output["priority"] != priority:
                self.result.is_failure(f"{server} - Incorrect priority - Priority: {output['priority']}")


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
