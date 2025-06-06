# Copyright (c) 2023-2025 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Tests for anta.tests.stp.py."""

from __future__ import annotations

import sys
from typing import TYPE_CHECKING, Any

from anta.models import AntaTest
from anta.result_manager.models import AntaTestStatus
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
    from tests.units.anta_tests import AntaUnitTestDataDict

DATA: AntaUnitTestDataDict = {
    (VerifySTPMode, "success"): {
        "eos_data": [
            {"spanningTreeVlanInstances": {"10": {"spanningTreeVlanInstance": {"protocol": "rstp"}}}},
            {"spanningTreeVlanInstances": {"20": {"spanningTreeVlanInstance": {"protocol": "rstp"}}}},
        ],
        "inputs": {"mode": "rstp", "vlans": [10, 20]},
        "expected": {"result": AntaTestStatus.SUCCESS},
    },
    (VerifySTPMode, "failure-no-instances"): {
        "eos_data": [{"spanningTreeVlanInstances": {}}, {"spanningTreeVlanInstances": {}}],
        "inputs": {"mode": "rstp", "vlans": [10, 20]},
        "expected": {"result": AntaTestStatus.FAILURE, "messages": ["VLAN 10 STP mode: rstp - Not configured", "VLAN 20 STP mode: rstp - Not configured"]},
    },
    (VerifySTPMode, "failure-wrong-mode"): {
        "eos_data": [
            {"spanningTreeVlanInstances": {"10": {"spanningTreeVlanInstance": {"protocol": "mstp"}}}},
            {"spanningTreeVlanInstances": {"20": {"spanningTreeVlanInstance": {"protocol": "mstp"}}}},
        ],
        "inputs": {"mode": "rstp", "vlans": [10, 20]},
        "expected": {
            "result": AntaTestStatus.FAILURE,
            "messages": ["VLAN 10 - Incorrect STP mode - Expected: rstp Actual: mstp", "VLAN 20 - Incorrect STP mode - Expected: rstp Actual: mstp"],
        },
    },
    (VerifySTPMode, "failure-both"): {
        "eos_data": [{"spanningTreeVlanInstances": {}}, {"spanningTreeVlanInstances": {"20": {"spanningTreeVlanInstance": {"protocol": "mstp"}}}}],
        "inputs": {"mode": "rstp", "vlans": [10, 20]},
        "expected": {
            "result": AntaTestStatus.FAILURE,
            "messages": ["VLAN 10 STP mode: rstp - Not configured", "VLAN 20 - Incorrect STP mode - Expected: rstp Actual: mstp"],
        },
    },
    (VerifySTPBlockedPorts, "success"): {"eos_data": [{"spanningTreeInstances": {}}], "expected": {"result": AntaTestStatus.SUCCESS}},
    (VerifySTPBlockedPorts, "failure"): {
        "eos_data": [{"spanningTreeInstances": {"MST0": {"spanningTreeBlockedPorts": ["Ethernet10"]}, "MST10": {"spanningTreeBlockedPorts": ["Ethernet10"]}}}],
        "expected": {
            "result": AntaTestStatus.FAILURE,
            "messages": ["STP Instance: MST0 - Blocked ports - Ethernet10", "STP Instance: MST10 - Blocked ports - Ethernet10"],
        },
    },
    (VerifySTPCounters, "success"): {
        "eos_data": [{"interfaces": {"Ethernet10": {"bpduSent": 99, "bpduReceived": 0, "bpduTaggedError": 0, "bpduOtherError": 0, "bpduRateLimitCount": 0}}}],
        "expected": {"result": AntaTestStatus.SUCCESS},
    },
    (VerifySTPCounters, "failure-bpdu-tagged-error-mismatch"): {
        "eos_data": [
            {
                "interfaces": {
                    "Ethernet10": {"bpduSent": 201, "bpduReceived": 0, "bpduTaggedError": 3, "bpduOtherError": 0, "bpduRateLimitCount": 0},
                    "Ethernet11": {"bpduSent": 99, "bpduReceived": 0, "bpduTaggedError": 3, "bpduOtherError": 0, "bpduRateLimitCount": 0},
                }
            }
        ],
        "expected": {
            "result": AntaTestStatus.FAILURE,
            "messages": [
                "Interface Ethernet10 - STP BPDU packet tagged errors count mismatch - Expected: 0 Actual: 3",
                "Interface Ethernet11 - STP BPDU packet tagged errors count mismatch - Expected: 0 Actual: 3",
            ],
        },
    },
    (VerifySTPCounters, "failure-bpdu-other-error-mismatch"): {
        "eos_data": [
            {
                "interfaces": {
                    "Ethernet10": {"bpduSent": 201, "bpduReceived": 0, "bpduTaggedError": 0, "bpduOtherError": 3, "bpduRateLimitCount": 0},
                    "Ethernet11": {"bpduSent": 99, "bpduReceived": 0, "bpduTaggedError": 0, "bpduOtherError": 6, "bpduRateLimitCount": 0},
                }
            }
        ],
        "expected": {
            "result": AntaTestStatus.FAILURE,
            "messages": [
                "Interface Ethernet10 - STP BPDU packet other errors count mismatch - Expected: 0 Actual: 3",
                "Interface Ethernet11 - STP BPDU packet other errors count mismatch - Expected: 0 Actual: 6",
            ],
        },
    },
    (VerifySTPCounters, "success-ignore-interface"): {
        "eos_data": [
            {
                "interfaces": {
                    "Ethernet10": {"bpduSent": 201, "bpduReceived": 0, "bpduTaggedError": 3, "bpduOtherError": 0, "bpduRateLimitCount": 0},
                    "Ethernet11": {"bpduSent": 99, "bpduReceived": 0, "bpduTaggedError": 0, "bpduOtherError": 0, "bpduRateLimitCount": 0},
                }
            }
        ],
        "inputs": {"ignored_interfaces": ["Ethernet10"]},
        "expected": {
            "result": AntaTestStatus.SUCCESS,
        },
    },
    (VerifySTPCounters, "success-specific-interface"): {
        "eos_data": [
            {
                "interfaces": {
                    "Ethernet10": {"bpduSent": 201, "bpduReceived": 0, "bpduTaggedError": 3, "bpduOtherError": 0, "bpduRateLimitCount": 0},
                    "Ethernet11": {"bpduSent": 99, "bpduReceived": 0, "bpduTaggedError": 0, "bpduOtherError": 0, "bpduRateLimitCount": 0},
                }
            }
        ],
        "inputs": {"interfaces": ["Ethernet11"]},
        "expected": {
            "result": AntaTestStatus.SUCCESS,
        },
    },
    (VerifySTPCounters, "failure-specific-interface-not-found"): {
        "eos_data": [
            {
                "interfaces": {
                    "Ethernet10": {"bpduSent": 201, "bpduReceived": 0, "bpduTaggedError": 3, "bpduOtherError": 0, "bpduRateLimitCount": 0},
                    "Ethernet11": {"bpduSent": 99, "bpduReceived": 0, "bpduTaggedError": 0, "bpduOtherError": 0, "bpduRateLimitCount": 0},
                }
            }
        ],
        "inputs": {"interfaces": ["Ethernet12"]},
        "expected": {"result": AntaTestStatus.FAILURE, "messages": ["Interface: Ethernet12 - Not found"]},
    },
    (VerifySTPForwardingPorts, "success"): {
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
        "expected": {"result": AntaTestStatus.SUCCESS},
    },
    (VerifySTPForwardingPorts, "success-vlan-not-in-topology"): {
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
        "expected": {"result": AntaTestStatus.SUCCESS},
    },
    (VerifySTPForwardingPorts, "failure-no-instances"): {
        "eos_data": [{"unmappedVlans": [], "topologies": {}}, {"unmappedVlans": [], "topologies": {}}],
        "inputs": {"vlans": [10, 20]},
        "expected": {"result": AntaTestStatus.FAILURE, "messages": ["VLAN 10 - STP instance is not configured", "VLAN 20 - STP instance is not configured"]},
    },
    (VerifySTPForwardingPorts, "failure"): {
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
            "result": AntaTestStatus.FAILURE,
            "messages": [
                "VLAN 10 Interface: Ethernet10 - Invalid state - Expected: forwarding Actual: discarding",
                "VLAN 20 Interface: Ethernet10 - Invalid state - Expected: forwarding Actual: discarding",
            ],
        },
    },
    (VerifySTPRootPriority, "success-specific-instances"): {
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
                        }
                    },
                    "VL20": {
                        "rootBridge": {
                            "priority": 32768,
                            "systemIdExtension": 20,
                            "macAddress": "00:1c:73:27:95:a2",
                            "helloTime": 2.0,
                            "maxAge": 20,
                            "forwardDelay": 15,
                        }
                    },
                    "VL30": {
                        "rootBridge": {
                            "priority": 32768,
                            "systemIdExtension": 30,
                            "macAddress": "00:1c:73:27:95:a2",
                            "helloTime": 2.0,
                            "maxAge": 20,
                            "forwardDelay": 15,
                        }
                    },
                }
            }
        ],
        "inputs": {"priority": 32768, "instances": [10, 20]},
        "expected": {"result": AntaTestStatus.SUCCESS},
    },
    (VerifySTPRootPriority, "success-all-instances"): {
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
                        }
                    },
                    "VL20": {
                        "rootBridge": {
                            "priority": 32768,
                            "systemIdExtension": 20,
                            "macAddress": "00:1c:73:27:95:a2",
                            "helloTime": 2.0,
                            "maxAge": 20,
                            "forwardDelay": 15,
                        }
                    },
                    "VL30": {
                        "rootBridge": {
                            "priority": 32768,
                            "systemIdExtension": 30,
                            "macAddress": "00:1c:73:27:95:a2",
                            "helloTime": 2.0,
                            "maxAge": 20,
                            "forwardDelay": 15,
                        }
                    },
                }
            }
        ],
        "inputs": {"priority": 32768},
        "expected": {"result": AntaTestStatus.SUCCESS},
    },
    (VerifySTPRootPriority, "success-MST"): {
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
                        }
                    }
                }
            }
        ],
        "inputs": {"priority": 16384, "instances": [0]},
        "expected": {"result": AntaTestStatus.SUCCESS},
    },
    (VerifySTPRootPriority, "success-input-instance-none"): {
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
                        }
                    }
                }
            }
        ],
        "inputs": {"priority": 16384},
        "expected": {"result": AntaTestStatus.SUCCESS},
    },
    (VerifySTPRootPriority, "failure-no-instances"): {
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
                        }
                    }
                }
            }
        ],
        "inputs": {"priority": 32768, "instances": [0]},
        "expected": {"result": AntaTestStatus.FAILURE, "messages": ["STP Instance: WRONG0 - Unsupported STP instance type"]},
    },
    (VerifySTPRootPriority, "failure-wrong-instance-type"): {
        "eos_data": [{"instances": {}}],
        "inputs": {"priority": 32768, "instances": [10, 20]},
        "expected": {"result": AntaTestStatus.FAILURE, "messages": ["No STP instances configured"]},
    },
    (VerifySTPRootPriority, "failure-instance-not-found"): {
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
                        }
                    }
                }
            }
        ],
        "inputs": {"priority": 32768, "instances": [11, 20]},
        "expected": {"result": AntaTestStatus.FAILURE, "messages": ["Instance: VL11 - Not configured", "Instance: VL20 - Not configured"]},
    },
    (VerifySTPRootPriority, "failure-wrong-priority"): {
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
                        }
                    },
                    "VL20": {
                        "rootBridge": {
                            "priority": 8196,
                            "systemIdExtension": 20,
                            "macAddress": "00:1c:73:27:95:a2",
                            "helloTime": 2.0,
                            "maxAge": 20,
                            "forwardDelay": 15,
                        }
                    },
                    "VL30": {
                        "rootBridge": {
                            "priority": 8196,
                            "systemIdExtension": 30,
                            "macAddress": "00:1c:73:27:95:a2",
                            "helloTime": 2.0,
                            "maxAge": 20,
                            "forwardDelay": 15,
                        }
                    },
                }
            }
        ],
        "inputs": {"priority": 32768, "instances": [10, 20, 30]},
        "expected": {
            "result": AntaTestStatus.FAILURE,
            "messages": [
                "STP Instance: VL20 - Incorrect root priority - Expected: 32768 Actual: 8196",
                "STP Instance: VL30 - Incorrect root priority - Expected: 32768 Actual: 8196",
            ],
        },
    },
    (VerifyStpTopologyChanges, "success-mstp"): {
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
            }
        ],
        "inputs": {"threshold": 10},
        "expected": {"result": AntaTestStatus.SUCCESS},
    },
    (VerifyStpTopologyChanges, "success-rstp"): {
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
            }
        ],
        "inputs": {"threshold": 10},
        "expected": {"result": AntaTestStatus.SUCCESS},
    },
    (VerifyStpTopologyChanges, "success-rapid-pvst"): {
        "eos_data": [
            {
                "unmappedVlans": [],
                "topologies": {
                    "NoStp": {
                        "vlans": [4094, 4093, 1006],
                        "interfaces": {"PeerEthernet2": {"state": "forwarding", "numChanges": 1, "lastChange": 1727151356.1330667}},
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
            }
        ],
        "inputs": {"threshold": 10},
        "expected": {"result": AntaTestStatus.SUCCESS},
    },
    (VerifyStpTopologyChanges, "failure-unstable-topology"): {
        "eos_data": [
            {
                "unmappedVlans": [],
                "topologies": {
                    "Cist": {
                        "interfaces": {
                            "Cpu": {"state": "forwarding", "numChanges": 15, "lastChange": 1723990624.735365},
                            "Port-Channel5": {"state": "forwarding", "numChanges": 15, "lastChange": 1723990624.7353542},
                        }
                    }
                },
            }
        ],
        "inputs": {"threshold": 10},
        "expected": {
            "result": AntaTestStatus.FAILURE,
            "messages": [
                "Topology: Cist Interface: Cpu - Number of changes not within the threshold - Expected: 10 Actual: 15",
                "Topology: Cist Interface: Port-Channel5 - Number of changes not within the threshold - Expected: 10 Actual: 15",
            ],
        },
    },
    (VerifyStpTopologyChanges, "failure-topologies-not-configured"): {
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
            }
        ],
        "inputs": {"threshold": 10},
        "expected": {"result": AntaTestStatus.FAILURE, "messages": ["STP is not configured"]},
    },
    (VerifySTPDisabledVlans, "success"): {
        "eos_data": [{"spanningTreeVlanInstances": {"1": {"spanningTreeVlanInstance": {"protocol": "mstp", "bridge": {"priority": 32768}}}, "6": {}, "4094": {}}}],
        "inputs": {"vlans": ["6", "4094"]},
        "expected": {"result": AntaTestStatus.SUCCESS},
    },
    (VerifySTPDisabledVlans, "failure-stp-not-configured"): {
        "eos_data": [{"spanningTreeVlanInstances": {}}],
        "inputs": {"vlans": ["6", "4094"]},
        "expected": {"result": AntaTestStatus.FAILURE, "messages": ["STP is not configured"]},
    },
    (VerifySTPDisabledVlans, "failure-vlans-not-found"): {
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
        "expected": {"result": AntaTestStatus.FAILURE, "messages": ["VLAN: 16 - Not configured", "VLAN: 4093 - Not configured"]},
    },
    (VerifySTPDisabledVlans, "failure-vlans-enabled"): {
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
        "expected": {"result": AntaTestStatus.FAILURE, "messages": ["VLAN: 6 - STP is enabled", "VLAN: 4094 - STP is enabled"]},
    },
}
