# Copyright (c) 2023 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""
Test functions related to various Spanning Tree Protocol (STP) settings
"""
# Mypy does not understand AntaTest.Input typing
# mypy: disable-error-code=attr-defined
from __future__ import annotations

# Need to keep List for pydantic in python 3.8
from typing import List, Literal

from anta.custom_types import Vlan
from anta.models import AntaCommand, AntaTemplate, AntaTest
from anta.tools.get_value import get_value


class VerifySTPMode(AntaTest):
    """
    Verifies the configured STP mode for a provided list of VLAN(s).

    Expected Results:
        * success: The test will pass if the STP mode is configured properly in the specified VLAN(s).
        * failure: The test will fail if the STP mode is NOT configured properly for one or more specified VLAN(s).
    """

    name = "VerifySTPMode"
    description = "Verifies the configured STP mode for a provided list of VLAN(s)."
    categories = ["stp"]
    commands = [AntaTemplate(template="show spanning-tree vlan {vlan}")]

    class Input(AntaTest.Input):  # pylint: disable=missing-class-docstring
        mode: Literal["mstp", "rstp", "rapidPvst"] = "mstp"
        """STP mode to verify"""
        vlans: List[Vlan]
        """List of VLAN on which to verify STP mode"""

    def render(self, template: AntaTemplate) -> list[AntaCommand]:
        return [template.render(vlan=vlan) for vlan in self.inputs.vlans]

    @AntaTest.anta_test
    def test(self) -> None:
        not_configured = []
        wrong_stp_mode = []
        for command in self.instance_commands:
            if "vlan" in command.params:
                vlan_id = command.params["vlan"]
            if not (stp_mode := get_value(command.json_output, f"spanningTreeVlanInstances.{vlan_id}.spanningTreeVlanInstance.protocol")):
                not_configured.append(vlan_id)
            elif stp_mode != self.inputs.mode:
                wrong_stp_mode.append(vlan_id)
        if not_configured:
            self.result.is_failure(f"STP mode '{self.inputs.mode}' not configured for the following VLAN(s): {not_configured}")
        if wrong_stp_mode:
            self.result.is_failure(f"Wrong STP mode configured for the following VLAN(s): {wrong_stp_mode}")
        if not not_configured and not wrong_stp_mode:
            self.result.is_success()


class VerifySTPBlockedPorts(AntaTest):
    """
    Verifies there is no STP blocked ports.

    Expected Results:
        * success: The test will pass if there are NO ports blocked by STP.
        * failure: The test will fail if there are ports blocked by STP.
    """

    name = "VerifySTPBlockedPorts"
    description = "Verifies there is no STP blocked ports."
    categories = ["stp"]
    commands = [AntaCommand(command="show spanning-tree blockedports")]

    @AntaTest.anta_test
    def test(self) -> None:
        command_output = self.instance_commands[0].json_output
        if not (stp_instances := command_output["spanningTreeInstances"]):
            self.result.is_success()
        else:
            for key, value in stp_instances.items():
                stp_instances[key] = value.pop("spanningTreeBlockedPorts")
            self.result.is_failure(f"The following ports are blocked by STP: {stp_instances}")


class VerifySTPCounters(AntaTest):
    """
    Verifies there is no errors in STP BPDU packets.

    Expected Results:
        * success: The test will pass if there are NO STP BPDU packet errors under all interfaces participating in STP.
        * failure: The test will fail if there are STP BPDU packet errors on one or many interface(s).
    """

    name = "VerifySTPCounters"
    description = "Verifies there is no errors in STP BPDU packets."
    categories = ["stp"]
    commands = [AntaCommand(command="show spanning-tree counters")]

    @AntaTest.anta_test
    def test(self) -> None:
        command_output = self.instance_commands[0].json_output
        interfaces_with_errors = [
            interface for interface, counters in command_output["interfaces"].items() if counters["bpduTaggedError"] or counters["bpduOtherError"] != 0
        ]
        if interfaces_with_errors:
            self.result.is_failure(f"The following interfaces have STP BPDU packet errors: {interfaces_with_errors}")
        else:
            self.result.is_success()


class VerifySTPForwardingPorts(AntaTest):
    """
    Verifies that all interfaces are in a forwarding state for a provided list of VLAN(s).

    Expected Results:
        * success: The test will pass if all interfaces are in a forwarding state for the specified VLAN(s).
        * failure: The test will fail if one or many interfaces are NOT in a forwarding state in the specified VLAN(s).
    """

    name = "VerifySTPForwardingPorts"
    description = "Verifies that all interfaces are forwarding for a provided list of VLAN(s)."
    categories = ["stp"]
    commands = [AntaTemplate(template="show spanning-tree topology vlan {vlan} status")]

    class Input(AntaTest.Input):  # pylint: disable=missing-class-docstring
        vlans: List[Vlan]
        """List of VLAN on which to verify forwarding states"""

    def render(self, template: AntaTemplate) -> list[AntaCommand]:
        return [template.render(vlan=vlan) for vlan in self.inputs.vlans]

    @AntaTest.anta_test
    def test(self) -> None:
        not_configured = []
        not_forwarding = []
        for command in self.instance_commands:
            if "vlan" in command.params:
                vlan_id = command.params["vlan"]
            if not (topologies := get_value(command.json_output, "topologies")):
                not_configured.append(vlan_id)
            else:
                for value in topologies.values():
                    if int(vlan_id) in value["vlans"]:
                        interfaces_not_forwarding = [interface for interface, state in value["interfaces"].items() if state["state"] != "forwarding"]
                if interfaces_not_forwarding:
                    not_forwarding.append({f"VLAN {vlan_id}": interfaces_not_forwarding})
        if not_configured:
            self.result.is_failure(f"STP instance is not configured for the following VLAN(s): {not_configured}")
        if not_forwarding:
            self.result.is_failure(f"The following VLAN(s) have interface(s) that are not in a fowarding state: {not_forwarding}")
        if not not_configured and not interfaces_not_forwarding:
            self.result.is_success()


class VerifySTPRootPriority(AntaTest):
    """
    Verifies the STP root priority for a provided list of VLAN or MST instance ID(s).

    Expected Results:
        * success: The test will pass if the STP root priority is configured properly for the specified VLAN or MST instance ID(s).
        * failure: The test will fail if the STP root priority is NOT configured properly for the specified VLAN or MST instance ID(s).
    """

    name = "VerifySTPRootPriority"
    description = "Verifies the STP root priority for a provided list of VLAN or MST instance ID(s)."
    categories = ["stp"]
    commands = [AntaCommand(command="show spanning-tree root detail")]

    class Input(AntaTest.Input):  # pylint: disable=missing-class-docstring
        priority: int
        """STP root priority to verify"""
        instances: List[Vlan] = []
        """List of VLAN or MST instance ID(s). If empty, ALL VLAN or MST instance ID(s) will be verified."""

    @AntaTest.anta_test
    def test(self) -> None:
        command_output = self.instance_commands[0].json_output
        if not (stp_instances := command_output["instances"]):
            self.result.is_failure("No STP instances configured")
            return
        for instance in stp_instances:
            if instance.startswith("MST"):
                prefix = "MST"
                break
            if instance.startswith("VL"):
                prefix = "VL"
                break
        check_instances = [f"{prefix}{instance_id}" for instance_id in self.inputs.instances] if self.inputs.instances else command_output["instances"].keys()
        wrong_priority_instances = [
            instance for instance in check_instances if get_value(command_output, f"instances.{instance}.rootBridge.priority") != self.inputs.priority
        ]
        if wrong_priority_instances:
            self.result.is_failure(f"The following instance(s) have the wrong STP root priority configured: {wrong_priority_instances}")
        else:
            self.result.is_success()
