"""
Test functions related to the EOS various AAA settings
"""
from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional, cast

from anta.models import AntaTest, AntaTestCommand

logger = logging.getLogger(__name__)


class VerifyTacacsAuth(AntaTest):
    """
    Verifies if TACACS authentication is successful for a specified user.

    Expected Results:
        * success: The test will pass if the TACACS authentication is successful.
        * failure: The test will fail if the TACACS authentication failed.

    Test should be used with a dummy username configured in TACACS.
    """

    name = "VerifyTacacsAuth"
    description = "Verifies if TACACS authentication is successful for a specified user."
    categories = ["aaa"]
    # TODO: Replace with AntaTestTemplate
    # NOTE: Need to test with json
    commands = [AntaTestCommand(command="test aaa group tacacs+ dummyuser dummypass", ofmt="text")]

    @AntaTest.anta_test
    def test(self) -> None:
        """
        Run VerifyTacacsAuth validation.
        """

        self.logger.debug(f"self.instance_commands is: {self.instance_commands}")
        command_output = cast(str, self.instance_commands[0].output)
        self.logger.debug(f"dataset is: {command_output}")

        if command_output == "User was successfully authenticated.\n":
            self.result.is_success()

        else:
            self.result.is_failure("Authentication failed")


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
    commands = [AntaTestCommand(command="show tacacs")]

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

        self.logger.debug(f"self.instance_commands is: {self.instance_commands}")
        command_output = cast(Dict[str, Any], self.instance_commands[0].output)
        self.logger.debug(f"dataset is: {command_output}")

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
    commands = [AntaTestCommand(command="show tacacs")]

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

        self.logger.debug(f"self.instance_commands is: {self.instance_commands}")
        command_output = cast(Dict[str, Any], self.instance_commands[0].output)
        self.logger.debug(f"dataset is: {command_output}")

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
    commands = [AntaTestCommand(command="show tacacs")]

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

        self.logger.debug(f"self.instance_commands is: {self.instance_commands}")
        command_output = cast(Dict[str, Any], self.instance_commands[0].output)
        self.logger.debug(f"dataset is: {command_output}")

        tacacs_groups = command_output["groups"]

        if not tacacs_groups:
            self.result.is_failure("No TACACS server group(s) are configured")
            return

        not_configured = [group for group in groups if group not in tacacs_groups]

        if not not_configured:
            self.result.is_success()
        else:
            self.result.is_failure(f"TACACS server group(s) {not_configured} are not configured")
