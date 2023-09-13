# Copyright (c) 2023 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""
Test functions related to the hardware or environment
"""
# Mypy does not understand AntaTest.Input typing
# mypy: disable-error-code=attr-defined
from __future__ import annotations

# Need to keep List for pydantic in python 3.8
from typing import List

from anta.decorators import skip_on_platforms
from anta.models import AntaCommand, AntaTest


class VerifyTransceiversManufacturers(AntaTest):
    """
    This test verifies if all the transceivers come from approved manufacturers.

    Expected Results:
      * success: The test will pass if all transceivers are from approved manufacturers.
      * failure: The test will fail if some transceivers are from unapproved manufacturers.
    """

    name = "VerifyTransceiversManufacturers"
    description = "Verifies the transceiver's manufacturer against a list of approved manufacturers."
    categories = ["hardware"]
    commands = [AntaCommand(command="show inventory", ofmt="json")]

    class Input(AntaTest.Input):  # pylint: disable=missing-class-docstring
        manufacturers: List[str]
        """List of approved transceivers manufacturers"""

    @skip_on_platforms(["cEOSLab", "vEOS-lab"])
    @AntaTest.anta_test
    def test(self) -> None:
        command_output = self.instance_commands[0].json_output
        wrong_manufacturers = {
            interface: value["mfgName"] for interface, value in command_output["xcvrSlots"].items() if value["mfgName"] not in self.inputs.manufacturers
        }
        if not wrong_manufacturers:
            self.result.is_success()
        else:
            self.result.is_failure(f"Some transceivers are from unapproved manufacturers: {wrong_manufacturers}")


class VerifyTemperature(AntaTest):
    """
    This test verifies if the device temperature is within acceptable limits.

    Expected Results:
      * success: The test will pass if the device temperature is currently OK: 'temperatureOk'.
      * failure: The test will fail if the device temperature is NOT OK.
    """

    name = "VerifyTemperature"
    description = "Verifies if the device temperature is within the acceptable range."
    categories = ["hardware"]
    commands = [AntaCommand(command="show system environment temperature", ofmt="json")]

    @skip_on_platforms(["cEOSLab", "vEOS-lab"])
    @AntaTest.anta_test
    def test(self) -> None:
        command_output = self.instance_commands[0].json_output
        temperature_status = command_output["systemStatus"] if "systemStatus" in command_output.keys() else ""
        if temperature_status == "temperatureOk":
            self.result.is_success()
        else:
            self.result.is_failure(f"Device temperature exceeds acceptable limits. Current system status: '{temperature_status}'")


class VerifyTransceiversTemperature(AntaTest):
    """
    This test verifies if all the transceivers are operating at an acceptable temperature.

    Expected Results:
          * success: The test will pass if all transceivers status are OK: 'ok'.
          * failure: The test will fail if some transceivers are NOT OK.
    """

    name = "VerifyTransceiversTemperature"
    description = "Verifies that all transceivers are operating within the acceptable temperature range."
    categories = ["hardware"]
    commands = [AntaCommand(command="show system environment temperature transceiver", ofmt="json")]

    @skip_on_platforms(["cEOSLab", "vEOS-lab"])
    @AntaTest.anta_test
    def test(self) -> None:
        command_output = self.instance_commands[0].json_output
        sensors = command_output["tempSensors"] if "tempSensors" in command_output.keys() else ""
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
    """
    This test verifies the device's system cooling.

    Expected Results:
      * success: The test will pass if the system cooling status is OK: 'coolingOk'.
      * failure: The test will fail if the system cooling status is NOT OK.
    """

    name = "VerifyEnvironmentSystemCooling"
    description = "Verifies the system cooling status."
    categories = ["hardware"]
    commands = [AntaCommand(command="show system environment cooling", ofmt="json")]

    @skip_on_platforms(["cEOSLab", "vEOS-lab"])
    @AntaTest.anta_test
    def test(self) -> None:
        command_output = self.instance_commands[0].json_output
        sys_status = command_output["systemStatus"] if "systemStatus" in command_output.keys() else ""
        self.result.is_success()
        if sys_status != "coolingOk":
            self.result.is_failure(f"Device system cooling is not OK: '{sys_status}'")


class VerifyEnvironmentCooling(AntaTest):
    """
    This test verifies the fans status.

    Expected Results:
      * success: The test will pass if the fans status are within the accepted states list.
      * failure: The test will fail if some fans status is not within the accepted states list.
    """

    name = "VerifyEnvironmentCooling"
    description = "Verifies if the fans status are within the accepted states list."
    categories = ["hardware"]
    commands = [AntaCommand(command="show system environment cooling", ofmt="json")]

    class Input(AntaTest.Input):  # pylint: disable=missing-class-docstring
        states: List[str]
        """Accepted states list for fan status"""

    @skip_on_platforms(["cEOSLab", "vEOS-lab"])
    @AntaTest.anta_test
    def test(self) -> None:
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
    """
    This test verifies the power supplies status.

    Expected Results:
      * success: The test will pass if the power supplies status are within the accepted states list.
      * failure: The test will fail if some power supplies status is not within the accepted states list.
    """

    name = "VerifyEnvironmentPower"
    description = "Verifies if the power supplies status are within the accepted states list."
    categories = ["hardware"]
    commands = [AntaCommand(command="show system environment power", ofmt="json")]

    class Input(AntaTest.Input):  # pylint: disable=missing-class-docstring
        states: List[str]
        """Accepted states list for power supplies status"""

    @skip_on_platforms(["cEOSLab", "vEOS-lab"])
    @AntaTest.anta_test
    def test(self) -> None:
        command_output = self.instance_commands[0].json_output
        power_supplies = command_output["powerSupplies"] if "powerSupplies" in command_output.keys() else "{}"
        wrong_power_supplies = {
            powersupply: {"state": value["state"]} for powersupply, value in dict(power_supplies).items() if value["state"] not in self.inputs.states
        }
        if not wrong_power_supplies:
            self.result.is_success()
        else:
            self.result.is_failure(f"The following power supplies status are not in the accepted states list: {wrong_power_supplies}")


class VerifyAdverseDrops(AntaTest):
    """
    This test verifies if there are no adverse drops on DCS7280E and DCS7500E.

    Expected Results:
      * success: The test will pass if there are no adverse drops.
      * failure: The test will fail if there are adverse drops.
    """

    name = "VerifyAdverseDrops"
    description = "Verifies there are no adverse drops on DCS7280E and DCS7500E"
    categories = ["hardware"]
    commands = [AntaCommand(command="show hardware counter drop", ofmt="json")]

    @skip_on_platforms(["cEOSLab", "vEOS-lab"])
    @AntaTest.anta_test
    def test(self) -> None:
        command_output = self.instance_commands[0].json_output
        total_adverse_drop = command_output["totalAdverseDrops"] if "totalAdverseDrops" in command_output.keys() else ""
        if total_adverse_drop == 0:
            self.result.is_success()
        else:
            self.result.is_failure(f"Device totalAdverseDrops counter is: '{total_adverse_drop}'")
