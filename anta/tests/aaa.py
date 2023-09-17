# Copyright (c) 2023 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""
Test functions related to the EOS various AAA settings
"""
# Mypy does not understand AntaTest.Input typing
# mypy: disable-error-code=attr-defined
from __future__ import annotations

from ipaddress import IPv4Address

# Need to keep List and Set for pydantic in python 3.8
from typing import List, Literal, Set

from anta.custom_types import AAAAuthMethod
from anta.models import AntaCommand, AntaTest


class VerifyTacacsSourceIntf(AntaTest):
    """
    Verifies TACACS source-interface for a specified VRF.

    Expected Results:
        * success: The test will pass if the provided TACACS source-interface is configured in the specified VRF.
        * failure: The test will fail if the provided TACACS source-interface is NOT configured in the specified VRF.
    """

    name = "VerifyTacacsSourceIntf"
    description = "Verifies TACACS source-interface for a specified VRF."
    categories = ["aaa"]
    commands = [AntaCommand(command="show tacacs")]

    class Input(AntaTest.Input):  # pylint: disable=missing-class-docstring
        intf: str
        """Source-interface to use as source IP of TACACS messages"""
        vrf: str = "default"
        """The name of the VRF to transport TACACS messages"""

    @AntaTest.anta_test
    def test(self) -> None:
        command_output = self.instance_commands[0].json_output
        try:
            if command_output["srcIntf"][self.inputs.vrf] == self.inputs.intf:
                self.result.is_success()
            else:
                self.result.is_failure(f"Wrong source-interface configured in VRF {self.inputs.vrf}")
        except KeyError:
            self.result.is_failure(f"Source-interface {self.inputs.intf} is not configured in VRF {self.inputs.vrf}")


class VerifyTacacsServers(AntaTest):
    """
    Verifies TACACS servers are configured for a specified VRF.

    Expected Results:
        * success: The test will pass if the provided TACACS servers are configured in the specified VRF.
        * failure: The test will fail if the provided TACACS servers are NOT configured in the specified VRF.
    """

    name = "VerifyTacacsServers"
    description = "Verifies TACACS servers are configured for a specified VRF."
    categories = ["aaa"]
    commands = [AntaCommand(command="show tacacs")]

    class Input(AntaTest.Input):  # pylint: disable=missing-class-docstring
        servers: List[IPv4Address]
        """List of TACACS servers"""
        vrf: str = "default"
        """The name of the VRF to transport TACACS messages"""

    @AntaTest.anta_test
    def test(self) -> None:
        command_output = self.instance_commands[0].json_output
        tacacs_servers = command_output["tacacsServers"]
        if not tacacs_servers:
            self.result.is_failure("No TACACS servers are configured")
            return
        not_configured = [
            str(server)
            for server in self.inputs.servers
            if not any(
                str(server) == tacacs_server["serverInfo"]["hostname"] and self.inputs.vrf == tacacs_server["serverInfo"]["vrf"] for tacacs_server in tacacs_servers
            )
        ]
        if not not_configured:
            self.result.is_success()
        else:
            self.result.is_failure(f"TACACS servers {not_configured} are not configured in VRF {self.inputs.vrf}")


class VerifyTacacsServerGroups(AntaTest):
    """
    Verifies if the provided TACACS server group(s) are configured.

    Expected Results:
        * success: The test will pass if the provided TACACS server group(s) are configured.
        * failure: The test will fail if one or all the provided TACACS server group(s) are NOT configured.
    """

    name = "VerifyTacacsServerGroups"
    description = "Verifies if the provided TACACS server group(s) are configured."
    categories = ["aaa"]
    commands = [AntaCommand(command="show tacacs")]

    class Input(AntaTest.Input):  # pylint: disable=missing-class-docstring
        groups: List[str]
        """List of TACACS server group"""

    @AntaTest.anta_test
    def test(self) -> None:
        command_output = self.instance_commands[0].json_output
        tacacs_groups = command_output["groups"]
        if not tacacs_groups:
            self.result.is_failure("No TACACS server group(s) are configured")
            return
        not_configured = [group for group in self.inputs.groups if group not in tacacs_groups]
        if not not_configured:
            self.result.is_success()
        else:
            self.result.is_failure(f"TACACS server group(s) {not_configured} are not configured")


class VerifyAuthenMethods(AntaTest):
    """
    Verifies the AAA authentication method lists for different authentication types (login, enable, dot1x).

    Expected Results:
        * success: The test will pass if the provided AAA authentication method list is matching in the configured authentication types.
        * failure: The test will fail if the provided AAA authentication method list is NOT matching in the configured authentication types.
    """

    name = "VerifyAuthenMethods"
    description = "Verifies the AAA authentication method lists for different authentication types (login, enable, dot1x)."
    categories = ["aaa"]
    commands = [AntaCommand(command="show aaa methods authentication")]

    class Input(AntaTest.Input):  # pylint: disable=missing-class-docstring
        methods: List[AAAAuthMethod]
        """List of AAA authentication methods. Methods should be in the right order"""
        types: Set[Literal["login", "enable", "dot1x"]]
        """List of authentication types to verify"""

    @AntaTest.anta_test
    def test(self) -> None:
        command_output = self.instance_commands[0].json_output
        not_matching = []
        for k, v in command_output.items():
            auth_type = k.replace("AuthenMethods", "")
            if auth_type not in self.inputs.types:
                # We do not need to verify this accounting type
                continue
            if auth_type == "login":
                if "login" not in v:
                    self.result.is_failure("AAA authentication methods are not configured for login console")
                    return
                if v["login"]["methods"] != self.inputs.methods:
                    self.result.is_failure(f"AAA authentication methods {self.inputs.methods} are not matching for login console")
                    return
            for methods in v.values():
                if methods["methods"] != self.inputs.methods:
                    not_matching.append(auth_type)
        if not not_matching:
            self.result.is_success()
        else:
            self.result.is_failure(f"AAA authentication methods {self.inputs.methods} are not matching for {not_matching}")


class VerifyAuthzMethods(AntaTest):
    """
    Verifies the AAA authorization method lists for different authorization types (commands, exec).

    Expected Results:
        * success: The test will pass if the provided AAA authorization method list is matching in the configured authorization types.
        * failure: The test will fail if the provided AAA authorization method list is NOT matching in the configured authorization types.
    """

    name = "VerifyAuthzMethods"
    description = "Verifies the AAA authorization method lists for different authorization types (commands, exec)."
    categories = ["aaa"]
    commands = [AntaCommand(command="show aaa methods authorization")]

    class Input(AntaTest.Input):  # pylint: disable=missing-class-docstring
        methods: List[AAAAuthMethod]
        """List of AAA authorization methods. Methods should be in the right order"""
        types: Set[Literal["commands", "exec"]]
        """List of authorization types to verify"""

    @AntaTest.anta_test
    def test(self) -> None:
        command_output = self.instance_commands[0].json_output
        not_matching = []
        for k, v in command_output.items():
            authz_type = k.replace("AuthzMethods", "")
            if authz_type not in self.inputs.types:
                # We do not need to verify this accounting type
                continue
            for methods in v.values():
                if methods["methods"] != self.inputs.methods:
                    not_matching.append(authz_type)
        if not not_matching:
            self.result.is_success()
        else:
            self.result.is_failure(f"AAA authorization methods {self.inputs.methods} are not matching for {not_matching}")


class VerifyAcctDefaultMethods(AntaTest):
    """
    Verifies the AAA accounting default method lists for different accounting types (system, exec, commands, dot1x).

    Expected Results:
        * success: The test will pass if the provided AAA accounting default method list is matching in the configured accounting types.
        * failure: The test will fail if the provided AAA accounting default method list is NOT matching in the configured accounting types.
    """

    name = "VerifyAcctDefaultMethods"
    description = "Verifies the AAA accounting default method lists for different accounting types (system, exec, commands, dot1x)."
    categories = ["aaa"]
    commands = [AntaCommand(command="show aaa methods accounting")]

    class Input(AntaTest.Input):  # pylint: disable=missing-class-docstring
        methods: List[AAAAuthMethod]
        """List of AAA accounting methods. Methods should be in the right order"""
        types: Set[Literal["commands", "exec", "system", "dot1x"]]
        """List of accounting types to verify"""

    @AntaTest.anta_test
    def test(self) -> None:
        command_output = self.instance_commands[0].json_output
        not_matching = []
        not_configured = []
        for k, v in command_output.items():
            acct_type = k.replace("AcctMethods", "")
            if acct_type not in self.inputs.types:
                # We do not need to verify this accounting type
                continue
            for methods in v.values():
                if "defaultAction" not in methods:
                    not_configured.append(acct_type)
                if methods["defaultMethods"] != self.inputs.methods:
                    not_matching.append(acct_type)
        if not_configured:
            self.result.is_failure(f"AAA default accounting is not configured for {not_configured}")
            return
        if not not_matching:
            self.result.is_success()
        else:
            self.result.is_failure(f"AAA accounting default methods {self.inputs.methods} are not matching for {not_matching}")


class VerifyAcctConsoleMethods(AntaTest):
    """
    Verifies the AAA accounting console method lists for different accounting types (system, exec, commands, dot1x).

    Expected Results:
        * success: The test will pass if the provided AAA accounting console method list is matching in the configured accounting types.
        * failure: The test will fail if the provided AAA accounting console method list is NOT matching in the configured accounting types.
    """

    name = "VerifyAcctConsoleMethods"
    description = "Verifies the AAA accounting console method lists for different accounting types (system, exec, commands, dot1x)."
    categories = ["aaa"]
    commands = [AntaCommand(command="show aaa methods accounting")]

    class Input(AntaTest.Input):  # pylint: disable=missing-class-docstring
        methods: List[AAAAuthMethod]
        """List of AAA accounting console methods. Methods should be in the right order"""
        types: Set[Literal["commands", "exec", "system", "dot1x"]]
        """List of accounting console types to verify"""

    @AntaTest.anta_test
    def test(self) -> None:
        command_output = self.instance_commands[0].json_output
        not_matching = []
        not_configured = []
        for k, v in command_output.items():
            acct_type = k.replace("AcctMethods", "")
            if acct_type not in self.inputs.types:
                # We do not need to verify this accounting type
                continue
            for methods in v.values():
                if "consoleAction" not in methods:
                    not_configured.append(acct_type)
                if methods["consoleMethods"] != self.inputs.methods:
                    not_matching.append(acct_type)
        if not_configured:
            self.result.is_failure(f"AAA console accounting is not configured for {not_configured}")
            return
        if not not_matching:
            self.result.is_success()
        else:
            self.result.is_failure(f"AAA accounting console methods {self.inputs.methods} are not matching for {not_matching}")
