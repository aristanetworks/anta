# Copyright (c) 2023-2025 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Module related to system-level features and protocols tests."""

# Mypy does not understand AntaTest.Input typing
# mypy: disable-error-code=attr-defined
from __future__ import annotations

import re
from typing import TYPE_CHECKING, ClassVar

from anta.custom_types import PositiveInteger
from anta.input_models.system import NTPServer
from anta.models import AntaCommand, AntaTest
from anta.tools import get_value

if TYPE_CHECKING:
    from anta.models import AntaTemplate

CPU_IDLE_THRESHOLD = 25
MEMORY_THRESHOLD = 0.25
DISK_SPACE_THRESHOLD = 75


class VerifyUptime(AntaTest):
    """Verifies if the device uptime is higher than the provided minimum uptime value.

    Expected Results
    ----------------
    * Success: The test will pass if the device uptime is higher than the provided value.
    * Failure: The test will fail if the device uptime is lower than the provided value.

    Examples
    --------
    ```yaml
    anta.tests.system:
      - VerifyUptime:
          minimum: 86400
    ```
    """

    description = "Verifies the device uptime."
    categories: ClassVar[list[str]] = ["system"]
    commands: ClassVar[list[AntaCommand | AntaTemplate]] = [AntaCommand(command="show uptime", revision=1)]

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

    Expected Results
    ----------------
    * Success: The test will pass if there are NO reload causes or if the last reload was caused by the user or after an FPGA upgrade.
    * Failure: The test will fail if the last reload was NOT caused by the user or after an FPGA upgrade.
    * Error: The test will report an error if the reload cause is NOT available.

    Examples
    --------
    ```yaml
    anta.tests.system:
      - VerifyReloadCause:
    ```
    """

    categories: ClassVar[list[str]] = ["system"]
    commands: ClassVar[list[AntaCommand | AntaTemplate]] = [AntaCommand(command="show reload cause", revision=1)]

    @AntaTest.anta_test
    def test(self) -> None:
        """Main test function for VerifyReloadCause."""
        command_output = self.instance_commands[0].json_output
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

    Expected Results
    ----------------
    * Success: The test will pass if there are NO core dump(s) in /var/core.
    * Failure: The test will fail if there are core dump(s) in /var/core.

    Notes
    -----
    * This test will NOT check for minidump(s) generated by certain agents in /var/core/minidump.

    Examples
    --------
    ```yaml
    anta.tests.system:
      - VerifyCoredump:
    ```
    """

    description = "Verifies there are no core dump files."
    categories: ClassVar[list[str]] = ["system"]
    commands: ClassVar[list[AntaCommand | AntaTemplate]] = [AntaCommand(command="show system coredump", revision=1)]

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
            self.result.is_failure(f"Core dump(s) have been found: {', '.join(core_files)}")


class VerifyAgentLogs(AntaTest):
    """Verifies there are no agent crash reports.

    Expected Results
    ----------------
    * Success: The test will pass if there is NO agent crash reported.
    * Failure: The test will fail if any agent crashes are reported.

    Examples
    --------
    ```yaml
    anta.tests.system:
      - VerifyAgentLogs:
    ```
    """

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

    Expected Results
    ----------------
    * Success: The test will pass if the CPU utilization is below 75%.
    * Failure: The test will fail if the CPU utilization is over 75%.

    Examples
    --------
    ```yaml
    anta.tests.system:
      - VerifyCPUUtilization:
    ```
    """

    categories: ClassVar[list[str]] = ["system"]
    commands: ClassVar[list[AntaCommand | AntaTemplate]] = [AntaCommand(command="show processes top once", revision=1)]

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

    Expected Results
    ----------------
    * Success: The test will pass if the memory utilization is below 75%.
    * Failure: The test will fail if the memory utilization is over 75%.

    Examples
    --------
    ```yaml
    anta.tests.system:
      - VerifyMemoryUtilization:
    ```
    """

    categories: ClassVar[list[str]] = ["system"]
    commands: ClassVar[list[AntaCommand | AntaTemplate]] = [AntaCommand(command="show version", revision=1)]

    @AntaTest.anta_test
    def test(self) -> None:
        """Main test function for VerifyMemoryUtilization."""
        command_output = self.instance_commands[0].json_output
        memory_usage = command_output["memFree"] / command_output["memTotal"]
        if memory_usage > MEMORY_THRESHOLD:
            self.result.is_success()
        else:
            self.result.is_failure(f"Device has reported a high memory usage: {(1 - memory_usage) * 100:.2f}%")


