# Copyright (c) 2023-2024 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Data for testing anta.tests.configuration"""
from __future__ import annotations

from typing import Any

from anta.tests.ptp import VerifyPtpStatus

DATA: list[dict[str, Any]] = [
    {
        "name": "success",
        "test": VerifyPtpStatus,
        "eos_data": [
            {
                "ptpMode": "ptpBoundaryClock",
                "ptpProfile": "ptpDefaultProfile",
                "ptpClockSummary": {
                    "clockIdentity": "0xcc:1a:a3:ff:ff:c3:bf:eb",
                    "gmClockIdentity": "0x00:00:00:00:00:00:00:00",
                    "numberOfSlavePorts": 0,
                    "numberOfMasterPorts": 0,
                    "offsetFromMaster": 0,
                    "meanPathDelay": 0,
                    "stepsRemoved": 0,
                    "skew": 1.0,
                },
                "ptpIntfSummaries": {},
            }
        ],
        "inputs": None,
        "expected": {"result": "success"},
    },
    {
        "name": "failure",
        "test": VerifyPtpStatus,
        "eos_data": [{"ptpIntfSummaries": {}}],
        "inputs": None,
        "expected": {"result": "failure"},
    },
]
