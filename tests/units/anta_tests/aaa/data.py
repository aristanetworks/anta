# Copyright (c) 2023 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Data for testing anta.tests.aaa"""

from typing import Any, Dict, List

INPUT_TACACS_SRC_INTF: List[Dict[str, Any]] = [
    {
        "name": "success",
        "eos_data": [
            {
                "tacacsServers": [
                    {
                       'serverInfo': {'hostname': '10.22.10.91', 'authport': 49, 'vrf': 'MGMT'},
                    }
                ],
                'groups': {'GROUP1': {'serverGroup': 'TACACS+', 'members': [{'hostname': 'SERVER1', 'authport': 49, 'vrf': 'MGMT'}]}},
                'srcIntf': {'MGMT': 'Management0'},
            }
        ],
        "inputs": ("Management0", "MGMT"),
        "expected": {"result": "success"},
    },
    {
        "name": "failure-not-configured",
        "eos_data": [
            {
                "tacacsServers": [],
                'groups': {},
                'srcIntf': {},
            }
        ],
        "inputs": ("Management0", "MGMT"),
        "expected": {"result": "failure", "messages": ["Source-interface Management0 is not configured in VRF MGMT"]}
    },
    {
        "name": "failure-wrong-intf",
        "eos_data": [
            {
                "tacacsServers": [
                    {
                       'serverInfo': {'hostname': '10.22.10.91', 'authport': 49, 'vrf': 'MGMT'},
                    }
                ],
                'groups': {'GROUP1': {'serverGroup': 'TACACS+', 'members': [{'hostname': 'SERVER1', 'authport': 49, 'vrf': 'MGMT'}]}},
                'srcIntf': {'MGMT': 'Management1'},
            }
        ],
        "inputs": ("Management0", "MGMT"),
        "expected": {"result": "failure", "messages": ["Wrong source-interface configured in VRF MGMT"]}
    },
    {
        "name": "failure-wrong-vrf",
        "eos_data": [
            {
                "tacacsServers": [
                    {
                       'serverInfo': {'hostname': '10.22.10.91', 'authport': 49, 'vrf': 'MGMT'},
                    }
                ],
                'groups': {'GROUP1': {'serverGroup': 'TACACS+', 'members': [{'hostname': 'SERVER1', 'authport': 49, 'vrf': 'MGMT'}]}},
                'srcIntf': {'PROD': 'Management0'},
            }
        ],
        "inputs": ("Management0", "MGMT"),
        "expected": {"result": "failure", "messages": ["Source-interface Management0 is not configured in VRF MGMT"]}
    },
    {
        "name": "skipped-no-vrf",
        "eos_data": [
            {
                "tacacsServers": [],
                'groups': {},
                'srcIntf': {},
            }
        ],
        "inputs": ("Management0", ""),
        "expected_result": "skipped", "messages": ["VerifyTacacsSourceIntf did not run because intf or vrf was not supplied"]
    },
    {
        "name": "skipped-no-intf",
        "eos_data": [
            {
                "tacacsServers": [],
                'groups': {},
                'srcIntf': {},
            }
        ],
        "inputs": ("", "MGMT"),
        "expected_result": "skipped", "messages": ["VerifyTacacsSourceIntf did not run because intf or vrf was not supplied"]
    },
]

