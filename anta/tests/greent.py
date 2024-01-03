# Copyright (c) 2023 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""
Test functions related to GreenT (Postcard Telemetry) in EOS
"""
# Mypy does not understand AntaTest.Input typing
# mypy: disable-error-code=attr-defined
from __future__ import annotations

from pydantic import conint

from anta.models import AntaCommand, AntaTest


class VerifyGreenTCounters(AntaTest):

    name = "VerifyGreenTCounters"
    description = "Verifies if the greent counters are incremented."
    categories = ["greent"]
    commands = [AntaCommand(command="show monitor telemetry postcard counters")]

    @AntaTest.anta_test
    def test(self) -> None:
        command_output = self.instance_commands[0].json_output
        grePktSent = command_output["grePktSent"]
        if command_output["grePktSent"] > 0:
            self.result.is_success()
        else:
            self.result.is_failure("GRE packets are not sent")


class VerifyGreenT(AntaTest):

    name = "VerifyGreenT"
    description = "Verifies if the greent."
    categories = ["greent"]
    commands = [AntaCommand(command="show monitor telemetry postcard policy profile")]

    

    @AntaTest.anta_test
    def test(self) -> None:
        command_output = self.instance_commands[0].json_output

        out = [f"{i} policy is created" for i in command_output['profiles'].keys() if "default" not in i]

        if len(out)>0:
            for i in out:
                self.result.is_success(f"{i} policy is created")
        else:
            self.result.is_failure("policy is not created")