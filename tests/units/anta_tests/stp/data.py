# Copyright (c) 2023 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Data for testing anta.tests.aaa"""

from typing import Any, Dict, List

INPUT_STP_MODE: List[Dict[str, Any]] = [
    {
        "name": "success",
        "eos_data": [
            {
                "spanningTreeVlanInstances": {
                    "10": {
                        "spanningTreeVlanInstance": {
                            "protocol": "rstp"
                        }
                    }
                }
            },
            {
                "spanningTreeVlanInstances": {
                    "20": {
                        "spanningTreeVlanInstance": {
                            "protocol": "rstp"
                        }
                    }
                }
            },
        ],
        "inputs": {"mode": "rstp", "template_params": [{"vlan": 10}, {"vlan": 20}]},
        "expected": {"result": "success"},
    },
    {
        "name": "failure-no-instances",
        "eos_data": [
            {
                "spanningTreeVlanInstances": {}
            },
            {
                "spanningTreeVlanInstances": {}
            },
        ],
        "inputs": {"mode": "rstp", "template_params": [{"vlan": 10}, {"vlan": 20}]},
        "expected": {"result": "failure", "messages": ["STP mode 'rstp' not configured for the following VLAN(s): [10, 20]"]}
    },
    {
        "name": "failure-wrong-mode",
        "eos_data": [
            {
                "spanningTreeVlanInstances": {
                    "10": {
                        "spanningTreeVlanInstance": {
                            "protocol": "mstp"
                        }
                    }
                }
            },
            {
                "spanningTreeVlanInstances": {
                    "20": {
                        "spanningTreeVlanInstance": {
                            "protocol": "mstp"
                        }
                    }
                }
            },
        ],
        "inputs": {"mode": "rstp", "template_params": [{"vlan": 10}, {"vlan": 20}]},
        "expected": {"result": "failure", "messages": ["Wrong STP mode configured for the following VLAN(s): [10, 20]"]}
    },
    {
        "name": "failure-both",
        "eos_data": [
            {
                "spanningTreeVlanInstances": {}
            },
            {
                "spanningTreeVlanInstances": {
                    "20": {
                        "spanningTreeVlanInstance": {
                            "protocol": "mstp"
                        }
                    }
                }
            },
        ],
        "inputs": {"mode": "rstp", "template_params": [{"vlan": 10}, {"vlan": 20}]},
        "expected": {"result": "failure"}, "messages": [
            "STP mode 'rstp' not configured for the following VLAN(s): [10]",
            "Wrong STP mode configured for the following VLAN(s): [20]"
            ]
    },
    {
        "name": "error-wrong-mode",
        "eos_data": [
            {
                "spanningTreeVlanInstances": {
                    "10": {
                        "spanningTreeVlanInstance": {
                            "protocol": "rstp"
                        }
                    }
                }
            },
            {
                "spanningTreeVlanInstances": {
                    "20": {
                        "spanningTreeVlanInstance": {
                            "protocol": "rstp"
                        }
                    }
                }
            },
        ],
        "inputs": {"mode": "incompatible_mode", "template_params": [{"vlan": 10}, {"vlan": 20}]},
        "expected": {"result": "error"}, "messages": ["ValueError (Wrong STP mode provided. Valid modes are: ['mstp', 'rstp', 'rapidPvst'])"]
    },
    {
        "name": "error-no-params",
        "eos_data": [
            {
                "spanningTreeVlanInstances": {
                    "10": {
                        "spanningTreeVlanInstance": {
                            "protocol": "rstp"
                        }
                    }
                }
            },
            {
                "spanningTreeVlanInstances": {
                    "20": {
                        "spanningTreeVlanInstance": {
                            "protocol": "rstp"
                        }
                    }
                }
            },
        ],
        "inputs": {"mode": "rstp", "template_params": None},
        "expected": {"result": "error"}, "messages": ["Command has template but no params were given"]
    },
    {
        "name": "error-wrong-params",
        "eos_data": [
            {
                "spanningTreeVlanInstances": {
                    "10": {
                        "spanningTreeVlanInstance": {
                            "protocol": "rstp"
                        }
                    }
                }
            },
            {
                "spanningTreeVlanInstances": {
                    "20": {
                        "spanningTreeVlanInstance": {
                            "protocol": "rstp"
                        }
                    }
                }
            },
        ],
        "inputs": {"mode": "rstp", "template_params": [{'plop': 1}]},
        "expected": {"result": "error"}, "messages": ["Cannot render template 'show spanning-tree vlan {vlan}': wrong parameters"]
    },
    {
        "name": "skipped",
        "eos_data": [
            {
                "spanningTreeVlanInstances": {
                    "10": {
                        "spanningTreeVlanInstance": {
                            "protocol": "rstp"
                        }
                    }
                }
            },
            {
                "spanningTreeVlanInstances": {
                    "20": {
                        "spanningTreeVlanInstance": {
                            "protocol": "rstp"
                        }
                    }
                }
            },
        ],
        "inputs": {"mode": "", "template_params": [{"vlan": 10}, {"vlan": 20}]},
        "expected": {"result":"skipped"}, "messages": ["VerifySTPMode did not run because mode was not supplied"]
    }
]

