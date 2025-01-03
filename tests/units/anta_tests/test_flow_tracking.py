# Copyright (c) 2023-2025 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Test inputs for anta.tests.flow_tracking."""

from __future__ import annotations

from typing import TYPE_CHECKING

from anta.tests.flow_tracking import VerifyHardwareFlowTrackerStatus
from tests.units.anta_tests import test

if TYPE_CHECKING:
    from tests.units.anta_tests import AntaUnitTest

DATA: list[AntaUnitTest] = [
    {
        "name": "success",
        "test": VerifyHardwareFlowTrackerStatus,
        "eos_data": [
            {
                "trackers": {
                    "FLOW-TRACKER": {
                        "active": True,
                        "inactiveTimeout": 60000,
                        "activeInterval": 300000,
                        "exporters": {"CV-TELEMETRY": {"localIntf": "Loopback0", "templateInterval": 3600000}},
                    }
                },
                "running": True,
            },
            {
                "trackers": {
                    "HARDWARE-TRACKER": {
                        "active": True,
                        "inactiveTimeout": 60000,
                        "activeInterval": 300000,
                        "exporters": {"CV-TELEMETRY": {"localIntf": "Loopback0", "templateInterval": 3600000}},
                    }
                },
                "running": True,
            },
        ],
        "inputs": {"trackers": [{"name": "FLOW-TRACKER"}, {"name": "HARDWARE-TRACKER"}]},
        "expected": {"result": "success"},
    },
    {
        "name": "success-with-optional-field",
        "test": VerifyHardwareFlowTrackerStatus,
        "eos_data": [
            {
                "trackers": {
                    "FLOW-TRACKER": {
                        "active": True,
                        "inactiveTimeout": 60000,
                        "activeInterval": 300000,
                        "exporters": {"CV-TELEMETRY": {"localIntf": "Loopback0", "templateInterval": 3600000}},
                    }
                },
                "running": True,
            },
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
            },
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
        "expected": {"result": "success"},
    },
    {
        "name": "failure-flow-tracking-not-running",
        "test": VerifyHardwareFlowTrackerStatus,
        "eos_data": [{"trackers": {}, "running": False}],
        "inputs": {"trackers": [{"name": "FLOW-TRACKER"}]},
        "expected": {
            "result": "failure",
            "messages": ["Hardware flow tracking is not running."],
        },
    },
    {
        "name": "failure-tracker-not-configured",
        "test": VerifyHardwareFlowTrackerStatus,
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
        "expected": {
            "result": "failure",
            "messages": ["Hardware flow tracker `FLOW-Sample` is not configured."],
        },
    },
    {
        "name": "failure-tracker-not-active",
        "test": VerifyHardwareFlowTrackerStatus,
        "eos_data": [
            {
                "trackers": {
                    "FLOW-TRACKER": {
                        "active": False,
                        "inactiveTimeout": 60000,
                        "activeInterval": 300000,
                        "exporters": {"CV-TELEMETRY": {"localIntf": "Loopback0", "templateInterval": 3600000}},
                    }
                },
                "running": True,
            },
            {
                "trackers": {
                    "HARDWARE-TRACKER": {
                        "active": False,
                        "inactiveTimeout": 60000,
                        "activeInterval": 300000,
                        "exporters": {"CVP-TELEMETRY": {"localIntf": "Loopback10", "templateInterval": 3600000}},
                    }
                },
                "running": True,
            },
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
        "expected": {
            "result": "failure",
            "messages": ["Hardware flow tracker `FLOW-TRACKER` is not active.", "Hardware flow tracker `HARDWARE-TRACKER` is not active."],
        },
    },
    {
        "name": "failure-incorrect-record-export",
        "test": VerifyHardwareFlowTrackerStatus,
        "eos_data": [
            {
                "trackers": {
                    "FLOW-TRACKER": {
                        "active": True,
                        "inactiveTimeout": 60000,
                        "activeInterval": 300000,
                        "exporters": {"CV-TELEMETRY": {"localIntf": "Loopback0", "templateInterval": 3600000}},
                    }
                },
                "running": True,
            },
            {
                "trackers": {
                    "HARDWARE-TRACKER": {
                        "active": True,
                        "inactiveTimeout": 6000,
                        "activeInterval": 30000,
                        "exporters": {"CVP-TELEMETRY": {"localIntf": "Loopback10", "templateInterval": 3600000}},
                    }
                },
                "running": True,
            },
        ],
        "inputs": {
            "trackers": [
                {
                    "name": "FLOW-TRACKER",
                    "record_export": {"on_inactive_timeout": 6000, "on_interval": 30000},
                },
                {
                    "name": "HARDWARE-TRACKER",
                    "record_export": {"on_inactive_timeout": 60000, "on_interval": 300000},
                },
            ]
        },
        "expected": {
            "result": "failure",
            "messages": [
                "FLOW-TRACKER: \n"
                "Expected `6000` as the inactive timeout, but found `60000` instead.\nExpected `30000` as the interval, but found `300000` instead.\n",
                "HARDWARE-TRACKER: \n"
                "Expected `60000` as the inactive timeout, but found `6000` instead.\nExpected `300000` as the interval, but found `30000` instead.\n",
            ],
        },
    },
    {
        "name": "failure-incorrect-exporters",
        "test": VerifyHardwareFlowTrackerStatus,
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
                    }
                },
                "running": True,
            },
            {
                "trackers": {
                    "HARDWARE-TRACKER": {
                        "active": True,
                        "inactiveTimeout": 6000,
                        "activeInterval": 30000,
                        "exporters": {
                            "CVP-TELEMETRY": {"localIntf": "Loopback10", "templateInterval": 3600000},
                            "Hardware-flow": {"localIntf": "Loopback10", "templateInterval": 3600000},
                        },
                    }
                },
                "running": True,
            },
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
            "result": "failure",
            "messages": [
                "FLOW-TRACKER: \n"
                "Exporter `CVP-FLOW`: \n"
                "Expected `Loopback10` as the local interface, but found `Loopback0` instead.\n"
                "Expected `3500000` as the template interval, but found `3600000` instead.\n",
                "HARDWARE-TRACKER: \n"
                "Exporter `Hardware-flow`: \n"
                "Expected `Loopback99` as the local interface, but found `Loopback10` instead.\n"
                "Expected `3000000` as the template interval, but found `3600000` instead.\n"
                "Exporter `Reverse-flow` is not configured.\n",
            ],
        },
    },
    {
        "name": "failure-all-type",
        "test": VerifyHardwareFlowTrackerStatus,
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
            },
            {
                "trackers": {
                    "FLOW-TRIGGER": {
                        "active": False,
                        "inactiveTimeout": 60000,
                        "activeInterval": 300000,
                        "exporters": {"CV-TELEMETRY": {"localIntf": "Loopback0", "templateInterval": 3600000}},
                    }
                },
                "running": True,
            },
            {
                "trackers": {
                    "HARDWARE-FLOW": {
                        "active": True,
                        "inactiveTimeout": 6000,
                        "activeInterval": 30000,
                        "exporters": {"CVP-TELEMETRY": {"localIntf": "Loopback10", "templateInterval": 3600000}},
                    }
                },
                "running": True,
            },
            {
                "trackers": {
                    "FLOW-TRACKER2": {
                        "active": True,
                        "inactiveTimeout": 60000,
                        "activeInterval": 300000,
                        "exporters": {
                            "CV-TELEMETRY": {"localIntf": "Loopback0", "templateInterval": 3600000},
                            "CVP-FLOW": {"localIntf": "Loopback0", "templateInterval": 3600000},
                        },
                    }
                },
                "running": True,
            },
            {
                "trackers": {
                    "HARDWARE-TRACKER2": {
                        "active": True,
                        "inactiveTimeout": 6000,
                        "activeInterval": 30000,
                        "exporters": {
                            "CVP-TELEMETRY": {"localIntf": "Loopback10", "templateInterval": 3600000},
                            "Hardware-flow": {"localIntf": "Loopback10", "templateInterval": 3600000},
                        },
                    }
                },
                "running": True,
            },
        ],
        "inputs": {
            "trackers": [
                {"name": "FLOW-Sample"},
                {
                    "name": "FLOW-TRIGGER",
                    "record_export": {"on_inactive_timeout": 60000, "on_interval": 300000},
                    "exporters": [{"name": "CV-TELEMETRY", "local_interface": "Loopback0", "template_interval": 3600000}],
                },
                {
                    "name": "HARDWARE-FLOW",
                    "record_export": {"on_inactive_timeout": 60000, "on_interval": 300000},
                },
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
            "result": "failure",
            "messages": [
                "Hardware flow tracker `FLOW-Sample` is not configured.",
                "Hardware flow tracker `FLOW-TRIGGER` is not active.",
                "HARDWARE-FLOW: \n"
                "Expected `60000` as the inactive timeout, but found `6000` instead.\nExpected `300000` as the interval, but found `30000` instead.\n",
                "FLOW-TRACKER2: \nExporter `CVP-FLOW`: \n"
                "Expected `Loopback10` as the local interface, but found `Loopback0` instead.\n"
                "Expected `3500000` as the template interval, but found `3600000` instead.\n",
                "HARDWARE-TRACKER2: \nExporter `Hardware-flow`: \n"
                "Expected `Loopback99` as the local interface, but found `Loopback10` instead.\n"
                "Expected `3000000` as the template interval, but found `3600000` instead.\n"
                "Exporter `Reverse-flow` is not configured.\n",
            ],
        },
    },
]
