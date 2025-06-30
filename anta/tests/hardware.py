# Copyright (c) 2023-2025 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Module related to the hardware or environment tests."""

# Mypy does not understand AntaTest.Input typing
# mypy: disable-error-code=attr-defined
from __future__ import annotations

from typing import TYPE_CHECKING, ClassVar, Literal

from anta.custom_types import PositiveInteger, PowerSupplyFanStatus, PowerSupplyStatus
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
    * Success: The test will pass if the system temperature is `temperatureOk` and if checked, all sensor statuses and temperatures are within operational limits.
    * Failure: The test will fail if the system temperature is not `temperatureOk` or if any checked sensor reports a hardware fault or high temperature.

    Examples
    --------
    ```yaml
    anta.tests.hardware:
      - VerifyTemperature:
    ```
    """

    categories: ClassVar[list[str]] = ["hardware"]
    commands: ClassVar[list[AntaCommand | AntaTemplate]] = [AntaCommand(command="show system environment temperature", revision=1)]

    class Input(AntaTest.Input):
        """Input model for the VerifyTemperature test."""

        check_temp_sensors: bool = False
        """If True, also verifies the hardware status and temperature of individual sensors."""

    @skip_on_platforms(["cEOSLab", "vEOS-lab", "cEOSCloudLab", "vEOS"])
    @AntaTest.anta_test
    def test(self) -> None:
        """Main test function for VerifyTemperature."""
        self.result.is_success()
        command_output = self.instance_commands[0].json_output
        temperature_status = command_output.get("systemStatus", "")

        # Verify system temperature status
        if temperature_status != "temperatureOk":
            self.result.is_failure(f"Device temperature exceeds acceptable limits - Expected: temperatureOk Actual: {temperature_status}")

        # Check all sensors only if check_temp_sensors knob is set.
        if not self.inputs.check_temp_sensors:
            return

        temp_sensors = command_output["tempSensors"]
        for power_supply in command_output["powerSupplySlots"]:
            temp_sensors.extend(power_supply["tempSensors"])

        for sensor in temp_sensors:
            # Account for PhyAlaska chips that don't give current temp in 7020TR
            if "PhyAlaska" in (sensor_desc := sensor["description"]):
                self.logger.debug("Sensor: %s Description: %s has been ignored due to PhyAlaska in sensor description", sensor, sensor_desc)
                continue
            # Verify sensor hardware state
            if sensor["hwStatus"] != "ok":
                self.result.is_failure(f"Sensor: {sensor['name']} Description: {sensor_desc} - Invalid hardware status - Expected: ok Actual: {sensor['hwStatus']}")
            # Verify sensor current temperature
            if (act_temp := sensor["currentTemperature"]) + 5 >= (over_heat_threshold := sensor["overheatThreshold"]):
                self.result.is_failure(
                    f"Sensor: {sensor['name']} Description: {sensor_desc} - Temperature is getting high - Current: {act_temp} "
                    f"Overheat Threshold: {over_heat_threshold}"
                )


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
    * Success: The test will pass if all fans have a status within the accepted states and if a speed limit is provided,
     their speed is within that limit.
    * Failure: The test will fail if any fan status is not in the accepted states or if any fan configured speed exceeds
     the speed limit, if provided.

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
        configured_fan_speed_limit: PositiveInteger | None = None
        """The upper limit for the configured fan speed."""

    @skip_on_platforms(["cEOSLab", "vEOS-lab", "cEOSCloudLab", "vEOS"])
    @AntaTest.anta_test
    def test(self) -> None:
        """Main test function for VerifyEnvironmentCooling."""
        command_output = self.instance_commands[0].json_output
        self.result.is_success()
        # First go through power supplies fans
        for power_supply in command_output.get("powerSupplySlots", []):
            for fan in power_supply.get("fans", []):
                # Verify the fan status
                if (state := fan["status"]) not in self.inputs.states:
                    self.result.is_failure(
                        f"Power Slot: {power_supply['label']} Fan: {fan['label']} - Invalid state - Expected: {', '.join(self.inputs.states)} Actual: {state}"
                    )
                # Verify the configured fan speed
                elif self.inputs.configured_fan_speed_limit and fan["configuredSpeed"] > self.inputs.configured_fan_speed_limit:
                    self.result.is_failure(
                        f"Power Slot: {power_supply['label']} Fan: {fan['label']} - High fan speed - Expected: < {self.inputs.configured_fan_speed_limit} "
                        f"Actual: {fan['configuredSpeed']}"
                    )
        # Then go through fan trays
        for fan_tray in command_output.get("fanTraySlots", []):
            for fan in fan_tray.get("fans", []):
                # Verify the fan status
                if (state := fan["status"]) not in self.inputs.states:
                    self.result.is_failure(
                        f"Fan Tray: {fan_tray['label']} Fan: {fan['label']} - Invalid state - Expected: {', '.join(self.inputs.states)} Actual: {state}"
                    )
                # Verify the configured fan speed
                elif self.inputs.configured_fan_speed_limit and fan["configuredSpeed"] > self.inputs.configured_fan_speed_limit:
                    self.result.is_failure(
                        f"Fan Tray: {fan_tray['label']} Fan: {fan['label']} - High fan speed - Expected: < {self.inputs.configured_fan_speed_limit} "
                        f"Actual: {fan['configuredSpeed']}"
                    )


class VerifyEnvironmentPower(AntaTest):
    """Verifies the power supplies state and input voltage.

    Expected Results
    ----------------
    * Success: The test will pass if all power supplies are in an accepted state and their input voltage is greater than or equal to `min_input_voltage`
    (if provided).
    * Failure: The test will fail if any power supply is in an unaccepted state or its input voltage is less than `min_input_voltage` (if provided).

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
        """List of accepted states for power supplies."""
        min_input_voltage: PositiveInteger | None = None
        """Optional minimum input voltage (Volts) to verify."""

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

            # Verify if the power supply voltage is greater than the minimum input voltage
            if self.inputs.min_input_voltage and value["inputVoltage"] < self.inputs.min_input_voltage:
                self.result.is_failure(
                    f"Power Supply: {power_supply} - Input voltage mismatch - Expected: > {self.inputs.min_input_voltage} Actual: {value['inputVoltage']}"
                )


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


