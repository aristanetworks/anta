# Copyright (c) 2023-2024 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Tests for anta.tests.stp.py."""

from __future__ import annotations

from typing import Any

from anta.tests.stp import VerifySTPBlockedPorts, VerifySTPCounters, VerifySTPForwardingPorts, VerifySTPMode, VerifySTPRootPriority, VerifyStpTopologyChanges
from tests.lib.anta import test

DATA: list[dict[str, Any]] = [
    {
        "name": "success",
        "test": VerifySTPMode,
        "eos_data": [
            {"spanningTreeVlanInstances": {"10": {"spanningTreeVlanInstance": {"protocol": "rstp"}}}},
            {"spanningTreeVlanInstances": {"20": {"spanningTreeVlanInstance": {"protocol": "rstp"}}}},
        ],
        "inputs": {"mode": "rstp", "vlans": [10, 20]},
        "expected": {"result": "success"},
    },
    {
        "name": "failure-no-instances",
        "test": VerifySTPMode,
        "eos_data": [
            {"spanningTreeVlanInstances": {}},
            {"spanningTreeVlanInstances": {}},
        ],
        "inputs": {"mode": "rstp", "vlans": [10, 20]},
        "expected": {"result": "failure", "messages": ["STP mode 'rstp' not configured for the following VLAN(s): [10, 20]"]},
    },
    {
        "name": "failure-wrong-mode",
        "test": VerifySTPMode,
        "eos_data": [
            {"spanningTreeVlanInstances": {"10": {"spanningTreeVlanInstance": {"protocol": "mstp"}}}},
            {"spanningTreeVlanInstances": {"20": {"spanningTreeVlanInstance": {"protocol": "mstp"}}}},
        ],
        "inputs": {"mode": "rstp", "vlans": [10, 20]},
        "expected": {"result": "failure", "messages": ["Wrong STP mode configured for the following VLAN(s): [10, 20]"]},
    },
    {
        "name": "failure-both",
        "test": VerifySTPMode,
        "eos_data": [
            {"spanningTreeVlanInstances": {}},
            {"spanningTreeVlanInstances": {"20": {"spanningTreeVlanInstance": {"protocol": "mstp"}}}},
        ],
        "inputs": {"mode": "rstp", "vlans": [10, 20]},
        "expected": {
            "result": "failure",
            "messages": ["STP mode 'rstp' not configured for the following VLAN(s): [10]", "Wrong STP mode configured for the following VLAN(s): [20]"],
        },
    },
    {
        "name": "success",
        "test": VerifySTPBlockedPorts,
        "eos_data": [{"spanningTreeInstances": {}}],
        "inputs": None,
        "expected": {"result": "success"},
    },
    {
        "name": "failure",
        "test": VerifySTPBlockedPorts,
        "eos_data": [{"spanningTreeInstances": {"MST0": {"spanningTreeBlockedPorts": ["Ethernet10"]}, "MST10": {"spanningTreeBlockedPorts": ["Ethernet10"]}}}],
        "inputs": None,
        "expected": {"result": "failure", "messages": ["The following ports are blocked by STP: {'MST0': ['Ethernet10'], 'MST10': ['Ethernet10']}"]},
    },
    {
        "name": "success",
        "test": VerifySTPCounters,
        "eos_data": [{"interfaces": {"Ethernet10": {"bpduSent": 99, "bpduReceived": 0, "bpduTaggedError": 0, "bpduOtherError": 0, "bpduRateLimitCount": 0}}}],
        "inputs": None,
        "expected": {"result": "success"},
    },
    {
        "name": "failure",
        "test": VerifySTPCounters,
        "eos_data": [
            {
                "interfaces": {
                    "Ethernet10": {"bpduSent": 201, "bpduReceived": 0, "bpduTaggedError": 3, "bpduOtherError": 0, "bpduRateLimitCount": 0},
                    "Ethernet11": {"bpduSent": 99, "bpduReceived": 0, "bpduTaggedError": 0, "bpduOtherError": 6, "bpduRateLimitCount": 0},
                },
            },
        ],
        "inputs": None,
        "expected": {"result": "failure", "messages": ["The following interfaces have STP BPDU packet errors: ['Ethernet10', 'Ethernet11']"]},
    },
    {
        "name": "success",
        "test": VerifySTPForwardingPorts,
        "eos_data": [
            {
                "unmappedVlans": [],
                "topologies": {"Mst10": {"vlans": [10], "interfaces": {"Ethernet10": {"state": "forwarding"}, "MplsTrunk1": {"state": "forwarding"}}}},
            },
            {
                "unmappedVlans": [],
                "topologies": {"Mst20": {"vlans": [20], "interfaces": {"Ethernet10": {"state": "forwarding"}, "MplsTrunk1": {"state": "forwarding"}}}},
            },
        ],
        "inputs": {"vlans": [10, 20]},
        "expected": {"result": "success"},
    },
    {
        "name": "success-vlan-not-in-topology",  # Should it succeed really ? TODO - this output should be impossible
        "test": VerifySTPForwardingPorts,
        "eos_data": [
            {
                "unmappedVlans": [],
                "topologies": {"Mst10": {"vlans": [10], "interfaces": {"Ethernet10": {"state": "forwarding"}, "MplsTrunk1": {"state": "forwarding"}}}},
            },
            {
                "unmappedVlans": [],
                "topologies": {"Mst10": {"vlans": [10], "interfaces": {"Ethernet10": {"state": "forwarding"}, "MplsTrunk1": {"state": "forwarding"}}}},
            },
        ],
        "inputs": {"vlans": [10, 20]},
        "expected": {"result": "success"},
    },
    {
        "name": "failure-no-instances",
        "test": VerifySTPForwardingPorts,
        "eos_data": [{"unmappedVlans": [], "topologies": {}}, {"unmappedVlans": [], "topologies": {}}],
        "inputs": {"vlans": [10, 20]},
        "expected": {"result": "failure", "messages": ["STP instance is not configured for the following VLAN(s): [10, 20]"]},
    },
    {
        "name": "failure",
        "test": VerifySTPForwardingPorts,
        "eos_data": [
            {
                "unmappedVlans": [],
                "topologies": {"Vl10": {"vlans": [10], "interfaces": {"Ethernet10": {"state": "discarding"}, "MplsTrunk1": {"state": "forwarding"}}}},
            },
            {
                "unmappedVlans": [],
                "topologies": {"Vl20": {"vlans": [20], "interfaces": {"Ethernet10": {"state": "discarding"}, "MplsTrunk1": {"state": "forwarding"}}}},
            },
        ],
        "inputs": {"vlans": [10, 20]},
        "expected": {
            "result": "failure",
            "messages": ["The following VLAN(s) have interface(s) that are not in a forwarding state: [{'VLAN 10': ['Ethernet10']}, {'VLAN 20': ['Ethernet10']}]"],
        },
    },
    {
        "name": "success-specific-instances",
        "test": VerifySTPRootPriority,
        "eos_data": [
            {
                "instances": {
                    "VL10": {
                        "rootBridge": {
                            "priority": 32768,
                            "systemIdExtension": 10,
                            "macAddress": "00:1c:73:27:95:a2",
                            "helloTime": 2.0,
                            "maxAge": 20,
                            "forwardDelay": 15,
                        },
                    },
                    "VL20": {
                        "rootBridge": {
                            "priority": 32768,
                            "systemIdExtension": 20,
                            "macAddress": "00:1c:73:27:95:a2",
                            "helloTime": 2.0,
                            "maxAge": 20,
                            "forwardDelay": 15,
                        },
                    },
                    "VL30": {
                        "rootBridge": {
                            "priority": 32768,
                            "systemIdExtension": 30,
                            "macAddress": "00:1c:73:27:95:a2",
                            "helloTime": 2.0,
                            "maxAge": 20,
                            "forwardDelay": 15,
                        },
                    },
                },
            },
        ],
        "inputs": {"priority": 32768, "instances": [10, 20]},
        "expected": {"result": "success"},
    },
    {
        "name": "success-all-instances",
        "test": VerifySTPRootPriority,
        "eos_data": [
            {
                "instances": {
                    "VL10": {
                        "rootBridge": {
                            "priority": 32768,
                            "systemIdExtension": 10,
                            "macAddress": "00:1c:73:27:95:a2",
                            "helloTime": 2.0,
                            "maxAge": 20,
                            "forwardDelay": 15,
                        },
                    },
                    "VL20": {
                        "rootBridge": {
                            "priority": 32768,
                            "systemIdExtension": 20,
                            "macAddress": "00:1c:73:27:95:a2",
                            "helloTime": 2.0,
                            "maxAge": 20,
                            "forwardDelay": 15,
                        },
                    },
                    "VL30": {
                        "rootBridge": {
                            "priority": 32768,
                            "systemIdExtension": 30,
                            "macAddress": "00:1c:73:27:95:a2",
                            "helloTime": 2.0,
                            "maxAge": 20,
                            "forwardDelay": 15,
                        },
                    },
                },
            },
        ],
        "inputs": {"priority": 32768},
        "expected": {"result": "success"},
    },
    {
        "name": "success-MST",
        "test": VerifySTPRootPriority,
        "eos_data": [
            {
                "instances": {
                    "MST0": {
                        "rootBridge": {
                            "priority": 16384,
                            "systemIdExtension": 0,
                            "macAddress": "02:1c:73:8b:93:ac",
                            "helloTime": 2.0,
                            "maxAge": 20,
                            "forwardDelay": 15,
                        },
                    },
                },
            },
        ],
        "inputs": {"priority": 16384, "instances": [0]},
        "expected": {"result": "success"},
    },
    {
        "name": "failure-no-instances",
        "test": VerifySTPRootPriority,
        "eos_data": [
            {
                "instances": {
                    "WRONG0": {
                        "rootBridge": {
                            "priority": 16384,
                            "systemIdExtension": 0,
                            "macAddress": "02:1c:73:8b:93:ac",
                            "helloTime": 2.0,
                            "maxAge": 20,
                            "forwardDelay": 15,
                        },
                    },
                },
            },
        ],
        "inputs": {"priority": 32768, "instances": [0]},
        "expected": {"result": "failure", "messages": ["Unsupported STP instance type: WRONG0"]},
    },
    {
        "name": "failure-wrong-instance-type",
        "test": VerifySTPRootPriority,
        "eos_data": [{"instances": {}}],
        "inputs": {"priority": 32768, "instances": [10, 20]},
        "expected": {"result": "failure", "messages": ["No STP instances configured"]},
    },
    {
        "name": "failure-wrong-priority",
        "test": VerifySTPRootPriority,
        "eos_data": [
            {
                "instances": {
                    "VL10": {
                        "rootBridge": {
                            "priority": 32768,
                            "systemIdExtension": 10,
                            "macAddress": "00:1c:73:27:95:a2",
                            "helloTime": 2.0,
                            "maxAge": 20,
                            "forwardDelay": 15,
                        },
                    },
                    "VL20": {
                        "rootBridge": {
                            "priority": 8196,
                            "systemIdExtension": 20,
                            "macAddress": "00:1c:73:27:95:a2",
                            "helloTime": 2.0,
                            "maxAge": 20,
                            "forwardDelay": 15,
                        },
                    },
                    "VL30": {
                        "rootBridge": {
                            "priority": 8196,
                            "systemIdExtension": 30,
                            "macAddress": "00:1c:73:27:95:a2",
                            "helloTime": 2.0,
                            "maxAge": 20,
                            "forwardDelay": 15,
                        },
                    },
                },
            },
        ],
        "inputs": {"priority": 32768, "instances": [10, 20, 30]},
        "expected": {"result": "failure", "messages": ["The following instance(s) have the wrong STP root priority configured: ['VL20', 'VL30']"]},
    },
    {
        "name": "success",
        "test": VerifyStpTopologyChanges,
        "eos_data": [
            {
                "unmappedVlans": [],
                "topologies": {
                    "Cist": {
                        "interfaces": {
                            "Cpu": {"state": "forwarding", "numChanges": 1, "lastChange": 1723990624.735365},
                            "Port-Channel5": {"state": "forwarding", "numChanges": 1, "lastChange": 1723990624.7353542},
                        }
                    },
                    "NoStp": {
                        "interfaces": {
                            "Cpu": {"state": "forwarding", "numChanges": 1, "lastChange": 1723990624.735365},
                            "Ethernet1": {"state": "forwarding", "numChanges": 15, "lastChange": 1723990624.7353542},
                        }
                    },
                },
            },
        ],
        "inputs": {},
        "expected": {"result": "success"},
    },
    {
        "name": "failure-unstable-topology",
        "test": VerifyStpTopologyChanges,
        "eos_data": [
            {
                "unmappedVlans": [],
                "topologies": {
                    "Cist": {
                        "interfaces": {
                            "Cpu": {"state": "forwarding", "numChanges": 15, "lastChange": 1723990624.735365},
                            "Port-Channel5": {"state": "forwarding", "numChanges": 15, "lastChange": 1723990624.7353542},
                        }
                    },
                },
            },
        ],
        "inputs": {},
        "expected": {
            "result": "failure",
            "messages": [
                "The following Spanning Tree Protocol (STP) topology(s) are not configured or number of changes"
                " not within the threshold:{'topologies': {'Cist': {'Cpu': {'Number of changes': 15}, 'Port-Channel5': {'Number of changes': 15}}}}"
            ],
        },
    },
    {
        "name": "failure-topologies-not-configured",
        "test": VerifyStpTopologyChanges,
        "eos_data": [
            {"unmappedVlans": [], "topologies": {}},
        ],
        "inputs": {},
        "expected": {"result": "failure", "messages": ["None of STP topology is configured."]},
    },
]