INPUT_TACACS_SERVERS: List[Dict[str, Any]] = [
    {
        "name": "success",
        "eos_data": [
            {
                "tacacsServers": [
                    {
                       'serverInfo': {'hostname': '10.22.10.91', 'authport': 49, 'vrf': 'MGMT'},
                    }
                ],
                'groups': {'GROUP1': {'serverGroup': 'TACACS+', 'members': [{'hostname': 'SERVER1', 'authport': 49, 'vrf': 'MGMT'}]}},
                'srcIntf': {'MGMT': 'Management0'},
            }
        ],
        "inputs": (["10.22.10.91"], "MGMT"),
        "expected": {"result": "success"},
    },
    {
        "name": "failure-no-servers",
        "eos_data": [
            {
                "tacacsServers": [],
                'groups': {},
                'srcIntf': {},
            }
        ],
        "inputs": (["10.22.10.91"], "MGMT"),
        "expected": {"result": "failure", "messages": ["No TACACS servers are configured"]}
    },
    {
        "name": "failure-not-configured",
        "eos_data": [
            {
                "tacacsServers": [
                    {
                       'serverInfo': {'hostname': '10.22.10.91', 'authport': 49, 'vrf': 'MGMT'},
                    }
                ],
                'groups': {'GROUP1': {'serverGroup': 'TACACS+', 'members': [{'hostname': 'SERVER1', 'authport': 49, 'vrf': 'MGMT'}]}},
                'srcIntf': {'MGMT': 'Management0'},
            }
        ],
        "inputs": (["10.22.10.91", "10.22.10.92"], "MGMT"),
        "expected": {"result": "failure", "messages": ["TACACS servers ['10.22.10.92'] are not configured in VRF MGMT"]}
    },
    {
        "name": "failure-wrong-vrf",
        "eos_data": [
            {
                "tacacsServers": [
                    {
                       'serverInfo': {'hostname': '10.22.10.91', 'authport': 49, 'vrf': 'PROD'},
                    }
                ],
                'groups': {'GROUP1': {'serverGroup': 'TACACS+', 'members': [{'hostname': 'SERVER1', 'authport': 49, 'vrf': 'MGMT'}]}},
                'srcIntf': {'MGMT': 'Management0'},
            }
        ],
        "inputs": (["10.22.10.91"], "MGMT"),
        "expected": {"result": "failure", "messages": ["TACACS servers ['10.22.10.91'] are not configured in VRF MGMT"]}
    },
    {
        "name": "skipped-no-servers",
        "eos_data": [
            {
                "tacacsServers": [],
                'groups': {},
                'srcIntf': {},
            }
        ],
        "inputs": ([], "MGMT"),
        "expected_result": "skipped", "messages": ["VerifyTacacsServers did not run because servers or vrf were not supplied"]
    },
    {
        "name": "skipped-no-vrf",
        "eos_data": [
            {
                "tacacsServers": [],
                'groups': {},
                'srcIntf': {},
            }
        ],
        "inputs": (["10.22.10.91"], ""),
        "expected_result": "skipped", "messages": ["VerifyTacacsServers did not run because servers or vrf were not supplied"]
    },
]

INPUT_TACACS_SERVER_GROUPS: List[Dict[str, Any]] = [
    {
        "name": "success",
        "eos_data": [
            {
                "tacacsServers": [
                    {
                       'serverInfo': {'hostname': '10.22.10.91', 'authport': 49, 'vrf': 'MGMT'},
                    }
                ],
                'groups': {'GROUP1': {'serverGroup': 'TACACS+', 'members': [{'hostname': 'SERVER1', 'authport': 49, 'vrf': 'MGMT'}]}},
                'srcIntf': {'MGMT': 'Management0'},
            }
        ],
        "inputs": ["GROUP1"],
        "expected": {"result": "success"},
    },
    {
        "name": "failure-no-server-groups",
        "eos_data": [
            {
                "tacacsServers": [],
                'groups': {},
                'srcIntf': {},
            }
        ],
        "inputs": ["GROUP1"],
        "expected": {"result": "failure", "messages": ["No TACACS server group(s) are configured"]}
    },
    {
        "name": "failure-not-configured",
        "eos_data": [
            {
                "tacacsServers": [
                    {
                       'serverInfo': {'hostname': '10.22.10.91', 'authport': 49, 'vrf': 'MGMT'},
                    }
                ],
                'groups': {'GROUP2': {'serverGroup': 'TACACS+', 'members': [{'hostname': 'SERVER1', 'authport': 49, 'vrf': 'MGMT'}]}},
                'srcIntf': {'MGMT': 'Management0'},
            }
        ],
        "inputs": ["GROUP1"],
        "expected": {"result": "failure", "messages": ["TACACS server group(s) ['GROUP1'] are not configured"]}
    },
    {
        "name": "skipped-no-server-groups",
        "eos_data": [
            {
                "tacacsServers": [],
                'groups': {},
                'srcIntf': {},
            }
        ],
        "inputs": None,
        "expected_result": "skipped", "messages": ["VerifyTacacsServerGroups did not run because groups were not supplied"]
    },
]

