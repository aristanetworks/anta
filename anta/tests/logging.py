# Copyright (c) 2023-2024 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Module related to the EOS various logging tests.

NOTE: The EOS command `show logging` does not support JSON output format.
"""

# Mypy does not understand AntaTest.Input typing
# mypy: disable-error-code=attr-defined
from __future__ import annotations

import re
from ipaddress import IPv4Address
from typing import TYPE_CHECKING, ClassVar

from anta.models import AntaCommand, AntaTest

if TYPE_CHECKING:
    import logging

    from anta.models import AntaTemplate


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

    name = "VerifyLoggingPersistent"
    description = "Verifies if logging persistent is enabled and logs are saved in flash."
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

    name = "VerifyLoggingSourceIntf"
    description = "Verifies logging source-interface for a specified VRF."
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
            self.result.is_failure(f"Source-interface '{self.inputs.interface}' is not configured in VRF {self.inputs.vrf}")


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

    name = "VerifyLoggingHosts"
    description = "Verifies logging hosts (syslog servers) for a specified VRF."
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
            self.result.is_failure(f"Syslog servers {not_configured} are not configured in VRF {self.inputs.vrf}")


class VerifyLoggingLogsGeneration(AntaTest):
    """Verifies if logs are generated.

    Expected Results
    ----------------
    * Success: The test will pass if logs are generated.
    * Failure: The test will fail if logs are NOT generated.

    Examples
    --------
    ```yaml
    anta.tests.logging:
      - VerifyLoggingLogsGeneration:
    ```
    """

    name = "VerifyLoggingLogsGeneration"
    description = "Verifies if logs are generated."
    categories: ClassVar[list[str]] = ["logging"]
    commands: ClassVar[list[AntaCommand | AntaTemplate]] = [
        AntaCommand(command="send log level informational message ANTA VerifyLoggingLogsGeneration validation", ofmt="text"),
        AntaCommand(command="show logging informational last 30 seconds | grep ANTA", ofmt="text", use_cache=False),
    ]

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

    Expected Results
    ----------------
    * Success: The test will pass if logs are generated with the device FQDN.
    * Failure: The test will fail if logs are NOT generated with the device FQDN.

    Examples
    --------
    ```yaml
    anta.tests.logging:
      - VerifyLoggingHostname:
    ```
    """

    name = "VerifyLoggingHostname"
    description = "Verifies if logs are generated with the device FQDN."
    categories: ClassVar[list[str]] = ["logging"]
    commands: ClassVar[list[AntaCommand | AntaTemplate]] = [
        AntaCommand(command="show hostname", revision=1),
        AntaCommand(command="send log level informational message ANTA VerifyLoggingHostname validation", ofmt="text"),
        AntaCommand(command="show logging informational last 30 seconds | grep ANTA", ofmt="text", use_cache=False),
    ]

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

    Expected Results
    ----------------
    * Success: The test will pass if logs are generated with the appropriate timestamp.
    * Failure: The test will fail if logs are NOT generated with the appropriate timestamp.

    Examples
    --------
    ```yaml
    anta.tests.logging:
      - VerifyLoggingTimestamp:
    ```
    """

    name = "VerifyLoggingTimestamp"
    description = "Verifies if logs are generated with the appropriate timestamp."
    categories: ClassVar[list[str]] = ["logging"]
    commands: ClassVar[list[AntaCommand | AntaTemplate]] = [
        AntaCommand(command="send log level informational message ANTA VerifyLoggingTimestamp validation", ofmt="text"),
        AntaCommand(command="show logging informational last 30 seconds | grep ANTA", ofmt="text", use_cache=False),
    ]

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

    name = "VerifyLoggingAccounting"
    description = "Verifies if AAA accounting logs are generated."
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
    ```
    """

    name = "VerifyLoggingErrors"
    description = "Verifies there are no syslog messages with a severity of ERRORS or higher."
    categories: ClassVar[list[str]] = ["logging"]
    commands: ClassVar[list[AntaCommand | AntaTemplate]] = [AntaCommand(command="show logging threshold errors", ofmt="text")]

    @AntaTest.anta_test
    def test(self) -> None:
        """Main test function for VerifyLoggingErrors."""
        command_output = self.instance_commands[0].text_output

        if len(command_output) == 0:
            self.result.is_success()
        else:
            self.result.is_failure("Device has reported syslog messages with a severity of ERRORS or higher")
