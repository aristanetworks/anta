# Copyright (c) 2023-2025 Arista Networks, Inc.
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
    VerifyAuthenMethods,
    VerifyAuthzMethods,
    VerifyTacacsServerGroups,
    VerifyTacacsServers,
    VerifyTacacsSourceIntf,
)
from tests.units.anta_tests import AntaUnitTest, test

if sys.version_info >= (3, 10):
    from typing import TypeAlias
else:
    TypeAlias = type


AntaUnitTestDataDict: TypeAlias = dict[tuple[type[AntaTest], str], AntaUnitTest]

DATA: AntaUnitTestDataDict = {
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
}
