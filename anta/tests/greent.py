# Copyright (c) 2023-2024 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Test functions related to GreenT (Postcard Telemetry) in EOS"""

from __future__ import annotations

from typing import TYPE_CHECKING, ClassVar

from anta.models import AntaCommand, AntaTest

if TYPE_CHECKING:
    from anta.models import AntaTemplate


class VerifyGreenTCounters(AntaTest):
    """Verifies whether GRE packets are sent.

    Expected Results:
        * Success: if >0 gre packets are sent
        * Failure: if no gre packets are sent
    """

    name = "VerifyGreenTCounters"
    description = "Verifies if the greent counters are incremented."
    categories: ClassVar[list[str]] = ["greent"]
    commands: ClassVar[list[AntaCommand | AntaTemplate]] = [AntaCommand(command="show monitor telemetry postcard counters")]

    @AntaTest.anta_test
    def test(self) -> None:
        command_output = self.instance_commands[0].json_output

        if command_output["grePktSent"] > 0:
            self.result.is_success()
        else:
            self.result.is_failure("GRE packets are not sent")


class VerifyGreenT(AntaTest):
    """Verifies whether GreenT policy is created.

    Expected Results:
        * Success: if there exists any policy other than "default" policy.
        * Failure: if no policy is created.
    """

    name = "VerifyGreenT"
    description = "Verifies whether greent policy is created."
    categories: ClassVar[list[str]] = ["greent"]
    commands: ClassVar[list[AntaCommand | AntaTemplate]] = [AntaCommand(command="show monitor telemetry postcard policy profile")]

    @AntaTest.anta_test
    def test(self) -> None:
        command_output = self.instance_commands[0].json_output

        out = [f"{i} policy is created" for i in command_output["profiles"].keys() if "default" not in i]

        if len(out) > 0:
            for i in out:
                self.result.is_success(f"{i} policy is created")
        else:
            self.result.is_failure("policy is not created")
