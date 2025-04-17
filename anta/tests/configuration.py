# Copyright (c) 2023-2025 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Module related to the device configuration tests."""

# Mypy does not understand AntaTest.Input typing
# mypy: disable-error-code=attr-defined
from __future__ import annotations

import re
from typing import TYPE_CHECKING, ClassVar

from pydantic import model_validator

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
    """Verifies that the specified regular expression patterns or section-specific patterns are present in the running configuration.

    !!! warning
        Since this uses regular expression searches on the whole running-config, it can
        drastically impact performance and should only be used if no other test is available.

        If possible, try using another ANTA test that is more specific.
    !!! Note

        For accurate results, the section_matcher field must be unique and clearly defined.

        Example:

          1. router bgp 65101
          2. router ospf 100
          3. interface ethernet1

    Expected Results
    ----------------
    * Success: The test will pass if all specified regular expression patterns or section-specific patterns are found in the running configuration.
    * Failure: The test will fail if any of the specified regular expression patterns, or section-specific patterns, are not found in the running configuration.

    Examples
    --------
    ```yaml
    anta.tests.configuration:
      - VerifyRunningConfigLines:
          sections:
            - section_matcher: router bgp 65101
              match_patterns:
                - neighbor 10.111.1.0 peer group SPINE
                - router-id 10.111.254.1
            - section_matcher: router ospf 100
              match_patterns:
                - router-id 10.111.254.1
          regex_patterns:
            - "^enable password.*$"
            - "bla bla"
    ```
    """

    description = "Search the Running-Config for the given RegEx patterns."
    categories: ClassVar[list[str]] = ["configuration"]
    commands: ClassVar[list[AntaCommand | AntaTemplate]] = [AntaTemplate(template="show running-config{section_matcher}", ofmt="text")]

    class Input(AntaTest.Input):
        """Input model for the VerifyRunningConfigLines test."""

        sections: list[RunningConfigSection] | None = None
        """List of regex sections with unique section matchers and their corresponding regular expressions."""
        regex_patterns: list[RegexString] | None = None
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
            return self

    def render(self, template: AntaTemplate) -> list[AntaCommand]:
        """Render the template for each host in the input list."""
        if self.inputs.sections:
            return [template.render(section_matcher=f" section {section.section_matcher}") for section in self.inputs.sections]
        return [template.render(section_matcher="")]

    @AntaTest.anta_test
    def test(self) -> None:
        """Main test function for VerifyRunningConfigLines."""
        self.result.is_success()
        # If only a regex pattern is provided, the matching configurations will be searched across the entire running configuration.
        if self.inputs.regex_patterns:
            for pattern in self.inputs.regex_patterns:
                re_search = re.compile(pattern, flags=re.MULTILINE)
                if not re_search.search(self.instance_commands[0].text_output):
                    self.result.is_failure(f"Regex pattern: {pattern} - Not found")
            return
        # If a section matcher is provided, the matching configuration will be searched only within the specified section.
        for output, section in zip(self.instance_commands, self.inputs.sections):
            # Matches a section starting with section matcher, capturing everything until the next section or end of file.
            pattern_to_search = rf"({section.section_matcher}[\s\S]+?)(?=\n(?:\S.*|\Z))"
            # Collects configurations containing the specified section matcher.
            matched_entries = re.findall(pattern_to_search, output.text_output, flags=re.MULTILINE)
            # Collects exact matches for the specified section matcher.
            exact_match = [item for item in matched_entries if re.match(f"{section.section_matcher}\n", item)]
            for match_pattern in section.match_patterns:
                # Verifies expected regex patterns in the section matcher.
                match_found = any(re.search(match_pattern, item) for item in exact_match)
                if not match_found:
                    self.result.is_failure(f"Section: {section.section_matcher} Regex pattern: {match_pattern} - Not found")
