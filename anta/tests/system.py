"""
Test functions related to system-level features and protocols
"""
from __future__ import annotations

import re
from typing import Optional

from anta.models import AntaCommand, AntaTest


class VerifyUptime(AntaTest):
    """
    This test verifies if the device uptime is higher than the provided minimum uptime value.

    Expected Results:
      * success: The test will pass if the device uptime is higher than the provided value.
      * failure: The test will fail if the device uptime is lower than the provided value.
      * skipped: The test will be skipped if the provided uptime value is invalid or negative.
    """

    name = "VerifyUptime"
    description = "This test verifies if the device uptime is higher than the provided minimum uptime value."
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
            self.result.is_skipped(f"{self.__class__.name} was not run since the provided uptime value is invalid or negative")
            return

        if command_output["upTime"] > minimum:
            self.result.is_success()
        else:
            self.result.is_failure(f"Device uptime is {command_output['upTime']} seconds")


class VerifyReloadCause(AntaTest):
    """
    This test verifies the last reload cause of the device.

    Expected Results:
      * success: The test will pass if there are NO reload causes or if the last reload was caused by the user or after an FPGA upgrade.
      * failure: The test will fail if the last reload was NOT caused by the user or after an FPGA upgrade.
      * error: The test will report an error if the reload cause is NOT available.
    """

    name = "VerifyReloadCause"
    description = "This test verifies the last reload cause of the device."
    categories = ["system"]
    commands = [AntaCommand(command="show reload cause")]

    @AntaTest.anta_test
    def test(self) -> None:
        """
        Run VerifyReloadCause validation
        """

        command_output = self.instance_commands[0].json_output

        if "resetCauses" not in command_output.keys():
            self.result.is_error("No reload causes available")
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
            self.result.is_failure(f"Reload cause is: '{command_output_data}'")


class VerifyCoredump(AntaTest):
    """
    This test verifies if there are core files saved in the /var/core directory.

    Expected Results:
      * success: The test will pass if there are NO core files saved in the directory.
      * failure: The test will fail if there are core files saved in the directory.
    """

    name = "VerifyCoredump"
    description = "This test verifies if there are core files saved in the /var/core directory."
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
            command_output = command_output.replace("\n", "")
            self.result.is_failure(f"Core-dump(s) have been found: {command_output}")


class VerifyAgentLogs(AntaTest):
    """
    This test verifies that no agent crash reports are present on the device.

    Expected Results:
      * success: The test will pass if there is NO agent crash reported.
      * failure: The test will fail if any agent crashes are reported.
    """

    name = "VerifyAgentLogs"
    description = "This test verifies that no agent crash reports are present on the device."
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
            pattern = re.compile(r"^===> (.*?) <===$", re.MULTILINE)
            agents = "\n * ".join(pattern.findall(command_output))
            self.result.is_failure(f"Device has reported agent crashes:\n * {agents}")


class VerifySyslog(AntaTest):
    """
    This test verifies there are no syslog messages with a severity of WARNING or higher in the last 7 days.

    Expected Results:
      * success: The test will pass if there are NO syslog messages with a severity of WARNING or higher in the last 7 days.
      * failure: The test will fail if WARNING or higher syslog messages are present in the last 7 days.
    """

    name = "VerifySyslog"
    description = "This test verifies there are no syslog messages with a severity of WARNING or higher in the last 7 days."
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
            self.result.is_failure("Device has reported some log messages with WARNING or higher severity")


class VerifyCPUUtilization(AntaTest):
    """
    This test verifies whether the CPU utilization is below 75%.

    Expected Results:
      * success: The test will pass if the CPU utilization is below 75%.
      * failure: The test will fail if the CPU utilization is over 75%.
    """

    name = "VerifyCPUUtilization"
    description = "This test verifies whether the CPU utilization is below 75%."
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
            self.result.is_failure(f"Device has reported a high CPU utilization: {100 - command_output_data}%")


class VerifyMemoryUtilization(AntaTest):
    """
    This test verifies whether the memory utilization is below 75%.

    Expected Results:
      * success: The test will pass if the memory utilization is below 75%.
      * failure: The test will fail if the memory utilization is over 75%.
    """

    name = "VerifyMemoryUtilization"
    description = "This test verifies whether the memory utilization is below 75%."
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
            self.result.is_failure(f"Device has reported a high memory usage: {(1 - memory_usage)*100:.2f}%")


class VerifyFileSystemUtilization(AntaTest):
    """
    This test verifies that no partition is utilizing more than 75% of its disk space.

    Expected Results:
      * success: The test will pass if all partitions are using less than 75% of its disk space.
      * failure: The test will fail if any partitions are using more than 75% of its disk space.
    """

    name = "VerifyFileSystemUtilization"
    description = "This test verifies that no partition is utilizing more than 75% of its disk space."
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
                self.result.is_failure(f"Mount point {line} is higher than 75%: reported {percentage}%")


class VerifyNTP(AntaTest):
    """
    This test verifies that the Network Time Protocol (NTP) is synchronized.

    Expected Results:
      * success: The test will pass if the NTP is synchronised.
      * failure: The test will fail if the NTP is NOT synchronised.
    """

    name = "VerifyNTP"
    description = "This test verifies if NTP is synchronised."
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
            self.result.is_failure(f"NTP server is not synchronized: '{data}'")
