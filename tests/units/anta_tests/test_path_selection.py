# Copyright (c) 2023-2024 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Tests for anta.tests.path_selection.py."""

from __future__ import annotations

from typing import Any

from anta.tests.path_selection import VerifyRouterPathsHealth, VerifySpecificRouterPath
from tests.lib.anta import test  # noqa: F401; pylint: disable=W0611

DATA: list[dict[str, Any]] = [
    {
        "name": "success",
        "test": VerifyRouterPathsHealth,
        "eos_data": [
            {
                "dpsPeers": {
                    "10.255.0.1": {
                        "dpsGroups": {
                            "internet": {
                                "dpsPaths": {
                                    "path3": {"state": "routeResolved", "dpsSessions": {"0": {"active": True}}},
                                },
                            },
                            "mpls": {
                                "dpsPaths": {
                                    "path4": {"state": "ipsecEstablished", "dpsSessions": {"0": {"active": True}}},
                                },
                            },
                        },
                    },
                    "10.255.0.2": {
                        "dpsGroups": {
                            "internet": {
                                "dpsPaths": {
                                    "path1": {"state": "ipsecEstablished", "dpsSessions": {"0": {"active": True}}},
                                },
                            },
                            "mpls": {
                                "dpsPaths": {
                                    "path2": {"state": "routeResolved", "dpsSessions": {"0": {"active": True}}},
                                },
                            },
                        },
                    },
                }
            },
        ],
        "inputs": {},
        "expected": {"result": "success"},
    },
    {
        "name": "failure-no-peer",
        "test": VerifyRouterPathsHealth,
        "eos_data": [
            {"dpsPeers": {}},
        ],
        "inputs": {},
        "expected": {"result": "failure", "messages": ["No paths are configured for router path-selection."]},
    },
    {
        "name": "failure-not-established",
        "test": VerifyRouterPathsHealth,
        "eos_data": [
            {
                "dpsPeers": {
                    "10.255.0.1": {
                        "dpsGroups": {
                            "internet": {
                                "dpsPaths": {
                                    "path3": {"state": "ipsecPending", "dpsSessions": {"0": {"active": False}}},
                                },
                            },
                            "mpls": {
                                "dpsPaths": {
                                    "path4": {"state": "ipsecPending", "dpsSessions": {"0": {"active": False}}},
                                },
                            },
                        },
                    },
                    "10.255.0.2": {
                        "dpsGroups": {
                            "internet": {
                                "dpsPaths": {
                                    "path1": {"state": "ipsecEstablished", "dpsSessions": {"0": {"active": True}}},
                                },
                            },
                            "mpls": {
                                "dpsPaths": {
                                    "path2": {"state": "ipsecPending", "dpsSessions": {"0": {"active": False}}},
                                },
                            },
                        },
                    },
                }
            },
        ],
        "inputs": {},
        "expected": {
            "result": "failure",
            "messages": [
                "Route state for peer 10.255.0.1 in group internet is `ipsecPending`.",
                "Route state for peer 10.255.0.1 in group mpls is `ipsecPending`.",
                "Route state for peer 10.255.0.2 in group mpls is `ipsecPending`.",
            ],
        },
    },
    {
        "name": "failure-inactive",
        "test": VerifyRouterPathsHealth,
        "eos_data": [
            {
                "dpsPeers": {
                    "10.255.0.1": {
                        "dpsGroups": {
                            "internet": {
                                "dpsPaths": {
                                    "path3": {"state": "routeResolved", "dpsSessions": {"0": {"active": False}}},
                                },
                            },
                            "mpls": {
                                "dpsPaths": {
                                    "path4": {"state": "routeResolved", "dpsSessions": {"0": {"active": False}}},
                                },
                            },
                        },
                    },
                    "10.255.0.2": {
                        "dpsGroups": {
                            "internet": {
                                "dpsPaths": {
                                    "path1": {"state": "routeResolved", "dpsSessions": {"0": {"active": True}}},
                                },
                            },
                            "mpls": {
                                "dpsPaths": {
                                    "path2": {"state": "routeResolved", "dpsSessions": {"0": {"active": False}}},
                                },
                            },
                        },
                    },
                }
            },
        ],
        "inputs": {},
        "expected": {
            "result": "failure",
            "messages": [
                "Telemetry state for peer 10.255.0.1 in group internet is `inactive`.",
                "Telemetry state for peer 10.255.0.1 in group mpls is `inactive`.",
                "Telemetry state for peer 10.255.0.2 in group mpls is `inactive`.",
            ],
        },
    },
    {
        "name": "success",
        "test": VerifySpecificRouterPath,
        "eos_data": [
            {
                "dpsPeers": {
                    "10.255.0.1": {"dpsGroups": {"internet": {"dpsPaths": {"path3": {"state": "ipsecEstablished", "dpsSessions": {"0": {"active": True}}}}}}}
                }
            },
            {"dpsPeers": {"10.255.0.1": {"dpsGroups": {"mpls": {"dpsPaths": {"path4": {"state": "routeResolved", "dpsSessions": {"0": {"active": True}}}}}}}}},
            {
                "dpsPeers": {
                    "10.255.0.2": {"dpsGroups": {"internet": {"dpsPaths": {"path2": {"state": "ipsecEstablished", "dpsSessions": {"0": {"active": True}}}}}}}
                }
            },
            {"dpsPeers": {"10.255.0.2": {"dpsGroups": {"mpls": {"dpsPaths": {"path1": {"state": "routeResolved", "dpsSessions": {"0": {"active": True}}}}}}}}},
        ],
        "inputs": {"paths": [{"peer": "10.255.0.1", "path_groups": ["internet", "mpls"]}, {"peer": "10.255.0.2", "path_groups": ["internet", "mpls"]}]},
        "expected": {"result": "success"},
    },
    {
        "name": "failure-no-peer",
        "test": VerifySpecificRouterPath,
        "eos_data": [
            {"dpsPeers": {}},
            {"dpsPeers": {"10.255.0.1": {"dpsGroups": {"mpls": {"dpsPaths": {"path4": {"state": "ipsecEstablished", "dpsSessions": {"0": {"active": True}}}}}}}}},
            {
                "dpsPeers": {
                    "10.255.0.2": {"dpsGroups": {"internet": {"dpsPaths": {"path2": {"state": "ipsecEstablished", "dpsSessions": {"0": {"active": True}}}}}}}
                }
            },
            {"dpsPeers": {}},
        ],
        "inputs": {"paths": [{"peer": "10.255.0.1", "path_groups": ["internet", "mpls"]}, {"peer": "10.255.0.2", "path_groups": ["internet", "mpls"]}]},
        "expected": {
            "result": "failure",
            "messages": ["Peer `10.255.0.1` is not configured for path group `internet`.", "Peer `10.255.0.2` is not configured for path group `mpls`."],
        },
    },
    {
        "name": "failure-not-established",
        "test": VerifySpecificRouterPath,
        "eos_data": [
            {
                "dpsPeers": {
                    "10.255.0.1": {"dpsGroups": {"internet": {"dpsPaths": {"path3": {"state": "ipsecEstablished", "dpsSessions": {"0": {"active": True}}}}}}}
                }
            },
            {"dpsPeers": {"10.255.0.1": {"dpsGroups": {"mpls": {"dpsPaths": {"path4": {"state": "ipsecPending", "dpsSessions": {"0": {"active": False}}}}}}}}},
            {
                "dpsPeers": {
                    "10.255.0.2": {"dpsGroups": {"internet": {"dpsPaths": {"path2": {"state": "ipsecEstablished", "dpsSessions": {"0": {"active": True}}}}}}}
                }
            },
            {"dpsPeers": {"10.255.0.2": {"dpsGroups": {"mpls": {"dpsPaths": {"path1": {"state": "ipsecPending", "dpsSessions": {"0": {"active": False}}}}}}}}},
        ],
        "inputs": {"paths": [{"peer": "10.255.0.1", "path_groups": ["internet", "mpls"]}, {"peer": "10.255.0.2", "path_groups": ["internet", "mpls"]}]},
        "expected": {
            "result": "failure",
            "messages": ["Route state for peer 10.255.0.1 in group mpls is `ipsecPending`.", "Route state for peer 10.255.0.2 in group mpls is `ipsecPending`."],
        },
    },
    {
        "name": "failure-inactive",
        "test": VerifySpecificRouterPath,
        "eos_data": [
            {"dpsPeers": {"10.255.0.1": {"dpsGroups": {"internet": {"dpsPaths": {"path3": {"state": "routeResolved", "dpsSessions": {"0": {"active": False}}}}}}}}},
            {"dpsPeers": {"10.255.0.1": {"dpsGroups": {"mpls": {"dpsPaths": {"path4": {"state": "routeResolved", "dpsSessions": {"0": {"active": False}}}}}}}}},
            {"dpsPeers": {"10.255.0.2": {"dpsGroups": {"internet": {"dpsPaths": {"path2": {"state": "routeResolved", "dpsSessions": {"0": {"active": True}}}}}}}}},
            {"dpsPeers": {"10.255.0.2": {"dpsGroups": {"mpls": {"dpsPaths": {"path1": {"state": "routeResolved", "dpsSessions": {"0": {"active": False}}}}}}}}},
        ],
        "inputs": {"paths": [{"peer": "10.255.0.1", "path_groups": ["internet", "mpls"]}, {"peer": "10.255.0.2", "path_groups": ["internet", "mpls"]}]},
        "expected": {
            "result": "failure",
            "messages": [
                "Telemetry state for peer 10.255.0.1 in group internet is `inactive`.",
                "Telemetry state for peer 10.255.0.1 in group mpls is `inactive`.",
                "Telemetry state for peer 10.255.0.2 in group mpls is `inactive`.",
            ],
        },
    },
]
