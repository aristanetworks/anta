# Copyright (c) 2023-2025 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Test inputs for anta.tests.hardware."""

from __future__ import annotations

import sys
from typing import TYPE_CHECKING, Any

from anta.models import AntaTest
from anta.result_manager.models import AntaTestStatus
from anta.tests.hardware import (
    VerifyAdverseDrops,
    VerifyEnvironmentCooling,
    VerifyEnvironmentPower,
    VerifyEnvironmentSystemCooling,
    VerifySupervisorRedundancy,
    VerifyTemperature,
    VerifyTransceiversManufacturers,
    VerifyTransceiversTemperature,
)
from tests.units.anta_tests import test

if TYPE_CHECKING:
    from tests.units.anta_tests import AntaUnitTestDataDict

DATA: AntaUnitTestDataDict = {
    (VerifyTransceiversManufacturers, "success"): {
        "eos_data": [
            {
                "xcvrSlots": {
                    "1": {"mfgName": "Arista Networks", "modelName": "QSFP-100G-DR", "serialNum": "XKT203501340", "hardwareRev": "21"},
                    "2": {"mfgName": "Arista Networks", "modelName": "QSFP-100G-DR", "serialNum": "XKT203501337", "hardwareRev": "21"},
                }
            }
        ],
        "inputs": {"manufacturers": ["Arista Networks"]},
        "expected": {"result": AntaTestStatus.SUCCESS},
    },
    (VerifyTransceiversManufacturers, "failure"): {
        "eos_data": [
            {
                "xcvrSlots": {
                    "1": {"mfgName": "Arista Networks", "modelName": "QSFP-100G-DR", "serialNum": "XKT203501340", "hardwareRev": "21"},
                    "2": {"mfgName": "Arista Networks", "modelName": "QSFP-100G-DR", "serialNum": "XKT203501337", "hardwareRev": "21"},
                }
            }
        ],
        "inputs": {"manufacturers": ["Arista"]},
        "expected": {
            "result": AntaTestStatus.FAILURE,
            "messages": [
                "Interface: 1 - Transceiver is from unapproved manufacturers - Expected: Arista Actual: Arista Networks",
                "Interface: 2 - Transceiver is from unapproved manufacturers - Expected: Arista Actual: Arista Networks",
            ],
        },
    },
    (VerifyTemperature, "success"): {
        "eos_data": [
            {
                "powercycleOnOverheat": "False",
                "ambientThreshold": 45,
                "cardSlots": [],
                "shutdownOnOverheat": "True",
                "systemStatus": "temperatureOk",
                "recoveryModeOnOverheat": "recoveryModeNA",
            }
        ],
        "expected": {"result": AntaTestStatus.SUCCESS},
    },
    (VerifyTemperature, "failure"): {
        "eos_data": [
            {
                "powercycleOnOverheat": "False",
                "ambientThreshold": 45,
                "cardSlots": [],
                "shutdownOnOverheat": "True",
                "systemStatus": "temperatureCritical",
                "recoveryModeOnOverheat": "recoveryModeNA",
            }
        ],
        "expected": {
            "result": AntaTestStatus.FAILURE,
            "messages": ["Device temperature exceeds acceptable limits - Expected: temperatureOk Actual: temperatureCritical"],
        },
    },
    (VerifyTransceiversTemperature, "success"): {
        "eos_data": [
            {
                "tempSensors": [
                    {
                        "maxTemperature": 25.03125,
                        "maxTemperatureLastChange": 1682509618.2227979,
                        "hwStatus": "ok",
                        "alertCount": 0,
                        "description": "Xcvr54 temp sensor",
                        "overheatThreshold": 70.0,
                        "criticalThreshold": 70.0,
                        "inAlertState": False,
                        "targetTemperature": 62.0,
                        "relPos": "54",
                        "currentTemperature": 24.171875,
                        "setPointTemperature": 61.8,
                        "pidDriverCount": 0,
                        "isPidDriver": False,
                        "name": "DomTemperatureSensor54",
                    }
                ],
                "cardSlots": [],
            }
        ],
        "expected": {"result": AntaTestStatus.SUCCESS},
    },
    (VerifyTransceiversTemperature, "failure-hwStatus"): {
        "eos_data": [
            {
                "tempSensors": [
                    {
                        "maxTemperature": 25.03125,
                        "maxTemperatureLastChange": 1682509618.2227979,
                        "hwStatus": "ko",
                        "alertCount": 0,
                        "description": "Xcvr54 temp sensor",
                        "overheatThreshold": 70.0,
                        "criticalThreshold": 70.0,
                        "inAlertState": False,
                        "targetTemperature": 62.0,
                        "relPos": "54",
                        "currentTemperature": 24.171875,
                        "setPointTemperature": 61.8,
                        "pidDriverCount": 0,
                        "isPidDriver": False,
                        "name": "DomTemperatureSensor54",
                    }
                ],
                "cardSlots": [],
            }
        ],
        "expected": {"result": AntaTestStatus.FAILURE, "messages": ["Sensor: DomTemperatureSensor54 - Invalid hardware state - Expected: ok Actual: ko"]},
    },
    (VerifyTransceiversTemperature, "failure-alertCount"): {
        "eos_data": [
            {
                "tempSensors": [
                    {
                        "maxTemperature": 25.03125,
                        "maxTemperatureLastChange": 1682509618.2227979,
                        "hwStatus": "ok",
                        "alertCount": 1,
                        "description": "Xcvr54 temp sensor",
                        "overheatThreshold": 70.0,
                        "criticalThreshold": 70.0,
                        "inAlertState": False,
                        "targetTemperature": 62.0,
                        "relPos": "54",
                        "currentTemperature": 24.171875,
                        "setPointTemperature": 61.8,
                        "pidDriverCount": 0,
                        "isPidDriver": False,
                        "name": "DomTemperatureSensor54",
                    }
                ],
                "cardSlots": [],
            }
        ],
        "expected": {"result": AntaTestStatus.FAILURE, "messages": ["Sensor: DomTemperatureSensor54 - Incorrect alert counter - Expected: 0 Actual: 1"]},
    },
    (VerifyEnvironmentSystemCooling, "success"): {
        "eos_data": [
            {
                "defaultZones": False,
                "numCoolingZones": [],
                "coolingMode": "automatic",
                "ambientTemperature": 24.5,
                "shutdownOnInsufficientFans": True,
                "airflowDirection": "frontToBackAirflow",
                "overrideFanSpeed": 0,
                "powerSupplySlots": [],
                "fanTraySlots": [],
                "minFanSpeed": 0,
                "currentZones": 1,
                "configuredZones": 0,
                "systemStatus": "coolingOk",
            }
        ],
        "expected": {"result": AntaTestStatus.SUCCESS},
    },
    (VerifyEnvironmentSystemCooling, "failure"): {
        "eos_data": [
            {
                "defaultZones": False,
                "numCoolingZones": [],
                "coolingMode": "automatic",
                "ambientTemperature": 24.5,
                "shutdownOnInsufficientFans": True,
                "airflowDirection": "frontToBackAirflow",
                "overrideFanSpeed": 0,
                "powerSupplySlots": [],
                "fanTraySlots": [],
                "minFanSpeed": 0,
                "currentZones": 1,
                "configuredZones": 0,
                "systemStatus": "coolingKo",
            }
        ],
        "expected": {"result": AntaTestStatus.FAILURE, "messages": ["Device system cooling status invalid - Expected: coolingOk Actual: coolingKo"]},
    },
    (VerifyEnvironmentCooling, "success"): {
        "eos_data": [
            {
                "defaultZones": False,
                "numCoolingZones": [],
                "coolingMode": "automatic",
                "ambientTemperature": 24.5,
                "shutdownOnInsufficientFans": True,
                "airflowDirection": "frontToBackAirflow",
                "overrideFanSpeed": 0,
                "powerSupplySlots": [
                    {
                        "status": "ok",
                        "fans": [
                            {
                                "status": "ok",
                                "uptime": 1682498937.0240965,
                                "maxSpeed": 23000,
                                "lastSpeedStableChangeTime": 1682499033.0403435,
                                "configuredSpeed": 30,
                                "actualSpeed": 33,
                                "speedHwOverride": True,
                                "speedStable": True,
                                "label": "PowerSupply1/1",
                            }
                        ],
                        "speed": 30,
                        "label": "PowerSupply1",
                    },
                    {
                        "status": "ok",
                        "fans": [
                            {
                                "status": "ok",
                                "uptime": 1682498935.9121106,
                                "maxSpeed": 23000,
                                "lastSpeedStableChangeTime": 1682499092.4665174,
                                "configuredSpeed": 30,
                                "actualSpeed": 33,
                                "speedHwOverride": True,
                                "speedStable": True,
                                "label": "PowerSupply2/1",
                            }
                        ],
                        "speed": 30,
                        "label": "PowerSupply2",
                    },
                ],
                "fanTraySlots": [
                    {
                        "status": "ok",
                        "fans": [
                            {
                                "status": "ok",
                                "uptime": 1682498923.9303148,
                                "maxSpeed": 17500,
                                "lastSpeedStableChangeTime": 1682498975.0139885,
                                "configuredSpeed": 30,
                                "actualSpeed": 29,
                                "speedHwOverride": False,
                                "speedStable": True,
                                "label": "1/1",
                            }
                        ],
                        "speed": 30,
                        "label": "1",
                    },
                    {
                        "status": "ok",
                        "fans": [
                            {
                                "status": "ok",
                                "uptime": 1682498923.9304729,
                                "maxSpeed": 17500,
                                "lastSpeedStableChangeTime": 1682498939.9329433,
                                "configuredSpeed": 30,
                                "actualSpeed": 30,
                                "speedHwOverride": False,
                                "speedStable": True,
                                "label": "2/1",
                            }
                        ],
                        "speed": 30,
                        "label": "2",
                    },
                    {
                        "status": "ok",
                        "fans": [
                            {
                                "status": "ok",
                                "uptime": 1682498923.9383528,
                                "maxSpeed": 17500,
                                "lastSpeedStableChangeTime": 1682498975.0140095,
                                "configuredSpeed": 30,
                                "actualSpeed": 30,
                                "speedHwOverride": False,
                                "speedStable": True,
                                "label": "3/1",
                            }
                        ],
                        "speed": 30,
                        "label": "3",
                    },
                    {
                        "status": "ok",
                        "fans": [
                            {
                                "status": "ok",
                                "uptime": 1682498923.9303904,
                                "maxSpeed": 17500,
                                "lastSpeedStableChangeTime": 1682498975.0140295,
                                "configuredSpeed": 30,
                                "actualSpeed": 30,
                                "speedHwOverride": False,
                                "speedStable": True,
                                "label": "4/1",
                            }
                        ],
                        "speed": 30,
                        "label": "4",
                    },
                ],
                "minFanSpeed": 0,
                "currentZones": 1,
                "configuredZones": 0,
                "systemStatus": "coolingOk",
            }
        ],
        "inputs": {"states": ["ok"]},
        "expected": {"result": AntaTestStatus.SUCCESS},
    },
    (VerifyEnvironmentCooling, "success-additional-states"): {
        "eos_data": [
            {
                "defaultZones": False,
                "numCoolingZones": [],
                "coolingMode": "automatic",
                "ambientTemperature": 24.5,
                "shutdownOnInsufficientFans": True,
                "airflowDirection": "frontToBackAirflow",
                "overrideFanSpeed": 0,
                "powerSupplySlots": [
                    {
                        "status": "ok",
                        "fans": [
                            {
                                "status": "ok",
                                "uptime": 1682498937.0240965,
                                "maxSpeed": 23000,
                                "lastSpeedStableChangeTime": 1682499033.0403435,
                                "configuredSpeed": 30,
                                "actualSpeed": 33,
                                "speedHwOverride": True,
                                "speedStable": True,
                                "label": "PowerSupply1/1",
                            }
                        ],
                        "speed": 30,
                        "label": "PowerSupply1",
                    },
                    {
                        "status": "ok",
                        "fans": [
                            {
                                "status": "powerLoss",
                                "uptime": 1682498935.9121106,
                                "maxSpeed": 23000,
                                "lastSpeedStableChangeTime": 1682499092.4665174,
                                "configuredSpeed": 30,
                                "actualSpeed": 33,
                                "speedHwOverride": True,
                                "speedStable": True,
                                "label": "PowerSupply2/1",
                            }
                        ],
                        "speed": 30,
                        "label": "PowerSupply2",
                    },
                ],
                "fanTraySlots": [
                    {
                        "status": "ok",
                        "fans": [
                            {
                                "status": "ok",
                                "uptime": 1682498923.9303148,
                                "maxSpeed": 17500,
                                "lastSpeedStableChangeTime": 1682498975.0139885,
                                "configuredSpeed": 30,
                                "actualSpeed": 29,
                                "speedHwOverride": False,
                                "speedStable": True,
                                "label": "1/1",
                            }
                        ],
                        "speed": 30,
                        "label": "1",
                    },
                    {
                        "status": "ok",
                        "fans": [
                            {
                                "status": "ok",
                                "uptime": 1682498923.9304729,
                                "maxSpeed": 17500,
                                "lastSpeedStableChangeTime": 1682498939.9329433,
                                "configuredSpeed": 30,
                                "actualSpeed": 30,
                                "speedHwOverride": False,
                                "speedStable": True,
                                "label": "2/1",
                            }
                        ],
                        "speed": 30,
                        "label": "2",
                    },
                    {
                        "status": "ok",
                        "fans": [
                            {
                                "status": "ok",
                                "uptime": 1682498923.9383528,
                                "maxSpeed": 17500,
                                "lastSpeedStableChangeTime": 1682498975.0140095,
                                "configuredSpeed": 30,
                                "actualSpeed": 30,
                                "speedHwOverride": False,
                                "speedStable": True,
                                "label": "3/1",
                            }
                        ],
                        "speed": 30,
                        "label": "3",
                    },
                    {
                        "status": "ok",
                        "fans": [
                            {
                                "status": "ok",
                                "uptime": 1682498923.9303904,
                                "maxSpeed": 17500,
                                "lastSpeedStableChangeTime": 1682498975.0140295,
                                "configuredSpeed": 30,
                                "actualSpeed": 30,
                                "speedHwOverride": False,
                                "speedStable": True,
                                "label": "4/1",
                            }
                        ],
                        "speed": 30,
                        "label": "4",
                    },
                ],
                "minFanSpeed": 0,
                "currentZones": 1,
                "configuredZones": 0,
                "systemStatus": "coolingOk",
            }
        ],
        "inputs": {"states": ["ok", "powerLoss"]},
        "expected": {"result": AntaTestStatus.SUCCESS},
    },
    (VerifyEnvironmentCooling, "failure-fan-tray"): {
        "eos_data": [
            {
                "defaultZones": False,
                "numCoolingZones": [],
                "coolingMode": "automatic",
                "ambientTemperature": 24.5,
                "shutdownOnInsufficientFans": True,
                "airflowDirection": "frontToBackAirflow",
                "overrideFanSpeed": 0,
                "powerSupplySlots": [
                    {
                        "status": "ok",
                        "fans": [
                            {
                                "status": "ok",
                                "uptime": 1682498937.0240965,
                                "maxSpeed": 23000,
                                "lastSpeedStableChangeTime": 1682499033.0403435,
                                "configuredSpeed": 30,
                                "actualSpeed": 33,
                                "speedHwOverride": True,
                                "speedStable": True,
                                "label": "PowerSupply1/1",
                            }
                        ],
                        "speed": 30,
                        "label": "PowerSupply1",
                    },
                    {
                        "status": "ok",
                        "fans": [
                            {
                                "status": "ok",
                                "uptime": 1682498935.9121106,
                                "maxSpeed": 23000,
                                "lastSpeedStableChangeTime": 1682499092.4665174,
                                "configuredSpeed": 30,
                                "actualSpeed": 33,
                                "speedHwOverride": True,
                                "speedStable": True,
                                "label": "PowerSupply2/1",
                            }
                        ],
                        "speed": 30,
                        "label": "PowerSupply2",
                    },
                ],
                "fanTraySlots": [
                    {
                        "status": "ok",
                        "fans": [
                            {
                                "status": "unknownHwStatus",
                                "uptime": 1682498923.9303148,
                                "maxSpeed": 17500,
                                "lastSpeedStableChangeTime": 1682498975.0139885,
                                "configuredSpeed": 30,
                                "actualSpeed": 29,
                                "speedHwOverride": False,
                                "speedStable": True,
                                "label": "1/1",
                            }
                        ],
                        "speed": 30,
                        "label": "1",
                    },
                    {
                        "status": "ok",
                        "fans": [
                            {
                                "status": "ok",
                                "uptime": 1682498923.9304729,
                                "maxSpeed": 17500,
                                "lastSpeedStableChangeTime": 1682498939.9329433,
                                "configuredSpeed": 30,
                                "actualSpeed": 30,
                                "speedHwOverride": False,
                                "speedStable": True,
                                "label": "2/1",
                            }
                        ],
                        "speed": 30,
                        "label": "2",
                    },
                    {
                        "status": "ok",
                        "fans": [
                            {
                                "status": "powerLoss",
                                "uptime": 1682498923.9383528,
                                "maxSpeed": 17500,
                                "lastSpeedStableChangeTime": 1682498975.0140095,
                                "configuredSpeed": 30,
                                "actualSpeed": 30,
                                "speedHwOverride": False,
                                "speedStable": True,
                                "label": "3/1",
                            }
                        ],
                        "speed": 30,
                        "label": "3",
                    },
                    {
                        "status": "ok",
                        "fans": [
                            {
                                "status": "ok",
                                "uptime": 1682498923.9303904,
                                "maxSpeed": 17500,
                                "lastSpeedStableChangeTime": 1682498975.0140295,
                                "configuredSpeed": 30,
                                "actualSpeed": 30,
                                "speedHwOverride": False,
                                "speedStable": True,
                                "label": "4/1",
                            }
                        ],
                        "speed": 30,
                        "label": "4",
                    },
                ],
                "minFanSpeed": 0,
                "currentZones": 1,
                "configuredZones": 0,
                "systemStatus": "CoolingKo",
            }
        ],
        "inputs": {"states": ["ok", "powerLoss"]},
        "expected": {"result": AntaTestStatus.FAILURE, "messages": ["Fan Tray: 1 Fan: 1/1 - Invalid state - Expected: ok, powerLoss Actual: unknownHwStatus"]},
    },
    (VerifyEnvironmentCooling, "failure-power-supply"): {
        "eos_data": [
            {
                "defaultZones": False,
                "numCoolingZones": [],
                "coolingMode": "automatic",
                "ambientTemperature": 24.5,
                "shutdownOnInsufficientFans": True,
                "airflowDirection": "frontToBackAirflow",
                "overrideFanSpeed": 0,
                "powerSupplySlots": [
                    {
                        "status": "ok",
                        "fans": [
                            {
                                "status": "unknownHwStatus",
                                "uptime": 1682498937.0240965,
                                "maxSpeed": 23000,
                                "lastSpeedStableChangeTime": 1682499033.0403435,
                                "configuredSpeed": 30,
                                "actualSpeed": 33,
                                "speedHwOverride": True,
                                "speedStable": True,
                                "label": "PowerSupply1/1",
                            }
                        ],
                        "speed": 30,
                        "label": "PowerSupply1",
                    },
                    {
                        "status": "ok",
                        "fans": [
                            {
                                "status": "ok",
                                "uptime": 1682498935.9121106,
                                "maxSpeed": 23000,
                                "lastSpeedStableChangeTime": 1682499092.4665174,
                                "configuredSpeed": 30,
                                "actualSpeed": 33,
                                "speedHwOverride": True,
                                "speedStable": True,
                                "label": "PowerSupply2/1",
                            }
                        ],
                        "speed": 30,
                        "label": "PowerSupply2",
                    },
                ],
                "fanTraySlots": [
                    {
                        "status": "ok",
                        "fans": [
                            {
                                "status": "ok",
                                "uptime": 1682498923.9303148,
                                "maxSpeed": 17500,
                                "lastSpeedStableChangeTime": 1682498975.0139885,
                                "configuredSpeed": 30,
                                "actualSpeed": 29,
                                "speedHwOverride": False,
                                "speedStable": True,
                                "label": "1/1",
                            }
                        ],
                        "speed": 30,
                        "label": "1",
                    },
                    {
                        "status": "ok",
                        "fans": [
                            {
                                "status": "ok",
                                "uptime": 1682498923.9304729,
                                "maxSpeed": 17500,
                                "lastSpeedStableChangeTime": 1682498939.9329433,
                                "configuredSpeed": 30,
                                "actualSpeed": 30,
                                "speedHwOverride": False,
                                "speedStable": True,
                                "label": "2/1",
                            }
                        ],
                        "speed": 30,
                        "label": "2",
                    },
                    {
                        "status": "ok",
                        "fans": [
                            {
                                "status": "powerLoss",
                                "uptime": 1682498923.9383528,
                                "maxSpeed": 17500,
                                "lastSpeedStableChangeTime": 1682498975.0140095,
                                "configuredSpeed": 30,
                                "actualSpeed": 30,
                                "speedHwOverride": False,
                                "speedStable": True,
                                "label": "3/1",
                            }
                        ],
                        "speed": 30,
                        "label": "3",
                    },
                    {
                        "status": "ok",
                        "fans": [
                            {
                                "status": "ok",
                                "uptime": 1682498923.9303904,
                                "maxSpeed": 17500,
                                "lastSpeedStableChangeTime": 1682498975.0140295,
                                "configuredSpeed": 30,
                                "actualSpeed": 30,
                                "speedHwOverride": False,
                                "speedStable": True,
                                "label": "4/1",
                            }
                        ],
                        "speed": 30,
                        "label": "4",
                    },
                ],
                "minFanSpeed": 0,
                "currentZones": 1,
                "configuredZones": 0,
                "systemStatus": "CoolingKo",
            }
        ],
        "inputs": {"states": ["ok", "powerLoss"]},
        "expected": {
            "result": AntaTestStatus.FAILURE,
            "messages": ["Power Slot: PowerSupply1 Fan: PowerSupply1/1 - Invalid state - Expected: ok, powerLoss Actual: unknownHwStatus"],
        },
    },
    (VerifyEnvironmentPower, "success"): {
        "eos_data": [
            {
                "powerSupplies": {
                    "1": {
                        "outputPower": 0.0,
                        "modelName": "PWR-500AC-F",
                        "capacity": 500.0,
                        "tempSensors": {
                            "TempSensorP1/2": {"status": "ok", "temperature": 0.0},
                            "TempSensorP1/3": {"status": "ok", "temperature": 0.0},
                            "TempSensorP1/1": {"status": "ok", "temperature": 0.0},
                        },
                        "fans": {"FanP1/1": {"status": "ok", "speed": 33}},
                        "state": "ok",
                        "inputCurrent": 0.0,
                        "dominant": False,
                        "inputVoltage": 0.0,
                        "outputCurrent": 0.0,
                        "managed": True,
                    },
                    "2": {
                        "outputPower": 117.375,
                        "uptime": 1682498935.9121966,
                        "modelName": "PWR-500AC-F",
                        "capacity": 500.0,
                        "tempSensors": {
                            "TempSensorP2/1": {"status": "ok", "temperature": 39.0},
                            "TempSensorP2/3": {"status": "ok", "temperature": 43.0},
                            "TempSensorP2/2": {"status": "ok", "temperature": 31.0},
                        },
                        "fans": {"FanP2/1": {"status": "ok", "speed": 33}},
                        "state": "ok",
                        "inputCurrent": 0.572265625,
                        "dominant": False,
                        "inputVoltage": 232.5,
                        "outputCurrent": 9.828125,
                        "managed": True,
                    },
                }
            }
        ],
        "inputs": {"states": ["ok"]},
        "expected": {"result": AntaTestStatus.SUCCESS},
    },
    (VerifyEnvironmentPower, "success-min_power-voltage"): {
        "eos_data": [
            {
                "powerSupplies": {
                    "1": {
                        "modelName": "PWR-747AC-RED",
                        "capacity": 750.0,
                        "dominant": False,
                        "inputCurrent": 0.705078125,
                        "outputCurrent": 9.921875,
                        "inputVoltage": 206.25,
                        "outputVoltage": 12.025390625,
                        "outputPower": 119.375,
                        "state": "ok",
                        "uptime": 1730845612.5112484,
                        "fans": {"FanP1/1": {"status": "ok", "speed": 33}},
                        "tempSensors": {"TempSensorP1/2": {"status": "ok", "temperature": 50.0}, "TempSensorP1/1": {"status": "ok", "temperature": 61.0}},
                        "managed": True,
                    },
                    "2": {
                        "modelName": "PWR-747AC-RED",
                        "capacity": 750.0,
                        "dominant": False,
                        "inputCurrent": 0.724609375,
                        "outputCurrent": 10.765625,
                        "inputVoltage": 204.75,
                        "outputVoltage": 12.009765625,
                        "outputPower": 128.0,
                        "state": "ok",
                        "uptime": 1730142355.4805274,
                        "fans": {"FanP2/1": {"status": "ok", "speed": 33}},
                        "tempSensors": {"TempSensorP2/2": {"status": "ok", "temperature": 53.0}, "TempSensorP2/1": {"status": "ok", "temperature": 63.0}},
                        "managed": True,
                    },
                }
            }
        ],
        "inputs": {"states": ["ok"], "min_input_voltage": 1},
        "expected": {"result": AntaTestStatus.SUCCESS},
    },
    (VerifyEnvironmentPower, "failure-min_power-voltage"): {
        "eos_data": [
            {
                "powerSupplies": {
                    "1": {
                        "modelName": "PWR-747AC-RED",
                        "capacity": 750.0,
                        "dominant": False,
                        "inputCurrent": 0.705078125,
                        "outputCurrent": 9.921875,
                        "inputVoltage": 0.25,
                        "outputVoltage": 12.025390625,
                        "outputPower": 119.375,
                        "state": "ok",
                        "uptime": 1730845612.5112484,
                        "fans": {"FanP1/1": {"status": "ok", "speed": 33}},
                        "tempSensors": {"TempSensorP1/2": {"status": "ok", "temperature": 50.0}, "TempSensorP1/1": {"status": "ok", "temperature": 61.0}},
                        "managed": True,
                    },
                    "2": {
                        "modelName": "PWR-747AC-RED",
                        "capacity": 750.0,
                        "dominant": False,
                        "inputCurrent": 0.724609375,
                        "outputCurrent": 10.765625,
                        "inputVoltage": 0.75,
                        "outputVoltage": 12.009765625,
                        "outputPower": 128.0,
                        "state": "ok",
                        "uptime": 1730142355.4805274,
                        "fans": {"FanP2/1": {"status": "ok", "speed": 33}},
                        "tempSensors": {"TempSensorP2/2": {"status": "ok", "temperature": 53.0}, "TempSensorP2/1": {"status": "ok", "temperature": 63.0}},
                        "managed": True,
                    },
                }
            }
        ],
        "inputs": {"states": ["ok"], "min_input_voltage": 1},
        "expected": {
            "result": AntaTestStatus.FAILURE,
            "messages": [
                "Power Supply: 1 - Input voltage mismatch - Expected: > 1 Actual: 0.25",
                "Power Supply: 2 - Input voltage mismatch - Expected: > 1 Actual: 0.75",
            ],
        },
    },
    (VerifyEnvironmentPower, "success-additional-states"): {
        "eos_data": [
            {
                "powerSupplies": {
                    "1": {
                        "outputPower": 0.0,
                        "modelName": "PWR-500AC-F",
                        "capacity": 500.0,
                        "tempSensors": {
                            "TempSensorP1/2": {"status": "ok", "temperature": 0.0},
                            "TempSensorP1/3": {"status": "ok", "temperature": 0.0},
                            "TempSensorP1/1": {"status": "ok", "temperature": 0.0},
                        },
                        "fans": {"FanP1/1": {"status": "ok", "speed": 33}},
                        "state": "powerLoss",
                        "inputCurrent": 0.0,
                        "dominant": False,
                        "inputVoltage": 0.0,
                        "outputCurrent": 0.0,
                        "managed": True,
                    },
                    "2": {
                        "outputPower": 117.375,
                        "uptime": 1682498935.9121966,
                        "modelName": "PWR-500AC-F",
                        "capacity": 500.0,
                        "tempSensors": {
                            "TempSensorP2/1": {"status": "ok", "temperature": 39.0},
                            "TempSensorP2/3": {"status": "ok", "temperature": 43.0},
                            "TempSensorP2/2": {"status": "ok", "temperature": 31.0},
                        },
                        "fans": {"FanP2/1": {"status": "ok", "speed": 33}},
                        "state": "ok",
                        "inputCurrent": 0.572265625,
                        "dominant": False,
                        "inputVoltage": 232.5,
                        "outputCurrent": 9.828125,
                        "managed": True,
                    },
                }
            }
        ],
        "inputs": {"states": ["ok", "powerLoss"]},
        "expected": {"result": AntaTestStatus.SUCCESS},
    },
    (VerifyEnvironmentPower, "failure"): {
        "eos_data": [
            {
                "powerSupplies": {
                    "1": {
                        "outputPower": 0.0,
                        "modelName": "PWR-500AC-F",
                        "capacity": 500.0,
                        "tempSensors": {
                            "TempSensorP1/2": {"status": "ok", "temperature": 0.0},
                            "TempSensorP1/3": {"status": "ok", "temperature": 0.0},
                            "TempSensorP1/1": {"status": "ok", "temperature": 0.0},
                        },
                        "fans": {"FanP1/1": {"status": "ok", "speed": 33}},
                        "state": "powerLoss",
                        "inputCurrent": 0.0,
                        "dominant": False,
                        "inputVoltage": 0.0,
                        "outputCurrent": 0.0,
                        "managed": True,
                    },
                    "2": {
                        "outputPower": 117.375,
                        "uptime": 1682498935.9121966,
                        "modelName": "PWR-500AC-F",
                        "capacity": 500.0,
                        "tempSensors": {
                            "TempSensorP2/1": {"status": "ok", "temperature": 39.0},
                            "TempSensorP2/3": {"status": "ok", "temperature": 43.0},
                            "TempSensorP2/2": {"status": "ok", "temperature": 31.0},
                        },
                        "fans": {"FanP2/1": {"status": "ok", "speed": 33}},
                        "state": "ok",
                        "inputCurrent": 0.572265625,
                        "dominant": False,
                        "inputVoltage": 232.5,
                        "outputCurrent": 9.828125,
                        "managed": True,
                    },
                }
            }
        ],
        "inputs": {"states": ["ok"]},
        "expected": {"result": AntaTestStatus.FAILURE, "messages": ["Power Slot: 1 - Invalid power supplies state - Expected: ok Actual: powerLoss"]},
    },
    (VerifyAdverseDrops, "success"): {"eos_data": [{"totalAdverseDrops": 0}], "expected": {"result": AntaTestStatus.SUCCESS}},
    (VerifyAdverseDrops, "failure"): {
        "eos_data": [{"totalAdverseDrops": 10}],
        "expected": {"result": AntaTestStatus.FAILURE, "messages": ["Incorrect total adverse drops counter - Expected: 0 Actual: 10"]},
    },
    (VerifySupervisorRedundancy, "success-redunduncy-status"): {
        "eos_data": [
            {
                "configuredProtocol": "sso",
                "operationalProtocol": "sso",
                "communicationDesc": "Up",
                "peerState": "unknownPeerState",
                "switchoverReady": True,
            }
        ],
        "expected": {"result": AntaTestStatus.SUCCESS},
    },
    (VerifySupervisorRedundancy, "success-redunduncy-status-simplex"): {
        "eos_data": [
            {
                "configuredProtocol": "simplex",
                "operationalProtocol": "simplex",
                "communicationDesc": "Up",
                "peerState": "unknownPeerState",
                "switchoverReady": True,
            }
        ],
        "inputs": {"redundency_proto": "simplex"},
        "expected": {"result": AntaTestStatus.SUCCESS},
    },
    (VerifySupervisorRedundancy, "failure-no-redunduncy-status"): {
        "eos_data": [
            {
                "configuredProtocol": "simplex",
                "operationalProtocol": "simplex",
                "communicationDesc": "Up",
                "peerState": "unknownPeerState",
                "switchoverReady": True,
            }
        ],
        "expected": {"result": AntaTestStatus.FAILURE, "messages": ["Configured redundancy protocol mismatch - Expected sso Actual: simplex"]},
    },
    (VerifySupervisorRedundancy, "failure-no-redunduncy-operational"): {
        "eos_data": [
            {
                "configuredProtocol": "sso",
                "operationalProtocol": "simplex",
                "communicationDesc": "Up",
                "peerState": "unknownPeerState",
                "switchoverReady": False,
            }
        ],
        "expected": {"result": AntaTestStatus.FAILURE, "messages": ["Operational redundancy protocol mismatch - Expected sso Actual: simplex"]},
    },
    (VerifySupervisorRedundancy, "skip-card-not-inserted"): {
        "eos_data": [
            {
                "configuredProtocol": "sso",
                "operationalProtocol": "sso",
                "communicationDesc": "Up",
                "peerState": "notInserted",
                "switchoverReady": False,
            }
        ],
        "expected": {"result": AntaTestStatus.SKIPPED, "messages": ["Peer supervisor card not inserted"]},
    },
    (VerifySupervisorRedundancy, "failure-no-redunduncy-switchover-ready"): {
        "eos_data": [
            {
                "configuredProtocol": "sso",
                "operationalProtocol": "sso",
                "communicationDesc": "Up",
                "peerState": "unknownPeerState",
                "switchoverReady": False,
            }
        ],
        "expected": {"result": AntaTestStatus.FAILURE, "messages": ["Redundancy protocol switchover status mismatch - Expected: True Actual: False"]},
    },
}
