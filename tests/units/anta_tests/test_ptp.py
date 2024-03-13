# Copyright (c) 2023-2024 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Data for testing anta.tests.configuration"""

from __future__ import annotations

from typing import Any

from anta.tests.ptp import PtpGMStatus, PtpLockStatus, PtpModeStatus, PtpOffset, PtpPortModeStatus

DATA: list[dict[str, Any]] = [
    {
        "name": "success",
        "test": PtpModeStatus,
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
        "test": PtpModeStatus,
        "eos_data": [{"ptpMode": "ptpDisabled", "ptpIntfSummaries": {}}],
        "inputs": None,
        "expected": {"result": "failure"},
    },
    {
        "name": "success",
        "test": PtpGMStatus,
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
        "inputs": {"validGM": "0xec:46:70:ff:fe:00:ff:a9"},
        "expected": {"result": "success"},
    },
    {
        "name": "failure",
        "test": PtpGMStatus,
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
        "inputs": {"validGM": "0xec:46:70:ff:fe:00:ff:a9"},
        "expected": {"result": "failure"},
    },
    {
        "name": "success",
        "test": PtpLockStatus,
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
        "test": PtpLockStatus,
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
        "expected": {"result": "failure"},
    },
    {
        "name": "success",
        "test": PtpOffset,
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
        "test": PtpOffset,
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
        "expected": {"result": "failure"},
    },
    {
        "name": "success",
        "test": PtpPortModeStatus,
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
        "inputs": {"validPortModes": ["psMaster", "psSlave", "psPassive", "psDisabled"]},
        "expected": {"result": "success"},
    },
    {
        "name": "failure",
        "test": PtpPortModeStatus,
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
        "inputs": {"validPortModes": ["psMaster", "psSlave", "psPassive", "psDisabled"]},
        "expected": {"result": "failure"},
    },
]
