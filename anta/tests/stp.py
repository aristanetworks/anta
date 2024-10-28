# Copyright (c) 2023-2024 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Module related to various Spanning Tree Protocol (STP) tests."""

# Mypy does not understand AntaTest.Input typing
# mypy: disable-error-code=attr-defined
from __future__ import annotations

from typing import Any, ClassVar, Literal

from pydantic import Field

from anta.custom_types import Vlan
from anta.models import AntaCommand, AntaTemplate, AntaTest
from anta.tools import get_value


class VerifySTPMode(AntaTest):
    """Verifies the configured STP mode for a provided list of VLAN(s).

    Expected Results
    ----------------
    * Success: The test will pass if the STP mode is configured properly in the specified VLAN(s).
    * Failure: The test will fail if the STP mode is NOT configured properly for one or more specified VLAN(s).

    Examples
    --------
    ```yaml
    anta.tests.stp:
      - VerifySTPMode:
          mode: rapidPvst
          vlans:
            - 10
            - 20
    ```
    """

    name = "VerifySTPMode"
    description = "Verifies the configured STP mode for a provided list of VLAN(s)."
    categories: ClassVar[list[str]] = ["stp"]
    commands: ClassVar[list[AntaCommand | AntaTemplate]] = [AntaTemplate(template="show spanning-tree vlan {vlan}", revision=1)]

    class Input(AntaTest.Input):
        """Input model for the VerifySTPMode test."""

        mode: Literal["mstp", "rstp", "rapidPvst"] = "mstp"
        """STP mode to verify. Supported values: mstp, rstp, rapidPvst. Defaults to mstp."""
        vlans: list[Vlan]
        """List of VLAN on which to verify STP mode."""

    def render(self, template: AntaTemplate) -> list[AntaCommand]:
        """Render the template for each VLAN in the input list."""
        return [template.render(vlan=vlan) for vlan in self.inputs.vlans]

    @AntaTest.anta_test
    def test(self) -> None:
        """Main test function for VerifySTPMode."""
        not_configured = []
        wrong_stp_mode = []
        for command in self.instance_commands:
            vlan_id = command.params.vlan
            if not (
                stp_mode := get_value(
                    command.json_output,
                    f"spanningTreeVlanInstances.{vlan_id}.spanningTreeVlanInstance.protocol",
                )
            ):
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
    """Verifies there is no STP blocked ports.

    Expected Results
    ----------------
    * Success: The test will pass if there are NO ports blocked by STP.
    * Failure: The test will fail if there are ports blocked by STP.

    Examples
    --------
    ```yaml
    anta.tests.stp:
      - VerifySTPBlockedPorts:
    ```
    """

    name = "VerifySTPBlockedPorts"
    description = "Verifies there is no STP blocked ports."
    categories: ClassVar[list[str]] = ["stp"]
    commands: ClassVar[list[AntaCommand | AntaTemplate]] = [AntaCommand(command="show spanning-tree blockedports", revision=1)]

    @AntaTest.anta_test
    def test(self) -> None:
        """Main test function for VerifySTPBlockedPorts."""
        command_output = self.instance_commands[0].json_output
        if not (stp_instances := command_output["spanningTreeInstances"]):
            self.result.is_success()
        else:
            for key, value in stp_instances.items():
                stp_instances[key] = value.pop("spanningTreeBlockedPorts")
            self.result.is_failure(f"The following ports are blocked by STP: {stp_instances}")


class VerifySTPCounters(AntaTest):
    """Verifies there is no errors in STP BPDU packets.

    Expected Results
    ----------------
    * Success: The test will pass if there are NO STP BPDU packet errors under all interfaces participating in STP.
    * Failure: The test will fail if there are STP BPDU packet errors on one or many interface(s).

    Examples
    --------
    ```yaml
    anta.tests.stp:
      - VerifySTPCounters:
    ```
    """

    name = "VerifySTPCounters"
    description = "Verifies there is no errors in STP BPDU packets."
    categories: ClassVar[list[str]] = ["stp"]
    commands: ClassVar[list[AntaCommand | AntaTemplate]] = [AntaCommand(command="show spanning-tree counters", revision=1)]

    @AntaTest.anta_test
    def test(self) -> None:
        """Main test function for VerifySTPCounters."""
        command_output = self.instance_commands[0].json_output
        interfaces_with_errors = [
            interface for interface, counters in command_output["interfaces"].items() if counters["bpduTaggedError"] or counters["bpduOtherError"] != 0
        ]
        if interfaces_with_errors:
            self.result.is_failure(f"The following interfaces have STP BPDU packet errors: {interfaces_with_errors}")
        else:
            self.result.is_success()


