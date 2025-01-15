# Copyright (c) 2023-2025 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Tests for anta.tests.path_selection.py."""

from __future__ import annotations

from typing import TYPE_CHECKING

from anta.tests.path_selection import VerifyPathsHealth, VerifySpecificPath
from tests.units.anta_tests import test

if TYPE_CHECKING:
    from tests.units.anta_tests import AntaUnitTest

DATA: list[AntaUnitTest] = [
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
                    "10.255.0.1": {
                        "dpsGroups": {
                            "internet": {
                                "dpsPaths": {
                                    "path3": {
                                        "state": "ipsecEstablished",
                                        "source": "172.18.13.2",
                                        "destination": "172.18.15.2",
                                        "dpsSessions": {"0": {"active": True}},
                                    }
                                }
                            }
                        }
                    }
                }
            },
            {
                "dpsPeers": {
                    "10.255.0.2": {
                        "dpsGroups": {
                            "mpls": {
                                "dpsPaths": {
                                    "path2": {
                                        "state": "ipsecEstablished",
                                        "source": "172.18.3.2",
                                        "destination": "172.18.5.2",
                                        "dpsSessions": {"0": {"active": True}},
                                    }
                                }
                            }
                        }
                    }
                }
            },
        ],
        "inputs": {
            "paths": [
                {"peer": "10.255.0.1", "path_group": "internet", "source_address": "172.18.3.2", "destination_address": "172.18.5.2"},
                {"peer": "10.255.0.2", "path_group": "mpls", "source_address": "172.18.13.2", "destination_address": "172.18.15.2"},
            ]
        },
        "expected": {"result": "success"},
    },
    {
        "name": "failure-no-peer",
        "test": VerifySpecificPath,
        "eos_data": [
            {"dpsPeers": {}},
            {"dpsPeers": {}},
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
                "Path `peer: 10.255.0.1 source: 172.18.3.2 destination: 172.18.5.2` is not configured for path-group `internet`.",
                "Path `peer: 10.255.0.2 source: 172.18.13.2 destination: 172.18.15.2` is not configured for path-group `mpls`.",
            ],
        },
    },
    {
        "name": "failure-not-established",
        "test": VerifySpecificPath,
        "eos_data": [
            {
                "dpsPeers": {
                    "10.255.0.1": {
                        "dpsGroups": {
                            "internet": {
                                "dpsPaths": {
                                    "path3": {"state": "ipsecPending", "source": "172.18.3.2", "destination": "172.18.5.2", "dpsSessions": {"0": {"active": True}}}
                                }
                            }
                        }
                    }
                }
            },
            {
                "dpsPeers": {
                    "10.255.0.2": {
                        "dpsGroups": {
                            "mpls": {
                                "dpsPaths": {
                                    "path4": {
                                        "state": "ipsecPending",
                                        "source": "172.18.13.2",
                                        "destination": "172.18.15.2",
                                        "dpsSessions": {"0": {"active": False}},
                                    }
                                }
                            }
                        }
                    }
                }
            },
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
                "Path state for `peer: 10.255.0.1 source: 172.18.3.2 destination: 172.18.5.2` in path-group internet is `ipsecPending`.",
                "Path state for `peer: 10.255.0.2 source: 172.18.13.2 destination: 172.18.15.2` in path-group mpls is `ipsecPending`.",
            ],
        },
    },
    {
        "name": "failure-inactive",
        "test": VerifySpecificPath,
        "eos_data": [
            {
                "dpsPeers": {
                    "10.255.0.1": {
                        "dpsGroups": {
                            "internet": {
                                "dpsPaths": {
                                    "path3": {"state": "routeResolved", "source": "172.18.3.2", "destination": "172.18.5.2", "dpsSessions": {"0": {"active": False}}}
                                }
                            }
                        }
                    }
                }
            },
            {
                "dpsPeers": {
                    "10.255.0.2": {
                        "dpsGroups": {
                            "mpls": {
                                "dpsPaths": {
                                    "path4": {
                                        "state": "routeResolved",
                                        "source": "172.18.13.2",
                                        "destination": "172.18.15.2",
                                        "dpsSessions": {"0": {"active": False}},
                                    }
                                }
                            }
                        }
                    }
                }
            },
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
                "Telemetry state for path `peer: 10.255.0.1 source: 172.18.3.2 destination: 172.18.5.2` in path-group internet is `inactive`.",
                "Telemetry state for path `peer: 10.255.0.2 source: 172.18.13.2 destination: 172.18.15.2` in path-group mpls is `inactive`.",
            ],
        },
    },
]
