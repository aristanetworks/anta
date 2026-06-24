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
                # Scenario: single stanza — two entries: regex+threshold (eq) and contains
                {
                    "stanza": ["router bgp 65101"],
                    "description": "BGP routing configuration",
                    "entries": [
                        {"match": "maximum-paths (\\d+)", "mode": "regex", "threshold": {"value": 4, "operator": "eq"}},
                        {"match": "router-id", "mode": "contains"},
                    ],
                },
                # Scenario: top-level exact+absent:true — "no enable password" ≠ "enable password", absent check passes
                {
                    "description": "Prohibited global configuration",
                    "entries": [
                        # "no enable password" is a different exact key — absent:true on "enable password" passes
                        {
                            "match": "enable password",
                            "mode": "exact",
                            "absent": True,
                            "context": "Cleartext enable password must not be configured",
                        }
                    ],
                },
                # Scenario: stanza without rule description — atomic label falls back to "Stanza: <key>"
                {
                    "stanza": ["interface Ethernet1"],
                    "entries": [{"match": "no switchport", "context": "Ethernet1 must be a routed (Layer-3) port"}],
                },
                # Scenario: sub-interface stanza — two entries verify encapsulation and IP address presence
                {
                    "stanza": ["interface Ethernet1.100"],
                    "description": "Sub-interface encapsulation",
                    "entries": [
                        {"match": "encapsulation dot1q vlan 100"},
                        {"match": "ip address", "mode": "contains"},
                    ],
                },
            ]
        },
        "expected": {
            "result": AntaTestStatus.SUCCESS,
            "atomic_results": [
                {"description": "BGP routing configuration", "result": AntaTestStatus.SUCCESS, "messages": []},
                {"description": "BGP routing configuration", "result": AntaTestStatus.SUCCESS, "messages": []},
                {"description": "Prohibited global configuration", "result": AntaTestStatus.SUCCESS, "messages": []},
                {"description": "Stanza: interface Ethernet1", "result": AntaTestStatus.SUCCESS, "messages": []},
                {"description": "Sub-interface encapsulation", "result": AntaTestStatus.SUCCESS, "messages": []},
                {"description": "Sub-interface encapsulation", "result": AntaTestStatus.SUCCESS, "messages": []},
            ],
        },
    },
    (VerifyRunningConfig, "success-wildcard-stanza"): {
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
                    "stanza": ["interface Ethernet\\d+"],
                    "description": "Interface descriptions",
                    "entries": [{"match": "description", "mode": "contains"}],
                },
                # Scenario: same wildcard stanza + regex threshold — each matched stanza validated independently
                {
                    "stanza": ["interface Ethernet\\d+"],
                    "description": "Interface MTU policy",
                    "entries": [{"match": "mtu (\\d+)", "mode": "regex", "threshold": {"value": 1500, "operator": "ge"}}],
                },
                # Scenario: $ anchor — re.fullmatch makes it redundant but harmless; Ethernet1 only, still wildcard
                {
                    "stanza": ["interface Ethernet1$"],
                    "description": "Ethernet1 Layer-3",
                    "entries": [{"match": "no switchport"}],
                },
            ]
        },
        "expected": {
            "result": AntaTestStatus.SUCCESS,
            "atomic_results": [
                {"description": "Interface descriptions [interface Ethernet1]", "result": AntaTestStatus.SUCCESS, "messages": []},
                {"description": "Interface descriptions [interface Ethernet2]", "result": AntaTestStatus.SUCCESS, "messages": []},
                {"description": "Interface MTU policy [interface Ethernet1]", "result": AntaTestStatus.SUCCESS, "messages": []},
                {"description": "Interface MTU policy [interface Ethernet2]", "result": AntaTestStatus.SUCCESS, "messages": []},
                {"description": "Ethernet1 Layer-3 [interface Ethernet1]", "result": AntaTestStatus.SUCCESS, "messages": []},
            ],
        },
    },
    (VerifyRunningConfig, "success-nested-stanza"): {
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
                # Scenario: two-level exact stanza — navigates bgp > vrf DEV; validates router-id
                {
                    "stanza": ["router bgp 65101", "vrf DEV"],
                    "description": "BGP VRF DEV router-id",
                    "entries": [{"match": "router-id", "mode": "contains"}],
                },
                # Scenario: entries=[] — stanza existence check only; no atomics emitted on success
                {
                    "stanza": ["router bgp 65101"],
                    "description": "BGP is configured",
                    "entries": [],
                },
            ]
        },
        "expected": {
            "result": AntaTestStatus.SUCCESS,
            "atomic_results": [
                {"description": "BGP VRF DEV router-id", "result": AntaTestStatus.SUCCESS, "messages": []},
            ],
        },
    },
    (VerifyRunningConfig, "failure-multiline-match"): {
        # Covers: exact mode on a multiline key — a single character difference anywhere in the string fails the match
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
    (VerifyRunningConfig, "failure-mode-exact"): {
        # Covers: exact fails (cipher keywords in wrong order; MAC string is prefix of actual command) and exact+absent:true inside a stanza
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
                    "stanza": ["management ssh"],
                    "entries": [
                        # Cipher keywords are in a different order than the EOS canonical output — exact equality fails
                        {"match": "cipher aes128-ctr aes256-ctr aes256-cbc", "context": "Only approved SSH ciphers must be configured"},
                        # Match is missing the trailing umac-64@openssh.com that EOS appends — exact fails
                        {"match": "mac hmac-sha2-256 hmac-sha2-512"},
                        # fips restrictions is present in the stanza but the rule requires it to be absent
                        {"match": "fips restrictions", "mode": "exact", "absent": True},
                    ],
                }
            ]
        },
        "expected": {
            "result": AntaTestStatus.FAILURE,
            "messages": [
                "Stanza: management ssh - Only approved SSH ciphers must be configured",
                "Stanza: management ssh - Config: mac hmac-sha2-256 hmac-sha2-512 - Not found",
                "Stanza: management ssh - Config: fips restrictions - Expected to be absent",
            ],
            "atomic_results": [
                {"description": "Stanza: management ssh", "result": AntaTestStatus.FAILURE, "messages": ["Only approved SSH ciphers must be configured"]},
                {"description": "Stanza: management ssh", "result": AntaTestStatus.FAILURE, "messages": ["Config: mac hmac-sha2-256 hmac-sha2-512 - Not found"]},
                {"description": "Stanza: management ssh", "result": AntaTestStatus.FAILURE, "messages": ["Config: fips restrictions - Expected to be absent"]},
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
                # Scenario: two entries in one rule — exact+not found (context label); exact+absent found
                {
                    "entries": [
                        # Must be present — not found
                        {"match": "aaa authentication login default local", "context": "Local authentication must be the login default"},
                        # Must be absent — found
                        {"match": "aaa authorization exec default local", "mode": "exact", "absent": True},
                    ]
                },
                # Scenario: no description — atomic label falls back to "Config: <match>"
                {
                    "entries": [{"match": "ntp server", "mode": "contains"}],
                },
                # Scenario: description + context — both appear together in the failure message
                {
                    "description": "Syslog reachability",
                    "entries": [{"match": "logging host", "mode": "contains", "context": "At least one syslog server must be configured"}],
                },
            ]
        },
        "expected": {
            "result": AntaTestStatus.FAILURE,
            "messages": [
                "Config: aaa authentication login default local - Local authentication must be the login default",
                "Config: aaa authorization exec default local - Expected to be absent",
                "Config: ntp server - Not found",
                "Syslog reachability - At least one syslog server must be configured",
            ],
            "atomic_results": [
                {
                    "description": "Config: aaa authentication login default local",
                    "result": AntaTestStatus.FAILURE,
                    "messages": ["Local authentication must be the login default"],
                },
                {
                    "description": "Config: aaa authorization exec default local",
                    "result": AntaTestStatus.FAILURE,
                    "messages": ["Expected to be absent"],
                },
                {"description": "Config: ntp server", "result": AntaTestStatus.FAILURE, "messages": ["Not found"]},
                {"description": "Syslog reachability", "result": AntaTestStatus.FAILURE, "messages": ["At least one syslog server must be configured"]},
            ],
        },
    },
    (VerifyRunningConfig, "failure-top-level-no-recurse"): {
        # Covers: top-level rule (no stanza) must NOT match commands that exist only inside nested stanzas
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
                    "description": "Router-id at top level",
                    "entries": [{"match": "router-id", "mode": "contains"}],
                }
            ]
        },
        "expected": {
            "result": AntaTestStatus.FAILURE,
            "messages": ["Router-id at top level - Not found"],
            "atomic_results": [
                {"description": "Router-id at top level", "result": AntaTestStatus.FAILURE, "messages": ["Not found"]},
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
                    "stanza": ["router bgp 65101"],
                    "description": "BGP ECMP path count",
                    "entries": [{"match": "ecmp (\\d+)", "mode": "regex", "threshold": {"value": 4, "operator": "le"}}],
                },
                # Scenario: eq operator — captured restart-time 200 ≠ expected 300; check fails
                {
                    "stanza": ["router bgp 65101"],
                    "description": "BGP graceful-restart timer",
                    "entries": [{"match": "graceful-restart restart-time (\\d+)", "mode": "regex", "threshold": {"value": 300, "operator": "eq"}}],
                },
                # Scenario: ge operator with context — captured MTU 800 below minimum 9000; context replaces default message
                {
                    "stanza": ["interface Ethernet1"],
                    "description": "Uplink must have jumbo MTU",
                    "entries": [
                        {
                            "match": "mtu (\\d+)",
                            "mode": "regex",
                            "threshold": {"value": 9000, "operator": "ge"},
                            "context": "Interface MTU must be at least 9000",
                        }
                    ],
                },
            ]
        },
        "expected": {
            "result": AntaTestStatus.FAILURE,
            "messages": [
                "BGP ECMP path count - Config: ecmp (\\d+) - maximum-paths 8 ecmp 8 - Expected: value <= 4 Actual: 8",
                "BGP graceful-restart timer - Config: graceful-restart restart-time (\\d+) - graceful-restart restart-time 200 - Expected: value == 300 Actual: 200",
                "Uplink must have jumbo MTU - Interface MTU must be at least 9000",
            ],
            "atomic_results": [
                {
                    "description": "BGP ECMP path count",
                    "result": AntaTestStatus.FAILURE,
                    "messages": ["Config: ecmp (\\d+) - maximum-paths 8 ecmp 8 - Expected: value <= 4 Actual: 8"],
                },
                {
                    "description": "BGP graceful-restart timer",
                    "result": AntaTestStatus.FAILURE,
                    "messages": ["Config: graceful-restart restart-time (\\d+) - graceful-restart restart-time 200 - Expected: value == 300 Actual: 200"],
                },
                {
                    "description": "Uplink must have jumbo MTU",
                    "result": AntaTestStatus.FAILURE,
                    "messages": ["Interface MTU must be at least 9000"],
                },
            ],
        },
    },
    (VerifyRunningConfig, "failure-regex-threshold-no-stanza"): {
        # Covers: regex+threshold:le at top level — no stanza means no stanza prefix in the atomic failure message
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
            "messages": ["Config: logging buffered (\\d+) - logging buffered 3000000 debugging - Expected: value <= 2000000 Actual: 3000000"],
            "atomic_results": [
                {
                    "description": "Config: logging buffered (\\d+)",
                    "result": AntaTestStatus.FAILURE,
                    "messages": ["logging buffered 3000000 debugging - Expected: value <= 2000000 Actual: 3000000"],
                }
            ],
        },
    },
    (VerifyRunningConfig, "failure-stanza-regex-no-partial-match"): {
        "eos_data": [{"cmds": {"interface Ethernet11": {"cmds": {"no switchport": None}}}}],
        "inputs": {
            "rules": [
                # Scenario: no $ anchor — re.fullmatch still prevents partial match; Ethernet1 does not match Ethernet11
                {
                    "stanza": ["interface Ethernet1"],
                    "description": "Ethernet1 config",
                    "entries": [{"match": "no switchport"}],
                },
                # Scenario: $ anchor — redundant with re.fullmatch but harmless; same rejection result
                {
                    "stanza": ["interface Ethernet1$"],
                    "description": "Ethernet1 anchor config",
                    "entries": [{"match": "no switchport"}],
                },
            ]
        },
        "expected": {
            "result": AntaTestStatus.FAILURE,
            "messages": [
                "Ethernet1 config - Not found in running-config",
                "Ethernet1 anchor config - Not found in running-config",
            ],
            "atomic_results": [
                {"description": "Ethernet1 config", "result": AntaTestStatus.FAILURE, "messages": ["Not found in running-config"]},
                {"description": "Ethernet1 anchor config", "result": AntaTestStatus.FAILURE, "messages": ["Not found in running-config"]},
            ],
        },
    },
    (VerifyRunningConfig, "failure-stanza-not-found"): {
        "eos_data": [{"cmds": {"interface Ethernet1": {"cmds": {"no switchport": None}}}}],
        "inputs": {
            "rules": [
                # Scenario: stanza not found, no description — label falls back to "Stanza: <key>"
                {
                    "stanza": ["interface Ethernet1.100"],
                    "entries": [{"match": "encapsulation dot1q vlan 100"}],
                },
                # Scenario: stanza not found, with description — description used as atomic label directly
                {
                    "stanza": ["interface Ethernet99"],
                    "description": "Uplink Ethernet99 config",
                    "entries": [{"match": "no switchport"}],
                },
            ]
        },
        "expected": {
            "result": AntaTestStatus.FAILURE,
            "messages": [
                "Stanza: interface Ethernet1.100 - Not found in running-config",
                "Uplink Ethernet99 config - Not found in running-config",
            ],
            "atomic_results": [
                {"description": "Stanza: interface Ethernet1.100", "result": AntaTestStatus.FAILURE, "messages": ["Not found in running-config"]},
                {"description": "Uplink Ethernet99 config", "result": AntaTestStatus.FAILURE, "messages": ["Not found in running-config"]},
            ],
        },
    },
    (VerifyRunningConfig, "failure-wildcard-stanza"): {
        # Covers: wildcard stanza; only Ethernet2 fails — Ethernet1 passes, proving per-stanza atomicity
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
                    "stanza": ["interface Ethernet\\d+"],
                    "description": "Interface descriptions",
                    "entries": [{"match": "description", "mode": "contains", "context": "Every Ethernet interface must have a description"}],
                }
            ]
        },
        "expected": {
            "result": AntaTestStatus.FAILURE,
            "messages": ["Interface descriptions [interface Ethernet2] - Every Ethernet interface must have a description"],
            "atomic_results": [
                {"description": "Interface descriptions [interface Ethernet1]", "result": AntaTestStatus.SUCCESS, "messages": []},
                {
                    "description": "Interface descriptions [interface Ethernet2]",
                    "result": AntaTestStatus.FAILURE,
                    "messages": ["Every Ethernet interface must have a description"],
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
                    "description": "No SNMP community strings",
                    "entries": [{"match": "snmp-server community", "mode": "contains", "absent": True, "context": "SNMP community strings are prohibited"}],
                },
                # Scenario: regex+absent:true — plaintext secret pattern not matched; check passes
                {
                    "description": "No plaintext secrets",
                    "entries": [{"match": "username .+ secret 0 ", "mode": "regex", "absent": True, "context": "Plaintext secrets (type 0) are prohibited"}],
                },
                # Scenario: regex+absent:false — at least one command matches the logging host pattern
                {
                    "description": "Remote syslog configured",
                    "entries": [{"match": "logging host \\S+", "mode": "regex"}],
                },
                # Scenario: contains+absent:false — ntp server substring found in a command
                {
                    "description": "NTP server configured",
                    "entries": [{"match": "ntp server", "mode": "contains"}],
                },
            ]
        },
        "expected": {
            "result": AntaTestStatus.SUCCESS,
            "atomic_results": [
                {"description": "No SNMP community strings", "result": AntaTestStatus.SUCCESS, "messages": []},
                {"description": "No plaintext secrets", "result": AntaTestStatus.SUCCESS, "messages": []},
                {"description": "Remote syslog configured", "result": AntaTestStatus.SUCCESS, "messages": []},
                {"description": "NTP server configured", "result": AntaTestStatus.SUCCESS, "messages": []},
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
                    "description": "No SNMP community strings",
                    "entries": [{"match": "snmp-server community", "mode": "contains", "absent": True, "context": "SNMP community strings are prohibited"}],
                },
                # Scenario: contains mid-command — "authorization exec" is found inside the full aaa line; check fails
                {
                    "description": "No AAA exec authorization",
                    "entries": [{"match": "authorization exec", "mode": "contains", "absent": True, "context": "AAA exec authorization must not be configured"}],
                },
                # Scenario: regex+absent:true — plaintext secret 0 pattern matched; check fails
                {
                    "description": "No plaintext secrets",
                    "entries": [{"match": "username .+ secret 0 ", "mode": "regex", "absent": True, "context": "Plaintext secrets (type 0) are prohibited"}],
                },
            ]
        },
        "expected": {
            "result": AntaTestStatus.FAILURE,
            "messages": [
                "No SNMP community strings - SNMP community strings are prohibited",
                "No AAA exec authorization - AAA exec authorization must not be configured",
                "No plaintext secrets - Plaintext secrets (type 0) are prohibited",
            ],
            "atomic_results": [
                {"description": "No SNMP community strings", "result": AntaTestStatus.FAILURE, "messages": ["SNMP community strings are prohibited"]},
                {"description": "No AAA exec authorization", "result": AntaTestStatus.FAILURE, "messages": ["AAA exec authorization must not be configured"]},
                {"description": "No plaintext secrets", "result": AntaTestStatus.FAILURE, "messages": ["Plaintext secrets (type 0) are prohibited"]},
            ],
        },
    },
    (VerifyRunningConfig, "failure-regex-threshold-non-numeric-capture"): {
        # Covers: regex matches but capture group is non-numeric — clean failure instead of ValueError crash
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
            "messages": ["Config: description (\\S+) - description Uplink - Capture group is not numeric: 'Uplink'"],
            "atomic_results": [
                {
                    "description": "Config: description (\\S+)",
                    "result": AntaTestStatus.FAILURE,
                    "messages": ["description Uplink - Capture group is not numeric: 'Uplink'"],
                }
            ],
        },
    },
    (VerifyRunningConfig, "success-nested-wildcard-stanza"): {
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
                    "stanza": ["router bgp \\d+", "vrf .*"],
                    "description": "BGP VRF router-ids",
                    "entries": [{"match": "router-id", "mode": "contains"}],
                },
                # Scenario: regex+exact — only DEV matched at second level; one atomic result
                {
                    "stanza": ["router bgp \\d+", "vrf DEV"],
                    "description": "BGP DEV VRF router-id",
                    "entries": [{"match": "router-id", "mode": "contains"}],
                },
            ]
        },
        "expected": {
            "result": AntaTestStatus.SUCCESS,
            "atomic_results": [
                {"description": "BGP VRF router-ids [router bgp 65101 > vrf PROD]", "result": AntaTestStatus.SUCCESS, "messages": []},
                {"description": "BGP VRF router-ids [router bgp 65101 > vrf DEV]", "result": AntaTestStatus.SUCCESS, "messages": []},
                {"description": "BGP DEV VRF router-id [router bgp 65101 > vrf DEV]", "result": AntaTestStatus.SUCCESS, "messages": []},
            ],
        },
    },
}
