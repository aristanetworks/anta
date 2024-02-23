# Copyright (c) 2023-2024 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""
Test functions related to VLAN
"""
# Mypy does not understand AntaTest.Input typing
# mypy: disable-error-code=attr-defined

from typing import Literal

from anta.custom_types import Vlan
from anta.models import AntaCommand, AntaTest
from anta.tools.get_value import get_value
from anta.tools.utils import get_failed_logs


class VerifyVlanInternalPolicy(AntaTest):
    """
    This class checks if the VLAN internal allocation policy is ascending or descending and
    if the VLANs are within the specified range.

    Expected Results:
      * Success: The test will pass if the VLAN internal allocation policy is either ascending or descending
                 and the VLANs are within the specified range.
      * Failure: The test will fail if the VLAN internal allocation policy is neither ascending nor descending
                 or the VLANs are outside the specified range.
    """

    name = "VerifyVlanInternalPolicy"
    description = "This test checks the VLAN internal allocation policy and the range of VLANs."
    categories = ["vlan"]
    commands = [AntaCommand(command="show vlan internal allocation policy")]

    class Input(AntaTest.Input):
        """Inputs for the VerifyVlanInternalPolicy test."""

        policy: Literal["ascending", "descending"]
        """The VLAN internal allocation policy."""
        start_vlan_id: Vlan
        """The starting VLAN ID in the range."""
        end_vlan_id: Vlan
        """The ending VLAN ID in the range."""

    @AntaTest.anta_test
    def test(self) -> None:
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
