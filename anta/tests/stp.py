"""
Test functions related to various Spanning Tree Protocol (STP) settings
"""
from __future__ import annotations

from typing import List, Optional

from anta.models import AntaCommand, AntaTemplate, AntaTest
from anta.tools.get_value import get_value


class VerifySTPMode(AntaTest):
    """
    Verifies the configured STP mode for a provided list of VLAN(s).

    Expected Results:
        * success: The test will pass if the STP mode is configured properly in the specified VLAN(s).
        * failure: The test will fail if the STP mode is NOT configured properly for one or more specified VLAN(s).
        * skipped: The test will be skipped if the STP mode is not provided.
        * error: The test will give an error if a list of VLAN(s) is not provided as template_params.
    """

    name = "VerifySTPMode"
    description = "Verifies the configured STP mode for a provided list of VLAN(s)."
    categories = ["stp"]
    template = AntaTemplate(template="show spanning-tree vlan {vlan}")

    @staticmethod
    def _check_stp_mode(mode: str) -> None:
        """
        Verifies if the provided STP mode is compatible with Arista EOS devices.

        Args:
            mode: The STP mode to verify.
        """
        stp_modes = ["mstp", "rstp", "rapidPvst"]

        if mode not in stp_modes:
            raise ValueError(f"Wrong STP mode provided. Valid modes are: {stp_modes}")

    @AntaTest.anta_test
    def test(self, mode: str = "mstp") -> None:
        """
        Run VerifySTPVersion validation.

        Args:
            mode: STP mode to verify. Defaults to 'mstp'.
        """
        if not mode:
            self.result.is_skipped(f"{self.__class__.name} did not run because mode was not supplied")
            return

        self._check_stp_mode(mode)

        self.result.is_success()

        for command in self.instance_commands:
            if command.params and "vlan" in command.params:
                vlan_id = command.params["vlan"]
            if not (stp_mode := get_value(command.json_output, f"spanningTreeVlanInstances.{vlan_id}.spanningTreeVlanInstance.protocol")):
                self.result.is_failure(f"STP mode '{mode}' not configured for VLAN {vlan_id}")

            elif stp_mode != mode:
                self.result.is_failure(f"Wrong STP mode configured for VLAN {vlan_id}")


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
        """
        Run VerifySTPBlockedPorts validation
        """

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
        """
        Run VerifySTPBlockedPorts validation
        """

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
        * error: The test will give an error if a list of VLAN(s) is not provided as template_params.
    """

    name = "VerifySTPForwardingPorts"
    description = "Verifies that all interfaces are forwarding for a provided list of VLAN(s)."
    categories = ["stp"]
    template = AntaTemplate(template="show spanning-tree topology vlan {vlan} status")

    @AntaTest.anta_test
    def test(self) -> None:
        """
        Run VerifySTPForwardingPorts validation.
        """

        self.result.is_success()

        for command in self.instance_commands:
            if command.params and "vlan" in command.params:
                vlan_id = command.params["vlan"]

            if not (topologies := get_value(command.json_output, "topologies")):
                self.result.is_failure(f"STP instance for VLAN {vlan_id} is not configured")

            else:
                for value in topologies.values():
                    if int(vlan_id) in value["vlans"]:
                        interfaces_not_forwarding = [interface for interface, state in value["interfaces"].items() if state["state"] != "forwarding"]

                if interfaces_not_forwarding:
                    self.result.is_failure(f"The following interface(s) are not in a forwarding state for VLAN {vlan_id}: {interfaces_not_forwarding}")


class VerifySTPRootPriority(AntaTest):
    """
    Verifies the STP root priority for a provided list of VLAN or MST instance ID(s).

    Expected Results:
        * success: The test will pass if the STP root priority is configured properly for the specified VLAN or MST instance ID(s).
        * failure: The test will fail if the STP root priority is NOT configured properly for the specified VLAN or MST instance ID(s).
        * skipped: The test will be skipped if the STP root priority is not provided.
    """

    name = "VerifySTPRootPriority"
    description = "Verifies the STP root priority for a provided list of VLAN or MST instance ID(s)."
    categories = ["stp"]
    commands = [AntaCommand(command="show spanning-tree root detail")]

    @AntaTest.anta_test
    def test(self, priority: Optional[int] = None, instances: Optional[List[int]] = None) -> None:
        """
        Run VerifySTPRootPriority validation.

        Args:
            priority: STP root priority to verify.
            instances: List of VLAN or MST instance ID(s). By default, ALL VLAN or MST instance ID(s) will be verified.
        """
        if not priority:
            self.result.is_skipped(f"{self.__class__.name} did not run because priority was not supplied")
            return

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

        check_instances = [f"{prefix}{instance_id}" for instance_id in instances] if instances else command_output["instances"].keys()

        wrong_priority_instances = [instance for instance in check_instances if get_value(command_output, f"instances.{instance}.rootBridge.priority") != priority]

        if wrong_priority_instances:
            self.result.is_failure(f"The following instance(s) have the wrong STP root priority configured: {wrong_priority_instances}")
        else:
            self.result.is_success()
