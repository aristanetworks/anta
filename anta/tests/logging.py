# Copyright (c) 2023 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""
Test functions related to the EOS various logging settings

NOTE: 'show logging' does not support json output yet
"""
# Mypy does not understand AntaTest.Input typing
# mypy: disable-error-code=attr-defined
from __future__ import annotations

import logging
import re
from ipaddress import IPv4Address

# Need to keep List for pydantic in python 3.8
from typing import List

from anta.models import AntaCommand, AntaTest


def _get_logging_states(logger: logging.Logger, command_output: str) -> str:
    """
    Parse "show logging" output and gets operational logging states used
    in the tests in this module.

    Args:
        command_output: The 'show logging' output
    """
    log_states = command_output.partition("\n\nExternal configuration:")[0]
    logger.debug(f"Device logging states:\n{log_states}")
    return log_states


class VerifyLoggingPersistent(AntaTest):
    """
    Verifies if logging persistent is enabled and logs are saved in flash.

    Expected Results:
        * success: The test will pass if logging persistent is enabled and logs are in flash.
        * failure: The test will fail if logging persistent is disabled or no logs are saved in flash.
    """

    name = "VerifyLoggingPersistent"
    description = "Verifies if logging persistent is enabled and logs are saved in flash."
    categories = ["logging"]
    commands = [
        AntaCommand(command="show logging", ofmt="text"),
        AntaCommand(command="dir flash:/persist/messages", ofmt="text"),
    ]

    @AntaTest.anta_test
    def test(self) -> None:
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
    """
    Verifies logging source-interface for a specified VRF.

    Expected Results:
        * success: The test will pass if the provided logging source-interface is configured in the specified VRF.
        * failure: The test will fail if the provided logging source-interface is NOT configured in the specified VRF.
    """

    name = "VerifyLoggingSourceInt"
    description = "Verifies logging source-interface for a specified VRF."
    categories = ["logging"]
    commands = [AntaCommand(command="show logging", ofmt="text")]

    class Input(AntaTest.Input):  # pylint: disable=missing-class-docstring
        interface: str
        """Source-interface to use as source IP of log messages"""
        vrf: str = "default"
        """The name of the VRF to transport log messages"""

    @AntaTest.anta_test
    def test(self) -> None:
        output = self.instance_commands[0].text_output
        pattern = rf"Logging source-interface '{self.inputs.interface}'.*VRF {self.inputs.vrf}"
        if re.search(pattern, _get_logging_states(self.logger, output)):
            self.result.is_success()
        else:
            self.result.is_failure(f"Source-interface '{self.inputs.interface}' is not configured in VRF {self.inputs.vrf}")


class VerifyLoggingHosts(AntaTest):
    """
    Verifies logging hosts (syslog servers) for a specified VRF.

    Expected Results:
        * success: The test will pass if the provided syslog servers are configured in the specified VRF.
        * failure: The test will fail if the provided syslog servers are NOT configured in the specified VRF.
    """

    name = "VerifyLoggingHosts"
    description = "Verifies logging hosts (syslog servers) for a specified VRF."
    categories = ["logging"]
    commands = [AntaCommand(command="show logging", ofmt="text")]

    class Input(AntaTest.Input):  # pylint: disable=missing-class-docstring
        hosts: List[IPv4Address]
        """List of hosts (syslog servers) IP addresses"""
        vrf: str = "default"
        """The name of the VRF to transport log messages"""

    @AntaTest.anta_test
    def test(self) -> None:
        output = self.instance_commands[0].text_output
        not_configured = []
        for host in self.inputs.hosts:
            pattern = rf"Logging to '{str(host)}'.*VRF {self.inputs.vrf}"
            if not re.search(pattern, _get_logging_states(self.logger, output)):
                not_configured.append(str(host))

        if not not_configured:
            self.result.is_success()
        else:
            self.result.is_failure(f"Syslog servers {not_configured} are not configured in VRF {self.inputs.vrf}")


class VerifyLoggingLogsGeneration(AntaTest):
    """
    Verifies if logs are generated.

    Expected Results:
        * success: The test will pass if logs are generated.
        * failure: The test will fail if logs are NOT generated.
    """

    name = "VerifyLoggingLogsGeneration"
    description = "Verifies if logs are generated."
    categories = ["logging"]
    commands = [
        AntaCommand(command="send log level informational message ANTA VerifyLoggingLogsGeneration validation"),
        AntaCommand(command="show logging informational last 30 seconds | grep ANTA", ofmt="text"),
    ]

    @AntaTest.anta_test
    def test(self) -> None:
        log_pattern = r"ANTA VerifyLoggingLogsGeneration validation"
        output = self.instance_commands[1].text_output
        lines = output.strip().split("\n")[::-1]
        for line in lines:
            if re.search(log_pattern, line):
                self.result.is_success()
                return
        self.result.is_failure("Logs are not generated")


class VerifyLoggingHostname(AntaTest):
    """
    Verifies if logs are generated with the device FQDN.

    Expected Results:
        * success: The test will pass if logs are generated with the device FQDN.
        * failure: The test will fail if logs are NOT generated with the device FQDN.
    """

    name = "VerifyLoggingHostname"
    description = "Verifies if logs are generated with the device FQDN."
    categories = ["logging"]
    commands = [
        AntaCommand(command="show hostname"),
        AntaCommand(command="send log level informational message ANTA VerifyLoggingHostname validation"),
        AntaCommand(command="show logging informational last 30 seconds | grep ANTA", ofmt="text"),
    ]

    @AntaTest.anta_test
    def test(self) -> None:
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
    """
    Verifies if logs are generated with the approprate timestamp.

    Expected Results:
        * success: The test will pass if logs are generated with the appropriated timestamp.
        * failure: The test will fail if logs are NOT generated with the appropriated timestamp.
    """

    name = "VerifyLoggingTimestamp"
    description = "Verifies if logs are generated with the appropriate timestamp."
    categories = ["logging"]
    commands = [
        AntaCommand(command="send log level informational message ANTA VerifyLoggingTimestamp validation"),
        AntaCommand(command="show logging informational last 30 seconds | grep ANTA", ofmt="text"),
    ]

    @AntaTest.anta_test
    def test(self) -> None:
        log_pattern = r"ANTA VerifyLoggingTimestamp validation"
        timestamp_pattern = r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{6}-\d{2}:\d{2}"
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
    """
    Verifies if AAA accounting logs are generated.

    Expected Results:
        * success: The test will pass if AAA accounting logs are generated.
        * failure: The test will fail if AAA accounting logs are NOT generated.
    """

    name = "VerifyLoggingAccounting"
    description = "Verifies if AAA accounting logs are generated."
    categories = ["logging"]
    commands = [AntaCommand(command="show aaa accounting logs | tail", ofmt="text")]

    @AntaTest.anta_test
    def test(self) -> None:
        pattern = r"cmd=show aaa accounting logs"
        output = self.instance_commands[0].text_output
        if re.search(pattern, output):
            self.result.is_success()
        else:
            self.result.is_failure("AAA accounting logs are not generated")


class VerifyLoggingErrors(AntaTest):
    """
    This test verifies there are no syslog messages with a severity of ERRORS or higher.

    Expected Results:
      * success: The test will pass if there are NO syslog messages with a severity of ERRORS or higher.
      * failure: The test will fail if ERRORS or higher syslog messages are present.
    """

    name = "VerifyLoggingWarning"
    description = "This test verifies there are no syslog messages with a severity of ERRORS or higher."
    categories = ["logging"]
    commands = [AntaCommand(command="show logging threshold errors", ofmt="text")]

    @AntaTest.anta_test
    def test(self) -> None:
        """
        Run VerifyLoggingWarning validation
        """
        command_output = self.instance_commands[0].text_output

        if len(command_output) == 0:
            self.result.is_success()
        else:
            self.result.is_failure("Device has reported syslog messages with a severity of ERRORS or higher")
