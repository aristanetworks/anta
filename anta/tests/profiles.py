# Copyright (c) 2023-2024 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Module related to ASIC profile tests."""

# Mypy does not understand AntaTest.Input typing
# mypy: disable-error-code=attr-defined
from __future__ import annotations

from typing import TYPE_CHECKING, ClassVar, Literal

from anta.decorators import skip_on_platforms
from anta.models import AntaCommand, AntaTest

if TYPE_CHECKING:
    from anta.models import AntaTemplate


class VerifyUnifiedForwardingTableMode(AntaTest):
    """Verifies the device is using the expected UFT (Unified Forwarding Table) mode.

    Expected Results
    ----------------
    * Success: The test will pass if the device is using the expected UFT mode.
    * Failure: The test will fail if the device is not using the expected UFT mode.

    Examples
    --------
    ```yaml
    anta.tests.profiles:
      - VerifyUnifiedForwardingTableMode:
          mode: 3
    ```
    """

    name = "VerifyUnifiedForwardingTableMode"
    description = "Verifies the device is using the expected UFT mode."
    categories: ClassVar[list[str]] = ["profiles"]
    commands: ClassVar[list[AntaCommand | AntaTemplate]] = [AntaCommand(command="show platform trident forwarding-table partition", revision=1)]

    class Input(AntaTest.Input):
        """Input model for the VerifyUnifiedForwardingTableMode test."""

        mode: Literal[0, 1, 2, 3, 4, "flexible"]
        """Expected UFT mode. Valid values are 0, 1, 2, 3, 4, or "flexible"."""

    @skip_on_platforms(["cEOSLab", "vEOS-lab", "cEOSCloudLab"])
    @AntaTest.anta_test
    def test(self) -> None:
        """Main test function for VerifyUnifiedForwardingTableMode."""
        command_output = self.instance_commands[0].json_output
        if command_output["uftMode"] == str(self.inputs.mode):
            self.result.is_success()
        else:
            self.result.is_failure(f"Device is not running correct UFT mode (expected: {self.inputs.mode} / running: {command_output['uftMode']})")


class VerifyTcamProfile(AntaTest):
    """Verifies that the device is using the provided Ternary Content-Addressable Memory (TCAM) profile.

    Expected Results
    ----------------
    * Success: The test will pass if the provided TCAM profile is actually running on the device.
    * Failure: The test will fail if the provided TCAM profile is not running on the device.

    Examples
    --------
    ```yaml
    anta.tests.profiles:
      - VerifyTcamProfile:
          profile: vxlan-routing
    ```
    """

    name = "VerifyTcamProfile"
    description = "Verifies the device TCAM profile."
    categories: ClassVar[list[str]] = ["profiles"]
    commands: ClassVar[list[AntaCommand | AntaTemplate]] = [AntaCommand(command="show hardware tcam profile", revision=1)]

    class Input(AntaTest.Input):
        """Input model for the VerifyTcamProfile test."""

        profile: str
        """Expected TCAM profile."""

    @skip_on_platforms(["cEOSLab", "vEOS-lab", "cEOSCloudLab"])
    @AntaTest.anta_test
    def test(self) -> None:
        """Main test function for VerifyTcamProfile."""
        command_output = self.instance_commands[0].json_output
        if command_output["pmfProfiles"]["FixedSystem"]["status"] == command_output["pmfProfiles"]["FixedSystem"]["config"] == self.inputs.profile:
            self.result.is_success()
        else:
            self.result.is_failure(f"Incorrect profile running on device: {command_output['pmfProfiles']['FixedSystem']['status']}")
