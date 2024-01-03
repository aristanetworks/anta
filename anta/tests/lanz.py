# Copyright (c) 2023 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""
Test functions related to LANZ
"""
# Mypy does not understand AntaTest.Input typing
# mypy: disable-error-code=attr-defined
from __future__ import annotations

from pydantic import conint

from anta.models import AntaCommand, AntaTest


class VerifyLANZ(AntaTest):

    name = "VerifyLANZ"
    description = "Verifies if LANZ is enabled."
    categories = ["lanz"]
    commands = [AntaCommand(command="show queue-monitor length status")]

    @AntaTest.anta_test
    def test(self) -> None:
        command_output = self.instance_commands[0].json_output

        if command_output["lanzEnabled"] != True:
            self.result.is_failure("LANZ is not enabled")
        else:
            self.result.is_success("LANZ is enabled")
