# Copyright (c) 2023-2024 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Tests for anta.tests.avt.py."""

from __future__ import annotations

from typing import Any

from anta.tests.avt import VerifyAVTPathHealth, VerifyAVTRole, VerifyAVTSpecificPath
from tests.units.anta_tests import test

DATA: list[dict[str, Any]] = [
    {
        "name": "success",
        "test": VerifyAVTPathHealth,
        "eos_data": [
            {
                "vrfs": {
                    "data": {
                        "avts": {
                            "DATA-AVT-POLICY-DEFAULT": {
                                "avtPaths": {
                                    "direct:9": {
                                        "flags": {"directPath": True, "valid": True, "active": True},
                                    },
                                    "direct:10": {
                                        "flags": {"directPath": True, "valid": True, "active": True},
                                    },
                                    "direct:1": {
                                        "flags": {"directPath": True, "valid": True, "active": True},
                                    },
                                    "direct:8": {
                                        "flags": {"directPath": True, "valid": True, "active": True},
                                    },
                                }
                            }
                        }
                    },
                    "guest": {
                        "avts": {
                            "GUEST-AVT-POLICY-DEFAULT": {
                                "avtPaths": {
                                    "direct:10": {
                                        "flags": {"directPath": True, "valid": True, "active": True},
                                    },
                                    "direct:8": {
                                        "flags": {"directPath": True, "valid": True, "active": True},
                                    },
                                }
                            }
                        }
                    },
                    "default": {
                        "avts": {
                            "CONTROL-PLANE-PROFILE": {
                                "avtPaths": {
                                    "direct:9": {
                                        "flags": {"directPath": True, "valid": True, "active": True},
                                    },
                                    "direct:10": {
                                        "flags": {"directPath": True, "valid": True, "active": True},
                                    },
                                    "direct:1": {
                                        "flags": {"directPath": True, "valid": True, "active": True},
                                    },
                                    "direct:8": {
                                        "flags": {"directPath": True, "valid": True, "active": True},
                                    },
                                }
                            },
                            "DEFAULT-AVT-POLICY-DEFAULT": {
                                "avtPaths": {
                                    "direct:10": {
                                        "flags": {"directPath": True, "valid": True, "active": True},
                                    },
                                    "direct:8": {
                                        "flags": {"directPath": True, "valid": True, "active": True},
                                    },
                                }
                            },
                        }
                    },
                }
            }
        ],
        "inputs": {},
        "expected": {"result": "success"},
    },
    {
        "name": "failure-avt-not-configured",
        "test": VerifyAVTPathHealth,
        "eos_data": [{"vrfs": {}}],
        "inputs": {},
        "expected": {
            "result": "failure",
            "messages": ["Adaptive virtual topology paths are not configured."],
        },
    },
    {
        "name": "failure-not-active-path",
        "test": VerifyAVTPathHealth,
        "eos_data": [
            {
                "vrfs": {
                    "data": {
                        "avts": {
                            "DATA-AVT-POLICY-DEFAULT": {
                                "avtPaths": {
                                    "direct:9": {
                                        "flags": {"directPath": True, "valid": True, "active": True},
                                    },
                                    "direct:10": {
                                        "flags": {"directPath": True, "valid": True, "active": True},
                                    },
                                    "direct:1": {
                                        "flags": {"directPath": True, "valid": True, "active": True},
                                    },
                                    "direct:8": {
                                        "flags": {"directPath": True, "valid": True, "active": True},
                                    },
                                }
                            }
                        }
                    },
                    "guest": {
                        "avts": {
                            "GUEST-AVT-POLICY-DEFAULT": {
                                "avtPaths": {
                                    "direct:10": {
                                        "flags": {"directPath": True, "valid": True, "active": False},
                                    },
                                    "direct:8": {
                                        "flags": {"directPath": True, "valid": True, "active": True},
                                    },
                                }
                            }
                        }
                    },
                    "default": {
                        "avts": {
                            "CONTROL-PLANE-PROFILE": {
                                "avtPaths": {
                                    "direct:9": {
                                        "flags": {"directPath": True, "valid": True, "active": True},
                                    },
                                    "direct:10": {
                                        "flags": {"directPath": True, "valid": True, "active": True},
                                    },
                                    "direct:1": {
                                        "flags": {"directPath": True, "valid": True, "active": False},
                                    },
                                    "direct:8": {
                                        "flags": {"directPath": True, "valid": True, "active": True},
                                    },
                                }
                            },
                            "DEFAULT-AVT-POLICY-DEFAULT": {
                                "avtPaths": {
                                    "direct:10": {
                                        "flags": {"directPath": True, "valid": True, "active": False},
                                    },
                                    "direct:8": {
                                        "flags": {"directPath": True, "valid": True, "active": True},
                                    },
                                }
                            },
                        }
                    },
                }
            }
        ],
        "inputs": {},
        "expected": {
            "result": "failure",
            "messages": [
                "AVT path direct:10 for profile GUEST-AVT-POLICY-DEFAULT in VRF guest is not active.",
                "AVT path direct:1 for profile CONTROL-PLANE-PROFILE in VRF default is not active.",
                "AVT path direct:10 for profile DEFAULT-AVT-POLICY-DEFAULT in VRF default is not active.",
            ],
        },
    },
    {
        "name": "failure-invalid-path",
        "test": VerifyAVTPathHealth,
        "eos_data": [
            {
                "vrfs": {
                    "data": {
                        "avts": {
                            "DATA-AVT-POLICY-DEFAULT": {
                                "avtPaths": {
                                    "direct:9": {
                                        "flags": {"directPath": True, "valid": True, "active": True},
                                    },
                                    "direct:10": {
                                        "flags": {"directPath": True, "valid": False, "active": True},
                                    },
                                    "direct:1": {
                                        "flags": {"directPath": True, "valid": True, "active": True},
                                    },
                                    "direct:8": {
                                        "flags": {"directPath": True, "valid": True, "active": True},
                                    },
                                }
                            }
                        }
                    },
                    "guest": {
                        "avts": {
                            "GUEST-AVT-POLICY-DEFAULT": {
                                "avtPaths": {
                                    "direct:10": {
                                        "flags": {"directPath": True, "valid": True, "active": True},
                                    },
                                    "direct:8": {
                                        "flags": {"directPath": True, "valid": False, "active": True},
                                    },
                                }
                            }
                        }
                    },
                    "default": {
                        "avts": {
                            "CONTROL-PLANE-PROFILE": {
                                "avtPaths": {
                                    "direct:9": {
                                        "flags": {"directPath": True, "valid": True, "active": True},
                                    },
                                    "direct:10": {
                                        "flags": {"directPath": True, "valid": False, "active": True},
                                    },
                                    "direct:1": {
                                        "flags": {"directPath": True, "valid": True, "active": True},
                                    },
                                    "direct:8": {
                                        "flags": {"directPath": True, "valid": True, "active": True},
                                    },
                                }
                            },
                            "DEFAULT-AVT-POLICY-DEFAULT": {
                                "avtPaths": {
                                    "direct:10": {
                                        "flags": {"directPath": True, "valid": True, "active": True},
                                    },
                                    "direct:8": {
                                        "flags": {"directPath": True, "valid": False, "active": True},
                                    },
                                }
                            },
                        }
                    },
                }
            }
        ],
        "inputs": {},
        "expected": {
            "result": "failure",
            "messages": [
                "AVT path direct:10 for profile DATA-AVT-POLICY-DEFAULT in VRF data is invalid.",
                "AVT path direct:8 for profile GUEST-AVT-POLICY-DEFAULT in VRF guest is invalid.",
                "AVT path direct:10 for profile CONTROL-PLANE-PROFILE in VRF default is invalid.",
                "AVT path direct:8 for profile DEFAULT-AVT-POLICY-DEFAULT in VRF default is invalid.",
            ],
        },
    },
    {
        "name": "failure-not-active-and-invalid",
        "test": VerifyAVTPathHealth,
        "eos_data": [
            {
                "vrfs": {
                    "data": {
                        "avts": {
                            "DATA-AVT-POLICY-DEFAULT": {
                                "avtPaths": {
                                    "direct:9": {
                                        "flags": {"directPath": True, "valid": True, "active": True},
                                    },
                                    "direct:10": {
                                        "flags": {"directPath": True, "valid": False, "active": False},
                                    },
                                    "direct:1": {
                                        "flags": {"directPath": True, "valid": True, "active": False},
                                    },
                                    "direct:8": {
                                        "flags": {"directPath": True, "valid": True, "active": True},
                                    },
                                }
                            }
                        }
                    },
                    "guest": {
                        "avts": {
                            "GUEST-AVT-POLICY-DEFAULT": {
                                "avtPaths": {
                                    "direct:10": {
                                        "flags": {"directPath": True, "valid": False, "active": True},
                                    },
                                    "direct:8": {
                                        "flags": {"directPath": True, "valid": False, "active": False},
                                    },
                                }
                            }
                        }
                    },
                    "default": {
                        "avts": {
                            "CONTROL-PLANE-PROFILE": {
                                "avtPaths": {
                                    "direct:9": {
                                        "flags": {"directPath": True, "valid": True, "active": True},
                                    },
                                    "direct:10": {
                                        "flags": {"directPath": True, "valid": False, "active": False},
                                    },
                                    "direct:1": {
                                        "flags": {"directPath": True, "valid": True, "active": True},
                                    },
                                    "direct:8": {
                                        "flags": {"directPath": True, "valid": True, "active": True},
                                    },
                                }
                            },
                            "DEFAULT-AVT-POLICY-DEFAULT": {
                                "avtPaths": {
                                    "direct:10": {
                                        "flags": {"directPath": True, "valid": True, "active": False},
                                    },
                                    "direct:8": {
                                        "flags": {"directPath": True, "valid": False, "active": False},
                                    },
                                }
                            },
                        }
                    },
                }
            }
        ],
        "inputs": {},
        "expected": {
            "result": "failure",
            "messages": [
                "AVT path direct:10 for profile DATA-AVT-POLICY-DEFAULT in VRF data is invalid and not active.",
                "AVT path direct:1 for profile DATA-AVT-POLICY-DEFAULT in VRF data is not active.",
                "AVT path direct:10 for profile GUEST-AVT-POLICY-DEFAULT in VRF guest is invalid.",
                "AVT path direct:8 for profile GUEST-AVT-POLICY-DEFAULT in VRF guest is invalid and not active.",
                "AVT path direct:10 for profile CONTROL-PLANE-PROFILE in VRF default is invalid and not active.",
                "AVT path direct:10 for profile DEFAULT-AVT-POLICY-DEFAULT in VRF default is not active.",
                "AVT path direct:8 for profile DEFAULT-AVT-POLICY-DEFAULT in VRF default is invalid and not active.",
            ],
        },
    },
    {
        "name": "success",
        "test": VerifyAVTSpecificPath,
        "eos_data": [
            {
                "vrfs": {
                    "default": {
                        "avts": {
                            "DEFAULT-AVT-POLICY-CONTROL-PLANE": {
                                "avtPaths": {
                                    "direct:10": {
                                        "flags": {"directPath": True, "valid": True, "active": True},
                                        "nexthopAddr": "10.101.255.1",
                                        "destination": "10.101.255.2",
                                    },
                                    "direct:9": {
                                        "flags": {"directPath": True, "valid": True, "active": True},
                                        "nexthopAddr": "10.101.255.1",
                                        "destination": "10.101.255.2",
                                    },
                                    "multihop:1": {
                                        "flags": {"directPath": False, "valid": True, "active": True},
                                        "nexthopAddr": "10.101.255.1",
                                        "destination": "10.101.255.2",
                                    },
                                    "multihop:3": {
                                        "flags": {"directPath": False, "valid": True, "active": True},
                                        "nexthopAddr": "10.101.255.1",
                                        "destination": "10.101.255.2",
                                    },
                                }
                            }
                        },
                    },
                    "data": {
                        "avts": {
                            "DATA-AVT-POLICY-CONTROL-PLANE": {
                                "avtPaths": {
                                    "direct:10": {
                                        "flags": {"directPath": True, "valid": True, "active": True},
                                        "nexthopAddr": "10.101.255.1",
                                        "destination": "10.101.255.1",
                                    },
                                    "direct:9": {
                                        "flags": {"directPath": True, "valid": True, "active": True},
                                        "nexthopAddr": "10.101.255.1",
                                        "destination": "10.101.255.1",
                                    },
                                    "direct:8": {
                                        "flags": {"directPath": True, "valid": True, "active": True},
                                        "nexthopAddr": "10.101.255.2",
                                        "destination": "10.101.255.1",
                                    },
                                    "multihop:1": {
                                        "flags": {"directPath": False, "valid": True, "active": True},
                                        "nexthopAddr": "10.101.255.2",
                                        "destination": "10.101.255.1",
                                    },
                                    "multihop:3": {
                                        "flags": {"directPath": False, "valid": True, "active": True},
                                        "nexthopAddr": "10.101.255.2",
                                        "destination": "10.101.255.1",
                                    },
                                }
                            },
                        }
                    },
                }
            },
        ],
        "inputs": {
            "avt_paths": [
                {"avt_name": "DEFAULT-AVT-POLICY-CONTROL-PLANE", "destination": "10.101.255.2", "next_hop": "10.101.255.1", "path_type": "multihop"},
                {"avt_name": "DATA-AVT-POLICY-CONTROL-PLANE", "vrf": "data", "destination": "10.101.255.1", "next_hop": "10.101.255.2", "path_type": "direct"},
                {"avt_name": "DATA-AVT-POLICY-CONTROL-PLANE", "vrf": "data", "destination": "10.101.255.1", "next_hop": "10.101.255.2"},
            ]
        },
        "expected": {"result": "success"},
    },
    {
        "name": "failure-no-peer",
        "test": VerifyAVTSpecificPath,
        "eos_data": [
            {"vrfs": {}},
        ],
        "inputs": {
            "avt_paths": [
                {"avt_name": "MGMT-AVT-POLICY-DEFAULT", "vrf": "default", "destination": "10.101.255.2", "next_hop": "10.101.255.1", "path_type": "multihop"},
                {"avt_name": "DATA-AVT-POLICY-CONTROL-PLANE", "vrf": "data", "destination": "10.101.255.1", "next_hop": "10.101.255.2", "path_type": "multihop"},
            ]
        },
        "expected": {
            "result": "failure",
            "messages": ["AVT MGMT-AVT-POLICY-DEFAULT VRF: default (Destination: 10.101.255.2, Next-hop: 10.101.255.1) - No AVT path configured"],
        },
    },
    {
        "name": "failure-path_type_check_true",
        "test": VerifyAVTSpecificPath,
        "eos_data": [
            {
                "vrfs": {
                    "default": {
                        "avts": {
                            "DEFAULT-AVT-POLICY-CONTROL-PLANE": {
                                "avtPaths": {
                                    "direct:10": {
                                        "flags": {"directPath": True, "valid": True, "active": True},
                                        "nexthopAddr": "10.101.255.1",
                                        "destination": "10.101.255.2",
                                    },
                                    "direct:9": {
                                        "flags": {"directPath": True, "valid": True, "active": True},
                                        "nexthopAddr": "10.101.255.1",
                                        "destination": "10.101.255.2",
                                    },
                                }
                            }
                        },
                    },
                    "data": {
                        "avts": {
                            "DATA-AVT-POLICY-CONTROL-PLANE": {
                                "avtPaths": {
                                    "direct:10": {
                                        "flags": {"directPath": True, "valid": True, "active": True},
                                        "nexthopAddr": "10.101.255.1",
                                        "destination": "10.101.255.3",
                                    },
                                    "direct:9": {
                                        "flags": {"directPath": True, "valid": True, "active": True},
                                        "nexthopAddr": "10.101.255.1",
                                        "destination": "10.101.255.3",
                                    },
                                }
                            },
                        }
                    },
                }
            },
        ],
        "inputs": {
            "avt_paths": [
                {
                    "avt_name": "DEFAULT-AVT-POLICY-CONTROL-PLANE",
                    "vrf": "default",
                    "destination": "10.101.255.2",
                    "next_hop": "10.101.255.11",
                    "path_type": "multihop",
                },
                {"avt_name": "DATA-AVT-POLICY-CONTROL-PLANE", "vrf": "data", "destination": "10.101.255.1", "next_hop": "10.101.255.21", "path_type": "direct"},
            ]
        },
        "expected": {
            "result": "failure",
            "messages": [
                "AVT DEFAULT-AVT-POLICY-CONTROL-PLANE VRF: default (Destination: 10.101.255.2, Next-hop: 10.101.255.11) Path Type: multihop - Path not found",
                "AVT DATA-AVT-POLICY-CONTROL-PLANE VRF: data (Destination: 10.101.255.1, Next-hop: 10.101.255.21) Path Type: direct - Path not found",
            ],
        },
    },
    {
        "name": "failure-path_type_check_false",
        "test": VerifyAVTSpecificPath,
        "eos_data": [
            {
                "vrfs": {
                    "default": {
                        "avts": {
                            "DEFAULT-AVT-POLICY-CONTROL-PLANE": {
                                "avtPaths": {
                                    "direct:10": {
                                        "flags": {"directPath": True, "valid": True, "active": True},
                                        "nexthopAddr": "10.101.255.1",
                                        "destination": "10.101.255.2",
                                    },
                                    "direct:9": {
                                        "flags": {"directPath": True, "valid": True, "active": True},
                                        "nexthopAddr": "10.101.255.1",
                                        "destination": "10.101.255.2",
                                    },
                                }
                            }
                        },
                    },
                    "data": {
                        "avts": {
                            "DATA-AVT-POLICY-CONTROL-PLANE": {
                                "avtPaths": {
                                    "direct:10": {
                                        "flags": {"directPath": True, "valid": True, "active": True},
                                        "nexthopAddr": "10.101.255.1",
                                        "destination": "10.101.255.3",
                                    },
                                    "direct:9": {
                                        "flags": {"directPath": True, "valid": True, "active": True},
                                        "nexthopAddr": "10.101.255.1",
                                        "destination": "10.101.255.3",
                                    },
                                }
                            },
                        }
                    },
                }
            },
        ],
        "inputs": {
            "avt_paths": [
                {
                    "avt_name": "DEFAULT-AVT-POLICY-CONTROL-PLANE",
                    "vrf": "default",
                    "destination": "10.101.255.2",
                    "next_hop": "10.101.255.11",
                },
                {"avt_name": "DATA-AVT-POLICY-CONTROL-PLANE", "vrf": "data", "destination": "10.101.255.1", "next_hop": "10.101.255.21"},
            ]
        },
        "expected": {
            "result": "failure",
            "messages": [
                "AVT DEFAULT-AVT-POLICY-CONTROL-PLANE VRF: default (Destination: 10.101.255.2, Next-hop: 10.101.255.11) - Path not found",
                "AVT DATA-AVT-POLICY-CONTROL-PLANE VRF: data (Destination: 10.101.255.1, Next-hop: 10.101.255.21) - Path not found",
            ],
        },
    },
    {
        "name": "failure-incorrect-path",
        "test": VerifyAVTSpecificPath,
        "eos_data": [
            {
                "vrfs": {
                    "default": {
                        "avts": {
                            "DEFAULT-AVT-POLICY-CONTROL-PLANE": {
                                "avtPaths": {
                                    "multihop:3": {
                                        "flags": {"directPath": False, "valid": False, "active": True},
                                        "nexthopAddr": "10.101.255.1",
                                        "destination": "10.101.255.2",
                                    },
                                }
                            }
                        },
                    },
                    "data": {
                        "avts": {
                            "DATA-AVT-POLICY-CONTROL-PLANE": {
                                "avtPaths": {
                                    "direct:10": {
                                        "flags": {"directPath": True, "valid": False, "active": True},
                                        "nexthopAddr": "10.101.255.1",
                                        "destination": "10.101.255.1",
                                    },
                                    "direct:9": {
                                        "flags": {"directPath": True, "valid": True, "active": False},
                                        "nexthopAddr": "10.101.255.1",
                                        "destination": "10.101.255.1",
                                    },
                                    "direct:8": {
                                        "flags": {"directPath": True, "valid": False, "active": False},
                                        "nexthopAddr": "10.101.255.2",
                                        "destination": "10.101.255.1",
                                    },
                                    "multihop:1": {
                                        "flags": {"directPath": False, "valid": True, "active": True},
                                        "nexthopAddr": "10.101.255.2",
                                        "destination": "10.101.255.1",
                                    },
                                    "multihop:3": {
                                        "flags": {"directPath": False, "valid": True, "active": True},
                                        "nexthopAddr": "10.101.255.2",
                                        "destination": "10.101.255.1",
                                    },
                                }
                            },
                        }
                    },
                }
            },
        ],
        "inputs": {
            "avt_paths": [
                {
                    "avt_name": "DEFAULT-AVT-POLICY-CONTROL-PLANE",
                    "vrf": "default",
                    "destination": "10.101.255.2",
                    "next_hop": "10.101.255.1",
                    "path_type": "multihop",
                },
                {"avt_name": "DATA-AVT-POLICY-CONTROL-PLANE", "vrf": "data", "destination": "10.101.255.1", "next_hop": "10.101.255.1", "path_type": "direct"},
            ]
        },
        "expected": {
            "result": "failure",
            "messages": [
                "AVT DEFAULT-AVT-POLICY-CONTROL-PLANE VRF: default (Destination: 10.101.255.2, Next-hop: 10.101.255.1) - "
                "Incorrect path multihop:3 - Valid: False, Active: True",
                "AVT DATA-AVT-POLICY-CONTROL-PLANE VRF: data (Destination: 10.101.255.1, Next-hop: 10.101.255.1) - "
                "Incorrect path direct:10 - Valid: False, Active: True",
                "AVT DATA-AVT-POLICY-CONTROL-PLANE VRF: data (Destination: 10.101.255.1, Next-hop: 10.101.255.1) - "
                "Incorrect path direct:9 - Valid: True, Active: False",
            ],
        },
    },
    {
        "name": "success",
        "test": VerifyAVTRole,
        "eos_data": [{"role": "edge"}],
        "inputs": {"role": "edge"},
        "expected": {"result": "success"},
    },
    {
        "name": "failure-incorrect-role",
        "test": VerifyAVTRole,
        "eos_data": [{"role": "transit"}],
        "inputs": {"role": "edge"},
        "expected": {"result": "failure", "messages": ["Expected AVT role as `edge`, but found `transit` instead."]},
    },
]
