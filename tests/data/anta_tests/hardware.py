"""Test inputs for anta.tests.hardware"""

INPUT_MANUFACTURER = [
    {
        "name": "success",
        "eos_data": [
            {
                "xcvrSlots": {
                    "1": {"mfgName": "Arista Networks", "modelName": "QSFP-100G-DR", "serialNum": "XKT203501340", "hardwareRev": "21"},
                    "2": {"mfgName": "Arista Networks", "modelName": "QSFP-100G-DR", "serialNum": "XKT203501337", "hardwareRev": "21"},
                }
            }
        ],
        "side_effect": ["Arista Networks"],
        "expected_result": "success",
        "expected_message": [],
    },
    {
        "name": "failure",
        "eos_data": [
            {
                "xcvrSlots": {
                    "1": {"mfgName": "Arista Networks", "modelName": "QSFP-100G-DR", "serialNum": "XKT203501340", "hardwareRev": "21"},
                    "2": {"mfgName": "Arista Networks", "modelName": "QSFP-100G-DR", "serialNum": "XKT203501337", "hardwareRev": "21"},
                }
            }
        ],
        "side_effect": ["Arista"],
        "expected_result": "failure",
        "expected_message": ["The following interfaces have transceivers from unauthorized manufacturers", "{'1': 'Arista Networks', '2': 'Arista Networks'}"],
    },
]
