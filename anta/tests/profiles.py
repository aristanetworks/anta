# Copyright (c) 2023 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""
Test functions related to ASIC profiles
"""
# Mypy does not understand AntaTest.Input typing
# mypy: disable-error-code=attr-defined
from __future__ import annotations

from typing import Literal

from anta.decorators import skip_on_platforms
from anta.models import AntaCommand, AntaTest


class VerifyUnifiedForwardingTableMode(AntaTest):
    """
    Verifies the device is using the expected Unified Forwarding Table mode.
    """

    name = "VerifyUnifiedForwardingTableMode"
    description = ""
    categories = ["profiles"]
    commands = [AntaCommand(command="show platform trident forwarding-table partition", ofmt="json")]

    class Input(AntaTest.Input):  # pylint: disable=missing-class-docstring
        mode: Literal[0, 1, 2, 3, 4, "flexible"]
        """Expected UFT mode"""

    @skip_on_platforms(["cEOSLab", "vEOS-lab"])
    @AntaTest.anta_test
    def test(self) -> None:
        command_output = self.instance_commands[0].json_output
        if command_output["uftMode"] == str(self.inputs.mode):
            self.result.is_success()
        else:
            self.result.is_failure(f"Device is not running correct UFT mode (expected: {self.inputs.mode} / running: {command_output['uftMode']})")


class VerifyTcamProfile(AntaTest):
    """
    Verifies the device is using the configured TCAM profile.
    """

    name = "VerifyTcamProfile"
    description = "Verify that the assigned TCAM profile is actually running on the device"
    categories = ["profiles"]
    commands = [AntaCommand(command="show hardware tcam profile", ofmt="json")]

    class Input(AntaTest.Input):  # pylint: disable=missing-class-docstring
        profile: str
        """Expected TCAM profile"""

    @skip_on_platforms(["cEOSLab", "vEOS-lab"])
    @AntaTest.anta_test
    def test(self) -> None:
        command_output = self.instance_commands[0].json_output
        if command_output["pmfProfiles"]["FixedSystem"]["status"] == command_output["pmfProfiles"]["FixedSystem"]["config"] == self.inputs.profile:
            self.result.is_success()
        else:
            self.result.is_failure(f"Incorrect profile running on device: {command_output['pmfProfiles']['FixedSystem']['status']}")
