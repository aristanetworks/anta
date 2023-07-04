"""
Test functions related to Multi-chassis Link Aggregation (MLAG)
"""
import logging
from typing import Any, Dict, Optional, cast

from anta.models import AntaTest, AntaTestCommand
from anta.tools.get_value import get_value

logger = logging.getLogger(__name__)


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
    commands = [AntaTestCommand(command="show mlag", ofmt="json")]

    @AntaTest.anta_test
    def test(self) -> None:
        """
        Run VerifyMlagStatus validation
        """

        command_output = cast(Dict[str, Dict[str, Any]], self.instance_commands[0].output)

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
    commands = [AntaTestCommand(command="show mlag", ofmt="json")]

    @AntaTest.anta_test
    def test(self) -> None:
        """
        Run VerifyMlagInterfaces validation
        """

        command_output = cast(Dict[str, Dict[str, Any]], self.instance_commands[0].output)

        if command_output["state"] == "disabled":
            self.result.is_skipped("MLAG is disabled")
            return

        if command_output["mlagPorts"]["Inactive"] != 0 or command_output["mlagPorts"]["Active-partial"] != 0:
            self.result.is_failure(f"MLAG status is not OK: {command_output['mlagPorts']}")
        else:
            self.result.is_success()


class VerifyMlagConfigSanity(AntaTest):
    """
    This test verifies there are no MLAG config-sanity inconsistencies.

    Expected Results:
        * success: The test will pass if there are NO MLAG config-sanity inconsistencies.
        * failure: The test will fail if there are MLAG config-sanity inconsistencies.
        * skipped: The test will be skipped if MLAG is 'disabled'.
    """

    name = "VerifyMlagConfigSanity"
    description = "This test verifies there are no MLAG config-sanity inconsistencies."
    categories = ["mlag"]
    commands = [AntaTestCommand(command="show mlag config-sanity", ofmt="json")]

    @AntaTest.anta_test
    def test(self) -> None:
        """
        Run VerifyMlagConfigSanity validation
        """

        command_output = cast(Dict[str, Dict[str, Any]], self.instance_commands[0].output)

        if command_output["mlagActive"] is False:
            self.result.is_skipped("MLAG is disabled")
            return

        if len(command_output["globalConfiguration"]) > 0 or len(command_output["interfaceConfiguration"]) > 0:
            self.result.is_failure()
            if len(command_output["globalConfiguration"]) > 0:
                self.result.is_failure(f"MLAG config-sanity returned Global inconsistancies: {command_output['globalConfiguration']}")
            if len(command_output["interfaceConfiguration"]) > 0:
                self.result.is_failure(f"MLAG config-sanity returned Interface inconsistancies: {command_output['interfaceConfiguration']}")
        else:
            self.result.is_success()


class VerifyMlagReloadDelay(AntaTest):
    """
    This test verifies the reload-delay parameters of the MLAG configuration.

    Expected Results:
        * success: The test will pass if the reload-delay parameters are configured properly.
        * failure: The test will fail if the reload-delay parameters are NOT configured properly.
        * skipped: The test will be skipped if the reload-delay parameters are NOT provided or if MLAG is 'disabled'.
    """

    name = "VerifyMlagReloadDelay"
    description = "This test verifies the reload-delay parameters of the MLAG configuration."
    categories = ["mlag"]
    commands = [AntaTestCommand(command="show mlag", ofmt="json")]

    @AntaTest.anta_test
    def test(self, reload_delay: Optional[int] = None, reload_delay_non_mlag: Optional[int] = None) -> None:
        """
        Run VerifyMlagReloadDelay validation

        Args:
            reload_delay: Delay (seconds) after reboot until non peer-link ports that are part of an MLAG are enabled.
            reload_delay_non_mlag: Delay (seconds) after reboot until ports that are not part of an MLAG are enabled.
        """

        if not reload_delay or not reload_delay_non_mlag:
            self.result.is_skipped(f"{self.__class__.name} did not run because reload_delay or reload_delay_non_mlag were not supplied")
            return

        command_output = cast(Dict[str, Dict[str, Any]], self.instance_commands[0].output)

        if command_output["state"] == "disabled":
            self.result.is_skipped("MLAG is disabled")
            return

        keys_to_verify = ["reloadDelay", "reloadDelayNonMlag"]
        verified_output = {key: get_value(command_output, key) for key in keys_to_verify}

        if verified_output["reloadDelay"] == reload_delay and verified_output["reloadDelayNonMlag"] == reload_delay_non_mlag:
            self.result.is_success()

        else:
            self.result.is_failure(f"The reload-delay parameters are not configured properly: {verified_output}")


class VerifyMlagDualPrimary(AntaTest):
    """
    This test verifies the dual-primary detection and its parameters of the MLAG configuration.

    Expected Results:
        * success: The test will pass if the dual-primary detection is enabled and its parameters are configured properly.
        * failure: The test will fail if the dual-primary detection is NOT enabled or its parameters are NOT configured properly.
        * skipped: The test will be skipped if the dual-primary parameters are NOT provided or if MLAG is 'disabled'.
    """

    name = "VerifyMlagDualPrimary"
    description = "This test verifies the dual-primary detection and its parameters of the MLAG configuration."
    categories = ["mlag"]
    commands = [AntaTestCommand(command="show mlag detail", ofmt="json")]

    @AntaTest.anta_test
    def test(
        self, detection_delay: Optional[int] = None, errdisabled: bool = False, recovery_delay: Optional[int] = None, recovery_delay_non_mlag: Optional[int] = None
    ) -> None:
        """
        Run VerifyMlagDualPrimary validation

        Args:
            detection_delay: Delay detection for <N> seconds.
            errdisabled: Errdisabled all interfaces when dual-primary is detected. Defaults to False.
            recovery_delay: Delay (seconds) after dual-primary detection resolves until non peer-link ports that are part of an MLAG are enabled.
            recovery_delay_non_mlag: Delay (seconds) after dual-primary detection resolves until ports that are not part of an MLAG are enabled.
        """

        if detection_delay is None or errdisabled is None or recovery_delay is None or recovery_delay_non_mlag is None:
            self.result.is_skipped(
                f"{self.__class__.name} did not run because detection_delay, errdisabled, recovery_delay or recovery_delay_non_mlag were not supplied"
            )
            return

        if errdisabled:
            action = "errdisableAllInterfaces"
        else:
            action = "none"

        command_output = cast(Dict[str, Dict[str, Any]], self.instance_commands[0].output)

        if command_output["state"] == "disabled":
            self.result.is_skipped("MLAG is disabled")
            return

        if command_output["dualPrimaryDetectionState"] == "disabled":
            self.result.is_failure("Dual-primary detection is disabled")
            return

        keys_to_verify = ["detail.dualPrimaryDetectionDelay", "detail.dualPrimaryAction", "dualPrimaryMlagRecoveryDelay", "dualPrimaryNonMlagRecoveryDelay"]
        verified_output = {key: get_value(command_output, key) for key in keys_to_verify}

        if (
            verified_output["detail.dualPrimaryDetectionDelay"] == detection_delay
            and verified_output["detail.dualPrimaryAction"] == action
            and verified_output["dualPrimaryMlagRecoveryDelay"] == recovery_delay
            and verified_output["dualPrimaryNonMlagRecoveryDelay"] == recovery_delay_non_mlag
        ):
            self.result.is_success()

        else:
            self.result.is_failure(f"The dual-primary parameters are not configured properly: {verified_output}")
