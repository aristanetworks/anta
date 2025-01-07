# Copyright (c) 2023-2025 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Tests for anta.tests.aaa.py."""

from __future__ import annotations

from typing import Any

from anta.tests.aaa import (
    VerifyAcctConsoleMethods,
    VerifyAcctDefaultMethods,
    VerifyAuthenMethods,
    VerifyAuthzMethods,
    VerifyTacacsServerGroups,
    VerifyTacacsServers,
    VerifyTacacsSourceIntf,
)
from tests.units.anta_tests import test

DATA: list[dict[str, Any]] = [
    {
        "name": "success",
        "test": VerifyTacacsSourceIntf,
        "eos_data": [
            {
                "tacacsServers": [
                    {
                        "serverInfo": {"hostname": "10.22.10.91", "authport": 49, "vrf": "MGMT"},
                    },
                ],
                "groups": {"GROUP1": {"serverGroup": "TACACS+", "members": [{"hostname": "SERVER1", "authport": 49, "vrf": "MGMT"}]}},
                "srcIntf": {"MGMT": "Management0"},
            },
        ],
        "inputs": {"intf": "Management0", "vrf": "MGMT"},
        "expected": {"result": "success"},
    },
    {
        "name": "failure-not-configured",
        "test": VerifyTacacsSourceIntf,
        "eos_data": [
            {
                "tacacsServers": [],
                "groups": {},
                "srcIntf": {},
            },
        ],
        "inputs": {"intf": "Management0", "vrf": "MGMT"},
        "expected": {"result": "failure", "messages": ["Source-interface Management0 is not configured in VRF MGMT"]},
    },
    {
        "name": "failure-wrong-intf",
        "test": VerifyTacacsSourceIntf,
        "eos_data": [
            {
                "tacacsServers": [
                    {
                        "serverInfo": {"hostname": "10.22.10.91", "authport": 49, "vrf": "MGMT"},
                    },
                ],
                "groups": {"GROUP1": {"serverGroup": "TACACS+", "members": [{"hostname": "SERVER1", "authport": 49, "vrf": "MGMT"}]}},
                "srcIntf": {"MGMT": "Management1"},
            },
        ],
        "inputs": {"intf": "Management0", "vrf": "MGMT"},
        "expected": {"result": "failure", "messages": ["Wrong source-interface configured in VRF MGMT"]},
    },
    {
        "name": "failure-wrong-vrf",
        "test": VerifyTacacsSourceIntf,
        "eos_data": [
            {
                "tacacsServers": [
                    {
                        "serverInfo": {"hostname": "10.22.10.91", "authport": 49, "vrf": "MGMT"},
                    },
                ],
                "groups": {"GROUP1": {"serverGroup": "TACACS+", "members": [{"hostname": "SERVER1", "authport": 49, "vrf": "MGMT"}]}},
                "srcIntf": {"PROD": "Management0"},
            },
        ],
        "inputs": {"intf": "Management0", "vrf": "MGMT"},
        "expected": {"result": "failure", "messages": ["Source-interface Management0 is not configured in VRF MGMT"]},
    },
    {
        "name": "success",
        "test": VerifyTacacsServers,
        "eos_data": [
            {
                "tacacsServers": [
                    {
                        "serverInfo": {"hostname": "10.22.10.91", "authport": 49, "vrf": "MGMT"},
                    },
                ],
                "groups": {"GROUP1": {"serverGroup": "TACACS+", "members": [{"hostname": "SERVER1", "authport": 49, "vrf": "MGMT"}]}},
                "srcIntf": {"MGMT": "Management0"},
            },
        ],
        "inputs": {"servers": ["10.22.10.91"], "vrf": "MGMT"},
        "expected": {"result": "success"},
    },
    {
        "name": "failure-no-servers",
        "test": VerifyTacacsServers,
        "eos_data": [
            {
                "tacacsServers": [],
                "groups": {},
                "srcIntf": {},
            },
        ],
        "inputs": {"servers": ["10.22.10.91"], "vrf": "MGMT"},
        "expected": {"result": "failure", "messages": ["No TACACS servers are configured"]},
    },
    {
        "name": "failure-not-configured",
        "test": VerifyTacacsServers,
        "eos_data": [
            {
                "tacacsServers": [
                    {
                        "serverInfo": {"hostname": "10.22.10.91", "authport": 49, "vrf": "MGMT"},
                    },
                ],
                "groups": {"GROUP1": {"serverGroup": "TACACS+", "members": [{"hostname": "SERVER1", "authport": 49, "vrf": "MGMT"}]}},
                "srcIntf": {"MGMT": "Management0"},
            },
        ],
        "inputs": {"servers": ["10.22.10.91", "10.22.10.92"], "vrf": "MGMT"},
        "expected": {"result": "failure", "messages": ["TACACS servers ['10.22.10.92'] are not configured in VRF MGMT"]},
    },
    {
        "name": "failure-wrong-vrf",
        "test": VerifyTacacsServers,
        "eos_data": [
            {
                "tacacsServers": [
                    {
                        "serverInfo": {"hostname": "10.22.10.91", "authport": 49, "vrf": "PROD"},
                    },
                ],
                "groups": {"GROUP1": {"serverGroup": "TACACS+", "members": [{"hostname": "SERVER1", "authport": 49, "vrf": "MGMT"}]}},
                "srcIntf": {"MGMT": "Management0"},
            },
        ],
        "inputs": {"servers": ["10.22.10.91"], "vrf": "MGMT"},
        "expected": {"result": "failure", "messages": ["TACACS servers ['10.22.10.91'] are not configured in VRF MGMT"]},
    },
    {
        "name": "success",
        "test": VerifyTacacsServerGroups,
        "eos_data": [
            {
                "tacacsServers": [
                    {
                        "serverInfo": {"hostname": "10.22.10.91", "authport": 49, "vrf": "MGMT"},
                    },
                ],
                "groups": {"GROUP1": {"serverGroup": "TACACS+", "members": [{"hostname": "SERVER1", "authport": 49, "vrf": "MGMT"}]}},
                "srcIntf": {"MGMT": "Management0"},
            },
        ],
        "inputs": {"groups": ["GROUP1"]},
        "expected": {"result": "success"},
    },
    {
        "name": "failure-no-server-groups",
        "test": VerifyTacacsServerGroups,
        "eos_data": [
            {
                "tacacsServers": [],
                "groups": {},
                "srcIntf": {},
            },
        ],
        "inputs": {"groups": ["GROUP1"]},
        "expected": {"result": "failure", "messages": ["No TACACS server group(s) are configured"]},
    },
    {
        "name": "failure-not-configured",
        "test": VerifyTacacsServerGroups,
        "eos_data": [
            {
                "tacacsServers": [
                    {
                        "serverInfo": {"hostname": "10.22.10.91", "authport": 49, "vrf": "MGMT"},
                    },
                ],
                "groups": {"GROUP2": {"serverGroup": "TACACS+", "members": [{"hostname": "SERVER1", "authport": 49, "vrf": "MGMT"}]}},
                "srcIntf": {"MGMT": "Management0"},
            },
        ],
        "inputs": {"groups": ["GROUP1"]},
        "expected": {"result": "failure", "messages": ["TACACS server group(s) ['GROUP1'] are not configured"]},
    },
    {
        "name": "success-login-enable",
        "test": VerifyAuthenMethods,
        "eos_data": [
            {
                "loginAuthenMethods": {"default": {"methods": ["group tacacs+", "local"]}, "login": {"methods": ["group tacacs+", "local"]}},
                "enableAuthenMethods": {"default": {"methods": ["group tacacs+", "local"]}},
                "dot1xAuthenMethods": {"default": {"methods": ["group radius"]}},
            },
        ],
        "inputs": {"methods": ["tacacs+", "local"], "types": ["login", "enable"]},
        "expected": {"result": "success"},
    },
    {
        "name": "success-dot1x",
        "test": VerifyAuthenMethods,
        "eos_data": [
            {
                "loginAuthenMethods": {"default": {"methods": ["group tacacs+", "local"]}, "login": {"methods": ["group tacacs+", "local"]}},
                "enableAuthenMethods": {"default": {"methods": ["group tacacs+", "local"]}},
                "dot1xAuthenMethods": {"default": {"methods": ["group radius"]}},
            },
        ],
        "inputs": {"methods": ["radius"], "types": ["dot1x"]},
        "expected": {"result": "success"},
    },
    {
        "name": "failure-no-login-console",
        "test": VerifyAuthenMethods,
        "eos_data": [
            {
                "loginAuthenMethods": {"default": {"methods": ["group tacacs+", "local"]}},
                "enableAuthenMethods": {"default": {"methods": ["group tacacs+", "local"]}},
                "dot1xAuthenMethods": {"default": {"methods": ["group radius"]}},
            },
        ],
        "inputs": {"methods": ["tacacs+", "local"], "types": ["login", "enable"]},
        "expected": {"result": "failure", "messages": ["AAA authentication methods are not configured for login console"]},
    },
    {
        "name": "failure-login-console",
        "test": VerifyAuthenMethods,
        "eos_data": [
            {
                "loginAuthenMethods": {"default": {"methods": ["group tacacs+", "local"]}, "login": {"methods": ["group radius", "local"]}},
                "enableAuthenMethods": {"default": {"methods": ["group tacacs+", "local"]}},
                "dot1xAuthenMethods": {"default": {"methods": ["group radius"]}},
            },
        ],
        "inputs": {"methods": ["tacacs+", "local"], "types": ["login", "enable"]},
        "expected": {"result": "failure", "messages": ["AAA authentication methods ['group tacacs+', 'local'] are not matching for login console"]},
    },
    {
        "name": "failure-login-default",
        "test": VerifyAuthenMethods,
        "eos_data": [
            {
                "loginAuthenMethods": {"default": {"methods": ["group radius", "local"]}, "login": {"methods": ["group tacacs+", "local"]}},
                "enableAuthenMethods": {"default": {"methods": ["group tacacs+", "local"]}},
                "dot1xAuthenMethods": {"default": {"methods": ["group radius"]}},
            },
        ],
        "inputs": {"methods": ["tacacs+", "local"], "types": ["login", "enable"]},
        "expected": {"result": "failure", "messages": ["AAA authentication methods ['group tacacs+', 'local'] are not matching for ['login']"]},
    },
    {
        "name": "success",
        "test": VerifyAuthzMethods,
        "eos_data": [
            {
                "commandsAuthzMethods": {"privilege0-15": {"methods": ["group tacacs+", "local"]}},
                "execAuthzMethods": {"exec": {"methods": ["group tacacs+", "local"]}},
            },
        ],
        "inputs": {"methods": ["tacacs+", "local"], "types": ["commands", "exec"]},
        "expected": {"result": "success"},
    },
    {
        "name": "success-skipping-exec",
        "test": VerifyAuthzMethods,
        "eos_data": [
            {
                "commandsAuthzMethods": {"privilege0-15": {"methods": ["group tacacs+", "local"]}},
                "execAuthzMethods": {"exec": {"methods": ["group tacacs+", "local"]}},
            },
        ],
        "inputs": {"methods": ["tacacs+", "local"], "types": ["commands"]},
        "expected": {"result": "success"},
    },
    {
        "name": "failure-commands",
        "test": VerifyAuthzMethods,
        "eos_data": [
            {
                "commandsAuthzMethods": {"privilege0-15": {"methods": ["group radius", "local"]}},
                "execAuthzMethods": {"exec": {"methods": ["group tacacs+", "local"]}},
            },
        ],
        "inputs": {"methods": ["tacacs+", "local"], "types": ["commands", "exec"]},
        "expected": {"result": "failure", "messages": ["AAA authorization methods ['group tacacs+', 'local'] are not matching for ['commands']"]},
    },
    {
        "name": "failure-exec",
        "test": VerifyAuthzMethods,
        "eos_data": [
            {
                "commandsAuthzMethods": {"privilege0-15": {"methods": ["group tacacs+", "local"]}},
                "execAuthzMethods": {"exec": {"methods": ["group radius", "local"]}},
            },
        ],
        "inputs": {"methods": ["tacacs+", "local"], "types": ["commands", "exec"]},
        "expected": {"result": "failure", "messages": ["AAA authorization methods ['group tacacs+', 'local'] are not matching for ['exec']"]},
    },
    {
        "name": "success-commands-exec-system",
        "test": VerifyAcctDefaultMethods,
        "eos_data": [
            {
                "commandsAcctMethods": {"privilege0-15": {"defaultAction": "startStop", "defaultMethods": ["group tacacs+", "logging"], "consoleMethods": []}},
                "execAcctMethods": {"exec": {"defaultAction": "startStop", "defaultMethods": ["group tacacs+", "logging"], "consoleMethods": []}},
                "systemAcctMethods": {"system": {"defaultAction": "startStop", "defaultMethods": ["group tacacs+", "logging"], "consoleMethods": []}},
                "dot1xAcctMethods": {"dot1x": {"defaultMethods": [], "consoleMethods": []}},
            },
        ],
        "inputs": {"methods": ["tacacs+", "logging"], "types": ["commands", "exec", "system"]},
        "expected": {"result": "success"},
    },
    {
        "name": "success-dot1x",
        "test": VerifyAcctDefaultMethods,
        "eos_data": [
            {
                "commandsAcctMethods": {"privilege0-15": {"defaultAction": "startStop", "defaultMethods": ["group tacacs+", "logging"], "consoleMethods": []}},
                "execAcctMethods": {"exec": {"defaultAction": "startStop", "defaultMethods": ["group tacacs+", "logging"], "consoleMethods": []}},
                "systemAcctMethods": {"system": {"defaultAction": "startStop", "defaultMethods": ["group tacacs+", "logging"], "consoleMethods": []}},
                "dot1xAcctMethods": {"dot1x": {"defaultAction": "startStop", "defaultMethods": ["group radius", "logging"], "consoleMethods": []}},
            },
        ],
        "inputs": {"methods": ["radius", "logging"], "types": ["dot1x"]},
        "expected": {"result": "success"},
    },
    {
        "name": "failure-not-configured",
        "test": VerifyAcctDefaultMethods,
        "eos_data": [
            {
                "commandsAcctMethods": {"privilege0-15": {"defaultMethods": [], "consoleMethods": []}},
                "execAcctMethods": {"exec": {"defaultAction": "startStop", "defaultMethods": ["group tacacs+", "logging"], "consoleMethods": []}},
                "systemAcctMethods": {"system": {"defaultAction": "startStop", "defaultMethods": ["group tacacs+", "logging"], "consoleMethods": []}},
                "dot1xAcctMethods": {"dot1x": {"defaultMethods": [], "consoleMethods": []}},
            },
        ],
        "inputs": {"methods": ["tacacs+", "logging"], "types": ["commands", "exec", "system"]},
        "expected": {"result": "failure", "messages": ["AAA default accounting is not configured for ['commands']"]},
    },
    {
        "name": "failure-not-configured-empty",
        "test": VerifyAcctDefaultMethods,
        "eos_data": [
            {
                "systemAcctMethods": {"system": {"defaultMethods": [], "consoleMethods": []}},
                "execAcctMethods": {"exec": {"defaultMethods": [], "consoleMethods": []}},
                "commandsAcctMethods": {"privilege0-15": {"defaultMethods": [], "consoleMethods": []}},
                "dot1xAcctMethods": {"dot1x": {"defaultMethods": [], "consoleMethods": []}},
            },
        ],
        "inputs": {"methods": ["tacacs+", "logging"], "types": ["commands", "exec", "system"]},
        "expected": {"result": "failure", "messages": ["AAA default accounting is not configured for ['system', 'exec', 'commands']"]},
    },
    {
        "name": "failure-not-matching",
        "test": VerifyAcctDefaultMethods,
        "eos_data": [
            {
                "commandsAcctMethods": {"privilege0-15": {"defaultAction": "startStop", "defaultMethods": ["group radius", "logging"], "consoleMethods": []}},
                "execAcctMethods": {"exec": {"defaultAction": "startStop", "defaultMethods": ["group tacacs+", "logging"], "consoleMethods": []}},
                "systemAcctMethods": {"system": {"defaultAction": "startStop", "defaultMethods": ["group tacacs+", "logging"], "consoleMethods": []}},
                "dot1xAcctMethods": {"dot1x": {"defaultMethods": [], "consoleMethods": []}},
            },
        ],
        "inputs": {"methods": ["tacacs+", "logging"], "types": ["commands", "exec", "system"]},
        "expected": {"result": "failure", "messages": ["AAA accounting default methods ['group tacacs+', 'logging'] are not matching for ['commands']"]},
    },
    {
        "name": "success-commands-exec-system",
        "test": VerifyAcctConsoleMethods,
        "eos_data": [
            {
                "commandsAcctMethods": {
                    "privilege0-15": {
                        "defaultMethods": [],
                        "consoleAction": "startStop",
                        "consoleMethods": ["group tacacs+", "logging"],
                    },
                },
                "execAcctMethods": {
                    "exec": {
                        "defaultMethods": [],
                        "consoleAction": "startStop",
                        "consoleMethods": ["group tacacs+", "logging"],
                    },
                },
                "systemAcctMethods": {
                    "system": {
                        "defaultMethods": [],
                        "consoleAction": "startStop",
                        "consoleMethods": ["group tacacs+", "logging"],
                    },
                },
                "dot1xAcctMethods": {"dot1x": {"defaultMethods": [], "consoleMethods": []}},
            },
        ],
        "inputs": {"methods": ["tacacs+", "logging"], "types": ["commands", "exec", "system"]},
        "expected": {"result": "success"},
    },
    {
        "name": "success-dot1x",
        "test": VerifyAcctConsoleMethods,
        "eos_data": [
            {
                "commandsAcctMethods": {
                    "privilege0-15": {
                        "defaultMethods": [],
                        "consoleAction": "startStop",
                        "consoleMethods": ["group tacacs+", "logging"],
                    },
                },
                "execAcctMethods": {
                    "exec": {
                        "defaultMethods": [],
                        "consoleAction": "startStop",
                        "consoleMethods": ["group tacacs+", "logging"],
                    },
                },
                "systemAcctMethods": {
                    "system": {
                        "defaultMethods": [],
                        "consoleAction": "startStop",
                        "consoleMethods": ["group tacacs+", "logging"],
                    },
                },
                "dot1xAcctMethods": {
                    "dot1x": {
                        "defaultMethods": [],
                        "consoleAction": "startStop",
                        "consoleMethods": ["group tacacs+", "logging"],
                    },
                },
            },
        ],
        "inputs": {"methods": ["tacacs+", "logging"], "types": ["dot1x"]},
        "expected": {"result": "success"},
    },
    {
        "name": "failure-not-configured",
        "test": VerifyAcctConsoleMethods,
        "eos_data": [
            {
                "commandsAcctMethods": {
                    "privilege0-15": {
                        "defaultMethods": [],
                        "consoleMethods": [],
                    },
                },
                "execAcctMethods": {
                    "exec": {
                        "defaultMethods": [],
                        "consoleAction": "startStop",
                        "consoleMethods": ["group tacacs+", "logging"],
                    },
                },
                "systemAcctMethods": {
                    "system": {
                        "defaultMethods": [],
                        "consoleAction": "startStop",
                        "consoleMethods": ["group tacacs+", "logging"],
                    },
                },
                "dot1xAcctMethods": {"dot1x": {"defaultMethods": [], "consoleMethods": []}},
            },
        ],
        "inputs": {"methods": ["tacacs+", "logging"], "types": ["commands", "exec", "system"]},
        "expected": {"result": "failure", "messages": ["AAA console accounting is not configured for ['commands']"]},
    },
    {
        "name": "failure-not-configured-empty",
        "test": VerifyAcctConsoleMethods,
        "eos_data": [
            {
                "systemAcctMethods": {"system": {"defaultMethods": [], "consoleMethods": []}},
                "execAcctMethods": {"exec": {"defaultMethods": [], "consoleMethods": []}},
                "commandsAcctMethods": {"privilege0-15": {"defaultMethods": [], "consoleMethods": []}},
                "dot1xAcctMethods": {"dot1x": {"defaultMethods": [], "consoleMethods": []}},
            },
        ],
        "inputs": {"methods": ["tacacs+", "logging"], "types": ["commands", "exec", "system"]},
        "expected": {"result": "failure", "messages": ["AAA console accounting is not configured for ['system', 'exec', 'commands']"]},
    },
    {
        "name": "failure-not-matching",
        "test": VerifyAcctConsoleMethods,
        "eos_data": [
            {
                "commandsAcctMethods": {
                    "privilege0-15": {
                        "defaultMethods": [],
                        "consoleAction": "startStop",
                        "consoleMethods": ["group radius", "logging"],
                    },
                },
                "execAcctMethods": {
                    "exec": {
                        "defaultMethods": [],
                        "consoleAction": "startStop",
                        "consoleMethods": ["group tacacs+", "logging"],
                    },
                },
                "systemAcctMethods": {
                    "system": {
                        "defaultMethods": [],
                        "consoleAction": "startStop",
                        "consoleMethods": ["group tacacs+", "logging"],
                    },
                },
                "dot1xAcctMethods": {"dot1x": {"defaultMethods": [], "consoleMethods": []}},
            },
        ],
        "inputs": {"methods": ["tacacs+", "logging"], "types": ["commands", "exec", "system"]},
        "expected": {"result": "failure", "messages": ["AAA accounting console methods ['group tacacs+', 'logging'] are not matching for ['commands']"]},
    },
]
