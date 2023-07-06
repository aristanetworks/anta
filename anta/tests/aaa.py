"""
Test functions related to the EOS various AAA settings
"""
from __future__ import annotations

from typing import List, Optional

from anta.models import AntaCommand, AntaTest


def _check_group_methods(methods: List[str]) -> List[str]:
    """
    Verifies if the provided methods in various AAA tests start with 'group'.

    Args:
        methods: List of AAA methods. Methods should be in the right order.
    """
    built_in_methods = ["local", "none", "logging"]

    return [f"group {method}" if method not in built_in_methods and not method.startswith("group ") else method for method in methods]


def _check_auth_type(auth_types: List[str], valid_auth_types: List[str]) -> None:
    """
    Verifies if the provided auth types in various AAA tests are valid.

    Args:
        auth_types: List of AAA auth types to validate.
        valid_auth_types: List of valid AAA auth types to validate against.
    """
    if len(auth_types) > len(valid_auth_types):
        raise ValueError(f"Too many parameters provided in auth_types. Valid parameters are: {valid_auth_types}")

    for auth_type in auth_types:
        if auth_type not in valid_auth_types:
            raise ValueError(f"Wrong parameter provided in auth_types. Valid parameters are: {valid_auth_types}")


class VerifyTacacsSourceIntf(AntaTest):
    """
    Verifies TACACS source-interface for a specified VRF.

    Expected Results:
        * success: The test will pass if the provided TACACS source-interface is configured in the specified VRF.
        * failure: The test will fail if the provided TACACS source-interface is NOT configured in the specified VRF.
        * skipped: The test will be skipped if source-interface or VRF is not provided.
    """

    name = "VerifyTacacsSourceIntf"
    description = "Verifies TACACS source-interface for a specified VRF."
    categories = ["aaa"]
    commands = [AntaCommand(command="show tacacs")]

    @AntaTest.anta_test
    def test(self, intf: Optional[str] = None, vrf: str = "default") -> None:
        """
        Run VerifyTacacsSourceIntf validation.

        Args:
            intf: Source-interface to use as source IP of TACACS messages.
            vrf: The name of the VRF to transport TACACS messages. Defaults to 'default'.
        """
        if not intf or not vrf:
            self.result.is_skipped(f"{self.__class__.name} did not run because intf or vrf was not supplied")
            return

        command_output = self.instance_commands[0].json_output

        try:
            if command_output["srcIntf"][vrf] == intf:
                self.result.is_success()
            else:
                self.result.is_failure(f"Wrong source-interface configured in VRF {vrf}")

        except KeyError:
            self.result.is_failure(f"Source-interface {intf} is not configured in VRF {vrf}")


class VerifyTacacsServers(AntaTest):
    """
    Verifies TACACS servers are configured for a specified VRF.

    Expected Results:
        * success: The test will pass if the provided TACACS servers are configured in the specified VRF.
        * failure: The test will fail if the provided TACACS servers are NOT configured in the specified VRF.
        * skipped: The test will be skipped if TACACS servers or VRF are not provided.
    """

    name = "VerifyTacacsServers"
    description = "Verifies TACACS servers are configured for a specified VRF."
    categories = ["aaa"]
    commands = [AntaCommand(command="show tacacs")]

    @AntaTest.anta_test
    def test(self, servers: Optional[List[str]] = None, vrf: str = "default") -> None:
        """
        Run VerifyTacacsServers validation.

        Args:
            servers: List of TACACS servers IP addresses.
            vrf: The name of the VRF to transport TACACS messages. Defaults to 'default'.
        """
        if not servers or not vrf:
            self.result.is_skipped(f"{self.__class__.name} did not run because servers or vrf were not supplied")
            return

        command_output = self.instance_commands[0].json_output

        tacacs_servers = command_output["tacacsServers"]

        if not tacacs_servers:
            self.result.is_failure("No TACACS servers are configured")
            return

        not_configured = [
            server
            for server in servers
            if not any(server == tacacs_server["serverInfo"]["hostname"] and vrf == tacacs_server["serverInfo"]["vrf"] for tacacs_server in tacacs_servers)
        ]

        if not not_configured:
            self.result.is_success()
        else:
            self.result.is_failure(f"TACACS servers {not_configured} are not configured in VRF {vrf}")


