"""
Test functions related to the EOS various logging settings

NOTE: 'show logging' does not support json output yet
"""
from __future__ import annotations

import logging
import re
from typing import Dict, List, Optional, cast

from anta.models import AntaTest, AntaTestCommand

logger = logging.getLogger(__name__)


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
        AntaTestCommand(command="show logging | awk 'NR==4 {print; exit}'", ofmt="text"),
        AntaTestCommand(command="dir flash:/persist/messages", ofmt="text"),
    ]

    @AntaTest.anta_test
    def test(self) -> None:
        """
        Run VerifyLoggingPersistent validation.
        """
        logger.debug(f"self.instance_commands is: {self.instance_commands}")
        log_output = cast(str, self.instance_commands[0].output)
        dir_flash_output = cast(str, self.instance_commands[1].output)
        logger.debug(f"dataset of log_output command is: {log_output}")
        logger.debug(f"dataset of dir_flash_output command is: {dir_flash_output}")

        pattern = r"-rw-\s+(\d+)"
        match = re.search(pattern, dir_flash_output)

        self.result.is_success()

        if "disabled" in log_output:
            self.result.is_failure("Persistent logging is disabled")
            return

        if not match or int(match.group(1)) == 0:
            self.result.is_failure("No persistent logs are saved in flash")


class VerifyLoggingSourceIntf(AntaTest):
    """
    Verifies logging source-interface for a specified VRF.

    Expected Results:
        * success: The test will pass if the provided logging source-interface is configured in the specified VRF.
        * failure: The test will fail if the provided logging source-interface is NOT configured in the specified VRF.
        * skipped: The test will be skipped if source-interface or VRF is not provided.
    """

    name = "VerifyLoggingSourceInt"
    description = "Verifies logging source-interface for a specified VRF."
    categories = ["logging"]
    commands = [AntaTestCommand(command="show logging | awk '/Trap logging/,/Sequence numbers/{if(/Sequence numbers/) exit; print}'", ofmt="text")]

    @AntaTest.anta_test
    def test(self, intf: Optional[str] = None, vrf: str = "default") -> None:
        """
        Run VerifyLoggingSrcDst validation.

        Args:
            intf: Source-interface to use as source IP of log messages.
            vrf: The name of the VRF to transport log messages. Defaults to 'default'.
        """
        if not intf or not vrf:
            self.result.is_skipped(f"{self.__class__.name} did not run because intf or vrf was not supplied")
            return

        logger.debug(f"self.instance_commands is: {self.instance_commands}")
        command_output = cast(str, self.instance_commands[0].output)
        logger.debug(f"dataset is: {command_output}")

        pattern = rf"Logging source-interface '{intf}'.*VRF {vrf}"

        if re.search(pattern, command_output):
            self.result.is_success()
        else:
            self.result.is_failure(f"Source-interface '{intf}' is not configured in VRF {vrf}")


class VerifyLoggingHosts(AntaTest):
    """
    Verifies logging hosts (syslog servers) for a specified VRF.

    Expected Results:
        * success: The test will pass if the provided syslog servers are configured in the specified VRF.
        * failure: The test will fail if the provided syslog servers are NOT configured in the specified VRF.
        * skipped: The test will be skipped if syslog servers or VRF are not provided.
    """

    name = "VerifyLoggingHosts"
    description = "Verifies logging hosts (syslog servers) for a specified VRF."
    categories = ["logging"]
    commands = [AntaTestCommand(command="show logging | awk '/Trap logging/,/Sequence numbers/{if(/Sequence numbers/) exit; print}'", ofmt="text")]

    @AntaTest.anta_test
    def test(self, hosts: Optional[List[str]] = None, vrf: str = "default") -> None:
        """
        Run VerifyLoggingHosts validation.

        Args:
            hosts: List of hosts (syslog servers) IP addresses.
            vrf: The name of the VRF to transport log messages. Defaults to 'default'.
        """
        if not hosts or not vrf:
            self.result.is_skipped(f"{self.__class__.name} did not run because hosts or vrf were not supplied")
            return

        logger.debug(f"self.instance_commands is: {self.instance_commands}")
        command_output = cast(str, self.instance_commands[0].output)
        logger.debug(f"dataset is: {command_output}")

        not_configured = []

        for host in hosts:
            pattern = rf"Logging to '{host}'.*VRF {vrf}"
            if not re.search(pattern, command_output):
                not_configured.append(host)

        if not not_configured:
            self.result.is_success()
        else:
            self.result.is_failure(f"Syslog servers {not_configured} are not configured in VRF {vrf}")


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
        AntaTestCommand(command="send log level informational message ANTA VerifyLoggingLogsGeneration validation"),
        AntaTestCommand(command="show logging informational last 30 seconds | grep ANTA", ofmt="text"),
    ]

    @AntaTest.anta_test
    def test(self) -> None:
        """
        Run VerifyLoggingLogs validation.
        """

        logger.debug(f"self.instance_commands is: {self.instance_commands}")
        command_output = cast(str, self.instance_commands[1].output)
        logger.debug(f"dataset is: {command_output}")

        log_pattern = r"ANTA VerifyLoggingLogsGeneration validation"

        lines = command_output.strip().split("\n")[::-1]

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
        AntaTestCommand(command="show hostname"),
        AntaTestCommand(command="send log level informational message ANTA VerifyLoggingHostname validation"),
        AntaTestCommand(command="show logging informational last 30 seconds | grep ANTA", ofmt="text"),
    ]

    @AntaTest.anta_test
    def test(self) -> None:
        """
        Run VerifyLoggingHostname validation.
        """

        logger.debug(f"self.instance_commands is: {self.instance_commands}")
        hostname_output = cast(Dict[str, str], self.instance_commands[0].output)
        log_output = cast(str, self.instance_commands[2].output)
        logger.debug(f"dataset of hostname_output is: {hostname_output}")
        logger.debug(f"dataset of log_output is: {log_output}")

        fqdn = hostname_output["fqdn"]

        log_pattern = r"ANTA VerifyLoggingHostname validation"

        lines = log_output.strip().split("\n")[::-1]

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
        AntaTestCommand(command="send log level informational message ANTA VerifyLoggingTimestamp validation"),
        AntaTestCommand(command="show logging informational last 30 seconds | grep ANTA", ofmt="text"),
    ]

    @AntaTest.anta_test
    def test(self) -> None:
        """
        Run VerifyLoggingTimestamp validation.
        """

        logger.debug(f"self.instance_commands is: {self.instance_commands}")
        command_output = cast(str, self.instance_commands[1].output)
        logger.debug(f"dataset is: {command_output}")

        log_pattern = r"ANTA VerifyLoggingTimestamp validation"
        timestamp_pattern = r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{6}-\d{2}:\d{2}"

        lines = command_output.strip().split("\n")[::-1]

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
    commands = [AntaTestCommand(command="show aaa accounting logs | tail", ofmt="text")]

    @AntaTest.anta_test
    def test(self) -> None:
        """
        Run VerifyLoggingAccountingvalidation.
        """

        logger.debug(f"self.instance_commands is: {self.instance_commands}")
        command_output = cast(str, self.instance_commands[0].output)
        logger.debug(f"dataset is: {command_output}")

        pattern = r"cmd=show aaa accounting logs"

        if re.search(pattern, command_output):
            self.result.is_success()
        else:
            self.result.is_failure("AAA accounting logs are not generated")
