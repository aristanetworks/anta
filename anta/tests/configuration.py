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
            - regex: router bgp
              regex_patterns:
                - neighbor*
                - router-id 10.111.254.1
            - regex: router ospf
              regex_patterns:
                - router-id
          regex_patterns:
            - "^enable password.*$"
            - "bla bla"

    ```
    """

    description = "Search the Running-Config for the given RegEx patterns."
    categories: ClassVar[list[str]] = ["configuration"]
    commands: ClassVar[list[AntaCommand | AntaTemplate]] = [AntaTemplate(template="show running-config{regex}", ofmt="text")]

    class Input(AntaTest.Input):
        """Input model for the VerifyRunningConfigLines test."""

        sections: list[RunningConfigSection] = Field(default=[])
        """List of regex sections."""
        regex_patterns: list[RegexString] = Field(default=[])
        """List of regular expressions."""

        @model_validator(mode="after")
        def validate_inputs(self) -> Self:
            """Validate the inputs provided to the VerifyRunningConfigLines test.

            Either `sections` or `regex_patterns` can be provided at the same time.
            """
            if not self.sections and not self.regex_patterns:
                msg = "'sections' or 'regex_patterns' must be provided"
                raise ValueError(msg)
            if self.sections and self.regex_patterns:
                msg = "Either 'sections' or 'regex_patterns' can be provided at the same time"
                raise ValueError(msg)

            # If Sections, Verifies that the regex and regex_patterns should be required.
            if self.sections:
                for section in self.sections:
                    if not section.regex_patterns:
                        msg = f"For {section} 'regex_patterns' field missing in the input"
                        raise ValueError(msg)
            return self

    def render(self, template: AntaTemplate) -> list[AntaCommand]:
        """Render the template for each host in the input list."""
        if self.inputs.sections:
            return [template.render(regex=f" section {section.regex}" if section.regex else "") for section in self.inputs.sections]
        if self.inputs.regex_patterns:
            return [template.render(regex="")]

        return []

    @AntaTest.anta_test
    def test(self) -> None:
        """Main test function for VerifyRunningConfigLines."""
        self.result.is_success()
        for output, section in zip(self.instance_commands, self.inputs.sections):
            pattern_to_search = rf"({section.regex}[\s\S]+?)(?=\n(?:\S.*|\Z))"
            stanzas = re.findall(pattern_to_search, output.text_output, flags=re.MULTILINE)
            exact_match = [item for item in stanzas if item.startswith(f"{section.regex}\n")]
            for regex_pattern in section.regex_patterns:
                match_found = any(re.search(regex_pattern, item) for item in exact_match)
                if not match_found:
                    self.result.is_failure(f"Section: {section.regex} Regex pattern: {regex_pattern} - Not found")

        if self.inputs.regex_patterns:
            for pattern in self.inputs.regex_patterns:
                re_search = re.compile(pattern, flags=re.MULTILINE)
                if not re_search.search(self.instance_commands[0].text_output):
                    self.result.is_failure(f"Regex pattern: {pattern} - Not found")
