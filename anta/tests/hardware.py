"""
Test functions related to the hardware or environement
"""
from __future__ import annotations

from typing import List, Optional

from anta.decorators import skip_on_platforms
from anta.models import AntaCommand, AntaTest


class VerifyTransceiversManufacturers(AntaTest):
    """
    Verifies Manufacturers of all Transceivers.
    """

    name = "VerifyTransceiversManufacturers"
    description = ""
    categories = ["hardware"]
    commands = [AntaCommand(command="show inventory", ofmt="json")]

    @skip_on_platforms(["cEOSLab", "vEOS-lab"])
    @AntaTest.anta_test
    def test(self, manufacturers: Optional[List[str]] = None) -> None:
        """
        Run VerifyTransceiversManufacturers validation

        Args:
            manufacturers: List of allowed transceivers manufacturers.
        """
        if not manufacturers:
            self.result.is_skipped(f"{self.__class__.name} was not run as no manufacturers were given")
        else:
            command_output = self.instance_commands[0].json_output
            wrong_manufacturers = {interface: value["mfgName"] for interface, value in command_output["xcvrSlots"].items() if value["mfgName"] not in manufacturers}
            if not wrong_manufacturers:
                self.result.is_success()
            else:
                self.result.is_failure("The following interfaces have transceivers from unauthorized manufacturers")
                self.result.messages.append(str(wrong_manufacturers))


class VerifyTemperature(AntaTest):
    """
    Verifies device temparture is currently OK (temperatureOK).
    """

    name = "VerifyTemperature"
    description = "Verifies device temparture is currently OK (temperatureOK)"
    categories = ["hardware"]
    commands = [AntaCommand(command="show system environment temperature", ofmt="json")]

    @skip_on_platforms(["cEOSLab", "vEOS-lab"])
    @AntaTest.anta_test
    def test(self) -> None:
        """Run VerifyTemperature validation"""
        command_output = self.instance_commands[0].json_output
        temperature_status = command_output["systemStatus"] if "systemStatus" in command_output.keys() else ""
        if temperature_status == "temperatureOk":
            self.result.is_success()
        else:
            self.result.is_failure(f"Device temperature is not OK, systemStatus: {temperature_status }")


class VerifyTransceiversTemperature(AntaTest):
    """
    Verifies Transceivers temperature is currently OK.
    """

    name = "VerifyTransceiversTemperature"
    description = "Verifies Transceivers temperature is currently OK"
    categories = ["hardware"]
    commands = [AntaCommand(command="show system environment temperature transceiver", ofmt="json")]

    @skip_on_platforms(["cEOSLab", "vEOS-lab"])
    @AntaTest.anta_test
    def test(self) -> None:
        """Run VerifyTransceiversTemperature validation"""
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
            self.result.is_failure("The following sensors do not have the correct temperature or had alarms in the past:")
            self.result.messages.append(str(wrong_sensors))


class VerifyEnvironmentSystemCooling(AntaTest):
    """
    Verifies the System Cooling is ok.
    """

    name = "VerifyEnvironmentSystemCooling"
    description = "Verifies the fans status is OK for fans"
    categories = ["hardware"]
    commands = [AntaCommand(command="show system environment cooling", ofmt="json")]

    @skip_on_platforms(["cEOSLab", "vEOS-lab"])
    @AntaTest.anta_test
    def test(self) -> None:
        """Run VerifyEnvironmentCooling validation"""

        command_output = self.instance_commands[0].json_output
        sys_status = command_output["systemStatus"] if "systemStatus" in command_output.keys() else ""

        self.result.is_success()
        if sys_status != "coolingOk":
            self.result.is_failure(f"Device System cooling is not OK: {sys_status}")


class VerifyEnvironmentCooling(AntaTest):
    """
    Verifies the fans status is in the accepted states list.

    Default accepted states list is ['ok']
    """

    name = "VerifyEnvironmentCooling"
    description = "Verifies the fans status is OK for fans"
    categories = ["hardware"]
    commands = [AntaCommand(command="show system environment cooling", ofmt="json")]

    @skip_on_platforms(["cEOSLab", "vEOS-lab"])
    @AntaTest.anta_test
    def test(self, accepted_states: Optional[List[str]] = None) -> None:
        """
        Run VerifyEnvironmentCooling validation

        Args:
            accepted_states: Accepted states list for fan status
        """
        if accepted_states is None:
            accepted_states = ["ok"]

        command_output = self.instance_commands[0].json_output
        self.result.is_success()
        # First go through power supplies fans
        for power_supply in command_output.get("powerSupplySlots", []):
            for fan in power_supply.get("fans", []):
                if (state := fan["status"]) not in accepted_states:
                    if self.result.result == "success":
                        self.result.is_failure(f"Some fans state are not in the accepted list: {accepted_states}.")
                    self.result.is_failure(f"Fan {fan['label']} on PowerSupply {power_supply['label']} has state '{state}'.")
        # Then go through Fan Trays
        for fan_tray in command_output.get("fanTraySlots", []):
            for fan in fan_tray.get("fans", []):
                if (state := fan["status"]) not in accepted_states:
                    if self.result.result == "success":
                        self.result.is_failure(f"Some fans state are not in the accepted list: {accepted_states}.")
                    self.result.is_failure(f"Fan {fan['label']} on Fan Tray {fan_tray['label']} has state '{state}'.")


class VerifyEnvironmentPower(AntaTest):
    """
    Verifies the power supplies status is in the accepted states list

    The default accepted states list is ['ok']
    """

    name = "VerifyEnvironmentPower"
    description = "Verifies the power supplies status is OK"
    categories = ["hardware"]
    commands = [AntaCommand(command="show system environment power", ofmt="json")]

    @skip_on_platforms(["cEOSLab", "vEOS-lab"])
    @AntaTest.anta_test
    def test(self, accepted_states: Optional[List[str]] = None) -> None:
        """
        Run VerifyEnvironmentPower validation

        Args:
            accepted_states: Accepted states list for power supplies
        """
        if accepted_states is None:
            accepted_states = ["ok"]
        command_output = self.instance_commands[0].json_output
        power_supplies = command_output["powerSupplies"] if "powerSupplies" in command_output.keys() else "{}"
        wrong_power_supplies = {
            powersupply: {"state": value["state"]} for powersupply, value in dict(power_supplies).items() if value["state"] not in accepted_states
        }
        if not wrong_power_supplies:
            self.result.is_success()
        else:
            self.result.is_failure(f"The following power supplies states are not in the accepted_states list {accepted_states}")
            self.result.messages.append(str(wrong_power_supplies))


class VerifyAdverseDrops(AntaTest):
    """
    Verifies there is no adverse drops on DCS7280E and DCS7500E.
    """

    name = "VerifyAdverseDrops"
    description = "Verifies there is no adverse drops on DCS7280E and DCS7500E"
    categories = ["hardware"]
    commands = [AntaCommand(command="show hardware counter drop", ofmt="json")]

    @skip_on_platforms(["cEOSLab", "vEOS-lab"])
    @AntaTest.anta_test
    def test(self) -> None:
        """Run VerifyAdverseDrops validation"""
        command_output = self.instance_commands[0].json_output
        total_adverse_drop = command_output["totalAdverseDrops"] if "totalAdverseDrops" in command_output.keys() else ""
        if total_adverse_drop == 0:
            self.result.is_success()
        else:
            self.result.is_failure(f"Device TotalAdverseDrops counter is {total_adverse_drop}")
