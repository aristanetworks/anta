# Copyright (c) 2023-2024 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Module related to the device configuration tests."""

# Mypy does not understand AntaTest.Input typing
# mypy: disable-error-code=attr-defined
from __future__ import annotations

import re
from typing import TYPE_CHECKING, ClassVar

from anta.custom_types import RegexString
from anta.models import AntaCommand, AntaTest

if TYPE_CHECKING:
    from anta.models import AntaTemplate


class VerifyZeroTouch(AntaTest):
    """Verifies ZeroTouch is disabled.

    Expected Results
    ----------------
    * Success: The test will pass if ZeroTouch is disabled.
    * Failure: The test will fail if ZeroTouch is enabled.

    Examples
    --------
    ```yaml
    anta.tests.configuration:
      - VerifyZeroTouch:
    ```
    """

    name = "VerifyZeroTouch"
    description = "Verifies ZeroTouch is disabled"
    categories: ClassVar[list[str]] = ["configuration"]
    commands: ClassVar[list[AntaCommand | AntaTemplate]] = [AntaCommand(command="show zerotouch", revision=1)]

    @AntaTest.anta_test
    def test(self) -> None:
        """Main test function for VerifyZeroTouch."""
        command_output = self.instance_commands[0].json_output
        if command_output["mode"] == "disabled":
            self.result.is_success()
        else:
            self.result.is_failure("ZTP is NOT disabled")


class VerifyRunningConfigDiffs(AntaTest):
    """Verifies there is no difference between the running-config and the startup-config.

    Expected Results
    ----------------
    * Success: The test will pass if there is no difference between the running-config and the startup-config.
    * Failure: The test will fail if there is a difference between the running-config and the startup-config.

    Examples
    --------
    ```yaml
    anta.tests.configuration:
      - VerifyRunningConfigDiffs:
    ```
    """

    name = "VerifyRunningConfigDiffs"
    description = "Verifies there is no difference between the running-config and the startup-config"
    categories: ClassVar[list[str]] = ["configuration"]
    commands: ClassVar[list[AntaCommand | AntaTemplate]] = [AntaCommand(command="show running-config diffs", ofmt="text")]

    @AntaTest.anta_test
    def test(self) -> None:
        """Main test function for VerifyRunningConfigDiffs."""
        command_output = self.instance_commands[0].text_output
        if command_output == "":
            self.result.is_success()
        else:
            self.result.is_failure(command_output)


class VerifyRunningConfigLines(AntaTest):
    """Verifies the given regular expression patterns are present in the running-config.

    !!! warning
        Since this uses regular expression searches on the whole running-config, it can
        drastically impact performance and should only be used if no other test is available.

        If possible, try using another ANTA test that is more specific.

    Expected Results
    ----------------
    * Success: The test will pass if all the patterns are found in the running-config.
    * Failure: The test will fail if any of the patterns are NOT found in the running-config.

    Examples
    --------
    ```yaml
    anta.tests.configuration:
      - VerifyRunningConfigLines:
            regex_patterns:
                - "^enable password.*$"
                - "bla bla"
    ```
    """

    name = "VerifyRunningConfigLines"
    description = "Search the Running-Config for the given RegEx patterns."
    categories: ClassVar[list[str]] = ["configuration"]
    commands: ClassVar[list[AntaCommand | AntaTemplate]] = [AntaCommand(command="show running-config", ofmt="text")]

    class Input(AntaTest.Input):
        """Input model for the VerifyRunningConfigLines test."""

        regex_patterns: list[RegexString]
        """List of regular expressions."""

    @AntaTest.anta_test
    def test(self) -> None:
        """Main test function for VerifyRunningConfigLines."""
        failure_msgs = []
        command_output = self.instance_commands[0].text_output

        for pattern in self.inputs.regex_patterns:
            re_search = re.compile(pattern, flags=re.MULTILINE)

            if not re_search.search(command_output):
                failure_msgs.append(f"'{pattern}'")

        if not failure_msgs:
            self.result.is_success()
        else:
            self.result.is_failure("Following patterns were not found: " + ",".join(failure_msgs))
