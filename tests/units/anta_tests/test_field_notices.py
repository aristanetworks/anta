# Copyright (c) 2023-2025 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Test inputs for anta.tests.field_notices."""

from __future__ import annotations

from typing import Any

from anta.tests.field_notices import VerifyFieldNotice44Resolution, VerifyFieldNotice72Resolution
from tests.units.anta_tests import test

DATA: list[dict[str, Any]] = [
    {
        "name": "success",
        "test": VerifyFieldNotice44Resolution,
        "eos_data": [
            {
                "imageFormatVersion": "1.0",
                "uptime": 1109144.35,
                "modelName": "DCS-7280QRA-C36S",
                "details": {
                    "deviations": [],
                    "components": [{"name": "Aboot", "version": "Aboot-veos-8.0.0-3255441"}, {"name": "NotAboot", "version": "Aboot-veos-8.0.0-3255441"}],
                },
            },
        ],
        "inputs": None,
        "expected": {"result": "success"},
    },
    {
        "name": "failure-4.0",
        "test": VerifyFieldNotice44Resolution,
        "eos_data": [
            {
                "imageFormatVersion": "1.0",
                "uptime": 1109144.35,
                "modelName": "DCS-7280QRA-C36S",
                "details": {
                    "deviations": [],
                    "components": [{"name": "Aboot", "version": "Aboot-veos-4.0.1-3255441"}],
                },
            },
        ],
        "inputs": None,
        "expected": {
            "result": "failure",
            "messages": ["device is running incorrect version of aboot (4.0.1)"],
        },
    },
    {
        "name": "failure-4.1",
        "test": VerifyFieldNotice44Resolution,
        "eos_data": [
            {
                "imageFormatVersion": "1.0",
                "uptime": 1109144.35,
                "modelName": "DCS-7280QRA-C36S",
                "details": {
                    "deviations": [],
                    "components": [{"name": "Aboot", "version": "Aboot-veos-4.1.0-3255441"}],
                },
            },
        ],
        "inputs": None,
        "expected": {
            "result": "failure",
            "messages": ["device is running incorrect version of aboot (4.1.0)"],
        },
    },
    {
        "name": "failure-6.0",
        "test": VerifyFieldNotice44Resolution,
        "eos_data": [
            {
                "imageFormatVersion": "1.0",
                "uptime": 1109144.35,
                "modelName": "DCS-7280QRA-C36S",
                "details": {
                    "deviations": [],
                    "components": [{"name": "Aboot", "version": "Aboot-veos-6.0.1-3255441"}],
                },
            },
        ],
        "inputs": None,
        "expected": {
            "result": "failure",
            "messages": ["device is running incorrect version of aboot (6.0.1)"],
        },
    },
    {
        "name": "failure-6.1",
        "test": VerifyFieldNotice44Resolution,
        "eos_data": [
            {
                "imageFormatVersion": "1.0",
                "uptime": 1109144.35,
                "modelName": "DCS-7280QRA-C36S",
                "details": {
                    "deviations": [],
                    "components": [{"name": "Aboot", "version": "Aboot-veos-6.1.1-3255441"}],
                },
            },
        ],
        "inputs": None,
        "expected": {
            "result": "failure",
            "messages": ["device is running incorrect version of aboot (6.1.1)"],
        },
    },
    {
        "name": "skipped-model",
        "test": VerifyFieldNotice44Resolution,
        "eos_data": [
            {
                "imageFormatVersion": "1.0",
                "uptime": 1109144.35,
                "modelName": "vEOS-lab",
                "details": {
                    "deviations": [],
                    "components": [{"name": "Aboot", "version": "Aboot-veos-8.0.0-3255441"}],
                },
            },
        ],
        "inputs": None,
        "expected": {
            "result": "skipped",
            "messages": ["device is not impacted by FN044"],
        },
    },
    {
        "name": "failure-no-aboot-component",
        "test": VerifyFieldNotice44Resolution,
        "eos_data": [
            {
                "imageFormatVersion": "1.0",
                "uptime": 1109144.35,
                "modelName": "DCS-7280QRA-C36S",
                "details": {
                    "deviations": [],
                    "components": [{"name": "NotAboot", "version": "Aboot-veos-4.0.1-3255441"}],
                },
            },
        ],
        "inputs": None,
        "expected": {
            "result": "failure",
            "messages": ["Aboot component not found"],
        },
    },
    {
        "name": "success-JPE",
        "test": VerifyFieldNotice72Resolution,
        "eos_data": [
            {
                "modelName": "DCS-7280SR3-48YC8",
                "serialNumber": "JPE2130000",
                "details": {
                    "deviations": [],
                    "components": [{"name": "FixedSystemvrm1", "version": "7"}],
                },
            },
        ],
        "inputs": None,
        "expected": {"result": "success", "messages": ["FN72 is mitigated"]},
    },
    {
        "name": "success-JAS",
        "test": VerifyFieldNotice72Resolution,
        "eos_data": [
            {
                "modelName": "DCS-7280SR3-48YC8",
                "serialNumber": "JAS2040000",
                "details": {
                    "deviations": [],
                    "components": [{"name": "FixedSystemvrm1", "version": "7"}],
                },
            },
        ],
        "inputs": None,
        "expected": {"result": "success", "messages": ["FN72 is mitigated"]},
    },
    {
        "name": "success-K-JPE",
        "test": VerifyFieldNotice72Resolution,
        "eos_data": [
            {
                "modelName": "DCS-7280SR3K-48YC8",
                "serialNumber": "JPE2133000",
                "details": {
                    "deviations": [],
                    "components": [{"name": "FixedSystemvrm1", "version": "7"}],
                },
            },
        ],
        "inputs": None,
        "expected": {"result": "success", "messages": ["FN72 is mitigated"]},
    },
    {
        "name": "success-K-JAS",
        "test": VerifyFieldNotice72Resolution,
        "eos_data": [
            {
                "modelName": "DCS-7280SR3K-48YC8",
                "serialNumber": "JAS2040000",
                "details": {
                    "deviations": [],
                    "components": [{"name": "FixedSystemvrm1", "version": "7"}],
                },
            },
        ],
        "inputs": None,
        "expected": {"result": "success", "messages": ["FN72 is mitigated"]},
    },
    {
        "name": "skipped-Serial",
        "test": VerifyFieldNotice72Resolution,
        "eos_data": [
            {
                "modelName": "DCS-7280SR3K-48YC8",
                "serialNumber": "BAN2040000",
                "details": {
                    "deviations": [],
                    "components": [{"name": "FixedSystemvrm1", "version": "7"}],
                },
            },
        ],
        "inputs": None,
        "expected": {"result": "skipped", "messages": ["Device not exposed"]},
    },
    {
        "name": "skipped-Platform",
        "test": VerifyFieldNotice72Resolution,
        "eos_data": [
            {
                "modelName": "DCS-7150-52-CL",
                "serialNumber": "JAS0040000",
                "details": {
                    "deviations": [],
                    "components": [{"name": "FixedSystemvrm1", "version": "5"}],
                },
            },
        ],
        "inputs": None,
        "expected": {
            "result": "skipped",
            "messages": ["Platform is not impacted by FN072"],
        },
    },
    {
        "name": "skipped-range-JPE",
        "test": VerifyFieldNotice72Resolution,
        "eos_data": [
            {
                "modelName": "DCS-7280SR3-48YC8",
                "serialNumber": "JPE2131000",
                "details": {
                    "deviations": [],
                    "components": [{"name": "FixedSystemvrm1", "version": "5"}],
                },
            },
        ],
        "inputs": None,
        "expected": {"result": "skipped", "messages": ["Device not exposed"]},
    },
    {
        "name": "skipped-range-K-JPE",
        "test": VerifyFieldNotice72Resolution,
        "eos_data": [
            {
                "modelName": "DCS-7280SR3K-48YC8",
                "serialNumber": "JPE2134000",
                "details": {
                    "deviations": [],
                    "components": [{"name": "FixedSystemvrm1", "version": "5"}],
                },
            },
        ],
        "inputs": None,
        "expected": {"result": "skipped", "messages": ["Device not exposed"]},
    },
    {
        "name": "skipped-range-JAS",
        "test": VerifyFieldNotice72Resolution,
        "eos_data": [
            {
                "modelName": "DCS-7280SR3-48YC8",
                "serialNumber": "JAS2041000",
                "details": {
                    "deviations": [],
                    "components": [{"name": "FixedSystemvrm1", "version": "5"}],
                },
            },
        ],
        "inputs": None,
        "expected": {"result": "skipped", "messages": ["Device not exposed"]},
    },
    {
        "name": "skipped-range-K-JAS",
        "test": VerifyFieldNotice72Resolution,
        "eos_data": [
            {
                "modelName": "DCS-7280SR3K-48YC8",
                "serialNumber": "JAS2041000",
                "details": {
                    "deviations": [],
                    "components": [{"name": "FixedSystemvrm1", "version": "5"}],
                },
            },
        ],
        "inputs": None,
        "expected": {"result": "skipped", "messages": ["Device not exposed"]},
    },
    {
        "name": "failed-JPE",
        "test": VerifyFieldNotice72Resolution,
        "eos_data": [
            {
                "modelName": "DCS-7280SR3K-48YC8",
                "serialNumber": "JPE2133000",
                "details": {
                    "deviations": [],
                    "components": [{"name": "FixedSystemvrm1", "version": "5"}],
                },
            },
        ],
        "inputs": None,
        "expected": {"result": "failure", "messages": ["Device is exposed to FN72"]},
    },
    {
        "name": "failed-JAS",
        "test": VerifyFieldNotice72Resolution,
        "eos_data": [
            {
                "modelName": "DCS-7280SR3-48YC8",
                "serialNumber": "JAS2040000",
                "details": {
                    "deviations": [],
                    "components": [{"name": "FixedSystemvrm1", "version": "5"}],
                },
            },
        ],
        "inputs": None,
        "expected": {"result": "failure", "messages": ["Device is exposed to FN72"]},
    },
    {
        "name": "error",
        "test": VerifyFieldNotice72Resolution,
        "eos_data": [
            {
                "modelName": "DCS-7280SR3-48YC8",
                "serialNumber": "JAS2040000",
                "details": {
                    "deviations": [],
                    "components": [{"name": "FixedSystemvrm2", "version": "5"}],
                },
            },
        ],
        "inputs": None,
        "expected": {
            "result": "failure",
            "messages": ["Error in running test - Component FixedSystemvrm1 not found in 'show version'"],
        },
    },
]
