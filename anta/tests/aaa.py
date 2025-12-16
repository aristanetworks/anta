# Copyright (c) 2023-2025 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Module related to the EOS various AAA tests."""

# Pyright does not understand AntaTest.Input typing
# pyright: reportAttributeAccessIssue=false
from __future__ import annotations

from ipaddress import IPv4Address
from typing import TYPE_CHECKING, ClassVar, Literal

from anta.custom_types import AAAAuthMethod
from anta.models import AntaCommand, AntaTest
from anta.tools import get_value

if TYPE_CHECKING:
    from anta.models import AntaTemplate


class VerifyTacacsSourceIntf(AntaTest):
    """Verifies TACACS source-interface for a specified VRF.

    Expected Results
    ----------------
    * Success: The test will pass if the provided TACACS source-interface is configured in the specified VRF.
    * Failure: The test will fail if the provided TACACS source-interface is NOT configured in the specified VRF.

    Examples
    --------
    ```yaml
    anta.tests.aaa:
      - VerifyTacacsSourceIntf:
          intf: Management0
          vrf: MGMT
    ```
    """

    categories: ClassVar[list[str]] = ["aaa"]
    commands: ClassVar[list[AntaCommand | AntaTemplate]] = [AntaCommand(command="show tacacs", revision=1)]

    class Input(AntaTest.Input):
        """Input model for the VerifyTacacsSourceIntf test."""

        intf: str
        """Source-interface to use as source IP of TACACS messages."""
        vrf: str = "default"
        """The name of the VRF to transport TACACS messages. Defaults to `default`."""

    @AntaTest.anta_test
    def test(self) -> None:
        """Main test function for VerifyTacacsSourceIntf."""
        command_output = self.instance_commands[0].json_output
        try:
            if (src_interface := command_output["srcIntf"][self.inputs.vrf]) == self.inputs.intf:
                self.result.is_success()
            else:
                self.result.is_failure(f"VRF: {self.inputs.vrf} - Source interface mismatch - Expected: {self.inputs.intf} Actual: {src_interface}")
        except KeyError:
            self.result.is_failure(f"VRF: {self.inputs.vrf} Source Interface: {self.inputs.intf} - Not configured")


class VerifyTacacsServers(AntaTest):
    """Verifies TACACS servers are configured for a specified VRF.

    Expected Results
    ----------------
    * Success: The test will pass if the provided TACACS servers are configured in the specified VRF.
    * Failure: The test will fail if the provided TACACS servers are NOT configured in the specified VRF.

    Examples
    --------
    ```yaml
    anta.tests.aaa:
      - VerifyTacacsServers:
          servers:
            - 10.10.10.21
            - 10.10.10.22
          vrf: MGMT
    ```
    """

    categories: ClassVar[list[str]] = ["aaa"]
    commands: ClassVar[list[AntaCommand | AntaTemplate]] = [AntaCommand(command="show tacacs", revision=1)]

    class Input(AntaTest.Input):
        """Input model for the VerifyTacacsServers test."""

        servers: list[IPv4Address]
        """List of TACACS servers."""
        vrf: str = "default"
        """The name of the VRF to transport TACACS messages. Defaults to `default`."""

    @AntaTest.anta_test
    def test(self) -> None:
        """Main test function for VerifyTacacsServers."""
        command_output = self.instance_commands[0].json_output
        tacacs_servers = command_output["tacacsServers"]
        if not tacacs_servers:
            self.result.is_failure("No TACACS servers are configured")
            return
        not_configured = [
            str(server)
            for server in self.inputs.servers
            if not any(
                str(server) == get_value(tacacs_server, "serverInfo.hostname") and self.inputs.vrf == get_value(tacacs_server, "serverInfo.vrf", default="default")
                for tacacs_server in tacacs_servers
            )
        ]
        if not not_configured:
            self.result.is_success()
        else:
            self.result.is_failure(f"TACACS servers {', '.join(not_configured)} are not configured in VRF {self.inputs.vrf}")


