# Copyright (c) 2023-2025 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Module related to multicast and IGMP tests."""

# Pyright does not understand AntaTest.Input typing
# pyright: reportAttributeAccessIssue=false
from __future__ import annotations

from typing import TYPE_CHECKING, ClassVar

from anta.custom_types import VlanId
from anta.models import AntaCommand, AntaTest

if TYPE_CHECKING:
    from anta.models import AntaTemplate


class VerifyIGMPSnoopingVlans(AntaTest):
    """Verifies the IGMP snooping status for the provided VLANs.

    Expected Results
    ----------------
    * Success: The test will pass if the IGMP snooping status matches the expected status for the provided VLANs.
    * Failure: The test will fail if the IGMP snooping status does not match the expected status for the provided VLANs.

    Examples
    --------
    ```yaml
    anta.tests.multicast:
      - VerifyIGMPSnoopingVlans:
          vlans:
            10: False
            12: False
    ```
    """

    categories: ClassVar[list[str]] = ["multicast"]
    commands: ClassVar[list[AntaCommand | AntaTemplate]] = [AntaCommand(command="show ip igmp snooping", revision=1)]

    class Input(AntaTest.Input):
        """Input model for the VerifyIGMPSnoopingVlans test."""

        vlans: dict[VlanId, bool]
        """Dictionary with VLAN ID and whether IGMP snooping must be enabled (True) or disabled (False)."""

    @AntaTest.anta_test
    def test(self) -> None:
        """Main test function for VerifyIGMPSnoopingVlans."""
        command_output = self.instance_commands[0].json_output
        self.result.is_success()
        for vlan, enabled in self.inputs.vlans.items():
            if str(vlan) not in command_output["vlans"]:
                self.result.is_failure(f"Supplied vlan {vlan} is not present on the device")
                continue
            expected_state = "enabled" if enabled else "disabled"
            igmp_state = command_output["vlans"][str(vlan)]["igmpSnoopingState"]
            if igmp_state != expected_state:
                self.result.is_failure(f"VLAN{vlan} - Incorrect IGMP state - Expected: {expected_state} Actual: {igmp_state}")


class VerifyIGMPSnoopingGlobal(AntaTest):
    """Verifies the IGMP snooping global status.

    Expected Results
    ----------------
    * Success: The test will pass if the IGMP snooping global status matches the expected status.
    * Failure: The test will fail if the IGMP snooping global status does not match the expected status.

    Examples
    --------
    ```yaml
    anta.tests.multicast:
      - VerifyIGMPSnoopingGlobal:
          enabled: True
    ```
    """

    categories: ClassVar[list[str]] = ["multicast"]
    commands: ClassVar[list[AntaCommand | AntaTemplate]] = [AntaCommand(command="show ip igmp snooping", revision=1)]

    class Input(AntaTest.Input):
        """Input model for the VerifyIGMPSnoopingGlobal test."""

        enabled: bool
        """Whether global IGMP snopping must be enabled (True) or disabled (False)."""

    @AntaTest.anta_test
    def test(self) -> None:
        """Main test function for VerifyIGMPSnoopingGlobal."""
        command_output = self.instance_commands[0].json_output
        self.result.is_success()
        igmp_state = command_output["igmpSnoopingState"]
        expected_state = "enabled" if self.inputs.enabled else "disabled"
        if igmp_state != expected_state:
            self.result.is_failure(f"IGMP state is not valid - Expected: {expected_state} Actual: {igmp_state}")