INPUT_AUTHEN_METHODS: List[Dict[str, Any]] = [
    {
        "name": "success-login-enable",
        "eos_data": [
             {
                "loginAuthenMethods": {
                    "default": {
                        "methods": [
                            "group tacacs+",
                            "local"
                        ]
                    },
                    "login": {
                        "methods": [
                            "group tacacs+",
                            "local"
                        ]
                    }
                },
                "enableAuthenMethods": {
                    "default": {
                        "methods": [
                            "group tacacs+",
                            "local"
                        ]
                    }
                },
                "dot1xAuthenMethods": {
                    "default": {
                        "methods": [
                            "group radius"
                        ]
                    }
                }
              }
        ],
        "inputs": (["tacacs+", "local"], ["login", "enable"]),
        "expected": {"result": "success"},
    },
    {
        "name": "success-dot1x",
        "eos_data": [
             {
                "loginAuthenMethods": {
                    "default": {
                        "methods": [
                            "group tacacs+",
                            "local"
                        ]
                    },
                    "login": {
                        "methods": [
                            "group tacacs+",
                            "local"
                        ]
                    }
                },
                "enableAuthenMethods": {
                    "default": {
                        "methods": [
                            "group tacacs+",
                            "local"
                        ]
                    }
                },
                "dot1xAuthenMethods": {
                    "default": {
                        "methods": [
                            "group radius"
                        ]
                    }
                }
              }
        ],
        "inputs": (["radius"], ["dot1x"]),
        "expected": {"result": "success"},
    },
    {
        "name": "failure-no-login-console",
        "eos_data": [
             {
                "loginAuthenMethods": {
                    "default": {
                        "methods": [
                            "group tacacs+",
                            "local"
                        ]
                    }
                },
                "enableAuthenMethods": {
                    "default": {
                        "methods": [
                            "group tacacs+",
                            "local"
                        ]
                    }
                },
                "dot1xAuthenMethods": {
                    "default": {
                        "methods": [
                            "group radius"
                        ]
                    }
                }
              }
        ],
        "inputs": (["tacacs+", "local"], ["login", "enable"]),
        "expected": {"result": "failure", "messages": ["AAA authentication methods are not configured for login console"]}
    },
    {
        "name": "failure-login-console",
        "eos_data": [
             {
                "loginAuthenMethods": {
                    "default": {
                        "methods": [
                            "group tacacs+",
                            "local"
                        ]
                    },
                    "login": {
                        "methods": [
                            "group radius",
                            "local"
                        ]
                    }
                },
                "enableAuthenMethods": {
                    "default": {
                        "methods": [
                            "group tacacs+",
                            "local"
                        ]
                    }
                },
                "dot1xAuthenMethods": {
                    "default": {
                        "methods": [
                            "group radius"
                        ]
                    }
                }
              }
        ],
        "inputs": (["tacacs+", "local"], ["login", "enable"]),
        "expected": {"result": "failure", "messages": ["AAA authentication methods ['tacacs+', 'local'] are not matching for login console"]}
    },
    {
        "name": "failure-login-default",
        "eos_data": [
             {
                "loginAuthenMethods": {
                    "default": {
                        "methods": [
                            "group radius",
                            "local"
                        ]
                    },
                    "login": {
                        "methods": [
                            "group tacacs+",
                            "local"
                        ]
                    }
                },
                "enableAuthenMethods": {
                    "default": {
                        "methods": [
                            "group tacacs+",
                            "local"
                        ]
                    }
                },
                "dot1xAuthenMethods": {
                    "default": {
                        "methods": [
                            "group radius"
                        ]
                    }
                }
              }
        ],
        "inputs": (["tacacs+", "local"], ["login", "enable"]),
        "expected": {"result": "failure", "messages": ["AAA authentication methods ['tacacs+', 'local'] are not matching for ['login']"]}
    },
    {
        "name": "error-wrong-auth-type",
        "eos_data": [
             {
                "loginAuthenMethods": {},
                "enableAuthenMethods": {},
                "dot1xAuthenMethods": {}
              }
        ],
        "inputs": (["tacacs+", "local"], ["login", "enable", "bad"]),
        "expected": {"result": "error"}, "messages": ["ValueError (Wrong parameter provided in auth_types. Valid parameters are: ['login', 'enable', 'dot1x'])"]
    },
    {
        "name": "error-too-many-auth-type",
        "eos_data": [
             {
                "loginAuthenMethods": {},
                "enableAuthenMethods": {},
                "dot1xAuthenMethods": {}
              }
        ],
        "inputs": (["tacacs+", "local"], ["login", "enable", "dot1x", "bad"]),
        "expected": {"result": "error"}, "messages": ["ValueError (Too many parameters provided in auth_types. Valid parameters are: ['login', 'enable', 'dot1x'])"]
    },
    {
        "name": "skipped-no-methods",
        "eos_data": [
             {
                "loginAuthenMethods": {},
                "enableAuthenMethods": {},
                "dot1xAuthenMethods": {}
              }
        ],
        "inputs": ([], ["login", "enable"]),
        "expected_result": "skipped", "messages": ["VerifyAuthenMethods did not run because methods or auth_types were not supplied"]
    },
    {
        "name": "skipped-no-auth-types",
        "eos_data": [
             {
                "loginAuthenMethods": {},
                "enableAuthenMethods": {},
                "dot1xAuthenMethods": {}
              }
        ],
        "inputs": (["tacacs+", "local"], []),
        "expected_result": "skipped", "messages": ["VerifyAuthenMethods did not run because methods or auth_types were not supplied"]
    },
]

