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
    """Verifies dynamic VLAN allocation for specified VLAN sources.

    This test performs the following checks for each specified VLAN source:

      1. Validates source exists in dynamic VLAN table.
      2. Verifies at least one VLAN is allocated to the source.
      3. When strict mode is enabled (`strict: true`), ensures no other sources have VLANs allocated.

    Expected Results
    ----------------
    * Success: The test will pass if all of the following conditions are met:
        - Each specified source exists in dynamic VLAN table.
        - Each specified source has at least one VLAN allocated.
        - In strict mode: No other sources have VLANs allocated.
    * Failure: The test will fail if any of the following conditions is met:
        - Specified source not found in configuration.
        - Source exists but has no VLANs allocated.
        - In strict mode: Non-specified sources have VLANs allocated.

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
        """The dynamic VLAN source list."""
        strict: bool = False
        """If True, only specified sources are allowed to have VLANs allocated. Default is False."""

    @AntaTest.anta_test
    def test(self) -> None:
        """Main test function for VerifyDynamicVlanSource."""
        self.result.is_success()
        command_output = self.instance_commands[0].json_output
        dynamic_vlans = command_output.get("dynamicVlans", {})

        # Get all configured sources and sources with VLANs allocated
        configured_sources = set(dynamic_vlans.keys())
        sources_with_vlans = {source for source, data in dynamic_vlans.items() if data.get("vlanIds")}
        expected_sources = set(self.inputs.sources)

        # Check if all specified sources exist in configuration
        missing_sources = expected_sources - configured_sources
        if missing_sources:
            self.result.is_failure(f"Dynamic VLAN source(s) not found in configuration: {', '.join(sorted(missing_sources))}")
            return

        # Check if configured sources have VLANs allocated
        sources_without_vlans = expected_sources - sources_with_vlans
        if sources_without_vlans:
            self.result.is_failure(f"Dynamic VLAN source(s) exist but have no VLANs allocated: {', '.join(sorted(sources_without_vlans))}")
            return

        # In strict mode, verify no other sources have VLANs allocated
        if self.inputs.strict:
            unexpected_sources = sources_with_vlans - expected_sources
            if unexpected_sources:
                self.result.is_failure(f"Strict mode enabled: Unexpected sources have VLANs allocated: {', '.join(sorted(unexpected_sources))}")