class VerifyTacacsServerGroups(AntaTest):
    """Verifies if the provided TACACS server group(s) are configured.

    Expected Results
    ----------------
    * Success: The test will pass if the provided TACACS server group(s) are configured.
    * Failure: The test will fail if one or all the provided TACACS server group(s) are NOT configured.

    Examples
    --------
    ```yaml
    anta.tests.aaa:
      - VerifyTacacsServerGroups:
          groups:
            - TACACS-GROUP1
            - TACACS-GROUP2
    ```
    """

    categories: ClassVar[list[str]] = ["aaa"]
    commands: ClassVar[list[AntaCommand | AntaTemplate]] = [AntaCommand(command="show tacacs", revision=1)]

    class Input(AntaTest.Input):
        """Input model for the VerifyTacacsServerGroups test."""

        groups: list[str]
        """List of TACACS server groups."""

    @AntaTest.anta_test
    def test(self) -> None:
        """Main test function for VerifyTacacsServerGroups."""
        command_output = self.instance_commands[0].json_output
        tacacs_groups = command_output["groups"]
        if not tacacs_groups:
            self.result.is_failure("No TACACS server group(s) are configured")
            return
        not_configured = [group for group in self.inputs.groups if group not in tacacs_groups]
        if not not_configured:
            self.result.is_success()
        else:
            self.result.is_failure(f"TACACS server group(s) {', '.join(not_configured)} are not configured")


class VerifyAuthenMethods(AntaTest):
    """Verifies the AAA authentication method lists for different authentication types (login, enable, dot1x).

    Expected Results
    ----------------
    * Success: The test will pass if the provided AAA authentication method list is matching in the configured authentication types.
    * Failure: The test will fail if the provided AAA authentication method list is NOT matching in the configured authentication types.

    Examples
    --------
    ```yaml
    anta.tests.aaa:
      - VerifyAuthenMethods:
          methods:
            - local
            - none
            - logging
          types:
            - login
            - enable
            - dot1x
    ```
    """

    categories: ClassVar[list[str]] = ["aaa"]
    commands: ClassVar[list[AntaCommand | AntaTemplate]] = [AntaCommand(command="show aaa methods authentication", revision=1)]

    class Input(AntaTest.Input):
        """Input model for the VerifyAuthenMethods test."""

        methods: list[AAAAuthMethod]
        """List of AAA authentication methods. Methods should be in the right order."""
        types: set[Literal["login", "enable", "dot1x"]]
        """List of authentication types to verify."""

    @AntaTest.anta_test
    def test(self) -> None:
        """Main test function for VerifyAuthenMethods."""
        command_output = self.instance_commands[0].json_output
        not_matching: list[str] = []
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
                    self.result.is_failure(f"AAA authentication methods {', '.join(self.inputs.methods)} are not matching for login console")
                    return
            not_matching.extend(auth_type for methods in v.values() if methods["methods"] != self.inputs.methods)

        if not not_matching:
            self.result.is_success()
        else:
            self.result.is_failure(f"AAA authentication methods {', '.join(self.inputs.methods)} are not matching for {', '.join(not_matching)}")


class VerifyAuthzMethods(AntaTest):
    """Verifies the AAA authorization method lists for different authorization types (commands, exec).

    Expected Results
    ----------------
    * Success: The test will pass if the provided AAA authorization method list is matching in the configured authorization types.
    * Failure: The test will fail if the provided AAA authorization method list is NOT matching in the configured authorization types.

    Examples
    --------
    ```yaml
    anta.tests.aaa:
      - VerifyAuthzMethods:
          methods:
            - local
            - none
            - logging
          types:
            - commands
            - exec
    ```
    """

    categories: ClassVar[list[str]] = ["aaa"]
    commands: ClassVar[list[AntaCommand | AntaTemplate]] = [AntaCommand(command="show aaa methods authorization", revision=1)]

    class Input(AntaTest.Input):
        """Input model for the VerifyAuthzMethods test."""

        methods: list[AAAAuthMethod]
        """List of AAA authorization methods. Methods should be in the right order."""
        types: set[Literal["commands", "exec"]]
        """List of authorization types to verify."""

    @AntaTest.anta_test
    def test(self) -> None:
        """Main test function for VerifyAuthzMethods."""
        command_output = self.instance_commands[0].json_output
        not_matching: list[str] = []
        for k, v in command_output.items():
            authz_type = k.replace("AuthzMethods", "")
            if authz_type not in self.inputs.types:
                # We do not need to verify this accounting type
                continue
            not_matching.extend(authz_type for methods in v.values() if methods["methods"] != self.inputs.methods)

        if not not_matching:
            self.result.is_success()
        else:
            self.result.is_failure(f"AAA authorization methods {', '.join(self.inputs.methods)} are not matching for {', '.join(not_matching)}")


