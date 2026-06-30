# Copyright (c) 2023-2026 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Tests for anta.tests.configuration.py."""

from __future__ import annotations

from typing import TYPE_CHECKING

from anta.result_manager.models import AntaTestStatus
from anta.tests.configuration import VerifyRunningConfig, VerifyRunningConfigDiffs, VerifyRunningConfigLines, VerifyZeroTouch
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
    (VerifyRunningConfigLines, "success"): {"eos_data": ["blah blah"], "inputs": {"regex_patterns": ["blah"]}, "expected": {"result": AntaTestStatus.SUCCESS}},
    (VerifyRunningConfigLines, "success-patterns"): {
        "eos_data": ["enable password something\nsome other line"],
        "inputs": {"regex_patterns": ["^enable password .*$", "^.*other line$"]},
        "expected": {"result": AntaTestStatus.SUCCESS},
    },
    (VerifyRunningConfigLines, "failure"): {
        "eos_data": ["enable password something\nsome other line"],
        "inputs": {"regex_patterns": ["bla", "bleh"]},
        "expected": {"result": AntaTestStatus.FAILURE, "messages": ["Following patterns were not found: 'bla', 'bleh"]},
    },
    (VerifyRunningConfig, "success"): {
        "eos_data": [
            {
                "cmds": {
                    "no enable password": None,
                    "interface Ethernet1": {"cmds": {"no switchport": None}},
                    "interface Ethernet1.100": {"cmds": {"encapsulation dot1q vlan 100": None, "ip address 10.0.0.1/30": None}},
                    "router bgp 65101": {
                        "cmds": {
                            "router-id 10.111.254.1": None,
                            "maximum-paths 4 ecmp 4": None,
                        }
                    },
                }
            }
        ],
        "inputs": {
            "rules": [
                # Scenario: single section — two entries: regex+threshold (eq) and contains
                {
                    "section": ["router bgp 65101"],
                    "entries": [
                        {
                            "match": "maximum-paths (\\d+)",
                            "mode": "regex",
                            "description": "BGP maximum ECMP paths",
                            "threshold": {"value": 4, "operator": "eq"},
                        },
                        {"match": "router-id", "mode": "contains", "description": "BGP router-id"},
                    ],
                },
                # Scenario: top-level exact+absent:true — "no enable password" ≠ "enable password", absent check passes
                {
                    "entries": [
                        {
                            "match": "enable password",
                            "mode": "exact",
                            "absent": True,
                            "description": "No cleartext enable password",
                        }
                    ],
                },
                # Scenario: section without entry description — auto-generated label
                {
                    "section": ["interface Ethernet1"],
                    "entries": [{"match": "no switchport"}],
                },
                # Scenario: sub-interface section — two entries verify encapsulation and IP address presence
                {
                    "section": ["interface Ethernet1.100"],
                    "entries": [
                        {"match": "encapsulation dot1q vlan 100", "description": "802.1Q encapsulation"},
                        {"match": "ip address", "mode": "contains", "description": "IP address assignment"},
                    ],
                },
            ]
        },
        "expected": {
            "result": AntaTestStatus.SUCCESS,
            "atomic_results": [
                {
                    "description": "BGP maximum ECMP paths - Captured value of 'maximum-paths (\\d+)' == 4 in 'router bgp 65101'",
                    "result": AntaTestStatus.SUCCESS,
                    "messages": [],
                },
                {
                    "description": "BGP router-id - Substring 'router-id' in 'router bgp 65101'",
                    "result": AntaTestStatus.SUCCESS,
                    "messages": [],
                },
                {
                    "description": "No cleartext enable password - Command 'enable password' in the running-config",
                    "result": AntaTestStatus.SUCCESS,
                    "messages": [],
                },
                {
                    "description": "Command 'no switchport' in 'interface Ethernet1'",
                    "result": AntaTestStatus.SUCCESS,
                    "messages": [],
                },
                {
                    "description": "802.1Q encapsulation - Command 'encapsulation dot1q vlan 100' in 'interface Ethernet1.100'",
                    "result": AntaTestStatus.SUCCESS,
                    "messages": [],
                },
                {
                    "description": "IP address assignment - Substring 'ip address' in 'interface Ethernet1.100'",
                    "result": AntaTestStatus.SUCCESS,
                    "messages": [],
                },
            ],
        },
    },
    (VerifyRunningConfig, "success-wildcard-section"): {
        "eos_data": [
            {
                "cmds": {
                    "interface Ethernet1": {"cmds": {"description WAN": None, "no switchport": None, "mtu 9214": None}},
                    "interface Ethernet2": {"cmds": {"description LAN": None, "no switchport": None, "mtu 9214": None}},
                    "interface Management0": {"cmds": {"description MGMT": None}},
                }
            }
        ],
        "inputs": {
            "rules": [
                # Scenario: regex wildcard + contains — Ethernet1 and Ethernet2 matched, Management0 excluded
                {
                    "section": ["interface Ethernet\\d+"],
                    "entries": [{"match": "description", "mode": "contains", "description": "Interface description"}],
                },
                # Scenario: same wildcard section + regex threshold — each matched section validated independently
                {
                    "section": ["interface Ethernet\\d+"],
                    "entries": [{"match": "mtu (\\d+)", "mode": "regex", "description": "Interface MTU", "threshold": {"value": 1500, "operator": "ge"}}],
                },
                # Scenario: $ anchor — re.fullmatch makes it redundant but harmless; Ethernet1 only, still wildcard
                {
                    "section": ["interface Ethernet1$"],
                    "entries": [{"match": "no switchport", "description": "Routed port mode"}],
                },
            ]
        },
        "expected": {
            "result": AntaTestStatus.SUCCESS,
            "atomic_results": [
                {
                    "description": "Interface description - Substring 'description' in 'interface Ethernet1'",
                    "result": AntaTestStatus.SUCCESS,
                    "messages": [],
                },
                {
                    "description": "Interface description - Substring 'description' in 'interface Ethernet2'",
                    "result": AntaTestStatus.SUCCESS,
                    "messages": [],
                },
                {
                    "description": "Interface MTU - Captured value of 'mtu (\\d+)' >= 1500 in 'interface Ethernet1'",
                    "result": AntaTestStatus.SUCCESS,
                    "messages": [],
                },
                {
                    "description": "Interface MTU - Captured value of 'mtu (\\d+)' >= 1500 in 'interface Ethernet2'",
                    "result": AntaTestStatus.SUCCESS,
                    "messages": [],
                },
                {
                    "description": "Routed port mode - Command 'no switchport' in 'interface Ethernet1'",
                    "result": AntaTestStatus.SUCCESS,
                    "messages": [],
                },
            ],
        },
    },
    (VerifyRunningConfig, "success-nested-section"): {
        "eos_data": [
            {
                "cmds": {
                    "router bgp 65101": {
                        "cmds": {
                            "router-id 10.111.254.1": None,
                            "vrf DEV": {"cmds": {"router-id 192.168.1.1": None}},
                        }
                    }
                }
            }
        ],
        "inputs": {
            "rules": [
                # Scenario: two-level exact section — navigates bgp > vrf DEV; validates router-id
                {
                    "section": ["router bgp 65101", "vrf DEV"],
                    "entries": [{"match": "router-id", "mode": "contains", "description": "BGP VRF DEV router-id"}],
                },
                # Scenario: entries=[] — section existence check only; no atomics emitted on success
                {
                    "section": ["router bgp 65101"],
                    "entries": [],
                },
            ]
        },
        "expected": {
            "result": AntaTestStatus.SUCCESS,
            "atomic_results": [
                {
                    "description": "BGP VRF DEV router-id - Substring 'router-id' in 'router bgp 65101 > vrf DEV'",
                    "result": AntaTestStatus.SUCCESS,
                    "messages": [],
                },
            ],
        },
    },
    (VerifyRunningConfig, "success-threshold-operators"): {
        # all threshold operators passing — le, ge, eq
        "eos_data": [
            {
                "cmds": {
                    "router bgp 65120": {
                        "cmds": {
                            "graceful-restart restart-time 300": None,
                            "maximum-paths 4": None,
                        }
                    },
                    "interface Ethernet1": {"cmds": {"mtu 9214": None}},
                }
            }
        ],
        "inputs": {
            "rules": [
                # Scenario: eq — captured restart-time 300 equals expected 300
                {
                    "section": ["router bgp 65120"],
                    "entries": [{"match": "graceful-restart restart-time (\\d+)", "mode": "regex", "threshold": {"value": 300, "operator": "eq"}}],
                },
                # Scenario: le — captured maximum-paths 4 is within limit 8
                {
                    "section": ["router bgp 65120"],
                    "entries": [{"match": "maximum-paths (\\d+)", "mode": "regex", "threshold": {"value": 8, "operator": "le"}}],
                },
                # Scenario: ge — captured MTU 9214 meets minimum 1500
                {
                    "section": ["interface Ethernet1"],
                    "entries": [
                        {"match": "mtu (\\d+)", "mode": "regex", "description": "Uplink MTU", "threshold": {"value": 1500, "operator": "ge"}},
                    ],
                },
            ]
        },
        "expected": {
            "result": AntaTestStatus.SUCCESS,
            "atomic_results": [
                {
                    "description": "Captured value of 'graceful-restart restart-time (\\d+)' == 300 in 'router bgp 65120'",
                    "result": AntaTestStatus.SUCCESS,
                    "messages": [],
                },
                {
                    "description": "Captured value of 'maximum-paths (\\d+)' <= 8 in 'router bgp 65120'",
                    "result": AntaTestStatus.SUCCESS,
                    "messages": [],
                },
                {
                    "description": "Uplink MTU - Captured value of 'mtu (\\d+)' >= 1500 in 'interface Ethernet1'",
                    "result": AntaTestStatus.SUCCESS,
                    "messages": [],
                },
            ],
        },
    },
    (VerifyRunningConfig, "failure-section-not-found-empty-entries"): {
        # entries=[] with section not found — failure atomic emitted even without entries to validate
        "eos_data": [{"cmds": {"ip routing": None}}],
        "inputs": {
            "rules": [
                {
                    "section": ["router ospf 1"],
                    "entries": [],
                },
            ]
        },
        "expected": {
            "result": AntaTestStatus.FAILURE,
            "messages": ["Section 'router ospf 1' - Not found in the running-config"],
            "atomic_results": [
                {"description": "Section 'router ospf 1'", "result": AntaTestStatus.FAILURE, "messages": ["Not found in the running-config"]},
            ],
        },
    },
    (VerifyRunningConfig, "failure-multiline-match"): {
        # exact mode on a multiline key — a single character difference anywhere in the string fails the match
        "eos_data": [
            {
                "cmds": {
                    "banner login\n   Welcome to this Arista switch.\n   Unauthorized access is prohibited.\n   Contact NOC at nc@example.com.\nEOF": None,
                    "banner motd\n   MOTD: Maintenance window scheduled Saturday 22:00-02:00 UTC.\nEOF": None,
                }
            }
        ],
        "inputs": {
            "rules": [
                {
                    "entries": [
                        {
                            "match": "banner login\n   Welcome to this Arista switch.\n   Unauthorized access is prohibited.\n   "
                            "Contact NOC at noc@example.com.\nEOF",
                        }
                    ]
                }
            ]
        },
        "expected": {
            "result": AntaTestStatus.FAILURE,
            "messages": [
                "Command 'banner login\n   Welcome to this Arista switch.\n   Unauthorized access is prohibited.\n"
                "   Contact NOC at noc@example.com.\nEOF' in the running-config - Not found"
            ],
            "atomic_results": [
                {
                    "description": "Command 'banner login\n   Welcome to this Arista switch.\n   Unauthorized access is prohibited.\n"
                    "   Contact NOC at noc@example.com.\nEOF' in the running-config",
                    "result": AntaTestStatus.FAILURE,
                    "messages": ["Not found"],
                }
            ],
        },
    },
    (VerifyRunningConfig, "failure-mode-exact"): {
        # exact fails (cipher keywords in wrong order; MAC string is prefix of actual command) and exact+absent:true inside a section
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
        "inputs": {
            "rules": [
                {
                    "section": ["management ssh"],
                    "entries": [
                        # Cipher keywords are in a different order than the EOS canonical output — exact equality fails
                        {"match": "cipher aes128-ctr aes256-ctr aes256-cbc"},
                        # Match is missing the trailing umac-64@openssh.com that EOS appends — exact fails
                        {"match": "mac hmac-sha2-256 hmac-sha2-512"},
                        # fips restrictions in the section but the rule requires it to be absent
                        {"match": "fips restrictions", "mode": "exact", "absent": True},
                    ],
                }
            ]
        },
        "expected": {
            "result": AntaTestStatus.FAILURE,
            "messages": [
                "Command 'cipher aes128-ctr aes256-ctr aes256-cbc' in 'management ssh' - Not found",
                "Command 'mac hmac-sha2-256 hmac-sha2-512' in 'management ssh' - Not found",
                "Command 'fips restrictions' in 'management ssh' - Expected to be absent",
            ],
            "atomic_results": [
                {
                    "description": "Command 'cipher aes128-ctr aes256-ctr aes256-cbc' in 'management ssh'",
                    "result": AntaTestStatus.FAILURE,
                    "messages": ["Not found"],
                },
                {
                    "description": "Command 'mac hmac-sha2-256 hmac-sha2-512' in 'management ssh'",
                    "result": AntaTestStatus.FAILURE,
                    "messages": ["Not found"],
                },
                {
                    "description": "Command 'fips restrictions' in 'management ssh'",
                    "result": AntaTestStatus.FAILURE,
                    "messages": ["Expected to be absent"],
                },
            ],
        },
    },
    (VerifyRunningConfig, "failure-top-level-entries"): {
        "eos_data": [
            {
                "cmds": {
                    "aaa authorization exec default local": None,
                    "logging buffered 3000000 debugging": None,
                }
            }
        ],
        "inputs": {
            "rules": [
                # Scenario: two entries in one rule — exact not found; exact+absent found
                {
                    "entries": [
                        # Must be present — not found
                        {"match": "aaa authentication login default local"},
                        # Must be absent — found
                        {"match": "aaa authorization exec default local", "mode": "exact", "absent": True},
                    ]
                },
                # Scenario: no description — auto-generated label
                {
                    "entries": [{"match": "ntp server", "mode": "contains"}],
                },
                # Scenario: entry with description
                {
                    "entries": [
                        {"match": "logging host", "mode": "contains", "description": "Syslog reachability"},
                    ],
                },
            ]
        },
        "expected": {
            "result": AntaTestStatus.FAILURE,
            "messages": [
                "Command 'aaa authentication login default local' in the running-config - Not found",
                "Command 'aaa authorization exec default local' in the running-config - Expected to be absent",
                "Substring 'ntp server' in the running-config - Not found",
                "Syslog reachability - Substring 'logging host' in the running-config - Not found",
            ],
            "atomic_results": [
                {
                    "description": "Command 'aaa authentication login default local' in the running-config",
                    "result": AntaTestStatus.FAILURE,
                    "messages": ["Not found"],
                },
                {
                    "description": "Command 'aaa authorization exec default local' in the running-config",
                    "result": AntaTestStatus.FAILURE,
                    "messages": ["Expected to be absent"],
                },
                {
                    "description": "Substring 'ntp server' in the running-config",
                    "result": AntaTestStatus.FAILURE,
                    "messages": ["Not found"],
                },
                {
                    "description": "Syslog reachability - Substring 'logging host' in the running-config",
                    "result": AntaTestStatus.FAILURE,
                    "messages": ["Not found"],
                },
            ],
        },
    },
    (VerifyRunningConfig, "failure-top-level-no-recurse"): {
        # top-level rule (no section) must NOT match commands that exist only inside nested sections
        "eos_data": [
            {
                "cmds": {
                    "ip routing": None,
                    "router bgp 65101": {"cmds": {"router-id 10.111.254.1": None}},
                }
            }
        ],
        "inputs": {
            "rules": [
                {
                    "entries": [{"match": "router-id", "mode": "contains", "description": "Router-id at top level"}],
                }
            ]
        },
        "expected": {
            "result": AntaTestStatus.FAILURE,
            "messages": ["Router-id at top level - Substring 'router-id' in the running-config - Not found"],
            "atomic_results": [
                {
                    "description": "Router-id at top level - Substring 'router-id' in the running-config",
                    "result": AntaTestStatus.FAILURE,
                    "messages": ["Not found"],
                },
            ],
        },
    },
    (VerifyRunningConfig, "failure-regex-threshold-operators"): {
        "eos_data": [
            {
                "cmds": {
                    "router bgp 65101": {
                        "cmds": {
                            "maximum-paths 8 ecmp 8": None,
                            "graceful-restart restart-time 200": None,
                        }
                    },
                    "interface Ethernet1": {"cmds": {"mtu 800": None}},
                }
            }
        ],
        "inputs": {
            "rules": [
                # Scenario: le operator — captured ecmp 8 exceeds limit 4; check fails
                {
                    "section": ["router bgp 65101"],
                    "entries": [{"match": "ecmp (\\d+)", "mode": "regex", "threshold": {"value": 4, "operator": "le"}}],
                },
                # Scenario: eq operator — captured restart-time 200 ≠ expected 300; check fails
                {
                    "section": ["router bgp 65101"],
                    "entries": [{"match": "graceful-restart restart-time (\\d+)", "mode": "regex", "threshold": {"value": 300, "operator": "eq"}}],
                },
                # Scenario: ge operator with description — captured MTU 800 below minimum 9000
                {
                    "section": ["interface Ethernet1"],
                    "entries": [
                        {
                            "match": "mtu (\\d+)",
                            "mode": "regex",
                            "threshold": {"value": 9000, "operator": "ge"},
                            "description": "Uplink must have jumbo MTU",
                        }
                    ],
                },
            ]
        },
        "expected": {
            "result": AntaTestStatus.FAILURE,
            "messages": [
                "Captured value of 'ecmp (\\d+)' <= 4 in 'router bgp 65101' - Actual: 8",
                "Captured value of 'graceful-restart restart-time (\\d+)' == 300 in 'router bgp 65101' - Actual: 200",
                "Uplink must have jumbo MTU - Captured value of 'mtu (\\d+)' >= 9000 in 'interface Ethernet1' - Actual: 800",
            ],
            "atomic_results": [
                {
                    "description": "Captured value of 'ecmp (\\d+)' <= 4 in 'router bgp 65101'",
                    "result": AntaTestStatus.FAILURE,
                    "messages": ["Actual: 8"],
                },
                {
                    "description": "Captured value of 'graceful-restart restart-time (\\d+)' == 300 in 'router bgp 65101'",
                    "result": AntaTestStatus.FAILURE,
                    "messages": ["Actual: 200"],
                },
                {
                    "description": "Uplink must have jumbo MTU - Captured value of 'mtu (\\d+)' >= 9000 in 'interface Ethernet1'",
                    "result": AntaTestStatus.FAILURE,
                    "messages": ["Actual: 800"],
                },
            ],
        },
    },
    (VerifyRunningConfig, "failure-regex-threshold-no-section"): {
        # regex+threshold:le at top level — no section
        "eos_data": [{"cmds": {"logging buffered 3000000 debugging": None}}],
        "inputs": {
            "rules": [
                {
                    "entries": [{"match": "logging buffered (\\d+)", "mode": "regex", "threshold": {"value": 2000000, "operator": "le"}}],
                }
            ]
        },
        "expected": {
            "result": AntaTestStatus.FAILURE,
            "messages": ["Captured value of 'logging buffered (\\d+)' <= 2000000 in the running-config - Actual: 3000000"],
            "atomic_results": [
                {
                    "description": "Captured value of 'logging buffered (\\d+)' <= 2000000 in the running-config",
                    "result": AntaTestStatus.FAILURE,
                    "messages": ["Actual: 3000000"],
                }
            ],
        },
    },
    (VerifyRunningConfig, "failure-section-regex-no-partial-match"): {
        "eos_data": [{"cmds": {"interface Ethernet11": {"cmds": {"no switchport": None}}}}],
        "inputs": {
            "rules": [
                # Scenario: no $ anchor — re.fullmatch still prevents partial match; Ethernet1 does not match Ethernet11
                {
                    "section": ["interface Ethernet1"],
                    "entries": [{"match": "no switchport"}],
                },
                # Scenario: $ anchor — redundant with re.fullmatch but harmless; same rejection result
                {
                    "section": ["interface Ethernet1$"],
                    "entries": [{"match": "no switchport"}],
                },
            ]
        },
        "expected": {
            "result": AntaTestStatus.FAILURE,
            "messages": [
                "Section 'interface Ethernet1' - Not found in the running-config",
                "Section 'interface Ethernet1$' - Not found in the running-config",
            ],
            "atomic_results": [
                {"description": "Section 'interface Ethernet1'", "result": AntaTestStatus.FAILURE, "messages": ["Not found in the running-config"]},
                {"description": "Section 'interface Ethernet1$'", "result": AntaTestStatus.FAILURE, "messages": ["Not found in the running-config"]},
            ],
        },
    },
    (VerifyRunningConfig, "failure-section-not-found"): {
        "eos_data": [{"cmds": {"interface Ethernet1": {"cmds": {"no switchport": None}}}}],
        "inputs": {
            "rules": [
                # Scenario: section not found — label is "Section '<pattern>'"
                {
                    "section": ["interface Ethernet1.100"],
                    "entries": [{"match": "encapsulation dot1q vlan 100"}],
                },
                # Scenario: another section not found
                {
                    "section": ["interface Ethernet99"],
                    "entries": [{"match": "no switchport"}],
                },
            ]
        },
        "expected": {
            "result": AntaTestStatus.FAILURE,
            "messages": [
                "Section 'interface Ethernet1.100' - Not found in the running-config",
                "Section 'interface Ethernet99' - Not found in the running-config",
            ],
            "atomic_results": [
                {"description": "Section 'interface Ethernet1.100'", "result": AntaTestStatus.FAILURE, "messages": ["Not found in the running-config"]},
                {"description": "Section 'interface Ethernet99'", "result": AntaTestStatus.FAILURE, "messages": ["Not found in the running-config"]},
            ],
        },
    },
    (VerifyRunningConfig, "failure-wildcard-section"): {
        # wildcard section; only Ethernet2 fails — Ethernet1 passes, proving per-section atomicity
        "eos_data": [
            {
                "cmds": {
                    "interface Ethernet1": {"cmds": {"description WAN": None, "no switchport": None}},
                    "interface Ethernet2": {"cmds": {"no switchport": None}},
                }
            }
        ],
        "inputs": {
            "rules": [
                {
                    "section": ["interface Ethernet\\d+"],
                    "entries": [{"match": "description", "mode": "contains", "description": "Interface description"}],
                }
            ]
        },
        "expected": {
            "result": AntaTestStatus.FAILURE,
            "messages": [
                "Interface description - Substring 'description' in 'interface Ethernet2' - Not found",
            ],
            "atomic_results": [
                {
                    "description": "Interface description - Substring 'description' in 'interface Ethernet1'",
                    "result": AntaTestStatus.SUCCESS,
                    "messages": [],
                },
                {
                    "description": "Interface description - Substring 'description' in 'interface Ethernet2'",
                    "result": AntaTestStatus.FAILURE,
                    "messages": ["Not found"],
                },
            ],
        },
    },
    (VerifyRunningConfig, "success-absent-modes"): {
        "eos_data": [
            {
                "cmds": {
                    "ip routing": None,
                    "username admin privilege 15": None,
                    "logging host 192.0.2.30 vrf MGMT": None,
                    "ntp server vrf MGMT 192.0.2.10 prefer": None,
                }
            }
        ],
        "inputs": {
            "rules": [
                # Scenario: contains+absent:true — prohibited prefix not present in config; check passes
                {
                    "entries": [{"match": "snmp-server community", "mode": "contains", "absent": True, "description": "No SNMP community strings"}],
                },
                # Scenario: regex+absent:true — plaintext secret pattern not matched; check passes
                {
                    "entries": [{"match": "username .+ secret 0 ", "mode": "regex", "absent": True, "description": "No plaintext secrets"}],
                },
                # Scenario: regex+absent:false — at least one command matches the logging host pattern
                {
                    "entries": [{"match": "logging host \\S+", "mode": "regex", "description": "Remote syslog configured"}],
                },
                # Scenario: contains+absent:false — ntp server substring found in a command
                {
                    "entries": [{"match": "ntp server", "mode": "contains", "description": "NTP server configured"}],
                },
            ]
        },
        "expected": {
            "result": AntaTestStatus.SUCCESS,
            "atomic_results": [
                {
                    "description": "No SNMP community strings - Substring 'snmp-server community' in the running-config",
                    "result": AntaTestStatus.SUCCESS,
                    "messages": [],
                },
                {
                    "description": "No plaintext secrets - Pattern 'username .+ secret 0 ' in the running-config",
                    "result": AntaTestStatus.SUCCESS,
                    "messages": [],
                },
                {
                    "description": "Remote syslog configured - Pattern 'logging host \\S+' in the running-config",
                    "result": AntaTestStatus.SUCCESS,
                    "messages": [],
                },
                {
                    "description": "NTP server configured - Substring 'ntp server' in the running-config",
                    "result": AntaTestStatus.SUCCESS,
                    "messages": [],
                },
            ],
        },
    },
    (VerifyRunningConfig, "failure-absent-prohibited"): {
        "eos_data": [
            {
                "cmds": {
                    "snmp-server community public ro": None,
                    "aaa authorization exec default local": None,
                    "username admin secret 0 plaintext123": None,
                    "ip routing": None,
                }
            }
        ],
        "inputs": {
            "rules": [
                # Scenario: contains+absent:true — "snmp-server community" prefix found; check fails
                {
                    "entries": [{"match": "snmp-server community", "mode": "contains", "absent": True, "description": "No SNMP community strings"}],
                },
                # Scenario: contains mid-command — "authorization exec" is found inside the full aaa line; check fails
                {
                    "entries": [{"match": "authorization exec", "mode": "contains", "absent": True, "description": "No AAA exec authorization"}],
                },
                # Scenario: regex+absent:true — plaintext secret 0 pattern matched; check fails
                {
                    "entries": [{"match": "username .+ secret 0 ", "mode": "regex", "absent": True, "description": "No plaintext secrets"}],
                },
            ]
        },
        "expected": {
            "result": AntaTestStatus.FAILURE,
            "messages": [
                "No SNMP community strings - Substring 'snmp-server community' in the running-config - Expected to be absent",
                "No AAA exec authorization - Substring 'authorization exec' in the running-config - Expected to be absent",
                "No plaintext secrets - Pattern 'username .+ secret 0 ' in the running-config - Expected to not match",
            ],
            "atomic_results": [
                {
                    "description": "No SNMP community strings - Substring 'snmp-server community' in the running-config",
                    "result": AntaTestStatus.FAILURE,
                    "messages": ["Expected to be absent"],
                },
                {
                    "description": "No AAA exec authorization - Substring 'authorization exec' in the running-config",
                    "result": AntaTestStatus.FAILURE,
                    "messages": ["Expected to be absent"],
                },
                {
                    "description": "No plaintext secrets - Pattern 'username .+ secret 0 ' in the running-config",
                    "result": AntaTestStatus.FAILURE,
                    "messages": ["Expected to not match"],
                },
            ],
        },
    },
    (VerifyRunningConfig, "failure-regex-threshold-non-numeric-capture"): {
        # regex matches but capture group is non-numeric — clean failure instead of ValueError crash
        "eos_data": [{"cmds": {"description Uplink": None}}],
        "inputs": {
            "rules": [
                {
                    "entries": [{"match": "description (\\S+)", "mode": "regex", "threshold": {"value": 5, "operator": "le"}}],
                }
            ]
        },
        "expected": {
            "result": AntaTestStatus.FAILURE,
            "messages": ["Captured value of 'description (\\S+)' <= 5 in the running-config - Captured value 'Uplink' is not an integer"],
            "atomic_results": [
                {
                    "description": "Captured value of 'description (\\S+)' <= 5 in the running-config",
                    "result": AntaTestStatus.FAILURE,
                    "messages": ["Captured value 'Uplink' is not an integer"],
                }
            ],
        },
    },
    (VerifyRunningConfig, "success-nested-wildcard-section"): {
        "eos_data": [
            {
                "cmds": {
                    "router bgp 65101": {
                        "cmds": {
                            "vrf PROD": {"cmds": {"router-id 10.0.1.1": None}},
                            "vrf DEV": {"cmds": {"router-id 10.0.2.1": None}},
                        }
                    }
                }
            }
        ],
        "inputs": {
            "rules": [
                # Scenario: regex+regex — both VRFs matched; PROD and DEV each get their own atomic
                {
                    "section": ["router bgp \\d+", "vrf .*"],
                    "entries": [{"match": "router-id", "mode": "contains", "description": "BGP VRF router-id"}],
                },
                # Scenario: regex+exact — only DEV matched at second level; one atomic result
                {
                    "section": ["router bgp \\d+", "vrf DEV"],
                    "entries": [{"match": "router-id", "mode": "contains", "description": "BGP DEV VRF router-id"}],
                },
            ]
        },
        "expected": {
            "result": AntaTestStatus.SUCCESS,
            "atomic_results": [
                {
                    "description": "BGP VRF router-id - Substring 'router-id' in 'router bgp 65101 > vrf PROD'",
                    "result": AntaTestStatus.SUCCESS,
                    "messages": [],
                },
                {
                    "description": "BGP VRF router-id - Substring 'router-id' in 'router bgp 65101 > vrf DEV'",
                    "result": AntaTestStatus.SUCCESS,
                    "messages": [],
                },
                {
                    "description": "BGP DEV VRF router-id - Substring 'router-id' in 'router bgp 65101 > vrf DEV'",
                    "result": AntaTestStatus.SUCCESS,
                    "messages": [],
                },
            ],
        },
    },
    (VerifyRunningConfig, "failure-nested-section-child-not-found"): {
        # first level matches but second level doesn't exist
        "eos_data": [
            {
                "cmds": {
                    "router bgp 65101": {
                        "cmds": {
                            "router-id 10.111.254.1": None,
                            "vrf DEV": {"cmds": {"router-id 10.0.2.1": None}},
                        }
                    }
                }
            }
        ],
        "inputs": {
            "rules": [
                {
                    "section": ["router bgp 65101", "vrf NONEXISTENT"],
                    "entries": [{"match": "router-id", "mode": "contains"}],
                },
            ]
        },
        "expected": {
            "result": AntaTestStatus.FAILURE,
            "messages": ["Section 'router bgp 65101 > vrf NONEXISTENT' - Not found in the running-config"],
            "atomic_results": [
                {
                    "description": "Section 'router bgp 65101 > vrf NONEXISTENT'",
                    "result": AntaTestStatus.FAILURE,
                    "messages": ["Not found in the running-config"],
                },
            ],
        },
    },
    (VerifyRunningConfig, "success-absent-in-section"): {
        # absent entries scoped to a section — prohibited commands not present in the section
        "eos_data": [
            {
                "cmds": {
                    "management ssh": {
                        "cmds": {
                            "cipher aes256-ctr aes256-cbc": None,
                        }
                    }
                }
            }
        ],
        "inputs": {
            "rules": [
                {
                    "section": ["management ssh"],
                    "entries": [
                        {"match": "fips restrictions", "absent": True, "description": "No FIPS mode"},
                        {"match": "telnet", "mode": "contains", "absent": True, "description": "No telnet reference"},
                        {"match": "password .+ 0 ", "mode": "regex", "absent": True, "description": "No plaintext passwords"},
                    ],
                },
            ]
        },
        "expected": {
            "result": AntaTestStatus.SUCCESS,
            "atomic_results": [
                {
                    "description": "No FIPS mode - Command 'fips restrictions' in 'management ssh'",
                    "result": AntaTestStatus.SUCCESS,
                    "messages": [],
                },
                {
                    "description": "No telnet reference - Substring 'telnet' in 'management ssh'",
                    "result": AntaTestStatus.SUCCESS,
                    "messages": [],
                },
                {
                    "description": "No plaintext passwords - Pattern 'password .+ 0 ' in 'management ssh'",
                    "result": AntaTestStatus.SUCCESS,
                    "messages": [],
                },
            ],
        },
    },
    (VerifyRunningConfig, "success-threshold-default-operator"): {
        # threshold without explicit operator — defaults to eq
        "eos_data": [
            {
                "cmds": {
                    "interface Ethernet1": {"cmds": {"mtu 9214": None}},
                }
            }
        ],
        "inputs": {
            "rules": [
                {
                    "section": ["interface Ethernet1"],
                    "entries": [{"match": "mtu (\\d+)", "mode": "regex", "description": "MTU check", "threshold": {"value": 9214}}],
                },
            ]
        },
        "expected": {
            "result": AntaTestStatus.SUCCESS,
            "atomic_results": [
                {
                    "description": "MTU check - Captured value of 'mtu (\\d+)' == 9214 in 'interface Ethernet1'",
                    "result": AntaTestStatus.SUCCESS,
                    "messages": [],
                },
            ],
        },
    },
    (VerifyRunningConfig, "failure-wildcard-section-no-match"): {
        # wildcard regex pattern matches zero sections — reported as section not found
        "eos_data": [
            {
                "cmds": {
                    "interface Ethernet1": {"cmds": {"no switchport": None}},
                }
            }
        ],
        "inputs": {
            "rules": [
                {
                    "section": ["interface Loopback\\d+"],
                    "entries": [{"match": "description", "mode": "contains", "description": "Loopback description"}],
                },
            ]
        },
        "expected": {
            "result": AntaTestStatus.FAILURE,
            "messages": ["Section 'interface Loopback\\d+' - Not found in the running-config"],
            "atomic_results": [
                {
                    "description": "Section 'interface Loopback\\d+'",
                    "result": AntaTestStatus.FAILURE,
                    "messages": ["Not found in the running-config"],
                },
            ],
        },
    },
    (VerifyRunningConfig, "failure-wildcard-threshold-mixed"): {
        # wildcard section + threshold — Ethernet1 passes (9214 >= 9000) but Ethernet2 fails (1500 < 9000)
        "eos_data": [
            {
                "cmds": {
                    "interface Ethernet1": {"cmds": {"mtu 9214": None}},
                    "interface Ethernet2": {"cmds": {"mtu 1500": None}},
                }
            }
        ],
        "inputs": {
            "rules": [
                {
                    "section": ["interface Ethernet\\d+"],
                    "entries": [
                        {
                            "match": "mtu (\\d+)",
                            "mode": "regex",
                            "description": "Jumbo MTU",
                            "threshold": {"value": 9000, "operator": "ge"},
                        }
                    ],
                },
            ]
        },
        "expected": {
            "result": AntaTestStatus.FAILURE,
            "messages": ["Jumbo MTU - Captured value of 'mtu (\\d+)' >= 9000 in 'interface Ethernet2' - Actual: 1500"],
            "atomic_results": [
                {
                    "description": "Jumbo MTU - Captured value of 'mtu (\\d+)' >= 9000 in 'interface Ethernet1'",
                    "result": AntaTestStatus.SUCCESS,
                    "messages": [],
                },
                {
                    "description": "Jumbo MTU - Captured value of 'mtu (\\d+)' >= 9000 in 'interface Ethernet2'",
                    "result": AntaTestStatus.FAILURE,
                    "messages": ["Actual: 1500"],
                },
            ],
        },
    },
}
