# Copyright (c) 2023 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""
Test functions related to Multi-chassis Link Aggregation (MLAG)
"""
# Mypy does not understand AntaTest.Input typing
# mypy: disable-error-code=attr-defined
from __future__ import annotations

from pydantic import conint

from anta.models import AntaCommand, AntaTest
from anta.tools.get_value import get_value


class VerifyMlagStatus(AntaTest):
    """
    This test verifies the health status of the MLAG configuration.

    Expected Results:
        * success: The test will pass if the MLAG state is 'active', negotiation status is 'connected',
                   peer-link status and local interface status are 'up'.
        * failure: The test will fail if the MLAG state is not 'active', negotiation status is not 'connected',
                   peer-link status or local interface status are not 'up'.
        * skipped: The test will be skipped if MLAG is 'disabled'.
    """

    name = "VerifyMlagStatus"
    description = "This test verifies the health status of the MLAG configuration."
    categories = ["mlag"]
    commands = [AntaCommand(command="show mlag", ofmt="json")]

    @AntaTest.anta_test
    def test(self) -> None:
        command_output = self.instance_commands[0].json_output
        if command_output["state"] == "disabled":
            self.result.is_skipped("MLAG is disabled")
            return
        keys_to_verify = ["state", "negStatus", "localIntfStatus", "peerLinkStatus"]
        verified_output = {key: get_value(command_output, key) for key in keys_to_verify}
        if (
            verified_output["state"] == "active"
            and verified_output["negStatus"] == "connected"
            and verified_output["localIntfStatus"] == "up"
            and verified_output["peerLinkStatus"] == "up"
        ):
            self.result.is_success()
        else:
            self.result.is_failure(f"MLAG status is not OK: {verified_output}")


class VerifyMlagInterfaces(AntaTest):
    """
    This test verifies there are no inactive or active-partial MLAG ports.

    Expected Results:
        * success: The test will pass if there are NO inactive or active-partial MLAG ports.
        * failure: The test will fail if there are inactive or active-partial MLAG ports.
        * skipped: The test will be skipped if MLAG is 'disabled'.
    """

    name = "VerifyMlagInterfaces"
    description = "This test verifies there are no inactive or active-partial MLAG ports."
    categories = ["mlag"]
    commands = [AntaCommand(command="show mlag", ofmt="json")]

    @AntaTest.anta_test
    def test(self) -> None:
        command_output = self.instance_commands[0].json_output
        if command_output["state"] == "disabled":
            self.result.is_skipped("MLAG is disabled")
            return
        if command_output["mlagPorts"]["Inactive"] == 0 and command_output["mlagPorts"]["Active-partial"] == 0:
            self.result.is_success()
        else:
            self.result.is_failure(f"MLAG status is not OK: {command_output['mlagPorts']}")


class VerifyMlagConfigSanity(AntaTest):
    """
    This test verifies there are no MLAG config-sanity inconsistencies.

    Expected Results:
        * success: The test will pass if there are NO MLAG config-sanity inconsistencies.
        * failure: The test will fail if there are MLAG config-sanity inconsistencies.
        * skipped: The test will be skipped if MLAG is 'disabled'.
        * error: The test will give an error if 'mlagActive' is not found in the JSON response.
    """

    name = "VerifyMlagConfigSanity"
    description = "This test verifies there are no MLAG config-sanity inconsistencies."
    categories = ["mlag"]
    commands = [AntaCommand(command="show mlag config-sanity", ofmt="json")]

    @AntaTest.anta_test
    def test(self) -> None:
        command_output = self.instance_commands[0].json_output
        if (mlag_status := get_value(command_output, "mlagActive")) is None:
            self.result.is_error(message="Incorrect JSON response - 'mlagActive' state was not found")
            return
        if mlag_status is False:
            self.result.is_skipped("MLAG is disabled")
            return
        keys_to_verify = ["globalConfiguration", "interfaceConfiguration"]
        verified_output = {key: get_value(command_output, key) for key in keys_to_verify}
        if not any(verified_output.values()):
            self.result.is_success()
        else:
            self.result.is_failure(f"MLAG config-sanity returned inconsistencies: {verified_output}")


class VerifyMlagReloadDelay(AntaTest):
    """
    This test verifies the reload-delay parameters of the MLAG configuration.

    Expected Results:
        * success: The test will pass if the reload-delay parameters are configured properly.
        * failure: The test will fail if the reload-delay parameters are NOT configured properly.
        * skipped: The test will be skipped if MLAG is 'disabled'.
    """

    name = "VerifyMlagReloadDelay"
    description = "This test verifies the reload-delay parameters of the MLAG configuration."
    categories = ["mlag"]
    commands = [AntaCommand(command="show mlag", ofmt="json")]

    class Input(AntaTest.Input):  # pylint: disable=missing-class-docstring
        reload_delay: conint(ge=0)  # type: ignore
        """Delay (seconds) after reboot until non peer-link ports that are part of an MLAG are enabled"""
        reload_delay_non_mlag: conint(ge=0)  # type: ignore
        """Delay (seconds) after reboot until ports that are not part of an MLAG are enabled"""

    @AntaTest.anta_test
    def test(self) -> None:
        command_output = self.instance_commands[0].json_output
        if command_output["state"] == "disabled":
            self.result.is_skipped("MLAG is disabled")
            return
        keys_to_verify = ["reloadDelay", "reloadDelayNonMlag"]
        verified_output = {key: get_value(command_output, key) for key in keys_to_verify}
        if verified_output["reloadDelay"] == self.inputs.reload_delay and verified_output["reloadDelayNonMlag"] == self.inputs.reload_delay_non_mlag:
            self.result.is_success()

        else:
            self.result.is_failure(f"The reload-delay parameters are not configured properly: {verified_output}")


class VerifyMlagDualPrimary(AntaTest):
    """
    This test verifies the dual-primary detection and its parameters of the MLAG configuration.

    Expected Results:
        * success: The test will pass if the dual-primary detection is enabled and its parameters are configured properly.
        * failure: The test will fail if the dual-primary detection is NOT enabled or its parameters are NOT configured properly.
        * skipped: The test will be skipped if MLAG is 'disabled'.
    """

    name = "VerifyMlagDualPrimary"
    description = "This test verifies the dual-primary detection and its parameters of the MLAG configuration."
    categories = ["mlag"]
    commands = [AntaCommand(command="show mlag detail", ofmt="json")]

    class Input(AntaTest.Input):  # pylint: disable=missing-class-docstring
        detection_delay: conint(ge=0)  # type: ignore
        """Delay detection (seconds)"""
        errdisabled: bool = False
        """Errdisabled all interfaces when dual-primary is detected"""
        recovery_delay: conint(ge=0)  # type: ignore
        """Delay (seconds) after dual-primary detection resolves until non peer-link ports that are part of an MLAG are enabled"""
        recovery_delay_non_mlag: conint(ge=0)  # type: ignore
        """Delay (seconds) after dual-primary detection resolves until ports that are not part of an MLAG are enabled"""

    @AntaTest.anta_test
    def test(self) -> None:
        errdisabled_action = "errdisableAllInterfaces" if self.inputs.errdisabled else "none"
        command_output = self.instance_commands[0].json_output
        if command_output["state"] == "disabled":
            self.result.is_skipped("MLAG is disabled")
            return
        if command_output["dualPrimaryDetectionState"] == "disabled":
            self.result.is_failure("Dual-primary detection is disabled")
            return
        keys_to_verify = ["detail.dualPrimaryDetectionDelay", "detail.dualPrimaryAction", "dualPrimaryMlagRecoveryDelay", "dualPrimaryNonMlagRecoveryDelay"]
        verified_output = {key: get_value(command_output, key) for key in keys_to_verify}
        if (
            verified_output["detail.dualPrimaryDetectionDelay"] == self.inputs.detection_delay
            and verified_output["detail.dualPrimaryAction"] == errdisabled_action
            and verified_output["dualPrimaryMlagRecoveryDelay"] == self.inputs.recovery_delay
            and verified_output["dualPrimaryNonMlagRecoveryDelay"] == self.inputs.recovery_delay_non_mlag
        ):
            self.result.is_success()
        else:
            self.result.is_failure(f"The dual-primary parameters are not configured properly: {verified_output}")
