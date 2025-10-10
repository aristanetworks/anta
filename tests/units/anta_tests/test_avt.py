# Copyright (c) 2023-2025 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Tests for anta.tests.avt.py."""

from __future__ import annotations

import sys
from typing import TYPE_CHECKING, Any

from anta.models import AntaTest
from anta.result_manager.models import AntaTestStatus
from anta.tests.avt import VerifyAVTPathHealth, VerifyAVTRole, VerifyAVTSpecificPath
from tests.units.anta_tests import test

if TYPE_CHECKING:
    from tests.units.anta_tests import AntaUnitTestData

DATA: AntaUnitTestData = {
    (VerifyAVTPathHealth, "success"): {
        "eos_data": [
            {
                "vrfs": {
                    "data": {
                        "avts": {
                            "DATA-AVT-POLICY-DEFAULT": {
                                "avtPaths": {
                                    "direct:9": {"flags": {"directPath": True, "valid": True, "active": True}},
                                    "direct:10": {"flags": {"directPath": True, "valid": True, "active": True}},
                                    "direct:1": {"flags": {"directPath": True, "valid": True, "active": True}},
                                    "direct:8": {"flags": {"directPath": True, "valid": True, "active": True}},
                                }
                            }
                        }
                    },
                    "guest": {
                        "avts": {
                            "GUEST-AVT-POLICY-DEFAULT": {
                                "avtPaths": {
                                    "direct:10": {"flags": {"directPath": True, "valid": True, "active": True}},
                                    "direct:8": {"flags": {"directPath": True, "valid": True, "active": True}},
                                }
                            }
                        }
                    },
                    "default": {
                        "avts": {
                            "CONTROL-PLANE-PROFILE": {
                                "avtPaths": {
                                    "direct:9": {"flags": {"directPath": True, "valid": True, "active": True}},
                                    "direct:10": {"flags": {"directPath": True, "valid": True, "active": True}},
                                    "direct:1": {"flags": {"directPath": True, "valid": True, "active": True}},
                                    "direct:8": {"flags": {"directPath": True, "valid": True, "active": True}},
                                }
                            },
                            "DEFAULT-AVT-POLICY-DEFAULT": {
                                "avtPaths": {
                                    "direct:10": {"flags": {"directPath": True, "valid": True, "active": True}},
                                    "direct:8": {"flags": {"directPath": True, "valid": True, "active": True}},
                                }
                            },
                        }
                    },
                }
            }
        ],
        "inputs": {},
        "expected": {"result": AntaTestStatus.SUCCESS},
    },
    (VerifyAVTPathHealth, "failure-avt-not-configured"): {
        "eos_data": [{"vrfs": {}}],
        "inputs": {},
        "expected": {"result": AntaTestStatus.FAILURE, "messages": ["Adaptive virtual topology paths are not configured"]},
    },
    (VerifyAVTPathHealth, "failure-not-active-path"): {
        "eos_data": [
            {
                "vrfs": {
                    "data": {
                        "avts": {
                            "DATA-AVT-POLICY-DEFAULT": {
                                "avtPaths": {
                                    "direct:9": {"flags": {"directPath": True, "valid": True, "active": True}},
                                    "direct:10": {"flags": {"directPath": True, "valid": True, "active": True}},
                                    "direct:1": {"flags": {"directPath": True, "valid": True, "active": True}},
                                    "direct:8": {"flags": {"directPath": True, "valid": True, "active": True}},
                                }
                            }
                        }
                    },
                    "guest": {
                        "avts": {
                            "GUEST-AVT-POLICY-DEFAULT": {
                                "avtPaths": {
                                    "direct:10": {"flags": {"directPath": True, "valid": True, "active": False}},
                                    "direct:8": {"flags": {"directPath": True, "valid": True, "active": True}},
                                }
                            }
                        }
                    },
                    "default": {
                        "avts": {
                            "CONTROL-PLANE-PROFILE": {
                                "avtPaths": {
                                    "direct:9": {"flags": {"directPath": True, "valid": True, "active": True}},
                                    "direct:10": {"flags": {"directPath": True, "valid": True, "active": True}},
                                    "direct:1": {"flags": {"directPath": True, "valid": True, "active": False}},
                                    "direct:8": {"flags": {"directPath": True, "valid": True, "active": True}},
                                }
                            },
                            "DEFAULT-AVT-POLICY-DEFAULT": {
                                "avtPaths": {
                                    "direct:10": {"flags": {"directPath": True, "valid": True, "active": False}},
                                    "direct:8": {"flags": {"directPath": True, "valid": True, "active": True}},
                                }
                            },
                        }
                    },
                }
            }
        ],
        "inputs": {},
        "expected": {
            "result": AntaTestStatus.FAILURE,
            "messages": [
                "VRF: guest Profile: GUEST-AVT-POLICY-DEFAULT AVT path: direct:10 - Not active",
                "VRF: default Profile: CONTROL-PLANE-PROFILE AVT path: direct:1 - Not active",
                "VRF: default Profile: DEFAULT-AVT-POLICY-DEFAULT AVT path: direct:10 - Not active",
            ],
        },
    },
    (VerifyAVTPathHealth, "failure-invalid-path"): {
        "eos_data": [
            {
                "vrfs": {
                    "data": {
                        "avts": {
                            "DATA-AVT-POLICY-DEFAULT": {
                                "avtPaths": {
                                    "direct:9": {"flags": {"directPath": True, "valid": True, "active": True}},
                                    "direct:10": {"flags": {"directPath": True, "valid": False, "active": True}},
                                    "direct:1": {"flags": {"directPath": True, "valid": True, "active": True}},
                                    "direct:8": {"flags": {"directPath": True, "valid": True, "active": True}},
                                }
                            }
                        }
                    },
                    "guest": {
                        "avts": {
                            "GUEST-AVT-POLICY-DEFAULT": {
                                "avtPaths": {
                                    "direct:10": {"flags": {"directPath": True, "valid": True, "active": True}},
                                    "direct:8": {"flags": {"directPath": True, "valid": False, "active": True}},
                                }
                            }
                        }
                    },
                    "default": {
                        "avts": {
                            "CONTROL-PLANE-PROFILE": {
                                "avtPaths": {
                                    "direct:9": {"flags": {"directPath": True, "valid": True, "active": True}},
                                    "direct:10": {"flags": {"directPath": True, "valid": False, "active": True}},
                                    "direct:1": {"flags": {"directPath": True, "valid": True, "active": True}},
                                    "direct:8": {"flags": {"directPath": True, "valid": True, "active": True}},
                                }
                            },
                            "DEFAULT-AVT-POLICY-DEFAULT": {
                                "avtPaths": {
                                    "direct:10": {"flags": {"directPath": True, "valid": True, "active": True}},
                                    "direct:8": {"flags": {"directPath": True, "valid": False, "active": True}},
                                }
                            },
                        }
                    },
                }
            }
        ],
        "inputs": {},
        "expected": {
            "result": AntaTestStatus.FAILURE,
            "messages": [
                "VRF: data Profile: DATA-AVT-POLICY-DEFAULT AVT path: direct:10 - Invalid",
                "VRF: guest Profile: GUEST-AVT-POLICY-DEFAULT AVT path: direct:8 - Invalid",
                "VRF: default Profile: CONTROL-PLANE-PROFILE AVT path: direct:10 - Invalid",
                "VRF: default Profile: DEFAULT-AVT-POLICY-DEFAULT AVT path: direct:8 - Invalid",
            ],
        },
    },
    (VerifyAVTPathHealth, "failure-not-active-and-invalid"): {
        "eos_data": [
            {
                "vrfs": {
                    "data": {
                        "avts": {
                            "DATA-AVT-POLICY-DEFAULT": {
                                "avtPaths": {
                                    "direct:9": {"flags": {"directPath": True, "valid": True, "active": True}},
                                    "direct:10": {"flags": {"directPath": True, "valid": False, "active": False}},
                                    "direct:1": {"flags": {"directPath": True, "valid": True, "active": False}},
                                    "direct:8": {"flags": {"directPath": True, "valid": True, "active": True}},
                                }
                            }
                        }
                    },
                    "guest": {
                        "avts": {
                            "GUEST-AVT-POLICY-DEFAULT": {
                                "avtPaths": {
                                    "direct:10": {"flags": {"directPath": True, "valid": False, "active": True}},
                                    "direct:8": {"flags": {"directPath": True, "valid": False, "active": False}},
                                }
                            }
                        }
                    },
                    "default": {
                        "avts": {
                            "CONTROL-PLANE-PROFILE": {
                                "avtPaths": {
                                    "direct:9": {"flags": {"directPath": True, "valid": True, "active": True}},
                                    "direct:10": {"flags": {"directPath": True, "valid": False, "active": False}},
                                    "direct:1": {"flags": {"directPath": True, "valid": True, "active": True}},
                                    "direct:8": {"flags": {"directPath": True, "valid": True, "active": True}},
                                }
                            },
                            "DEFAULT-AVT-POLICY-DEFAULT": {
                                "avtPaths": {
                                    "direct:10": {"flags": {"directPath": True, "valid": True, "active": False}},
                                    "direct:8": {"flags": {"directPath": True, "valid": False, "active": False}},
                                }
                            },
                        }
                    },
                }
            }
        ],
        "inputs": {},
        "expected": {
            "result": AntaTestStatus.FAILURE,
            "messages": [
                "VRF: data Profile: DATA-AVT-POLICY-DEFAULT AVT path: direct:10 - Invalid and not active",
                "VRF: data Profile: DATA-AVT-POLICY-DEFAULT AVT path: direct:1 - Not active",
                "VRF: guest Profile: GUEST-AVT-POLICY-DEFAULT AVT path: direct:10 - Invalid",
                "VRF: guest Profile: GUEST-AVT-POLICY-DEFAULT AVT path: direct:8 - Invalid and not active",
                "VRF: default Profile: CONTROL-PLANE-PROFILE AVT path: direct:10 - Invalid and not active",
                "VRF: default Profile: DEFAULT-AVT-POLICY-DEFAULT AVT path: direct:10 - Not active",
                "VRF: default Profile: DEFAULT-AVT-POLICY-DEFAULT AVT path: direct:8 - Invalid and not active",
            ],
        },
    },
    (VerifyAVTSpecificPath, "success"): {
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
                        }
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
                            }
                        }
                    },
                }
            }
        ],
        "inputs": {
            "avt_paths": [
                {"avt_name": "DEFAULT-AVT-POLICY-CONTROL-PLANE", "destination": "10.101.255.2", "next_hop": "10.101.255.1", "path_type": "multihop"},
                {"avt_name": "DATA-AVT-POLICY-CONTROL-PLANE", "vrf": "data", "destination": "10.101.255.1", "next_hop": "10.101.255.2", "path_type": "direct"},
                {"avt_name": "DATA-AVT-POLICY-CONTROL-PLANE", "vrf": "data", "destination": "10.101.255.1", "next_hop": "10.101.255.2"},
            ]
        },
        "expected": {"result": AntaTestStatus.SUCCESS},
    },
    (VerifyAVTSpecificPath, "failure-no-peer"): {
        "eos_data": [{"vrfs": {}}],
        "inputs": {
            "avt_paths": [
                {"avt_name": "MGMT-AVT-POLICY-DEFAULT", "vrf": "default", "destination": "10.101.255.2", "next_hop": "10.101.255.1", "path_type": "multihop"},
                {"avt_name": "DATA-AVT-POLICY-CONTROL-PLANE", "vrf": "data", "destination": "10.101.255.1", "next_hop": "10.101.255.2", "path_type": "multihop"},
            ]
        },
        "expected": {
            "result": AntaTestStatus.FAILURE,
            "messages": ["AVT: MGMT-AVT-POLICY-DEFAULT VRF: default Destination: 10.101.255.2 Next-hop: 10.101.255.1 - No AVT path configured"],
        },
    },
    (VerifyAVTSpecificPath, "failure-path_type_check_true"): {
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
                        }
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
                            }
                        }
                    },
                }
            }
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
            "result": AntaTestStatus.FAILURE,
            "messages": [
                "AVT: DEFAULT-AVT-POLICY-CONTROL-PLANE VRF: default Destination: 10.101.255.2 Next-hop: 10.101.255.11 Path Type: multihop - Path not found",
                "AVT: DATA-AVT-POLICY-CONTROL-PLANE VRF: data Destination: 10.101.255.1 Next-hop: 10.101.255.21 Path Type: direct - Path not found",
            ],
        },
    },
    (VerifyAVTSpecificPath, "failure-path_type_check_false"): {
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
                        }
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
                            }
                        }
                    },
                }
            }
        ],
        "inputs": {
            "avt_paths": [
                {"avt_name": "DEFAULT-AVT-POLICY-CONTROL-PLANE", "vrf": "default", "destination": "10.101.255.2", "next_hop": "10.101.255.11"},
                {"avt_name": "DATA-AVT-POLICY-CONTROL-PLANE", "vrf": "data", "destination": "10.101.255.1", "next_hop": "10.101.255.21"},
            ]
        },
        "expected": {
            "result": AntaTestStatus.FAILURE,
            "messages": [
                "AVT: DEFAULT-AVT-POLICY-CONTROL-PLANE VRF: default Destination: 10.101.255.2 Next-hop: 10.101.255.11 - Path not found",
                "AVT: DATA-AVT-POLICY-CONTROL-PLANE VRF: data Destination: 10.101.255.1 Next-hop: 10.101.255.21 - Path not found",
            ],
        },
    },
    (VerifyAVTSpecificPath, "failure-incorrect-path"): {
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
                                    }
                                }
                            }
                        }
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
                            }
                        }
                    },
                }
            }
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
            "result": AntaTestStatus.FAILURE,
            "messages": [
                "AVT: DEFAULT-AVT-POLICY-CONTROL-PLANE VRF: default Destination: 10.101.255.2 Next-hop: 10.101.255.1 - Incorrect path multihop:3 - "
                "Valid: False Active: True",
                "AVT: DATA-AVT-POLICY-CONTROL-PLANE VRF: data Destination: 10.101.255.1 Next-hop: 10.101.255.1 - Incorrect path direct:10 - "
                "Valid: False Active: True",
                "AVT: DATA-AVT-POLICY-CONTROL-PLANE VRF: data Destination: 10.101.255.1 Next-hop: 10.101.255.1 - Incorrect path direct:9 - "
                "Valid: True Active: False",
            ],
        },
    },
    (VerifyAVTRole, "success"): {"eos_data": [{"role": "edge"}], "inputs": {"role": "edge"}, "expected": {"result": AntaTestStatus.SUCCESS}},
    (VerifyAVTRole, "failure-incorrect-role"): {
        "eos_data": [{"role": "transit"}],
        "inputs": {"role": "edge"},
        "expected": {"result": AntaTestStatus.FAILURE, "messages": ["AVT role mismatch - Expected: edge Actual: transit"]},
    },
}
