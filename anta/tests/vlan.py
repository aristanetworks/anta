# Copyright (c) 2023-2025 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Module related to VLAN tests."""

# Mypy does not understand AntaTest.Input typing
# mypy: disable-error-code=attr-defined
from __future__ import annotations

from typing import TYPE_CHECKING, ClassVar, Literal

from pydantic import ConfigDict

from anta.custom_types import DynamicVLANSource, Vlan
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
    """Verifies dynamic VLAN source.

    This test performs the following checks for each specified dynamic VLAN:

      1. Ensures that dynamic VLAN(s) are properly configured in the system.
      2. Confirms that dynamic VLAN(s) are active for any of the designated sources.
      3. When strict mode is enabled (`strict: true`):
        - Dynamic VLAN(s) are activated for all the designated sources.
      4. Confirms that the dynamic VLAN(s) are disabled for other than designated sources.

    Expected Results
    ----------------
    * Success: The test will pass if all of the following conditions are met:
        - Dynamic VLAN(s) are properly configured in the system.
        - Dynamic VLAN(s) are active for any of the designated sources.
        - In strict mode, Dynamic Vlans(s) are active for all the designated sources.
        - Dynamic VLAN(s) are disabled for other than designated sources.
    * Failure: The test will fail if any of the following conditions is met:
        - Dynamic VLAN(s) are not active within the designated source
        - Dynamic VLAN(s) are active for other than designated sources.
        - In strict mode, dynamic VLAN(s) are disabled for any of the designated sources.
    * Skipped: The test will Skip if the following conditions is met:
        - Dynamic VLAN(s) are not configured on the device.

    Examples
    --------
    ```yaml
    anta.tests.vlan:
      - VerifyDynamicVlanSource:
          source:
            - evpn
            - mlagsync
          strict: False
    ```
    """

    categories: ClassVar[list[str]] = ["vlan"]
    commands: ClassVar[list[AntaCommand | AntaTemplate]] = [AntaCommand(command="show vlan dynamic", revision=1)]

    class Input(AntaTest.Input):
        """Input model for the VerifyDynamicVlanSource test."""

        model_config = ConfigDict(extra="forbid")
        source: list[DynamicVLANSource]
        """The dynamic VLAN source list."""
        strict: bool = False
        """If True, requires exact match of the provided dynamic VLAN sources, Defaults to `False`"""

    @AntaTest.anta_test
    def test(self) -> None:
        """Main test function for VerifyDynamicVlanSource."""
        self.result.is_success()
        command_output = self.instance_commands[0].json_output
        dynamic_vlans = command_output.get("dynamicVlans", {})

        actual_source = [source for source, data in dynamic_vlans.items() if data.get("vlanIds")]
        # If the dynamic vlans are not configured, skipping the test.
        if not actual_source:
            self.result.is_skipped("Dynamic VLANs are not configured")
            return

        expected_source = self.inputs.source
        str_expected_source = ", ".join(expected_source)
        str_actual_source = ", ".join(actual_source)

        # If strict flag is True and not all designated source have dynamic VLAN(s), test fails.
        if self.inputs.strict and sorted(actual_source) != (expected_source):
            self.result.is_failure(f"Dynamic VLAN(s) all source are not in {str_expected_source} Actual: {str_actual_source}")
            return

        # If dynamic VLANs are not active for None of the designated source or additional sources with dynamic VLAN(s) are found. test fails
        if not set(actual_source).issubset(expected_source):
            self.result.is_failure(f"Dynamic VLAN(s) source are not in {str_expected_source} Actual: {str_actual_source}")
