# Copyright (c) 2024-2025 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Module related to PTP tests."""

# Pyright does not understand AntaTest.Input typing
# pyright: reportAttributeAccessIssue=false
from __future__ import annotations

from typing import TYPE_CHECKING, ClassVar

from anta.decorators import skip_on_platforms
from anta.models import AntaCommand, AntaTest

if TYPE_CHECKING:
    from anta.models import AntaTemplate


class VerifyPtpModeStatus(AntaTest):
    """Verifies that the device is configured as a PTP Boundary Clock.

    Expected Results
    ----------------
    * Success: The test will pass if the device is a BC.
    * Failure: The test will fail if the device is not a BC.
    * Skipped: The test will be skipped if PTP is not configured on the device.

    Examples
    --------
    ```yaml
    anta.tests.ptp:
      - VerifyPtpModeStatus:
    ```
    """

    categories: ClassVar[list[str]] = ["ptp"]
    commands: ClassVar[list[AntaCommand | AntaTemplate]] = [AntaCommand(command="show ptp", revision=2)]

    @skip_on_platforms(["cEOSLab", "vEOS-lab", "cEOSCloudLab", "vEOS"])
    @AntaTest.anta_test
    def test(self) -> None:
        """Main test function for VerifyPtpModeStatus."""
        command_output = self.instance_commands[0].json_output

        if (ptp_mode := command_output.get("ptpMode")) is None:
            self.result.is_skipped("PTP is not configured")
            return

        if ptp_mode != "ptpBoundaryClock":
            self.result.is_failure(f"Not configured as a PTP Boundary Clock - Actual: {ptp_mode}")
        else:
            self.result.is_success()


class VerifyPtpGMStatus(AntaTest):
    """Verifies that the device is locked to a valid PTP Grandmaster.

    To test PTP failover, re-run the test with a secondary GMID configured.

    Expected Results
    ----------------
    * Success: The test will pass if the device is locked to the provided Grandmaster.
    * Failure: The test will fail if the device is not locked to the provided Grandmaster.
    * Skipped: The test will be skipped if PTP is not configured on the device.

    Examples
    --------
    ```yaml
    anta.tests.ptp:
      - VerifyPtpGMStatus:
          gmid: 0xec:46:70:ff:fe:00:ff:a9
    ```
    """

    class Input(AntaTest.Input):
        """Input model for the VerifyPtpGMStatus test."""

        gmid: str
        """Identifier of the Grandmaster to which the device should be locked."""

    categories: ClassVar[list[str]] = ["ptp"]
    commands: ClassVar[list[AntaCommand | AntaTemplate]] = [AntaCommand(command="show ptp", revision=2)]

    @skip_on_platforms(["cEOSLab", "vEOS-lab", "cEOSCloudLab", "vEOS"])
    @AntaTest.anta_test
    def test(self) -> None:
        """Main test function for VerifyPtpGMStatus."""
        self.result.is_success()
        command_output = self.instance_commands[0].json_output

        if (ptp_clock_summary := command_output.get("ptpClockSummary")) is None:
            self.result.is_skipped("PTP is not configured")
            return

        if (act_gmid := ptp_clock_summary["gmClockIdentity"]) != self.inputs.gmid:
            self.result.is_failure(f"The device is locked to the incorrect Grandmaster - Expected: {self.inputs.gmid} Actual: {act_gmid}")


