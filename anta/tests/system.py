# Copyright (c) 2023-2024 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Module related to system-level features and protocols tests."""

# Mypy does not understand AntaTest.Input typing
# mypy: disable-error-code=attr-defined
from __future__ import annotations

import re
from typing import TYPE_CHECKING, ClassVar

from anta.custom_types import PositiveInteger
from anta.models import AntaCommand, AntaTest

if TYPE_CHECKING:
    from anta.models import AntaTemplate

CPU_IDLE_THRESHOLD = 25
MEMORY_THRESHOLD = 0.25
DISK_SPACE_THRESHOLD = 75

class VerifyUptime(AntaTest):
    """Verifies if the device uptime is higher than the provided minimum uptime value.

    Expected Results:
      * Success: The test will pass if the device uptime is higher than the provided value.
      * Failure: The test will fail if the device uptime is lower than the provided value.
    """

    name = "VerifyUptime"
    description = "Verifies the device uptime."
    categories: ClassVar[list[str]] = ["system"]
    commands: ClassVar[list[AntaCommand | AntaTemplate]] = [AntaCommand(command="show uptime")]

    class Input(AntaTest.Input):
        """Input model for the VerifyUptime test."""

        minimum: PositiveInteger
        """Minimum uptime in seconds."""

    @AntaTest.anta_test
    def test(self) -> None:
        """Main test function for VerifyUptime."""
        command_output = self.instance_commands[0].json_output
        if command_output["upTime"] > self.inputs.minimum:
            self.result.is_success()
        else:
            self.result.is_failure(f"Device uptime is {command_output['upTime']} seconds")


class VerifyReloadCause(AntaTest):
    """Verifies the last reload cause of the device.

    Expected results:
      * Success: The test will pass if there are NO reload causes or if the last reload was caused by the user or after an FPGA upgrade.
      * Failure: The test will fail if the last reload was NOT caused by the user or after an FPGA upgrade.
      * Error: The test will report an error if the reload cause is NOT available.
    """

    name = "VerifyReloadCause"
    description = "Verifies the last reload cause of the device."
    categories: ClassVar[list[str]] = ["system"]
    commands: ClassVar[list[AntaCommand | AntaTemplate]] = [AntaCommand(command="show reload cause")]

    @AntaTest.anta_test
    def test(self) -> None:
        """Main test function for VerifyReloadCause."""
        command_output = self.instance_commands[0].json_output
        if "resetCauses" not in command_output:
            self.result.is_error(message="No reload causes available")
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
    """Verifies if there are core dump files in the /var/core directory.

    Expected Results:
      * Success: The test will pass if there are NO core dump(s) in /var/core.
      * Failure: The test will fail if there are core dump(s) in /var/core.

    Note:
    ----
      * This test will NOT check for minidump(s) generated by certain agents in /var/core/minidump.

    """

    name = "VerifyCoredump"
    description = "Verifies there are no core dump files."
    categories: ClassVar[list[str]] = ["system"]
    commands: ClassVar[list[AntaCommand | AntaTemplate]] = [AntaCommand(command="show system coredump", ofmt="json")]

    @AntaTest.anta_test
    def test(self) -> None:
        """Main test function for VerifyCoredump."""
        command_output = self.instance_commands[0].json_output
        core_files = command_output["coreFiles"]
        if "minidump" in core_files:
            core_files.remove("minidump")
        if not core_files:
            self.result.is_success()
        else:
            self.result.is_failure(f"Core dump(s) have been found: {core_files}")


class VerifyAgentLogs(AntaTest):
    """Verifies that no agent crash reports are present on the device.

    Expected Results:
      * Success: The test will pass if there is NO agent crash reported.
      * Failure: The test will fail if any agent crashes are reported.
    """

    name = "VerifyAgentLogs"
    description = "Verifies there are no agent crash reports."
    categories: ClassVar[list[str]] = ["system"]
    commands: ClassVar[list[AntaCommand | AntaTemplate]] = [AntaCommand(command="show agent logs crash", ofmt="text")]

    @AntaTest.anta_test
    def test(self) -> None:
        """Main test function for VerifyAgentLogs."""
        command_output = self.instance_commands[0].text_output
        if len(command_output) == 0:
            self.result.is_success()
        else:
            pattern = re.compile(r"^===> (.*?) <===$", re.MULTILINE)
            agents = "\n * ".join(pattern.findall(command_output))
            self.result.is_failure(f"Device has reported agent crashes:\n * {agents}")