class VerifySTPForwardingPorts(AntaTest):
    """Verifies that all interfaces are in a forwarding state for a provided list of VLAN(s).

    Expected Results
    ----------------
    * Success: The test will pass if all interfaces are in a forwarding state for the specified VLAN(s).
    * Failure: The test will fail if one or many interfaces are NOT in a forwarding state in the specified VLAN(s).

    Examples
    --------
    ```yaml
    anta.tests.stp:
      - VerifySTPForwardingPorts:
          vlans:
            - 10
            - 20
    ```
    """

    name = "VerifySTPForwardingPorts"
    description = "Verifies that all interfaces are forwarding for a provided list of VLAN(s)."
    categories: ClassVar[list[str]] = ["stp"]
    commands: ClassVar[list[AntaCommand | AntaTemplate]] = [AntaTemplate(template="show spanning-tree topology vlan {vlan} status", revision=1)]

    class Input(AntaTest.Input):
        """Input model for the VerifySTPForwardingPorts test."""

        vlans: list[Vlan]
        """List of VLAN on which to verify forwarding states."""

    def render(self, template: AntaTemplate) -> list[AntaCommand]:
        """Render the template for each VLAN in the input list."""
        return [template.render(vlan=vlan) for vlan in self.inputs.vlans]

    @AntaTest.anta_test
    def test(self) -> None:
        """Main test function for VerifySTPForwardingPorts."""
        not_configured = []
        not_forwarding = []
        for command in self.instance_commands:
            vlan_id = command.params.vlan
            if not (topologies := get_value(command.json_output, "topologies")):
                not_configured.append(vlan_id)
            else:
                interfaces_not_forwarding = []
                for value in topologies.values():
                    if vlan_id and int(vlan_id) in value["vlans"]:
                        interfaces_not_forwarding = [interface for interface, state in value["interfaces"].items() if state["state"] != "forwarding"]
                if interfaces_not_forwarding:
                    not_forwarding.append({f"VLAN {vlan_id}": interfaces_not_forwarding})
        if not_configured:
            self.result.is_failure(f"STP instance is not configured for the following VLAN(s): {not_configured}")
        if not_forwarding:
            self.result.is_failure(f"The following VLAN(s) have interface(s) that are not in a forwarding state: {not_forwarding}")
        if not not_configured and not interfaces_not_forwarding:
            self.result.is_success()


class VerifySTPRootPriority(AntaTest):
    """Verifies the STP root priority for a provided list of VLAN or MST instance ID(s).

    Expected Results
    ----------------
    * Success: The test will pass if the STP root priority is configured properly for the specified VLAN or MST instance ID(s).
    * Failure: The test will fail if the STP root priority is NOT configured properly for the specified VLAN or MST instance ID(s).

    Examples
    --------
    ```yaml
    anta.tests.stp:
      - VerifySTPRootPriority:
          priority: 32768
          instances:
            - 10
            - 20
    ```
    """

    name = "VerifySTPRootPriority"
    description = "Verifies the STP root priority for a provided list of VLAN or MST instance ID(s)."
    categories: ClassVar[list[str]] = ["stp"]
    commands: ClassVar[list[AntaCommand | AntaTemplate]] = [AntaCommand(command="show spanning-tree root detail", revision=1)]

    class Input(AntaTest.Input):
        """Input model for the VerifySTPRootPriority test."""

        priority: int
        """STP root priority to verify."""
        instances: list[Vlan] = Field(default=[])
        """List of VLAN or MST instance ID(s). If empty, ALL VLAN or MST instance ID(s) will be verified."""

    @AntaTest.anta_test
    def test(self) -> None:
        """Main test function for VerifySTPRootPriority."""
        command_output = self.instance_commands[0].json_output
        if not (stp_instances := command_output["instances"]):
            self.result.is_failure("No STP instances configured")
            return
        # Checking the type of instances based on first instance
        first_name = next(iter(stp_instances))
        if first_name.startswith("MST"):
            prefix = "MST"
        elif first_name.startswith("VL"):
            prefix = "VL"
        else:
            self.result.is_failure(f"Unsupported STP instance type: {first_name}")
            return
        check_instances = [f"{prefix}{instance_id}" for instance_id in self.inputs.instances] if self.inputs.instances else command_output["instances"].keys()
        wrong_priority_instances = [
            instance for instance in check_instances if get_value(command_output, f"instances.{instance}.rootBridge.priority") != self.inputs.priority
        ]
        if wrong_priority_instances:
            self.result.is_failure(f"The following instance(s) have the wrong STP root priority configured: {wrong_priority_instances}")
        else:
            self.result.is_success()


class VerifyStpTopologyChanges(AntaTest):
    """Verifies the number of changes across all interfaces in the Spanning Tree Protocol (STP) topology is below a threshold.

    Expected Results
    ----------------
    * Success: The test will pass if the total number of changes across all interfaces is less than the specified threshold.
    * Failure: The test will fail if the total number of changes across all interfaces meets or exceeds the specified threshold,
    indicating potential instability in the topology.

    Examples
    --------
    ```yaml
    anta.tests.stp:
      - VerifyStpTopologyChanges:
          threshold: 10
    ```
    """

    name = "VerifyStpTopologyChanges"
    description = "Verifies the number of changes across all interfaces in the Spanning Tree Protocol (STP) topology is below a threshold."
    categories: ClassVar[list[str]] = ["stp"]
    commands: ClassVar[list[AntaCommand | AntaTemplate]] = [AntaCommand(command="show spanning-tree topology status detail", revision=1)]

    class Input(AntaTest.Input):
        """Input model for the VerifyStpTopologyChanges test."""

        threshold: int
        """The threshold number of changes in the STP topology."""

    @AntaTest.anta_test
    def test(self) -> None:
        """Main test function for VerifyStpTopologyChanges."""
        failures: dict[str, Any] = {"topologies": {}}

        command_output = self.instance_commands[0].json_output
        stp_topologies = command_output.get("topologies", {})

        # verifies all available topologies except the "NoStp" topology.
        stp_topologies.pop("NoStp", None)

        # Verify the STP topology(s).
        if not stp_topologies:
            self.result.is_failure("STP is not configured.")
            return

        # Verifies the number of changes across all interfaces
        for topology, topology_details in stp_topologies.items():
            interfaces = {
                interface: {"Number of changes": num_of_changes}
                for interface, details in topology_details.get("interfaces", {}).items()
                if (num_of_changes := details.get("numChanges")) > self.inputs.threshold
            }
            if interfaces:
                failures["topologies"][topology] = interfaces

        if failures["topologies"]:
            self.result.is_failure(f"The following STP topologies are not configured or number of changes not within the threshold:\n{failures}")
        else:
            self.result.is_success()
