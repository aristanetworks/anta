# Copyright (c) 2023-2025 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Module related to Multi-chassis Link Aggregation (MLAG) tests."""

# Mypy does not understand AntaTest.Input typing
# mypy: disable-error-code=attr-defined
from __future__ import annotations

from typing import TYPE_CHECKING, ClassVar

from anta.custom_types import MlagPriority, PositiveInteger
from anta.models import AntaCommand, AntaTest
from anta.tools import get_value

if TYPE_CHECKING:
    from anta.models import AntaTemplate


class VerifyMlagStatus(AntaTest):
    """Verifies the health status of the MLAG configuration.

    Expected Results
    ----------------
    * Success: The test will pass if the MLAG state is 'active', negotiation status is 'connected',
                   peer-link status and local interface status are 'up'.
    * Failure: The test will fail if the MLAG state is not 'active', negotiation status is not 'connected',
                   peer-link status or local interface status are not 'up'.
    * Skipped: The test will be skipped if MLAG is 'disabled'.

    Examples
    --------
    ```yaml
    anta.tests.mlag:
      - VerifyMlagStatus:
    ```
    """

    categories: ClassVar[list[str]] = ["mlag"]
    commands: ClassVar[list[AntaCommand | AntaTemplate]] = [AntaCommand(command="show mlag", revision=2)]

    @AntaTest.anta_test
    def test(self) -> None:
        """Main test function for VerifyMlagStatus."""
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
    """Verifies there are no inactive or active-partial MLAG ports.

    Expected Results
    ----------------
    * Success: The test will pass if there are NO inactive or active-partial MLAG ports.
    * Failure: The test will fail if there are inactive or active-partial MLAG ports.
    * Skipped: The test will be skipped if MLAG is 'disabled'.

    Examples
    --------
    ```yaml
    anta.tests.mlag:
      - VerifyMlagInterfaces:
    ```
    """

    categories: ClassVar[list[str]] = ["mlag"]
    commands: ClassVar[list[AntaCommand | AntaTemplate]] = [AntaCommand(command="show mlag", revision=2)]

    @AntaTest.anta_test
    def test(self) -> None:
        """Main test function for VerifyMlagInterfaces."""
        command_output = self.instance_commands[0].json_output
        if command_output["state"] == "disabled":
            self.result.is_skipped("MLAG is disabled")
            return
        if command_output["mlagPorts"]["Inactive"] == 0 and command_output["mlagPorts"]["Active-partial"] == 0:
            self.result.is_success()
        else:
            self.result.is_failure(f"MLAG status is not OK: {command_output['mlagPorts']}")


class VerifyMlagConfigSanity(AntaTest):
    """Verifies there are no MLAG config-sanity inconsistencies.

    Expected Results
    ----------------
    * Success: The test will pass if there are NO MLAG config-sanity inconsistencies.
    * Failure: The test will fail if there are MLAG config-sanity inconsistencies.
    * Skipped: The test will be skipped if MLAG is 'disabled'.
    * Error: The test will give an error if 'mlagActive' is not found in the JSON response.

    Examples
    --------
    ```yaml
    anta.tests.mlag:
      - VerifyMlagConfigSanity:
    ```
    """

    categories: ClassVar[list[str]] = ["mlag"]
    commands: ClassVar[list[AntaCommand | AntaTemplate]] = [AntaCommand(command="show mlag config-sanity", revision=1)]

    @AntaTest.anta_test
    def test(self) -> None:
        """Main test function for VerifyMlagConfigSanity."""
        command_output = self.instance_commands[0].json_output
        if command_output["mlagActive"] is False:
            self.result.is_skipped("MLAG is disabled")
            return
        keys_to_verify = ["globalConfiguration", "interfaceConfiguration"]
        verified_output = {key: get_value(command_output, key) for key in keys_to_verify}
        if not any(verified_output.values()):
            self.result.is_success()
        else:
            self.result.is_failure(f"MLAG config-sanity returned inconsistencies: {verified_output}")


