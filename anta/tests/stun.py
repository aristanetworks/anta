# Copyright (c) 2023-2024 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""
Test functions related to various STUN settings
"""
# Mypy does not understand AntaTest.Input typing
# mypy: disable-error-code=attr-defined
from __future__ import annotations

from ipaddress import IPv4Address

# Need to keep List for pydantic in python 3.8
from typing import List, Optional

from pydantic import BaseModel

from anta.custom_types import TcpPort
from anta.models import AntaCommand, AntaTemplate, AntaTest
from anta.tools.get_value import get_value
from anta.tools.utils import get_failed_logs


class VerifyStunClient(AntaTest):
    """
    Verifies the configuration of the STUN client, specifically the IPv4 source address and port.

    Optionally, it can also verify the public address and port.

    Expected Results:
        * success: The test will pass if the STUN client is correctly configured with the specified IPv4 source address, public address, and port.
        * failure: The test will fail if the STUN client is not configured or if the IPv4 source address, public address, or port details are incorrect.
    """

    name = "VerifyStunClient"
    description = "Verifies the STUN client is configured with the specified IPv4 source address, public address, and port."
    categories = ["stun"]
    commands = [AntaTemplate(template="show stun client translations {source_address} {port}")]

    class Input(AntaTest.Input):
        """
        This class defines the inputs for the VerifyStunClient test.
        """

        stun_clients: List[ClientAddress]

        class ClientAddress(BaseModel):
            """
            Source and public address details of STUN client
            """

            source_address: IPv4Address
            """
            IPv4 source address of STUN client
            """
            public_address: Optional[IPv4Address] = None
            """
            IPV4 public address of STUN client
            """
            port: TcpPort
            """
            Port number for STUN client
            """

    def render(self, template: AntaTemplate) -> list[AntaCommand]:
        return [template.render(source_address=client.source_address, public_address=client.public_address, port=client.port) for client in self.inputs.stun_clients]

    @AntaTest.anta_test
    def test(self) -> None:
        self.result.is_success()

        for command in self.instance_commands:
            command_output = command.json_output["bindings"]
            source_address = str(command.params["source_address"])
            public_address = command.params["public_address"]
            port = command.params["port"]
            if not command_output:
                self.result.is_failure(f"STUN client transaction for source `{source_address}:{port}` is not found.")
                continue

            transaction_id = list(command_output.keys())[0]
            actual_stun_data = {
                "source ip": get_value(command_output, f"{transaction_id}.sourceAddress.ip"),
                "source port": get_value(command_output, f"{transaction_id}.sourceAddress.port"),
            }
            expected_stun_data = {"source ip": source_address, "source port": port}

            # Skip public address verification when the public address is not defined in the input
            if public_address is None:
                if actual_stun_data != expected_stun_data:
                    failed_log = get_failed_logs(expected_stun_data, actual_stun_data)
                    self.result.is_failure(f"For STUN source address {source_address}:{failed_log}")

            else:
                public_address = str(public_address)
                actual_stun_data.update(
                    {
                        "public ip": get_value(command_output, f"{transaction_id}.publicAddress.ip"),
                        "public port": get_value(command_output, f"{transaction_id}.publicAddress.port"),
                    }
                )
                expected_stun_data.update({"public ip": public_address, "public port": port})

                if actual_stun_data != expected_stun_data:
                    failed_log = get_failed_logs(expected_stun_data, actual_stun_data)
                    self.result.is_failure(f"For STUN source address {source_address}:{failed_log}")
