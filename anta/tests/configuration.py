# Copyright (c) 2023-2026 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Module related to the device configuration tests."""

# Pyright does not understand AntaTest.Input typing
# pyright: reportAttributeAccessIssue=false
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
    """Verifies the given regular expression patterns are present in the running-config.

    This test can search for patterns across the entire running-config or within specific
    configuration sections.

    !!! warning
        Since this uses regular expression searches, it can impact performance.
        Prefer more specific ANTA tests when available.

    Expected Results
    ----------------
    * Success: The test will pass if all specified patterns are found.
    * Failure: The test will fail if any pattern is not found.

    Examples
    --------
    ```yaml
    anta.tests.configuration:
      - VerifyRunningConfigLines:
          # Search for patterns only within specific running-config sections
          sections:
            - section: router bgp 65101
              regex_patterns:
                - neighbor 10.111.1.0 peer group SPINE
                - router-id 10.111.254.1
            - section: interface Ethernet1
              regex_patterns:
                - switchport mode trunk
          # Search for patterns across the entire running-config
          regex_patterns:
            - "^enable password.*$"
    ```
    """

    categories: ClassVar[list[str]] = ["configuration"]
    commands: ClassVar[list[AntaCommand | AntaTemplate]] = [AntaCommand(command="show running-config", ofmt="text")]

    class Input(AntaTest.Input):
        """Input model for the VerifyRunningConfigLines test."""

        sections: list[RunningConfigSection] | None = None
        """A list of running-config sections to search within. Each item defines a unique section and the patterns to find within it."""
        regex_patterns: list[RegexString] | None = None
        """A list of regex patterns to search for across the entire running-config."""

        @model_validator(mode="after")
        def validate_inputs(self) -> Self:
            """Validate the inputs provided to the VerifyRunningConfigLines test.

            At least one of `sections` or `regex_patterns` must be provided.
            """
            if not self.sections and not self.regex_patterns:
                msg = "'sections' or 'regex_patterns' must be provided"
                raise ValueError(msg)
            return self

    @AntaTest.anta_test
    def test(self) -> None:
        """Main test function for VerifyRunningConfigLines."""
        self.result.is_success()
        output = self.instance_commands[0].text_output
        # Global running-config pattern search
        if self.inputs.regex_patterns:
            for pattern in self.inputs.regex_patterns:
                self._validate_pattern_in_running_configs(pattern, output)

        # If sections are specified, matching configurations will be searched only within their respective configuration sections
        if self.inputs.sections:
            for section in self.inputs.sections:
                # Matches a section starting with section matcher, capturing everything until the next section or end of file
                pattern_to_search = rf"^{section.section}$([\s\S]*?)(?=\n\S|\Z)"
                # Collects exact matches for the specified section matcher
                matched_blocks = re.findall(pattern_to_search, output, re.IGNORECASE | re.MULTILINE)
                if not matched_blocks:
                    self.result.is_failure(f"Section: `{section.section}`: Not found")
                    continue
                if len(matched_blocks) > 1:
                    self.result.is_failure(f"Section: `{section.section}`: Found multiple matches ({len(matched_blocks)})")
                    continue

                # We have a unique section block to search within
                section_content = matched_blocks[0]
                for pattern in section.regex_patterns:
                    failure_msg_prefix = f"Section: `{section.section}` "
                    self._validate_pattern_in_running_configs(pattern, section_content, failure_msg_prefix)

    def _validate_pattern_in_running_configs(self, pattern: str, running_config_details: str, failure_msg_prefix: str = "") -> None:
        """Validate the provided pattern in the running configs."""
        regex_patern = pattern
        # If multiline regex pattern or nested pattern validation inside a section
        if "\n" in pattern:
            pattern_lines = pattern.strip().splitlines()
            # Build regex that tolerates any whitespace between lines
            regex_patern = "".join(r"\s*" + re.escape(line.strip()) for line in pattern_lines)

        if not re.search(regex_patern, running_config_details, re.IGNORECASE | re.MULTILINE | re.DOTALL):
            self.result.is_failure(f"{failure_msg_prefix}RegEx pattern: `{pattern}` - Not found")
