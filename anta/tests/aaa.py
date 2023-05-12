"""
Test functions related to the EOS various AAA settings
"""
from __future__ import annotations

import logging
from typing import Any, Dict, Optional, cast

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
    # TODO Replace with AntaTestTemplate
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
