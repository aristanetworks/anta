# Copyright (c) 2023-2024 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Module related to multicast and IGMP tests."""

# Mypy does not understand AntaTest.Input typing
# mypy: disable-error-code=attr-defined
from __future__ import annotations

from typing import TYPE_CHECKING, ClassVar

from anta.custom_types import Vlan
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

    name = "VerifyIGMPSnoopingVlans"
    description = "Verifies the IGMP snooping status for the provided VLANs."
    categories: ClassVar[list[str]] = ["multicast"]
    commands: ClassVar[list[AntaCommand | AntaTemplate]] = [AntaCommand(command="show ip igmp snooping", revision=1)]

    class Input(AntaTest.Input):
        """Input model for the VerifyIGMPSnoopingVlans test."""

        vlans: dict[Vlan, bool]
        """Dictionary with VLAN ID and whether IGMP snooping must be enabled (True) or disabled (False)."""

    @AntaTest.anta_test
    def test(self) -> None:
        """Main test function for VerifyIGMPSnoopingVlans."""
        command_output = self.instance_commands[0].json_output
        self.result.is_success()
        for vlan, enabled in self.inputs.vlans.items():
            if str(vlan) not in command_output["vlans"]:
                self.result.is_failure(f"Supplied vlan {vlan} is not present on the device.")
                continue

            igmp_state = command_output["vlans"][str(vlan)]["igmpSnoopingState"]
            if igmp_state != "enabled" if enabled else igmp_state != "disabled":
                self.result.is_failure(f"IGMP state for vlan {vlan} is {igmp_state}")


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

    name = "VerifyIGMPSnoopingGlobal"
    description = "Verifies the IGMP snooping global configuration."
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
        if igmp_state != "enabled" if self.inputs.enabled else igmp_state != "disabled":
            self.result.is_failure(f"IGMP state is not valid: {igmp_state}")
