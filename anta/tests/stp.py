# Copyright (c) 2023-2025 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Module related to various Spanning Tree Protocol (STP) tests."""

# Pyright does not understand AntaTest.Input typing
# pyright: reportAttributeAccessIssue=false
from __future__ import annotations

from typing import ClassVar, Literal

from pydantic import Field

from anta.custom_types import Interface, InterfaceType, VlanId
from anta.models import AntaCommand, AntaTemplate, AntaTest
from anta.result_manager.models import AntaTestStatus
from anta.tools import get_value, is_interface_ignored


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

    categories: ClassVar[list[str]] = ["stp"]
    commands: ClassVar[list[AntaCommand | AntaTemplate]] = [AntaTemplate(template="show spanning-tree vlan {vlan}", revision=1)]

    class Input(AntaTest.Input):
        """Input model for the VerifySTPMode test."""

        mode: Literal["mstp", "rstp", "rapidPvst"] = "mstp"
        """STP mode to verify. Supported values: mstp, rstp, rapidPvst. Defaults to mstp."""
        vlans: list[VlanId]
        """List of VLAN on which to verify STP mode."""

    def render(self, template: AntaTemplate) -> list[AntaCommand]:
        """Render the template for each VLAN in the input list."""
        return [template.render(vlan=vlan) for vlan in self.inputs.vlans]

    @AntaTest.anta_test
    def test(self) -> None:
        """Main test function for VerifySTPMode."""
        self.result.is_success()
        for command in self.instance_commands:
            vlan_id = command.params.vlan
            if not (
                stp_mode := get_value(
                    command.json_output,
                    f"spanningTreeVlanInstances.{vlan_id}.spanningTreeVlanInstance.protocol",
                )
            ):
                self.result.is_failure(f"VLAN {vlan_id} STP mode: {self.inputs.mode} - Not configured")
            elif stp_mode != self.inputs.mode:
                self.result.is_failure(f"VLAN {vlan_id} - Incorrect STP mode - Expected: {self.inputs.mode} Actual: {stp_mode}")


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
                stp_block_ports = value.get("spanningTreeBlockedPorts")
                self.result.is_failure(f"STP Instance: {key} - Blocked ports - {', '.join(stp_block_ports)}")