class VerifyFileSystemUtilization(AntaTest):
    """Verifies that no partition is utilizing more than 75% of its disk space.

    Expected Results
    ----------------
    * Success: The test will pass if all partitions are using less than 75% of its disk space.
    * Failure: The test will fail if any partitions are using more than 75% of its disk space.

    Examples
    --------
    ```yaml
    anta.tests.system:
      - VerifyFileSystemUtilization:
    ```
    """

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

    Expected Results
    ----------------
    * Success: The test will pass if the NTP is synchronised.
    * Failure: The test will fail if the NTP is NOT synchronised.

    Examples
    --------
    ```yaml
    anta.tests.system:
      - VerifyNTP:
    ```
    """

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
            self.result.is_failure(f"The device is not synchronized with the configured NTP server(s) - Actual: {data}")


class VerifyNTPAssociations(AntaTest):
    """Verifies the Network Time Protocol (NTP) associations.

    Expected Results
    ----------------
    * Success: The test will pass if the Primary NTP server (marked as preferred) has the condition 'sys.peer' and
    all other NTP servers have the condition 'candidate'.
    * Failure: The test will fail if the Primary NTP server (marked as preferred) does not have the condition 'sys.peer' or
    if any other NTP server does not have the condition 'candidate'.

    Examples
    --------
    ```yaml
    anta.tests.system:
      - VerifyNTPAssociations:
          ntp_servers:
            - server_address: 1.1.1.1
              preferred: True
              stratum: 1
            - server_address: 2.2.2.2
              stratum: 2
            - server_address: 3.3.3.3
              stratum: 2
    ```
    """

    categories: ClassVar[list[str]] = ["system"]
    commands: ClassVar[list[AntaCommand | AntaTemplate]] = [AntaCommand(command="show ntp associations")]

    class Input(AntaTest.Input):
        """Input model for the VerifyNTPAssociations test."""

        ntp_servers: list[NTPServer]
        """List of NTP servers."""
        NTPServer: ClassVar[type[NTPServer]] = NTPServer

    @AntaTest.anta_test
    def test(self) -> None:
        """Main test function for VerifyNTPAssociations."""
        self.result.is_success()

        if not (peers := get_value(self.instance_commands[0].json_output, "peers")):
            self.result.is_failure("No NTP peers configured")
            return

        # Iterate over each NTP server.
        for ntp_server in self.inputs.ntp_servers:
            server_address = str(ntp_server.server_address)

            # We check `peerIpAddr` in the peer details - covering IPv4Address input, or the peer key - covering Hostname input.
            matching_peer = next((peer for peer, peer_details in peers.items() if (server_address in {peer_details["peerIpAddr"], peer})), None)

            if not matching_peer:
                self.result.is_failure(f"{ntp_server} - Not configured")
                continue

            # Collecting the expected/actual NTP peer details.
            exp_condition = "sys.peer" if ntp_server.preferred else "candidate"
            exp_stratum = ntp_server.stratum
            act_condition = get_value(peers[matching_peer], "condition")
            act_stratum = get_value(peers[matching_peer], "stratumLevel")

            if act_condition != exp_condition or act_stratum != exp_stratum:
                self.result.is_failure(f"{ntp_server} - Bad association - Condition: {act_condition}, Stratum: {act_stratum}")
