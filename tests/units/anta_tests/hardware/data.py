"""Test inputs for anta.tests.hardware"""

from typing import Any, Dict, List

INPUT_MANUFACTURER: List[Dict[str, Any]] = [
    {
        'name': 'success',
        'eos_data': [
            {
                "xcvrSlots": {
                    "1": {
                        "mfgName": "Arista Networks",
                        "modelName": "QSFP-100G-DR",
                        "serialNum": "XKT203501340",
                        "hardwareRev": "21"
                    },
                    "2": {
                        "mfgName": "Arista Networks",
                        "modelName": "QSFP-100G-DR",
                        "serialNum": "XKT203501337",
                        "hardwareRev": "21"
                    }
                }
            }
        ],
        'side_effect': ['Arista Networks'],
        'expected_result': 'success',
        'expected_messages': []
    },
    {
        "name": "failure",
        'eos_data': [
            {
                "xcvrSlots": {
                    "1": {
                        "mfgName": "Arista Networks",
                        "modelName": "QSFP-100G-DR",
                        "serialNum": "XKT203501340",
                        "hardwareRev": "21"
                    },
                    "2": {
                        "mfgName": "Arista Networks",
                        "modelName": "QSFP-100G-DR",
                        "serialNum": "XKT203501337",
                        "hardwareRev": "21"
                    }
                }
            }
        ],
        'side_effect': ['Arista'],
        'expected_result': 'failure',
        'expected_messages': ['The following interfaces have transceivers from unauthorized manufacturers', "{'1': 'Arista Networks', '2': 'Arista Networks'}"]
    },
]


INPUT_TEMPERATURE: List[Dict[str, Any]] = [
    {
        "name": "success",
        "eos_data": [
            {
                "powercycleOnOverheat": "False",
                "ambientThreshold": 45,
                "cardSlots": [],
                "shutdownOnOverheat": "True",
                "systemStatus": "temperatureOk",
                "recoveryModeOnOverheat": "recoveryModeNA"
            }
        ],
        "side_effect": "",
        "expected_result": "success",
        "expected_messages": []
    },
    {
        "name": "failure",
        "eos_data": [
            {
                "powercycleOnOverheat": "False",
                "ambientThreshold": 45,
                "cardSlots": [],
                "shutdownOnOverheat": "True",
                "systemStatus": "temperatureKO",
                "recoveryModeOnOverheat": "recoveryModeNA"
            }
        ],
        "side_effect": "",
        "expected_result": "failure",
        "expected_messages": []
    },
]

INPUT_TEMPERATURE_TRANSCEIVER: List[Dict[str, Any]] = [
    {
        "name": "success",
        "eos_data": [
            {
                'tempSensors': [
                    {
                        'maxTemperature': 25.03125,
                        'maxTemperatureLastChange': 1682509618.2227979,
                        'hwStatus': 'ok',
                        'alertCount': 0,
                        'description': 'Xcvr54 temp sensor',
                        'overheatThreshold': 70.0,
                        'criticalThreshold': 70.0,
                        'inAlertState': False,
                        'targetTemperature': 62.0,
                        'relPos': '54',
                        'currentTemperature': 24.171875,
                        'setPointTemperature': 61.8,
                        'pidDriverCount': 0,
                        'isPidDriver': False,
                        'name': 'DomTemperatureSensor54'
                    }
                ],
                'cardSlots': []
            }
        ],
        "side_effect": "",
        "expected_result": "success",
        "expected_messages": []
    },
    {
        "name": "failure-hwStatus",
        "eos_data": [
            {
                'tempSensors': [
                    {
                        'maxTemperature': 25.03125,
                        'maxTemperatureLastChange': 1682509618.2227979,
                        'hwStatus': 'ko',
                        'alertCount': 0,
                        'description': 'Xcvr54 temp sensor',
                        'overheatThreshold': 70.0,
                        'criticalThreshold': 70.0,
                        'inAlertState': False,
                        'targetTemperature': 62.0,
                        'relPos': '54',
                        'currentTemperature': 24.171875,
                        'setPointTemperature': 61.8,
                        'pidDriverCount': 0,
                        'isPidDriver': False,
                        'name': 'DomTemperatureSensor54'
                    }
                ],
                'cardSlots': []
            }
        ],
        "side_effect": "",
        "expected_result": "failure",
        "expected_messages": []
    },
    {
        "name": "failure-alertCount",
        "eos_data": [
            {
                'tempSensors': [
                    {
                        'maxTemperature': 25.03125,
                        'maxTemperatureLastChange': 1682509618.2227979,
                        'hwStatus': 'ok',
                        'alertCount': 1,
                        'description': 'Xcvr54 temp sensor',
                        'overheatThreshold': 70.0,
                        'criticalThreshold': 70.0,
                        'inAlertState': False,
                        'targetTemperature': 62.0,
                        'relPos': '54',
                        'currentTemperature': 24.171875,
                        'setPointTemperature': 61.8,
                        'pidDriverCount': 0,
                        'isPidDriver': False,
                        'name': 'DomTemperatureSensor54'
                    }
                ],
                'cardSlots': []
            }
        ],
        "side_effect": "",
        "expected_result": "failure",
        "expected_messages": []
    },
]
