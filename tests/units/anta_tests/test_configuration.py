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
        # Covers: happy path across all three stanza types — single stanza (contains, regex+threshold), top-level (exact+absent:true),
        #  stanza with no rule description
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
                {
                    "stanza": ["router bgp 65101"],
                    "description": "BGP routing configuration",
                    "entries": [
                        {"match": "maximum-paths (\\d+)", "mode": "regex", "threshold": {"value": 4, "operator": "eq"}},
                        {"match": "router-id", "mode": "contains"},
                    ],
                },
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
                {
                    "stanza": ["interface Ethernet1"],
                    "entries": [{"match": "no switchport", "context": "Ethernet1 must be a routed (Layer-3) port"}],
                },
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
        # Covers: regex fallback matches Ethernet1/2 but excludes Management0; each matched stanza produces its own atomic result
        "eos_data": [
            {
                "cmds": {
                    "interface Ethernet1": {"cmds": {"description WAN": None, "no switchport": None}},
                    "interface Ethernet2": {"cmds": {"description LAN": None, "no switchport": None}},
                    "interface Management0": {"cmds": {"description MGMT": None}},
                }
            }
        ],
        "inputs": {
            "rules": [
                {
                    "stanza": ["interface Ethernet\\d+"],
                    "description": "Interface descriptions",
                    "entries": [{"match": "description", "mode": "contains"}],
                }
            ]
        },
        "expected": {
            "result": AntaTestStatus.SUCCESS,
            "atomic_results": [
                {"description": "Interface descriptions [interface Ethernet1]", "result": AntaTestStatus.SUCCESS, "messages": []},
                {"description": "Interface descriptions [interface Ethernet2]", "result": AntaTestStatus.SUCCESS, "messages": []},
            ],
        },
    },
    (VerifyRunningConfig, "success-nested-stanza"): {
        # Covers: two-level exact stanza navigation
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
                {
                    "stanza": ["router bgp 65101", "vrf DEV"],
                    "description": "BGP VRF DEV router-id",
                    "entries": [{"match": "router-id", "mode": "contains"}],
                }
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
    (VerifyRunningConfig, "failure-mode-absent"): {
        # Covers: exact not-found and exact+absent:true, both at top level (no stanza)
        "eos_data": [
            {
                "cmds": {
                    "aaa authorization exec default local": None,
                }
            }
        ],
        "inputs": {
            "rules": [
                {
                    "entries": [
                        # Must be present — not found
                        {"match": "aaa authentication login default local", "context": "Local authentication must be the login default"},
                        # Must be absent — found
                        {"match": "aaa authorization exec default local", "mode": "exact", "absent": True},
                    ]
                }
            ]
        },
        "expected": {
            "result": AntaTestStatus.FAILURE,
            "messages": [
                "Config: aaa authentication login default local - Local authentication must be the login default",
                "Config: aaa authorization exec default local - Expected to be absent",
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
            ],
        },
    },
    (VerifyRunningConfig, "failure-regex-threshold-le"): {
        # Covers: regex mode + threshold le — captured ECMP count (8) exceeds the allowed maximum (4)
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
        "inputs": {
            "rules": [
                {
                    "stanza": ["router bgp 65101"],
                    "description": "BGP ECMP exact path count",
                    "entries": [{"match": "ecmp (\\d+)", "mode": "regex", "threshold": {"value": 4, "operator": "le"}}],
                }
            ]
        },
        "expected": {
            "result": AntaTestStatus.FAILURE,
            "messages": ["BGP ECMP exact path count - Config: ecmp (\\d+) - maximum-paths 8 ecmp 8 - Expected: value <= 4 Actual: 8"],
            "atomic_results": [
                {
                    "description": "BGP ECMP exact path count",
                    "result": AntaTestStatus.FAILURE,
                    "messages": ["Config: ecmp (\\d+) - maximum-paths 8 ecmp 8 - Expected: value <= 4 Actual: 8"],
                }
            ],
        },
    },
    (VerifyRunningConfig, "failure-regex-threshold-ge"): {
        # Covers: regex mode + threshold ge + context — MTU (800) below the required minimum (9000)
        "eos_data": [{"cmds": {"interface Ethernet1": {"comments": [], "cmds": {"mtu 800": None, "no switchport": None}}}}],
        "inputs": {
            "rules": [
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
                }
            ]
        },
        "expected": {
            "result": AntaTestStatus.FAILURE,
            "messages": ["Uplink must have jumbo MTU - Interface MTU must be at least 9000"],
            "atomic_results": [{"description": "Uplink must have jumbo MTU", "result": AntaTestStatus.FAILURE, "messages": ["Interface MTU must be at least 9000"]}],
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
    (VerifyRunningConfig, "failure-stanza-not-found"): {
        # Covers: stanza not found — no description uses fallback label; with description uses it directly
        "eos_data": [{"cmds": {"interface Ethernet1": {"cmds": {"no switchport": None}}}}],
        "inputs": {
            "rules": [
                {
                    "stanza": ["interface Ethernet1.100"],
                    "entries": [{"match": "encapsulation dot1q vlan 100"}],
                },
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
    (VerifyRunningConfig, "failure-contains-not-found"): {
        # Covers: contains not-found — bare Config label (no description) and described label with context
        "eos_data": [{"cmds": {"logging buffered 3000000 debugging": None}}],
        "inputs": {
            "rules": [
                {
                    "entries": [{"match": "ntp server", "mode": "contains"}],
                },
                {
                    "description": "Syslog reachability",
                    "entries": [{"match": "logging host", "mode": "contains", "context": "At least one syslog server must be configured"}],
                },
            ]
        },
        "expected": {
            "result": AntaTestStatus.FAILURE,
            "messages": [
                "Config: ntp server - Not found",
                "Syslog reachability - At least one syslog server must be configured",
            ],
            "atomic_results": [
                {"description": "Config: ntp server", "result": AntaTestStatus.FAILURE, "messages": ["Not found"]},
                {"description": "Syslog reachability", "result": AntaTestStatus.FAILURE, "messages": ["At least one syslog server must be configured"]},
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
        # Covers: contains+absent:true and regex+absent:true passing when no command matches
        "eos_data": [{"cmds": {"ip routing": None, "username admin privilege 15": None}}],
        "inputs": {
            "rules": [
                {
                    "description": "No SNMP community strings",
                    "entries": [{"match": "snmp-server community", "mode": "contains", "absent": True, "context": "SNMP community strings are prohibited"}],
                },
                {
                    "description": "No plaintext secrets",
                    "entries": [{"match": "username .+ secret 0 ", "mode": "regex", "absent": True, "context": "Plaintext secrets (type 0) are prohibited"}],
                },
            ]
        },
        "expected": {
            "result": AntaTestStatus.SUCCESS,
            "atomic_results": [
                {"description": "No SNMP community strings", "result": AntaTestStatus.SUCCESS, "messages": []},
                {"description": "No plaintext secrets", "result": AntaTestStatus.SUCCESS, "messages": []},
            ],
        },
    },
    (VerifyRunningConfig, "failure-contains-absent-substring"): {
        # Covers: contains+absent:true fails when the match string appears mid-command, not just as a prefix
        "eos_data": [{"cmds": {"aaa authorization exec default local": None, "ip routing": None}}],
        "inputs": {
            "rules": [
                {
                    "description": "No AAA exec authorization",
                    "entries": [{"match": "authorization exec", "mode": "contains", "absent": True, "context": "AAA exec authorization must not be configured"}],
                }
            ]
        },
        "expected": {
            "result": AntaTestStatus.FAILURE,
            "messages": ["No AAA exec authorization - AAA exec authorization must not be configured"],
            "atomic_results": [
                {"description": "No AAA exec authorization", "result": AntaTestStatus.FAILURE, "messages": ["AAA exec authorization must not be configured"]},
            ],
        },
    },
    (VerifyRunningConfig, "failure-contains-absent"): {
        # Covers: contains+absent:true failure — prohibited command found in running-config
        "eos_data": [{"cmds": {"snmp-server community public ro": None, "ip routing": None}}],
        "inputs": {
            "rules": [
                {
                    "description": "No SNMP community strings",
                    "entries": [{"match": "snmp-server community", "mode": "contains", "absent": True, "context": "SNMP community strings are prohibited"}],
                }
            ]
        },
        "expected": {
            "result": AntaTestStatus.FAILURE,
            "messages": ["No SNMP community strings - SNMP community strings are prohibited"],
            "atomic_results": [
                {"description": "No SNMP community strings", "result": AntaTestStatus.FAILURE, "messages": ["SNMP community strings are prohibited"]},
            ],
        },
    },
    (VerifyRunningConfig, "failure-regex-absent"): {
        # Covers: regex+absent:true failure — pattern matches a command that must be absent
        "eos_data": [{"cmds": {"username admin secret 0 plaintext123": None, "ip routing": None}}],
        "inputs": {
            "rules": [
                {
                    "description": "No plaintext secrets",
                    "entries": [{"match": "username .+ secret 0 ", "mode": "regex", "absent": True, "context": "Plaintext secrets (type 0) are prohibited"}],
                }
            ]
        },
        "expected": {
            "result": AntaTestStatus.FAILURE,
            "messages": ["No plaintext secrets - Plaintext secrets (type 0) are prohibited"],
            "atomic_results": [
                {"description": "No plaintext secrets", "result": AntaTestStatus.FAILURE, "messages": ["Plaintext secrets (type 0) are prohibited"]},
            ],
        },
    },
    (VerifyRunningConfig, "failure-regex-threshold-eq"): {
        # Covers: regex+threshold:eq failure — captured BGP restart-time (200) does not equal required (300)
        "eos_data": [{"cmds": {"router bgp 65101": {"cmds": {"graceful-restart restart-time 200": None, "router-id 10.0.0.1": None}}}}],
        "inputs": {
            "rules": [
                {
                    "stanza": ["router bgp 65101"],
                    "description": "BGP graceful-restart timer",
                    "entries": [{"match": "graceful-restart restart-time (\\d+)", "mode": "regex", "threshold": {"value": 300, "operator": "eq"}}],
                }
            ]
        },
        "expected": {
            "result": AntaTestStatus.FAILURE,
            "messages": [
                "BGP graceful-restart timer - Config: graceful-restart restart-time (\\d+) - graceful-restart restart-time 200 - Expected: value == 300 Actual: 200"
            ],
            "atomic_results": [
                {
                    "description": "BGP graceful-restart timer",
                    "result": AntaTestStatus.FAILURE,
                    "messages": ["Config: graceful-restart restart-time (\\d+) - graceful-restart restart-time 200 - Expected: value == 300 Actual: 200"],
                }
            ],
        },
    },
    (VerifyRunningConfig, "success-nested-wildcard-stanza"): {
        # Covers: regex+regex nested (both VRFs) and regex+exact nested (vrf DEV only)
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
                {
                    "stanza": ["router bgp \\d+", "vrf .*"],
                    "description": "BGP VRF router-ids",
                    "entries": [{"match": "router-id", "mode": "contains"}],
                },
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
                {"description": "BGP DEV VRF router-id", "result": AntaTestStatus.SUCCESS, "messages": []},
            ],
        },
    },
}
