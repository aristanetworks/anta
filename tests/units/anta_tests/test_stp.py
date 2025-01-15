# Copyright (c) 2023-2025 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Tests for anta.tests.stp.py."""

from __future__ import annotations

from typing import TYPE_CHECKING

from anta.tests.stp import (
    VerifySTPBlockedPorts,
    VerifySTPCounters,
    VerifySTPDisabledVlans,
    VerifySTPForwardingPorts,
    VerifySTPMode,
    VerifySTPRootPriority,
    VerifyStpTopologyChanges,
)
from tests.units.anta_tests import test

if TYPE_CHECKING:
    from tests.units.anta_tests import AntaUnitTest

DATA: list[AntaUnitTest] = [
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
        "expected": {"result": "success"},
    },
    {
        "name": "failure",
        "test": VerifySTPBlockedPorts,
        "eos_data": [{"spanningTreeInstances": {"MST0": {"spanningTreeBlockedPorts": ["Ethernet10"]}, "MST10": {"spanningTreeBlockedPorts": ["Ethernet10"]}}}],
        "expected": {"result": "failure", "messages": ["The following ports are blocked by STP: {'MST0': ['Ethernet10'], 'MST10': ['Ethernet10']}"]},
    },
    {
        "name": "success",
        "test": VerifySTPCounters,
        "eos_data": [{"interfaces": {"Ethernet10": {"bpduSent": 99, "bpduReceived": 0, "bpduTaggedError": 0, "bpduOtherError": 0, "bpduRateLimitCount": 0}}}],
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
        "name": "success-mstp",
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
        "inputs": {"threshold": 10},
        "expected": {"result": "success"},
    },
    {
        "name": "success-rstp",
        "test": VerifyStpTopologyChanges,
        "eos_data": [
            {
                "unmappedVlans": [],
                "topologies": {
                    "Cist": {
                        "interfaces": {
                            "Vxlan1": {"state": "forwarding", "numChanges": 1, "lastChange": 1723990624.735365},
                            "PeerEthernet3": {"state": "forwarding", "numChanges": 1, "lastChange": 1723990624.7353542},
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
        "inputs": {"threshold": 10},
        "expected": {"result": "success"},
    },
    {
        "name": "success-rapid-pvst",
        "test": VerifyStpTopologyChanges,
        "eos_data": [
            {
                "unmappedVlans": [],
                "topologies": {
                    "NoStp": {
                        "vlans": [4094, 4093, 1006],
                        "interfaces": {
                            "PeerEthernet2": {"state": "forwarding", "numChanges": 1, "lastChange": 1727151356.1330667},
                        },
                    },
                    "Vl1": {"vlans": [1], "interfaces": {"Port-Channel5": {"state": "forwarding", "numChanges": 1, "lastChange": 1727326710.0615358}}},
                    "Vl10": {
                        "vlans": [10],
                        "interfaces": {
                            "Cpu": {"state": "forwarding", "numChanges": 1, "lastChange": 1727326710.0673406},
                            "Vxlan1": {"state": "forwarding", "numChanges": 1, "lastChange": 1727326710.0677001},
                            "Port-Channel5": {"state": "forwarding", "numChanges": 1, "lastChange": 1727326710.0728855},
                            "Ethernet3": {"state": "forwarding", "numChanges": 3, "lastChange": 1727326730.255137},
                        },
                    },
                    "Vl1198": {
                        "vlans": [1198],
                        "interfaces": {
                            "Cpu": {"state": "forwarding", "numChanges": 1, "lastChange": 1727326710.074386},
                            "Vxlan1": {"state": "forwarding", "numChanges": 1, "lastChange": 1727326710.0743902},
                            "Port-Channel5": {"state": "forwarding", "numChanges": 1, "lastChange": 1727326710.0743942},
                        },
                    },
                    "Vl1199": {
                        "vlans": [1199],
                        "interfaces": {
                            "Cpu": {"state": "forwarding", "numChanges": 1, "lastChange": 1727326710.0744},
                            "Vxlan1": {"state": "forwarding", "numChanges": 1, "lastChange": 1727326710.07453},
                            "Port-Channel5": {"state": "forwarding", "numChanges": 1, "lastChange": 1727326710.074535},
                        },
                    },
                    "Vl20": {
                        "vlans": [20],
                        "interfaces": {
                            "Cpu": {"state": "forwarding", "numChanges": 1, "lastChange": 1727326710.073489},
                            "Vxlan1": {"state": "forwarding", "numChanges": 1, "lastChange": 1727326710.0743747},
                            "Port-Channel5": {"state": "forwarding", "numChanges": 1, "lastChange": 1727326710.0743794},
                            "Ethernet3": {"state": "forwarding", "numChanges": 3, "lastChange": 1727326730.2551405},
                        },
                    },
                    "Vl3009": {
                        "vlans": [3009],
                        "interfaces": {
                            "Cpu": {"state": "forwarding", "numChanges": 1, "lastChange": 1727326710.074541},
                            "Port-Channel5": {"state": "forwarding", "numChanges": 1, "lastChange": 1727326710.0745454},
                        },
                    },
                    "Vl3019": {
                        "vlans": [3019],
                        "interfaces": {
                            "Cpu": {"state": "forwarding", "numChanges": 1, "lastChange": 1727326710.0745502},
                            "Port-Channel5": {"state": "forwarding", "numChanges": 1, "lastChange": 1727326710.0745537},
                        },
                    },
                },
            },
        ],
        "inputs": {"threshold": 10},
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
        "inputs": {"threshold": 10},
        "expected": {
            "result": "failure",
            "messages": [
                "The following STP topologies are not configured or number of changes not within the threshold:\n"
                "{'topologies': {'Cist': {'Cpu': {'Number of changes': 15}, 'Port-Channel5': {'Number of changes': 15}}}}"
            ],
        },
    },
    {
        "name": "failure-topologies-not-configured",
        "test": VerifyStpTopologyChanges,
        "eos_data": [
            {
                "unmappedVlans": [],
                "topologies": {
                    "NoStp": {
                        "interfaces": {
                            "Cpu": {"state": "forwarding", "numChanges": 1, "lastChange": 1723990624.735365},
                            "Ethernet1": {"state": "forwarding", "numChanges": 15, "lastChange": 1723990624.7353542},
                        }
                    }
                },
            },
        ],
        "inputs": {"threshold": 10},
        "expected": {"result": "failure", "messages": ["STP is not configured."]},
    },
    {
        "name": "success",
        "test": VerifySTPDisabledVlans,
        "eos_data": [{"spanningTreeVlanInstances": {"1": {"spanningTreeVlanInstance": {"protocol": "mstp", "bridge": {"priority": 32768}}}, "6": {}, "4094": {}}}],
        "inputs": {"vlans": ["6", "4094"]},
        "expected": {"result": "success"},
    },
    {
        "name": "failure-stp-not-configured",
        "test": VerifySTPDisabledVlans,
        "eos_data": [{"spanningTreeVlanInstances": {}}],
        "inputs": {"vlans": ["6", "4094"]},
        "expected": {"result": "failure", "messages": ["STP is not configured"]},
    },
    {
        "name": "failure-vlans-not-found",
        "test": VerifySTPDisabledVlans,
        "eos_data": [
            {
                "spanningTreeVlanInstances": {
                    "1": {"spanningTreeVlanInstance": {"protocol": "mstp", "bridge": {}}},
                    "6": {"spanningTreeVlanInstance": {"protocol": "mstp", "bridge": {}}},
                    "4094": {"spanningTreeVlanInstance": {"protocol": "mstp", "bridge": {}}},
                }
            }
        ],
        "inputs": {"vlans": ["16", "4093"]},
        "expected": {"result": "failure", "messages": ["VLAN: 16 - Not configured", "VLAN: 4093 - Not configured"]},
    },
    {
        "name": "failure-vlans-enabled",
        "test": VerifySTPDisabledVlans,
        "eos_data": [
            {
                "spanningTreeVlanInstances": {
                    "1": {"spanningTreeVlanInstance": {"protocol": "mstp", "bridge": {}}},
                    "6": {"spanningTreeVlanInstance": {"protocol": "mstp", "bridge": {}}},
                    "4094": {"spanningTreeVlanInstance": {"protocol": "mstp", "bridge": {}}},
                }
            }
        ],
        "inputs": {"vlans": ["6", "4094"]},
        "expected": {"result": "failure", "messages": ["VLAN: 6 - STP is enabled", "VLAN: 4094 - STP is enabled"]},
    },
]
