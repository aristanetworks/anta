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

INPUT_FIELD_NOTICE_72_RESOLUTION: List[Dict[str, Any]] = [
    {
        "name": "success-JPE",
        "eos_data": [
            {
                "modelName": "DCS-7280SR3-48YC8",
                "serialNumber": "JPE2130000",
                "details": {
                    "deviations": [],
                    "components": [{"name": "FixedSystemvrm1", "version": "7"}],
                },
            }
        ],
        "side_effect": [],
        "expected_result": "success",
        "expected_messages": ["FN72 is mitigated"],
    },
    {
        "name": "success-JAS",
        "eos_data": [
            {
                "modelName": "DCS-7280SR3-48YC8",
                "serialNumber": "JAS2040000",
                "details": {
                    "deviations": [],
                    "components": [{"name": "FixedSystemvrm1", "version": "7"}],
                },
            }
        ],
        "side_effect": [],
        "expected_result": "success",
        "expected_messages": ["FN72 is mitigated"],
    },
    {
        "name": "success-K-JPE",
        "eos_data": [
            {
                "modelName": "DCS-7280SR3K-48YC8",
                "serialNumber": "JPE2133000",
                "details": {
                    "deviations": [],
                    "components": [{"name": "FixedSystemvrm1", "version": "7"}],
                },
            }
        ],
        "side_effect": [],
        "expected_result": "success",
        "expected_messages": ["FN72 is mitigated"],
    },
    {
        "name": "success-K-JAS",
        "eos_data": [
            {
                "modelName": "DCS-7280SR3K-48YC8",
                "serialNumber": "JAS2040000",
                "details": {
                    "deviations": [],
                    "components": [{"name": "FixedSystemvrm1", "version": "7"}],
                },
            }
        ],
        "side_effect": [],
        "expected_result": "success",
        "expected_messages": ["FN72 is mitigated"],
    },
    {
        "name": "skipped-Serial",
        "eos_data": [
            {
                "modelName": "DCS-7280SR3K-48YC8",
                "serialNumber": "BAN2040000",
                "details": {
                    "deviations": [],
                    "components": [{"name": "FixedSystemvrm1", "version": "7"}],
                },
            }
        ],
        "side_effect": [],
        "expected_result": "skipped",
        "expected_messages": ["Device not exposed"],
    },
    {
        "name": "skipped-Platform",
        "eos_data": [
            {
                "modelName": "DCS-7150-52-CL",
                "serialNumber": "JAS0040000",
                "details": {
                    "deviations": [],
                    "components": [{"name": "FixedSystemvrm1", "version": "5"}],
                },
            }
        ],
        "side_effect": [],
        "expected_result": "skipped",
        "expected_messages": ["Platform is not impacted by FN072"],
    },
    {
        "name": "skipped-range-JPE",
        "eos_data": [
            {
                "modelName": "DCS-7280SR3-48YC8",
                "serialNumber": "JPE2131000",
                "details": {
                    "deviations": [],
                    "components": [{"name": "FixedSystemvrm1", "version": "5"}],
                },
            }
        ],
        "side_effect": [],
        "expected_result": "skipped",
        "expected_messages": ["Device not exposed"],
    },
    {
        "name": "skipped-range-K-JAS",
        "eos_data": [
            {
                "modelName": "DCS-7280SR3K-48YC8",
                "serialNumber": "JAS2041000",
                "details": {
                    "deviations": [],
                    "components": [{"name": "FixedSystemvrm1", "version": "5"}],
                },
            }
        ],
        "side_effect": [],
        "expected_result": "skipped",
        "expected_messages": ["Device not exposed"],
    },
    {
        "name": "failed-JPE",
        "eos_data": [
            {
                "modelName": "DCS-7280SR3K-48YC8",
                "serialNumber": "JPE2133000",
                "details": {
                    "deviations": [],
                    "components": [{"name": "FixedSystemvrm1", "version": "5"}],
                },
            }
        ],
        "side_effect": [],
        "expected_result": "failure",
        "expected_messages": ["Device is exposed to FN72"],
    },
    {
        "name": "failed-JAS",
        "eos_data": [
            {
                "modelName": "DCS-7280SR3-48YC8",
                "serialNumber": "JAS2040000",
                "details": {
                    "deviations": [],
                    "components": [{"name": "FixedSystemvrm1", "version": "5"}],
                },
            }
        ],
        "side_effect": [],
        "expected_result": "failure",
        "expected_messages": ["Device is exposed to FN72"],
    },
    {
        "name": "error",
        "eos_data": [
            {
                "modelName": "DCS-7280SR3-48YC8",
                "serialNumber": "JAS2040000",
                "details": {
                    "deviations": [],
                    "components": [{"name": "FixedSystemvrm2", "version": "5"}],
                },
            }
        ],
        "side_effect": [],
        "expected_result": "error",
        "expected_messages": ["Error in running test - FixedSystemvrm1 not found"],
    },
]