class VerifyTacacsServerGroups(AntaTest):
    """
    Verifies if the provided TACACS server group(s) are configured.

    Expected Results:
        * success: The test will pass if the provided TACACS server group(s) are configured.
        * failure: The test will fail if one or all the provided TACACS server group(s) are NOT configured.
        * skipped: The test will be skipped if TACACS server group(s) are not provided.
    """

    name = "VerifyTacacsServerGroups"
    description = "Verifies if the provided TACACS server group(s) are configured."
    categories = ["aaa"]
    commands = [AntaCommand(command="show tacacs")]

    @AntaTest.anta_test
    def test(self, groups: Optional[List[str]] = None) -> None:
        """
        Run VerifyTacacsServerGroups validation.

        Args:
            groups: List of TACACS server group.
        """
        if not groups:
            self.result.is_skipped(f"{self.__class__.name} did not run because groups were not supplied")
            return

        command_output = self.instance_commands[0].json_output

        tacacs_groups = command_output["groups"]

        if not tacacs_groups:
            self.result.is_failure("No TACACS server group(s) are configured")
            return

        not_configured = [group for group in groups if group not in tacacs_groups]

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
        * skipped: The test will be skipped if the AAA authentication method list or authentication type list are not provided.
    """

    name = "VerifyAuthenMethods"
    description = "Verifies the AAA authentication method lists for different authentication types (login, enable, dot1x)."
    categories = ["aaa"]
    commands = [AntaCommand(command="show aaa methods authentication")]

    @AntaTest.anta_test
    def test(self, methods: Optional[List[str]] = None, auth_types: Optional[List[str]] = None) -> None:
        """
        Run VerifyAuthenMethods validation.

        Args:
            methods: List of AAA authentication methods. Methods should be in the right order.
            auth_types: List of authentication types to verify. List elements must be: login, enable, dot1x.
        """
        if not methods or not auth_types:
            self.result.is_skipped(f"{self.__class__.name} did not run because methods or auth_types were not supplied")
            return

        methods_with_group = _check_group_methods(methods)

        _check_auth_type(auth_types, ["login", "enable", "dot1x"])

        command_output = self.instance_commands[0].json_output

        not_matching = []

        for auth_type in auth_types:
            auth_type_key = f"{auth_type}AuthenMethods"

            if auth_type_key == "loginAuthenMethods":
                if not command_output[auth_type_key].get("login"):
                    self.result.is_failure("AAA authentication methods are not configured for login console")
                    return

                if command_output[auth_type_key]["login"]["methods"] != methods_with_group:
                    self.result.is_failure(f"AAA authentication methods {methods} are not matching for login console")
                    return

            if command_output[auth_type_key]["default"]["methods"] != methods_with_group:
                not_matching.append(auth_type)

        if not not_matching:
            self.result.is_success()
        else:
            self.result.is_failure(f"AAA authentication methods {methods} are not matching for {not_matching}")


class VerifyAuthzMethods(AntaTest):
    """
    Verifies the AAA authorization method lists for different authorization types (commands, exec).

    Expected Results:
        * success: The test will pass if the provided AAA authorization method list is matching in the configured authorization types.
        * failure: The test will fail if the provided AAA authorization method list is NOT matching in the configured authorization types.
        * skipped: The test will be skipped if the AAA authentication method list or authorization type list are not provided.
    """

    name = "VerifyAuthzMethods"
    description = "Verifies the AAA authorization method lists for different authorization types (commands, exec)."
    categories = ["aaa"]
    commands = [AntaCommand(command="show aaa methods authorization")]

    @AntaTest.anta_test
    def test(self, methods: Optional[List[str]] = None, auth_types: Optional[List[str]] = None) -> None:
        """
        Run VerifyAuthzMethods validation.

        Args:
            methods: List of AAA authorization methods. Methods should be in the right order.
            auth_types: List of authorization types to verify. List elements must be: commands, exec.
        """
        if not methods or not auth_types:
            self.result.is_skipped(f"{self.__class__.name} did not run because methods or auth_types were not supplied")
            return

        _check_auth_type(auth_types, ["commands", "exec"])

        methods_with_group = _check_group_methods(methods)

        command_output = self.instance_commands[0].json_output

        not_matching = []

        for auth_type in auth_types:
            auth_type_key = f"{auth_type}AuthzMethods"

            method_key = list(command_output[auth_type_key].keys())[0]

            if command_output[auth_type_key][method_key]["methods"] != methods_with_group:
                not_matching.append(auth_type)

        if not not_matching:
            self.result.is_success()
        else:
            self.result.is_failure(f"AAA authorization methods {methods} are not matching for {not_matching}")


class VerifyAcctDefaultMethods(AntaTest):
    """
    Verifies the AAA accounting default method lists for different accounting types (system, exec, commands, dot1x).

    Expected Results:
        * success: The test will pass if the provided AAA accounting default method list is matching in the configured accounting types.
        * failure: The test will fail if the provided AAA accounting default method list is NOT matching in the configured accounting types.
        * skipped: The test will be skipped if the AAA accounting default method list or accounting type list are not provided.
    """

    name = "VerifyAcctDefaultMethods"
    description = "Verifies the AAA accounting default method lists for different accounting types (system, exec, commands, dot1x)."
    categories = ["aaa"]
    commands = [AntaCommand(command="show aaa methods accounting")]

    @AntaTest.anta_test
    def test(self, methods: Optional[List[str]] = None, auth_types: Optional[List[str]] = None) -> None:
        """
        Run VerifyAcctDefaultMethods validation.

        Args:
            methods: List of AAA accounting default methods. Methods should be in the right order.
            auth_types: List of accounting types to verify. List elements must be: commands, exec, system, dot1x.
        """
        if not methods or not auth_types:
            self.result.is_skipped(f"{self.__class__.name} did not run because methods or auth_types were not supplied")
            return

        methods_with_group = _check_group_methods(methods)

        _check_auth_type(auth_types, ["system", "exec", "commands", "dot1x"])

        command_output = self.instance_commands[0].json_output

        not_matching = []
        not_configured = []

        for auth_type in auth_types:
            auth_type_key = f"{auth_type}AcctMethods"

            method_key = list(command_output[auth_type_key].keys())[0]

            if not command_output[auth_type_key][method_key].get("defaultAction"):
                not_configured.append(auth_type)

            if command_output[auth_type_key][method_key]["defaultMethods"] != methods_with_group:
                not_matching.append(auth_type)

        if not_configured:
            self.result.is_failure(f"AAA default accounting is not configured for {not_configured}")
            return

        if not not_matching:
            self.result.is_success()
        else:
            self.result.is_failure(f"AAA accounting default methods {methods} are not matching for {not_matching}")


class VerifyAcctConsoleMethods(AntaTest):
    """
    Verifies the AAA accounting console method lists for different accounting types (system, exec, commands, dot1x).

    Expected Results:
        * success: The test will pass if the provided AAA accounting console method list is matching in the configured accounting types.
        * failure: The test will fail if the provided AAA accounting console method list is NOT matching in the configured accounting types.
        * skipped: The test will be skipped if the AAA accounting console method list or accounting type list are not provided.
    """

    name = "VerifyAcctConsoleMethods"
    description = "Verifies the AAA accounting console method lists for different accounting types (system, exec, commands, dot1x)."
    categories = ["aaa"]
    commands = [AntaCommand(command="show aaa methods accounting")]

    @AntaTest.anta_test
    def test(self, methods: Optional[List[str]] = None, auth_types: Optional[List[str]] = None) -> None:
        """
        Run VerifyAcctConsoleMethods validation.

        Args:
            methods: List of AAA accounting console methods. Methods should be in the right order.
            auth_types: List of accounting types to verify. List elements must be: commands, exec, system, dot1x.
        """
        if not methods or not auth_types:
            self.result.is_skipped(f"{self.__class__.name} did not run because methods or auth_types were not supplied")
            return

        methods_with_group = _check_group_methods(methods)

        _check_auth_type(auth_types, ["system", "exec", "commands", "dot1x"])

        command_output = self.instance_commands[0].json_output

        not_matching = []
        not_configured = []

        for auth_type in auth_types:
            auth_type_key = f"{auth_type}AcctMethods"

            method_key = list(command_output[auth_type_key].keys())[0]

            if not command_output[auth_type_key][method_key].get("consoleAction"):
                not_configured.append(auth_type)

            if command_output[auth_type_key][method_key]["consoleMethods"] != methods_with_group:
                not_matching.append(auth_type)

        if not_configured:
            self.result.is_failure(f"AAA console accounting is not configured for {not_configured}")
            return

        if not not_matching:
            self.result.is_success()
        else:
            self.result.is_failure(f"AAA accounting console methods {methods} are not matching for {not_matching}")