class VerifySupervisorRedundancy(AntaTest):
    """Verifies the redundancy protocol configured on the active supervisor.

    Expected Results
    ----------------
    * Success: The test will pass if the expected redundancy protocol is configured and operational, and if switchover is ready.
    * Failure: The test will fail if the expected redundancy protocol is not configured, not operational, or if switchover is not ready.
    * Skipped: The test will be skipped if the peer supervisor card is not inserted.

    Examples
    --------
    ```yaml
    anta.tests.hardware:
      - VerifySupervisorRedundancy:
    ```
    """

    categories: ClassVar[list[str]] = ["hardware"]
    commands: ClassVar[list[AntaCommand | AntaTemplate]] = [AntaCommand(command="show redundancy status", revision=1)]

    class Input(AntaTest.Input):
        """Input model for the VerifySupervisorRedundancy test."""

        redundancy_proto: Literal["sso", "rpr", "simplex"] = "sso"
        """Configured redundancy protocol."""

    @skip_on_platforms(["cEOSLab", "vEOS-lab", "cEOSCloudLab", "vEOS"])
    @AntaTest.anta_test
    def test(self) -> None:
        """Main test function for VerifySupervisorRedundancy."""
        self.result.is_success()
        command_output = self.instance_commands[0].json_output

        # Verify peer supervisor card insertion
        if command_output["peerState"] == "notInserted":
            self.result.is_skipped("Peer supervisor card not inserted")
            return

        # Verify that the expected redundancy protocol is configured
        if (act_proto := command_output["configuredProtocol"]) != self.inputs.redundancy_proto:
            self.result.is_failure(f"Configured redundancy protocol mismatch - Expected {self.inputs.redundancy_proto} Actual: {act_proto}")

        # Verify that the expected redundancy protocol configured and operational
        elif (act_proto := command_output["operationalProtocol"]) != self.inputs.redundancy_proto:
            self.result.is_failure(f"Operational redundancy protocol mismatch - Expected {self.inputs.redundancy_proto} Actual: {act_proto}")

        # Verify that the expected redundancy protocol configured, operational and switchover ready
        elif not command_output["switchoverReady"]:
            self.result.is_failure(f"Redundancy protocol switchover status mismatch - Expected: True Actual: {command_output['switchoverReady']}")
