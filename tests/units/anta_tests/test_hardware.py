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
    VerifyAdverseDrops,
    VerifyEnvironmentCooling,
    VerifyEnvironmentPower,
    VerifyEnvironmentSystemCooling,
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
                "Sensor: TempSensor1 Description: Cpu temp sensor - Temperature is getting high - Current: 93.85271955304604 Overheat Threshold: 90.0",
                "Sensor: TempSensor2 Description: Switch card temp sensor - Temperature is getting high - Current: 74.875 Overheat Threshold: 75.0",
            ],
        },
    },
    (VerifyTemperature, "failure-status-high-temp"): {
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
        "expected": {
            "result": AntaTestStatus.FAILURE,
            "messages": ["Device temperature exceeds acceptable limits - Expected: temperatureOk Actual: temperatureCritical"],
        },
    },
    (VerifyTemperature, "failure-status"): {
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
                "Sensor: TempSensorP1/1 Description: Hotspot - Temperature is getting high - Current: 54.0 Overheat Threshold: 55.0",
                "Sensor: TempSensorP1/2 Description: Inlet - Invalid hardware status - Expected: ok Actual: failed",
                "Sensor: TempSensorP2/2 Description: Inlet - Temperature is getting high - Current: 59.0 Overheat Threshold: 60.0",
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
}
