# Copyright (c) 2023-2024 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Test functions related to LANZ"""

from __future__ import annotations

from typing import TYPE_CHECKING, ClassVar

from anta.decorators import skip_on_platforms
from anta.models import AntaCommand, AntaTest

if TYPE_CHECKING:
    from anta.models import AntaTemplate

class VerifyLANZ(AntaTest):
    """Verifies if LANZ is enabled

    Expected results:
        * Success: the test will pass if lanz is enabled
        * Failure: the test will fail if lanz is disabled
    """

    name = "VerifyLANZ"
    description = "Verifies if LANZ is enabled."
    categories: ClassVar[list[str]] = ["lanz"]
    commands: ClassVar[list[AntaCommand | AntaTemplate]] = [AntaCommand(command="show queue-monitor length status")]

    @skip_on_platforms(["cEOSLab", "vEOS-lab"])
    @AntaTest.anta_test
    def test(self) -> None:
        command_output = self.instance_commands[0].json_output

        if command_output["lanzEnabled"] is not True:
            self.result.is_failure("LANZ is not enabled")
        else:
            self.result.is_success("LANZ is enabled")
