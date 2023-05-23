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
        "side_effect": ("Management0", "MGMT"),
        "expected_result": "success",
        "expected_messages": []
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
        "side_effect": ("Management0", "MGMT"),
        "expected_result": "failure",
        "expected_messages": ["Source-interface Management0 is not configured in VRF MGMT"]
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
        "side_effect": ("Management0", "MGMT"),
        "expected_result": "failure",
        "expected_messages": ["Wrong source-interface configured in VRF MGMT"]
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
        "side_effect": ("Management0", "MGMT"),
        "expected_result": "failure",
        "expected_messages": ["Source-interface Management0 is not configured in VRF MGMT"]
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
        "side_effect": ("Management0", ""),
        "expected_result": "skipped",
        "expected_messages": ["VerifyTacacsSourceIntf did not run because intf or vrf was not supplied"]
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
        "side_effect": ("", "MGMT"),
        "expected_result": "skipped",
        "expected_messages": ["VerifyTacacsSourceIntf did not run because intf or vrf was not supplied"]
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
        "side_effect": (["10.22.10.91"], "MGMT"),
        "expected_result": "success",
        "expected_messages": []
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
        "side_effect": (["10.22.10.91"], "MGMT"),
        "expected_result": "failure",
        "expected_messages": ["No TACACS servers are configured"]
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
        "side_effect": (["10.22.10.91", "10.22.10.92"], "MGMT"),
        "expected_result": "failure",
        "expected_messages": ["TACACS servers ['10.22.10.92'] are not configured in VRF MGMT"]
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
        "side_effect": (["10.22.10.91"], "MGMT"),
        "expected_result": "failure",
        "expected_messages": ["TACACS servers ['10.22.10.91'] are not configured in VRF MGMT"]
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
        "side_effect": ([], "MGMT"),
        "expected_result": "skipped",
        "expected_messages": ["VerifyTacacsServers did not run because servers or vrf were not supplied"]
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
        "side_effect": (["10.22.10.91"], ""),
        "expected_result": "skipped",
        "expected_messages": ["VerifyTacacsServers did not run because servers or vrf were not supplied"]
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
        "side_effect": ["GROUP1"],
        "expected_result": "success",
        "expected_messages": []
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
        "side_effect": ["GROUP1"],
        "expected_result": "failure",
        "expected_messages": ["No TACACS server group(s) are configured"]
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
        "side_effect": ["GROUP1"],
        "expected_result": "failure",
        "expected_messages": ["TACACS server group(s) ['GROUP1'] are not configured"]
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
        "side_effect": [],
        "expected_result": "skipped",
        "expected_messages": ["VerifyTacacsServerGroups did not run because groups were not supplied"]
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
        "side_effect": (["tacacs+", "local"], ["login", "enable"]),
        "expected_result": "success",
        "expected_messages": []
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
        "side_effect": (["radius"], ["dot1x"]),
        "expected_result": "success",
        "expected_messages": []
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
        "side_effect": (["tacacs+", "local"], ["login", "enable"]),
        "expected_result": "failure",
        "expected_messages": ["AAA authentication methods are not configured for login console"]
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
        "side_effect": (["tacacs+", "local"], ["login", "enable"]),
        "expected_result": "failure",
        "expected_messages": ["AAA authentication methods ['tacacs+', 'local'] are not matching for login console"]
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
        "side_effect": (["tacacs+", "local"], ["login", "enable"]),
        "expected_result": "failure",
        "expected_messages": ["AAA authentication methods ['tacacs+', 'local'] are not matching for ['login']"]
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
        "side_effect": (["tacacs+", "local"], ["login", "enable", "bad"]),
        "expected_result": "error",
        "expected_messages": ["ValueError (Wrong parameter provided in auth_types. Valid parameters are: ['login', 'enable', 'dot1x'])"]
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
        "side_effect": (["tacacs+", "local"], ["login", "enable", "dot1x", "bad"]),
        "expected_result": "error",
        "expected_messages": ["ValueError (Too many parameters provided in auth_types. Valid parameters are: ['login', 'enable', 'dot1x'])"]
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
        "side_effect": ([], ["login", "enable"]),
        "expected_result": "skipped",
        "expected_messages": ["VerifyAuthenMethods did not run because methods or auth_types were not supplied"]
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
        "side_effect": (["tacacs+", "local"], []),
        "expected_result": "skipped",
        "expected_messages": ["VerifyAuthenMethods did not run because methods or auth_types were not supplied"]
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
        "side_effect": (["tacacs+", "local"], ["commands", "exec"]),
        "expected_result": "success",
        "expected_messages": []
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
        "side_effect": (["tacacs+", "local"], ["commands", "exec"]),
        "expected_result": "failure",
        "expected_messages": ["AAA authorization methods ['tacacs+', 'local'] are not matching for ['commands']"]
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
        "side_effect": (["tacacs+", "local"], ["commands", "exec"]),
        "expected_result": "failure",
        "expected_messages": ["AAA authorization methods ['tacacs+', 'local'] are not matching for ['exec']"]
    },
    {
        "name": "error-wrong-auth-type",
        "eos_data": [
            {
                "commandsAuthzMethods": {},
                "execAuthzMethods": {}
            }
        ],
        "side_effect": (["tacacs+", "local"], ["commands", "bad"]),
        "expected_result": "error",
        "expected_messages": ["ValueError (Wrong parameter provided in auth_types. Valid parameters are: ['commands', 'exec'])"]
    },
    {
        "name": "error-too-many-auth-type",
        "eos_data": [
            {
                "commandsAuthzMethods": {},
                "execAuthzMethods": {}
            }
        ],
        "side_effect": (["tacacs+", "local"], ["commands", "exec", "bad"]),
        "expected_result": "error",
        "expected_messages": ["ValueError (Too many parameters provided in auth_types. Valid parameters are: ['commands', 'exec'])"]
    },
    {
        "name": "skipped-no-methods",
        "eos_data": [
             {
                "commandsAuthzMethods": {},
                "execAuthzMethods": {}
              }
        ],
        "side_effect": ([], ["commands", "exec"]),
        "expected_result": "skipped",
        "expected_messages": ["VerifyAuthzMethods did not run because methods or auth_types were not supplied"]
    },
    {
        "name": "skipped-no-auth-types",
        "eos_data": [
             {
                "commandsAuthzMethods": {},
                "execAuthzMethods": {}
              }
        ],
        "side_effect": (["tacacs+", "local"], []),
        "expected_result": "skipped",
        "expected_messages": ["VerifyAuthzMethods did not run because methods or auth_types were not supplied"]
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
        "side_effect": (["tacacs+", "logging"], ["commands", "exec", "system"]),
        "expected_result": "success",
        "expected_messages": []
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
        "side_effect": (["radius", "logging"], ["dot1x"]),
        "expected_result": "success",
        "expected_messages": []
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
        "side_effect": (["tacacs+", "logging"], ["commands", "exec", "system"]),
        "expected_result": "failure",
        "expected_messages": ["AAA default accounting is not configured for ['commands']"]
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
        "side_effect": (["tacacs+", "logging"], ["commands", "exec", "system"]),
        "expected_result": "failure",
        "expected_messages": ["AAA accounting default methods ['tacacs+', 'logging'] are not matching for ['commands']"]
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
        "side_effect": (["tacacs+", "local"], ["commands", "exec", "system", "bad"]),
        "expected_result": "error",
        "expected_messages": ["ValueError (Wrong parameter provided in auth_types. Valid parameters are: ['system', 'exec', 'commands', 'dot1x'])"]
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
        "side_effect": (["tacacs+", "local"], ["commands", "exec", "system", "dot1x", "bad"]),
        "expected_result": "error",
        "expected_messages": ["ValueError (Too many parameters provided in auth_types. Valid parameters are: ['system', 'exec', 'commands', 'dot1x'])"]
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
        "side_effect": ([], ["commands", "exec", "system"]),
        "expected_result": "skipped",
        "expected_messages": ["VerifyAcctDefaultMethods did not run because methods or auth_types were not supplied"]
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
        "side_effect": (["tacacs+", "local"], []),
        "expected_result": "skipped",
        "expected_messages": ["VerifyAcctDefaultMethods did not run because methods or auth_types were not supplied"]
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
        "side_effect": (["tacacs+", "logging"], ["commands", "exec", "system"]),
        "expected_result": "success",
        "expected_messages": []
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
        "side_effect": (["tacacs+", "logging"], ["dot1x"]),
        "expected_result": "success",
        "expected_messages": []
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
        "side_effect": (["tacacs+", "logging"], ["commands", "exec", "system"]),
        "expected_result": "failure",
        "expected_messages": ["AAA console accounting is not configured for ['commands']"]
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
        "side_effect": (["tacacs+", "logging"], ["commands", "exec", "system"]),
        "expected_result": "failure",
        "expected_messages": ["AAA accounting console methods ['tacacs+', 'logging'] are not matching for ['commands']"]
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
        "side_effect": (["tacacs+", "local"], ["commands", "exec", "system", "bad"]),
        "expected_result": "error",
        "expected_messages": ["ValueError (Wrong parameter provided in auth_types. Valid parameters are: ['system', 'exec', 'commands', 'dot1x'])"]
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
        "side_effect": (["tacacs+", "local"], ["commands", "exec", "system", "dot1x", "bad"]),
        "expected_result": "error",
        "expected_messages": ["ValueError (Too many parameters provided in auth_types. Valid parameters are: ['system', 'exec', 'commands', 'dot1x'])"]
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
        "side_effect": ([], ["commands", "exec", "system"]),
        "expected_result": "skipped",
        "expected_messages": ["VerifyAcctConsoleMethods did not run because methods or auth_types were not supplied"]
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
        "side_effect": (["tacacs+", "local"], []),
        "expected_result": "skipped",
        "expected_messages": ["VerifyAcctConsoleMethods did not run because methods or auth_types were not supplied"]
    },
]
