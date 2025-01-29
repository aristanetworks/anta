# Copyright (c) 2023-2025 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Tests for anta.tests.path_selection.py."""

from __future__ import annotations

from typing import Any

from anta.tests.path_selection import VerifyPathsHealth, VerifySpecificPath
from tests.units.anta_tests import test

DATA: list[dict[str, Any]] = [
    {
        "name": "success",
        "test": VerifyPathsHealth,
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
        "test": VerifyPathsHealth,
        "eos_data": [
            {"dpsPeers": {}},
        ],
        "inputs": {},
        "expected": {"result": "failure", "messages": ["No path configured for router path-selection."]},
    },
    {
        "name": "failure-not-established",
        "test": VerifyPathsHealth,
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
                "Path state for peer 10.255.0.1 in path-group internet is `ipsecPending`.",
                "Path state for peer 10.255.0.1 in path-group mpls is `ipsecPending`.",
                "Path state for peer 10.255.0.2 in path-group mpls is `ipsecPending`.",
            ],
        },
    },
    {
        "name": "failure-inactive",
        "test": VerifyPathsHealth,
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
                "Telemetry state for peer 10.255.0.1 in path-group internet is `inactive`.",
                "Telemetry state for peer 10.255.0.1 in path-group mpls is `inactive`.",
                "Telemetry state for peer 10.255.0.2 in path-group mpls is `inactive`.",
            ],
        },
    },
    {
        "name": "success",
        "test": VerifySpecificPath,
        "eos_data": [
            {
                "dpsPeers": {
                    "10.255.0.2": {
                        "dpsGroups": {
                            "mpls": {
                                "dpsPaths": {
                                    "path7": {},
                                    "path8": {
                                        "source": "172.18.13.2",
                                        "destination": "172.18.15.2",
                                        "state": "ipsecEstablished",
                                        "dpsSessions": {"0": {"active": True}},
                                    },
                                }
                            },
                            "internet": {},
                        }
                    },
                    "10.255.0.1": {
                        "dpsGroups": {
                            "internet": {
                                "dpsPaths": {
                                    "path6": {
                                        "source": "100.64.3.2",
                                        "destination": "100.64.1.2",
                                        "state": "ipsecEstablished",
                                        "dpsSessions": {"0": {"active": True}},
                                    }
                                }
                            },
                            "mpls": {},
                        }
                    },
                }
            }
        ],
        "inputs": {
            "paths": [
                {"peer": "10.255.0.1", "path_group": "internet", "source_address": "100.64.3.2", "destination_address": "100.64.1.2"},
                {"peer": "10.255.0.2", "path_group": "mpls", "source_address": "172.18.13.2", "destination_address": "172.18.15.2"},
            ]
        },
        "expected": {"result": "success"},
    },
    {
        "name": "failure-expected-path-group-not-found",
        "test": VerifySpecificPath,
        "eos_data": [
            {
                "dpsPeers": {
                    "10.255.0.2": {
                        "dpsGroups": {"internet": {}},
                    },
                    "10.255.0.1": {"peerName": "", "dpsGroups": {"mpls": {}}},
                }
            }
        ],
        "inputs": {
            "paths": [
                {"peer": "10.255.0.1", "path_group": "internet", "source_address": "100.64.3.2", "destination_address": "100.64.1.2"},
                {"peer": "10.255.0.2", "path_group": "mpls", "source_address": "172.18.13.2", "destination_address": "172.18.15.2"},
            ]
        },
        "expected": {
            "result": "failure",
            "messages": [
                "Peer: 10.255.0.1, PathGroup: internet, Source: 100.64.3.2, Destination: 100.64.1.2 - No DPS path found for this peer and path group",
                "Peer: 10.255.0.2, PathGroup: mpls, Source: 172.18.13.2, Destination: 172.18.15.2 - No DPS path found for this peer and path group.",
            ],
        },
    },
    {
        "name": "failure-no-router-path-configured",
        "test": VerifySpecificPath,
        "eos_data": [{"dpsPeers": {}}],
        "inputs": {"paths": [{"peer": "10.255.0.1", "path_group": "internet", "source_address": "100.64.3.2", "destination_address": "100.64.1.2"}]},
        "expected": {"result": "failure", "messages": ["Router path-selection not configured"]},
    },
    {
        "name": "failure-no-specific-peer-configured",
        "test": VerifySpecificPath,
        "eos_data": [{"dpsPeers": {"10.255.0.2": {}}}],
        "inputs": {"paths": [{"peer": "10.255.0.1", "path_group": "internet", "source_address": "172.18.3.2", "destination_address": "172.18.5.2"}]},
        "expected": {"result": "failure", "messages": ["Peer: 10.255.0.1, PathGroup: internet, Source: 172.18.3.2, Destination: 172.18.5.2 - Peer not found"]},
    },
    {
        "name": "failure-not-established",
        "test": VerifySpecificPath,
        "eos_data": [
            {
                "dpsPeers": {
                    "10.255.0.2": {
                        "dpsGroups": {
                            "mpls": {
                                "dpsPaths": {
                                    "path7": {},
                                    "path8": {
                                        "source": "172.18.13.2",
                                        "destination": "172.18.15.2",
                                        "state": "ipsecPending",
                                        "dpsSessions": {"0": {"active": True}},
                                    },
                                }
                            },
                            "internet": {"dpsPaths": {}},
                        }
                    },
                    "10.255.0.1": {
                        "dpsGroups": {
                            "internet": {
                                "dpsPaths": {
                                    "path6": {"source": "172.18.3.2", "destination": "172.18.5.2", "state": "ipsecPending", "dpsSessions": {"0": {"active": True}}}
                                }
                            },
                            "mpls": {"dpsPaths": {}},
                        }
                    },
                }
            }
        ],
        "inputs": {
            "paths": [
                {"peer": "10.255.0.1", "path_group": "internet", "source_address": "172.18.3.2", "destination_address": "172.18.5.2"},
                {"peer": "10.255.0.2", "path_group": "mpls", "source_address": "172.18.13.2", "destination_address": "172.18.15.2"},
            ]
        },
        "expected": {
            "result": "failure",
            "messages": [
                "Peer: 10.255.0.1, PathGroup: internet, Source: 172.18.3.2, Destination: 172.18.5.2 - State is not in ipsecEstablished, routeResolved."
                " Actual: ipsecPending",
                "Peer: 10.255.0.2, PathGroup: mpls, Source: 172.18.13.2, Destination: 172.18.15.2 - State is not in ipsecEstablished, routeResolved."
                " Actual: ipsecPending",
            ],
        },
    },
    {
        "name": "failure-inactive",
        "test": VerifySpecificPath,
        "eos_data": [
            {
                "dpsPeers": {
                    "10.255.0.2": {
                        "dpsGroups": {
                            "mpls": {
                                "dpsPaths": {
                                    "path8": {
                                        "source": "172.18.13.2",
                                        "destination": "172.18.15.2",
                                        "state": "routeResolved",
                                        "dpsSessions": {"0": {"active": False}},
                                    }
                                }
                            }
                        }
                    },
                    "10.255.0.1": {
                        "dpsGroups": {
                            "internet": {
                                "dpsPaths": {
                                    "path6": {"source": "172.18.3.2", "destination": "172.18.5.2", "state": "routeResolved", "dpsSessions": {"0": {"active": False}}}
                                }
                            }
                        }
                    },
                }
            }
        ],
        "inputs": {
            "paths": [
                {"peer": "10.255.0.1", "path_group": "internet", "source_address": "172.18.3.2", "destination_address": "172.18.5.2"},
                {"peer": "10.255.0.2", "path_group": "mpls", "source_address": "172.18.13.2", "destination_address": "172.18.15.2"},
            ]
        },
        "expected": {
            "result": "failure",
            "messages": [
                "Peer: 10.255.0.1, PathGroup: internet, Source: 172.18.3.2, Destination: 172.18.5.2 - Telemetry state inactive for this path",
                "Peer: 10.255.0.2, PathGroup: mpls, Source: 172.18.13.2, Destination: 172.18.15.2 - Telemetry state inactive for this path",
            ],
        },
    },
    {
        "name": "failure-source-destination-not-configured",
        "test": VerifySpecificPath,
        "eos_data": [
            {
                "dpsPeers": {
                    "10.255.0.2": {
                        "dpsGroups": {
                            "mpls": {
                                "dpsPaths": {
                                    "path8": {"source": "172.18.3.2", "destination": "172.8.15.2", "state": "routeResolved", "dpsSessions": {"0": {"active": False}}}
                                }
                            }
                        }
                    },
                    "10.255.0.1": {
                        "dpsGroups": {
                            "internet": {
                                "dpsPaths": {
                                    "path6": {"source": "172.8.3.2", "destination": "172.8.5.2", "state": "routeResolved", "dpsSessions": {"0": {"active": False}}}
                                }
                            }
                        }
                    },
                }
            }
        ],
        "inputs": {
            "paths": [
                {"peer": "10.255.0.1", "path_group": "internet", "source_address": "172.18.3.2", "destination_address": "172.18.5.2"},
                {"peer": "10.255.0.2", "path_group": "mpls", "source_address": "172.18.13.2", "destination_address": "172.18.15.2"},
            ]
        },
        "expected": {
            "result": "failure",
            "messages": [
                "Peer: 10.255.0.1, PathGroup: internet, Source: 172.18.3.2, Destination: 172.18.5.2 - No path matching the source and destination found",
                "Peer: 10.255.0.2, PathGroup: mpls, Source: 172.18.13.2, Destination: 172.18.15.2 - No path matching the source and destination found",
            ],
        },
    },
]
