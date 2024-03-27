# Copyright (c) 2023-2024 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Module related to the hardware or environment tests."""

# Mypy does not understand AntaTest.Input typing
# mypy: disable-error-code=attr-defined
from __future__ import annotations

from typing import TYPE_CHECKING, ClassVar

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

    name = "VerifyTransceiversManufacturers"
    description = "Verifies if all transceivers come from approved manufacturers."
    categories: ClassVar[list[str]] = ["hardware"]
    commands: ClassVar[list[AntaCommand | AntaTemplate]] = [AntaCommand(command="show inventory", revision=2)]

    class Input(AntaTest.Input):
        """Input model for the VerifyTransceiversManufacturers test."""

        manufacturers: list[str]
        """List of approved transceivers manufacturers."""

    @skip_on_platforms(["cEOSLab", "vEOS-lab", "cEOSCloudLab"])
    @AntaTest.anta_test
    def test(self) -> None:
        """Main test function for VerifyTransceiversManufacturers."""
        command_output = self.instance_commands[0].json_output
        wrong_manufacturers = {
            interface: value["mfgName"] for interface, value in command_output["xcvrSlots"].items() if value["mfgName"] not in self.inputs.manufacturers
        }
        if not wrong_manufacturers:
            self.result.is_success()
        else:
            self.result.is_failure(f"Some transceivers are from unapproved manufacturers: {wrong_manufacturers}")


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

    name = "VerifyTemperature"
    description = "Verifies the device temperature."
    categories: ClassVar[list[str]] = ["hardware"]
    commands: ClassVar[list[AntaCommand | AntaTemplate]] = [AntaCommand(command="show system environment temperature", revision=1)]

    @skip_on_platforms(["cEOSLab", "vEOS-lab", "cEOSCloudLab"])
    @AntaTest.anta_test
    def test(self) -> None:
        """Main test function for VerifyTemperature."""
        command_output = self.instance_commands[0].json_output
        temperature_status = command_output.get("systemStatus", "")
        if temperature_status == "temperatureOk":
            self.result.is_success()
        else:
            self.result.is_failure(f"Device temperature exceeds acceptable limits. Current system status: '{temperature_status}'")


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

    name = "VerifyTransceiversTemperature"
    description = "Verifies the transceivers temperature."
    categories: ClassVar[list[str]] = ["hardware"]
    commands: ClassVar[list[AntaCommand | AntaTemplate]] = [AntaCommand(command="show system environment temperature transceiver", revision=1)]

    @skip_on_platforms(["cEOSLab", "vEOS-lab", "cEOSCloudLab"])
    @AntaTest.anta_test
    def test(self) -> None:
        """Main test function for VerifyTransceiversTemperature."""
        command_output = self.instance_commands[0].json_output
        sensors = command_output.get("tempSensors", "")
        wrong_sensors = {
            sensor["name"]: {
                "hwStatus": sensor["hwStatus"],
                "alertCount": sensor["alertCount"],
            }
            for sensor in sensors
            if sensor["hwStatus"] != "ok" or sensor["alertCount"] != 0
        }
        if not wrong_sensors:
            self.result.is_success()
        else:
            self.result.is_failure(f"The following sensors are operating outside the acceptable temperature range or have raised alerts: {wrong_sensors}")


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

    name = "VerifyEnvironmentSystemCooling"
    description = "Verifies the system cooling status."
    categories: ClassVar[list[str]] = ["hardware"]
    commands: ClassVar[list[AntaCommand | AntaTemplate]] = [AntaCommand(command="show system environment cooling", revision=1)]

    @skip_on_platforms(["cEOSLab", "vEOS-lab", "cEOSCloudLab"])
    @AntaTest.anta_test
    def test(self) -> None:
        """Main test function for VerifyEnvironmentSystemCooling."""
        command_output = self.instance_commands[0].json_output
        sys_status = command_output.get("systemStatus", "")
        self.result.is_success()
        if sys_status != "coolingOk":
            self.result.is_failure(f"Device system cooling is not OK: '{sys_status}'")


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

    name = "VerifyEnvironmentCooling"
    description = "Verifies the status of power supply fans and all fan trays."
    categories: ClassVar[list[str]] = ["hardware"]
    commands: ClassVar[list[AntaCommand | AntaTemplate]] = [AntaCommand(command="show system environment cooling", revision=1)]

    class Input(AntaTest.Input):
        """Input model for the VerifyEnvironmentCooling test."""

        states: list[str]
        """List of accepted states of fan status."""

    @skip_on_platforms(["cEOSLab", "vEOS-lab", "cEOSCloudLab"])
    @AntaTest.anta_test
    def test(self) -> None:
        """Main test function for VerifyEnvironmentCooling."""
        command_output = self.instance_commands[0].json_output
        self.result.is_success()
        # First go through power supplies fans
        for power_supply in command_output.get("powerSupplySlots", []):
            for fan in power_supply.get("fans", []):
                if (state := fan["status"]) not in self.inputs.states:
                    self.result.is_failure(f"Fan {fan['label']} on PowerSupply {power_supply['label']} is: '{state}'")
        # Then go through fan trays
        for fan_tray in command_output.get("fanTraySlots", []):
            for fan in fan_tray.get("fans", []):
                if (state := fan["status"]) not in self.inputs.states:
                    self.result.is_failure(f"Fan {fan['label']} on Fan Tray {fan_tray['label']} is: '{state}'")


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

    name = "VerifyEnvironmentPower"
    description = "Verifies the power supplies status."
    categories: ClassVar[list[str]] = ["hardware"]
    commands: ClassVar[list[AntaCommand | AntaTemplate]] = [AntaCommand(command="show system environment power", revision=1)]

    class Input(AntaTest.Input):
        """Input model for the VerifyEnvironmentPower test."""

        states: list[str]
        """List of accepted states list of power supplies status."""

    @skip_on_platforms(["cEOSLab", "vEOS-lab", "cEOSCloudLab"])
    @AntaTest.anta_test
    def test(self) -> None:
        """Main test function for VerifyEnvironmentPower."""
        command_output = self.instance_commands[0].json_output
        power_supplies = command_output.get("powerSupplies", "{}")
        wrong_power_supplies = {
            powersupply: {"state": value["state"]} for powersupply, value in dict(power_supplies).items() if value["state"] not in self.inputs.states
        }
        if not wrong_power_supplies:
            self.result.is_success()
        else:
            self.result.is_failure(f"The following power supplies status are not in the accepted states list: {wrong_power_supplies}")


class VerifyAdverseDrops(AntaTest):
    """Verifies there are no adverse drops on DCS-7280 and DCS-7500 family switches (Arad/Jericho chips).

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

    name = "VerifyAdverseDrops"
    description = "Verifies there are no adverse drops on DCS-7280 and DCS-7500 family switches."
    categories: ClassVar[list[str]] = ["hardware"]
    commands: ClassVar[list[AntaCommand | AntaTemplate]] = [AntaCommand(command="show hardware counter drop", revision=1)]

    @skip_on_platforms(["cEOSLab", "vEOS-lab", "cEOSCloudLab"])
    @AntaTest.anta_test
    def test(self) -> None:
        """Main test function for VerifyAdverseDrops."""
        command_output = self.instance_commands[0].json_output
        total_adverse_drop = command_output.get("totalAdverseDrops", "")
        if total_adverse_drop == 0:
            self.result.is_success()
        else:
            self.result.is_failure(f"Device totalAdverseDrops counter is: '{total_adverse_drop}'")
