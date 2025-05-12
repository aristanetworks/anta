# Copyright (c) 2023-2025 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Module related to the hardware or environment tests."""

# Mypy does not understand AntaTest.Input typing
# mypy: disable-error-code=attr-defined
from __future__ import annotations

from typing import TYPE_CHECKING, ClassVar

from anta.custom_types import PowerSupplyFanStatus, PowerSupplyStatus
from anta.decorators import skip_on_platforms
from anta.models import AntaCommand, AntaTest

if TYPE_CHECKING:
    from anta.models import AntaTemplate


class VerifyTransceiversManufacturers(AntaTest):
    """Verifies if all the transceivers come from approved manufacturers.

    Expected Results
    ----------------
    * Success: The test will pass if all transceivers are from approved manufacturers.
    * Failure: The test will fail if some transceivers are from unapproved manufacturers.

    Examples
    --------
    ```yaml
    anta.tests.hardware:
      - VerifyTransceiversManufacturers:
          manufacturers:
            - Not Present
            - Arista Networks
            - Arastra, Inc.
    ```
    """

    categories: ClassVar[list[str]] = ["hardware"]
    commands: ClassVar[list[AntaCommand | AntaTemplate]] = [AntaCommand(command="show inventory", revision=2)]

    class Input(AntaTest.Input):
        """Input model for the VerifyTransceiversManufacturers test."""

        manufacturers: list[str]
        """List of approved transceivers manufacturers."""

    @skip_on_platforms(["cEOSLab", "vEOS-lab", "cEOSCloudLab", "vEOS"])
    @AntaTest.anta_test
    def test(self) -> None:
        """Main test function for VerifyTransceiversManufacturers."""
        self.result.is_success()
        command_output = self.instance_commands[0].json_output
        for interface, value in command_output["xcvrSlots"].items():
            if value["mfgName"] not in self.inputs.manufacturers:
                self.result.is_failure(
                    f"Interface: {interface} - Transceiver is from unapproved manufacturers - Expected: {', '.join(self.inputs.manufacturers)}"
                    f" Actual: {value['mfgName']}"
                )


class VerifyTemperature(AntaTest):
    """Verifies if the device temperature is within acceptable limits.

    Expected Results
    ----------------
    * Success: The test will pass if the device temperature is currently OK: 'temperatureOk'.
    * Failure: The test will fail if the device temperature is NOT OK.

    Examples
    --------
    ```yaml
    anta.tests.hardware:
      - VerifyTemperature:
    ```
    """

    categories: ClassVar[list[str]] = ["hardware"]
    commands: ClassVar[list[AntaCommand | AntaTemplate]] = [AntaCommand(command="show system environment temperature", revision=1)]

    @skip_on_platforms(["cEOSLab", "vEOS-lab", "cEOSCloudLab", "vEOS"])
    @AntaTest.anta_test
    def test(self) -> None:
        """Main test function for VerifyTemperature."""
        self.result.is_success()
        command_output = self.instance_commands[0].json_output
        temperature_status = command_output.get("systemStatus", "")
        if temperature_status != "temperatureOk":
            self.result.is_failure(f"Device temperature exceeds acceptable limits - Expected: temperatureOk Actual: {temperature_status}")


class VerifyTransceiversTemperature(AntaTest):
    """Verifies if all the transceivers are operating at an acceptable temperature.

    Expected Results
    ----------------
    * Success: The test will pass if all transceivers status are OK: 'ok'.
    * Failure: The test will fail if some transceivers are NOT OK.

    Examples
    --------
    ```yaml
    anta.tests.hardware:
      - VerifyTransceiversTemperature:
    ```
    """

    categories: ClassVar[list[str]] = ["hardware"]
    commands: ClassVar[list[AntaCommand | AntaTemplate]] = [AntaCommand(command="show system environment temperature transceiver", revision=1)]

    @skip_on_platforms(["cEOSLab", "vEOS-lab", "cEOSCloudLab", "vEOS"])
    @AntaTest.anta_test
    def test(self) -> None:
        """Main test function for VerifyTransceiversTemperature."""
        self.result.is_success()
        command_output = self.instance_commands[0].json_output
        sensors = command_output.get("tempSensors", "")
        for sensor in sensors:
            if sensor["hwStatus"] != "ok":
                self.result.is_failure(f"Sensor: {sensor['name']} - Invalid hardware state - Expected: ok Actual: {sensor['hwStatus']}")
            if sensor["alertCount"] != 0:
                self.result.is_failure(f"Sensor: {sensor['name']} - Incorrect alert counter - Expected: 0 Actual: {sensor['alertCount']}")


