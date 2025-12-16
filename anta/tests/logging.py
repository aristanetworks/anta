# Copyright (c) 2023-2025 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Module related to the EOS various logging tests.

NOTE: The EOS command `show logging` does not support JSON output format.
"""

# Pyright does not understand AntaTest.Input typing
# pyright: reportAttributeAccessIssue=false
from __future__ import annotations

import re
from ipaddress import IPv4Address
from typing import TYPE_CHECKING, Annotated, ClassVar, Literal

from pydantic import Field

from anta.custom_types import LogSeverityLevel
from anta.input_models.logging import LoggingQuery
from anta.models import AntaCommand, AntaTemplate, AntaTest

if TYPE_CHECKING:
    import logging


def _get_logging_states(logger: logging.Logger, command_output: str) -> str:
    """Parse `show logging` output and gets operational logging states used in the tests in this module.

    Parameters
    ----------
    logger
        The logger object.
    command_output
        The `show logging` output.

    Returns
    -------
    str
        The operational logging states.

    """
    log_states = command_output.partition("\n\nExternal configuration:")[0]
    logger.debug("Device logging states:\n%s", log_states)
    return log_states


class VerifySyslogLogging(AntaTest):
    """Verifies if syslog logging is enabled.

    Expected Results
    ----------------
    * Success: The test will pass if syslog logging is enabled.
    * Failure: The test will fail if syslog logging is disabled.

    Examples
    --------
    ```yaml
    anta.tests.logging:
      - VerifySyslogLogging:
    ```
    """

    categories: ClassVar[list[str]] = ["logging"]
    commands: ClassVar[list[AntaCommand | AntaTemplate]] = [AntaCommand(command="show logging", ofmt="text")]

    @AntaTest.anta_test
    def test(self) -> None:
        """Main test function for VerifySyslogLogging."""
        self.result.is_success()
        log_output = self.instance_commands[0].text_output

        if "Syslog logging: enabled" not in _get_logging_states(self.logger, log_output):
            self.result.is_failure("Syslog logging is disabled")


class VerifyLoggingPersistent(AntaTest):
    """Verifies if logging persistent is enabled and logs are saved in flash.

    Expected Results
    ----------------
    * Success: The test will pass if logging persistent is enabled and logs are in flash.
    * Failure: The test will fail if logging persistent is disabled or no logs are saved in flash.

    Examples
    --------
    ```yaml
    anta.tests.logging:
      - VerifyLoggingPersistent:
    ```
    """

    categories: ClassVar[list[str]] = ["logging"]
    commands: ClassVar[list[AntaCommand | AntaTemplate]] = [
        AntaCommand(command="show logging", ofmt="text"),
        AntaCommand(command="dir flash:/persist/messages", ofmt="text"),
    ]

    @AntaTest.anta_test
    def test(self) -> None:
        """Main test function for VerifyLoggingPersistent."""
        self.result.is_success()
        log_output = self.instance_commands[0].text_output
        dir_flash_output = self.instance_commands[1].text_output
        if "Persistent logging: disabled" in _get_logging_states(self.logger, log_output):
            self.result.is_failure("Persistent logging is disabled")
            return
        pattern = r"-rw-\s+(\d+)"
        persist_logs = re.search(pattern, dir_flash_output)
        if not persist_logs or int(persist_logs.group(1)) == 0:
            self.result.is_failure("No persistent logs are saved in flash")


class VerifyLoggingSourceIntf(AntaTest):
    """Verifies logging source-interface for a specified VRF.

    Expected Results
    ----------------
    * Success: The test will pass if the provided logging source-interface is configured in the specified VRF.
    * Failure: The test will fail if the provided logging source-interface is NOT configured in the specified VRF.

    Examples
    --------
    ```yaml
    anta.tests.logging:
      - VerifyLoggingSourceIntf:
          interface: Management0
          vrf: default
    ```
    """

    categories: ClassVar[list[str]] = ["logging"]
    commands: ClassVar[list[AntaCommand | AntaTemplate]] = [AntaCommand(command="show logging", ofmt="text")]

    class Input(AntaTest.Input):
        """Input model for the VerifyLoggingSourceIntf test."""

        interface: str
        """Source-interface to use as source IP of log messages."""
        vrf: str = "default"
        """The name of the VRF to transport log messages. Defaults to `default`."""

    @AntaTest.anta_test
    def test(self) -> None:
        """Main test function for VerifyLoggingSourceIntf."""
        output = self.instance_commands[0].text_output
        pattern = rf"Logging source-interface '{self.inputs.interface}'.*VRF {self.inputs.vrf}"
        if re.search(pattern, _get_logging_states(self.logger, output)):
            self.result.is_success()
        else:
            self.result.is_failure(f"Source-interface: {self.inputs.interface} VRF: {self.inputs.vrf} - Not configured")


class VerifyLoggingHosts(AntaTest):
    """Verifies logging hosts (syslog servers) for a specified VRF.

    Expected Results
    ----------------
    * Success: The test will pass if the provided syslog servers are configured in the specified VRF.
    * Failure: The test will fail if the provided syslog servers are NOT configured in the specified VRF.

    Examples
    --------
    ```yaml
    anta.tests.logging:
      - VerifyLoggingHosts:
          hosts:
            - 1.1.1.1
            - 2.2.2.2
          vrf: default
    ```
    """

    categories: ClassVar[list[str]] = ["logging"]
    commands: ClassVar[list[AntaCommand | AntaTemplate]] = [AntaCommand(command="show logging", ofmt="text")]

    class Input(AntaTest.Input):
        """Input model for the VerifyLoggingHosts test."""

        hosts: list[IPv4Address]
        """List of hosts (syslog servers) IP addresses."""
        vrf: str = "default"
        """The name of the VRF to transport log messages. Defaults to `default`."""

    @AntaTest.anta_test
    def test(self) -> None:
        """Main test function for VerifyLoggingHosts."""
        output = self.instance_commands[0].text_output
        not_configured = []
        for host in self.inputs.hosts:
            pattern = rf"Logging to '{host!s}'.*VRF {self.inputs.vrf}"
            if not re.search(pattern, _get_logging_states(self.logger, output)):
                not_configured.append(str(host))

        if not not_configured:
            self.result.is_success()
        else:
            self.result.is_failure(f"Syslog servers {', '.join(not_configured)} are not configured in VRF {self.inputs.vrf}")


class VerifyLoggingLogsGeneration(AntaTest):
    """Verifies if logs are generated.

    This test performs the following checks:

      1. Sends a test log message at the specified severity log level.
      2. Retrieves the most recent logs (last 30 seconds).
      3. Verifies that the test message was successfully logged.

    Expected Results
    ----------------
    * Success: If logs are being generated and the test message is found in recent logs.
    * Failure: If any of the following occur:
        - The test message is not found in recent logs.
        - The logging system is not capturing new messages.
        - No logs are being generated.

    Examples
    --------
    ```yaml
    anta.tests.logging:
      - VerifyLoggingLogsGeneration:
          severity_level: informational
    ```
    """

    categories: ClassVar[list[str]] = ["logging"]
    commands: ClassVar[list[AntaCommand | AntaTemplate]] = [
        AntaTemplate(template="send log level {severity_level} message ANTA VerifyLoggingLogsGeneration validation", ofmt="text"),
        AntaTemplate(template="show logging {severity_level} last 30 seconds | grep ANTA", ofmt="text", use_cache=False),
    ]

    class Input(AntaTest.Input):
        """Input model for the VerifyLoggingLogsGeneration test."""

        severity_level: LogSeverityLevel = "informational"
        """Log severity level. Defaults to informational."""

    def render(self, template: AntaTemplate) -> list[AntaCommand]:
        """Render the template for log severity level in the input."""
        return [template.render(severity_level=self.inputs.severity_level)]

    @AntaTest.anta_test
    def test(self) -> None:
        """Main test function for VerifyLoggingLogsGeneration."""
        log_pattern = r"ANTA VerifyLoggingLogsGeneration validation"
        output = self.instance_commands[1].text_output
        lines = output.strip().split("\n")[::-1]
        for line in lines:
            if re.search(log_pattern, line):
                self.result.is_success()
                return
        self.result.is_failure("Logs are not generated")


class VerifyLoggingHostname(AntaTest):
    """Verifies if logs are generated with the device FQDN.

    This test performs the following checks:

      1. Retrieves the device's configured FQDN.
      2. Sends a test log message at the specified severity log level.
      3. Retrieves the most recent logs (last 30 seconds).
      4. Verifies that the test message includes the complete FQDN of the device.

    Expected Results
    ----------------
    * Success: If logs are generated with the device's complete FQDN.
    * Failure: If any of the following occur:
        - The test message is not found in recent logs.
        - The log message does not include the device's FQDN.
        - The FQDN in the log message doesn't match the configured FQDN.

    Examples
    --------
    ```yaml
    anta.tests.logging:
      - VerifyLoggingHostname:
          severity_level: informational
    ```
    """

    categories: ClassVar[list[str]] = ["logging"]
    commands: ClassVar[list[AntaCommand | AntaTemplate]] = [
        AntaCommand(command="show hostname", revision=1),
        AntaTemplate(template="send log level {severity_level} message ANTA VerifyLoggingHostname validation", ofmt="text"),
        AntaTemplate(template="show logging {severity_level} last 30 seconds | grep ANTA", ofmt="text", use_cache=False),
    ]

    class Input(AntaTest.Input):
        """Input model for the VerifyLoggingHostname test."""

        severity_level: LogSeverityLevel = "informational"
        """Log severity level. Defaults to informational."""

    def render(self, template: AntaTemplate) -> list[AntaCommand]:
        """Render the template for log severity level in the input."""
        return [template.render(severity_level=self.inputs.severity_level)]

    @AntaTest.anta_test
    def test(self) -> None:
        """Main test function for VerifyLoggingHostname."""
        output_hostname = self.instance_commands[0].json_output
        output_logging = self.instance_commands[2].text_output
        fqdn = output_hostname["fqdn"]
        lines = output_logging.strip().split("\n")[::-1]
        log_pattern = r"ANTA VerifyLoggingHostname validation"
        last_line_with_pattern = ""
        for line in lines:
            if re.search(log_pattern, line):
                last_line_with_pattern = line
                break
        if fqdn in last_line_with_pattern:
            self.result.is_success()
        else:
            self.result.is_failure("Logs are not generated with the device FQDN")


class VerifyLoggingTimestamp(AntaTest):
    """Verifies if logs are generated with the appropriate timestamp.

    This test performs the following checks:

      1. Sends a test log message at the specified severity log level.
      2. Retrieves the most recent logs (last 30 seconds).
      3. Verifies that the test message is present with a high-resolution RFC3339 timestamp format.
        - Example format: `2024-01-25T15:30:45.123456+00:00`.
        - Includes microsecond precision.
        - Contains timezone offset.

    Expected Results
    ----------------
    * Success: If logs are generated with the correct high-resolution RFC3339 timestamp format.
    * Failure: If any of the following occur:
        - The test message is not found in recent logs.
        - The timestamp format does not match the expected RFC3339 format.

    Examples
    --------
    ```yaml
    anta.tests.logging:
      - VerifyLoggingTimestamp:
          severity_level: informational
    ```
    """

    categories: ClassVar[list[str]] = ["logging"]
    commands: ClassVar[list[AntaCommand | AntaTemplate]] = [
        AntaTemplate(template="send log level {severity_level} message ANTA VerifyLoggingTimestamp validation", ofmt="text"),
        AntaTemplate(template="show logging {severity_level} last 30 seconds | grep ANTA", ofmt="text", use_cache=False),
    ]

    class Input(AntaTest.Input):
        """Input model for the VerifyLoggingTimestamp test."""

        severity_level: LogSeverityLevel = "informational"
        """Log severity level. Defaults to informational."""

    def render(self, template: AntaTemplate) -> list[AntaCommand]:
        """Render the template for log severity level in the input."""
        return [template.render(severity_level=self.inputs.severity_level)]

    @AntaTest.anta_test
    def test(self) -> None:
        """Main test function for VerifyLoggingTimestamp."""
        log_pattern = r"ANTA VerifyLoggingTimestamp validation"
        timestamp_pattern = r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{6}[+-]\d{2}:\d{2}"
        output = self.instance_commands[1].text_output
        lines = output.strip().split("\n")[::-1]
        last_line_with_pattern = ""
        for line in lines:
            if re.search(log_pattern, line):
                last_line_with_pattern = line
                break
        if re.search(timestamp_pattern, last_line_with_pattern):
            self.result.is_success()
        else:
            self.result.is_failure("Logs are not generated with the appropriate timestamp format")


class VerifyLoggingAccounting(AntaTest):
    """Verifies if AAA accounting logs are generated.

    Expected Results
    ----------------
    * Success: The test will pass if AAA accounting logs are generated.
    * Failure: The test will fail if AAA accounting logs are NOT generated.

    Examples
    --------
    ```yaml
    anta.tests.logging:
      - VerifyLoggingAccounting:
    ```
    """

    categories: ClassVar[list[str]] = ["logging"]
    commands: ClassVar[list[AntaCommand | AntaTemplate]] = [AntaCommand(command="show aaa accounting logs | tail", ofmt="text")]

    @AntaTest.anta_test
    def test(self) -> None:
        """Main test function for VerifyLoggingAccounting."""
        pattern = r"cmd=show aaa accounting logs"
        output = self.instance_commands[0].text_output
        if re.search(pattern, output):
            self.result.is_success()
        else:
            self.result.is_failure("AAA accounting logs are not generated")


class VerifyLoggingErrors(AntaTest):
    """Verifies there are no syslog messages with a severity of ERRORS or higher.

    Expected Results
    ----------------
      * Success: The test will pass if there are NO syslog messages with a severity of ERRORS or higher.
      * Failure: The test will fail if ERRORS or higher syslog messages are present.

    Examples
    --------
    ```yaml
    anta.tests.logging:
      - VerifyLoggingErrors:
          last_number_time_units: 10
          time_unit: hours
    ```
    """

    categories: ClassVar[list[str]] = ["logging"]
    commands: ClassVar[list[AntaCommand | AntaTemplate]] = [AntaTemplate(template="show logging threshold errors {log_history_depth}", ofmt="text")]

    class Input(AntaTest.Input):
        """Input model for the VerifyLoggingErrors test."""

        last_number_time_units: Annotated[int, Field(ge=1, le=9999)] | None = None
        """Number of time units to look in the logging buffers.

        The actual duration is determined based on the selected `time_unit` (e.g. 5 days, 10 minutes)."""
        time_unit: Literal["days", "hours", "minutes", "seconds"] = "days"
        """Unit of time to be used with `last_number_time_units`."""

    def render(self, template: AntaTemplate) -> list[AntaCommand]:
        """Render the template for log history depth in the input."""
        commands: list[AntaCommand] = []
        log_history_depth: str = ""

        if self.inputs.last_number_time_units:
            log_history_depth = f"last {self.inputs.last_number_time_units} {self.inputs.time_unit}"
        commands.append(template.render(log_history_depth=log_history_depth))

        return commands

    @AntaTest.anta_test
    def test(self) -> None:
        """Main test function for VerifyLoggingErrors."""
        command_output = self.instance_commands[0].text_output

        if len(command_output) == 0:
            self.result.is_success()
        else:
            self.result.is_failure(f"Device has reported syslog messages with a severity of ERRORS or higher:\n{command_output}")


class VerifyLoggingEntries(AntaTest):
    """Verifies that log strings are present or absent in the logging buffer.

    Expected Results
    ----------------
    * Success:
        - If `fail_on_match` is `False` (default): the test will pass if all specified patterns are found in the log output.
        - If `fail_on_match` is `True`: the test will pass if none of the specified patterns are found in the log output.

    * Failure:
        - If `fail_on_match` is `False`: the test will fail if any of the specified patterns are missing from the log output.
        - If `fail_on_match` is `True`: the test will fail if any of the specified patterns are found in the log output.

    Examples
    --------
    ```yaml
    anta.tests.logging:
      - VerifyLoggingEntries:
          logging_entries:
            - regex_match: ".*ACCOUNTING-5-EXEC: cvpadmin ssh.*"
              last_number_messages: 30
              severity_level: alerts
            - regex_match:
                - ".*SPANTREE-6-INTERFACE_ADD:.*"
                - ".*ACCOUNTING-5-EXEC: cvpadmin ssh.*"
              last_number_time_units: 3
              time_unit: hours
              severity_level: critical
              fail_on_match: True
    ```
    """

    categories: ClassVar[list[str]] = ["logging"]
    commands: ClassVar[list[AntaCommand | AntaTemplate]] = [AntaTemplate(template="show logging {log_history_depth} {severity_level}", ofmt="text", use_cache=False)]

    class Input(AntaTest.Input):
        """Input model for the VerifyLoggingEntries test."""

        logging_entries: list[LoggingQuery]
        """List of logging entries and regex match."""

    def render(self, template: AntaTemplate) -> list[AntaCommand]:
        """Render the template for log history depth and log severity level in the input."""
        commands: list[AntaCommand] = []
        for entry in self.inputs.logging_entries:
            log_history_depth: str | int = ""
            if entry.last_number_messages:
                log_history_depth = entry.last_number_messages
            elif entry.last_number_time_units:
                log_history_depth = f"last {entry.last_number_time_units} {entry.time_unit}"
            commands.append(template.render(log_history_depth=log_history_depth, severity_level=entry.severity_level))
        return commands

    @AntaTest.anta_test
    def test(self) -> None:
        """Main test function for VerifyLoggingEntries."""
        self.result.is_success()
        for command_output, logging_entry in zip(self.instance_commands, self.inputs.logging_entries, strict=False):
            output = command_output.text_output
            log_history_depth = command_output.params.log_history_depth
            patterns_to_check = logging_entry.regex_match if isinstance(logging_entry.regex_match, list) else [logging_entry.regex_match]

            for pattern in patterns_to_check:
                match_found = re.search(pattern, output)

                # Fails if any of the regex patterns are found
                if logging_entry.fail_on_match and match_found:
                    self.result.is_failure(f"Unexpected Pattern: `{pattern}` - Found in last {log_history_depth} {logging_entry.severity_level} log entries")

                # Fails if any of the regex patterns not found
                if not logging_entry.fail_on_match and not match_found:
                    self.result.is_failure(f"Pattern: `{pattern}` - Not found in last {log_history_depth} {logging_entry.severity_level} log entries")
