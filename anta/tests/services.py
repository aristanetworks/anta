# Copyright (c) 2023-2024 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""
Test functions related to the EOS various services settings
"""
from __future__ import annotations

# Mypy does not understand AntaTest.Input typing
# mypy: disable-error-code=attr-defined
from anta.models import AntaCommand, AntaTest


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
