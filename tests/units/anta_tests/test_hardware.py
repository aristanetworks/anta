# Copyright (c) 2023-2025 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Test inputs for anta.tests.hardware."""
# pylint: disable=too-many-lines
# TODO: Cleanup unused data or move some tests to another module

from __future__ import annotations

import sys
from typing import TYPE_CHECKING, Any

from anta.models import AntaTest
from anta.result_manager.models import AntaTestStatus
from anta.tests.hardware import (
    VerifyAbsenceOfLinecards,
    VerifyAdverseDrops,
    VerifyChassisHealth,
    VerifyEnvironmentCooling,
    VerifyEnvironmentPower,
    VerifyEnvironmentSystemCooling,
    VerifyModuleStatus,
    VerifyPCIeErrors,
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
    (VerifyTransceiversManufacturers, "failure-unsupported"): {
        "eos_data": [
            {
                "xcvrSlots": {
                    "1": {"mfgName": "", "modelName": "", "serialNum": "", "hardwareRev": ""},
                }
            }
        ],
        "inputs": {"manufacturers": ["Arista"]},
        "expected": {
            "result": AntaTestStatus.FAILURE,
            "messages": [
                "Interface: 1 - Manufacturer name is not available - This may indicate an unsupported or faulty transceiver",
            ],
        },
    },
    (VerifyTemperature, "success"): {
        "eos_data": [
            {
                "systemStatus": "temperatureOk",
                "ambientThreshold": 45,
                "tempSensors": [
                    {
                        "name": "TempSensor1",
                        "description": "Cpu temp sensor",
                        "overheatThreshold": 90.0,
                        "criticalThreshold": 95.0,
                        "hwStatus": "ok",
                        "currentTemperature": 52.85271955304604,
                    },
                    {
                        "name": "TempSensor2",
                        "description": "Switch card temp sensor",
                        "overheatThreshold": 75.0,
                        "criticalThreshold": 85.0,
                        "hwStatus": "ok",
                        "currentTemperature": 45.875,
                    },
                ],
                "powerSupplySlots": [
                    {
                        "relPos": "1",
                        "entPhysicalClass": "PowerSupply",
                        "tempSensors": [
                            {
                                "name": "TempSensorP1/1",
                                "description": "Hotspot",
                                "overheatThreshold": 95.0,
                                "criticalThreshold": 100.0,
                                "targetTemperature": 80.0,
                                "hwStatus": "ok",
                                "currentTemperature": 54.0,
                                "inAlertState": False,
                                "alertCount": 0,
                                "isPidDriver": False,
                                "pidDriverCount": 0,
                            },
                            {
                                "relPos": "2",
                                "name": "TempSensorP1/2",
                                "description": "Inlet",
                                "overheatThreshold": 70.0,
                                "criticalThreshold": 75.0,
                                "targetTemperature": 55.0,
                                "hwStatus": "ok",
                                "currentTemperature": 44.0,
                                "inAlertState": False,
                                "alertCount": 0,
                            },
                        ],
                    },
                    {
                        "relPos": "2",
                        "entPhysicalClass": "PowerSupply",
                        "tempSensors": [
                            {
                                "relPos": "1",
                                "name": "TempSensorP2/1",
                                "description": "Hotspot",
                                "overheatThreshold": 95.0,
                                "criticalThreshold": 100.0,
                                "hwStatus": "ok",
                                "currentTemperature": 60.0,
                                "setPointTemperature": 82.65,
                                "inAlertState": False,
                                "alertCount": 0,
                            },
                            {
                                "name": "TempSensorP2/2",
                                "description": "Inlet",
                                "overheatThreshold": 70.0,
                                "criticalThreshold": 75.0,
                                "targetTemperature": 55.0,
                                "hwStatus": "ok",
                                "currentTemperature": 49.0,
                                "inAlertState": False,
                                "alertCount": 0,
                            },
                        ],
                    },
                ],
            }
        ],
        "expected": {"result": AntaTestStatus.SUCCESS},
    },
    (VerifyTemperature, "success-check-sensors-status-true"): {
        "eos_data": [
            {
                "systemStatus": "temperatureOk",
                "ambientThreshold": 45,
                "tempSensors": [
                    {
                        "name": "TempSensor1",
                        "description": "Cpu temp sensor",
                        "overheatThreshold": 90.0,
                        "criticalThreshold": 95.0,
                        "hwStatus": "ok",
                        "currentTemperature": 52.85271955304604,
                    },
                    {
                        "name": "TempSensor2",
                        "description": "Switch card temp sensor",
                        "overheatThreshold": 75.0,
                        "criticalThreshold": 85.0,
                        "hwStatus": "ok",
                        "currentTemperature": 45.875,
                    },
                ],
                "powerSupplySlots": [
                    {
                        "relPos": "1",
                        "entPhysicalClass": "PowerSupply",
                        "tempSensors": [
                            {
                                "name": "TempSensorP1/1",
                                "description": "Hotspot",
                                "overheatThreshold": 95.0,
                                "criticalThreshold": 100.0,
                                "targetTemperature": 80.0,
                                "hwStatus": "ok",
                                "currentTemperature": 54.0,
                                "inAlertState": False,
                                "alertCount": 0,
                                "isPidDriver": False,
                                "pidDriverCount": 0,
                            },
                            {
                                "relPos": "2",
                                "name": "TempSensorP1/2",
                                "description": "Inlet",
                                "overheatThreshold": 70.0,
                                "criticalThreshold": 75.0,
                                "targetTemperature": 55.0,
                                "hwStatus": "ok",
                                "currentTemperature": 44.0,
                                "inAlertState": False,
                                "alertCount": 0,
                            },
                        ],
                    },
                    {
                        "relPos": "2",
                        "entPhysicalClass": "PowerSupply",
                        "tempSensors": [
                            {
                                "relPos": "1",
                                "name": "TempSensorP2/1",
                                "description": "Hotspot",
                                "overheatThreshold": 95.0,
                                "criticalThreshold": 100.0,
                                "hwStatus": "ok",
                                "currentTemperature": 60.0,
                                "setPointTemperature": 82.65,
                                "inAlertState": False,
                                "alertCount": 0,
                            },
                            {
                                "name": "TempSensorP2/2",
                                "description": "Inlet",
                                "overheatThreshold": 70.0,
                                "criticalThreshold": 75.0,
                                "targetTemperature": 55.0,
                                "hwStatus": "ok",
                                "currentTemperature": 49.0,
                                "inAlertState": False,
                                "alertCount": 0,
                            },
                        ],
                    },
                ],
            }
        ],
        "inputs": {"check_temp_sensors": True},
        "expected": {"result": AntaTestStatus.SUCCESS},
    },
    (VerifyTemperature, "failure-hw-status-high-temp"): {
        "eos_data": [
            {
                "systemStatus": "temperatureOk",
                "ambientThreshold": 45,
                "tempSensors": [
                    {
                        "name": "TempSensor1",
                        "description": "Cpu temp sensor",
                        "overheatThreshold": 90.0,
                        "criticalThreshold": 95.0,
                        "hwStatus": "ok",
                        "currentTemperature": 93.85271955304604,
                    },
                    {
                        "name": "TempSensor2",
                        "description": "Switch card temp sensor",
                        "overheatThreshold": 75.0,
                        "criticalThreshold": 85.0,
                        "hwStatus": "ok",
                        "currentTemperature": 74.875,
                    },
                ],
                "powerSupplySlots": [
                    {
                        "relPos": "1",
                        "entPhysicalClass": "PowerSupply",
                        "tempSensors": [
                            {
                                "name": "TempSensorP1/1",
                                "description": "Hotspot",
                                "overheatThreshold": 90.0,
                                "criticalThreshold": 100.0,
                                "targetTemperature": 80.0,
                                "hwStatus": "ok",
                                "currentTemperature": 68.171875,
                                "inAlertState": False,
                                "alertCount": 0,
                                "isPidDriver": False,
                                "pidDriverCount": 0,
                            },
                            {
                                "relPos": "2",
                                "name": "TempSensorP1/2",
                                "description": "Inlet",
                                "overheatThreshold": 70.0,
                                "criticalThreshold": 75.0,
                                "targetTemperature": 55.0,
                                "hwStatus": "ok",
                                "currentTemperature": 44.0,
                                "inAlertState": False,
                                "alertCount": 0,
                            },
                        ],
                    },
                    {
                        "relPos": "2",
                        "entPhysicalClass": "PowerSupply",
                        "tempSensors": [
                            {
                                "relPos": "1",
                                "name": "TempSensorP2/1",
                                "description": "Hotspot",
                                "overheatThreshold": 95.0,
                                "criticalThreshold": 100.0,
                                "hwStatus": "ok",
                                "currentTemperature": 83.0,
                                "setPointTemperature": 82.65,
                                "inAlertState": False,
                                "alertCount": 0,
                            },
                            {
                                "name": "TempSensorP2/2",
                                "description": "Inlet",
                                "overheatThreshold": 70.0,
                                "criticalThreshold": 75.0,
                                "targetTemperature": 55.0,
                                "hwStatus": "ok",
                                "currentTemperature": 49.0,
                                "inAlertState": False,
                                "alertCount": 0,
                            },
                        ],
                    },
                ],
            }
        ],
        "inputs": {"check_temp_sensors": True},
        "expected": {
            "result": AntaTestStatus.FAILURE,
            "messages": [
                "Sensor: TempSensor1 Description: Cpu temp sensor - Temperature is getting high - "
                "Expected: <= 85.00°C (Overheat: 90.00°C - Margin: 5°C) Actual: 93.85°C",
                "Sensor: TempSensor2 Description: Switch card temp sensor - Temperature is getting high - "
                "Expected: <= 70.00°C (Overheat: 75.00°C - Margin: 5°C) Actual: 74.88°C",
            ],
        },
    },
    (VerifyTemperature, "failure-temperature-status"): {
        "eos_data": [
            {
                "systemStatus": "temperatureCritical",
                "ambientThreshold": 45,
                "tempSensors": [
                    {
                        "name": "TempSensor1",
                        "description": "Cpu temp sensor",
                        "overheatThreshold": 90.0,
                        "criticalThreshold": 95.0,
                        "hwStatus": "ok",
                        "currentTemperature": 52.85271955304604,
                    },
                    {
                        "name": "TempSensor2",
                        "description": "Switch card temp sensor",
                        "overheatThreshold": 75.0,
                        "criticalThreshold": 85.0,
                        "hwStatus": "ok",
                        "currentTemperature": 45.875,
                    },
                ],
                "powerSupplySlots": [
                    {
                        "relPos": "1",
                        "entPhysicalClass": "PowerSupply",
                        "tempSensors": [
                            {
                                "name": "TempSensorP1/1",
                                "description": "Hotspot",
                                "overheatThreshold": 55.0,
                                "criticalThreshold": 100.0,
                                "targetTemperature": 80.0,
                                "hwStatus": "ok",
                                "currentTemperature": 54.0,
                                "inAlertState": False,
                                "alertCount": 0,
                                "isPidDriver": False,
                                "pidDriverCount": 0,
                            },
                            {
                                "relPos": "2",
                                "name": "TempSensorP1/2",
                                "description": "Inlet",
                                "overheatThreshold": 70.0,
                                "criticalThreshold": 50.0,
                                "targetTemperature": 55.0,
                                "hwStatus": "ok",
                                "currentTemperature": 44.0,
                                "inAlertState": False,
                                "alertCount": 0,
                            },
                        ],
                    },
                    {
                        "relPos": "2",
                        "entPhysicalClass": "PowerSupply",
                        "tempSensors": [
                            {
                                "relPos": "1",
                                "name": "TempSensorP2/1",
                                "description": "Hotspot",
                                "overheatThreshold": 95.0,
                                "criticalThreshold": 100.0,
                                "hwStatus": "ok",
                                "currentTemperature": 60.0,
                                "setPointTemperature": 82.65,
                                "inAlertState": False,
                                "alertCount": 0,
                            },
                            {
                                "name": "TempSensorP2/2",
                                "description": "Inlet",
                                "overheatThreshold": 60.0,
                                "criticalThreshold": 75.0,
                                "targetTemperature": 55.0,
                                "hwStatus": "ok",
                                "currentTemperature": 59.0,
                                "inAlertState": False,
                                "alertCount": 0,
                            },
                        ],
                    },
                ],
            }
        ],
        "inputs": {"failure_margin": 6},
        "expected": {
            "result": AntaTestStatus.FAILURE,
            "messages": ["Device temperature exceeds acceptable limits - Expected: temperatureOk Actual: temperatureCritical"],
        },
    },
    (VerifyTemperature, "failure-all"): {
        "eos_data": [
            {
                "systemStatus": "temperatureCritical",
                "ambientThreshold": 45,
                "tempSensors": [
                    {
                        "name": "TempSensor1",
                        "description": "Cpu temp sensor",
                        "overheatThreshold": 90.0,
                        "criticalThreshold": 95.0,
                        "hwStatus": "ok",
                        "currentTemperature": 52.85271955304604,
                    },
                    {
                        "name": "TempSensor2",
                        "description": "Switch card temp sensor",
                        "overheatThreshold": 75.0,
                        "criticalThreshold": 85.0,
                        "hwStatus": "ok",
                        "currentTemperature": 45.875,
                    },
                ],
                "powerSupplySlots": [
                    {
                        "relPos": "1",
                        "entPhysicalClass": "PowerSupply",
                        "tempSensors": [
                            {
                                "name": "TempSensorP1/1",
                                "description": "Hotspot",
                                "overheatThreshold": 55.0,
                                "criticalThreshold": 100.0,
                                "targetTemperature": 80.0,
                                "hwStatus": "failed",
                                "currentTemperature": 54.0,
                                "inAlertState": False,
                                "alertCount": 0,
                                "isPidDriver": False,
                                "pidDriverCount": 0,
                            },
                            {
                                "relPos": "2",
                                "name": "TempSensorP1/2",
                                "description": "Inlet",
                                "overheatThreshold": 70.0,
                                "criticalThreshold": 50.0,
                                "targetTemperature": 55.0,
                                "hwStatus": "failed",
                                "currentTemperature": 44.0,
                                "inAlertState": False,
                                "alertCount": 0,
                            },
                        ],
                    },
                    {
                        "relPos": "2",
                        "entPhysicalClass": "PowerSupply",
                        "tempSensors": [
                            {
                                "relPos": "1",
                                "name": "TempSensorP2/1",
                                "description": "Hotspot",
                                "overheatThreshold": 95.0,
                                "criticalThreshold": 100.0,
                                "hwStatus": "ok",
                                "currentTemperature": 60.0,
                                "setPointTemperature": 82.65,
                                "inAlertState": False,
                                "alertCount": 0,
                            },
                            {
                                "name": "TempSensorP2/2",
                                "description": "Inlet",
                                "overheatThreshold": 60.0,
                                "criticalThreshold": 75.0,
                                "targetTemperature": 55.0,
                                "hwStatus": "ok",
                                "currentTemperature": 59.0,
                                "inAlertState": False,
                                "alertCount": 0,
                            },
                        ],
                    },
                ],
            }
        ],
        "inputs": {"check_temp_sensors": True},
        "expected": {
            "result": AntaTestStatus.FAILURE,
            "messages": [
                "Device temperature exceeds acceptable limits - Expected: temperatureOk Actual: temperatureCritical",
                "Sensor: TempSensorP1/1 Description: Hotspot - Invalid hardware status - Expected: ok Actual: failed",
                "Sensor: TempSensorP1/1 Description: Hotspot - Temperature is getting high - Expected: <= 50.00°C (Overheat: 55.00°C - Margin: 5°C) Actual: 54.00°C",
                "Sensor: TempSensorP1/2 Description: Inlet - Invalid hardware status - Expected: ok Actual: failed",
                "Sensor: TempSensorP2/2 Description: Inlet - Temperature is getting high - Expected: <= 55.00°C (Overheat: 60.00°C - Margin: 5°C) Actual: 59.00°C",
            ],
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
                        "hwStatus": "failed",
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
        "expected": {"result": AntaTestStatus.FAILURE, "messages": ["Sensor: DomTemperatureSensor54 - Invalid hardware state - Expected: ok Actual: failed"]},
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
    (VerifyEnvironmentCooling, "success-config-speed"): {
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
        "inputs": {"states": ["ok"], "configured_fan_speed_limit": 80},
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
    (VerifyEnvironmentCooling, "failure-powe-supply-fan-configspeed"): {
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
                                "configuredSpeed": 90,
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
                                "configuredSpeed": 90,
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
                                "configuredSpeed": 80,
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
        "inputs": {"states": ["ok"], "configured_fan_speed_limit": 80},
        "expected": {
            "result": AntaTestStatus.FAILURE,
            "messages": [
                "Power Slot: PowerSupply1 Fan: PowerSupply1/1 - High fan speed - Expected: <= 80 Actual: 90",
                "Power Slot: PowerSupply2 Fan: PowerSupply2/1 - High fan speed - Expected: <= 80 Actual: 90",
            ],
        },
    },
    (VerifyEnvironmentCooling, "failure-fan-tray-fan-configspeed"): {
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
                                "configuredSpeed": 34,
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
                                "configuredSpeed": 85,
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
                                "configuredSpeed": 90,
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
                                "configuredSpeed": 100,
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
        "inputs": {"states": ["ok"], "configured_fan_speed_limit": 80},
        "expected": {
            "result": AntaTestStatus.FAILURE,
            "messages": [
                "Fan Tray: 1 Fan: 1/1 - High fan speed - Expected: <= 80 Actual: 85",
                "Fan Tray: 2 Fan: 2/1 - High fan speed - Expected: <= 80 Actual: 90",
                "Fan Tray: 3 Fan: 3/1 - High fan speed - Expected: <= 80 Actual: 100",
            ],
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
                "Power Supply: 1 - Input voltage mismatch - Expected: >= 1 Actual: 0.25",
                "Power Supply: 2 - Input voltage mismatch - Expected: >= 1 Actual: 0.75",
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
    (VerifyAdverseDrops, "success"): {
        "eos_data": [
            {
                "dropEvents": {
                    "Fap0": {
                        "dropEvent": [
                            {
                                "counterName": "EpniAlignerError",
                                "counterType": "Adverse",
                                "dropCount": 7,
                                "dropInLastMinute": 0,
                                "dropInLastTenMinute": 0,
                                "dropInLastOneHour": 0,
                                "dropInLastOneDay": 0,
                                "dropInLastOneWeek": 0,
                            },
                        ]
                    }
                }
            },
            {
                "aradMappings": [
                    {
                        "fapName": "Fap0",
                        "portMappings": {
                            "2": {
                                "interface": "Ethernet1/1",
                            },
                        },
                    }
                ]
            },
            {
                "interfaceErrorCounters": {
                    "Ethernet1/1": {
                        "fcsErrors": 0,
                    },
                }
            },
        ],
        "expected": {"result": AntaTestStatus.SUCCESS},
    },
    (VerifyAdverseDrops, "success-drop-count-zero"): {
        "eos_data": [
            {
                "dropEvents": {
                    "Fap0": {
                        "dropEvent": [
                            {
                                "counterName": "EpniAlignerError",
                                "counterType": "Adverse",
                                "dropCount": 0,
                                "dropInLastMinute": 0,
                                "dropInLastTenMinute": 0,
                                "dropInLastOneHour": 0,
                                "dropInLastOneDay": 0,
                                "dropInLastOneWeek": 0,
                            },
                        ]
                    }
                }
            },
            {
                "aradMappings": [
                    {
                        "fapName": "Fap0",
                        "portMappings": {
                            "2": {
                                "interface": "Ethernet1/1",
                            },
                        },
                    }
                ]
            },
            {
                "interfaceErrorCounters": {
                    "Ethernet1/1": {
                        "fcsErrors": 0,
                    },
                }
            },
        ],
        "expected": {"result": AntaTestStatus.SUCCESS},
    },
    (VerifyAdverseDrops, "success-with-thresholds"): {
        "eos_data": [
            {
                "dropEvents": {
                    "Fap0": {
                        "dropEvent": [
                            {
                                "counterName": "EpniAlignerError",
                                "counterType": "Adverse",
                                "dropCount": 10,
                                "dropInLastMinute": 2,
                                "dropInLastTenMinute": 2,
                                "dropInLastOneHour": 2,
                                "dropInLastOneDay": 2,
                                "dropInLastOneWeek": 2,
                            },
                        ]
                    }
                }
            },
            {
                "aradMappings": [
                    {
                        "fapName": "Fap0",
                        "portMappings": {
                            "2": {
                                "interface": "Ethernet1/1",
                            },
                        },
                    }
                ]
            },
            {
                "interfaceErrorCounters": {
                    "Ethernet1/1": {
                        "fcsErrors": 0,
                    },
                }
            },
        ],
        "inputs": {"thresholds": {"minute": 10, "ten_minute": 10, "hour": 10, "day": 10, "week": 10}},
        "expected": {"result": AntaTestStatus.SUCCESS},
    },
    (VerifyAdverseDrops, "success-with-missing-thresholds-from-eapi"): {
        "eos_data": [
            {
                "dropEvents": {
                    "Fap0": {
                        "dropEvent": [
                            {
                                "counterName": "EpniAlignerError",
                                "counterType": "Adverse",
                                "dropCount": 10,
                                "dropInLastMinute": 2,
                                "dropInLastTenMinute": 2,
                            },
                        ]
                    }
                }
            },
            {
                "aradMappings": [
                    {
                        "fapName": "Fap0",
                        "portMappings": {
                            "2": {
                                "interface": "Ethernet1/1",
                            },
                        },
                    }
                ]
            },
            {
                "interfaceErrorCounters": {
                    "Ethernet1/1": {
                        "fcsErrors": 0,
                    },
                }
            },
        ],
        "inputs": {"thresholds": {"minute": 10, "ten_minute": 10, "hour": 10, "day": 10, "week": 10}},
        "expected": {"result": AntaTestStatus.SUCCESS},
    },
    (VerifyAdverseDrops, "success-not-adverse"): {
        "eos_data": [
            {
                "dropEvents": {
                    "Fap0": {
                        "dropEvent": [
                            {
                                "counterName": "EpniAlignerError",
                                "counterType": "PacketProcessor",
                                "dropCount": 7,
                                "dropInLastMinute": 0,
                                "dropInLastTenMinute": 0,
                                "dropInLastOneHour": 0,
                                "dropInLastOneDay": 0,
                                "dropInLastOneWeek": 0,
                            },
                        ]
                    }
                }
            },
            {
                "aradMappings": [
                    {
                        "fapName": "Fap0",
                        "portMappings": {
                            "2": {
                                "interface": "Ethernet1/1",
                            },
                        },
                    }
                ]
            },
            {
                "interfaceErrorCounters": {
                    "Ethernet1/1": {
                        "fcsErrors": 0,
                    },
                }
            },
        ],
        "expected": {"result": AntaTestStatus.SUCCESS},
    },
    (VerifyAdverseDrops, "failure"): {
        "eos_data": [
            {
                "dropEvents": {
                    "Fap0": {
                        "dropEvent": [
                            {
                                "counterName": "EpniAlignerError",
                                "counterType": "Adverse",
                                "dropCount": 7,
                                "dropInLastMinute": 1,
                                "dropInLastTenMinute": 2,
                                "dropInLastOneHour": 3,
                                "dropInLastOneDay": 4,
                                "dropInLastOneWeek": 5,
                            },
                        ]
                    }
                }
            },
            {
                "aradMappings": [
                    {
                        "fapName": "Fap0",
                        "portMappings": {
                            "2": {
                                "interface": "Ethernet1/1",
                            },
                        },
                    }
                ]
            },
            {
                "interfaceErrorCounters": {
                    "Ethernet1/1": {
                        "fcsErrors": 2,
                    },
                }
            },
        ],
        "expected": {
            "result": AntaTestStatus.FAILURE,
            "messages": [
                "FAP: Fap0 Counter: EpniAlignerError - Last minute rate above threshold - Expected: <= 0 Actual: 1",
                "FAP: Fap0 Counter: EpniAlignerError - Last 10 minutes rate above threshold - Expected: <= 0 Actual: 2",
                "FAP: Fap0 Counter: EpniAlignerError - Last hour rate above threshold - Expected: <= 0 Actual: 3",
                "FAP: Fap0 Counter: EpniAlignerError - Last day rate above threshold - Expected: <= 0 Actual: 4",
                "FAP: Fap0 Counter: EpniAlignerError - Last week rate above threshold - Expected: <= 0 Actual: 5",
            ],
        },
    },
    (VerifyAdverseDrops, "success-reassembly-errors"): {
        "eos_data": [
            {
                "dropEvents": {
                    "Fap0": {
                        "dropEvent": [
                            {
                                "counterName": "ReassemblyErrors",
                                "counterType": "Adverse",
                                "dropCount": 7,
                                "dropInLastMinute": 1,
                                "dropInLastTenMinute": 2,
                                "dropInLastOneHour": 3,
                                "dropInLastOneDay": 4,
                                "dropInLastOneWeek": 5,
                            },
                        ]
                    }
                }
            },
            {
                "aradMappings": [
                    {
                        "fapName": "Fap0",
                        "portMappings": {
                            "2": {
                                "interface": "Ethernet1/1",
                            },
                        },
                    }
                ]
            },
            {
                "interfaceErrorCounters": {
                    "Ethernet1/1": {
                        "fcsErrors": 2,
                    },
                }
            },
        ],
        "inputs": {"always_fail_on_reassembly_errors": False},
        "expected": {"result": AntaTestStatus.SUCCESS},
    },
    (VerifyAdverseDrops, "failure-reassembly-errors"): {
        "eos_data": [
            {
                "dropEvents": {
                    "Fap0": {
                        "dropEvent": [
                            {
                                "counterName": "ReassemblyErrors",
                                "counterType": "Adverse",
                                "dropCount": 5,
                                "dropInLastMinute": 0,
                                "dropInLastTenMinute": 0,
                                "dropInLastOneHour": 0,
                                "dropInLastOneDay": 0,
                                "dropInLastOneWeek": 5,
                            },
                        ]
                    }
                }
            },
            {
                "aradMappings": [
                    {
                        "fapName": "Fap0",
                        "portMappings": {
                            "2": {
                                "interface": "Ethernet1/1",
                            },
                        },
                    }
                ]
            },
            {
                "interfaceErrorCounters": {
                    "Ethernet1/1": {
                        "fcsErrors": 2,
                    },
                }
            },
        ],
        "inputs": {"always_fail_on_reassembly_errors": True},
        "expected": {
            "result": AntaTestStatus.FAILURE,
            "messages": [
                "FAP: Fap0 Counter: ReassemblyErrors - Last week rate above threshold - Expected: <= 0 Actual: 5",
            ],
        },
    },
    (VerifyAdverseDrops, "failure-with-thresholds"): {
        "eos_data": [
            {
                "dropEvents": {
                    "Fap0": {
                        "dropEvent": [
                            {
                                "counterName": "EpniAlignerError",
                                "counterType": "Adverse",
                                "dropCount": 10,
                                "dropInLastMinute": 2,
                                "dropInLastTenMinute": 2,
                                "dropInLastOneHour": 2,
                                "dropInLastOneDay": 2,
                                "dropInLastOneWeek": 2,
                            },
                        ]
                    }
                }
            },
            {
                "aradMappings": [
                    {
                        "fapName": "Fap0",
                        "portMappings": {
                            "2": {
                                "interface": "Ethernet1/1",
                            },
                        },
                    }
                ]
            },
            {
                "interfaceErrorCounters": {
                    "Ethernet1/1": {
                        "fcsErrors": 0,
                    },
                }
            },
        ],
        "inputs": {"thresholds": {"minute": 0, "ten_minute": 10, "hour": 10, "day": 10, "week": 10}},
        "expected": {
            "result": AntaTestStatus.FAILURE,
            "messages": [
                "FAP: Fap0 Counter: EpniAlignerError - Last minute rate above threshold - Expected: <= 0 Actual: 2",
            ],
        },
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
        "inputs": {"redundancy_proto": "simplex"},
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
    (VerifyPCIeErrors, "success"): {
        "eos_data": [
            {
                "pciIds": {
                    "00:00.0": {"name": "DomainRoot0", "correctableErrors": 0, "nonFatalErrors": 0, "fatalErrors": 0, "linkSpeed": 0.0, "linkWidth": 0},
                    "05:00.0": {
                        "name": "Slot1:SwitchMicrosemiSwitch:BridgeBr0",
                        "correctableErrors": 0,
                        "nonFatalErrors": 0,
                        "fatalErrors": 0,
                        "linkSpeed": 8.0,
                        "linkWidth": 16,
                    },
                    "06:00.0": {
                        "name": "Slot1:SwitchMicrosemiSwitch:BridgeBr1",
                        "correctableErrors": 0,
                        "nonFatalErrors": 0,
                        "fatalErrors": 0,
                        "linkSpeed": 8.0,
                        "linkWidth": 1,
                    },
                }
            }
        ],
        "expected": {"result": AntaTestStatus.SUCCESS},
    },
    (VerifyPCIeErrors, "failure-correctable-errors"): {
        "eos_data": [
            {
                "pciIds": {
                    "00:00.0": {"name": "DomainRoot0", "correctableErrors": 300000, "nonFatalErrors": 0, "fatalErrors": 0, "linkSpeed": 0.0, "linkWidth": 0},
                    "05:00.0": {
                        "name": "Slot1:SwitchMicrosemiSwitch:BridgeBr0",
                        "correctableErrors": 140000,
                        "nonFatalErrors": 0,
                        "fatalErrors": 0,
                        "linkSpeed": 8.0,
                        "linkWidth": 16,
                    },
                    "06:00.0": {
                        "name": "Slot1:SwitchMicrosemiSwitch:BridgeBr1",
                        "correctableErrors": 20000,
                        "nonFatalErrors": 0,
                        "fatalErrors": 0,
                        "linkSpeed": 8.0,
                        "linkWidth": 1,
                    },
                }
            }
        ],
        "inputs": {"thresholds": {"correctable_errors": 20000}},
        "expected": {
            "result": AntaTestStatus.FAILURE,
            "messages": [
                "PCI Name: DomainRoot0 PCI ID: 00:00.0 - Correctable errors above threshold - Expected: <= 20000 Actual: 300000",
                "PCI Name: Slot1:SwitchMicrosemiSwitch:BridgeBr0 PCI ID: 05:00.0 - Correctable errors above threshold - Expected: <= 20000 Actual: 140000",
            ],
        },
    },
    (VerifyPCIeErrors, "failure-non-fatal-errors"): {
        "eos_data": [
            {
                "pciIds": {
                    "00:00.0": {"name": "DomainRoot0", "correctableErrors": 0, "nonFatalErrors": 550, "fatalErrors": 0, "linkSpeed": 0.0, "linkWidth": 0},
                    "05:00.0": {
                        "name": "Slot1:SwitchMicrosemiSwitch:BridgeBr0",
                        "correctableErrors": 0,
                        "nonFatalErrors": 260,
                        "fatalErrors": 0,
                        "linkSpeed": 8.0,
                        "linkWidth": 16,
                    },
                    "06:00.0": {
                        "name": "Slot1:SwitchMicrosemiSwitch:BridgeBr1",
                        "correctableErrors": 0,
                        "nonFatalErrors": 270,
                        "fatalErrors": 0,
                        "linkSpeed": 8.0,
                        "linkWidth": 1,
                    },
                }
            }
        ],
        "inputs": {"thresholds": {"non_fatal_errors": 260}},
        "expected": {
            "result": AntaTestStatus.FAILURE,
            "messages": [
                "PCI Name: DomainRoot0 PCI ID: 00:00.0 - Non-fatal errors above threshold - Expected: <= 260 Actual: 550",
                "PCI Name: Slot1:SwitchMicrosemiSwitch:BridgeBr1 PCI ID: 06:00.0 - Non-fatal errors above threshold - Expected: <= 260 Actual: 270",
            ],
        },
    },
    (VerifyPCIeErrors, "failure-fatal-errors"): {
        "eos_data": [
            {
                "pciIds": {
                    "00:00.0": {"name": "DomainRoot0", "correctableErrors": 0, "nonFatalErrors": 0, "fatalErrors": 0, "linkSpeed": 0.0, "linkWidth": 0},
                    "05:00.0": {
                        "name": "Slot1:SwitchMicrosemiSwitch:BridgeBr0",
                        "correctableErrors": 0,
                        "nonFatalErrors": 0,
                        "fatalErrors": 260,
                        "linkSpeed": 8.0,
                        "linkWidth": 16,
                    },
                    "06:00.0": {
                        "name": "Slot1:SwitchMicrosemiSwitch:BridgeBr1",
                        "correctableErrors": 0,
                        "nonFatalErrors": 0,
                        "fatalErrors": 280,
                        "linkSpeed": 8.0,
                        "linkWidth": 1,
                    },
                }
            }
        ],
        "expected": {
            "result": AntaTestStatus.FAILURE,
            "messages": [
                "PCI Name: Slot1:SwitchMicrosemiSwitch:BridgeBr0 PCI ID: 05:00.0 - Fatal errors above threshold - Expected: <= 0 Actual: 260",
                "PCI Name: Slot1:SwitchMicrosemiSwitch:BridgeBr1 PCI ID: 06:00.0 - Fatal errors above threshold - Expected: <= 0 Actual: 280",
            ],
        },
    },
    (VerifyPCIeErrors, "failure-all-errors"): {
        "eos_data": [
            {
                "pciIds": {
                    "00:00.0": {"name": "DomainRoot0", "correctableErrors": 500, "nonFatalErrors": 80, "fatalErrors": 90, "linkSpeed": 0.0, "linkWidth": 0},
                    "05:00.0": {
                        "name": "Slot1:SwitchMicrosemiSwitch:BridgeBr0",
                        "correctableErrors": 990,
                        "nonFatalErrors": 50,
                        "fatalErrors": 260,
                        "linkSpeed": 8.0,
                        "linkWidth": 16,
                    },
                    "06:00.0": {
                        "name": "Slot1:SwitchMicrosemiSwitch:BridgeBr1",
                        "correctableErrors": 0,
                        "nonFatalErrors": 0,
                        "fatalErrors": 280,
                        "linkSpeed": 8.0,
                        "linkWidth": 1,
                    },
                }
            }
        ],
        "inputs": {"thresholds": {"correctable_errors": 300, "non_fatal_errors": 60, "fatal_errors": 60}},
        "expected": {
            "result": AntaTestStatus.FAILURE,
            "messages": [
                "PCI Name: DomainRoot0 PCI ID: 00:00.0 - Correctable errors above threshold - Expected: <= 300 Actual: 500",
                "PCI Name: DomainRoot0 PCI ID: 00:00.0 - Non-fatal errors above threshold - Expected: <= 60 Actual: 80",
                "PCI Name: DomainRoot0 PCI ID: 00:00.0 - Fatal errors above threshold - Expected: <= 60 Actual: 90",
                "PCI Name: Slot1:SwitchMicrosemiSwitch:BridgeBr0 PCI ID: 05:00.0 - Correctable errors above threshold - Expected: <= 300 Actual: 990",
                "PCI Name: Slot1:SwitchMicrosemiSwitch:BridgeBr0 PCI ID: 05:00.0 - Fatal errors above threshold - Expected: <= 60 Actual: 260",
                "PCI Name: Slot1:SwitchMicrosemiSwitch:BridgeBr1 PCI ID: 06:00.0 - Fatal errors above threshold - Expected: <= 60 Actual: 280",
            ],
        },
    },
    (VerifyAbsenceOfLinecards, "success"): {
        "eos_data": [
            {
                "cardSlots": {
                    "Fabric1": {
                        "modelName": "7812R3-FM",
                        "serialNum": "VITTHAL0104A",
                    },
                    "Fabric2": {
                        "modelName": "7812R3-FM",
                        "serialNum": "VITTHAL0104B",
                    },
                    "Supervisor1": {
                        "modelName": "DCS-7816-SUP",
                        "serialNum": "VITTHAL0104C",
                    },
                    "Supervisor2": {
                        "modelName": "DCS-7816-SUP",
                        "serialNum": "VITTHAL0104D",
                    },
                    "Linecard3": {
                        "modelName": "7800R3A-36D-LC",
                        "serialNum": "VITTHAL0104E",
                    },
                    "Linecard4": {
                        "modelName": "7800R3A-36D-LC",
                        "serialNum": "VITTHAL0104F",
                    },
                    "Linecard5": {
                        "modelName": "7800R3A-36D-LC",
                        "serialNum": "VITTHAL0104G",
                    },
                },
            }
        ],
        "inputs": {"serial_numbers": ["FGN23450CW1"]},
        "expected": {"result": AntaTestStatus.SUCCESS},
    },
    (VerifyAbsenceOfLinecards, "failure"): {
        "eos_data": [
            {
                "cardSlots": {
                    "Fabric1": {
                        "modelName": "7812R3-FM",
                        "serialNum": "VITTHAL0104A",
                    },
                    "Fabric2": {
                        "modelName": "7812R3-FM",
                        "serialNum": "VITTHAL0104B",
                    },
                    "Supervisor1": {
                        "modelName": "DCS-7816-SUP",
                        "serialNum": "VITTHAL0104C",
                    },
                    "Supervisor2": {
                        "modelName": "DCS-7816-SUP",
                        "serialNum": "VITTHAL0104D",
                    },
                    "Linecard3": {
                        "modelName": "7800R3A-36D-LC",
                        "serialNum": "VITTHAL0104E",
                    },
                    "Linecard4": {
                        "modelName": "7800R3A-36D-LC",
                        "serialNum": "VITTHAL0104F",
                    },
                    "Linecard5": {
                        "modelName": "7800R3A-36D-LC",
                        "serialNum": "VITTHAL0104G",
                    },
                },
            }
        ],
        "inputs": {"serial_numbers": ["VITTHAL0104E", "VITTHAL0104C", "VITTHAL0104A"]},
        "expected": {
            "result": AntaTestStatus.FAILURE,
            "messages": ["Decommissioned linecards found in inventory: VITTHAL0104A, VITTHAL0104C, VITTHAL0104E"],
        },
    },
    (VerifyChassisHealth, "success"): {
        "eos_data": [
            {
                "numLinecards": 12,
                "linecardsNotInitialized": {},
                "numFabricCards": 6,
                "fabricCardsNotInitialized": {},
                "fabricInterruptOccurrences": {
                    "Fabric6": {"count": 0},
                    "Fabric1": {"count": 0},
                    "Fabric2": {"count": 0},
                    "Fabric3": {"count": 0},
                    "Fabric5": {"count": 0},
                    "Fabric4": {"count": 0},
                },
            }
        ],
        "expected": {"result": AntaTestStatus.SUCCESS},
    },
    (VerifyChassisHealth, "failure-no-linecard-initialized"): {
        "eos_data": [
            {
                "numLinecards": 12,
                "linecardsNotInitialized": {"line_card1": "not initialized", "line_card2": "not initialized"},
                "numFabricCards": 6,
                "fabricCardsNotInitialized": {},
                "fabricInterruptOccurrences": {
                    "Fabric6": {"count": 0},
                    "Fabric1": {"count": 0},
                    "Fabric2": {"count": 0},
                    "Fabric3": {"count": 0},
                    "Fabric5": {"count": 0},
                    "Fabric4": {"count": 0},
                },
            }
        ],
        "expected": {"result": AntaTestStatus.FAILURE, "messages": ["Linecard: line_card1 - Not initialized", "Linecard: line_card2 - Not initialized"]},
    },
    (VerifyChassisHealth, "failure-no-fabric-card-initialized"): {
        "eos_data": [
            {
                "numLinecards": 12,
                "linecardsNotInitialized": {},
                "numFabricCards": 6,
                "fabricCardsNotInitialized": {"FixedSystem": "hwStateUninitialized"},
                "fabricInterruptOccurrences": {
                    "Fabric6": {"count": 0},
                    "Fabric1": {"count": 0},
                    "Fabric2": {"count": 0},
                    "Fabric3": {"count": 0},
                    "Fabric5": {"count": 0},
                    "Fabric4": {"count": 0},
                },
            }
        ],
        "expected": {"result": AntaTestStatus.FAILURE, "messages": ["Fabric card: FixedSystem - Not initialized"]},
    },
    (VerifyChassisHealth, "failure-fabric-interrupts"): {
        "eos_data": [
            {
                "numLinecards": 12,
                "linecardsNotInitialized": {},
                "numFabricCards": 6,
                "fabricCardsNotInitialized": {},
                "fabricInterruptOccurrences": {
                    "Fabric6": {"count": 10},
                    "Fabric1": {"count": 0},
                    "Fabric2": {"count": 0},
                    "Fabric3": {"count": 20},
                    "Fabric5": {"count": 0},
                    "Fabric4": {"count": 40},
                },
            }
        ],
        "expected": {
            "result": AntaTestStatus.FAILURE,
            "messages": [
                "Fabric: Fabric6 - Fabric interrupts above threshold - Expected: <= 0 Actual: 10",
                "Fabric: Fabric3 - Fabric interrupts above threshold - Expected: <= 0 Actual: 20",
                "Fabric: Fabric4 - Fabric interrupts above threshold - Expected: <= 0 Actual: 40",
            ],
        },
    },
    (VerifyChassisHealth, "failure-all"): {
        "eos_data": [
            {
                "numLinecards": 12,
                "linecardsNotInitialized": {"line_card1": "not initialized", "line_card2": "not initialized"},
                "numFabricCards": 6,
                "fabricCardsNotInitialized": {"fabric_card1": "not initialized", "fabric_card2": "not initialized"},
                "fabricInterruptOccurrences": {
                    "Fabric6": {"count": 0},
                    "Fabric1": {"count": 0},
                    "Fabric2": {"count": 0},
                    "Fabric3": {"count": 20},
                    "Fabric5": {"count": 0},
                    "Fabric4": {"count": 0},
                },
            }
        ],
        "expected": {
            "result": AntaTestStatus.FAILURE,
            "messages": [
                "Linecard: line_card1 - Not initialized",
                "Linecard: line_card2 - Not initialized",
                "Fabric card: fabric_card1 - Not initialized",
                "Fabric card: fabric_card2 - Not initialized",
                "Fabric: Fabric3 - Fabric interrupts above threshold - Expected: <= 0 Actual: 20",
            ],
        },
    },
    (VerifyModuleStatus, "success-dual-supervisor"): {
        "eos_data": [
            {
                "modules": {
                    "3": {
                        "status": "ok",
                        "modelName": "7R3AK-ABC-LC",
                    },
                    "Fabric1": {
                        "status": "ok",
                        "modelName": "7R3AK-XYZ-LC",
                    },
                    "Fabric2": {
                        "status": "ok",
                        "modelName": "7R3AK-XYZ-OP",
                    },
                    "4": {
                        "status": "ok",
                        "modelName": "78939-XYZ-OP",
                    },
                    "1": {
                        "status": "active",
                        "modelName": "78939-XYZ-SUP",
                    },
                    "2": {
                        "status": "standby",
                        "modelName": "939-XYZ-SUP",
                    },
                }
            },
            {
                "modules": {
                    "Fabric6": {"risers": {}},
                    "Linecard10": {
                        "risers": {
                            "3": {"interfaces": "Ethernet10/5/1,Ethernet10/6/1", "powerGood": True},
                        }
                    },
                    "Linecard3": {
                        "risers": {
                            "6": {"interfaces": "Ethernet3/11/1,Ethernet3/12/1", "powerGood": True},
                            "13": {"interfaces": "Ethernet3/25/1,Ethernet3/26/1", "powerGood": True},
                        }
                    },
                    "Linecard14": {
                        "risers": {
                            "10": {"interfaces": "Ethernet14/19/1,Ethernet14/20/1", "powerGood": True},
                            "2": {"interfaces": "Ethernet14/3/1,Ethernet14/4/1", "powerGood": True},
                        }
                    },
                }
            },
        ],
        "inputs": {"check_dual_supervisor_system": True},
        "expected": {"result": AntaTestStatus.SUCCESS},
    },
    (VerifyModuleStatus, "failure-dual-supervisor-primary-not-found"): {
        "eos_data": [
            {
                "modules": {
                    "3": {
                        "status": "ok",
                        "modelName": "7R3AK-ABC-LC",
                    },
                    "Fabric1": {
                        "status": "ok",
                        "modelName": "7R3AK-UI-LC",
                    },
                    "4": {
                        "status": "ok",
                        "modelName": "7AHCAK-UI-LC",
                    },
                    "2": {
                        "status": "standby",
                        "modelName": "7ASAK-UI-SUP",
                    },
                }
            },
            {
                "modules": {
                    "Linecard3": {
                        "risers": {
                            "6": {"interfaces": "Ethernet3/11/1,Ethernet3/12/1", "powerGood": True},
                            "11": {"interfaces": "Ethernet3/21/1,Ethernet3/22/1", "powerGood": True},
                        }
                    },
                    "Fabric1": {"risers": {}},
                    "Linecard14": {
                        "risers": {
                            "13": {"interfaces": "Ethernet14/25/1,Ethernet14/26/1", "powerGood": True},
                        }
                    },
                }
            },
        ],
        "inputs": {"check_dual_supervisor_system": True},
        "expected": {"result": AntaTestStatus.FAILURE, "messages": ["Dual supervisor system - Expected supervisor module(s) not found"]},
    },
    (VerifyModuleStatus, "failure-dual-supervisors-not-found"): {
        "eos_data": [
            {
                "modules": {
                    "3": {
                        "status": "ok",
                        "modelName": "7R3AK-ABC-LC",
                    },
                    "Fabric1": {
                        "status": "ok",
                        "modelName": "7R3AK-UI-LC",
                    },
                    "4": {
                        "status": "ok",
                        "modelName": "7AHCAK-UI-LC",
                    },
                }
            },
            {
                "modules": {
                    "Linecard3": {
                        "risers": {
                            "6": {"interfaces": "Ethernet3/11/1,Ethernet3/12/1", "powerGood": True},
                            "11": {"interfaces": "Ethernet3/21/1,Ethernet3/22/1", "powerGood": True},
                        }
                    },
                    "Fabric1": {"risers": {}},
                    "Linecard14": {
                        "risers": {
                            "13": {"interfaces": "Ethernet14/25/1,Ethernet14/26/1", "powerGood": True},
                        }
                    },
                }
            },
        ],
        "inputs": {"check_dual_supervisor_system": True},
        "expected": {"result": AntaTestStatus.FAILURE, "messages": ["Dual supervisor system - Expected supervisor module(s) not found"]},
    },
    (VerifyModuleStatus, "failure-single-supervisor-not-connected"): {
        "eos_data": [
            {
                "modules": {
                    "3": {
                        "status": "ok",
                        "modelName": "7AHCAK-UI-UP",
                    },
                    "Fabric1": {
                        "status": "ok",
                        "modelName": "7AHCAK-UI-SP",
                    },
                    "4": {
                        "status": "ok",
                        "modelName": "7AHCAK-SCUI-UP",
                    },
                }
            },
            {
                "modules": {
                    "Linecard3": {
                        "risers": {
                            "6": {"interfaces": "Ethernet3/11/1,Ethernet3/12/1", "powerGood": True},
                            "11": {"interfaces": "Ethernet3/21/1,Ethernet3/22/1", "powerGood": True},
                        }
                    },
                    "Fabric1": {"risers": {}},
                    "Linecard14": {
                        "risers": {
                            "13": {"interfaces": "Ethernet14/25/1,Ethernet14/26/1", "powerGood": True},
                        }
                    },
                }
            },
        ],
        "expected": {"result": AntaTestStatus.FAILURE, "messages": ["Single supervisor system - Expected supervisor module(s) not found"]},
    },
    (VerifyModuleStatus, "failure-peer-supervisor-not-standby"): {
        "eos_data": [
            {
                "modules": {
                    "3": {
                        "status": "ok",
                        "modelName": "7AHCAK-UI-UP",
                    },
                    "Fabric1": {
                        "status": "ok",
                        "modelName": "7USAHCAK-UI-UP",
                    },
                    "4": {
                        "status": "ok",
                        "modelName": "7USAHCAK-UI-FP",
                    },
                    "1": {
                        "status": "active",
                        "modelName": "7USAHCAK-UI-SUP",
                    },
                    "2": {
                        "status": "ok",
                        "modelName": "89USAHCAK-UI-SUP",
                    },
                }
            },
            {
                "modules": {
                    "Linecard3": {
                        "risers": {
                            "6": {"interfaces": "Ethernet3/11/1,Ethernet3/12/1", "powerGood": True},
                            "11": {"interfaces": "Ethernet3/21/1,Ethernet3/22/1", "powerGood": True},
                        }
                    },
                    "Fabric1": {"risers": {}},
                    "Linecard14": {
                        "risers": {
                            "13": {"interfaces": "Ethernet14/25/1,Ethernet14/26/1", "powerGood": True},
                        }
                    },
                }
            },
        ],
        "inputs": {"check_dual_supervisor_system": True},
        "expected": {
            "result": AntaTestStatus.FAILURE,
            "messages": ["Dual supervisor system - Supervisor status mismatch - Expected: active/standby Actual: active/ok"],
        },
    },
    (VerifyModuleStatus, "failure-dual-supervisor-not-standby"): {
        "eos_data": [
            {
                "modules": {
                    "3": {
                        "status": "ok",
                        "modelName": "7USAHCAK-UI-UP",
                    },
                    "Fabric1": {
                        "status": "ok",
                        "modelName": "7USAHCAD-UI-UP",
                    },
                    "4": {
                        "status": "ok",
                        "modelName": "7USAHCAK-UI-2UUP",
                    },
                    "1": {
                        "status": "ok",
                        "modelName": "7USAHCAK-UI-SUP",
                    },
                    "2": {
                        "status": "active",
                        "modelName": "90SAHCAK-UI-SUP",
                    },
                }
            },
            {
                "modules": {
                    "Linecard3": {
                        "risers": {
                            "6": {"interfaces": "Ethernet3/11/1,Ethernet3/12/1", "powerGood": True},
                            "11": {"interfaces": "Ethernet3/21/1,Ethernet3/22/1", "powerGood": True},
                        }
                    },
                    "Fabric1": {"risers": {}},
                    "Linecard14": {
                        "risers": {
                            "13": {"interfaces": "Ethernet14/25/1,Ethernet14/26/1", "powerGood": True},
                        }
                    },
                }
            },
        ],
        "inputs": {"check_dual_supervisor_system": True},
        "expected": {
            "result": AntaTestStatus.FAILURE,
            "messages": ["Dual supervisor system - Supervisor status mismatch - Expected: active/standby Actual: ok/active"],
        },
    },
    (VerifyModuleStatus, "success-single-supervisor-system-module-1"): {
        "eos_data": [
            {
                "modules": {
                    "3": {
                        "status": "ok",
                        "modelName": "7USAHCAK-UI-UP",
                    },
                    "Fabric1": {
                        "status": "ok",
                        "modelName": "7U9AHCAK-UI-UP",
                    },
                    "4": {
                        "status": "ok",
                        "modelName": "7USAIOOHCAK-UI-UP",
                    },
                    "2": {
                        "status": "ok",
                        "modelName": "7UBCAIOOHCAK-UI-UP",
                    },
                    "1": {
                        "status": "active",
                        "modelName": "7USAHCAK-UI-SUP",
                    },
                }
            },
            {
                "modules": {
                    "Linecard3": {
                        "risers": {
                            "6": {"interfaces": "Ethernet3/11/1,Ethernet3/12/1", "powerGood": True},
                            "11": {"interfaces": "Ethernet3/21/1,Ethernet3/22/1", "powerGood": True},
                        }
                    },
                    "Fabric1": {"risers": {}},
                    "Linecard14": {
                        "risers": {
                            "13": {"interfaces": "Ethernet14/25/1,Ethernet14/26/1", "powerGood": True},
                        }
                    },
                }
            },
        ],
        "expected": {"result": AntaTestStatus.SUCCESS},
    },
    (VerifyModuleStatus, "failiure-single-supervisor-cardslots-state"): {
        "eos_data": [
            {
                "modules": {
                    "3": {
                        "status": "notok",
                        "modelName": "7USAHCAK-UI-UP",
                    },
                    "Fabric1": {
                        "status": "ok",
                        "modelName": "7USPPHCAK-UI-UP",
                    },
                    "4": {
                        "status": "notok",
                        "modelName": "7999-RUSAHCAK-UI-UP",
                    },
                    "1": {
                        "status": "active",
                        "modelName": "7999-RUSAHCAK-UI-SUP",
                    },
                    "2": {
                        "status": "ok",
                        "modelName": "7999-RUSAHCAK-UI",
                    },
                }
            },
            {
                "modules": {
                    "Linecard3": {
                        "risers": {
                            "6": {"interfaces": "Ethernet3/11/1,Ethernet3/12/1", "powerGood": True},
                            "11": {"interfaces": "Ethernet3/21/1,Ethernet3/22/1", "powerGood": True},
                        }
                    },
                    "Fabric1": {"risers": {}},
                    "Linecard14": {
                        "risers": {
                            "13": {"interfaces": "Ethernet14/25/1,Ethernet14/26/1", "powerGood": True},
                        }
                    },
                }
            },
        ],
        "expected": {
            "result": AntaTestStatus.FAILURE,
            "messages": [
                "Module: 3 Model: 7USAHCAK-UI-UP - Invalid status - Expected: ok Actual: notok",
                "Module: 4 Model: 7999-RUSAHCAK-UI-UP - Invalid status - Expected: ok Actual: notok",
            ],
        },
    },
    (VerifyModuleStatus, "failiure-single-supervisior-module-2-cardslots-state"): {
        "eos_data": [
            {
                "modules": {
                    "3": {
                        "status": "notok",
                        "modelName": "7USAHCAK-UI-UP",
                    },
                    "Fabric1": {
                        "status": "ok",
                        "modelName": "7USPPHCAK-UI-UP",
                    },
                    "4": {
                        "status": "failed",
                        "modelName": "7999-RUSAHCAK-UI-UP",
                    },
                    "1": {
                        "status": "active",
                        "modelName": "7999-RUSAHCAK-UI-SUP",
                    },
                    "2": {
                        "status": "failed",
                        "modelName": "7999-RUSAHCAK-UI",
                    },
                }
            },
            {
                "modules": {
                    "Linecard3": {
                        "risers": {
                            "6": {"interfaces": "Ethernet3/11/1,Ethernet3/12/1", "powerGood": True},
                            "11": {"interfaces": "Ethernet3/21/1,Ethernet3/22/1", "powerGood": True},
                        }
                    },
                    "Fabric1": {"risers": {}},
                    "Linecard14": {
                        "risers": {
                            "13": {"interfaces": "Ethernet14/25/1,Ethernet14/26/1", "powerGood": True},
                        }
                    },
                }
            },
        ],
        "expected": {
            "result": AntaTestStatus.FAILURE,
            "messages": [
                "Module: 3 Model: 7USAHCAK-UI-UP - Invalid status - Expected: ok Actual: notok",
                "Module: 4 Model: 7999-RUSAHCAK-UI-UP - Invalid status - Expected: ok Actual: failed",
                "Module: 2 Model: 7999-RUSAHCAK-UI - Invalid status - Expected: ok Actual: failed",
            ],
        },
    },
    (VerifyModuleStatus, "failiure-single-cardslots-state-input-not-matched"): {
        "eos_data": [
            {
                "modules": {
                    "3": {
                        "status": "ok",
                        "modelName": "7USAHCAK-UI-UP",
                    },
                    "Fabric1": {
                        "status": "poweringOn",
                        "modelName": "7USPPHCAK-UI-UP",
                    },
                    "4": {
                        "status": "failed",
                        "modelName": "7999-RUSAHCAK-UI-UP",
                    },
                    "1": {
                        "status": "active",
                        "modelName": "7999-RUSAHCAK-UI-SUP",
                    },
                    "2": {
                        "status": "failed",
                        "modelName": "7999-RUSAHCAK-UI",
                    },
                }
            },
            {
                "modules": {
                    "Linecard3": {
                        "risers": {
                            "6": {"interfaces": "Ethernet3/11/1,Ethernet3/12/1", "powerGood": True},
                            "11": {"interfaces": "Ethernet3/21/1,Ethernet3/22/1", "powerGood": True},
                        }
                    },
                    "Fabric1": {"risers": {}},
                    "Linecard14": {
                        "risers": {
                            "13": {"interfaces": "Ethernet14/25/1,Ethernet14/26/1", "powerGood": True},
                        }
                    },
                }
            },
        ],
        "inputs": {"module_statuses": ["ok", "poweringOn"]},
        "expected": {
            "result": AntaTestStatus.FAILURE,
            "messages": [
                "Module: 4 Model: 7999-RUSAHCAK-UI-UP - Invalid status - Expected: ok, poweringOn Actual: failed",
                "Module: 2 Model: 7999-RUSAHCAK-UI - Invalid status - Expected: ok, poweringOn Actual: failed",
            ],
        },
    },
    (VerifyModuleStatus, "failiure-dual-supervisor-power-unstable"): {
        "eos_data": [
            {
                "modules": {
                    "3": {
                        "status": "ok",
                        "modelName": "7999-RUSAHCAK-UI-UP",
                    },
                    "Fabric1": {
                        "status": "ok",
                        "modelName": "7999-RUSAHCAK-UI-HKUP",
                    },
                    "4": {
                        "status": "ok",
                        "modelName": "79DF99-RUSAHCAK-UI-UP",
                    },
                    "2": {
                        "status": "active",
                        "modelName": "7999-RUSAHCAK-UI-SUP",
                    },
                    "1": {
                        "status": "standby",
                        "modelName": "DJ999-RUSAHCAK-UI-SUP",
                    },
                }
            },
            {
                "modules": {
                    "Fabric6": {"risers": {}},
                    "Linecard10": {
                        "risers": {
                            "3": {"interfaces": "Ethernet10/5/1,Ethernet10/6/1", "powerGood": False},
                        }
                    },
                    "Linecard3": {
                        "risers": {
                            "6": {"interfaces": "Ethernet3/11/1,Ethernet3/12/1", "powerGood": False},
                            "13": {"interfaces": "Ethernet3/25/1,Ethernet3/26/1", "powerGood": False},
                        }
                    },
                    "Fabric1": {"risers": {}},
                    "Fabric2": {"risers": {}},
                    "Linecard14": {
                        "risers": {
                            "10": {"interfaces": "Ethernet14/19/1,Ethernet14/20/1", "powerGood": True},
                            "2": {"interfaces": "Ethernet14/3/1,Ethernet14/4/1", "powerGood": False},
                            "6": {"interfaces": "Ethernet14/11/1,Ethernet14/12/1", "powerGood": True},
                            "13": {"interfaces": "Ethernet14/25/1,Ethernet14/26/1", "powerGood": True},
                        }
                    },
                }
            },
        ],
        "inputs": {"check_dual_supervisor_system": True},
        "expected": {
            "result": AntaTestStatus.FAILURE,
            "messages": [
                "Module: Linecard10 Riser 3 - Power is not stable",
                "Module: Linecard3 Riser 6 - Power is not stable",
                "Module: Linecard3 Riser 13 - Power is not stable",
                "Module: Linecard14 Riser 2 - Power is not stable",
            ],
        },
    },
    (VerifyModuleStatus, "failiure-dual-supervisor-all"): {
        "eos_data": [
            {
                "modules": {
                    "Fabric1": {
                        "status": "notok",
                        "modelName": "7999-RUSAHCAK-UI-UP",
                    },
                    "Fabric2": {
                        "status": "failed",
                        "modelName": "7999-RUSAHCAK-UI-UP",
                    },
                    "Fabric3": {
                        "status": "poweredOff",
                        "modelName": "7999-RUSAHCAK-UI-UP",
                    },
                    "4": {
                        "status": "disabled",
                        "modelName": "7999-RUSAHCAK-UI-UP",
                    },
                    "2": {
                        "status": "active",
                        "modelName": "7999-RUSAHCAK-UI-SUP",
                    },
                    "1": {
                        "status": "standby",
                        "modelName": "7EN99-RUSAHCAK-UI-SUP",
                    },
                }
            },
            {
                "modules": {
                    "Fabric6": {"risers": {}},
                    "Linecard10": {
                        "risers": {
                            "3": {"interfaces": "Ethernet10/5/1,Ethernet10/6/1", "powerGood": True},
                        }
                    },
                    "Linecard3": {
                        "risers": {
                            "6": {"interfaces": "Ethernet3/11/1,Ethernet3/12/1", "powerGood": False},
                            "13": {"interfaces": "Ethernet3/25/1,Ethernet3/26/1", "powerGood": True},
                        }
                    },
                }
            },
        ],
        "inputs": {"check_dual_supervisor_system": True, "module_statuses": ["ok", "disabled"]},
        "expected": {
            "result": AntaTestStatus.FAILURE,
            "messages": [
                "Module: Fabric1 Model: 7999-RUSAHCAK-UI-UP - Invalid status - Expected: ok, disabled Actual: notok",
                "Module: Fabric2 Model: 7999-RUSAHCAK-UI-UP - Invalid status - Expected: ok, disabled Actual: failed",
                "Module: Fabric3 Model: 7999-RUSAHCAK-UI-UP - Invalid status - Expected: ok, disabled Actual: poweredOff",
                "Module: Linecard3 Riser 6 - Power is not stable",
            ],
        },
    },
}
