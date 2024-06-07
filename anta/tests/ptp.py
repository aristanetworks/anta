# Copyright (c) 2024 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Module related to PTP tests."""

# Mypy does not understand AntaTest.Input typing
# mypy: disable-error-code=attr-defined
from __future__ import annotations

from typing import TYPE_CHECKING, ClassVar

from anta.decorators import skip_on_platforms
from anta.models import AntaCommand, AntaTest

if TYPE_CHECKING:
    from anta.models import AntaTemplate


class VerifyPtpModeStatus(AntaTest):
    """Verifies that the device is configured as a Precision Time Protocol (PTP) Boundary Clock (BC).

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

    name = "VerifyPtpModeStatus"
    description = "Verifies that the device is configured as a PTP Boundary Clock."
    categories: ClassVar[list[str]] = ["ptp"]
    commands: ClassVar[list[AntaCommand | AntaTemplate]] = [AntaCommand(command="show ptp", revision=2)]

    @skip_on_platforms(["cEOSLab", "vEOS-lab", "cEOSCloudLab"])
    @AntaTest.anta_test
    def test(self) -> None:
        """Main test function for VerifyPtpModeStatus."""
        command_output = self.instance_commands[0].json_output

        if (ptp_mode := command_output.get("ptpMode")) is None:
            self.result.is_skipped("PTP is not configured")
            return

        if ptp_mode != "ptpBoundaryClock":
            self.result.is_failure(f"The device is not configured as a PTP Boundary Clock: '{ptp_mode}'")
        else:
            self.result.is_success()


class VerifyPtpGMStatus(AntaTest):
    """Verifies that the device is locked to a valid Precision Time Protocol (PTP) Grandmaster (GM).

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

    name = "VerifyPtpGMStatus"
    description = "Verifies that the device is locked to a valid PTP Grandmaster."
    categories: ClassVar[list[str]] = ["ptp"]
    commands: ClassVar[list[AntaCommand | AntaTemplate]] = [AntaCommand(command="show ptp", revision=2)]

    @skip_on_platforms(["cEOSLab", "vEOS-lab", "cEOSCloudLab"])
    @AntaTest.anta_test
    def test(self) -> None:
        """Main test function for VerifyPtpGMStatus."""
        command_output = self.instance_commands[0].json_output

        if (ptp_clock_summary := command_output.get("ptpClockSummary")) is None:
            self.result.is_skipped("PTP is not configured")
            return

        if ptp_clock_summary["gmClockIdentity"] != self.inputs.gmid:
            self.result.is_failure(
                f"The device is locked to the following Grandmaster: '{ptp_clock_summary['gmClockIdentity']}', which differ from the expected one.",
            )
        else:
            self.result.is_success()


class VerifyPtpLockStatus(AntaTest):
    """Verifies that the device was locked to the upstream Precision Time Protocol (PTP) Grandmaster (GM) in the last minute.

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

    name = "VerifyPtpLockStatus"
    description = "Verifies that the device was locked to the upstream PTP GM in the last minute."
    categories: ClassVar[list[str]] = ["ptp"]
    commands: ClassVar[list[AntaCommand | AntaTemplate]] = [AntaCommand(command="show ptp", revision=2)]

    @skip_on_platforms(["cEOSLab", "vEOS-lab", "cEOSCloudLab"])
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
            self.result.is_failure(f"The device lock is more than {threshold}s old: {time_difference}s")
        else:
            self.result.is_success()


class VerifyPtpOffset(AntaTest):
    """Verifies that the Precision Time Protocol (PTP) timing offset is within +/- 1000ns from the master clock.

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

    name = "VerifyPtpOffset"
    description = "Verifies that the PTP timing offset is within +/- 1000ns from the master clock."
    categories: ClassVar[list[str]] = ["ptp"]
    commands: ClassVar[list[AntaCommand | AntaTemplate]] = [AntaCommand(command="show ptp monitor", revision=1)]

    @skip_on_platforms(["cEOSLab", "vEOS-lab", "cEOSCloudLab"])
    @AntaTest.anta_test
    def test(self) -> None:
        """Main test function for VerifyPtpOffset."""
        threshold = 1000
        offset_interfaces: dict[str, list[int]] = {}
        command_output = self.instance_commands[0].json_output

        if not command_output["ptpMonitorData"]:
            self.result.is_skipped("PTP is not configured")
            return

        for interface in command_output["ptpMonitorData"]:
            if abs(interface["offsetFromMaster"]) > threshold:
                offset_interfaces.setdefault(interface["intf"], []).append(interface["offsetFromMaster"])

        if offset_interfaces:
            self.result.is_failure(f"The device timing offset from master is greater than +/- {threshold}ns: {offset_interfaces}")
        else:
            self.result.is_success()


class VerifyPtpPortModeStatus(AntaTest):
    """Verifies that all interfaces are in a valid Precision Time Protocol (PTP) state.

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

    name = "VerifyPtpPortModeStatus"
    description = "Verifies the PTP interfaces state."
    categories: ClassVar[list[str]] = ["ptp"]
    commands: ClassVar[list[AntaCommand | AntaTemplate]] = [AntaCommand(command="show ptp", revision=2)]

    @skip_on_platforms(["cEOSLab", "vEOS-lab", "cEOSCloudLab"])
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
            self.result.is_failure(f"The following interface(s) are not in a valid PTP state: '{invalid_interfaces}'")
