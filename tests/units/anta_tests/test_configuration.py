# Copyright (c) 2023-2026 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Data for testing anta.tests.configuration."""

from __future__ import annotations

import sys
from typing import TYPE_CHECKING, Any

from anta.models import AntaTest
from anta.result_manager.models import AntaTestStatus
from anta.tests.configuration import VerifyRunningConfigDiffs, VerifyRunningConfigLines, VerifyZeroTouch
from tests.units.anta_tests import test

if TYPE_CHECKING:
    from tests.units.anta_tests import AntaUnitTestData

DATA: AntaUnitTestData = {
    (VerifyZeroTouch, "success"): {"eos_data": [{"mode": "disabled"}], "expected": {"result": AntaTestStatus.SUCCESS}},
    (VerifyZeroTouch, "failure"): {
        "eos_data": [{"mode": "enabled"}],
        "expected": {"result": AntaTestStatus.FAILURE, "messages": ["ZTP is NOT disabled"]},
    },
    (VerifyRunningConfigDiffs, "success"): {"eos_data": [""], "expected": {"result": AntaTestStatus.SUCCESS}},
    (VerifyRunningConfigDiffs, "failure"): {"eos_data": ["blah blah"], "expected": {"result": AntaTestStatus.FAILURE, "messages": ["blah blah"]}},
    (VerifyRunningConfigLines, "success"): {
        "inputs": {
            "configs": [
                {
                    "section": "router bgp 65101",
                    "description": "BGP routing configuration",
                    "config_entries": [
                        {
                            "search_string": "maximum-paths",
                            "validation_mode": "contains",
                            "threshold": 4,
                        }
                    ],
                },
                {
                    "description": "Prohibited global configuration",
                    "config_entries": [
                        {
                            "search_string": "enable password",
                            "validation_mode": "absent",
                            "context": "Cleartext enable password must not be configured",
                        }
                    ],
                },
                {
                    "section": "interface Ethernet1",
                    "config_entries": [
                        {
                            "search_string": "no switchport",
                            "context": "Ethernet1 must be a routed (Layer-3) port",
                        }
                    ],
                },
            ]
        },
        "eos_data": [
            {
                "cmds": {
                    "no enable password": None,
                    "interface Ethernet1": {"cmds": {"no switchport": None}},
                    "router bgp 65101": {
                        "cmds": {
                            "router-id 10.111.254.1": None,
                            "maximum-paths 4 ecmp 4": None,
                        }
                    },
                }
            }
        ],
        "expected": {
            "result": AntaTestStatus.SUCCESS,
            "atomic_results": [
                {"description": "BGP routing configuration", "result": AntaTestStatus.SUCCESS, "messages": []},
                {"description": "Prohibited global configuration", "result": AntaTestStatus.SUCCESS, "messages": []},
                {"description": "Section: interface Ethernet1", "result": AntaTestStatus.SUCCESS, "messages": []},
            ],
        },
    },
    (VerifyRunningConfigLines, "failure-multiline-match"): {
        "inputs": {
            "configs": [
                {
                    "config_entries": [
                        {
                            "search_string": "banner login\n   Welcome to this Arista switch.\n   Unauthorized access is prohibited.\n   "
                            "Contact NOC at noc@example.com.\nEOF",
                        }
                    ]
                }
            ]
        },
        "eos_data": [
            {
                "cmds": {
                    "banner login\n   Welcome to this Arista switch.\n   Unauthorized access is prohibited.\n   Contact NOC at nc@example.com.\nEOF": None,
                    "banner motd\n   MOTD: Maintenance window scheduled Saturday 22:00-02:00 UTC.\nEOF": None,
                }
            }
        ],
        "expected": {
            "result": AntaTestStatus.FAILURE,
            "messages": [
                "Config: banner login\n   Welcome to this Arista switch.\n   Unauthorized access is prohibited.\n   Contact NOC at noc@example.com.\nEOF - Not found"
            ],
            "atomic_results": [
                {
                    "description": "Config: banner login\n   Welcome to this Arista switch.\n   Unauthorized access is prohibited.\n"
                    "   Contact NOC at noc@example.com.\nEOF",
                    "result": AntaTestStatus.FAILURE,
                    "messages": ["Not found"],
                }
            ],
        },
    },
    (VerifyRunningConfigLines, "failure-mode-exact-match"): {
        "inputs": {
            "configs": [
                {
                    "section": "management ssh",
                    "config_entries": [
                        {
                            "search_string": "cipher aes128-ctr aes256-ctr aes256-cbc",
                            "context": "Only approved SSH ciphers must be configured",
                        },
                        {
                            "search_string": "mac hmac-sha2-256 hmac-sha2-512",
                        },
                    ],
                }
            ]
        },
        "eos_data": [
            {
                "cmds": {
                    "management ssh": {
                        "cmds": {
                            "cipher aes128-ctr arcfour aes256-cbc aes256-ctr": None,
                            "mac hmac-sha2-256 hmac-sha2-512 umac-64@openssh.com": None,
                            "fips restrictions": None,
                        }
                    }
                }
            }
        ],
        "expected": {
            "result": AntaTestStatus.FAILURE,
            "messages": [
                "Section: management ssh - Only approved SSH ciphers must be configured",
                "Section: management ssh - Config: mac hmac-sha2-256 hmac-sha2-512 - Not found",
            ],
            "atomic_results": [
                {"description": "Section: management ssh", "result": AntaTestStatus.FAILURE, "messages": ["Only approved SSH ciphers must be configured"]},
                {"description": "Section: management ssh", "result": AntaTestStatus.FAILURE, "messages": ["Config: mac hmac-sha2-256 hmac-sha2-512 - Not found"]},
            ],
        },
    },
    (VerifyRunningConfigLines, "failure-mode-absent-with-desc"): {
        "inputs": {
            "configs": [
                {
                    "config_entries": [
                        {
                            "search_string": "aaa authentication login default local",
                            "context": "Local authentication must be the login default",
                        },
                        {
                            "search_string": "aaa authorization exec default local",
                            "validation_mode": "absent",
                        },
                    ]
                }
            ]
        },
        "eos_data": [
            {
                "cmds": {
                    "aaa authorization exec default local": None,
                }
            }
        ],
        "expected": {
            "result": AntaTestStatus.FAILURE,
            "messages": [
                "Config: aaa authentication login default local - Local authentication must be the login default",
                "Config: aaa authorization exec default local -  Expected to be not found",
            ],
            "atomic_results": [
                {
                    "description": "Config: aaa authentication login default local",
                    "result": AntaTestStatus.FAILURE,
                    "messages": ["Local authentication must be the login default"],
                },
                {"description": "Config: aaa authorization exec default local", "result": AntaTestStatus.FAILURE, "messages": ["Expected to be not found"]},
            ],
        },
    },
    (VerifyRunningConfigLines, "failure-mode-contains-with-threshold-section-desc"): {
        "inputs": {
            "configs": [
                {
                    "section": "router bgp 65101",
                    "description": "BGP ECMP exact path count",
                    "config_entries": [
                        {
                            "search_string": "ecmp",
                            "validation_mode": "contains",
                            "threshold": 4,
                            "threshold_operator": "le",
                        }
                    ],
                }
            ]
        },
        "eos_data": [
            {
                "cmds": {
                    "router bgp 65101": {
                        "cmds": {
                            "router-id 10.111.254.1": None,
                            "maximum-paths 8 ecmp 8": None,
                            "neighbor SPINE peer group": None,
                        }
                    },
                }
            }
        ],
        "expected": {
            "result": AntaTestStatus.FAILURE,
            "messages": ["BGP ECMP exact path count - Config: ecmp - maximum-paths 8 ecmp 8 - Expected: value <= 4 Actual: 8"],
            "atomic_results": [
                {
                    "description": "BGP ECMP exact path count",
                    "result": AntaTestStatus.FAILURE,
                    "messages": ["Config: ecmp - maximum-paths 8 ecmp 8 - Expected: value <= 4 Actual: 8"],
                }
            ],
        },
    },
    (VerifyRunningConfigLines, "failure-mode-contains-with-threshold-le-section-no-desc"): {
        "inputs": {
            "configs": [
                {
                    "section": "interface Ethernet1",
                    "description": "Uplink must have jumbo MTU",
                    "config_entries": [
                        {
                            "search_string": "mtu",
                            "validation_mode": "contains",
                            "threshold": 9000,
                            "threshold_operator": "ge",
                            "context": "Interface MTU must be at least 9000",
                        }
                    ],
                }
            ]
        },
        "eos_data": [{"cmds": {"interface Ethernet1": {"comments": [], "cmds": {"mtu 800": None, "no switchport": None}}}}],
        "expected": {
            "result": AntaTestStatus.FAILURE,
            "messages": ["Uplink must have jumbo MTU - Interface MTU must be at least 9000"],
            "atomic_results": [{"description": "Uplink must have jumbo MTU", "result": AntaTestStatus.FAILURE, "messages": ["Interface MTU must be at least 9000"]}],
        },
    },
    (VerifyRunningConfigLines, "failure-mode-contains-with-threshold-le-no-section-no-desc"): {
        "inputs": {
            "configs": [
                {
                    "config_entries": [
                        {
                            "search_string": "logging buffered",
                            "validation_mode": "contains",
                            "threshold": 2000000,
                            "threshold_operator": "le",
                        }
                    ],
                }
            ]
        },
        "eos_data": [{"cmds": {"logging buffered 3000000 debugging": None}}],
        "expected": {
            "result": AntaTestStatus.FAILURE,
            "messages": ["Config: logging buffered - logging buffered 3000000 debugging - Expected: value <= 2000000 Actual: 3000000"],
            "atomic_results": [
                {
                    "description": "Config: logging buffered",
                    "result": AntaTestStatus.FAILURE,
                    "messages": ["logging buffered 3000000 debugging - Expected: value <= 2000000 Actual: 3000000"],
                }
            ],
        },
    },
    (VerifyRunningConfigLines, "failure-section-not-found"): {
        "inputs": {
            "configs": [
                {
                    "section": "router ospf 1",
                    "config_entries": [
                        {
                            "search_string": "router-id",
                            "validation_mode": "contains",
                        }
                    ],
                }
            ]
        },
        "eos_data": [{"cmds": {"logging buffered 3000000 debugging": None}}],
        "expected": {
            "result": AntaTestStatus.FAILURE,
            "messages": ["Section: router ospf 1 - Not found in running-config"],
            "atomic_results": [],
        },
    },
    (VerifyRunningConfigLines, "failure-global-config-not-found"): {
        "inputs": {
            "configs": [
                {
                    "description": "Syslog and NTP reachability",
                    "config_entries": [
                        {
                            "search_string": "logging host",
                            "validation_mode": "contains",
                            "context": "At least one syslog server must be configured",
                        },
                        {
                            "search_string": "ntp server",
                            "validation_mode": "contains",
                            "context": "At least one NTP server must be configured",
                        },
                    ],
                }
            ]
        },
        "eos_data": [{"cmds": {"logging buffered 3000000 debugging": None}}],
        "expected": {
            "result": AntaTestStatus.FAILURE,
            "messages": [
                "Syslog and NTP reachability - At least one syslog server must be configured",
                "Syslog and NTP reachability - At least one NTP server must be configured",
            ],
            "atomic_results": [
                {"description": "Syslog and NTP reachability", "result": AntaTestStatus.FAILURE, "messages": ["At least one syslog server must be configured"]},
                {"description": "Syslog and NTP reachability", "result": AntaTestStatus.FAILURE, "messages": ["At least one NTP server must be configured"]},
            ],
        },
    },
}
