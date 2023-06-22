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
        "side_effect": {"mode": "rstp", "template_params": [{"vlan": 10}, {"vlan": 20}]},
        "expected_result": "success",
        "expected_messages": []
    },
    {
        "name": "failure",
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
        "side_effect": {"mode": "rstp", "template_params": [{"vlan": 10}, {"vlan": 20}]},
        "expected_result": "failure",
        "expected_messages": ["Wrong STP mode configured for VLAN 10", "Wrong STP mode configured for VLAN 20"]
    },
    {
        "name": "error",
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
        "side_effect": {"mode": "incompatible_mode", "template_params": [{"vlan": 10}, {"vlan": 20}]},
        "expected_result": "error",
        "expected_messages": ["ValueError (Wrong STP mode provided. Valid modes are: ['mstp', 'rstp', 'rapidPvst'])"]
    },
    {
        "name": "error",
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
        "side_effect": {"mode": "rstp", "template_params": None},
        "expected_result": "error",
        "expected_messages": ["Command has template but no params were given"]
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
        "side_effect": {"mode": "", "template_params": [{"vlan": 10}, {"vlan": 20}]},
        "expected_result": "skipped",
        "expected_messages": ["VerifySTPMode did not run because mode was not supplied"]
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
        "side_effect": {},
        "expected_result": "success",
        "expected_messages": []
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
        "side_effect": {},
        "expected_result": "failure",
        "expected_messages": ["The following ports are blocked by STP: {'MST0': ['Ethernet10'], 'MST10': ['Ethernet10']}"]
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
        "side_effect": {},
        "expected_result": "success",
        "expected_messages": []
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
        "side_effect": {},
        "expected_result": "failure",
        "expected_messages": ["The following interfaces have STP BPDU packet errors: ['Ethernet10', 'Ethernet11']"]
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
        "side_effect": {"template_params": [{"vlan": 10}, {"vlan": 20}]},
        "expected_result": "success",
        "expected_messages": []
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
        "side_effect": {"template_params": [{"vlan": 10}, {"vlan": 20}]},
        "expected_result": "failure",
        "expected_messages": ["The following interface(s) are not in a forwarding state for VLAN 10: ['Ethernet10']",
                              "The following interface(s) are not in a forwarding state for VLAN 20: ['Ethernet10']"]
    },
    {
        "name": "error",
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
        "side_effect": {"template_params": None},
        "expected_result": "error",
        "expected_messages": ["Command has template but no params were given"]
    }
]