class VerifyEnvironmentSystemCooling(AntaTest):
    """Verifies the device's system cooling status.

    Expected Results
    ----------------
    * Success: The test will pass if the system cooling status is OK: 'coolingOk'.
    * Failure: The test will fail if the system cooling status is NOT OK.

    Examples
    --------
    ```yaml
    anta.tests.hardware:
      - VerifyEnvironmentSystemCooling:
    ```
    """

    categories: ClassVar[list[str]] = ["hardware"]
    commands: ClassVar[list[AntaCommand | AntaTemplate]] = [AntaCommand(command="show system environment cooling", revision=1)]

    @skip_on_platforms(["cEOSLab", "vEOS-lab", "cEOSCloudLab", "vEOS"])
    @AntaTest.anta_test
    def test(self) -> None:
        """Main test function for VerifyEnvironmentSystemCooling."""
        command_output = self.instance_commands[0].json_output
        sys_status = command_output.get("systemStatus", "")
        self.result.is_success()
        if sys_status != "coolingOk":
            self.result.is_failure(f"Device system cooling status invalid - Expected: coolingOk Actual: {sys_status}")


class VerifyEnvironmentCooling(AntaTest):
    """Verifies the status of power supply fans and all fan trays.

    Expected Results
    ----------------
    * Success: The test will pass if the fans status are within the accepted states list.
    * Failure: The test will fail if some fans status is not within the accepted states list.

    Examples
    --------
    ```yaml
    anta.tests.hardware:
      - VerifyEnvironmentCooling:
          states:
            - ok
    ```
    """

    categories: ClassVar[list[str]] = ["hardware"]
    commands: ClassVar[list[AntaCommand | AntaTemplate]] = [AntaCommand(command="show system environment cooling", revision=1)]

    class Input(AntaTest.Input):
        """Input model for the VerifyEnvironmentCooling test."""

        states: list[PowerSupplyFanStatus]
        """List of accepted states of fan status."""

    @skip_on_platforms(["cEOSLab", "vEOS-lab", "cEOSCloudLab", "vEOS"])
    @AntaTest.anta_test
    def test(self) -> None:
        """Main test function for VerifyEnvironmentCooling."""
        command_output = self.instance_commands[0].json_output
        self.result.is_success()
        # First go through power supplies fans
        for power_supply in command_output.get("powerSupplySlots", []):
            for fan in power_supply.get("fans", []):
                if (state := fan["status"]) not in self.inputs.states:
                    self.result.is_failure(
                        f"Power Slot: {power_supply['label']} Fan: {fan['label']} - Invalid state - Expected: {', '.join(self.inputs.states)} Actual: {state}"
                    )
        # Then go through fan trays
        for fan_tray in command_output.get("fanTraySlots", []):
            for fan in fan_tray.get("fans", []):
                if (state := fan["status"]) not in self.inputs.states:
                    self.result.is_failure(
                        f"Fan Tray: {fan_tray['label']} Fan: {fan['label']} - Invalid state - Expected: {', '.join(self.inputs.states)} Actual: {state}"
                    )


