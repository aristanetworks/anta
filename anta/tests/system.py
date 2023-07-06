"""
Test functions related to system-level features and protocols
"""
from __future__ import annotations

from typing import Optional

from anta.models import AntaCommand, AntaTest


class VerifyUptime(AntaTest):
    """
    Verifies the device uptime is higher than a value.
    """

    name = "VerifyUptime"
    description = "Verifies the device uptime is higher than a value."
    categories = ["system"]
    commands = [AntaCommand(command="show uptime")]

    @AntaTest.anta_test
    def test(self, minimum: Optional[int] = None) -> None:
        """
        Run VerifyUptime validation

        Args:
            minimum: Minimum uptime in seconds.
        """

        command_output = self.instance_commands[0].json_output

        if not (isinstance(minimum, (int, float))) or minimum < 0:
            self.result.is_skipped("VerifyUptime was not run as incorrect minimum uptime was given")
            return

        if command_output["upTime"] > minimum:
            self.result.is_success()
        else:
            self.result.is_failure(f"Uptime is {command_output['upTime']}")


class VerifyReloadCause(AntaTest):
    """
    Verifies the last reload of the device was requested by a user.

    Test considers the following messages as normal and will return success. Failure is for other messages
    * Reload requested by the user.
    * Reload requested after FPGA upgrade
    """

    name = "VerifyReloadCause"
    description = "Verifies the device uptime is higher than a value."
    categories = ["system"]
    commands = [AntaCommand(command="show reload cause")]

    @AntaTest.anta_test
    def test(self) -> None:
        """
        Run VerifyReloadCause validation
        """

        command_output = self.instance_commands[0].json_output

        if "resetCauses" not in command_output.keys():
            self.result.is_error("no reload cause available")
            return

        if len(command_output["resetCauses"]) == 0:
            # No reload causes
            self.result.is_success()
            return

        reset_causes = command_output["resetCauses"]
        command_output_data = reset_causes[0].get("description")
        if command_output_data in [
            "Reload requested by the user.",
            "Reload requested after FPGA upgrade",
        ]:
            self.result.is_success()
        else:
            self.result.is_failure(f"Reload cause is {command_output_data}")


class VerifyCoredump(AntaTest):
    """
    Verifies there is no core file.
    """

    name = "VerifyCoredump"
    description = "Verifies there is no core file."
    categories = ["system"]
    commands = [AntaCommand(command="bash timeout 10 ls /var/core", ofmt="text")]

    @AntaTest.anta_test
    def test(self) -> None:
        """
        Run VerifyCoredump validation
        """
        command_output = self.instance_commands[0].text_output

        if len(command_output) == 0:
            self.result.is_success()
        else:
            self.result.is_failure(f"Core-dump(s) have been found: {command_output}")


class VerifyAgentLogs(AntaTest):
    """
    Verifies there is no agent crash reported on the device.
    """

    name = "VerifyAgentLogs"
    description = "Verifies there is no agent crash reported on the device."
    categories = ["system"]
    commands = [AntaCommand(command="show agent logs crash", ofmt="text")]

    @AntaTest.anta_test
    def test(self) -> None:
        """
        Run VerifyAgentLogs validation
        """
        command_output = self.instance_commands[0].text_output

        if len(command_output) == 0:
            self.result.is_success()
        else:
            self.result.is_failure(f"device reported some agent crashes: {command_output}")


class VerifySyslog(AntaTest):
    """
    Verifies the device had no syslog message with a severity of warning (or a more severe message) during the last 7 days.
    """

    name = "VerifySyslog"
    description = "Verifies the device had no syslog message with a severity of warning (or a more severe message) during the last 7 days."
    categories = ["system"]
    commands = [AntaCommand(command="show logging last 7 days threshold warnings", ofmt="text")]

    @AntaTest.anta_test
    def test(self) -> None:
        """
        Run VerifySyslog validation
        """
        command_output = self.instance_commands[0].text_output

        if len(command_output) == 0:
            self.result.is_success()
        else:
            self.result.is_failure("Device has some log messages with a severity WARNING or higher")


class VerifyCPUUtilization(AntaTest):
    """
    Verifies the CPU utilization is less than 75%.
    """

    name = "VerifyCPUUtilization"
    description = "Verifies the CPU utilization is less than 75%."
    categories = ["system"]
    commands = [AntaCommand(command="show processes top once")]

    @AntaTest.anta_test
    def test(self) -> None:
        """
        Run VerifyCPUUtilization validation
        """
        command_output = self.instance_commands[0].json_output
        command_output_data = command_output["cpuInfo"]["%Cpu(s)"]["idle"]

        if command_output_data > 25:
            self.result.is_success()
        else:
            self.result.is_failure(f"device reported a high CPU utilization ({100 - command_output_data}%)")


class VerifyMemoryUtilization(AntaTest):
    """
    Verifies the Memory utilization is less than 75%.
    """

    name = "VerifyMemoryUtilization"
    description = "Verifies the Memory utilization is less than 75%."
    categories = ["system"]
    commands = [AntaCommand(command="show version")]

    @AntaTest.anta_test
    def test(self) -> None:
        """
        Run VerifyMemoryUtilization validation
        """
        command_output = self.instance_commands[0].json_output

        memory_usage = command_output["memFree"] / command_output["memTotal"]
        if memory_usage > 0.25:
            self.result.is_success()
        else:
            self.result.is_failure(f"device report a high memory usage: {(1 - memory_usage)*100:.2f}%")


class VerifyFileSystemUtilization(AntaTest):
    """
    Verifies each partition on the disk is used less than 75%.
    """

    name = "VerifyFileSystemUtilization"
    description = "Verifies each partition on the disk is used less than 75%."
    categories = ["system"]
    commands = [AntaCommand(command="bash timeout 10 df -h", ofmt="text")]

    @AntaTest.anta_test
    def test(self) -> None:
        """
        Run VerifyFileSystemUtilization validation
        """
        command_output = self.instance_commands[0].text_output

        self.result.is_success()

        for line in command_output.split("\n")[1:]:
            if "loop" not in line and len(line) > 0 and (percentage := int(line.split()[4].replace("%", ""))) > 75:
                self.result.is_failure(f"mount point {line} is higher than 75% (reported {percentage})")


class VerifyNTP(AntaTest):
    """
    Verifies NTP is synchronised.
    """

    name = "VerifyNTP"
    description = "Verifies NTP is synchronised."
    categories = ["system"]
    commands = [AntaCommand(command="show ntp status", ofmt="text")]

    @AntaTest.anta_test
    def test(self) -> None:
        """
        Run VerifyNTP validation
        """
        command_output = self.instance_commands[0].text_output

        if command_output.split("\n")[0].split(" ")[0] == "synchronised":
            self.result.is_success()
        else:
            data = command_output.split("\n")[0]
            self.result.is_failure(f"not sync with NTP server ({data})")
