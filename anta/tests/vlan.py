# Copyright (c) 2023-2025 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Module related to VLAN tests."""

# Pyright does not understand AntaTest.Input typing
# pyright: reportAttributeAccessIssue=false
from __future__ import annotations

from typing import TYPE_CHECKING, ClassVar, Literal

from anta.custom_types import DynamicVlanSource, VlanId
from anta.input_models.vlan import Vlan
from anta.models import AntaCommand, AntaTest
from anta.tools import get_value

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
        start_vlan_id: VlanId
        """The starting VLAN ID in the range."""
        end_vlan_id: VlanId
        """The ending VLAN ID in the range."""

    @AntaTest.anta_test
    def test(self) -> None:
        """Main test function for VerifyVlanInternalPolicy."""
        self.result.is_success()
        command_output = self.instance_commands[0].json_output

        if (policy := self.inputs.policy) != (act_policy := get_value(command_output, "policy")):
            self.result.is_failure(f"Incorrect VLAN internal allocation policy configured - Expected: {policy} Actual: {act_policy}")
            return

        if (start_vlan_id := self.inputs.start_vlan_id) != (act_vlan_id := get_value(command_output, "startVlanId")):
            self.result.is_failure(
                f"VLAN internal allocation policy: {self.inputs.policy} - Incorrect start VLAN id configured - Expected: {start_vlan_id} Actual: {act_vlan_id}"
            )

        if (end_vlan_id := self.inputs.end_vlan_id) != (act_vlan_id := get_value(command_output, "endVlanId")):
            self.result.is_failure(
                f"VLAN internal allocation policy: {self.inputs.policy} - Incorrect end VLAN id configured - Expected: {end_vlan_id} Actual: {act_vlan_id}"
            )


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


class VerifyVlanStatus(AntaTest):
    """Verifies the administrative status of specified VLANs.

    Expected Results
    ----------------
    * Success: The test will pass if all specified VLANs exist in the configuration and their administrative status is correct.
    * Failure: The test will fail if any of the specified VLANs is not found in the configuration or if its administrative status is incorrect.

    Examples
    --------
    ```yaml
    anta.tests.vlan:
      - VerifyVlanStatus:
          vlans:
            - vlan_id: 10
              status: suspended
            - vlan_id: 4094
              status: active
    ```
    """

    categories: ClassVar[list[str]] = ["vlan"]
    commands: ClassVar[list[AntaCommand | AntaTemplate]] = [AntaCommand(command="show vlan", revision=1)]

    class Input(AntaTest.Input):
        """Input model for the VerifyVlanStatus test."""

        vlans: list[Vlan]
        """List of VLAN details."""

    @AntaTest.anta_test
    def test(self) -> None:
        """Main test function for VerifyVlanStatus."""
        self.result.is_success()
        command_output = self.instance_commands[0].json_output

        for vlan in self.inputs.vlans:
            if (vlan_detail := get_value(command_output, f"vlans.{vlan.vlan_id}")) is None:
                self.result.is_failure(f"{vlan} - Not configured")
                continue

            if (act_status := vlan_detail["status"]) != vlan.status:
                self.result.is_failure(f"{vlan} - Incorrect administrative status - Expected: {vlan.status} Actual: {act_status}")
