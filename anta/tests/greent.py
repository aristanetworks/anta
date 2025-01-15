# Copyright (c) 2023-2025 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Module related to GreenT (Postcard Telemetry) tests."""

from __future__ import annotations

from typing import TYPE_CHECKING, ClassVar

from anta.models import AntaCommand, AntaTest

if TYPE_CHECKING:
    from anta.models import AntaTemplate


class VerifyGreenTCounters(AntaTest):
    """Verifies if the GreenT (GRE Encapsulated Telemetry) counters are incremented.

    Expected Results
    ----------------
    * Success: The test will pass if the GreenT counters are incremented.
    * Failure: The test will fail if the GreenT counters are not incremented.

    Examples
    --------
    ```yaml
    anta.tests.greent:
      - VerifyGreenTCounters:
    ```

    """

    description = "Verifies if the GreenT counters are incremented."
    categories: ClassVar[list[str]] = ["greent"]
    commands: ClassVar[list[AntaCommand | AntaTemplate]] = [AntaCommand(command="show monitor telemetry postcard counters", revision=1)]

    @AntaTest.anta_test
    def test(self) -> None:
        """Main test function for VerifyGreenTCounters."""
        command_output = self.instance_commands[0].json_output

        if command_output["grePktSent"] > 0:
            self.result.is_success()
        else:
            self.result.is_failure("GreenT counters are not incremented")


class VerifyGreenT(AntaTest):
    """Verifies if a GreenT (GRE Encapsulated Telemetry) policy other than the default is created.

    Expected Results
    ----------------
    * Success: The test will pass if a GreenT policy is created other than the default one.
    * Failure: The test will fail if no other GreenT policy is created.

    Examples
    --------
    ```yaml
    anta.tests.greent:
      - VerifyGreenT:
    ```

    """

    description = "Verifies if a GreenT policy other than the default is created."
    categories: ClassVar[list[str]] = ["greent"]
    commands: ClassVar[list[AntaCommand | AntaTemplate]] = [AntaCommand(command="show monitor telemetry postcard policy profile", revision=1)]

    @AntaTest.anta_test
    def test(self) -> None:
        """Main test function for VerifyGreenT."""
        command_output = self.instance_commands[0].json_output

        profiles = [profile for profile in command_output["profiles"] if profile != "default"]

        if profiles:
            self.result.is_success()
        else:
            self.result.is_failure("No GreenT policy is created")
