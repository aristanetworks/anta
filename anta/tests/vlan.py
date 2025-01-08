# Copyright (c) 2023-2025 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Module related to VLAN tests."""

# Mypy does not understand AntaTest.Input typing
# mypy: disable-error-code=attr-defined
from __future__ import annotations

from typing import TYPE_CHECKING, ClassVar, Literal

from anta.custom_types import DynamicVlanSource, Vlan
from anta.models import AntaCommand, AntaTest
from anta.tools import get_failed_logs, get_value

if TYPE_CHECKING:
    from anta.models import AntaTemplate


class VerifyVlanInternalPolicy(AntaTest):
    """Verifies if the VLAN internal allocation policy is ascending or descending and if the VLANs are within the specified range.

    Expected Results
    ----------------
    * Success: The test will pass if the VLAN internal allocation policy is either ascending or descending
                 and the VLANs are within the specified range.
    * Failure: The test will fail if the VLAN internal allocation policy is neither ascending nor descending
                 or the VLANs are outside the specified range.

    Examples
    --------
    ```yaml
    anta.tests.vlan:
      - VerifyVlanInternalPolicy:
          policy: ascending
          start_vlan_id: 1006
          end_vlan_id: 4094
    ```
    """

    description = "Verifies the VLAN internal allocation policy and the range of VLANs."
    categories: ClassVar[list[str]] = ["vlan"]
    commands: ClassVar[list[AntaCommand | AntaTemplate]] = [AntaCommand(command="show vlan internal allocation policy", revision=1)]

    class Input(AntaTest.Input):
        """Input model for the VerifyVlanInternalPolicy test."""

        policy: Literal["ascending", "descending"]
        """The VLAN internal allocation policy. Supported values: ascending, descending."""
        start_vlan_id: Vlan
        """The starting VLAN ID in the range."""
        end_vlan_id: Vlan
        """The ending VLAN ID in the range."""

    @AntaTest.anta_test
    def test(self) -> None:
        """Main test function for VerifyVlanInternalPolicy."""
        command_output = self.instance_commands[0].json_output

        keys_to_verify = ["policy", "startVlanId", "endVlanId"]
        actual_policy_output = {key: get_value(command_output, key) for key in keys_to_verify}
        expected_policy_output = {"policy": self.inputs.policy, "startVlanId": self.inputs.start_vlan_id, "endVlanId": self.inputs.end_vlan_id}

        # Check if the actual output matches the expected output
        if actual_policy_output != expected_policy_output:
            failed_log = "The VLAN internal allocation policy is not configured properly:"
            failed_log += get_failed_logs(expected_policy_output, actual_policy_output)
            self.result.is_failure(failed_log)
        else:
            self.result.is_success()


class VerifyDynamicVlanSource(AntaTest):
    """Verifies dynamic VLAN(s) sources.

    This test performs the following checks for specified dynamic VLAN(s):

      1. Ensures that dynamic VLAN(s) are properly configured in the system.
      2. Confirms that dynamic VLAN(s) are enabled on all the designated sources.
      3. When strict mode is enabled (`strict: true`):
        - The dynamic VLAN(s) are enabled on all the designated sources and disabled for non designated sources.

    Expected Results
    ----------------
    * Success: The test will pass if all of the following conditions are met:
        - The dynamic VLAN(s) are properly configured in the system.
        - The dynamic VLAN(s) are enabled for all of the designated sources.
        - In strict mode, The dynamic VLAN(s) are enabled on all the designated sources and disabled for non designated sources.
    * Failure: The test will fail if any of the following conditions is met:
        - The dynamic VLAN(s) are disabled on any of designated sources.
        - In strict mode, dynamic VLAN(s) are disabled on any of the designated sources. or enabled for non designated sources.
    * Skipped: The test will skip if the following conditions is met:
        - Dynamic VLAN(s) are not configured on the device.

    Examples
    --------
    ```yaml
    anta.tests.vlan:
      - VerifyDynamicVlanSource:
          sources:
            - evpn
            - mlagsync
          strict: False
    ```
    """

    categories: ClassVar[list[str]] = ["vlan"]
    commands: ClassVar[list[AntaCommand | AntaTemplate]] = [AntaCommand(command="show vlan dynamic", revision=1)]

    class Input(AntaTest.Input):
        """Input model for the VerifyDynamicVlanSource test."""

        sources: list[DynamicVlanSource]
        """The dynamic VLAN(s) source list."""
        strict: bool = False
        """If True, dynamic VLAN(s) should be enabled only on designated sources, Defaults to `False`."""

    @AntaTest.anta_test
    def test(self) -> None:
        """Main test function for VerifyDynamicVlanSource."""
        self.result.is_success()
        command_output = self.instance_commands[0].json_output
        dynamic_vlans = command_output.get("dynamicVlans", {})

        actual_sources = [source for source, data in dynamic_vlans.items() if data.get("vlanIds")]
        # If the dynamic vlans are not configured, skipping the test.
        if not actual_sources:
            self.result.is_skipped("Dynamic VLANs are not configured")
            return

        expected_sources = self.inputs.sources
        str_expected_sources = ", ".join(expected_sources)
        str_actual_sources = ", ".join(actual_sources)

        # If strict flag True, and dynamic VLAN(s) are disabled on any of the designated sources or enabled non designated sources, test fails.
        if self.inputs.strict and sorted(actual_sources) != sorted(expected_sources):
            self.result.is_failure(f"Dynamic VLAN(s) sources mismatch - Expected: {str_expected_sources} Actual: {str_actual_sources}")
            return

        # If dynamic VLAN(s) are disabled on any of the designated sources, test fails.
        absent_sources = set(expected_sources).difference(set(actual_sources))
        if absent_sources:
            self.result.is_failure(f"Dynamic VLAN(s) sources mismatch - Expected: {str_expected_sources} Actual: {str_actual_sources}")
