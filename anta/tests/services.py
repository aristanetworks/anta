# Copyright (c) 2023-2025 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Module related to the EOS various services tests."""

from __future__ import annotations

# Pyright does not understand AntaTest.Input typing
# pyright: reportAttributeAccessIssue=false
from typing import ClassVar

from anta.input_models.services import DnsServer, ErrDisableReason, ErrdisableRecovery
from anta.models import AntaCommand, AntaTemplate, AntaTest
from anta.tools import get_dict_superset, get_item


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
            self.result.is_failure(f"Incorrect Hostname - Expected: {self.inputs.hostname} Actual: {hostname}")
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
    """Verifies the error disable recovery functionality.

    This test performs the following checks for each specified error disable reason:

      1. Verifying if the specified error disable reason exists.
      2. Checking if the recovery timer status matches the expected enabled/disabled state.
      3. Validating that the timer interval matches the configured value.

    Expected Results
    ----------------
    * Success: The test will pass if:
        - The specified error disable reason exists.
        - The recovery timer status matches the expected state.
        - The timer interval matches the configured value.
    * Failure: The test will fail if:
        - The specified error disable reason does not exist.
        - The recovery timer status does not match the expected state.
        - The timer interval does not match the configured value.

    Examples
    --------
    ```yaml
    anta.tests.services:
      - VerifyErrdisableRecovery:
          reasons:
            - reason: acl
              interval: 30
              status: Enabled
            - reason: bpduguard
              interval: 30
              status: Enabled
    ```
    """

    categories: ClassVar[list[str]] = ["services"]
    # NOTE: Only `text` output format is supported for this command
    commands: ClassVar[list[AntaCommand | AntaTemplate]] = [AntaCommand(command="show errdisable recovery", ofmt="text")]

    class Input(AntaTest.Input):
        """Input model for the VerifyErrdisableRecovery test."""

        reasons: list[ErrdisableRecovery]
        """List of errdisable reasons."""
        ErrDisableReason: ClassVar[type[ErrdisableRecovery]] = ErrDisableReason

    @AntaTest.anta_test
    def test(self) -> None:
        """Main test function for VerifyErrdisableRecovery."""
        self.result.is_success()

        # Skip header and last empty line
        command_output = self.instance_commands[0].text_output.split("\n")[2:-1]

        # Collecting the actual errdisable reasons for faster lookup
        errdisable_reasons = [
            {"reason": reason, "status": status, "interval": interval}
            for line in command_output
            if line.strip()  # Skip empty lines
            for reason, status, interval in [line.split(None, 2)]  # Unpack split result
        ]

        for error_reason in self.inputs.reasons:
            if not (reason_output := get_item(errdisable_reasons, "reason", error_reason.reason)):
                self.result.is_failure(f"{error_reason} - Not found")
                continue

            if (act_interval := reason_output["interval"]) == "N/A":
                self.result.is_failure(f"{error_reason} - Interval is not configurable")
                continue

            if error_reason.status != (act_status := reason_output["status"]):
                self.result.is_failure(f"Reason: {error_reason.reason} - Invalid status - Expected: {error_reason.status} Actual: {act_status}")

            if error_reason.interval != int(act_interval):
                self.result.is_failure(
                    f"Reason: {error_reason.reason} - Incorrect interval - Expected: {error_reason.interval} second(s) Actual: {act_interval} second(s)"
                )