class VerifyEnvironmentPower(AntaTest):
    """Verifies the power supplies status.

    Expected Results
    ----------------
    * Success: The test will pass if the power supplies status are within the accepted states list.
    * Failure: The test will fail if some power supplies status is not within the accepted states list.

    Examples
    --------
    ```yaml
    anta.tests.hardware:
      - VerifyEnvironmentPower:
          states:
            - ok
    ```
    """

    categories: ClassVar[list[str]] = ["hardware"]
    commands: ClassVar[list[AntaCommand | AntaTemplate]] = [AntaCommand(command="show system environment power", revision=1)]

    class Input(AntaTest.Input):
        """Input model for the VerifyEnvironmentPower test."""

        states: list[PowerSupplyStatus]
        """List of accepted states list of power supplies status."""

    @skip_on_platforms(["cEOSLab", "vEOS-lab", "cEOSCloudLab", "vEOS"])
    @AntaTest.anta_test
    def test(self) -> None:
        """Main test function for VerifyEnvironmentPower."""
        self.result.is_success()
        command_output = self.instance_commands[0].json_output
        power_supplies = command_output.get("powerSupplies", "{}")
        for power_supply, value in dict(power_supplies).items():
            if (state := value["state"]) not in self.inputs.states:
                self.result.is_failure(f"Power Slot: {power_supply} - Invalid power supplies state - Expected: {', '.join(self.inputs.states)} Actual: {state}")


class VerifyAdverseDrops(AntaTest):
    """Verifies there are no adverse drops on DCS-7280 and DCS-7500 family switches.

    Expected Results
    ----------------
    * Success: The test will pass if there are no adverse drops.
    * Failure: The test will fail if there are adverse drops.

    Examples
    --------
    ```yaml
    anta.tests.hardware:
      - VerifyAdverseDrops:
    ```
    """

    categories: ClassVar[list[str]] = ["hardware"]
    commands: ClassVar[list[AntaCommand | AntaTemplate]] = [AntaCommand(command="show hardware counter drop", revision=1)]

    @skip_on_platforms(["cEOSLab", "vEOS-lab", "cEOSCloudLab", "vEOS"])
    @AntaTest.anta_test
    def test(self) -> None:
        """Main test function for VerifyAdverseDrops."""
        self.result.is_success()
        command_output = self.instance_commands[0].json_output
        total_adverse_drop = command_output.get("totalAdverseDrops", "")
        if total_adverse_drop != 0:
            self.result.is_failure(f"Incorrect total adverse drops counter - Expected: 0 Actual: {total_adverse_drop}")


class VerifyredundencySso(AntaTest):
    """Verifies that the redundancy SSO is enabled.

    Expected Results
    ----------------
    * Success: The test will pass if redundancy protocol SSO is configured and operational and switchover is ready.
    * Failure: The test will fail if the redundancy protocol SSO is not configured, not operational, or switchover is not ready.
    * Skipped: The test will be skipped if the peer supervisor card is not inserted.

    Examples
    --------
    ```yaml
    anta.tests.hardware:
      - VerifyredundencySso:
    ```
    """

    categories: ClassVar[list[str]] = ["hardware"]
    commands: ClassVar[list[AntaCommand | AntaTemplate]] = [AntaCommand(command="show redundancy status", revision=1)]

    @skip_on_platforms(["cEOSLab", "vEOS-lab", "cEOSCloudLab", "vEOS"])
    @AntaTest.anta_test
    def test(self) -> None:
        """Main test function for VerifyredundencySso."""
        self.result.is_success()
        command_output = self.instance_commands[0].json_output
        # Verify peer supervisor card insertion
        if command_output["peerState"] == "notInserted":
            self.result.is_skipped("Peer supervisor card not inserted")
        # Verify redundancy protocol SSO configured
        elif command_output["configuredProtocol"] != "sso":
            self.result.is_failure("Redundancy protocol SSO not configured")
        # Verify redundancy protocol SSO is configured and operational
        elif command_output["operationalProtocol"] != "sso":
            self.result.is_failure("Redundancy protocol SSO configured but not operational")
        # Verify redundancy protocol SSO is configured, operational and switchover is not ready
        elif not command_output["switchoverReady"]:
            self.result.is_failure("Redundancy protocol SSO is configured and operational but switchover is not ready")
