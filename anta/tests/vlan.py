# Copyright (c) 2023-2024 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""
Test functions related to VLAN
"""
# Mypy does not understand AntaTest.Input typing
# mypy: disable-error-code=attr-defined

from anta.custom_types import VlanPolicy, Vlan
from anta.models import AntaCommand, AntaTest
from anta.tools.get_value import get_value
from anta.tools.utils import get_failed_logs


class VerifyVlanInternalPolicy(AntaTest):
    """
    This class verifies vlan internal policy as ascending or descending and the range of vlans.

    Expected Results:
      * success: The test will pass if vlan internal policy is ascending or descending and the vlans are within input range.
      * failure: The test will fail if vlan internal policy is not ascending or descending and the vlans are not within input range.
    """

    name = "VerifyVlanInternalPolicy"
    description = "This test verifies vlan internal policy as ascending or descending and the range of vlans."
    categories = ["vlan"]
    commands = [AntaCommand(command="show vlan internal allocation policy")]

    class Input(AntaTest.Input):
        """Inputs for the VerifyVlanInternalPolicy test."""
        policy: VlanPolicy
        """Vlan internal allocation policy"""
        start_vlan_id: Vlan
        """Start range of vlan"""
        end_vlan_id: Vlan
        """End range of vlan"""

    @AntaTest.anta_test
    def test(self) -> None:
        command_output = self.instance_commands[0].json_output
        
        keys_to_verify = ["policy", "startVlanId", "endVlanId"]
        actual_policy_output = {key: get_value(command_output, key) for key in keys_to_verify}
        expected_policy_output = {"policy": self.inputs.policy, "startVlanId": self.inputs.start_vlan_id, "endVlanId": self.inputs.end_vlan_id}
        self.result.is_success()
        
        if actual_policy_output != expected_policy_output:
            failed_log = f"Vlan internal allocation policy is not configured properly:"
            failed_log += get_failed_logs(expected_policy_output, actual_policy_output)
            self.result.is_failure(f"{failed_log}")