class VerifyAcctDefaultMethods(AntaTest):
    """Verifies the AAA accounting default method lists for different accounting types (system, exec, commands, dot1x).

    Expected Results
    ----------------
    * Success: The test will pass if the provided AAA accounting default method list is matching in the configured accounting types.
    * Failure: The test will fail if the provided AAA accounting default method list is NOT matching in the configured accounting types.

    Examples
    --------
    ```yaml
    anta.tests.aaa:
      - VerifyAcctDefaultMethods:
          methods:
            - local
            - none
            - logging
          types:
            - system
            - exec
            - commands
            - dot1x
    ```
    """

    categories: ClassVar[list[str]] = ["aaa"]
    commands: ClassVar[list[AntaCommand | AntaTemplate]] = [AntaCommand(command="show aaa methods accounting", revision=1)]

    class Input(AntaTest.Input):
        """Input model for the VerifyAcctDefaultMethods test."""

        methods: list[AAAAuthMethod]
        """List of AAA accounting methods. Methods should be in the right order."""
        types: set[Literal["commands", "exec", "system", "dot1x"]]
        """List of accounting types to verify."""

    @AntaTest.anta_test
    def test(self) -> None:
        """Main test function for VerifyAcctDefaultMethods."""
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
            self.result.is_failure(f"AAA default accounting is not configured for {', '.join(not_configured)}")
            return
        if not not_matching:
            self.result.is_success()
        else:
            self.result.is_failure(f"AAA accounting default methods {', '.join(self.inputs.methods)} are not matching for {', '.join(not_matching)}")


class VerifyAcctConsoleMethods(AntaTest):
    """Verifies the AAA accounting console method lists for different accounting types (system, exec, commands, dot1x).

    Expected Results
    ----------------
    * Success: The test will pass if the provided AAA accounting console method list is matching in the configured accounting types.
    * Failure: The test will fail if the provided AAA accounting console method list is NOT matching in the configured accounting types.

    Examples
    --------
    ```yaml
    anta.tests.aaa:
      - VerifyAcctConsoleMethods:
          methods:
            - local
            - none
            - logging
          types:
            - system
            - exec
            - commands
            - dot1x
    ```
    """

    categories: ClassVar[list[str]] = ["aaa"]
    commands: ClassVar[list[AntaCommand | AntaTemplate]] = [AntaCommand(command="show aaa methods accounting", revision=1)]

    class Input(AntaTest.Input):
        """Input model for the VerifyAcctConsoleMethods test."""

        methods: list[AAAAuthMethod]
        """List of AAA accounting console methods. Methods should be in the right order."""
        types: set[Literal["commands", "exec", "system", "dot1x"]]
        """List of accounting console types to verify."""

    @AntaTest.anta_test
    def test(self) -> None:
        """Main test function for VerifyAcctConsoleMethods."""
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
            self.result.is_failure(f"AAA console accounting is not configured for {', '.join(not_configured)}")
            return
        if not not_matching:
            self.result.is_success()
        else:
            self.result.is_failure(f"AAA accounting console methods {', '.join(self.inputs.methods)} are not matching for {', '.join(not_matching)}")
