# Copyright (c) 2023-2025 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Test inputs for anta.tests.flow_tracking."""

from __future__ import annotations

import sys
from typing import TYPE_CHECKING, Any

from anta.models import AntaTest
from anta.result_manager.models import AntaTestStatus
from anta.tests.flow_tracking import VerifyHardwareFlowTrackerStatus
from tests.units.anta_tests import test

if TYPE_CHECKING:
    from tests.units.anta_tests import AntaUnitTestDataDict

DATA: AntaUnitTestDataDict = {
    (VerifyHardwareFlowTrackerStatus, "success"): {
        "eos_data": [
            {
                "trackers": {
                    "FLOW-TRACKER": {
                        "active": True,
                        "inactiveTimeout": 60000,
                        "activeInterval": 300000,
                        "exporters": {"CV-TELEMETRY": {"localIntf": "Loopback0", "templateInterval": 3600000}},
                    },
                    "HARDWARE-TRACKER": {
                        "active": True,
                        "inactiveTimeout": 60000,
                        "activeInterval": 300000,
                        "exporters": {"CV-TELEMETRY": {"localIntf": "Loopback0", "templateInterval": 3600000}},
                    },
                },
                "running": True,
            }
        ],
        "inputs": {"trackers": [{"name": "FLOW-TRACKER"}, {"name": "HARDWARE-TRACKER"}]},
        "expected": {"result": AntaTestStatus.SUCCESS},
    },
    (VerifyHardwareFlowTrackerStatus, "success-with-optional-field"): {
        "eos_data": [
            {
                "trackers": {
                    "FLOW-TRACKER": {
                        "active": True,
                        "inactiveTimeout": 60000,
                        "activeInterval": 300000,
                        "exporters": {"CV-TELEMETRY": {"localIntf": "Loopback0", "templateInterval": 3600000}},
                    },
                    "HARDWARE-TRACKER": {
                        "active": True,
                        "inactiveTimeout": 60000,
                        "activeInterval": 300000,
                        "exporters": {"CVP-TELEMETRY": {"localIntf": "Loopback10", "templateInterval": 3600000}},
                    },
                },
                "running": True,
            }
        ],
        "inputs": {
            "trackers": [
                {
                    "name": "FLOW-TRACKER",
                    "record_export": {"on_inactive_timeout": 60000, "on_interval": 300000},
                    "exporters": [{"name": "CV-TELEMETRY", "local_interface": "Loopback0", "template_interval": 3600000}],
                },
                {
                    "name": "HARDWARE-TRACKER",
                    "record_export": {"on_inactive_timeout": 60000, "on_interval": 300000},
                    "exporters": [{"name": "CVP-TELEMETRY", "local_interface": "Loopback10", "template_interval": 3600000}],
                },
            ]
        },
        "expected": {"result": AntaTestStatus.SUCCESS},
    },
    (VerifyHardwareFlowTrackerStatus, "failure-flow-tracking-not-running"): {
        "eos_data": [{"trackers": {}, "running": False}],
        "inputs": {"trackers": [{"name": "FLOW-TRACKER"}]},
        "expected": {"result": AntaTestStatus.FAILURE, "messages": ["Hardware flow tracking is not running"]},
    },
    (VerifyHardwareFlowTrackerStatus, "failure-tracker-not-configured"): {
        "eos_data": [
            {
                "trackers": {
                    "HARDWARE-TRACKER": {
                        "active": True,
                        "inactiveTimeout": 60000,
                        "activeInterval": 300000,
                        "exporters": {"CVP-TELEMETRY": {"localIntf": "Loopback10", "templateInterval": 3600000}},
                    }
                },
                "running": True,
            }
        ],
        "inputs": {"trackers": [{"name": "FLOW-Sample"}]},
        "expected": {"result": AntaTestStatus.FAILURE, "messages": ["Flow Tracker: FLOW-Sample - Not found"]},
    },
    (VerifyHardwareFlowTrackerStatus, "failure-tracker-not-active"): {
        "eos_data": [
            {
                "trackers": {
                    "FLOW-TRACKER": {
                        "active": False,
                        "inactiveTimeout": 60000,
                        "activeInterval": 300000,
                        "exporters": {"CV-TELEMETRY": {"localIntf": "Loopback0", "templateInterval": 3600000}},
                    },
                    "HARDWARE-TRACKER": {
                        "active": False,
                        "inactiveTimeout": 60000,
                        "activeInterval": 300000,
                        "exporters": {"CVP-TELEMETRY": {"localIntf": "Loopback10", "templateInterval": 3600000}},
                    },
                },
                "running": True,
            }
        ],
        "inputs": {
            "trackers": [
                {
                    "name": "FLOW-TRACKER",
                    "record_export": {"on_inactive_timeout": 60000, "on_interval": 300000},
                    "exporters": [{"name": "CV-TELEMETRY", "local_interface": "Loopback0", "template_interval": 3600000}],
                },
                {
                    "name": "HARDWARE-TRACKER",
                    "record_export": {"on_inactive_timeout": 60000, "on_interval": 300000},
                    "exporters": [{"name": "CVP-TELEMETRY", "local_interface": "Loopback10", "template_interval": 3600000}],
                },
            ]
        },
        "expected": {"result": AntaTestStatus.FAILURE, "messages": ["Flow Tracker: FLOW-TRACKER - Disabled", "Flow Tracker: HARDWARE-TRACKER - Disabled"]},
    },
    (VerifyHardwareFlowTrackerStatus, "failure-incorrect-record-export"): {
        "eos_data": [
            {
                "trackers": {
                    "FLOW-TRACKER": {
                        "active": True,
                        "inactiveTimeout": 60000,
                        "activeInterval": 300000,
                        "exporters": {"CV-TELEMETRY": {"localIntf": "Loopback0", "templateInterval": 3600000}},
                    },
                    "HARDWARE-TRACKER": {
                        "active": True,
                        "inactiveTimeout": 6000,
                        "activeInterval": 30000,
                        "exporters": {"CVP-TELEMETRY": {"localIntf": "Loopback10", "templateInterval": 3600000}},
                    },
                },
                "running": True,
            }
        ],
        "inputs": {
            "trackers": [
                {"name": "FLOW-TRACKER", "record_export": {"on_inactive_timeout": 6000, "on_interval": 30000}},
                {"name": "HARDWARE-TRACKER", "record_export": {"on_inactive_timeout": 60000, "on_interval": 300000}},
            ]
        },
        "expected": {
            "result": AntaTestStatus.FAILURE,
            "messages": [
                "Flow Tracker: FLOW-TRACKER Inactive Timeout: 6000 Active Interval: 30000 - Incorrect timers - Inactive Timeout: 60000 OnActive Interval: 300000",
                "Flow Tracker: HARDWARE-TRACKER Inactive Timeout: 60000 Active Interval: 300000 - Incorrect timers - "
                "Inactive Timeout: 6000 OnActive Interval: 30000",
            ],
        },
    },
    (VerifyHardwareFlowTrackerStatus, "failure-incorrect-exporters"): {
        "eos_data": [
            {
                "trackers": {
                    "FLOW-TRACKER": {
                        "active": True,
                        "inactiveTimeout": 60000,
                        "activeInterval": 300000,
                        "exporters": {
                            "CV-TELEMETRY": {"localIntf": "Loopback0", "templateInterval": 3600000},
                            "CVP-FLOW": {"localIntf": "Loopback0", "templateInterval": 3600000},
                        },
                    },
                    "HARDWARE-TRACKER": {
                        "active": True,
                        "inactiveTimeout": 6000,
                        "activeInterval": 30000,
                        "exporters": {
                            "CVP-TELEMETRY": {"localIntf": "Loopback10", "templateInterval": 3600000},
                            "Hardware-flow": {"localIntf": "Loopback10", "templateInterval": 3600000},
                        },
                    },
                },
                "running": True,
            }
        ],
        "inputs": {
            "trackers": [
                {
                    "name": "FLOW-TRACKER",
                    "exporters": [
                        {"name": "CV-TELEMETRY", "local_interface": "Loopback0", "template_interval": 3600000},
                        {"name": "CVP-FLOW", "local_interface": "Loopback10", "template_interval": 3500000},
                    ],
                },
                {
                    "name": "HARDWARE-TRACKER",
                    "exporters": [
                        {"name": "Hardware-flow", "local_interface": "Loopback99", "template_interval": 3000000},
                        {"name": "Reverse-flow", "local_interface": "Loopback101", "template_interval": 3000000},
                    ],
                },
            ]
        },
        "expected": {
            "result": AntaTestStatus.FAILURE,
            "messages": [
                "Flow Tracker: FLOW-TRACKER Exporter: CVP-FLOW - Incorrect local interface - Expected: Loopback10 Actual: Loopback0",
                "Flow Tracker: FLOW-TRACKER Exporter: CVP-FLOW - Incorrect template interval - Expected: 3500000 Actual: 3600000",
                "Flow Tracker: HARDWARE-TRACKER Exporter: Hardware-flow - Incorrect local interface - Expected: Loopback99 Actual: Loopback10",
                "Flow Tracker: HARDWARE-TRACKER Exporter: Hardware-flow - Incorrect template interval - Expected: 3000000 Actual: 3600000",
                "Flow Tracker: HARDWARE-TRACKER Exporter: Reverse-flow - Not configured",
            ],
        },
    },
    (VerifyHardwareFlowTrackerStatus, "failure-all-type"): {
        "eos_data": [
            {
                "trackers": {
                    "HARDWARE-TRACKER": {
                        "active": True,
                        "inactiveTimeout": 60000,
                        "activeInterval": 300000,
                        "exporters": {"CVP-TELEMETRY": {"localIntf": "Loopback10", "templateInterval": 3600000}},
                    },
                    "FLOW-TRIGGER": {
                        "active": False,
                        "inactiveTimeout": 60000,
                        "activeInterval": 300000,
                        "exporters": {"CV-TELEMETRY": {"localIntf": "Loopback0", "templateInterval": 3600000}},
                    },
                    "HARDWARE-FLOW": {
                        "active": True,
                        "inactiveTimeout": 6000,
                        "activeInterval": 30000,
                        "exporters": {"CVP-TELEMETRY": {"localIntf": "Loopback10", "templateInterval": 3600000}},
                    },
                    "FLOW-TRACKER2": {
                        "active": True,
                        "inactiveTimeout": 60000,
                        "activeInterval": 300000,
                        "exporters": {
                            "CV-TELEMETRY": {"localIntf": "Loopback0", "templateInterval": 3600000},
                            "CVP-FLOW": {"localIntf": "Loopback0", "templateInterval": 3600000},
                        },
                    },
                    "HARDWARE-TRACKER2": {
                        "active": True,
                        "inactiveTimeout": 6000,
                        "activeInterval": 30000,
                        "exporters": {
                            "CVP-TELEMETRY": {"localIntf": "Loopback10", "templateInterval": 3600000},
                            "Hardware-flow": {"localIntf": "Loopback10", "templateInterval": 3600000},
                        },
                    },
                },
                "running": True,
            }
        ],
        "inputs": {
            "trackers": [
                {"name": "FLOW-Sample"},
                {
                    "name": "FLOW-TRIGGER",
                    "record_export": {"on_inactive_timeout": 60000, "on_interval": 300000},
                    "exporters": [{"name": "CV-TELEMETRY", "local_interface": "Loopback0", "template_interval": 3600000}],
                },
                {"name": "HARDWARE-FLOW", "record_export": {"on_inactive_timeout": 60000, "on_interval": 300000}},
                {
                    "name": "FLOW-TRACKER2",
                    "exporters": [
                        {"name": "CV-TELEMETRY", "local_interface": "Loopback0", "template_interval": 3600000},
                        {"name": "CVP-FLOW", "local_interface": "Loopback10", "template_interval": 3500000},
                    ],
                },
                {
                    "name": "HARDWARE-TRACKER2",
                    "exporters": [
                        {"name": "Hardware-flow", "local_interface": "Loopback99", "template_interval": 3000000},
                        {"name": "Reverse-flow", "local_interface": "Loopback101", "template_interval": 3000000},
                    ],
                },
            ]
        },
        "expected": {
            "result": AntaTestStatus.FAILURE,
            "messages": [
                "Flow Tracker: FLOW-Sample - Not found",
                "Flow Tracker: FLOW-TRIGGER - Disabled",
                "Flow Tracker: HARDWARE-FLOW Inactive Timeout: 60000 Active Interval: 300000 - Incorrect timers - Inactive Timeout: 6000 OnActive Interval: 30000",
                "Flow Tracker: FLOW-TRACKER2 Exporter: CVP-FLOW - Incorrect local interface - Expected: Loopback10 Actual: Loopback0",
                "Flow Tracker: FLOW-TRACKER2 Exporter: CVP-FLOW - Incorrect template interval - Expected: 3500000 Actual: 3600000",
                "Flow Tracker: HARDWARE-TRACKER2 Exporter: Hardware-flow - Incorrect local interface - Expected: Loopback99 Actual: Loopback10",
                "Flow Tracker: HARDWARE-TRACKER2 Exporter: Hardware-flow - Incorrect template interval - Expected: 3000000 Actual: 3600000",
                "Flow Tracker: HARDWARE-TRACKER2 Exporter: Reverse-flow - Not configured",
            ],
        },
    },
}
