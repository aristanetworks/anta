"""
Test functions related to the hardware or environement
"""

# pylint: disable = too-few-public-methods

from __future__ import annotations

import logging
from typing import List, Optional

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
            command_output = self.instance_commands[0].output
            wrong_manufacturers = {interface: value["mfgName"] for interface, value in command_output["xcvrSlots"].items() if value["mfgName"] not in manufacturers}
            if not wrong_manufacturers:
                self.result.is_success()
            else:
                self.result.is_failure("The following interfaces have transceivers from unauthorized manufacturers")
                self.result.messages.append(str(wrong_manufacturers))


# @skip_on_platforms(["cEOSLab", "vEOS-lab"])
# @anta_test
# async def verify_system_temperature(device: InventoryDevice, result: TestResult) -> TestResult:
#     """
#     Verifies the device temperature is currently OK
#     and the device did not report any temperature alarm in the past.

#     Args:
#         device (InventoryDevice): InventoryDevice instance containing all devices information.

#     Returns:
#         TestResult instance with
#         * result = "unset" if the test has not been executed
#         * result = "success" if the device temperature is OK.
#         * result = "failure" otherwise.
#         * result = "error" if any exception is caught

#     """
#     response = await device.session.cli(command="show system environment temperature", ofmt="json")
#     logger.debug(f"query result is: {response}")

#     if response["systemStatus"] == "temperatureOk":
#         result.is_success()
#     else:
#         result.is_failure(f"Device temperature is not OK, systemStatus: {response['systemStatus'] }")

#     return result


# @skip_on_platforms(["cEOSLab", "vEOS-lab"])
# @anta_test
# async def verify_transceiver_temperature(device: InventoryDevice, result: TestResult) -> TestResult:
#     """
#     Verifies the transceivers temperature is currently OK
#     and the device did not report any alarm in the past for its transceivers temperature.

#     Args:
#         device (InventoryDevice): InventoryDevice instance containing all devices information.

#     Returns:
#         TestResult instance with
#         * result = "unset" if the test has not been executed
#         * result = "success" if the device transceivers temperature of the device is currently OK
#                              AND the device did not report any alarm in the past for its transceivers temperature.
#         * result = "failure" otherwise,
#         * result = "error" if any exception is caught

#     """
#     response = await device.session.cli(command="show system environment temperature transceiver", ofmt="json")
#     logger.debug(f"query result is: {response}")

#     # Get the list of sensors
#     sensors = response["tempSensors"]

#     wrong_sensors = {
#         sensor["name"]: {
#             "hwStatus": sensor["hwStatus"],
#             "alertCount": sensor["alertCount"],
#         }
#         for sensor in sensors
#         if sensor["hwStatus"] != "ok" or sensor["alertCount"] != 0
#     }
#     if not wrong_sensors:
#         result.is_success()
#     else:
#         result.is_failure("The following sensors do not have the correct temperature or had alarms in the past:")
#         result.messages.append(str(wrong_sensors))

#     return result


# @skip_on_platforms(["cEOSLab", "vEOS-lab"])
# @anta_test
# async def verify_environment_cooling(device: InventoryDevice, result: TestResult) -> TestResult:
#     """
#     Verifies the fans status is OK.

#     Args:
#         device (InventoryDevice): InventoryDevice instance containing all devices information.

#     Returns:
#         TestResult instance with
#         * result = "unset" if the test has not been executed
#         * result = "success" if the fans status is OK.
#         * result = "failure" otherwise.
#         * result = "error" if any exception is caught

#     """
#     response = await device.session.cli(command="show system environment cooling", ofmt="json")
#     logger.debug(f"query result is: {response}")

#     if response["systemStatus"] == "coolingOk":
#         result.is_success()
#     else:
#         result.is_failure(f"Device cooling is not OK, systemStatus: {response['systemStatus'] }")

#     return result


# @skip_on_platforms(["cEOSLab", "vEOS-lab"])
# @anta_test
# async def verify_environment_power(device: InventoryDevice, result: TestResult) -> TestResult:
#     """
#     Verifies the power supplies status is OK.

#     Args:
#         device (InventoryDevice): InventoryDevice instance containing all devices information.

#     Returns:
#         TestResult instance with
#         * result = "unset" if the test has not been executed
#         * result = "success" if the power supplies status is OK.
#         * result = "failure" otherwise.
#         * result = "error" if any exception is caught

#     """
#     response = await device.session.cli(command="show system environment power", ofmt="json")
#     logger.debug(f"query result is: {response}")

#     wrong_power_supplies = {powersupply: {"state": value["state"]} for powersupply, value in response["powerSupplies"].items() if value["state"] != "ok"}
#     if not wrong_power_supplies:
#         result.is_success()
#     else:
#         result.is_failure("The following power suppliers are not ok:")
#         result.messages.append(str(wrong_power_supplies))

#     return result


# @skip_on_platforms(["cEOSLab", "vEOS-lab"])
# @anta_test
# async def verify_adverse_drops(device: InventoryDevice, result: TestResult) -> TestResult:
#     """
#     Verifies there is no adverse drops on DCS-7280E and DCS-7500E switches.

#     Args:
#         device (InventoryDevice): InventoryDevice instance containing all devices information.

#     Returns:
#         TestResult instance with
#         * result = "unset" if the test has not been executed
#         * result = "success" if the device (DCS-7280E and DCS-7500E) doesnt reports adverse drops.
#         * result = "failure" if the device (DCS-7280E and DCS-7500E) report adverse drops.
#         * result = "error" if any exception is caught

#     """
#     response = await device.session.cli(command="show hardware counter drop", ofmt="json")
#     logger.debug(f"query result is: {response}")

#     if response["totalAdverseDrops"] == 0:
#         result.is_success()
#     else:
#         result.is_failure(f"Device TotalAdverseDrops counter is {response['totalAdverseDrops']}.")

#     return result
