"""
Test functions related to the hardware or environement
"""
from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional, cast

from anta.decorators import skip_on_platforms
from anta.models import AntaTest, AntaTestCommand

logger = logging.getLogger(__name__)


class VerifyTransceiversManufacturers(AntaTest):
    """
    Verifies Manufacturers of all Transceivers.
    """

    name = "verify_transceivers_manufacturers"
    description = ""
    categories = ["hardware"]
    commands = [AntaTestCommand(command="show inventory", ofmt="json")]

    @skip_on_platforms(["cEOSLab", "vEOS-lab"])
    @AntaTest.anta_test
    def test(self, manufacturers: Optional[List[str]] = None) -> None:
        """Run VerifyTransceiversManufacturers validation"""
        self.logger.setLevel(logging.DEBUG)
        if not manufacturers:
            self.result.is_skipped(f"{self.__class__.name} was not run as no manufacturers were given")
        else:
            command_output = cast(Dict[str, Dict[Any, Any]], self.instance_commands[0].output)
            wrong_manufacturers = {interface: value["mfgName"] for interface, value in command_output["xcvrSlots"].items() if value["mfgName"] not in manufacturers}
            if not wrong_manufacturers:
                self.result.is_success()
            else:
                self.result.is_failure("The following interfaces have transceivers from unauthorized manufacturers")
                self.result.messages.append(str(wrong_manufacturers))


class VerifyTemperature(AntaTest):
    """
    Verifies device temparture is currently OK.
    """

    name = "VerifyTemperature"
    description = "Verifies device temparture is currently OK"
    categories = ["hardware"]
    commands = [AntaTestCommand(command="show system environment temperature", ofmt="json")]

    @skip_on_platforms(["cEOSLab", "vEOS-lab"])
    @AntaTest.anta_test
    def test(self) -> None:
        """Run VerifyTemperature validation"""
        command_output = cast(Dict[str, Dict[Any, Any]], self.instance_commands[0].output)
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
    commands = [AntaTestCommand(command="show system environment temperature transceiver", ofmt="json")]

    @skip_on_platforms(["cEOSLab", "vEOS-lab"])
    @AntaTest.anta_test
    def test(self) -> None:  # type: ignore[override]
        """Run VerifyTransceiversTemperature validation"""
        command_output = cast(Dict[str, Dict[Any, Any]], self.instance_commands[0].output)
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


class VerifyEnvironmentCooling(AntaTest):
    """
    Verifies the fans status is OK.
    """

    name = "VerifyEnvironmentCooling"
    description = "Verifies the fans status is OK"
    categories = ["hardware"]
    commands = [AntaTestCommand(command="show system environment cooling", ofmt="json")]

    @skip_on_platforms(["cEOSLab", "vEOS-lab"])
    @AntaTest.anta_test
    def test(self) -> None:  # type: ignore[override]
        """Run VerifyEnvironmentCooling validation"""

        command_output = cast(Dict[str, Dict[Any, Any]], self.instance_commands[0].output)
        sys_status = command_output["systemStatus"] if "systemStatus" in command_output.keys() else ""
        if sys_status == "coolingOk":
            self.result.is_success()
        else:
            self.result.is_failure("Device cooling is not OK")


class VerifyEnvironmentPower(AntaTest):
    """
    Verifies the power supplied status is OK.
    """

    name = "VerifyEnvironmentPower"
    description = "Verifies the power supplied status is OK"
    categories = ["hardware"]
    commands = [AntaTestCommand(command="show system environment power", ofmt="json")]

    @skip_on_platforms(["cEOSLab", "vEOS-lab"])
    @AntaTest.anta_test
    def test(self) -> None:  # type: ignore[override]
        """Run VerifyEnvironmentPower validation"""
        command_output = cast(Dict[str, Dict[Any, Any]], self.instance_commands[0].output)
        power_supplies = command_output["powerSupplies"] if "powerSupplies" in command_output.keys() else "{}"
        wrong_power_supplies = {powersupply: {"state": value["state"]} for powersupply, value in dict(power_supplies).items() if value["state"] != "ok"}
        if not wrong_power_supplies:
            self.result.is_success()
        else:
            self.result.is_failure("The following power supplies are not OK")
            self.result.messages.append(str(wrong_power_supplies))


class VerifyAdverseDrops(AntaTest):
    """
    Verifies there is no adverse drops on DCS7280E and DCS7500E.
    """

    name = "VerifyAdverseDrops"
    description = "Verifies there is no adverse drops on DCS7280E and DCS7500E"
    categories = ["hardware"]
    commands = [AntaTestCommand(command="show hardware counter drop", ofmt="json")]

    @AntaTest.anta_test
    def test(self) -> None:  # type: ignore[override]
        """Run VerifyAdverseDrops validation"""
        command_output = cast(Dict[str, Dict[Any, Any]], self.instance_commands[0].output)
        total_adverse_drop = command_output["totalAdverseDrops"] if "totalAdverseDrops" in command_output.keys() else ""
        if total_adverse_drop == 0:
            self.result.is_success()
        else:
            self.result.is_failure(f"Device TotalAdverseDrops counter is {total_adverse_drop}")