INPUT_AUTHZ_METHODS: List[Dict[str, Any]] = [
    {
        "name": "success",
        "eos_data": [
            {
                "commandsAuthzMethods": {
                    "privilege0-15": {
                        "methods": [
                            "group tacacs+",
                            "local"
                        ]
                    }
                },
                "execAuthzMethods": {
                    "exec": {
                        "methods": [
                            "group tacacs+",
                            "local"
                        ]
                    }
                }
            }
        ],
        "inputs": (["tacacs+", "local"], ["commands", "exec"]),
        "expected": {"result": "success"},
    },
    {
        "name": "failure-commands",
        "eos_data": [
            {
                "commandsAuthzMethods": {
                    "privilege0-15": {
                        "methods": [
                            "group radius",
                            "local"
                        ]
                    }
                },
                "execAuthzMethods": {
                    "exec": {
                        "methods": [
                            "group tacacs+",
                            "local"
                        ]
                    }
                }
            }
        ],
        "inputs": (["tacacs+", "local"], ["commands", "exec"]),
        "expected": {"result": "failure", "messages": ["AAA authorization methods ['tacacs+', 'local'] are not matching for ['commands']"]}
    },
    {
        "name": "failure-exec",
        "eos_data": [
            {
                "commandsAuthzMethods": {
                    "privilege0-15": {
                        "methods": [
                            "group tacacs+",
                            "local"
                        ]
                    }
                },
                "execAuthzMethods": {
                    "exec": {
                        "methods": [
                            "group radius",
                            "local"
                        ]
                    }
                }
            }
        ],
        "inputs": (["tacacs+", "local"], ["commands", "exec"]),
        "expected": {"result": "failure", "messages": ["AAA authorization methods ['tacacs+', 'local'] are not matching for ['exec']"]}
    },
    {
        "name": "error-wrong-auth-type",
        "eos_data": [
            {
                "commandsAuthzMethods": {},
                "execAuthzMethods": {}
            }
        ],
        "inputs": (["tacacs+", "local"], ["commands", "bad"]),
        "expected": {"result": "error"}, "messages": ["ValueError (Wrong parameter provided in auth_types. Valid parameters are: ['commands', 'exec'])"]
    },
    {
        "name": "error-too-many-auth-type",
        "eos_data": [
            {
                "commandsAuthzMethods": {},
                "execAuthzMethods": {}
            }
        ],
        "inputs": (["tacacs+", "local"], ["commands", "exec", "bad"]),
        "expected": {"result": "error"}, "messages": ["ValueError (Too many parameters provided in auth_types. Valid parameters are: ['commands', 'exec'])"]
    },
    {
        "name": "skipped-no-methods",
        "eos_data": [
             {
                "commandsAuthzMethods": {},
                "execAuthzMethods": {}
              }
        ],
        "inputs": ([], ["commands", "exec"]),
        "expected_result": "skipped", "messages": ["VerifyAuthzMethods did not run because methods or auth_types were not supplied"]
    },
    {
        "name": "skipped-no-auth-types",
        "eos_data": [
             {
                "commandsAuthzMethods": {},
                "execAuthzMethods": {}
              }
        ],
        "inputs": (["tacacs+", "local"], []),
        "expected_result": "skipped", "messages": ["VerifyAuthzMethods did not run because methods or auth_types were not supplied"]
    },
]

