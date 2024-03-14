# Copyright (c) 2023-2024 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""
Tests for anta.tests.path_selection.py
"""
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
                                    "path3": {
                                        "state": "ipsecEstablished",
                                    },
                                },
                            },
                            "mpls": {
                                "dpsPaths": {
                                    "path4": {
                                        "state": "ipsecEstablished",
                                    },
                                },
                            },
                        },
                    },
                    "10.255.0.2": {
                        "dpsGroups": {
                            "internet": {
                                "dpsPaths": {
                                    "path1": {
                                        "state": "ipsecEstablished",
                                    },
                                },
                            },
                            "mpls": {
                                "dpsPaths": {
                                    "path2": {
                                        "state": "ipsecEstablished",
                                    },
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
                                    "path3": {
                                        "state": "ipsecPending",
                                    },
                                },
                            },
                            "mpls": {
                                "dpsPaths": {
                                    "path4": {
                                        "state": "ipsecPending",
                                    },
                                },
                            },
                        },
                    },
                    "10.255.0.2": {
                        "dpsGroups": {
                            "internet": {
                                "dpsPaths": {
                                    "path1": {
                                        "state": "ipsecEstablished",
                                    },
                                },
                            },
                            "mpls": {
                                "dpsPaths": {
                                    "path2": {
                                        "state": "ipsecPending",
                                    },
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
                "State of following peers is not `ipsecEstablished`:\n"
                "Peer 10.255.0.1 in group internet is `ipsecPending`.\n"
                "Peer 10.255.0.1 in group mpls is `ipsecPending`.\n"
                "Peer 10.255.0.2 in group mpls is `ipsecPending`."
            ],
        },
    },
    {
        "name": "success",
        "test": VerifySpecificRouterPath,
        "eos_data": [
            {
                "dpsPeers": {
                    "10.255.0.1": {
                        "dpsGroups": {
                            "internet": {
                                "dpsPaths": {
                                    "path3": {
                                        "state": "ipsecEstablished",
                                    }
                                }
                            }
                        }
                    }
                }
            },
            {
                "dpsPeers": {
                    "10.255.0.1": {
                        "dpsGroups": {
                            "mpls": {
                                "dpsPaths": {
                                    "path4": {
                                        "state": "ipsecEstablished",
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
                            "internet": {
                                "dpsPaths": {
                                    "path2": {
                                        "state": "ipsecEstablished",
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
                                    "path1": {
                                        "state": "ipsecEstablished",
                                    }
                                }
                            }
                        }
                    }
                }
            },
        ],
        "inputs": {"paths": [{"peer": "10.255.0.1", "path_groups": ["internet", "mpls"]}, {"peer": "10.255.0.2", "path_groups": ["internet", "mpls"]}]},
        "expected": {"result": "success"},
    },
    {
        "name": "failure-no-peer",
        "test": VerifySpecificRouterPath,
        "eos_data": [
            {"dpsPeers": {}},
            {
                "dpsPeers": {
                    "10.255.0.1": {
                        "dpsGroups": {
                            "mpls": {
                                "dpsPaths": {
                                    "path4": {
                                        "state": "ipsecEstablished",
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
                            "internet": {
                                "dpsPaths": {
                                    "path2": {
                                        "state": "ipsecEstablished",
                                    }
                                }
                            }
                        }
                    }
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
                    "10.255.0.1": {
                        "dpsGroups": {
                            "internet": {
                                "dpsPaths": {
                                    "path3": {
                                        "state": "ipsecEstablished",
                                    }
                                }
                            }
                        }
                    }
                }
            },
            {
                "dpsPeers": {
                    "10.255.0.1": {
                        "dpsGroups": {
                            "mpls": {
                                "dpsPaths": {
                                    "path4": {
                                        "state": "ipsecPending",
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
                            "internet": {
                                "dpsPaths": {
                                    "path2": {
                                        "state": "ipsecEstablished",
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
                                    "path1": {
                                        "state": "ipsecPending",
                                    }
                                }
                            }
                        }
                    }
                }
            },
        ],
        "inputs": {"paths": [{"peer": "10.255.0.1", "path_groups": ["internet", "mpls"]}, {"peer": "10.255.0.2", "path_groups": ["internet", "mpls"]}]},
        "expected": {
            "result": "failure",
            "messages": ["Peer 10.255.0.1 in group mpls is `ipsecPending`.", "Peer 10.255.0.2 in group mpls is `ipsecPending`."],
        },
    },
]
