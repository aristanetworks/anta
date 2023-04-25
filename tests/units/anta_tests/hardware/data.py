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