class VerifyPtpLockStatus(AntaTest):
    """Verifies that the device was locked to the upstream PTP GM in the last minute.

    Expected Results
    ----------------
    * Success: The test will pass if the device was locked to the upstream GM in the last minute.
    * Failure: The test will fail if the device was not locked to the upstream GM in the last minute.
    * Skipped: The test will be skipped if PTP is not configured on the device.

    Examples
    --------
    ```yaml
    anta.tests.ptp:
      - VerifyPtpLockStatus:
    ```
    """

    categories: ClassVar[list[str]] = ["ptp"]
    commands: ClassVar[list[AntaCommand | AntaTemplate]] = [AntaCommand(command="show ptp", revision=2)]

    @skip_on_platforms(["cEOSLab", "vEOS-lab", "cEOSCloudLab", "vEOS"])
    @AntaTest.anta_test
    def test(self) -> None:
        """Main test function for VerifyPtpLockStatus."""
        threshold = 60
        command_output = self.instance_commands[0].json_output

        if (ptp_clock_summary := command_output.get("ptpClockSummary")) is None:
            self.result.is_skipped("PTP is not configured")
            return

        time_difference = ptp_clock_summary["currentPtpSystemTime"] - ptp_clock_summary["lastSyncTime"]

        if time_difference >= threshold:
            self.result.is_failure(f"Lock is more than {threshold}s old - Actual: {time_difference}s")
        else:
            self.result.is_success()


class VerifyPtpOffset(AntaTest):
    """Verifies that the PTP timing offset is within +/- 1000ns from the master clock.

    Expected Results
    ----------------
    * Success: The test will pass if the PTP timing offset is within +/- 1000ns from the master clock.
    * Failure: The test will fail if the PTP timing offset is greater than +/- 1000ns from the master clock.
    * Skipped: The test will be skipped if PTP is not configured on the device.

    Examples
    --------
    ```yaml
    anta.tests.ptp:
      - VerifyPtpOffset:
    ```
    """

    categories: ClassVar[list[str]] = ["ptp"]
    commands: ClassVar[list[AntaCommand | AntaTemplate]] = [AntaCommand(command="show ptp monitor", revision=1)]

    @skip_on_platforms(["cEOSLab", "vEOS-lab", "cEOSCloudLab", "vEOS"])
    @AntaTest.anta_test
    def test(self) -> None:
        """Main test function for VerifyPtpOffset."""
        threshold = 1000
        self.result.is_success()
        command_output = self.instance_commands[0].json_output
        offset_interfaces: dict[str, list[int]] = {}
        if not command_output["ptpMonitorData"]:
            self.result.is_skipped("PTP is not configured")
            return

        for interface in command_output["ptpMonitorData"]:
            if abs(interface["offsetFromMaster"]) > threshold:
                offset_interfaces.setdefault(interface["intf"], []).append(interface["offsetFromMaster"])

        for interface, data in offset_interfaces.items():
            self.result.is_failure(f"Interface: {interface} - Timing offset from master is greater than +/- {threshold}ns: Actual: {', '.join(map(str, data))}")


class VerifyPtpPortModeStatus(AntaTest):
    """Verifies the PTP interfaces state.

    The interfaces can be in one of the following state: Master, Slave, Passive, or Disabled.

    Expected Results
    ----------------
    * Success: The test will pass if all PTP enabled interfaces are in a valid state.
    * Failure: The test will fail if there are no PTP enabled interfaces or if some interfaces are not in a valid state.

    Examples
    --------
    ```yaml
    anta.tests.ptp:
      - VerifyPtpPortModeStatus:
    ```
    """

    categories: ClassVar[list[str]] = ["ptp"]
    commands: ClassVar[list[AntaCommand | AntaTemplate]] = [AntaCommand(command="show ptp", revision=2)]

    @skip_on_platforms(["cEOSLab", "vEOS-lab", "cEOSCloudLab", "vEOS"])
    @AntaTest.anta_test
    def test(self) -> None:
        """Main test function for VerifyPtpPortModeStatus."""
        valid_state = ("psMaster", "psSlave", "psPassive", "psDisabled")
        command_output = self.instance_commands[0].json_output

        if not command_output["ptpIntfSummaries"]:
            self.result.is_failure("No interfaces are PTP enabled")
            return

        invalid_interfaces = [
            interface
            for interface in command_output["ptpIntfSummaries"]
            for vlan in command_output["ptpIntfSummaries"][interface]["ptpIntfVlanSummaries"]
            if vlan["portState"] not in valid_state
        ]

        if not invalid_interfaces:
            self.result.is_success()
        else:
            self.result.is_failure(f"The following interface(s) are not in a valid PTP state: {', '.join(invalid_interfaces)}")
