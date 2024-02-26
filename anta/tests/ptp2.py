# Copyright (c) 2024 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""
Test functions related to PTP tests
"""
# Mypy does not understand AntaTest.Input typing
# mypy: disable-error-code=attr-defined
from anta.decorators import skip_on_platforms
from anta.models import AntaCommand, AntaTest


class PtpModeStatus(AntaTest):
    """
    This test verifies that the device is in Boundary Clock Mode
    """

    name = "PtpModeStatus"
    description = "Check Boundary Clock mode is enabled"
    categories = ["hardware"]
    commands = [AntaCommand(command="show ptp", ofmt="json")]

    # Verify that all switches are running Boundary Clock

    @skip_on_platforms(["cEOSLab", "vEOS-lab"])
    @AntaTest.anta_test
    def test(self) -> None:
        command_output = self.instance_commands[0].json_output
        ptp_mode = command_output["ptpMode"] if "ptpMode" in command_output.keys() else ""
        if ptp_mode == "ptpBoundaryClock":
            self.result.is_success(f"Valid PTP mode found: '{ptp_mode}'")
        else:
            self.result.is_failure(f"Device is not configured as a Boundary Clock: '{ptp_mode}'")


class PtpGMStatus(AntaTest):
    """
    This test verifies that the device is locked to a valid GM
    The user should provide a single "validGM" as an input
    To test PTP failover, re-run the test with secondary GMid configured.
    """

    class Input(AntaTest.Input):  # pylint: disable=missing-class-docstring
        validGM: str
        """ expected validGM as input from the user in nrfu file"""

    name = "PtpGMStatus"
    description = "Check device is locked to an allowed GM"
    categories = ["hardware"]
    commands = [AntaCommand(command="show ptp", ofmt="json")]

    # Verify that all switches are locked to the same GMID, and that this GMID is one of the provided GMs

    @skip_on_platforms(["cEOSLab", "vEOS-lab"])
    @AntaTest.anta_test
    def test(self) -> None:
        command_output = self.instance_commands[0].json_output
        validGM = self.inputs.validGM
        ptp_gmid = command_output["ptpClockSummary"]["gmClockIdentity"] if "gmClockIdentity" in command_output["ptpClockSummary"].keys() else ""
        # print(command_output["ptpClockSummary"]["gmClockIdentity"])

        if ptp_gmid == validGM:
            self.result.is_success(f"Valid GM found: '{ptp_gmid}'")
        else:
            self.result.is_failure(f"Device is not locked to valid GM: '{ptp_gmid}'")


class PtpLockStatus(AntaTest):
    """
    This test verifies that the device as a recent PTP lock
    """

    name = "PtpLockStatus"
    description = "Check that the device was locked to the upstream GM in the last minute"
    categories = ["hardware"]
    commands = [AntaCommand(command="show ptp", ofmt="json")]

    # Verify that last lock time is within the last minute

    @skip_on_platforms(["cEOSLab", "vEOS-lab"])
    @AntaTest.anta_test
    def test(self) -> None:
        command_output = self.instance_commands[0].json_output
        ptp_lastSyncTime = command_output["ptpClockSummary"]["lastSyncTime"] if "lastSyncTime" in command_output["ptpClockSummary"].keys() else ""
        ptp_currentPtpSystemTime = (
            command_output["ptpClockSummary"]["currentPtpSystemTime"] if "currentPtpSystemTime" in command_output["ptpClockSummary"].keys() else ""
        )
        # print(command_output["ptpClockSummary"])

        time_to_last_sync = ptp_currentPtpSystemTime - ptp_lastSyncTime

        if time_to_last_sync <= 60:
            self.result.is_success(f"Current PTP lock found: '{time_to_last_sync}'s")
        else:
            self.result.is_failure(f"Device Lock is old: '{time_to_last_sync}'s")


class PtpOmfStatus(AntaTest):
    """
    This test verifies that the has a reasonable offset from master (jitter) level
    """

    name = "PtpOfmStatus"
    description = "Check that the Offset From Master is within +/- 1000ns"
    categories = ["hardware"]
    commands = [AntaCommand(command="show ptp monitor", ofmt="json")]

    # Verify that offset from master is acceptable

    @skip_on_platforms(["cEOSLab", "vEOS-lab"])
    @AntaTest.anta_test
    def test(self) -> None:
        command_output = self.instance_commands[0].json_output
        # print(command_output["ptpMonitorData"])
        offsetMaxPos = 0
        offsetMaxNeg = 0

        for interface in command_output["ptpMonitorData"]:
            # print(interface["offsetFromMaster"])
            if interface["offsetFromMaster"] > offsetMaxPos:
                offsetMaxPos = interface["offsetFromMaster"]
            elif interface["offsetFromMaster"] < offsetMaxNeg:
                offsetMaxNeg = interface["offsetFromMaster"]

        if (offsetMaxPos < 1000) and (offsetMaxNeg > -1000):
            self.result.is_success(f"Max Offset From Master (Max/Min): '{offsetMaxPos, offsetMaxNeg}'s")
        else:
            self.result.is_failure(f"Bad max Offset From Master (Max/Min): '{offsetMaxPos, offsetMaxNeg}'")


class PtpPortModeStatus(AntaTest):
    """
    This test verifies that all ports are in stable PTP modes
    """

    name = "PtpPortModeStatus"
    description = "Check that all PTP enabled ports are not in transitory states"
    categories = ["hardware"]
    commands = [AntaCommand(command="show ptp", ofmt="json")]

    # Verify that ports are either Master / Slave / Passive or Disabled
    @skip_on_platforms(["cEOSLab", "vEOS-lab"])
    @AntaTest.anta_test
    def test(self) -> None:
        validPortModes = ["psMaster", "psSlave", "psPassive", "psDisabled"]
        invalidPorts = 0
        command_output = self.instance_commands[0].json_output
        # print(command_output["ptpIntfSummaries"])

        for interface in command_output["ptpIntfSummaries"]:
            # print (interface)
            # print(command_output["ptpIntfSummaries"][interface]["ptpIntfVlanSummaries"][0]['portState'])
            for vlan in command_output["ptpIntfSummaries"][interface]["ptpIntfVlanSummaries"]:
                # print(vlan['portState'])
                if not vlan["portState"] in validPortModes:
                    invalidPorts += 1

        if invalidPorts == 0:
            self.result.is_success("Ports all in valid state")
        else:
            self.result.is_failure("Some ports are no in valid sates (Master / Slave / Passive / Disabled)")