class VerifyMlagReloadDelay(AntaTest):
    """Verifies the reload-delay parameters of the MLAG configuration.

    Expected Results
    ----------------
    * Success: The test will pass if the reload-delay parameters are configured properly.
    * Failure: The test will fail if the reload-delay parameters are NOT configured properly.
    * Skipped: The test will be skipped if MLAG is 'disabled'.

    Examples
    --------
    ```yaml
    anta.tests.mlag:
      - VerifyMlagReloadDelay:
          reload_delay: 300
          reload_delay_non_mlag: 330
    ```
    """

    categories: ClassVar[list[str]] = ["mlag"]
    commands: ClassVar[list[AntaCommand | AntaTemplate]] = [AntaCommand(command="show mlag", revision=2)]

    class Input(AntaTest.Input):
        """Input model for the VerifyMlagReloadDelay test."""

        reload_delay: PositiveInteger
        """Delay (seconds) after reboot until non peer-link ports that are part of an MLAG are enabled."""
        reload_delay_non_mlag: PositiveInteger
        """Delay (seconds) after reboot until ports that are not part of an MLAG are enabled."""

    @AntaTest.anta_test
    def test(self) -> None:
        """Main test function for VerifyMlagReloadDelay."""
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
    """Verifies the dual-primary detection and its parameters of the MLAG configuration.

    Expected Results
    ----------------
    * Success: The test will pass if the dual-primary detection is enabled and its parameters are configured properly.
    * Failure: The test will fail if the dual-primary detection is NOT enabled or its parameters are NOT configured properly.
    * Skipped: The test will be skipped if MLAG is 'disabled'.

    Examples
    --------
    ```yaml
    anta.tests.mlag:
      - VerifyMlagDualPrimary:
          detection_delay: 200
          errdisabled: True
          recovery_delay: 60
          recovery_delay_non_mlag: 0
    ```
    """

    description = "Verifies the MLAG dual-primary detection parameters."
    categories: ClassVar[list[str]] = ["mlag"]
    commands: ClassVar[list[AntaCommand | AntaTemplate]] = [AntaCommand(command="show mlag detail", revision=2)]

    class Input(AntaTest.Input):
        """Input model for the VerifyMlagDualPrimary test."""

        detection_delay: PositiveInteger
        """Delay detection (seconds)."""
        errdisabled: bool = False
        """Errdisabled all interfaces when dual-primary is detected."""
        recovery_delay: PositiveInteger
        """Delay (seconds) after dual-primary detection resolves until non peer-link ports that are part of an MLAG are enabled."""
        recovery_delay_non_mlag: PositiveInteger
        """Delay (seconds) after dual-primary detection resolves until ports that are not part of an MLAG are enabled."""

    @AntaTest.anta_test
    def test(self) -> None:
        """Main test function for VerifyMlagDualPrimary."""
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


class VerifyMlagPrimaryPriority(AntaTest):
    """Verify the MLAG (Multi-Chassis Link Aggregation) primary priority.

    Expected Results
    ----------------
    * Success: The test will pass if the MLAG state is set as 'primary' and the priority matches the input.
    * Failure: The test will fail if the MLAG state is not 'primary' or the priority doesn't match the input.
    * Skipped: The test will be skipped if MLAG is 'disabled'.

    Examples
    --------
    ```yaml
    anta.tests.mlag:
      - VerifyMlagPrimaryPriority:
          primary_priority: 3276
    ```
    """

    description = "Verifies the configuration of the MLAG primary priority."
    categories: ClassVar[list[str]] = ["mlag"]
    commands: ClassVar[list[AntaCommand | AntaTemplate]] = [AntaCommand(command="show mlag detail", revision=2)]

    class Input(AntaTest.Input):
        """Input model for the VerifyMlagPrimaryPriority test."""

        primary_priority: MlagPriority
        """The expected MLAG primary priority."""

    @AntaTest.anta_test
    def test(self) -> None:
        """Main test function for VerifyMlagPrimaryPriority."""
        command_output = self.instance_commands[0].json_output
        self.result.is_success()
        # Skip the test if MLAG is disabled
        if command_output["state"] == "disabled":
            self.result.is_skipped("MLAG is disabled")
            return

        mlag_state = get_value(command_output, "detail.mlagState")
        primary_priority = get_value(command_output, "detail.primaryPriority")

        # Check MLAG state
        if mlag_state != "primary":
            self.result.is_failure("The device is not set as MLAG primary.")

        # Check primary priority
        if primary_priority != self.inputs.primary_priority:
            self.result.is_failure(
                f"The primary priority does not match expected. Expected `{self.inputs.primary_priority}`, but found `{primary_priority}` instead.",
            )