class VerifyCPUUtilization(AntaTest):
    """Verifies whether the CPU utilization is below 75%.

    Expected Results:
      * Success: The test will pass if the CPU utilization is below 75%.
      * Failure: The test will fail if the CPU utilization is over 75%.
    """

    name = "VerifyCPUUtilization"
    description = "Verifies whether the CPU utilization is below 75%."
    categories: ClassVar[list[str]] = ["system"]
    commands: ClassVar[list[AntaCommand | AntaTemplate]] = [AntaCommand(command="show processes top once")]

    @AntaTest.anta_test
    def test(self) -> None:
        """Main test function for VerifyCPUUtilization."""
        command_output = self.instance_commands[0].json_output
        command_output_data = command_output["cpuInfo"]["%Cpu(s)"]["idle"]
        if command_output_data > CPU_IDLE_THRESHOLD:
            self.result.is_success()
        else:
            self.result.is_failure(f"Device has reported a high CPU utilization: {100 - command_output_data}%")


class VerifyMemoryUtilization(AntaTest):
    """Verifies whether the memory utilization is below 75%.

    Expected Results:
      * Success: The test will pass if the memory utilization is below 75%.
      * Failure: The test will fail if the memory utilization is over 75%.
    """

    name = "VerifyMemoryUtilization"
    description = "Verifies whether the memory utilization is below 75%."
    categories: ClassVar[list[str]] = ["system"]
    commands: ClassVar[list[AntaCommand | AntaTemplate]] = [AntaCommand(command="show version")]

    @AntaTest.anta_test
    def test(self) -> None:
        """Main test function for VerifyMemoryUtilization."""
        command_output = self.instance_commands[0].json_output
        memory_usage = command_output["memFree"] / command_output["memTotal"]
        if memory_usage > MEMORY_THRESHOLD:
            self.result.is_success()
        else:
            self.result.is_failure(f"Device has reported a high memory usage: {(1 - memory_usage)*100:.2f}%")


class VerifyFileSystemUtilization(AntaTest):
    """Verifies that no partition is utilizing more than 75% of its disk space.

    Expected Results:
      * Success: The test will pass if all partitions are using less than 75% of its disk space.
      * Failure: The test will fail if any partitions are using more than 75% of its disk space.
    """

    name = "VerifyFileSystemUtilization"
    description = "Verifies that no partition is utilizing more than 75% of its disk space."
    categories: ClassVar[list[str]] = ["system"]
    commands: ClassVar[list[AntaCommand | AntaTemplate]] = [AntaCommand(command="bash timeout 10 df -h", ofmt="text")]

    @AntaTest.anta_test
    def test(self) -> None:
        """Main test function for VerifyFileSystemUtilization."""
        command_output = self.instance_commands[0].text_output
        self.result.is_success()
        for line in command_output.split("\n")[1:]:
            if "loop" not in line and len(line) > 0 and (percentage := int(line.split()[4].replace("%", ""))) > DISK_SPACE_THRESHOLD:
                self.result.is_failure(f"Mount point {line} is higher than 75%: reported {percentage}%")


class VerifyNTP(AntaTest):
    """Verifies that the Network Time Protocol (NTP) is synchronized.

    Expected Results:
      * Success: The test will pass if the NTP is synchronised.
      * Failure: The test will fail if the NTP is NOT synchronised.
    """

    name = "VerifyNTP"
    description = "Verifies if NTP is synchronised."
    categories: ClassVar[list[str]] = ["system"]
    commands: ClassVar[list[AntaCommand | AntaTemplate]] = [AntaCommand(command="show ntp status", ofmt="text")]

    @AntaTest.anta_test
    def test(self) -> None:
        """Main test function for VerifyNTP."""
        command_output = self.instance_commands[0].text_output
        if command_output.split("\n")[0].split(" ")[0] == "synchronised":
            self.result.is_success()
        else:
            data = command_output.split("\n")[0]
            self.result.is_failure(f"The device is not synchronized with the configured NTP server(s): '{data}'")
