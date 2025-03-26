# Copyright (c) 2023-2025 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Module related to LANZ tests."""

from __future__ import annotations

from typing import TYPE_CHECKING, ClassVar

from anta.decorators import skip_on_platforms
from anta.models import AntaCommand, AntaTest

if TYPE_CHECKING:
    from anta.models import AntaTemplate


class VerifyLANZ(AntaTest):
    """Verifies if LANZ (Latency Analyzer) is enabled.

    Expected Results
    ----------------
    * Success: The test will pass if LANZ is enabled.
    * Failure: The test will fail if LANZ is disabled.

    Examples
    --------
    ```yaml
    anta.tests.lanz:
      - VerifyLANZ:
    ```
    """

    description = "Verifies if LANZ is enabled."
    categories: ClassVar[list[str]] = ["lanz"]
    commands: ClassVar[list[AntaCommand | AntaTemplate]] = [AntaCommand(command="show queue-monitor length status", revision=1)]

    @skip_on_platforms(["cEOSLab", "vEOS-lab", "cEOSCloudLab", "vEOS"])
    @AntaTest.anta_test
    def test(self) -> None:
        """Main test function for VerifyLANZ."""
        command_output = self.instance_commands[0].json_output

        if command_output["lanzEnabled"] is not True:
            self.result.is_failure("LANZ is not enabled")
        else:
            self.result.is_success()
