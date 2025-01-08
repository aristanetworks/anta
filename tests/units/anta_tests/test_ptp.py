# Copyright (c) 2023-2025 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Data for testing anta.tests.ptp."""

from __future__ import annotations

from typing import Any

from anta.tests.ptp import VerifyPtpGMStatus, VerifyPtpLockStatus, VerifyPtpModeStatus, VerifyPtpOffset, VerifyPtpPortModeStatus
from tests.units.anta_tests import test

DATA: list[dict[str, Any]] = [
    {
        "name": "success",
        "test": VerifyPtpModeStatus,
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
        "test": VerifyPtpModeStatus,
        "eos_data": [{"ptpMode": "ptpDisabled", "ptpIntfSummaries": {}}],
        "inputs": None,
        "expected": {"result": "failure", "messages": ["The device is not configured as a PTP Boundary Clock: 'ptpDisabled'"]},
    },
    {
        "name": "skipped",
        "test": VerifyPtpModeStatus,
        "eos_data": [{"ptpIntfSummaries": {}}],
        "inputs": None,
        "expected": {"result": "skipped", "messages": ["PTP is not configured"]},
    },
    {
        "name": "success",
        "test": VerifyPtpGMStatus,
        "eos_data": [
            {
                "ptpMode": "ptpBoundaryClock",
                "ptpProfile": "ptpDefaultProfile",
                "ptpClockSummary": {
                    "clockIdentity": "0x00:1c:73:ff:ff:14:00:01",
                    "gmClockIdentity": "0xec:46:70:ff:fe:00:ff:a8",
                    "numberOfSlavePorts": 1,
                    "numberOfMasterPorts": 8,
                    "slavePort": "Ethernet27/1",
                    "slaveVlanId": 0,
                    "offsetFromMaster": -11,
                    "meanPathDelay": 105,
                    "stepsRemoved": 2,
                    "skew": 1.0000015265007687,
                    "lastSyncTime": 1708599750,
                    "currentPtpSystemTime": 1708599750,
                },
            }
        ],
        "inputs": {"gmid": "0xec:46:70:ff:fe:00:ff:a8"},
        "expected": {"result": "success"},
    },
    {
        "name": "failure",
        "test": VerifyPtpGMStatus,
        "eos_data": [
            {
                "ptpMode": "ptpBoundaryClock",
                "ptpProfile": "ptpDefaultProfile",
                "ptpClockSummary": {
                    "clockIdentity": "0x00:1c:73:ff:ff:0a:00:01",
                    "gmClockIdentity": "0x00:1c:73:ff:ff:0a:00:01",
                    "numberOfSlavePorts": 0,
                    "numberOfMasterPorts": 4,
                    "offsetFromMaster": 3,
                    "meanPathDelay": 496,
                    "stepsRemoved": 0,
                    "skew": 1.0000074628720317,
                    "lastSyncTime": 1708600129,
                    "currentPtpSystemTime": 1708600153,
                },
            }
        ],
        "inputs": {"gmid": "0xec:46:70:ff:fe:00:ff:a8"},
        "expected": {
            "result": "failure",
            "messages": [
                "The device is locked to the following Grandmaster: '0x00:1c:73:ff:ff:0a:00:01', which differ from the expected one.",
            ],
        },
    },
    {
        "name": "skipped",
        "test": VerifyPtpGMStatus,
        "eos_data": [{"ptpIntfSummaries": {}}],
        "inputs": {"gmid": "0xec:46:70:ff:fe:00:ff:a8"},
        "expected": {"result": "skipped", "messages": ["PTP is not configured"]},
    },
    {
        "name": "success",
        "test": VerifyPtpLockStatus,
        "eos_data": [
            {
                "ptpMode": "ptpBoundaryClock",
                "ptpProfile": "ptpDefaultProfile",
                "ptpClockSummary": {
                    "clockIdentity": "0x00:1c:73:ff:ff:14:00:01",
                    "gmClockIdentity": "0xec:46:70:ff:fe:00:ff:a8",
                    "numberOfSlavePorts": 1,
                    "numberOfMasterPorts": 8,
                    "slavePort": "Ethernet27/1",
                    "slaveVlanId": 0,
                    "offsetFromMaster": -11,
                    "meanPathDelay": 105,
                    "stepsRemoved": 2,
                    "skew": 1.0000015265007687,
                    "lastSyncTime": 1708599750,
                    "currentPtpSystemTime": 1708599750,
                },
            }
        ],
        "inputs": None,
        "expected": {"result": "success"},
    },
    {
        "name": "failure",
        "test": VerifyPtpLockStatus,
        "eos_data": [
            {
                "ptpMode": "ptpBoundaryClock",
                "ptpProfile": "ptpDefaultProfile",
                "ptpClockSummary": {
                    "clockIdentity": "0x00:1c:73:ff:ff:0a:00:01",
                    "gmClockIdentity": "0x00:1c:73:ff:ff:0a:00:01",
                    "numberOfSlavePorts": 0,
                    "numberOfMasterPorts": 4,
                    "offsetFromMaster": 3,
                    "meanPathDelay": 496,
                    "stepsRemoved": 0,
                    "skew": 1.0000074628720317,
                    "lastSyncTime": 1708600129,
                    "currentPtpSystemTime": 1708600286,
                },
            }
        ],
        "inputs": None,
        "expected": {"result": "failure", "messages": ["The device lock is more than 60s old: 157s"]},
    },
    {
        "name": "skipped",
        "test": VerifyPtpLockStatus,
        "eos_data": [{"ptpIntfSummaries": {}}],
        "inputs": None,
        "expected": {
            "result": "skipped",
            "messages": [
                "PTP is not configured",
            ],
        },
    },
    {
        "name": "success",
        "test": VerifyPtpOffset,
        "eos_data": [
            {
                "monitorEnabled": True,
                "ptpMode": "ptpBoundaryClock",
                "offsetFromMasterThreshold": 250,
                "meanPathDelayThreshold": 1500,
                "ptpMonitorData": [
                    {
                        "intf": "Ethernet27/1",
                        "realLastSyncTime": 1708599815611398400,
                        "lastSyncSeqId": 44413,
                        "offsetFromMaster": 2,
                        "meanPathDelay": 105,
                        "skew": 1.000001614,
                    },
                    {
                        "intf": "Ethernet27/1",
                        "realLastSyncTime": 1708599815486101500,
                        "lastSyncSeqId": 44412,
                        "offsetFromMaster": -13,
                        "meanPathDelay": 105,
                        "skew": 1.000001614,
                    },
                ],
            }
        ],
        "inputs": None,
        "expected": {"result": "success"},
    },
    {
        "name": "failure",
        "test": VerifyPtpOffset,
        "eos_data": [
            {
                "monitorEnabled": True,
                "ptpMode": "ptpBoundaryClock",
                "offsetFromMasterThreshold": 250,
                "meanPathDelayThreshold": 1500,
                "ptpMonitorData": [
                    {
                        "intf": "Ethernet27/1",
                        "realLastSyncTime": 1708599815611398400,
                        "lastSyncSeqId": 44413,
                        "offsetFromMaster": 1200,
                        "meanPathDelay": 105,
                        "skew": 1.000001614,
                    },
                    {
                        "intf": "Ethernet27/1",
                        "realLastSyncTime": 1708599815486101500,
                        "lastSyncSeqId": 44412,
                        "offsetFromMaster": -1300,
                        "meanPathDelay": 105,
                        "skew": 1.000001614,
                    },
                ],
            }
        ],
        "inputs": None,
        "expected": {
            "result": "failure",
            "messages": [("The device timing offset from master is greater than +/- 1000ns: {'Ethernet27/1': [1200, -1300]}")],
        },
    },
    {
        "name": "skipped",
        "test": VerifyPtpOffset,
        "eos_data": [
            {
                "monitorEnabled": True,
                "ptpMonitorData": [],
            },
        ],
        "inputs": None,
        "expected": {"result": "skipped", "messages": ["PTP is not configured"]},
    },
    {
        "name": "success",
        "test": VerifyPtpPortModeStatus,
        "eos_data": [
            {
                "ptpMode": "ptpBoundaryClock",
                "ptpProfile": "ptpDefaultProfile",
                "ptpClockSummary": {
                    "clockIdentity": "0x00:1c:73:ff:ff:0a:00:01",
                    "gmClockIdentity": "0x00:1c:73:ff:ff:0a:00:01",
                    "numberOfSlavePorts": 0,
                    "numberOfMasterPorts": 4,
                    "offsetFromMaster": 0,
                    "meanPathDelay": 0,
                    "stepsRemoved": 0,
                    "skew": 1.0,
                },
                "ptpIntfSummaries": {
                    "Ethernet53": {
                        "interface": "Ethernet53",
                        "ptpIntfVlanSummaries": [
                            {
                                "vlanId": 0,
                                "portState": "psDisabled",
                                "delayMechanism": "e2e",
                                "transportMode": "ipv4",
                                "mpassEnabled": False,
                                "mpassStatus": "active",
                            }
                        ],
                    },
                    "Ethernet1": {
                        "interface": "Ethernet1",
                        "ptpIntfVlanSummaries": [
                            {"vlanId": 0, "portState": "psMaster", "delayMechanism": "e2e", "transportMode": "ipv4", "mpassEnabled": False, "mpassStatus": "active"}
                        ],
                    },
                },
            }
        ],
        "inputs": None,
        "expected": {"result": "success"},
    },
    {
        "name": "failure-no-interfaces",
        "test": VerifyPtpPortModeStatus,
        "eos_data": [{"ptpIntfSummaries": {}}],
        "inputs": None,
        "expected": {"result": "failure", "messages": ["No interfaces are PTP enabled"]},
    },
    {
        "name": "failure-invalid-state",
        "test": VerifyPtpPortModeStatus,
        "eos_data": [
            {
                "ptpMode": "ptpBoundaryClock",
                "ptpProfile": "ptpDefaultProfile",
                "ptpClockSummary": {
                    "clockIdentity": "0x00:1c:73:ff:ff:0a:00:01",
                    "gmClockIdentity": "0x00:1c:73:ff:ff:0a:00:01",
                    "numberOfSlavePorts": 0,
                    "numberOfMasterPorts": 4,
                    "offsetFromMaster": 0,
                    "meanPathDelay": 0,
                    "stepsRemoved": 0,
                    "skew": 1.0,
                },
                "ptpIntfSummaries": {
                    "Ethernet53": {
                        "interface": "Ethernet53",
                        "ptpIntfVlanSummaries": [
                            {"vlanId": 0, "portState": "none", "delayMechanism": "e2e", "transportMode": "ipv4", "mpassEnabled": False, "mpassStatus": "active"}
                        ],
                    },
                    "Ethernet1": {
                        "interface": "Ethernet1",
                        "ptpIntfVlanSummaries": [
                            {"vlanId": 0, "portState": "none", "delayMechanism": "e2e", "transportMode": "ipv4", "mpassEnabled": False, "mpassStatus": "active"}
                        ],
                    },
                },
            }
        ],
        "inputs": None,
        "expected": {"result": "failure", "messages": ["The following interface(s) are not in a valid PTP state: '['Ethernet53', 'Ethernet1']'"]},
    },
]