INPUT_ACCT_DEFAULT_METHODS: List[Dict[str, Any]] = [
    {
        "name": "success-commands-exec-system",
        "eos_data": [
            {
                "commandsAcctMethods": {
                    "privilege0-15": {
                        "defaultAction": "startStop",
                        "defaultMethods": [
                            "group tacacs+",
                            "logging"
                        ],
                        "consoleMethods": []
                    }
                },
                "execAcctMethods": {
                    "exec": {
                        "defaultAction": "startStop",
                        "defaultMethods": [
                            "group tacacs+",
                            "logging"
                        ],
                        "consoleMethods": []
                    }
                },
                "systemAcctMethods": {
                    "system": {
                        "defaultAction": "startStop",
                        "defaultMethods": [
                            "group tacacs+",
                            "logging"
                        ],
                        "consoleMethods": []
                    }
                },
                "dot1xAcctMethods": {
                    "dot1x": {
                        "defaultMethods": [],
                        "consoleMethods": []
                    }
                }
            }
        ],
        "inputs": (["tacacs+", "logging"], ["commands", "exec", "system"]),
        "expected": {"result": "success"},
    },
    {
        "name": "success-dot1x",
        "eos_data": [
            {
                "commandsAcctMethods": {
                    "privilege0-15": {
                        "defaultAction": "startStop",
                        "defaultMethods": [
                            "group tacacs+",
                            "logging"
                        ],
                        "consoleMethods": []
                    }
                },
                "execAcctMethods": {
                    "exec": {
                        "defaultAction": "startStop",
                        "defaultMethods": [
                            "group tacacs+",
                            "logging"
                        ],
                        "consoleMethods": []
                    }
                },
                "systemAcctMethods": {
                    "system": {
                        "defaultAction": "startStop",
                        "defaultMethods": [
                            "group tacacs+",
                            "logging"
                        ],
                        "consoleMethods": []
                    }
                },
                "dot1xAcctMethods": {
                    "dot1x": {
                        "defaultAction": "startStop",
                        "defaultMethods": [
                            "group radius",
                            "logging"
                        ],
                        "consoleMethods": []
                    }
                }
            }
        ],
        "inputs": (["radius", "logging"], ["dot1x"]),
        "expected": {"result": "success"},
    },
    {
        "name": "failure-not-configured",
        "eos_data": [
            {
                "commandsAcctMethods": {
                    "privilege0-15": {
                        "defaultMethods": [],
                        "consoleMethods": []
                    }
                },
                "execAcctMethods": {
                    "exec": {
                        "defaultAction": "startStop",
                        "defaultMethods": [
                            "group tacacs+",
                            "logging"
                        ],
                        "consoleMethods": []
                    }
                },
                "systemAcctMethods": {
                    "system": {
                        "defaultAction": "startStop",
                        "defaultMethods": [
                            "group tacacs+",
                            "logging"
                        ],
                        "consoleMethods": []
                    }
                },
                "dot1xAcctMethods": {
                    "dot1x": {
                        "defaultMethods": [],
                        "consoleMethods": []
                    }
                }
            }
        ],
        "inputs": (["tacacs+", "logging"], ["commands", "exec", "system"]),
        "expected": {"result": "failure", "messages": ["AAA default accounting is not configured for ['commands']"]}
    },
    {
        "name": "failure-not-matching",
        "eos_data": [
            {
                "commandsAcctMethods": {
                    "privilege0-15": {
                        "defaultAction": "startStop",
                        "defaultMethods": [
                            "group radius",
                            "logging"
                        ],
                        "consoleMethods": []
                    }
                },
                "execAcctMethods": {
                    "exec": {
                        "defaultAction": "startStop",
                        "defaultMethods": [
                            "group tacacs+",
                            "logging"
                        ],
                        "consoleMethods": []
                    }
                },
                "systemAcctMethods": {
                    "system": {
                        "defaultAction": "startStop",
                        "defaultMethods": [
                            "group tacacs+",
                            "logging"
                        ],
                        "consoleMethods": []
                    }
                },
                "dot1xAcctMethods": {
                    "dot1x": {
                        "defaultMethods": [],
                        "consoleMethods": []
                    }
                }
            }
        ],
        "inputs": (["tacacs+", "logging"], ["commands", "exec", "system"]),
        "expected": {"result": "failure", "messages": ["AAA accounting default methods ['tacacs+', 'logging'] are not matching for ['commands']"]}
    },
    {
        "name": "error-wrong-auth-type",
        "eos_data": [
            {
                "commandsAcctMethods": {},
                "execAcctMethods": {},
                "systemAcctMethods": {},
                "dot1xAcctMethods": {}
            }
        ],
        "inputs": (["tacacs+", "local"], ["commands", "exec", "system", "bad"]),
        "expected": {"result": "error"}, "messages": ["ValueError (Wrong parameter provided in auth_types. Valid parameters are: ['system', 'exec', 'commands', 'dot1x'])"]
    },
    {
        "name": "error-too-many-auth-type",
        "eos_data": [
            {
                "commandsAcctMethods": {},
                "execAcctMethods": {},
                "systemAcctMethods": {},
                "dot1xAcctMethods": {}
            }
        ],
        "inputs": (["tacacs+", "local"], ["commands", "exec", "system", "dot1x", "bad"]),
        "expected": {"result": "error"}, "messages": ["ValueError (Too many parameters provided in auth_types. Valid parameters are: ['system', 'exec', 'commands', 'dot1x'])"]
    },
    {
        "name": "skipped-no-methods",
        "eos_data": [
             {
                "commandsAcctMethods": {},
                "execAcctMethods": {},
                "systemAcctMethods": {},
                "dot1xAcctMethods": {}
              }
        ],
        "inputs": ([], ["commands", "exec", "system"]),
        "expected_result": "skipped", "messages": ["VerifyAcctDefaultMethods did not run because methods or auth_types were not supplied"]
    },
    {
        "name": "skipped-no-auth-types",
        "eos_data": [
             {
                "commandsAcctMethods": {},
                "execAcctMethods": {},
                "systemAcctMethods": {},
                "dot1xAcctMethods": {}
              }
        ],
        "inputs": (["tacacs+", "local"], []),
        "expected_result": "skipped", "messages": ["VerifyAcctDefaultMethods did not run because methods or auth_types were not supplied"]
    },
]

