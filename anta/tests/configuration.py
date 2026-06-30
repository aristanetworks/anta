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
from anta.decorators import deprecated_test_class
from anta.input_models.configuration import ConfigEntry, ConfigRule
from anta.models import AntaCommand, AntaTemplate, AntaTest
from anta.result_manager.models import AntaTestStatus

if TYPE_CHECKING:
    from typing import Any

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


@deprecated_test_class(new_tests=["VerifyRunningConfig"], removal_in_version="v2.0.0")
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


class VerifyRunningConfig(AntaTest):
    r"""Verifies the running-config against a set of rules.

    This test supports exact, substring, and regex matching with optional numeric threshold comparisons.
    See the examples below for the full range of supported use cases.

    !!! warning
        **PREVIEW**: Input models and behavior may change between minor releases without a deprecation notice.

    Expected Results
    ----------------
    * Success: The test will pass if all rules pass validation.
    * Failure: The test will fail if any rule does not pass validation.

    Examples
    --------
    ```yaml
    anta.tests.configuration:
      - VerifyRunningConfig:
          rules:
            # Top-level: exact command must be present
            - entries:
                - match: "aaa authorization exec default local"
                  description: "AAA authorization"

            # Top-level: exact command must be absent
            - entries:
                - match: "enable password"
                  mode: exact
                  absent: true
                  description: "No static enable password"

            # Section: contains mode and regex+threshold
            - section: ["router bgp 65101"]
              entries:
                - match: "router-id"
                  mode: contains
                  description: "BGP router-id"
                - match: 'maximum-paths (\d+)'
                  mode: regex
                  description: "BGP ECMP paths"
                  threshold:
                    value: 4
                    operator: ge

            # Nested section
            - section: ["management api http-commands", "vrf MGMT"]
              entries:
                - match: "no shutdown"
                  description: "eAPI enabled in MGMT VRF"

            # Wildcard section — one atomic result per matched interface
            - section: ["interface Ethernet\\d+"]
              entries:
                - match: "description"
                  mode: contains
                  description: "Interface description"
    ```
    """

    categories: ClassVar[list[str]] = ["configuration"]
    commands: ClassVar[list[AntaCommand | AntaTemplate]] = [AntaCommand(command="show running-config", revision=1)]
    _atomic_support: ClassVar[bool] = True

    class Input(AntaTest.Input):
        """Input model for the VerifyRunningConfig test."""

        rules: list[ConfigRule]
        """List of rules to validate. Each rule defines an optional section scope and the entries to verify."""

    @AntaTest.anta_test
    def test(self) -> None:
        """Main test function for VerifyRunningConfig."""
        self.result.is_success()
        output = self.instance_commands[0].json_output["cmds"]
        top_level_cmds = list(output.keys())

        for rule in self.inputs.rules:
            if rule.section is None:
                self._validate_rule(rule, cmds=top_level_cmds, section_path=None)
            else:
                resolved_sections = self._resolve_section_path(output, rule.section)
                if not resolved_sections:
                    # Section missing — one failure atomic is enough; no entries to validate.
                    description = f"Section '{' > '.join(rule.section)}'"
                    self.result.add(description=description).is_failure("Not found in the running-config")
                    continue
                for section_path, cmds in resolved_sections.items():
                    self._validate_rule(rule, cmds=cmds, section_path=section_path)

    def _resolve_section_path(self, config: dict[str, Any], section_patterns: list[str]) -> dict[str, list[str]]:
        """Resolve a section path against the running-config tree.

        Navigates the config tree level by level. Each pattern is matched by exact key lookup first;
        if no exact key exists, `re.fullmatch` is applied against all keys at that level.

        Returns a mapping of resolved path to command list. An empty dict means no section matched.
        """
        pattern, *remaining = section_patterns

        if pattern in config and isinstance(config[pattern], dict):
            # Exact key found; EOS nests sub-commands under a "cmds" key.
            matches = [(pattern, config[pattern].get("cmds", {}))]
        else:
            # Regex fallback; re.fullmatch prevents "Ethernet1" from partially matching "Ethernet11".
            matches = [(key, node.get("cmds", {})) for key, node in config.items() if isinstance(node, dict) and re.fullmatch(pattern, key)]

        results: dict[str, list[str]] = {}
        for key, sub_config in matches:
            if not remaining:
                # Last pattern — we've reached the leaf; collect the commands.
                results[key] = list(sub_config.keys())
            else:
                # More patterns to resolve — recurse deeper and join the paths.
                for child_path, child_cmds in self._resolve_section_path(sub_config, remaining).items():
                    results[f"{key} > {child_path}"] = child_cmds
        return results

    def _validate_rule(self, rule: ConfigRule, cmds: list[str], *, section_path: str | None) -> None:
        """Validate all entries of a rule."""
        for entry in rule.entries:
            description = entry.build_description(section_path)
            atomic_result = self.result.add(description=description, status=AntaTestStatus.SUCCESS)
            self._validate_entry(entry, cmds, atomic_result)

    def _validate_entry(self, entry: ConfigEntry, cmds: list[str], atomic_result: AtomicTestResult) -> None:
        """Validate a single entry against the resolved command list."""
        matched = entry.matches(cmds)

        # Entry must be present but wasn't found.
        if not entry.absent and not matched:
            atomic_result.is_failure("Not found")
            return

        # Entry must be absent but was found.
        if entry.absent and matched:
            atomic_result.is_failure("Expected to not match" if entry.mode == "regex" else "Expected to be absent")
            return

        # No threshold to validate.
        if entry.threshold is None:
            return

        # Threshold validation — re-run regex to extract the capture group value.
        for cmd in matched:
            match_obj = re.search(entry.match, cmd)
            if match_obj and match_obj.groups():
                try:
                    captured = int(match_obj.group(1))
                except (ValueError, TypeError):
                    atomic_result.is_failure(f"Captured value '{match_obj.group(1)}' is not an integer")
                    continue
                if not entry.threshold.evaluate(captured):
                    atomic_result.is_failure(f"Actual: {captured}")