INPUT_STP_BLOCKED_PORTS: List[Dict[str, Any]] = [
    {
        "name": "success",
        "eos_data": [
            {
                "spanningTreeInstances": {}
            }
        ],
        "inputs": {},
        "expected": {"result": "success"},
    },
    {
        "name": "failure",
        "eos_data": [
            {
                "spanningTreeInstances": {
                    "MST0": {
                        "spanningTreeBlockedPorts": [
                            "Ethernet10"
                        ]
                    },
                    "MST10": {
                        "spanningTreeBlockedPorts": [
                            "Ethernet10"
                        ]
                    }
                }
            }
        ],
        "inputs": {},
        "expected": {"result": "failure", "messages": ["The following ports are blocked by STP: {'MST0': ['Ethernet10'], 'MST10': ['Ethernet10']}"]}
    },
]

INPUT_STP_COUNTERS: List[Dict[str, Any]] = [
    {
        "name": "success",
        "eos_data": [
            {
                "interfaces": {
                    "Ethernet10": {
                        "bpduSent": 99,
                        "bpduReceived": 0,
                        "bpduTaggedError": 0,
                        "bpduOtherError": 0,
                        "bpduRateLimitCount": 0
                    }
                }
            }
        ],
        "inputs": {},
        "expected": {"result": "success"},
    },
    {
        "name": "failure",
        "eos_data": [
            {
                "interfaces": {
                    "Ethernet10": {
                        "bpduSent": 201,
                        "bpduReceived": 0,
                        "bpduTaggedError": 3,
                        "bpduOtherError": 0,
                        "bpduRateLimitCount": 0
                    },
                    "Ethernet11": {
                        "bpduSent": 99,
                        "bpduReceived": 0,
                        "bpduTaggedError": 0,
                        "bpduOtherError": 6,
                        "bpduRateLimitCount": 0
                    }
                }
            }
        ],
        "inputs": {},
        "expected": {"result": "failure", "messages": ["The following interfaces have STP BPDU packet errors: ['Ethernet10', 'Ethernet11']"]}
    },
]

INPUT_STP_FORWARDING_PORTS: List[Dict[str, Any]] = [
    {
        "name": "success",
        "eos_data": [
            {
                "unmappedVlans": [],
                "topologies": {
                    "Mst10": {
                        "vlans": [
                            10
                        ],
                        "interfaces": {
                            "Ethernet10": {
                                "state": "forwarding"
                            },
                            "MplsTrunk1": {
                                "state": "forwarding"
                            }
                        }
                    }
                }
            },
            {
                "unmappedVlans": [],
                "topologies": {
                    "Mst20": {
                        "vlans": [
                            20
                        ],
                        "interfaces": {
                            "Ethernet10": {
                                "state": "forwarding"
                            },
                            "MplsTrunk1": {
                                "state": "forwarding"
                            }
                        }
                    }
                }
            },
        ],
        "inputs": {"template_params": [{"vlan": 10}, {"vlan": 20}]},
        "expected": {"result": "success"},
    },
    {
        "name": "failure-no-instances",
        "eos_data": [
            {
                "unmappedVlans": [],
                "topologies": {}
            },
            {
                "unmappedVlans": [],
                "topologies": {}
            }
        ],
        "inputs": {"template_params": [{"vlan": 10}, {"vlan": 20}]},
        "expected": {"result": "failure", "messages": ["STP instance is not configured for the following VLAN(s): [10, 20]"]}
    },
    {
        "name": "failure",
        "eos_data": [
            {
                "unmappedVlans": [],
                "topologies": {
                    "Vl10": {
                        "vlans": [
                            10
                        ],
                        "interfaces": {
                            "Ethernet10": {
                                "state": "discarding"
                            },
                            "MplsTrunk1": {
                                "state": "forwarding"
                            }
                        }
                    }
                }
            },
            {
                "unmappedVlans": [],
                "topologies": {
                    "Vl20": {
                        "vlans": [
                            20
                        ],
                        "interfaces": {
                            "Ethernet10": {
                                "state": "discarding"
                            },
                            "MplsTrunk1": {
                                "state": "forwarding"
                            }
                        }
                    }
                }
            }
        ],
        "inputs": {"template_params": [{"vlan": 10}, {"vlan": 20}]},
        "expected": {"result": "failure"}, "messages": ["The following VLAN(s) have interface(s) that are not in a fowarding state: "
                              "[{'VLAN 10': ['Ethernet10']}, {'VLAN 20': ['Ethernet10']}]"]
    },
    {
        "name": "error-no-params",
        "eos_data": [
            {
                "unmappedVlans": [],
                "topologies": {
                    "Mst10": {
                        "vlans": [
                            10
                        ],
                        "interfaces": {
                            "Ethernet10": {
                                "state": "forwarding"
                            },
                            "MplsTrunk1": {
                                "state": "forwarding"
                            }
                        }
                    }
                }
            },
            {
                "unmappedVlans": [],
                "topologies": {
                    "Mst20": {
                        "vlans": [
                            20
                        ],
                        "interfaces": {
                            "Ethernet10": {
                                "state": "forwarding"
                            },
                            "MplsTrunk1": {
                                "state": "forwarding"
                            }
                        }
                    }
                }
            },
        ],
        "inputs": {"template_params": None},
        "expected": {"result": "error"}, "messages": ["Command has template but no params were given"]
    },
    {
        "name": "error-wrong-params",
        "eos_data": [
            {
                "unmappedVlans": [],
                "topologies": {
                    "Mst10": {
                        "vlans": [
                            10
                        ],
                        "interfaces": {
                            "Ethernet10": {
                                "state": "forwarding"
                            },
                            "MplsTrunk1": {
                                "state": "forwarding"
                            }
                        }
                    }
                }
            },
            {
                "unmappedVlans": [],
                "topologies": {
                    "Mst20": {
                        "vlans": [
                            20
                        ],
                        "interfaces": {
                            "Ethernet10": {
                                "state": "forwarding"
                            },
                            "MplsTrunk1": {
                                "state": "forwarding"
                            }
                        }
                    }
                }
            },
        ],
        "inputs": {"template_params": [{"wrong": 10}, {"wrong": 20}]},
        "expected": {"result": "error"}, "messages": ["Cannot render template 'show spanning-tree topology vlan {vlan} status': wrong parameters"]
    }
]