INPUT_ACCT_CONSOLE_METHODS: List[Dict[str, Any]] = [
    {
        "name": "success-commands-exec-system",
        "eos_data": [
            {
                "commandsAcctMethods": {
                    "privilege0-15": {
                        "defaultMethods": [],
                        "consoleAction": "startStop",
                        "consoleMethods": [
                            "group tacacs+",
                            "logging"
                        ],
                    }
                },
                "execAcctMethods": {
                    "exec": {
                        "defaultMethods": [],
                        "consoleAction": "startStop",
                        "consoleMethods": [
                            "group tacacs+",
                            "logging"
                        ],
                    }
                },
                "systemAcctMethods": {
                    "system": {
                        "defaultMethods": [],
                        "consoleAction": "startStop",
                        "consoleMethods": [
                            "group tacacs+",
                            "logging"
                        ],
                    }
                },
                "dot1xAcctMethods": {
                    "dot1x": {
                        "defaultMethods": [],
                        "consoleMethods": []
                    }
                }
            }
        ],
        "inputs": (["tacacs+", "logging"], ["commands", "exec", "system"]),
        "expected": {"result": "success"},
    },
    {
        "name": "success-dot1x",
        "eos_data": [
            {
                "commandsAcctMethods": {
                    "privilege0-15": {
                        "defaultMethods": [],
                        "consoleAction": "startStop",
                        "consoleMethods": [
                            "group tacacs+",
                            "logging"
                        ],
                    }
                },
                "execAcctMethods": {
                    "exec": {
                        "defaultMethods": [],
                        "consoleAction": "startStop",
                        "consoleMethods": [
                            "group tacacs+",
                            "logging"
                        ],
                    }
                },
                "systemAcctMethods": {
                    "system": {
                        "defaultMethods": [],
                        "consoleAction": "startStop",
                        "consoleMethods": [
                            "group tacacs+",
                            "logging"
                        ],
                    }
                },
                "dot1xAcctMethods": {
                    "dot1x": {
                        "defaultMethods": [],
                        "consoleAction": "startStop",
                        "consoleMethods": [
                            "group tacacs+",
                            "logging"
                        ],
                    }
                }
            }
        ],
        "inputs": (["tacacs+", "logging"], ["dot1x"]),
        "expected": {"result": "success"},
    },
    {
        "name": "failure-not-configured",
        "eos_data": [
            {
                "commandsAcctMethods": {
                    "privilege0-15": {
                        "defaultMethods": [],
                        "consoleMethods": [],
                    }
                },
                "execAcctMethods": {
                    "exec": {
                        "defaultMethods": [],
                        "consoleAction": "startStop",
                        "consoleMethods": [
                            "group tacacs+",
                            "logging"
                        ],
                    }
                },
                "systemAcctMethods": {
                    "system": {
                        "defaultMethods": [],
                        "consoleAction": "startStop",
                        "consoleMethods": [
                            "group tacacs+",
                            "logging"
                        ],
                    }
                },
                "dot1xAcctMethods": {
                    "dot1x": {
                        "defaultMethods": [],
                        "consoleMethods": []
                    }
                }
            }
        ],
        "inputs": (["tacacs+", "logging"], ["commands", "exec", "system"]),
        "expected": {"result": "failure", "messages": ["AAA console accounting is not configured for ['commands']"]}
    },
    {
        "name": "failure-not-matching",
        "eos_data": [
            {
                "commandsAcctMethods": {
                    "privilege0-15": {
                        "defaultMethods": [],
                        "consoleAction": "startStop",
                        "consoleMethods": [
                            "group radius",
                            "logging"
                        ],
                    }
                },
                "execAcctMethods": {
                    "exec": {
                        "defaultMethods": [],
                        "consoleAction": "startStop",
                        "consoleMethods": [
                            "group tacacs+",
                            "logging"
                        ],
                    }
                },
                "systemAcctMethods": {
                    "system": {
                        "defaultMethods": [],
                        "consoleAction": "startStop",
                        "consoleMethods": [
                            "group tacacs+",
                            "logging"
                        ],
                    }
                },
                "dot1xAcctMethods": {
                    "dot1x": {
                        "defaultMethods": [],
                        "consoleMethods": []
                    }
                }
            }
        ],
        "inputs": (["tacacs+", "logging"], ["commands", "exec", "system"]),
        "expected": {"result": "failure", "messages": ["AAA accounting console methods ['tacacs+', 'logging'] are not matching for ['commands']"]}
    },
    {
        "name": "error-wrong-auth-type",
        "eos_data": [
            {
                "commandsAcctMethods": {},
                "execAcctMethods": {},
                "systemAcctMethods": {},
                "dot1xAcctMethods": {}
            }
        ],
        "inputs": (["tacacs+", "local"], ["commands", "exec", "system", "bad"]),
        "expected": {"result": "error"}, "messages": ["ValueError (Wrong parameter provided in auth_types. Valid parameters are: ['system', 'exec', 'commands', 'dot1x'])"]
    },
    {
        "name": "error-too-many-auth-type",
        "eos_data": [
            {
                "commandsAcctMethods": {},
                "execAcctMethods": {},
                "systemAcctMethods": {},
                "dot1xAcctMethods": {}
            }
        ],
        "inputs": (["tacacs+", "local"], ["commands", "exec", "system", "dot1x", "bad"]),
        "expected": {"result": "error"}, "messages": ["ValueError (Too many parameters provided in auth_types. Valid parameters are: ['system', 'exec', 'commands', 'dot1x'])"]
    },
    {
        "name": "skipped-no-methods",
        "eos_data": [
             {
                "commandsAcctMethods": {},
                "execAcctMethods": {},
                "systemAcctMethods": {},
                "dot1xAcctMethods": {}
              }
        ],
        "inputs": ([], ["commands", "exec", "system"]),
        "expected_result": "skipped", "messages": ["VerifyAcctConsoleMethods did not run because methods or auth_types were not supplied"]
    },
    {
        "name": "skipped-no-auth-types",
        "eos_data": [
             {
                "commandsAcctMethods": {},
                "execAcctMethods": {},
                "systemAcctMethods": {},
                "dot1xAcctMethods": {}
              }
        ],
        "inputs": (["tacacs+", "local"], []),
        "expected_result": "skipped", "messages": ["VerifyAcctConsoleMethods did not run because methods or auth_types were not supplied"]
    },
]
