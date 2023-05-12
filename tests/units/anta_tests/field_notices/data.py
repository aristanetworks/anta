"""Test inputs for anta.tests.field_notices"""

from typing import Any, Dict, List


INPUT_FIELD_NOTICE_44_RESOLUTION: List[Dict[str, Any]] = [
    {
        "name": "success",
        "eos_data": [
            {
                "imageFormatVersion": "1.0",
                "uptime": 1109144.35,
                "modelName": "DCS-7280QRA-C36S",
                "details": {
                    "deviations": [],
                    "components": [{"name": "Aboot", "version": "Aboot-veos-8.0.0-3255441"}],
                },
            }
        ],
        "side_effect": [],
        "expected_result": "success",
        "expected_messages": [],
    },
    {
        "name": "failure-4.0",
        "eos_data": [
            {
                "imageFormatVersion": "1.0",
                "uptime": 1109144.35,
                "modelName": "DCS-7280QRA-C36S",
                "details": {
                    "deviations": [],
                    "components": [{"name": "Aboot", "version": "Aboot-veos-4.0.1-3255441"}],
                },
            }
        ],
        "side_effect": [],
        "expected_result": "failure",
        "expected_messages": ["device is running incorrect version of aboot (4.0.1)"],
    },
    {
        "name": "failure-4.1",
        "eos_data": [
            {
                "imageFormatVersion": "1.0",
                "uptime": 1109144.35,
                "modelName": "DCS-7280QRA-C36S",
                "details": {
                    "deviations": [],
                    "components": [{"name": "Aboot", "version": "Aboot-veos-4.1.0-3255441"}],
                },
            }
        ],
        "side_effect": [],
        "expected_result": "failure",
        "expected_messages": ["device is running incorrect version of aboot (4.1.0)"],
    },
    {
        "name": "failure-6.0",
        "eos_data": [
            {
                "imageFormatVersion": "1.0",
                "uptime": 1109144.35,
                "modelName": "DCS-7280QRA-C36S",
                "details": {
                    "deviations": [],
                    "components": [{"name": "Aboot", "version": "Aboot-veos-6.0.1-3255441"}],
                },
            }
        ],
        "side_effect": [],
        "expected_result": "failure",
        "expected_messages": ["device is running incorrect version of aboot (6.0.1)"],
    },
    {
        "name": "failure-6.1",
        "eos_data": [
            {
                "imageFormatVersion": "1.0",
                "uptime": 1109144.35,
                "modelName": "DCS-7280QRA-C36S",
                "details": {
                    "deviations": [],
                    "components": [{"name": "Aboot", "version": "Aboot-veos-6.1.1-3255441"}],
                },
            }
        ],
        "side_effect": [],
        "expected_result": "failure",
        "expected_messages": ["device is running incorrect version of aboot (6.1.1)"],
    },
    {
        "name": "skipped-model",
        "eos_data": [
            {
                "imageFormatVersion": "1.0",
                "uptime": 1109144.35,
                "modelName": "vEOS-lab",
                "details": {
                    "deviations": [],
                    "components": [{"name": "Aboot", "version": "Aboot-veos-8.0.0-3255441"}],
                },
            }
        ],
        "side_effect": [],
        "expected_result": "skipped",
        "expected_messages": ["device is not impacted by FN044"],
    },
]