INPUT_STP_ROOT_PRIORITY: List[Dict[str, Any]] = [
    {
        "name": "success-specific-instances",
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
                            "forwardDelay": 15
                        }
                    },
                    "VL20": {
                        "rootBridge": {
                            "priority": 32768,
                            "systemIdExtension": 20,
                            "macAddress": "00:1c:73:27:95:a2",
                            "helloTime": 2.0,
                            "maxAge": 20,
                            "forwardDelay": 15
                        }
                    },
                    "VL30": {
                        "rootBridge": {
                            "priority": 32768,
                            "systemIdExtension": 30,
                            "macAddress": "00:1c:73:27:95:a2",
                            "helloTime": 2.0,
                            "maxAge": 20,
                            "forwardDelay": 15
                        }
                    }
                }
            }
        ],
        "inputs": {"priority": 32768, "instances": [10, 20]},
        "expected": {"result": "success"},
    },
    {
        "name": "success-all-instances",
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
                            "forwardDelay": 15
                        }
                    },
                    "VL20": {
                        "rootBridge": {
                            "priority": 32768,
                            "systemIdExtension": 20,
                            "macAddress": "00:1c:73:27:95:a2",
                            "helloTime": 2.0,
                            "maxAge": 20,
                            "forwardDelay": 15
                        }
                    },
                    "VL30": {
                        "rootBridge": {
                            "priority": 32768,
                            "systemIdExtension": 30,
                            "macAddress": "00:1c:73:27:95:a2",
                            "helloTime": 2.0,
                            "maxAge": 20,
                            "forwardDelay": 15
                        }
                    }
                }
            }
        ],
        "inputs": {"priority": 32768, "instances": None},
        "expected": {"result": "success"},
    },
    {
        "name": "failure-no-instances",
        "eos_data": [
            {
                "instances": {}
            }
        ],
        "inputs": {"priority": 32768, "instances": [10, 20]},
        "expected": {"result": "failure", "messages": ["No STP instances configured"]}
    },
    {
        "name": "failure-wrong-priority",
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
                            "forwardDelay": 15
                        }
                    },
                    "VL20": {
                        "rootBridge": {
                            "priority": 8196,
                            "systemIdExtension": 20,
                            "macAddress": "00:1c:73:27:95:a2",
                            "helloTime": 2.0,
                            "maxAge": 20,
                            "forwardDelay": 15
                        }
                    },
                    "VL30": {
                        "rootBridge": {
                            "priority": 8196,
                            "systemIdExtension": 30,
                            "macAddress": "00:1c:73:27:95:a2",
                            "helloTime": 2.0,
                            "maxAge": 20,
                            "forwardDelay": 15
                        }
                    }
                }
            }
        ],
        "inputs": {"priority": 32768, "instances": [10, 20, 30]},
        "expected": {"result": "failure", "messages": ["The following instance(s) have the wrong STP root priority configured: ['VL20', 'VL30']"]}
    },
    {
        "name": "skipped",
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
                            "forwardDelay": 15
                        }
                    },
                    "VL20": {
                        "rootBridge": {
                            "priority": 32768,
                            "systemIdExtension": 20,
                            "macAddress": "00:1c:73:27:95:a2",
                            "helloTime": 2.0,
                            "maxAge": 20,
                            "forwardDelay": 15
                        }
                    },
                    "VL30": {
                        "rootBridge": {
                            "priority": 32768,
                            "systemIdExtension": 30,
                            "macAddress": "00:1c:73:27:95:a2",
                            "helloTime": 2.0,
                            "maxAge": 20,
                            "forwardDelay": 15
                        }
                    }
                }
            }
        ],
        "inputs": {"priority": None, "instances": [10, 20, 30]},
        "expected": {"result":"skipped"}, "messages": ["VerifySTPRootPriority did not run because priority was not supplied"]
    },
]
