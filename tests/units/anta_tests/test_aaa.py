# Copyright (c) 2023-2026 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Tests for anta.tests.aaa.py."""

from __future__ import annotations

import sys
from typing import TYPE_CHECKING

from anta.models import AntaTest
from anta.result_manager.models import AntaTestStatus
from anta.tests.aaa import (
    VerifyAcctConsoleMethods,
    VerifyAcctDefaultMethods,
    VerifyAcctMethods,
    VerifyAuthenMethods,
    VerifyAuthzMethods,
    VerifyTacacsServerGroups,
    VerifyTacacsServers,
    VerifyTacacsSourceIntf,
)
from tests.units.anta_tests import test

if TYPE_CHECKING:
    from tests.units.anta_tests import AntaUnitTestData

DATA: AntaUnitTestData = {
    (VerifyTacacsSourceIntf, "success"): {
        "eos_data": [
            {
                "tacacsServers": [{"serverInfo": {"hostname": "10.22.10.91", "authport": 49, "vrf": "MGMT"}}],
                "groups": {"GROUP1": {"serverGroup": "TACACS+", "members": [{"hostname": "SERVER1", "authport": 49, "vrf": "MGMT"}]}},
                "srcIntf": {"MGMT": "Management0"},
            }
        ],
        "inputs": {"intf": "Management0", "vrf": "MGMT"},
        "expected": {"result": AntaTestStatus.SUCCESS},
    },
    (VerifyTacacsSourceIntf, "failure-not-configured"): {
        "eos_data": [{"tacacsServers": [], "groups": {}, "srcIntf": {}}],
        "inputs": {"intf": "Management0", "vrf": "MGMT"},
        "expected": {"result": AntaTestStatus.FAILURE, "messages": ["VRF: MGMT Source Interface: Management0 - Not configured"]},
    },
    (VerifyTacacsSourceIntf, "failure-wrong-intf"): {
        "eos_data": [
            {
                "tacacsServers": [{"serverInfo": {"hostname": "10.22.10.91", "authport": 49, "vrf": "MGMT"}}],
                "groups": {"GROUP1": {"serverGroup": "TACACS+", "members": [{"hostname": "SERVER1", "authport": 49, "vrf": "MGMT"}]}},
                "srcIntf": {"MGMT": "Management1"},
            }
        ],
        "inputs": {"intf": "Management0", "vrf": "MGMT"},
        "expected": {"result": AntaTestStatus.FAILURE, "messages": ["VRF: MGMT - Source interface mismatch - Expected: Management0 Actual: Management1"]},
    },
    (VerifyTacacsSourceIntf, "failure-wrong-vrf"): {
        "eos_data": [
            {
                "tacacsServers": [{"serverInfo": {"hostname": "10.22.10.91", "authport": 49, "vrf": "MGMT"}}],
                "groups": {"GROUP1": {"serverGroup": "TACACS+", "members": [{"hostname": "SERVER1", "authport": 49, "vrf": "MGMT"}]}},
                "srcIntf": {"PROD": "Management0"},
            }
        ],
        "inputs": {"intf": "Management0", "vrf": "MGMT"},
        "expected": {"result": AntaTestStatus.FAILURE, "messages": ["VRF: MGMT Source Interface: Management0 - Not configured"]},
    },
    (VerifyTacacsServers, "success"): {
        "eos_data": [
            {
                "tacacsServers": [{"serverInfo": {"hostname": "10.22.10.91", "authport": 49, "vrf": "MGMT"}}],
                "groups": {"GROUP1": {"serverGroup": "TACACS+", "members": [{"hostname": "SERVER1", "authport": 49, "vrf": "MGMT"}]}},
                "srcIntf": {"MGMT": "Management0"},
            }
        ],
        "inputs": {"servers": ["10.22.10.91"], "vrf": "MGMT"},
        "expected": {"result": AntaTestStatus.SUCCESS},
    },
    (VerifyTacacsServers, "success-default-vrf"): {
        "eos_data": [
            {
                "tacacsServers": [{"serverInfo": {"hostname": "10.22.10.91", "authport": 49}}],
            }
        ],
        "inputs": {"servers": ["10.22.10.91"]},
        "expected": {"result": AntaTestStatus.SUCCESS},
    },
    (VerifyTacacsServers, "failure-no-servers"): {
        "eos_data": [{"tacacsServers": [], "groups": {}, "srcIntf": {}}],
        "inputs": {"servers": ["10.22.10.91"], "vrf": "MGMT"},
        "expected": {"result": AntaTestStatus.FAILURE, "messages": ["No TACACS servers are configured"]},
    },
    (VerifyTacacsServers, "failure-not-configured"): {
        "eos_data": [
            {
                "tacacsServers": [{"serverInfo": {"hostname": "10.22.10.91", "authport": 49, "vrf": "MGMT"}}],
                "groups": {"GROUP1": {"serverGroup": "TACACS+", "members": [{"hostname": "SERVER1", "authport": 49, "vrf": "MGMT"}]}},
                "srcIntf": {"MGMT": "Management0"},
            }
        ],
        "inputs": {"servers": ["10.22.10.91", "10.22.10.92"], "vrf": "MGMT"},
        "expected": {"result": AntaTestStatus.FAILURE, "messages": ["TACACS servers 10.22.10.92 are not configured in VRF MGMT"]},
    },
    (VerifyTacacsServers, "failure-wrong-vrf"): {
        "eos_data": [
            {
                "tacacsServers": [{"serverInfo": {"hostname": "10.22.10.91", "authport": 49, "vrf": "PROD"}}],
                "groups": {"GROUP1": {"serverGroup": "TACACS+", "members": [{"hostname": "SERVER1", "authport": 49, "vrf": "MGMT"}]}},
                "srcIntf": {"MGMT": "Management0"},
            }
        ],
        "inputs": {"servers": ["10.22.10.91"], "vrf": "MGMT"},
        "expected": {"result": AntaTestStatus.FAILURE, "messages": ["TACACS servers 10.22.10.91 are not configured in VRF MGMT"]},
    },
    (VerifyTacacsServers, "failure-wrong-vrf-2"): {
        "eos_data": [
            {
                "tacacsServers": [{"serverInfo": {"hostname": "10.22.10.91", "authport": 49, "vrf": "PROD"}}],
            }
        ],
        "inputs": {"servers": ["10.22.10.91"]},
        "expected": {"result": AntaTestStatus.FAILURE, "messages": ["TACACS servers 10.22.10.91 are not configured in VRF default"]},
    },
    (VerifyTacacsServers, "failure-wrong-vrf-3"): {
        "eos_data": [
            {
                "tacacsServers": [{"serverInfo": {"hostname": "10.22.10.91", "authport": 49}}],
            }
        ],
        "inputs": {"servers": ["10.22.10.91"], "vrf": "MGMT"},
        "expected": {"result": AntaTestStatus.FAILURE, "messages": ["TACACS servers 10.22.10.91 are not configured in VRF MGMT"]},
    },
    (VerifyTacacsServerGroups, "success"): {
        "eos_data": [
            {
                "tacacsServers": [{"serverInfo": {"hostname": "10.22.10.91", "authport": 49, "vrf": "MGMT"}}],
                "groups": {"GROUP1": {"serverGroup": "TACACS+", "members": [{"hostname": "SERVER1", "authport": 49, "vrf": "MGMT"}]}},
                "srcIntf": {"MGMT": "Management0"},
            }
        ],
        "inputs": {"groups": ["GROUP1"]},
        "expected": {"result": AntaTestStatus.SUCCESS},
    },
    (VerifyTacacsServerGroups, "failure-no-server-groups"): {
        "eos_data": [{"tacacsServers": [], "groups": {}, "srcIntf": {}}],
        "inputs": {"groups": ["GROUP1"]},
        "expected": {"result": AntaTestStatus.FAILURE, "messages": ["No TACACS server group(s) are configured"]},
    },
    (VerifyTacacsServerGroups, "failure-not-configured"): {
        "eos_data": [
            {
                "tacacsServers": [{"serverInfo": {"hostname": "10.22.10.91", "authport": 49, "vrf": "MGMT"}}],
                "groups": {"GROUP2": {"serverGroup": "TACACS+", "members": [{"hostname": "SERVER1", "authport": 49, "vrf": "MGMT"}]}},
                "srcIntf": {"MGMT": "Management0"},
            }
        ],
        "inputs": {"groups": ["GROUP1"]},
        "expected": {"result": AntaTestStatus.FAILURE, "messages": ["TACACS server group(s) GROUP1 are not configured"]},
    },
    (VerifyAuthenMethods, "success-login-enable"): {
        "eos_data": [
            {
                "loginAuthenMethods": {"default": {"methods": ["group tacacs+", "local"]}, "login": {"methods": ["group tacacs+", "local"]}},
                "enableAuthenMethods": {"default": {"methods": ["group tacacs+", "local"]}},
                "dot1xAuthenMethods": {"default": {"methods": ["group radius"]}},
            }
        ],
        "inputs": {"methods": ["tacacs+", "local"], "types": ["login", "enable"]},
        "expected": {"result": AntaTestStatus.SUCCESS},
    },
    (VerifyAuthenMethods, "success-login-enable-console-method-list"): {
        "eos_data": [
            {
                "loginAuthenMethods": {"default": {"methods": ["group tacacs+", "local"]}, "console": {"methods": ["group tacacs+", "local"]}},
                "enableAuthenMethods": {"default": {"methods": ["group tacacs+", "local"]}},
                "dot1xAuthenMethods": {"default": {"methods": ["group radius"]}},
            }
        ],
        "inputs": {"methods": ["tacacs+", "local"], "types": ["login", "enable"]},
        "expected": {"result": AntaTestStatus.SUCCESS},
    },
    (VerifyAuthenMethods, "success-dot1x"): {
        "eos_data": [
            {
                "loginAuthenMethods": {"default": {"methods": ["group tacacs+", "local"]}, "login": {"methods": ["group tacacs+", "local"]}},
                "enableAuthenMethods": {"default": {"methods": ["group tacacs+", "local"]}},
                "dot1xAuthenMethods": {"default": {"methods": ["group radius"]}},
            }
        ],
        "inputs": {"methods": ["radius"], "types": ["dot1x"]},
        "expected": {"result": AntaTestStatus.SUCCESS},
    },
    (VerifyAuthenMethods, "failure-no-login-console"): {
        "eos_data": [
            {
                "loginAuthenMethods": {"default": {"methods": ["group tacacs+", "local"]}},
                "enableAuthenMethods": {"default": {"methods": ["group tacacs+", "local"]}},
                "dot1xAuthenMethods": {"default": {"methods": ["group radius"]}},
            }
        ],
        "inputs": {"methods": ["tacacs+", "local"], "types": ["login", "enable"]},
        "expected": {"result": AntaTestStatus.FAILURE, "messages": ["AAA authentication methods are not configured for login console"]},
    },
    (VerifyAuthenMethods, "failure-login-console"): {
        "eos_data": [
            {
                "loginAuthenMethods": {"default": {"methods": ["group tacacs+", "local"]}, "login": {"methods": ["group radius", "local"]}},
                "enableAuthenMethods": {"default": {"methods": ["group tacacs+", "local"]}},
                "dot1xAuthenMethods": {"default": {"methods": ["group radius"]}},
            }
        ],
        "inputs": {"methods": ["tacacs+", "local"], "types": ["login", "enable"]},
        "expected": {"result": AntaTestStatus.FAILURE, "messages": ["AAA authentication methods group tacacs+, local are not matching for login console"]},
    },
    (VerifyAuthenMethods, "failure-login-console-method-list"): {
        "eos_data": [
            {
                "loginAuthenMethods": {"default": {"methods": ["group tacacs+", "local"]}, "console": {"methods": ["group radius", "local"]}},
                "enableAuthenMethods": {"default": {"methods": ["group tacacs+", "local"]}},
                "dot1xAuthenMethods": {"default": {"methods": ["group radius"]}},
            }
        ],
        "inputs": {"methods": ["tacacs+", "local"], "types": ["login", "enable"]},
        "expected": {"result": AntaTestStatus.FAILURE, "messages": ["AAA authentication methods group tacacs+, local are not matching for login console"]},
    },
    (VerifyAuthenMethods, "failure-login-command-api-and-default-method-lists"): {
        "eos_data": [
            {
                "loginAuthenMethods": {
                    "default": {"methods": ["local", "none"]},
                    "command-api": {"methods": ["group tacacs+", "none"]},
                    "login": {"methods": ["none"]},
                },
                "enableAuthenMethods": {"default": {"methods": ["local"]}},
                "dot1xAuthenMethods": {"default": {"methods": []}},
            }
        ],
        "inputs": {"methods": ["none"], "types": ["login"]},
        "expected": {"result": AntaTestStatus.FAILURE, "messages": ["AAA authentication methods none are not matching for login"]},
    },
    (VerifyAuthenMethods, "failure-login-default"): {
        "eos_data": [
            {
                "loginAuthenMethods": {"default": {"methods": ["group radius", "local"]}, "login": {"methods": ["group tacacs+", "local"]}},
                "enableAuthenMethods": {"default": {"methods": ["group tacacs+", "local"]}},
                "dot1xAuthenMethods": {"default": {"methods": ["group radius"]}},
            }
        ],
        "inputs": {"methods": ["tacacs+", "local"], "types": ["login", "enable"]},
        "expected": {"result": AntaTestStatus.FAILURE, "messages": ["AAA authentication methods group tacacs+, local are not matching for login"]},
    },
    (VerifyAuthzMethods, "success"): {
        "eos_data": [
            {
                "commandsAuthzMethods": {"privilege0-15": {"methods": ["group tacacs+", "local"]}},
                "execAuthzMethods": {"exec": {"methods": ["group tacacs+", "local"]}},
            }
        ],
        "inputs": {"methods": ["tacacs+", "local"], "types": ["commands", "exec"]},
        "expected": {"result": AntaTestStatus.SUCCESS},
    },
    (VerifyAuthzMethods, "success-skipping-exec"): {
        "eos_data": [
            {
                "commandsAuthzMethods": {"privilege0-15": {"methods": ["group tacacs+", "local"]}},
                "execAuthzMethods": {"exec": {"methods": ["group tacacs+", "local"]}},
            }
        ],
        "inputs": {"methods": ["tacacs+", "local"], "types": ["commands"]},
        "expected": {"result": AntaTestStatus.SUCCESS},
    },
    (VerifyAuthzMethods, "failure-commands"): {
        "eos_data": [
            {
                "commandsAuthzMethods": {"privilege0-15": {"methods": ["group radius", "local"]}},
                "execAuthzMethods": {"exec": {"methods": ["group tacacs+", "local"]}},
            }
        ],
        "inputs": {"methods": ["tacacs+", "local"], "types": ["commands", "exec"]},
        "expected": {"result": AntaTestStatus.FAILURE, "messages": ["AAA authorization methods group tacacs+, local are not matching for commands"]},
    },
    (VerifyAuthzMethods, "failure-exec"): {
        "eos_data": [
            {
                "commandsAuthzMethods": {"privilege0-15": {"methods": ["group tacacs+", "local"]}},
                "execAuthzMethods": {"exec": {"methods": ["group radius", "local"]}},
            }
        ],
        "inputs": {"methods": ["tacacs+", "local"], "types": ["commands", "exec"]},
        "expected": {"result": AntaTestStatus.FAILURE, "messages": ["AAA authorization methods group tacacs+, local are not matching for exec"]},
    },
    (VerifyAcctDefaultMethods, "success-commands-exec-system"): {
        "eos_data": [
            {
                "commandsAcctMethods": {"privilege0-15": {"defaultAction": "startStop", "defaultMethods": ["group tacacs+", "logging"], "consoleMethods": []}},
                "execAcctMethods": {"exec": {"defaultAction": "startStop", "defaultMethods": ["group tacacs+", "logging"], "consoleMethods": []}},
                "systemAcctMethods": {"system": {"defaultAction": "startStop", "defaultMethods": ["group tacacs+", "logging"], "consoleMethods": []}},
                "dot1xAcctMethods": {"dot1x": {"defaultMethods": [], "consoleMethods": []}},
            }
        ],
        "inputs": {"methods": ["tacacs+", "logging"], "types": ["commands", "exec", "system"]},
        "expected": {"result": AntaTestStatus.SUCCESS},
    },
    (VerifyAcctDefaultMethods, "success-dot1x"): {
        "eos_data": [
            {
                "commandsAcctMethods": {"privilege0-15": {"defaultAction": "startStop", "defaultMethods": ["group tacacs+", "logging"], "consoleMethods": []}},
                "execAcctMethods": {"exec": {"defaultAction": "startStop", "defaultMethods": ["group tacacs+", "logging"], "consoleMethods": []}},
                "systemAcctMethods": {"system": {"defaultAction": "startStop", "defaultMethods": ["group tacacs+", "logging"], "consoleMethods": []}},
                "dot1xAcctMethods": {"dot1x": {"defaultAction": "startStop", "defaultMethods": ["group radius", "logging"], "consoleMethods": []}},
            }
        ],
        "inputs": {"methods": ["radius", "logging"], "types": ["dot1x"]},
        "expected": {"result": AntaTestStatus.SUCCESS},
    },
    (VerifyAcctDefaultMethods, "failure-not-configured"): {
        "eos_data": [
            {
                "commandsAcctMethods": {"privilege0-15": {"defaultMethods": [], "consoleMethods": []}},
                "execAcctMethods": {"exec": {"defaultAction": "startStop", "defaultMethods": ["group tacacs+", "logging"], "consoleMethods": []}},
                "systemAcctMethods": {"system": {"defaultAction": "startStop", "defaultMethods": ["group tacacs+", "logging"], "consoleMethods": []}},
                "dot1xAcctMethods": {"dot1x": {"defaultMethods": [], "consoleMethods": []}},
            }
        ],
        "inputs": {"methods": ["tacacs+", "logging"], "types": ["commands", "exec", "system"]},
        "expected": {"result": AntaTestStatus.FAILURE, "messages": ["AAA default accounting is not configured for commands"]},
    },
    (VerifyAcctDefaultMethods, "failure-not-configured-empty"): {
        "eos_data": [
            {
                "systemAcctMethods": {"system": {"defaultMethods": [], "consoleMethods": []}},
                "execAcctMethods": {"exec": {"defaultMethods": [], "consoleMethods": []}},
                "commandsAcctMethods": {"privilege0-15": {"defaultMethods": [], "consoleMethods": []}},
                "dot1xAcctMethods": {"dot1x": {"defaultMethods": [], "consoleMethods": []}},
            }
        ],
        "inputs": {"methods": ["tacacs+", "logging"], "types": ["commands", "exec", "system"]},
        "expected": {"result": AntaTestStatus.FAILURE, "messages": ["AAA default accounting is not configured for system, exec, commands"]},
    },
    (VerifyAcctDefaultMethods, "failure-not-matching"): {
        "eos_data": [
            {
                "commandsAcctMethods": {"privilege0-15": {"defaultAction": "startStop", "defaultMethods": ["group radius", "logging"], "consoleMethods": []}},
                "execAcctMethods": {"exec": {"defaultAction": "startStop", "defaultMethods": ["group tacacs+", "logging"], "consoleMethods": []}},
                "systemAcctMethods": {"system": {"defaultAction": "startStop", "defaultMethods": ["group tacacs+", "logging"], "consoleMethods": []}},
                "dot1xAcctMethods": {"dot1x": {"defaultMethods": [], "consoleMethods": []}},
            }
        ],
        "inputs": {"methods": ["tacacs+", "logging"], "types": ["commands", "exec", "system"]},
        "expected": {"result": AntaTestStatus.FAILURE, "messages": ["AAA accounting default methods group tacacs+, logging are not matching for commands"]},
    },
    (VerifyAcctConsoleMethods, "success-commands-exec-system"): {
        "eos_data": [
            {
                "commandsAcctMethods": {"privilege0-15": {"defaultMethods": [], "consoleAction": "startStop", "consoleMethods": ["group tacacs+", "logging"]}},
                "execAcctMethods": {"exec": {"defaultMethods": [], "consoleAction": "startStop", "consoleMethods": ["group tacacs+", "logging"]}},
                "systemAcctMethods": {"system": {"defaultMethods": [], "consoleAction": "startStop", "consoleMethods": ["group tacacs+", "logging"]}},
                "dot1xAcctMethods": {"dot1x": {"defaultMethods": [], "consoleMethods": []}},
            }
        ],
        "inputs": {"methods": ["tacacs+", "logging"], "types": ["commands", "exec", "system"]},
        "expected": {"result": AntaTestStatus.SUCCESS},
    },
    (VerifyAcctConsoleMethods, "success-dot1x"): {
        "eos_data": [
            {
                "commandsAcctMethods": {"privilege0-15": {"defaultMethods": [], "consoleAction": "startStop", "consoleMethods": ["group tacacs+", "logging"]}},
                "execAcctMethods": {"exec": {"defaultMethods": [], "consoleAction": "startStop", "consoleMethods": ["group tacacs+", "logging"]}},
                "systemAcctMethods": {"system": {"defaultMethods": [], "consoleAction": "startStop", "consoleMethods": ["group tacacs+", "logging"]}},
                "dot1xAcctMethods": {"dot1x": {"defaultMethods": [], "consoleAction": "startStop", "consoleMethods": ["group tacacs+", "logging"]}},
            }
        ],
        "inputs": {"methods": ["tacacs+", "logging"], "types": ["dot1x"]},
        "expected": {"result": AntaTestStatus.SUCCESS},
    },
    (VerifyAcctConsoleMethods, "failure-not-configured"): {
        "eos_data": [
            {
                "commandsAcctMethods": {"privilege0-15": {"defaultMethods": [], "consoleMethods": []}},
                "execAcctMethods": {"exec": {"defaultMethods": [], "consoleAction": "startStop", "consoleMethods": ["group tacacs+", "logging"]}},
                "systemAcctMethods": {"system": {"defaultMethods": [], "consoleAction": "startStop", "consoleMethods": ["group tacacs+", "logging"]}},
                "dot1xAcctMethods": {"dot1x": {"defaultMethods": [], "consoleMethods": []}},
            }
        ],
        "inputs": {"methods": ["tacacs+", "logging"], "types": ["commands", "exec", "system"]},
        "expected": {"result": AntaTestStatus.FAILURE, "messages": ["AAA console accounting is not configured for commands"]},
    },
    (VerifyAcctConsoleMethods, "failure-not-configured-empty"): {
        "eos_data": [
            {
                "systemAcctMethods": {"system": {"defaultMethods": [], "consoleMethods": []}},
                "execAcctMethods": {"exec": {"defaultMethods": [], "consoleMethods": []}},
                "commandsAcctMethods": {"privilege0-15": {"defaultMethods": [], "consoleMethods": []}},
                "dot1xAcctMethods": {"dot1x": {"defaultMethods": [], "consoleMethods": []}},
            }
        ],
        "inputs": {"methods": ["tacacs+", "logging"], "types": ["commands", "exec", "system"]},
        "expected": {"result": AntaTestStatus.FAILURE, "messages": ["AAA console accounting is not configured for system, exec, commands"]},
    },
    (VerifyAcctConsoleMethods, "failure-not-matching"): {
        "eos_data": [
            {
                "commandsAcctMethods": {"privilege0-15": {"defaultMethods": [], "consoleAction": "startStop", "consoleMethods": ["group radius", "logging"]}},
                "execAcctMethods": {"exec": {"defaultMethods": [], "consoleAction": "startStop", "consoleMethods": ["group tacacs+", "logging"]}},
                "systemAcctMethods": {"system": {"defaultMethods": [], "consoleAction": "startStop", "consoleMethods": ["group tacacs+", "logging"]}},
                "dot1xAcctMethods": {"dot1x": {"defaultMethods": [], "consoleMethods": []}},
            }
        ],
        "inputs": {"methods": ["tacacs+", "logging"], "types": ["commands", "exec", "system"]},
        "expected": {"result": AntaTestStatus.FAILURE, "messages": ["AAA accounting console methods group tacacs+, logging are not matching for commands"]},
    },
    (VerifyAcctMethods, "success-default-methods"): {
        "eos_data": [
            {
                "commandsAcctMethods": {"privilege0-15": {"defaultAction": "startStop", "defaultMethods": ["group tacacs+", "logging"], "consoleMethods": []}},
                "execAcctMethods": {"exec": {"defaultAction": "startStop", "defaultMethods": ["group tacacs+", "logging"], "consoleMethods": []}},
                "systemAcctMethods": {"system": {"defaultAction": "startStop", "defaultMethods": ["group tacacs+", "logging"], "consoleMethods": []}},
                "dot1xAcctMethods": {"dot1x": {"defaultMethods": [], "consoleMethods": []}},
            }
        ],
        "inputs": {
            "accounting": [
                {"acct_type": "commands", "method_configs": [{"name": "all", "default_methods": ["tacacs+", "logging"]}]},
                {"acct_type": "exec", "method_configs": [{"name": "exec", "default_methods": ["tacacs+", "logging"]}]},
                {"acct_type": "system", "method_configs": [{"name": "system", "default_methods": ["tacacs+", "logging"]}]},
            ]
        },
        "expected": {
            "result": AntaTestStatus.SUCCESS,
            "atomic_results": [
                {"description": "AAA commands accounting - privilege0-15", "result": AntaTestStatus.SUCCESS},
                {"description": "AAA exec accounting", "result": AntaTestStatus.SUCCESS},
                {"description": "AAA system accounting", "result": AntaTestStatus.SUCCESS},
            ],
        },
    },
    (VerifyAcctMethods, "success-console-methods"): {
        "eos_data": [
            {
                "commandsAcctMethods": {"privilege0-15": {"defaultMethods": [], "consoleAction": "startStop", "consoleMethods": ["group tacacs+", "logging"]}},
                "execAcctMethods": {"exec": {"defaultMethods": [], "consoleAction": "startStop", "consoleMethods": ["group tacacs+", "logging"]}},
                "systemAcctMethods": {"system": {"defaultAction": "startStop", "defaultMethods": ["group tacacs+", "logging"], "consoleMethods": []}},
                "dot1xAcctMethods": {"dot1x": {"defaultMethods": [], "consoleMethods": []}},
            }
        ],
        "inputs": {
            "accounting": [
                {"acct_type": "commands", "method_configs": [{"name": "all", "console_methods": ["tacacs+", "logging"]}]},
                {"acct_type": "exec", "method_configs": [{"name": "exec", "console_methods": ["tacacs+", "logging"]}]},
            ]
        },
        "expected": {
            "result": AntaTestStatus.SUCCESS,
            "atomic_results": [
                {"description": "AAA commands accounting - privilege0-15", "result": AntaTestStatus.SUCCESS},
                {"description": "AAA exec accounting", "result": AntaTestStatus.SUCCESS},
            ],
        },
    },
    (VerifyAcctMethods, "success-both-planes"): {
        # Both default and console methods verified for commands; only default for exec
        "eos_data": [
            {
                "commandsAcctMethods": {
                    "privilege0-15": {
                        "defaultAction": "startStop",
                        "defaultMethods": ["group tacacs+", "logging"],
                        "consoleAction": "startStop",
                        "consoleMethods": ["group tacacs+", "logging"],
                    }
                },
                "execAcctMethods": {"exec": {"defaultAction": "startStop", "defaultMethods": ["group tacacs+", "logging"], "consoleMethods": []}},
                "systemAcctMethods": {"system": {"defaultAction": "startStop", "defaultMethods": ["group tacacs+", "logging"], "consoleMethods": []}},
                "dot1xAcctMethods": {"dot1x": {"defaultMethods": [], "consoleMethods": []}},
            }
        ],
        "inputs": {
            "accounting": [
                {
                    "acct_type": "commands",
                    "method_configs": [{"name": "all", "default_methods": ["tacacs+", "logging"], "console_methods": ["tacacs+", "logging"]}],
                },
                {"acct_type": "exec", "method_configs": [{"name": "exec", "default_methods": ["tacacs+", "logging"]}]},
            ]
        },
        "expected": {
            "result": AntaTestStatus.SUCCESS,
            "atomic_results": [
                {"description": "AAA commands accounting - privilege0-15", "result": AntaTestStatus.SUCCESS},
                {"description": "AAA exec accounting", "result": AntaTestStatus.SUCCESS},
            ],
        },
    },
    (VerifyAcctMethods, "success-dot1x"): {
        "eos_data": [
            {
                "commandsAcctMethods": {"privilege0-15": {"defaultAction": "startStop", "defaultMethods": ["group tacacs+", "logging"], "consoleMethods": []}},
                "execAcctMethods": {"exec": {"defaultAction": "startStop", "defaultMethods": ["group tacacs+", "logging"], "consoleMethods": []}},
                "systemAcctMethods": {"system": {"defaultAction": "startStop", "defaultMethods": ["group tacacs+", "logging"], "consoleMethods": []}},
                "dot1xAcctMethods": {"dot1x": {"defaultAction": "startStop", "defaultMethods": ["group radius", "logging"], "consoleMethods": []}},
            }
        ],
        "inputs": {
            "accounting": [
                {"acct_type": "dot1x", "method_configs": [{"name": "dot1x", "default_methods": ["radius", "logging"]}]},
            ]
        },
        "expected": {
            "result": AntaTestStatus.SUCCESS,
            "atomic_results": [
                {"description": "AAA dot1x accounting", "result": AntaTestStatus.SUCCESS},
            ],
        },
    },
    (VerifyAcctMethods, "failure-default-not-configured"): {
        # defaultAction is absent for commands — accounting not set up on that type
        "eos_data": [
            {
                "commandsAcctMethods": {"privilege0-15": {"defaultMethods": [], "consoleMethods": []}},
                "execAcctMethods": {"exec": {"defaultAction": "startStop", "defaultMethods": ["group tacacs+", "logging"], "consoleMethods": []}},
                "systemAcctMethods": {"system": {"defaultAction": "startStop", "defaultMethods": ["group tacacs+", "logging"], "consoleMethods": []}},
                "dot1xAcctMethods": {"dot1x": {"defaultMethods": [], "consoleMethods": []}},
            }
        ],
        "inputs": {
            "accounting": [
                {"acct_type": "commands", "method_configs": [{"name": "all", "default_methods": ["tacacs+", "logging"]}]},
                {"acct_type": "exec", "method_configs": [{"name": "exec", "default_methods": ["tacacs+", "logging"]}]},
            ]
        },
        "expected": {
            "result": AntaTestStatus.FAILURE,
            "messages": ["AAA commands accounting - privilege0-15 - Default methods - Not configured"],
            "atomic_results": [
                {
                    "description": "AAA commands accounting - privilege0-15",
                    "result": AntaTestStatus.FAILURE,
                    "messages": ["Default methods - Not configured"],
                },
                {"description": "AAA exec accounting", "result": AntaTestStatus.SUCCESS},
            ],
        },
    },
    (VerifyAcctMethods, "failure-console-not-configured"): {
        # consoleAction is absent for commands
        "eos_data": [
            {
                "commandsAcctMethods": {"privilege0-15": {"defaultMethods": [], "consoleMethods": []}},
                "execAcctMethods": {"exec": {"defaultMethods": [], "consoleAction": "startStop", "consoleMethods": ["group tacacs+", "logging"]}},
                "systemAcctMethods": {"system": {"defaultAction": "startStop", "defaultMethods": ["group tacacs+", "logging"], "consoleMethods": []}},
                "dot1xAcctMethods": {"dot1x": {"defaultMethods": [], "consoleMethods": []}},
            }
        ],
        "inputs": {
            "accounting": [
                {"acct_type": "commands", "method_configs": [{"name": "all", "console_methods": ["tacacs+", "logging"]}]},
                {"acct_type": "exec", "method_configs": [{"name": "exec", "console_methods": ["tacacs+", "logging"]}]},
            ]
        },
        "expected": {
            "result": AntaTestStatus.FAILURE,
            "messages": ["AAA commands accounting - privilege0-15 - Console methods - Not configured"],
            "atomic_results": [
                {
                    "description": "AAA commands accounting - privilege0-15",
                    "result": AntaTestStatus.FAILURE,
                    "messages": ["Console methods - Not configured"],
                },
                {"description": "AAA exec accounting", "result": AntaTestStatus.SUCCESS},
            ],
        },
    },
    (VerifyAcctMethods, "failure-default-not-matching"): {
        # commands has radius instead of the expected tacacs+
        "eos_data": [
            {
                "commandsAcctMethods": {"privilege0-15": {"defaultAction": "startStop", "defaultMethods": ["group radius", "logging"], "consoleMethods": []}},
                "execAcctMethods": {"exec": {"defaultAction": "startStop", "defaultMethods": ["group tacacs+", "logging"], "consoleMethods": []}},
                "systemAcctMethods": {"system": {"defaultAction": "startStop", "defaultMethods": ["group tacacs+", "logging"], "consoleMethods": []}},
                "dot1xAcctMethods": {"dot1x": {"defaultMethods": [], "consoleMethods": []}},
            }
        ],
        "inputs": {
            "accounting": [
                {"acct_type": "commands", "method_configs": [{"name": "all", "default_methods": ["tacacs+", "logging"]}]},
                {"acct_type": "exec", "method_configs": [{"name": "exec", "default_methods": ["tacacs+", "logging"]}]},
            ]
        },
        "expected": {
            "result": AntaTestStatus.FAILURE,
            "messages": ["AAA commands accounting - privilege0-15 - Default methods - Mismatch - Expected: group tacacs+, logging, Actual: group radius, logging"],
            "atomic_results": [
                {
                    "description": "AAA commands accounting - privilege0-15",
                    "result": AntaTestStatus.FAILURE,
                    "messages": ["Default methods - Mismatch - Expected: group tacacs+, logging, Actual: group radius, logging"],
                },
                {"description": "AAA exec accounting", "result": AntaTestStatus.SUCCESS},
            ],
        },
    },
    (VerifyAcctMethods, "failure-console-not-matching"): {
        # commands has radius instead of the expected tacacs+ on the console plane
        "eos_data": [
            {
                "commandsAcctMethods": {"privilege0-15": {"defaultMethods": [], "consoleAction": "startStop", "consoleMethods": ["group radius", "logging"]}},
                "execAcctMethods": {"exec": {"defaultMethods": [], "consoleAction": "startStop", "consoleMethods": ["group tacacs+", "logging"]}},
                "systemAcctMethods": {"system": {"defaultAction": "startStop", "defaultMethods": ["group tacacs+", "logging"], "consoleMethods": []}},
                "dot1xAcctMethods": {"dot1x": {"defaultMethods": [], "consoleMethods": []}},
            }
        ],
        "inputs": {
            "accounting": [
                {"acct_type": "commands", "method_configs": [{"name": "all", "console_methods": ["tacacs+", "logging"]}]},
                {"acct_type": "exec", "method_configs": [{"name": "exec", "console_methods": ["tacacs+", "logging"]}]},
            ]
        },
        "expected": {
            "result": AntaTestStatus.FAILURE,
            "messages": ["AAA commands accounting - privilege0-15 - Console methods - Mismatch - Expected: group tacacs+, logging, Actual: group radius, logging"],
            "atomic_results": [
                {
                    "description": "AAA commands accounting - privilege0-15",
                    "result": AntaTestStatus.FAILURE,
                    "messages": ["Console methods - Mismatch - Expected: group tacacs+, logging, Actual: group radius, logging"],
                },
                {"description": "AAA exec accounting", "result": AntaTestStatus.SUCCESS},
            ],
        },
    },
    (VerifyAcctMethods, "failure-method-list-not-found"): {
        # privilege1-5 does not appear in EOS output
        "eos_data": [
            {
                "commandsAcctMethods": {"privilege0-15": {"defaultAction": "startStop", "defaultMethods": ["group tacacs+", "logging"], "consoleMethods": []}},
                "execAcctMethods": {"exec": {"defaultAction": "startStop", "defaultMethods": ["group tacacs+", "logging"], "consoleMethods": []}},
                "systemAcctMethods": {"system": {"defaultAction": "startStop", "defaultMethods": ["group tacacs+", "logging"], "consoleMethods": []}},
                "dot1xAcctMethods": {"dot1x": {"defaultMethods": [], "consoleMethods": []}},
            }
        ],
        "inputs": {
            "accounting": [
                {"acct_type": "commands", "method_configs": [{"name": "privilege1-5", "default_methods": ["tacacs+", "logging"]}]},
            ]
        },
        "expected": {
            "result": AntaTestStatus.FAILURE,
            "messages": ["AAA commands accounting - privilege1-5 - Not found"],
            "atomic_results": [
                {
                    "description": "AAA commands accounting - privilege1-5",
                    "result": AntaTestStatus.FAILURE,
                    "messages": ["Not found"],
                },
            ],
        },
    },
    (VerifyAcctMethods, "failure-multiple-methods-not-matching"): {
        # Both default and console methods are wrong for commands privilege0-15
        "eos_data": [
            {
                "commandsAcctMethods": {
                    "privilege0-15": {
                        "defaultAction": "startStop",
                        "defaultMethods": ["group radius", "logging"],
                        "consoleAction": "startStop",
                        "consoleMethods": ["group radius", "logging"],
                    }
                },
                "execAcctMethods": {"exec": {"defaultAction": "startStop", "defaultMethods": ["group tacacs+", "logging"], "consoleMethods": []}},
                "systemAcctMethods": {"system": {"defaultAction": "startStop", "defaultMethods": ["group tacacs+", "logging"], "consoleMethods": []}},
                "dot1xAcctMethods": {"dot1x": {"defaultMethods": [], "consoleMethods": []}},
            }
        ],
        "inputs": {
            "accounting": [
                {
                    "acct_type": "commands",
                    "method_configs": [{"name": "all", "default_methods": ["tacacs+", "logging"], "console_methods": ["tacacs+", "logging"]}],
                },
            ]
        },
        "expected": {
            "result": AntaTestStatus.FAILURE,
            "messages": [
                "AAA commands accounting - privilege0-15 - Default methods - Mismatch - Expected: group tacacs+, logging, Actual: group radius, logging",
                "AAA commands accounting - privilege0-15 - Console methods - Mismatch - Expected: group tacacs+, logging, Actual: group radius, logging",
            ],
            "atomic_results": [
                {
                    "description": "AAA commands accounting - privilege0-15",
                    "result": AntaTestStatus.FAILURE,
                    "messages": [
                        "Default methods - Mismatch - Expected: group tacacs+, logging, Actual: group radius, logging",
                        "Console methods - Mismatch - Expected: group tacacs+, logging, Actual: group radius, logging",
                    ],
                },
            ],
        },
    },
    (VerifyAcctMethods, "failure-exec-default-not-configured"): {
        # exec accounting exists but defaultAction is absent — default plane not configured
        "eos_data": [
            {
                "commandsAcctMethods": {},
                "execAcctMethods": {"exec": {"defaultMethods": [], "consoleMethods": []}},
                "systemAcctMethods": {},
                "dot1xAcctMethods": {},
            }
        ],
        "inputs": {
            "accounting": [
                {"acct_type": "exec", "method_configs": [{"name": "exec", "default_methods": ["tacacs+", "logging"]}]},
            ]
        },
        "expected": {
            "result": AntaTestStatus.FAILURE,
            "messages": ["AAA exec accounting - Default methods - Not configured"],
            "atomic_results": [
                {
                    "description": "AAA exec accounting",
                    "result": AntaTestStatus.FAILURE,
                    "messages": ["Default methods - Not configured"],
                },
            ],
        },
    },
    (VerifyAcctMethods, "failure-exec-default-not-matching"): {
        # exec default plane is configured but with radius instead of the expected tacacs+
        "eos_data": [
            {
                "commandsAcctMethods": {},
                "execAcctMethods": {"exec": {"defaultAction": "startStop", "defaultMethods": ["group radius", "logging"], "consoleMethods": []}},
                "systemAcctMethods": {},
                "dot1xAcctMethods": {},
            }
        ],
        "inputs": {
            "accounting": [
                {"acct_type": "exec", "method_configs": [{"name": "exec", "default_methods": ["tacacs+", "logging"]}]},
            ]
        },
        "expected": {
            "result": AntaTestStatus.FAILURE,
            "messages": ["AAA exec accounting - Default methods - Mismatch - Expected: group tacacs+, logging, Actual: group radius, logging"],
            "atomic_results": [
                {
                    "description": "AAA exec accounting",
                    "result": AntaTestStatus.FAILURE,
                    "messages": ["Default methods - Mismatch - Expected: group tacacs+, logging, Actual: group radius, logging"],
                },
            ],
        },
    },
    (VerifyAcctMethods, "failure-exec-console-not-configured"): {
        # exec accounting exists but consoleAction is absent — console plane not configured
        "eos_data": [
            {
                "commandsAcctMethods": {},
                "execAcctMethods": {"exec": {"defaultMethods": [], "consoleMethods": []}},
                "systemAcctMethods": {},
                "dot1xAcctMethods": {},
            }
        ],
        "inputs": {
            "accounting": [
                {"acct_type": "exec", "method_configs": [{"name": "exec", "console_methods": ["tacacs+", "logging"]}]},
            ]
        },
        "expected": {
            "result": AntaTestStatus.FAILURE,
            "messages": ["AAA exec accounting - Console methods - Not configured"],
            "atomic_results": [
                {
                    "description": "AAA exec accounting",
                    "result": AntaTestStatus.FAILURE,
                    "messages": ["Console methods - Not configured"],
                },
            ],
        },
    },
    (VerifyAcctMethods, "failure-exec-console-not-matching"): {
        # exec console plane is configured but with radius instead of the expected tacacs+
        "eos_data": [
            {
                "commandsAcctMethods": {},
                "execAcctMethods": {"exec": {"defaultMethods": [], "consoleAction": "startStop", "consoleMethods": ["group radius", "logging"]}},
                "systemAcctMethods": {},
                "dot1xAcctMethods": {},
            }
        ],
        "inputs": {
            "accounting": [
                {"acct_type": "exec", "method_configs": [{"name": "exec", "console_methods": ["tacacs+", "logging"]}]},
            ]
        },
        "expected": {
            "result": AntaTestStatus.FAILURE,
            "messages": ["AAA exec accounting - Console methods - Mismatch - Expected: group tacacs+, logging, Actual: group radius, logging"],
            "atomic_results": [
                {
                    "description": "AAA exec accounting",
                    "result": AntaTestStatus.FAILURE,
                    "messages": ["Console methods - Mismatch - Expected: group tacacs+, logging, Actual: group radius, logging"],
                },
            ],
        },
    },
    (VerifyAcctMethods, "failure-system-default-not-configured"): {
        # system accounting exists but defaultAction is absent — default plane not configured
        "eos_data": [
            {
                "commandsAcctMethods": {},
                "execAcctMethods": {},
                "systemAcctMethods": {"system": {"defaultMethods": [], "consoleMethods": []}},
                "dot1xAcctMethods": {},
            }
        ],
        "inputs": {
            "accounting": [
                {"acct_type": "system", "method_configs": [{"name": "system", "default_methods": ["tacacs+", "logging"]}]},
            ]
        },
        "expected": {
            "result": AntaTestStatus.FAILURE,
            "messages": ["AAA system accounting - Default methods - Not configured"],
            "atomic_results": [
                {
                    "description": "AAA system accounting",
                    "result": AntaTestStatus.FAILURE,
                    "messages": ["Default methods - Not configured"],
                },
            ],
        },
    },
    (VerifyAcctMethods, "failure-system-default-not-matching"): {
        # system default plane is configured but with radius instead of the expected tacacs+
        "eos_data": [
            {
                "commandsAcctMethods": {},
                "execAcctMethods": {},
                "systemAcctMethods": {"system": {"defaultAction": "startStop", "defaultMethods": ["group radius", "logging"], "consoleMethods": []}},
                "dot1xAcctMethods": {},
            }
        ],
        "inputs": {
            "accounting": [
                {"acct_type": "system", "method_configs": [{"name": "system", "default_methods": ["tacacs+", "logging"]}]},
            ]
        },
        "expected": {
            "result": AntaTestStatus.FAILURE,
            "messages": ["AAA system accounting - Default methods - Mismatch - Expected: group tacacs+, logging, Actual: group radius, logging"],
            "atomic_results": [
                {
                    "description": "AAA system accounting",
                    "result": AntaTestStatus.FAILURE,
                    "messages": ["Default methods - Mismatch - Expected: group tacacs+, logging, Actual: group radius, logging"],
                },
            ],
        },
    },
    (VerifyAcctMethods, "failure-dot1x-default-not-configured"): {
        # dot1x accounting exists but defaultAction is absent — default plane not configured
        "eos_data": [
            {
                "commandsAcctMethods": {},
                "execAcctMethods": {},
                "systemAcctMethods": {},
                "dot1xAcctMethods": {"dot1x": {"defaultMethods": [], "consoleMethods": []}},
            }
        ],
        "inputs": {
            "accounting": [
                {"acct_type": "dot1x", "method_configs": [{"name": "dot1x", "default_methods": ["radius"]}]},
            ]
        },
        "expected": {
            "result": AntaTestStatus.FAILURE,
            "messages": ["AAA dot1x accounting - Default methods - Not configured"],
            "atomic_results": [
                {
                    "description": "AAA dot1x accounting",
                    "result": AntaTestStatus.FAILURE,
                    "messages": ["Default methods - Not configured"],
                },
            ],
        },
    },
    (VerifyAcctMethods, "failure-dot1x-default-not-matching"): {
        # dot1x default plane is configured but with tacacs+ instead of the expected radius
        "eos_data": [
            {
                "commandsAcctMethods": {},
                "execAcctMethods": {},
                "systemAcctMethods": {},
                "dot1xAcctMethods": {"dot1x": {"defaultAction": "startStop", "defaultMethods": ["group tacacs+"], "consoleMethods": []}},
            }
        ],
        "inputs": {
            "accounting": [
                {"acct_type": "dot1x", "method_configs": [{"name": "dot1x", "default_methods": ["radius"]}]},
            ]
        },
        "expected": {
            "result": AntaTestStatus.FAILURE,
            "messages": ["AAA dot1x accounting - Default methods - Mismatch - Expected: group radius, Actual: group tacacs+"],
            "atomic_results": [
                {
                    "description": "AAA dot1x accounting",
                    "result": AntaTestStatus.FAILURE,
                    "messages": ["Default methods - Mismatch - Expected: group radius, Actual: group tacacs+"],
                },
            ],
        },
    },
    (VerifyAcctMethods, "failure-exec-method-list-not-found"): {
        # exec method list is absent from EOS output entirely
        "eos_data": [
            {
                "commandsAcctMethods": {},
                "execAcctMethods": {},
                "systemAcctMethods": {},
                "dot1xAcctMethods": {},
            }
        ],
        "inputs": {
            "accounting": [
                {"acct_type": "exec", "method_configs": [{"name": "exec", "default_methods": ["tacacs+"]}]},
            ]
        },
        "expected": {
            "result": AntaTestStatus.FAILURE,
            "messages": ["AAA exec accounting - Not found"],
            "atomic_results": [
                {
                    "description": "AAA exec accounting",
                    "result": AntaTestStatus.FAILURE,
                    "messages": ["Not found"],
                },
            ],
        },
    },
    (VerifyAcctMethods, "failure-multiple-acct-types"): {
        # commands privilege0-15 not found; exec default methods mismatch; system passes
        "eos_data": [
            {
                "commandsAcctMethods": {},
                "execAcctMethods": {"exec": {"defaultAction": "startStop", "defaultMethods": ["group radius"], "consoleMethods": []}},
                "systemAcctMethods": {"system": {"defaultAction": "startStop", "defaultMethods": ["group tacacs+", "logging"], "consoleMethods": []}},
                "dot1xAcctMethods": {},
            }
        ],
        "inputs": {
            "accounting": [
                {"acct_type": "commands", "method_configs": [{"name": "all", "default_methods": ["tacacs+", "logging"]}]},
                {"acct_type": "exec", "method_configs": [{"name": "exec", "default_methods": ["tacacs+", "logging"]}]},
                {"acct_type": "system", "method_configs": [{"name": "system", "default_methods": ["tacacs+", "logging"]}]},
            ]
        },
        "expected": {
            "result": AntaTestStatus.FAILURE,
            "messages": [
                "AAA commands accounting - privilege0-15 - Not found",
                "AAA exec accounting - Default methods - Mismatch - Expected: group tacacs+, logging, Actual: group radius",
            ],
            "atomic_results": [
                {
                    "description": "AAA commands accounting - privilege0-15",
                    "result": AntaTestStatus.FAILURE,
                    "messages": ["Not found"],
                },
                {
                    "description": "AAA exec accounting",
                    "result": AntaTestStatus.FAILURE,
                    "messages": ["Default methods - Mismatch - Expected: group tacacs+, logging, Actual: group radius"],
                },
                {"description": "AAA system accounting", "result": AntaTestStatus.SUCCESS},
            ],
        },
    },
    (VerifyAcctMethods, "failure-commands-multiple-privilege-ranges"): {
        # Two privilege ranges: privilege0-5 not found; privilege6-15 default methods mismatch
        "eos_data": [
            {
                "commandsAcctMethods": {"privilege6-15": {"defaultAction": "startStop", "defaultMethods": ["group radius"], "consoleMethods": []}},
                "execAcctMethods": {},
                "systemAcctMethods": {},
                "dot1xAcctMethods": {},
            }
        ],
        "inputs": {
            "accounting": [
                {
                    "acct_type": "commands",
                    "method_configs": [
                        {"name": "privilege0-5", "default_methods": ["tacacs+", "logging"]},
                        {"name": "privilege6-15", "default_methods": ["tacacs+", "logging"]},
                    ],
                }
            ]
        },
        "expected": {
            "result": AntaTestStatus.FAILURE,
            "messages": [
                "AAA commands accounting - privilege0-5 - Not found",
                "AAA commands accounting - privilege6-15 - Default methods - Mismatch - Expected: group tacacs+, logging, Actual: group radius",
            ],
            "atomic_results": [
                {
                    "description": "AAA commands accounting - privilege0-5",
                    "result": AntaTestStatus.FAILURE,
                    "messages": ["Not found"],
                },
                {
                    "description": "AAA commands accounting - privilege6-15",
                    "result": AntaTestStatus.FAILURE,
                    "messages": ["Default methods - Mismatch - Expected: group tacacs+, logging, Actual: group radius"],
                },
            ],
        },
    },
}
