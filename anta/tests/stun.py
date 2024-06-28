# Copyright (c) 2023-2024 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Test functions related to various STUN settings."""

# Mypy does not understand AntaTest.Input typing
# mypy: disable-error-code=attr-defined
from __future__ import annotations

from ipaddress import IPv4Address
from typing import ClassVar

from pydantic import BaseModel

from anta.custom_types import Port
from anta.models import AntaCommand, AntaTemplate, AntaTest
from anta.tools import get_failed_logs, get_value


class VerifyStunClient(AntaTest):
    """
    Verifies the configuration of the STUN client, specifically the IPv4 source address and port.

    Optionally, it can also verify the public address and port.

    Expected Results
    ----------------
    * Success: The test will pass if the STUN client is correctly configured with the specified IPv4 source address/port and public address/port.
    * Failure: The test will fail if the STUN client is not configured or if the IPv4 source address, public address, or port details are incorrect.

    Examples
    --------
    ```yaml
    anta.tests.stun:
      - VerifyStunClient:
          stun_clients:
            - source_address: 172.18.3.2
              public_address: 172.18.3.21
              source_port: 4500
              public_port: 6006
            - source_address: 100.64.3.2
              public_address: 100.64.3.21
              source_port: 4500
              public_port: 6006
    ```
    """

    name = "VerifyStunClient"
    description = "Verifies the STUN client is configured with the specified IPv4 source address and port. Validate the public IP and port if provided."
    categories: ClassVar[list[str]] = ["stun"]
    commands: ClassVar[list[AntaCommand | AntaTemplate]] = [AntaTemplate(template="show stun client translations {source_address} {source_port}")]

    class Input(AntaTest.Input):
        """Input model for the VerifyStunClient test."""

        stun_clients: list[ClientAddress]

        class ClientAddress(BaseModel):
            """Source and public address/port details of STUN client."""

            source_address: IPv4Address
            """IPv4 source address of STUN client."""
            source_port: Port = 4500
            """Source port number for STUN client."""
            public_address: IPv4Address | None = None
            """Optional IPv4 public address of STUN client."""
            public_port: Port | None = None
            """Optional public port number for STUN client."""

    def render(self, template: AntaTemplate) -> list[AntaCommand]:
        """Render the template for each STUN translation."""
        return [template.render(source_address=client.source_address, source_port=client.source_port) for client in self.inputs.stun_clients]

    @AntaTest.anta_test
    def test(self) -> None:
        """Main test function for VerifyStunClient."""
        self.result.is_success()

        # Iterate over each command output and corresponding client input
        for command, client_input in zip(self.instance_commands, self.inputs.stun_clients):
            bindings = command.json_output["bindings"]
            source_address = str(command.params.source_address)
            source_port = command.params.source_port

            # If no bindings are found for the STUN client, mark the test as a failure and continue with the next client
            if not bindings:
                self.result.is_failure(f"STUN client transaction for source `{source_address}:{source_port}` is not found.")
                continue

            # Extract the public address and port from the client input
            public_address = client_input.public_address
            public_port = client_input.public_port

            # Extract the transaction ID from the bindings
            transaction_id = next(iter(bindings.keys()))

            # Prepare the actual and expected STUN data for comparison
            actual_stun_data = {
                "source ip": get_value(bindings, f"{transaction_id}.sourceAddress.ip"),
                "source port": get_value(bindings, f"{transaction_id}.sourceAddress.port"),
            }
            expected_stun_data = {"source ip": source_address, "source port": source_port}

            # If public address is provided, add it to the actual and expected STUN data
            if public_address is not None:
                actual_stun_data["public ip"] = get_value(bindings, f"{transaction_id}.publicAddress.ip")
                expected_stun_data["public ip"] = str(public_address)

            # If public port is provided, add it to the actual and expected STUN data
            if public_port is not None:
                actual_stun_data["public port"] = get_value(bindings, f"{transaction_id}.publicAddress.port")
                expected_stun_data["public port"] = public_port

            # If the actual STUN data does not match the expected STUN data, mark the test as failure
            if actual_stun_data != expected_stun_data:
                failed_log = get_failed_logs(expected_stun_data, actual_stun_data)
                self.result.is_failure(f"For STUN source `{source_address}:{source_port}`:{failed_log}")


class VerifyStunServer(AntaTest):
    """
    Verifies the STUN server status is enabled and running.

    Expected Results
    ----------------
    * Success: The test will pass if the STUN server status is enabled and running.
    * Failure: The test will fail if the STUN server is disabled or not running.

    Examples
    --------
    ```yaml
    anta.tests.stun:
      - VerifyStunServer:
    ```
    """

    name = "VerifyStunServer"
    description = "Verifies the STUN server status is enabled and running."
    categories: ClassVar[list[str]] = ["stun"]
    commands: ClassVar[list[AntaCommand | AntaTemplate]] = [AntaCommand(command="show stun server status", revision=1)]

    @AntaTest.anta_test
    def test(self) -> None:
        """Main test function for VerifyStunServer."""
        command_output = self.instance_commands[0].json_output
        status_disabled = not command_output.get("enabled")
        not_running = command_output.get("pid") == 0

        if status_disabled and not_running:
            self.result.is_failure("STUN server status is disabled and not running.")
        elif status_disabled:
            self.result.is_failure("STUN server status is disabled.")
        elif not_running:
            self.result.is_failure("STUN server is not running.")
        else:
            self.result.is_success()