class VerifySTPCounters(AntaTest):
    """Verifies there is no errors in STP BPDU packets.

    Expected Results
    ----------------
    * Success: The test will pass if there are NO STP BPDU packet errors under all or on specified interfaces participating in STP.
    * Failure: The test will fail if there are STP BPDU packet errors on one or many interface(s).

    Examples
    --------
    ```yaml
    anta.tests.stp:
      - VerifySTPCounters:
          interfaces:
            - Ethernet10
            - Ethernet12
          ignored_interfaces:
            - Vxlan1
            - Loopback0
    ```
    """

    categories: ClassVar[list[str]] = ["stp"]
    commands: ClassVar[list[AntaCommand | AntaTemplate]] = [AntaCommand(command="show spanning-tree counters", revision=1)]
    _atomic_support: ClassVar[bool] = True

    class Input(AntaTest.Input):
        """Input model for the VerifySTPCounters test."""

        interfaces: list[Interface] | None = None
        """A list of interfaces to be tested. If not provided, all interfaces (excluding any in `ignored_interfaces`) are tested."""
        ignored_interfaces: list[InterfaceType | Interface] | None = None
        """A list of interfaces or interface types like Ethernet which will ignore all Ethernet interfaces."""

    @AntaTest.anta_test
    def test(self) -> None:
        """Main test function for VerifySTPCounters."""
        self.result.is_success()
        command_output = self.instance_commands[0].json_output
        interfaces = self.inputs.interfaces if self.inputs.interfaces else command_output["interfaces"].keys()

        for interface in interfaces:
            # Verification is skipped if the interface is in the ignored interfaces list.
            if is_interface_ignored(interface, self.inputs.ignored_interfaces):
                continue

            # Atomic result
            result = self.result.add(description=f"Interface: {interface}", status=AntaTestStatus.SUCCESS)

            # If specified interface is not configured, test fails
            if (counters := get_value(command_output, f"interfaces..{interface}", separator="..")) is None:
                result.is_failure("Not found")
                continue

            if counters["bpduTaggedError"] != 0:
                result.is_failure(f"STP BPDU packet tagged errors count mismatch - Expected: 0 Actual: {counters['bpduTaggedError']}")
            if counters["bpduOtherError"] != 0:
                result.is_failure(f"STP BPDU packet other errors count mismatch - Expected: 0 Actual: {counters['bpduOtherError']}")


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

    description = "Verifies that all interfaces are forwarding for a provided list of VLAN(s)."
    categories: ClassVar[list[str]] = ["stp"]
    commands: ClassVar[list[AntaCommand | AntaTemplate]] = [AntaTemplate(template="show spanning-tree topology vlan {vlan} status", revision=1)]

    class Input(AntaTest.Input):
        """Input model for the VerifySTPForwardingPorts test."""

        vlans: list[VlanId]
        """List of VLAN on which to verify forwarding states."""

    def render(self, template: AntaTemplate) -> list[AntaCommand]:
        """Render the template for each VLAN in the input list."""
        return [template.render(vlan=vlan) for vlan in self.inputs.vlans]

    @AntaTest.anta_test
    def test(self) -> None:
        """Main test function for VerifySTPForwardingPorts."""
        self.result.is_success()
        interfaces_state = []
        for command in self.instance_commands:
            vlan_id = command.params.vlan
            if not (topologies := get_value(command.json_output, "topologies")):
                self.result.is_failure(f"VLAN {vlan_id} - STP instance is not configured")
                continue
            for value in topologies.values():
                if vlan_id and int(vlan_id) in value["vlans"]:
                    interfaces_state = [
                        (interface, actual_state) for interface, state in value["interfaces"].items() if (actual_state := state["state"]) != "forwarding"
                    ]

            if interfaces_state:
                for interface, state in interfaces_state:
                    self.result.is_failure(f"VLAN {vlan_id} Interface: {interface} - Invalid state - Expected: forwarding Actual: {state}")


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

    categories: ClassVar[list[str]] = ["stp"]
    commands: ClassVar[list[AntaCommand | AntaTemplate]] = [AntaCommand(command="show spanning-tree root detail", revision=1)]

    class Input(AntaTest.Input):
        """Input model for the VerifySTPRootPriority test."""

        priority: int
        """STP root priority to verify."""
        instances: list[VlanId] = Field(default=[])
        """List of VLAN or MST instance ID(s). If empty, ALL VLAN or MST instance ID(s) will be verified."""

    @AntaTest.anta_test
    def test(self) -> None:
        """Main test function for VerifySTPRootPriority."""
        self.result.is_success()
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
            self.result.is_failure(f"STP Instance: {first_name} - Unsupported STP instance type")
            return
        check_instances = [f"{prefix}{instance_id}" for instance_id in self.inputs.instances] if self.inputs.instances else command_output["instances"].keys()
        for instance in check_instances:
            if not (instance_details := get_value(command_output, f"instances.{instance}")):
                self.result.is_failure(f"Instance: {instance} - Not configured")
                continue
            if (priority := get_value(instance_details, "rootBridge.priority")) != self.inputs.priority:
                self.result.is_failure(f"STP Instance: {instance} - Incorrect root priority - Expected: {self.inputs.priority} Actual: {priority}")


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

    categories: ClassVar[list[str]] = ["stp"]
    commands: ClassVar[list[AntaCommand | AntaTemplate]] = [AntaCommand(command="show spanning-tree topology status detail", revision=1)]

    class Input(AntaTest.Input):
        """Input model for the VerifyStpTopologyChanges test."""

        threshold: int
        """The threshold number of changes in the STP topology."""

    @AntaTest.anta_test
    def test(self) -> None:
        """Main test function for VerifyStpTopologyChanges."""
        self.result.is_success()
        command_output = self.instance_commands[0].json_output
        stp_topologies = command_output.get("topologies", {})

        # verifies all available topologies except the "NoStp" topology.
        stp_topologies.pop("NoStp", None)

        # Verify the STP topology(s).
        if not stp_topologies:
            self.result.is_failure("STP is not configured")
            return

        # Verifies the number of changes across all interfaces
        for topology, topology_details in stp_topologies.items():
            for interface, details in topology_details.get("interfaces", {}).items():
                if (num_of_changes := details.get("numChanges")) > self.inputs.threshold:
                    self.result.is_failure(
                        f"Topology: {topology} Interface: {interface} - Number of changes not within the threshold - Expected: "
                        f"{self.inputs.threshold} Actual: {num_of_changes}"
                    )


class VerifySTPDisabledVlans(AntaTest):
    """Verifies the STP disabled VLAN(s).

    This test performs the following checks:

      1. Verifies that the STP is configured.
      2. Verifies that the specified VLAN(s) exist on the device.
      3. Verifies that the STP is disabled for the specified VLAN(s).

    Expected Results
    ----------------
    * Success: The test will pass if all of the following conditions are met:
        - STP is properly configured on the device.
        - The specified VLAN(s) exist on the device.
        - STP is confirmed to be disabled for all the specified VLAN(s).
    * Failure: The test will fail if any of the following condition is met:
        - STP is not configured on the device.
        - The specified VLAN(s) do not exist on the device.
        - STP is enabled for any of the specified VLAN(s).

    Examples
    --------
    ```yaml
    anta.tests.stp:
      - VerifySTPDisabledVlans:
            vlans:
              - 6
              - 4094
    ```
    """

    categories: ClassVar[list[str]] = ["stp"]
    commands: ClassVar[list[AntaCommand | AntaTemplate]] = [AntaCommand(command="show spanning-tree vlan detail", revision=1)]

    class Input(AntaTest.Input):
        """Input model for the VerifySTPDisabledVlans test."""

        vlans: list[VlanId]
        """List of STP disabled VLAN(s)."""

    @AntaTest.anta_test
    def test(self) -> None:
        """Main test function for VerifySTPDisabledVlans."""
        self.result.is_success()

        command_output = self.instance_commands[0].json_output
        stp_vlan_instances = command_output.get("spanningTreeVlanInstances", {})

        # If the spanningTreeVlanInstances detail are not found in the command output, the test fails.
        if not stp_vlan_instances:
            self.result.is_failure("STP is not configured")
            return

        actual_vlans = list(stp_vlan_instances)
        # If the specified VLAN is not present on the device, STP is enabled for the VLAN(s), test fails.
        for vlan in self.inputs.vlans:
            if str(vlan) not in actual_vlans:
                self.result.is_failure(f"VLAN: {vlan} - Not configured")
                continue

            if stp_vlan_instances.get(str(vlan)):
                self.result.is_failure(f"VLAN: {vlan} - STP is enabled")
