# Copyright (c) 2023-2025 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Module related to the device configuration tests."""

# Mypy does not understand AntaTest.Input typing
# mypy: disable-error-code=attr-defined
from __future__ import annotations

import re
from typing import TYPE_CHECKING, ClassVar

from pydantic import Field, model_validator

from anta.custom_types import RegexString
from anta.input_models.configuration import RunningConfigSection
from anta.models import AntaCommand, AntaTemplate, AntaTest

if TYPE_CHECKING:
    import sys

    if sys.version_info >= (3, 11):
        from typing import Self
    else:
        from typing_extensions import Self


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
          sections:
            - section: router bgp
              regex_patterns:
                - neighbor 10.111.1.0 peer group SPINE
                - router-id 10.111.254.1
            - section: ^interface ethernet1$
              regex_patterns:
                - switchport mode trunk
          regex_patterns:
            - "^enable password.*$"
            - "bla bla"
    ```
    """

    categories: ClassVar[list[str]] = ["configuration"]
    commands: ClassVar[list[AntaCommand | AntaTemplate]] = [AntaCommand(command="show running-config", ofmt="text")]

    class Input(AntaTest.Input):
        """Input model for the VerifyRunningConfigLines test."""

        sections: list[RunningConfigSection] = Field(default=[])
        """A list of unique regex sections and their corresponding regular expressions. Each pattern is validated only within its specific configuration section.

         For accurate results, the section field must be unique and clearly defined.

         Example:
          1. section: router bgp 65101, regex_patterns: router-id 10.111.254.1
          2. section: ^router isis 1$ regex_patterns: address-family ipv4 unicast
          """
        regex_patterns: list[RegexString] = Field(default=[])
        """A list of regular expressions validated across the entire running configuration."""

        @model_validator(mode="after")
        def validate_inputs(self) -> Self:
            """Validate the inputs provided to the VerifyRunningConfigLines test.

            Either `sections` or `regex_patterns` can be provided at the same time.
            """
            if not self.sections and not self.regex_patterns:
                msg = "'sections' or 'regex_patterns' must be provided"
                raise ValueError(msg)
            return self

    @AntaTest.anta_test
    def test(self) -> None:
        """Main test function for VerifyRunningConfigLines."""
        self.result.is_success()
        # If regex patterns are provided, matching configurations will be searched throughout the entire running configuration.
        for pattern in self.inputs.regex_patterns:
            re_search = re.compile(pattern, re.IGNORECASE | re.MULTILINE)
            if not re_search.search(self.instance_commands[0].text_output):
                self.result.is_failure(f"Regex pattern: {pattern} - Not found")
        # If sections are specified, matching configurations will be searched only within their respective configuration sections.
        for section in self.inputs.sections:
            # Matches a section starting with section matcher, capturing everything until the next section or end of file.
            pattern_to_search = rf"({section.section}[\s\S]+?)(?=\n(?:\S.*|\Z))"
            # Collects exact matches for the specified section matcher.
            matched_entries = re.findall(pattern_to_search, self.instance_commands[0].text_output, re.IGNORECASE | re.MULTILINE)
            for match_pattern in section.regex_patterns:
                # Verifies expected regex patterns in the section matcher.
                match_found = any(re.search(match_pattern, item) for item in matched_entries)
                if not match_found:
                    self.result.is_failure(f"Section: {section.section} Regex pattern: {match_pattern} - Not found")
