# Copyright (c) 2023-2026 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Module related to the device configuration tests."""

# Pyright does not understand AntaTest.Input typing
# pyright: reportAttributeAccessIssue=false
from __future__ import annotations

import re
from typing import TYPE_CHECKING, ClassVar

from anta.custom_types import RegexString
from anta.input_models.configuration import ConfigEntries, RunningConfigSection
from anta.models import AntaCommand, AntaTemplate, AntaTest
from anta.result_manager.models import AntaTestStatus
from anta.tools import get_value

if TYPE_CHECKING:
    from anta.result_manager.models import AtomicTestResult


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
          regex_patterns:
            - "^enable password.*$"
            - "bla bla"
    ```
    """

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
            self.result.is_failure("Following patterns were not found: " + ", ".join(failure_msgs))


class VerifyRunningConfigs(AntaTest):
    """Verifies running-config entries within specific configuration sections or across the entire running-configuration.

    Each entry in `configs` either targets a named configuration section (identified by its first line) or,
    when `section` is omitted, validates against the top-level commands of the entire running-configuration.

    Expected Results
    ----------------
    * Success: The test will pass if all config entries satisfy their validation criteria within each specified section
      or within the entire running-configuration.
    * Failure: The test will fail if any specified section is not found or any config entry does not satisfy its validation criteria.

    Examples
    --------
    ```yaml
    anta.tests.configuration:
      - VerifyRunningConfigs:
          configs:
            # Validate entries within a specific configuration section
            - section: router bgp 65101
              description: BGP routing configuration
              config_entries:
                - search_string: router-id 10.111.254.1
                - search_string: maximum-paths
                  validation_mode: contains
                  threshold: 2  # Number to compare against extracted command value
                  threshold_operator: ge  # Comparison operator for threshold value
                  context: BGP is not configured with enough paths
            - section: interface Ethernet1
              config_entries:
                - search_string: no switchport
                  validation_mode: absent
            # Validate entries across the entire running-configuration (no section)
            - config_entries:
                - search_string: aaa authentication login default local
                - search_string: ntp
                  validation_mode: absent
                  context: NTP should not be configured on this device
    ```
    """

    categories: ClassVar[list[str]] = ["configuration"]
    commands: ClassVar[list[AntaCommand | AntaTemplate]] = [AntaCommand(command="show running-config all")]
    _atomic_support: ClassVar[bool] = True

    class Input(AntaTest.Input):
        """Input model for the VerifyRunningConfigs test."""

        configs: list[RunningConfigSection] | None = None
        """List of running-config scopes to validate. Each item defines an optional section and the config entries to verify.
        When section is omitted, config entries are validated against the entire running-configuration."""

    @staticmethod
    def _get_section_label(config: RunningConfigSection, search_string: str | None = None) -> str:
        """Return the display label for a config section."""
        if config.description:
            return config.description
        if config.section:
            return f"Section: {config.section}"
        return f"Config: {search_string}" if search_string else ""

    @AntaTest.anta_test
    def test(self) -> None:
        """Main test function for VerifyRunningConfigs."""
        self.result.is_success()
        output = self.instance_commands[0].json_output["cmds"]
        # Iterate over each section scope defined in the test inputs
        for config_section in self.inputs.configs:
            if config_section.section is None:
                section_cmds = list(output.keys())

            else:
                section_data = get_value(output, config_section.section)
                if section_data is None:
                    section_desc = self._get_section_label(config_section)
                    result = self.result.add(description=section_desc, status=AntaTestStatus.FAILURE)
                    result.is_failure("Not found in running-config")
                    continue
                section_cmds = list(section_data.get("cmds", {}).keys())
            # Validate entries against the resolved command list
            self._validate_section_entries(config_section, section_cmds)

    def _validate_section_entries(self, config_details: RunningConfigSection, section_cmds: list[str]) -> None:
        """Validate each config entry for a resolved running-config section."""
        for entry in config_details.config_entries:
            result = self.result.add(description=self._get_section_label(config_details, entry.search_string), status=AntaTestStatus.SUCCESS)
            # Run validation and record atomic result per entry
            self._validate_config_entry(entry, section_cmds, config_details.section, result)

    def _validate_config_entry(self, entry: ConfigEntries, cmds: list[str], section_str: str | None, search_string_result: AtomicTestResult) -> None:
        """Validate a single config entry against the commands found in a running-config section or the entire running-configuration."""
        failure_prefix = f"Config: {entry.search_string} - " if section_str else ""
        if entry.validation_mode == "exact_match":
            matched = [cmd for cmd in cmds if entry.search_string == cmd]
            if not matched:
                search_string_result.is_failure(entry.context or f"{failure_prefix}Not found")

        elif entry.validation_mode == "contains":
            self._validate_contains_entry(entry, cmds, failure_prefix, search_string_result)

        else:
            matched = [cmd for cmd in cmds if entry.search_string == cmd]
            if matched:
                search_string_result.is_failure(entry.context or f"{failure_prefix} Expected to be not found")

    def _validate_contains_entry(self, entry: ConfigEntries, cmds: list[str], base: str, search_string_result: AtomicTestResult) -> None:
        """Validate a contains mode config entry, including optional threshold checks."""
        matched = [cmd for cmd in cmds if entry.search_string in cmd]
        if not matched:
            search_string_result.is_failure(entry.context or f"{base}Not found")

        elif entry.threshold is not None:
            for cmd in matched:
                # Slice the string after the search keyword
                suffix = cmd[cmd.index(entry.search_string) + len(entry.search_string) :]
                # Extract all numeric values from the remaining text
                numbers = re.findall(r"\d+", suffix)
                # First numeric value after the keyword is the one compared
                if numbers and not self._check_threshold(int(numbers[0]), entry.threshold, entry.threshold_operator):
                    op_symbols = {"le": "<=", "ge": ">=", "eq": "=="}
                    search_string_result.is_failure(
                        entry.context or f"{base}{cmd} - Expected: value {op_symbols[entry.threshold_operator]} {entry.threshold} Actual: {numbers[0]}"
                    )

    def _check_threshold(self, value: int, threshold: int, operator: str) -> bool:
        """Return True if value satisfies the threshold constraint under the given operator."""
        if operator == "le":
            return value <= threshold
        if operator == "ge":
            return value >= threshold
        return value == threshold
