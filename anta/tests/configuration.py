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
from anta.input_models.configuration import ConfigRule, RuleEntry
from anta.models import AntaCommand, AntaTemplate, AntaTest
from anta.result_manager.models import AntaTestStatus

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
    """Verifies running-config entries within named stanzas or across the top-level running-configuration.

    Each rule targets a stanza (a list of patterns navigating the config tree) or top-level commands
    when `stanza` is omitted. Stanza patterns use exact key lookup first, falling back to regex matching.
    Wildcard patterns produce one independent atomic result per matched stanza.

    Expected Results
    ----------------
    * Success: The test will pass if all entries satisfy their validation criteria within each
      resolved stanza or across the top-level running-configuration.
    * Failure: The test will fail if any stanza is not found or any entry does not satisfy its
      validation criteria.

    Examples
    --------
    ```yaml
    anta.tests.configuration:
      - VerifyRunningConfig:
          rules:
            # Top-level: exact command must be present
            - description: AAA authorization
              entries:
                - match: "aaa authorization exec default local"
                  mode: exact
                  absent: false

            # Top-level: exact command must be absent
            - description: No static enable password
              entries:
                - match: "enable password"
                  mode: exact
                  absent: true
                  context: "Enable password must not be set in plaintext"

            # Stanza: contains mode and regex+threshold
            - stanza: ["router bgp 65101"]
              description: BGP routing configuration
              entries:
                - match: "router-id"
                  mode: contains
                  absent: false
                - match: "maximum-paths (4)"
                  mode: regex
                  absent: false
                  threshold:
                    value: 4
                    operator: ge

            # Nested stanza
            - stanza: ["management api http-commands", "vrf MGMT"]
              description: eAPI enabled in MGMT VRF
              entries:
                - match: "no shutdown"
                  mode: exact
                  absent: false

            # Wildcard stanza — one atomic result per matched interface
            - stanza: ["interface Ethernet"]
              description: Interface descriptions
              entries:
                - match: "description"
                  mode: contains
                  absent: false
                  context: "Every Ethernet interface must have a description"
    ```
    """

    categories: ClassVar[list[str]] = ["configuration"]
    commands: ClassVar[list[AntaCommand | AntaTemplate]] = [AntaCommand(command="show running-config", revision=1)]
    _atomic_support: ClassVar[bool] = True

    class Input(AntaTest.Input):
        """Input model for the VerifyRunningConfig test."""

        rules: list[ConfigRule]
        """List of rules to validate. Each rule defines an optional stanza scope and the entries to verify."""

    @AntaTest.anta_test
    def test(self) -> None:
        """Main test function for VerifyRunningConfig."""
        self.result.is_success()
        output = self.instance_commands[0].json_output["cmds"]

        for rule in self.inputs.rules:
            if rule.stanza is None:
                self._validate_rule(rule, stanza_label=None, cmds=list(output.keys()), is_wildcard=False)
            else:
                resolved = self._resolve_stanzas(output, rule.stanza)
                if not resolved:
                    stanza_desc = rule.description or f"Stanza: {' > '.join(rule.stanza)}"
                    atomic = self.result.add(description=stanza_desc, status=AntaTestStatus.FAILURE)
                    atomic.is_failure("Not found in running-config")
                    continue
                is_wildcard = len(resolved) > 1
                for stanza_label, leaf_cmds in resolved:
                    self._validate_rule(rule, stanza_label=stanza_label, cmds=list(leaf_cmds.keys()), is_wildcard=is_wildcard)

    def _resolve_stanzas(self, tree: dict, patterns: list[str]) -> list[tuple[str, dict]]:
        """Resolve stanza patterns against the running-config tree.

        Each pattern uses exact key lookup first; if no exact match, a regex pattern is
        applied against all keys at that level.
        """
        if not patterns:
            return [("", tree)]

        pattern, remaining = patterns[0], patterns[1:]
        matches: list[tuple[str, dict]] = []

        if pattern in tree and isinstance(tree[pattern], dict):
            # Exact key found — no regex needed
            matches = [(pattern, tree[pattern].get("cmds", {}))]
        else:
            # Regex fallback — collect every key that re.match accepts
            matches = [(k, v.get("cmds", {})) for k, v in tree.items() if isinstance(v, dict) and re.match(pattern, k)]

        results: list[tuple[str, dict]] = []
        for label, next_tree in matches:
            for sub_label, leaf_tree in self._resolve_stanzas(next_tree, remaining):
                # sub_label is non-empty only when remaining patterns produce a deeper path
                full_label = f"{label} > {sub_label}" if sub_label else label
                results.append((full_label, leaf_tree))
        return results

    def _entry_description(self, rule: ConfigRule, stanza_label: str | None, entry: RuleEntry, *, is_wildcard: bool) -> str:
        """Return the atomic result description for one entry."""
        if rule.description:
            return f"{rule.description} [{stanza_label}]" if is_wildcard and stanza_label else rule.description
        if stanza_label:
            return f"Stanza: {stanza_label}"
        return f"Config: {entry.match}"

    def _validate_rule(self, rule: ConfigRule, stanza_label: str | None, cmds: list[str], *, is_wildcard: bool) -> None:
        """Validate all entries for one resolved stanza."""
        for entry in rule.entries:
            desc = self._entry_description(rule, stanza_label, entry, is_wildcard=is_wildcard)
            atomic = self.result.add(description=desc, status=AntaTestStatus.SUCCESS)
            self._validate_entry(entry, cmds, stanza_label, atomic)

    def _match_cmds(self, entry: RuleEntry, cmds: list[str]) -> list[str]:
        """Return the commands that satisfy the entry's match mode."""
        if entry.mode == "exact":
            return [cmd for cmd in cmds if cmd == entry.match]
        if entry.mode == "contains":
            return [cmd for cmd in cmds if entry.match in cmd]
        return [cmd for cmd in cmds if re.search(entry.match, cmd)]  # regex

    def _validate_entry(self, entry: RuleEntry, cmds: list[str], stanza_label: str | None, atomic: AtomicTestResult) -> None:
        """Validate a single entry against the resolved command list."""
        prefix = f"Config: {entry.match} - " if stanza_label else ""
        matched = self._match_cmds(entry, cmds)

        if not entry.absent and not matched:
            atomic.is_failure(entry.context or f"{prefix}Not found")
        elif entry.absent and matched:
            atomic.is_failure(entry.context or f"{prefix}Expected to be absent")
        elif not entry.absent and matched and entry.threshold is not None:
            self._validate_threshold(entry, matched, prefix, atomic)

    def _validate_threshold(self, entry: RuleEntry, matched_cmds: list[str], prefix: str, atomic: AtomicTestResult) -> None:
        """Validate the first capture group of each regex match against the entry's threshold."""
        if entry.threshold is None:
            return
        op_symbols = {"le": "<=", "ge": ">=", "eq": "=="}
        for cmd in matched_cmds:
            # Re-search to access the capture group from the already-matched command.
            match_obj = re.search(entry.match, cmd)
            if match_obj and match_obj.groups():
                captured = int(match_obj.group(1))
                if not self._check_threshold(captured, entry.threshold.value, entry.threshold.operator):
                    atomic.is_failure(
                        entry.context or f"{prefix}{cmd} - Expected: value {op_symbols[entry.threshold.operator]} {entry.threshold.value} Actual: {captured}"
                    )

    def _check_threshold(self, value: int, threshold: int, operator: str) -> bool:
        """Return True if value satisfies the threshold constraint under the given operator."""
        if operator == "le":
            return value <= threshold
        if operator == "ge":
            return value >= threshold
        return value == threshold
