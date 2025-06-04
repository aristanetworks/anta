# Copyright (c) 2023-2025 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Module related to the device interfaces tests."""

# Mypy does not understand AntaTest.Input typing
# mypy: disable-error-code=attr-defined
from __future__ import annotations

from typing import Any, ClassVar, TypeVar

from pydantic import Field, field_validator
from pydantic_extra_types.mac_address import MacAddress

from anta.custom_types import Interface, InterfaceType, Percent, PortChannelInterface, PositiveInteger
from anta.decorators import skip_on_platforms
from anta.input_models.interfaces import InterfaceDetail, InterfaceState
from anta.models import AntaCommand, AntaTemplate, AntaTest
from anta.tools import custom_division, get_item, get_value, is_interface_ignored

BPS_GBPS_CONVERSIONS = 1000000000

# Using a TypeVar for the InterfaceState model since mypy thinks it's a ClassVar and not a valid type when used in field validators
T = TypeVar("T", bound=InterfaceState)


class VerifyInterfaceUtilization(AntaTest):
    """Verifies that the utilization of interfaces is below a certain threshold.

    Load interval (default to 5 minutes) is defined in device configuration.

    !!! warning
        This test has been implemented for full-duplex interfaces only.

    Expected Results
    ----------------
    * Success: The test will pass if all or specified interfaces are full duplex and have a usage below the threshold.
    * Failure: The test will fail if any interface is non full-duplex or has a usage above the threshold.

    Examples
    --------
    ```yaml
    anta.tests.interfaces:
      - VerifyInterfaceUtilization:
          threshold: 70.0
          ignored_interfaces:
            - Ethernet1
            - Port-Channel1
          interfaces:
            - Ethernet10
            - Loopback0
    ```
    """

    categories: ClassVar[list[str]] = ["interfaces"]
    commands: ClassVar[list[AntaCommand | AntaTemplate]] = [
        AntaCommand(command="show interfaces counters rates", revision=1),
        AntaCommand(command="show interfaces status", revision=1),
    ]

    class Input(AntaTest.Input):
        """Input model for the VerifyInterfaceUtilization test."""

        threshold: Percent = 75.0
        """Interface utilization threshold above which the test will fail."""
        interfaces: list[Interface] | None = None
        """A list of interfaces to be tested. If not provided, all interfaces (excluding any in `ignored_interfaces`) are tested."""
        ignored_interfaces: list[InterfaceType | Interface] | None = None
        """A list of interfaces or interface types like Management which will ignore all Management interfaces."""

    @AntaTest.anta_test
    def test(self) -> None:
        """Main test function for VerifyInterfaceUtilization."""
        self.result.is_success()

        interfaces_counters_rates = self.instance_commands[0].json_output
        interfaces_status = self.instance_commands[1].json_output

        test_has_input_interfaces = bool(self.inputs.interfaces)
        interfaces_to_check = self.inputs.interfaces if test_has_input_interfaces else interfaces_counters_rates["interfaces"].keys()

        for intf in interfaces_to_check:
            # Verification is skipped if the interface is in the ignored interfaces list
            if is_interface_ignored(intf, self.inputs.ignored_interfaces):
                continue

            # If specified interface is not configured, test fails
            intf_counters = get_value(interfaces_counters_rates, f"interfaces..{intf}", separator="..")
            intf_status = get_value(interfaces_status, f"interfaceStatuses..{intf}", separator="..")
            if intf_counters is None or intf_status is None:
                self.result.is_failure(f"Interface: {intf} - Not found")
                continue

            # The utilization logic has been implemented for full-duplex interfaces only
            if (intf_duplex := intf_status["duplex"]) != "duplexFull":
                self.result.is_failure(f"Interface: {intf} - Test not implemented for non-full-duplex interfaces - Expected: duplexFull Actual: {intf_duplex}")
                continue

            if (intf_bandwidth := intf_status["bandwidth"]) == 0:
                if test_has_input_interfaces:
                    # Test fails on user-provided interfaces
                    self.result.is_failure(f"Interface: {intf} - Cannot get interface utilization due to null bandwidth value")
                else:
                    self.logger.debug("Interface %s has been ignored due to null bandwidth value", intf)
                continue

            # If one or more interfaces have a usage above the threshold, test fails
            for bps_rate in ("inBpsRate", "outBpsRate"):
                usage = intf_counters[bps_rate] / intf_bandwidth * 100
                if usage > self.inputs.threshold:
                    self.result.is_failure(
                        f"Interface: {intf} BPS Rate: {bps_rate} - Usage exceeds the threshold - Expected: <{self.inputs.threshold}% Actual: {usage}%"
                    )


class VerifyInterfaceErrors(AntaTest):
    """Verifies that the interfaces error counters are equal to zero.

    Expected Results
    ----------------
    * Success: The test will pass if all interfaces have error counters equal to zero.
    * Failure: The test will fail if one or more interfaces have non-zero error counters.

    Examples
    --------
    ```yaml
    anta.tests.interfaces:
      - VerifyInterfaceErrors:
    ```
    """

    categories: ClassVar[list[str]] = ["interfaces"]
    commands: ClassVar[list[AntaCommand | AntaTemplate]] = [AntaCommand(command="show interfaces counters errors", revision=1)]

    class Input(AntaTest.Input):
        """Input model for the VerifyInterfaceErrors test."""

        interfaces: list[Interface] | None = None
        """A list of interfaces to be tested. If not provided, all interfaces (excluding any in `ignored_interfaces`) are tested."""
        ignored_interfaces: list[InterfaceType | Interface] | None = None
        """A list of interfaces or interface types like Management which will ignore all Management interfaces."""

    @AntaTest.anta_test
    def test(self) -> None:
        """Main test function for VerifyInterfaceErrors."""
        self.result.is_success()
        command_output = self.instance_commands[0].json_output
        interfaces = self.inputs.interfaces if self.inputs.interfaces else command_output["interfaceErrorCounters"].keys()
        for interface in interfaces:
            # Verification is skipped if the interface is in the ignored interfaces list.
            if is_interface_ignored(interface, self.inputs.ignored_interfaces):
                continue

            # If specified interface is not configured, test fails
            if (intf_counters := get_value(command_output, f"interfaceErrorCounters..{interface}", separator="..")) is None:
                self.result.is_failure(f"Interface: {interface} - Not found")
                continue

            counters_data = [f"{counter}: {value}" for counter, value in intf_counters.items() if value > 0]
            if counters_data:
                self.result.is_failure(f"Interface: {interface} - Non-zero error counter(s) - {', '.join(counters_data)}")


class VerifyInterfaceDiscards(AntaTest):
    """Verifies that the interfaces packet discard counters are equal to zero.

    Expected Results
    ----------------
    * Success: The test will pass if all or specified interfaces have discard counters equal to zero.
    * Failure: The test will fail if one or more interfaces have non-zero discard counters.

    Examples
    --------
    ```yaml
    anta.tests.interfaces:
      - VerifyInterfaceDiscards:
          interfaces:
            - Ethernet
            - Port-Channel1
          ignored_interfaces:
            - Vxlan1
            - Loopback0
    ```
    """

    categories: ClassVar[list[str]] = ["interfaces"]
    commands: ClassVar[list[AntaCommand | AntaTemplate]] = [AntaCommand(command="show interfaces counters discards", revision=1)]

    class Input(AntaTest.Input):
        """Input model for the VerifyInterfaceDiscards test."""

        interfaces: list[Interface] | None = None
        """A list of interfaces to be tested. If not provided, all interfaces (excluding any in `ignored_interfaces`) are tested."""
        ignored_interfaces: list[InterfaceType | Interface] | None = None
        """A list of interfaces or interface types like Management which will ignore all Management interfaces."""

    @AntaTest.anta_test
    def test(self) -> None:
        """Main test function for VerifyInterfaceDiscards."""
        self.result.is_success()
        command_output = self.instance_commands[0].json_output
        interfaces = self.inputs.interfaces if self.inputs.interfaces else command_output["interfaces"].keys()

        for interface in interfaces:
            # Verification is skipped if the interface is in the ignored interfaces list.
            if is_interface_ignored(interface, self.inputs.ignored_interfaces):
                continue

            # If specified interface is not configured, test fails
            if (intf_details := get_value(command_output, f"interfaces..{interface}", separator="..")) is None:
                self.result.is_failure(f"Interface: {interface} - Not found")
                continue

            counters_data = [f"{counter}: {value}" for counter, value in intf_details.items() if value > 0]
            if counters_data:
                self.result.is_failure(f"Interface: {interface} - Non-zero discard counter(s): {', '.join(counters_data)}")


class VerifyInterfaceErrDisabled(AntaTest):
    """Verifies there are no interfaces in the errdisabled state.

    Expected Results
    ----------------
    * Success: The test will pass if there are no interfaces in the errdisabled state.
    * Failure: The test will fail if there is at least one interface in the errdisabled state.

    Examples
    --------
    ```yaml
    anta.tests.interfaces:
      - VerifyInterfaceErrDisabled:
    ```
    """

    categories: ClassVar[list[str]] = ["interfaces"]
    commands: ClassVar[list[AntaCommand | AntaTemplate]] = [AntaCommand(command="show interfaces status errdisabled", revision=1)]

    @AntaTest.anta_test
    def test(self) -> None:
        """Main test function for VerifyInterfaceErrDisabled."""
        self.result.is_success()
        command_output = self.instance_commands[0].json_output
        if not (interface_details := get_value(command_output, "interfaceStatuses")):
            return

        for interface, value in interface_details.items():
            if causes := value.get("causes"):
                msg = f"Interface: {interface} - Error disabled - Causes: {', '.join(causes)}"
                self.result.is_failure(msg)
                continue
            self.result.is_failure(f"Interface: {interface} - Error disabled")


class VerifyInterfacesStatus(AntaTest):
    """Verifies the operational states of specified interfaces to ensure they match expected configurations.

    This test performs the following checks for each specified interface:

      1. If `line_protocol_status` is defined, both `status` and `line_protocol_status` are verified for the specified interface.
      2. If `line_protocol_status` is not provided but the `status` is "up", it is assumed that both the status and line protocol should be "up".
      3. If the interface `status` is not "up", only the interface's status is validated, with no line protocol check performed.

    Expected Results
    ----------------
    * Success: If the interface status and line protocol status matches the expected operational state for all specified interfaces.
    * Failure: If any of the following occur:
        - The specified interface is not configured.
        - The specified interface status and line protocol status does not match the expected operational state for any interface.

    Examples
    --------
    ```yaml
    anta.tests.interfaces:
      - VerifyInterfacesStatus:
          interfaces:
            - name: Ethernet1
              status: up
            - name: Port-Channel100
              status: down
              line_protocol_status: lowerLayerDown
            - name: Ethernet49/1
              status: adminDown
              line_protocol_status: notPresent
    ```
    """

    categories: ClassVar[list[str]] = ["interfaces"]
    commands: ClassVar[list[AntaCommand | AntaTemplate]] = [AntaCommand(command="show interfaces description", revision=1)]

    class Input(AntaTest.Input):
        """Input model for the VerifyInterfacesStatus test."""

        interfaces: list[InterfaceState]
        """List of interfaces with their expected state."""
        InterfaceState: ClassVar[type[InterfaceState]] = InterfaceState

        @field_validator("interfaces")
        @classmethod
        def validate_interfaces(cls, interfaces: list[T]) -> list[T]:
            """Validate that 'status' field is provided in each interface."""
            for interface in interfaces:
                if interface.status is None:
                    msg = f"{interface} 'status' field missing in the input"
                    raise ValueError(msg)
            return interfaces

    @AntaTest.anta_test
    def test(self) -> None:
        """Main test function for VerifyInterfacesStatus."""
        self.result.is_success()

        command_output = self.instance_commands[0].json_output
        for interface in self.inputs.interfaces:
            if (intf_status := get_value(command_output["interfaceDescriptions"], interface.name, separator="..")) is None:
                self.result.is_failure(f"{interface.name} - Not configured")
                continue

            status = "up" if intf_status["interfaceStatus"] in {"up", "connected"} else intf_status["interfaceStatus"]
            proto = "up" if intf_status["lineProtocolStatus"] in {"up", "connected"} else intf_status["lineProtocolStatus"]

            # If line protocol status is provided, prioritize checking against both status and line protocol status
            if interface.line_protocol_status:
                if any([interface.status != status, interface.line_protocol_status != proto]):
                    actual_state = f"Expected: {interface.status}/{interface.line_protocol_status}, Actual: {status}/{proto}"
                    self.result.is_failure(f"{interface.name} - Status mismatch - {actual_state}")

            # If line protocol status is not provided and interface status is "up", expect both status and proto to be "up"
            # If interface status is not "up", check only the interface status without considering line protocol status
            elif all([interface.status == "up", status != "up" or proto != "up"]):
                self.result.is_failure(f"{interface.name} - Status mismatch - Expected: up/up, Actual: {status}/{proto}")
            elif interface.status != status:
                self.result.is_failure(f"{interface.name} - Status mismatch - Expected: {interface.status}, Actual: {status}")


class VerifyStormControlDrops(AntaTest):
    """Verifies there are no interface storm-control drop counters.

    Expected Results
    ----------------
    * Success: The test will pass if there are no storm-control drop counters.
    * Failure: The test will fail if there is at least one storm-control drop counter.

    Examples
    --------
    ```yaml
    anta.tests.interfaces:
      - VerifyStormControlDrops:
          interfaces:
            - Ethernet1
            - Ethernet2
          ignored_interfaces:
            - Vxlan1
            - Loopback0
    ```
    """

    categories: ClassVar[list[str]] = ["interfaces"]
    commands: ClassVar[list[AntaCommand | AntaTemplate]] = [AntaCommand(command="show storm-control", revision=1)]

    class Input(AntaTest.Input):
        """Input model for the VerifyStormControlDrops test."""

        interfaces: list[Interface] | None = None
        """A list of interfaces to be tested. If not provided, all interfaces (excluding any in `ignored_interfaces`) are tested."""
        ignored_interfaces: list[InterfaceType | Interface] | None = None
        """A list of interfaces or interface types like Management which will ignore all Management interfaces."""

    @skip_on_platforms(["cEOSLab", "vEOS-lab", "cEOSCloudLab", "vEOS"])
    @AntaTest.anta_test
    def test(self) -> None:
        """Main test function for VerifyStormControlDrops."""
        command_output = self.instance_commands[0].json_output
        self.result.is_success()
        interfaces = self.inputs.interfaces if self.inputs.interfaces else command_output["interfaces"].keys()

        for interface in interfaces:
            # Verification is skipped if the interface is in the ignored interfaces list.
            if is_interface_ignored(interface, self.inputs.ignored_interfaces):
                continue

            # If specified interface is not configured, test fails
            if (intf_details := get_value(command_output, f"interfaces..{interface}", separator="..")) is None:
                self.result.is_failure(f"Interface: {interface} - Not found")
                continue

            for traffic_type, traffic_type_dict in intf_details["trafficTypes"].items():
                if "drop" in traffic_type_dict and traffic_type_dict["drop"] != 0:
                    storm_controlled_interfaces = f"{traffic_type}: {traffic_type_dict['drop']}"
                    self.result.is_failure(f"Interface: {interface} - Non-zero storm-control drop counter(s) - {storm_controlled_interfaces}")


class VerifyPortChannels(AntaTest):
    """Verifies there are no inactive ports in port channels.

    Expected Results
    ----------------
    * Success: The test will pass if there are no inactive ports in all or specified port channels.
    * Failure: The test will fail if there is at least one inactive port in a port channel.

    Examples
    --------
    ```yaml
    anta.tests.interfaces:
      - VerifyPortChannels:
          ignored_interfaces:
            - Port-Channel1
            - Port-Channel2
          interfaces:
            - Port-Channel11
            - Port-Channel22
    ```
    """

    categories: ClassVar[list[str]] = ["interfaces"]
    commands: ClassVar[list[AntaCommand | AntaTemplate]] = [AntaCommand(command="show port-channel", revision=1)]

    class Input(AntaTest.Input):
        """Input model for the VerifyPortChannels test."""

        interfaces: list[PortChannelInterface] | None = None
        """A list of port-channel interfaces to be tested. If not provided, all port-channel interfaces (excluding any in `ignored_interfaces`) are tested."""
        ignored_interfaces: list[PortChannelInterface] | None = None
        """A list of port-channel interfaces to ignore."""

    @AntaTest.anta_test
    def test(self) -> None:
        """Main test function for VerifyPortChannels."""
        self.result.is_success()
        command_output = self.instance_commands[0].json_output
        port_channels = self.inputs.interfaces if self.inputs.interfaces else command_output["portChannels"].keys()

        for port_channel in port_channels:
            # Verification is skipped if the interface is in the ignored interfaces list.
            if is_interface_ignored(port_channel, self.inputs.ignored_interfaces):
                continue

            # If specified interface is not configured, test fails
            if (port_channel_details := get_value(command_output, f"portChannels..{port_channel}", separator="..")) is None:
                self.result.is_failure(f"Interface: {port_channel} - Not found")
                continue

            # Verify that the no inactive ports in all port channels.
            if inactive_ports := port_channel_details["inactivePorts"]:
                self.result.is_failure(f"{port_channel} - Inactive port(s) - {', '.join(inactive_ports.keys())}")


class VerifyIllegalLACP(AntaTest):
    """Verifies there are no illegal LACP packets in port channels.

    Expected Results
    ----------------
    * Success: The test will pass if there are no illegal LACP packets received.
    * Failure: The test will fail if there is at least one illegal LACP packet received.

    Examples
    --------
    ```yaml
    anta.tests.interfaces:
      - VerifyIllegalLACP:
          ignored_interfaces:
            - Port-Channel1
            - Port-Channel2
          interfaces:
            - Port-Channel10
            - Port-Channel12
    ```
    """

    categories: ClassVar[list[str]] = ["interfaces"]
    commands: ClassVar[list[AntaCommand | AntaTemplate]] = [AntaCommand(command="show lacp counters all-ports", revision=1)]

    class Input(AntaTest.Input):
        """Input model for the VerifyIllegalLACP test."""

        interfaces: list[PortChannelInterface] | None = None
        """A list of port-channel interfaces to be tested. If not provided, all port-channel interfaces (excluding any in `ignored_interfaces`) are tested."""
        ignored_interfaces: list[PortChannelInterface] | None = None
        """A list of port-channel interfaces to ignore."""

    @AntaTest.anta_test
    def test(self) -> None:
        """Main test function for VerifyIllegalLACP."""
        self.result.is_success()
        command_output = self.instance_commands[0].json_output
        port_channels = self.inputs.interfaces if self.inputs.interfaces else command_output["portChannels"].keys()

        for port_channel in port_channels:
            # Verification is skipped if the interface is in the ignored interfaces list.
            if is_interface_ignored(port_channel, self.inputs.ignored_interfaces):
                continue

            # If specified port-channel is not configured, test fails
            if (port_channel_details := get_value(command_output, f"portChannels..{port_channel}", separator="..")) is None:
                self.result.is_failure(f"Interface: {port_channel} - Not found")
                continue

            for interface, interface_details in port_channel_details["interfaces"].items():
                # Verify that the no illegal LACP packets in all port channels.
                if interface_details["illegalRxCount"] != 0:
                    self.result.is_failure(f"{port_channel} Interface: {interface} - Illegal LACP packets found")


class VerifyLoopbackCount(AntaTest):
    """Verifies that the device has the expected number of loopback interfaces and all are operational.

    Expected Results
    ----------------
    * Success: The test will pass if the device has the correct number of loopback interfaces and none are down.
    * Failure: The test will fail if the loopback interface count is incorrect or any are non-operational.

    Examples
    --------
    ```yaml
    anta.tests.interfaces:
      - VerifyLoopbackCount:
          number: 3
    ```
    """

    description = "Verifies the number of loopback interfaces and their status."
    categories: ClassVar[list[str]] = ["interfaces"]
    commands: ClassVar[list[AntaCommand | AntaTemplate]] = [AntaCommand(command="show ip interface brief", revision=1)]

    class Input(AntaTest.Input):
        """Input model for the VerifyLoopbackCount test."""

        number: PositiveInteger
        """Number of loopback interfaces expected to be present."""

    @AntaTest.anta_test
    def test(self) -> None:
        """Main test function for VerifyLoopbackCount."""
        self.result.is_success()
        command_output = self.instance_commands[0].json_output
        loopback_count = 0
        for interface, interface_details in command_output["interfaces"].items():
            if "Loopback" in interface:
                loopback_count += 1
                if (status := interface_details["lineProtocolStatus"]) != "up":
                    self.result.is_failure(f"Interface: {interface} - Invalid line protocol status - Expected: up Actual: {status}")

                if (status := interface_details["interfaceStatus"]) != "connected":
                    self.result.is_failure(f"Interface: {interface} - Invalid interface status - Expected: connected Actual: {status}")

        if loopback_count != self.inputs.number:
            self.result.is_failure(f"Loopback interface(s) count mismatch: Expected {self.inputs.number} Actual: {loopback_count}")


class VerifySVI(AntaTest):
    """Verifies the status of all SVIs.

    Expected Results
    ----------------
    * Success: The test will pass if all SVIs are up.
    * Failure: The test will fail if one or many SVIs are not up.

    Examples
    --------
    ```yaml
    anta.tests.interfaces:
      - VerifySVI:
    ```
    """

    categories: ClassVar[list[str]] = ["interfaces"]
    commands: ClassVar[list[AntaCommand | AntaTemplate]] = [AntaCommand(command="show ip interface brief", revision=1)]

    @AntaTest.anta_test
    def test(self) -> None:
        """Main test function for VerifySVI."""
        self.result.is_success()
        command_output = self.instance_commands[0].json_output
        for interface, int_data in command_output["interfaces"].items():
            if "Vlan" in interface and (status := int_data["lineProtocolStatus"]) != "up":
                self.result.is_failure(f"SVI: {interface} - Invalid line protocol status - Expected: up Actual: {status}")
            if "Vlan" in interface and int_data["interfaceStatus"] != "connected":
                self.result.is_failure(f"SVI: {interface} - Invalid interface status - Expected: connected Actual: {int_data['interfaceStatus']}")


class VerifyL3MTU(AntaTest):
    """Verifies the L3 MTU of routed interfaces.

    Test that layer 3 (routed) interfaces are configured with the correct MTU.

    Expected Results
    ----------------
    * Success: The test will pass if all layer 3 interfaces have the proper MTU configured.
    * Failure: The test will fail if one or many layer 3 interfaces have the wrong MTU configured.

    Examples
    --------
    ```yaml
    anta.tests.interfaces:
      - VerifyL3MTU:
          mtu: 1500
          ignored_interfaces:
              - Management  # Ignore all Management interfaces
              - Ethernet2.100
              - Ethernet1/1
          specific_mtu:
              - Ethernet10: 9200
    ```
    """

    description = "Verifies the global L3 MTU of all L3 interfaces."
    categories: ClassVar[list[str]] = ["interfaces"]
    commands: ClassVar[list[AntaCommand | AntaTemplate]] = [AntaCommand(command="show interfaces", revision=1)]

    class Input(AntaTest.Input):
        """Input model for the VerifyL3MTU test."""

        mtu: int = 1500
        """Expected L3 MTU configured on all non-excluded interfaces."""
        ignored_interfaces: list[InterfaceType | Interface] = Field(default=["Dps", "Fabric", "Loopback", "Management", "Recirc-Channel", "Tunnel", "Vxlan"])
        """A list of L3 interfaces or interfaces types like Loopback, Tunnel which will ignore all Loopback and Tunnel interfaces.

        Takes precedence over the `specific_mtu` field."""
        specific_mtu: list[dict[Interface, int]] = Field(default=[])
        """A list of dictionary of L3 interfaces with their expected L3 MTU configured."""

    @AntaTest.anta_test
    def test(self) -> None:
        """Main test function for VerifyL3MTU."""
        self.result.is_success()
        command_output = self.instance_commands[0].json_output
        specific_interfaces = {intf: mtu for intf_mtu in self.inputs.specific_mtu for intf, mtu in intf_mtu.items()}

        for interface, details in command_output["interfaces"].items():
            # Verification is skipped if the interface is in the ignored interfaces list
            if is_interface_ignored(interface, self.inputs.ignored_interfaces) or details["forwardingModel"] != "routed":
                continue

            actual_mtu = details["mtu"]
            expected_mtu = specific_interfaces.get(interface, self.inputs.mtu)

            if (actual_mtu := details["mtu"]) != expected_mtu:
                self.result.is_failure(f"Interface: {interface} - Incorrect MTU - Expected: {expected_mtu} Actual: {actual_mtu}")


class VerifyIPProxyARP(AntaTest):
    """Verifies if Proxy ARP is enabled.

    Expected Results
    ----------------
    * Success: The test will pass if Proxy-ARP is enabled on the specified interface(s).
    * Failure: The test will fail if Proxy-ARP is disabled on the specified interface(s).

    Examples
    --------
    ```yaml
    anta.tests.interfaces:
      - VerifyIPProxyARP:
          interfaces:
            - Ethernet1
            - Ethernet2
    ```
    """

    categories: ClassVar[list[str]] = ["interfaces"]
    commands: ClassVar[list[AntaCommand | AntaTemplate]] = [AntaCommand(command="show ip interface", revision=2)]

    class Input(AntaTest.Input):
        """Input model for the VerifyIPProxyARP test."""

        interfaces: list[Interface]
        """List of interfaces to be tested."""

    @AntaTest.anta_test
    def test(self) -> None:
        """Main test function for VerifyIPProxyARP."""
        self.result.is_success()
        command_output = self.instance_commands[0].json_output

        for interface in self.inputs.interfaces:
            if (interface_detail := get_value(command_output, f"interfaces..{interface}", separator="..")) is None:
                self.result.is_failure(f"Interface: {interface} - Not found")
                continue

            if not interface_detail["proxyArp"]:
                self.result.is_failure(f"Interface: {interface} - Proxy-ARP disabled")


class VerifyL2MTU(AntaTest):
    """Verifies the L2 MTU of bridged interfaces.

    Test that layer 2 (bridged) interfaces are configured with the correct MTU.

    Expected Results
    ----------------
    * Success: The test will pass if all layer 2 interfaces have the proper MTU configured.
    * Failure: The test will fail if one or many layer 2 interfaces have the wrong MTU configured.

    Examples
    --------
    ```yaml
    anta.tests.interfaces:
      - VerifyL2MTU:
          mtu: 9214
          ignored_interfaces:
            - Ethernet2/1
            - Port-Channel  # Ignore all Port-Channel interfaces
          specific_mtu:
            - Ethernet1/1: 1500
    ```
    """

    description = "Verifies the global L2 MTU of all L2 interfaces."
    categories: ClassVar[list[str]] = ["interfaces"]
    commands: ClassVar[list[AntaCommand | AntaTemplate]] = [AntaCommand(command="show interfaces", revision=1)]

    class Input(AntaTest.Input):
        """Input model for the VerifyL2MTU test."""

        mtu: int = 9214
        """Expected L2 MTU configured on all non-excluded interfaces."""
        ignored_interfaces: list[InterfaceType | Interface] = Field(default=["Dps", "Fabric", "Loopback", "Management", "Recirc-Channel", "Tunnel", "Vlan", "Vxlan"])
        """A list of L2 interfaces or interface types like Ethernet, Port-Channel which will ignore all Ethernet and Port-Channel interfaces.

        Takes precedence over the `specific_mtu` field."""
        specific_mtu: list[dict[Interface, int]] = Field(default=[])
        """A list of dictionary of L2 interfaces with their expected L2 MTU configured."""

    @AntaTest.anta_test
    def test(self) -> None:
        """Main test function for VerifyL2MTU."""
        self.result.is_success()
        interface_output = self.instance_commands[0].json_output["interfaces"]
        specific_interfaces = {intf: mtu for intf_mtu in self.inputs.specific_mtu for intf, mtu in intf_mtu.items()}

        for interface, details in interface_output.items():
            # Verification is skipped if the interface is in the ignored interfaces list
            if is_interface_ignored(interface, self.inputs.ignored_interfaces) or details["forwardingModel"] != "bridged":
                continue

            actual_mtu = details["mtu"]
            expected_mtu = specific_interfaces.get(interface, self.inputs.mtu)

            if (actual_mtu := details["mtu"]) != expected_mtu:
                self.result.is_failure(f"Interface: {interface} - Incorrect MTU - Expected: {expected_mtu} Actual: {actual_mtu}")


class VerifyInterfaceIPv4(AntaTest):
    """Verifies the interface IPv4 addresses.

    Expected Results
    ----------------
    * Success: The test will pass if an interface is configured with a correct primary and secondary IPv4 address.
    * Failure: The test will fail if an interface is not found or the primary and secondary IPv4 addresses do not match with the input.

    Examples
    --------
    ```yaml
    anta.tests.interfaces:
      - VerifyInterfaceIPv4:
          interfaces:
            - name: Ethernet2
              primary_ip: 172.30.11.1/31
              secondary_ips:
                - 10.10.10.1/31
                - 10.10.10.10/31
    ```
    """

    categories: ClassVar[list[str]] = ["interfaces"]
    commands: ClassVar[list[AntaCommand | AntaTemplate]] = [AntaCommand(command="show ip interface", revision=2)]

    class Input(AntaTest.Input):
        """Input model for the VerifyInterfaceIPv4 test."""

        interfaces: list[InterfaceState]
        """List of interfaces with their details."""
        InterfaceDetail: ClassVar[type[InterfaceDetail]] = InterfaceDetail

        @field_validator("interfaces")
        @classmethod
        def validate_interfaces(cls, interfaces: list[T]) -> list[T]:
            """Validate that 'primary_ip' field is provided in each interface."""
            for interface in interfaces:
                if interface.primary_ip is None:
                    msg = f"{interface} 'primary_ip' field missing in the input"
                    raise ValueError(msg)
            return interfaces

    @AntaTest.anta_test
    def test(self) -> None:
        """Main test function for VerifyInterfaceIPv4."""
        self.result.is_success()
        command_output = self.instance_commands[0].json_output

        for interface in self.inputs.interfaces:
            if (interface_detail := get_value(command_output, f"interfaces..{interface.name}", separator="..")) is None:
                self.result.is_failure(f"{interface} - Not found")
                continue

            if (ip_address := get_value(interface_detail, "interfaceAddress.primaryIp")) is None:
                self.result.is_failure(f"{interface} - IP address is not configured")
                continue

            # Combine IP address and subnet for primary IP
            actual_primary_ip = f"{ip_address['address']}/{ip_address['maskLen']}"

            # Check if the primary IP address matches the input
            if actual_primary_ip != str(interface.primary_ip):
                self.result.is_failure(f"{interface} - IP address mismatch - Expected: {interface.primary_ip} Actual: {actual_primary_ip}")

            if interface.secondary_ips:
                if not (secondary_ips := get_value(interface_detail, "interfaceAddress.secondaryIpsOrderedList")):
                    self.result.is_failure(f"{interface} - Secondary IP address is not configured")
                    continue

                actual_secondary_ips = sorted([f"{secondary_ip['address']}/{secondary_ip['maskLen']}" for secondary_ip in secondary_ips])
                input_secondary_ips = sorted([str(ip) for ip in interface.secondary_ips])

                if actual_secondary_ips != input_secondary_ips:
                    self.result.is_failure(
                        f"{interface} - Secondary IP address mismatch - Expected: {', '.join(input_secondary_ips)} Actual: {', '.join(actual_secondary_ips)}"
                    )


class VerifyIpVirtualRouterMac(AntaTest):
    """Verifies the IP virtual router MAC address.

    Expected Results
    ----------------
    * Success: The test will pass if the IP virtual router MAC address matches the input.
    * Failure: The test will fail if the IP virtual router MAC address does not match the input.

    Examples
    --------
    ```yaml
    anta.tests.interfaces:
      - VerifyIpVirtualRouterMac:
          mac_address: 00:1c:73:00:dc:01
    ```
    """

    categories: ClassVar[list[str]] = ["interfaces"]
    commands: ClassVar[list[AntaCommand | AntaTemplate]] = [AntaCommand(command="show ip virtual-router", revision=2)]

    class Input(AntaTest.Input):
        """Input model for the VerifyIpVirtualRouterMac test."""

        mac_address: MacAddress
        """IP virtual router MAC address."""

    @AntaTest.anta_test
    def test(self) -> None:
        """Main test function for VerifyIpVirtualRouterMac."""
        self.result.is_success()
        command_output = self.instance_commands[0].json_output["virtualMacs"]
        if get_item(command_output, "macAddress", self.inputs.mac_address) is None:
            self.result.is_failure(f"IP virtual router MAC address: {self.inputs.mac_address} - Not configured")


class VerifyInterfacesSpeed(AntaTest):
    """Verifies the speed, lanes, auto-negotiation status, and mode as full duplex for interfaces.

    - If the auto-negotiation status is set to True, verifies that auto-negotiation is successful, the mode is full duplex and the speed/lanes match the input.
    - If the auto-negotiation status is set to False, verifies that the mode is full duplex and the speed/lanes match the input.

    Expected Results
    ----------------
    * Success: The test will pass if an interface is configured correctly with the specified speed, lanes, auto-negotiation status, and mode as full duplex.
    * Failure: The test will fail if an interface is not found, if the speed, lanes, and auto-negotiation status do not match the input, or mode is not full duplex.

    Examples
    --------
    ```yaml
    anta.tests.interfaces:
      - VerifyInterfacesSpeed:
          interfaces:
            - name: Ethernet2
              auto: False
              speed: 10
            - name: Eth3
              auto: True
              speed: 100
              lanes: 1
            - name: Eth2
              auto: False
              speed: 2.5
    ```
    """

    categories: ClassVar[list[str]] = ["interfaces"]
    commands: ClassVar[list[AntaCommand | AntaTemplate]] = [AntaCommand(command="show interfaces")]

    class Input(AntaTest.Input):
        """Inputs for the VerifyInterfacesSpeed test."""

        interfaces: list[InterfaceState]
        """List of interfaces with their expected state."""
        InterfaceDetail: ClassVar[type[InterfaceDetail]] = InterfaceDetail

        @field_validator("interfaces")
        @classmethod
        def validate_interfaces(cls, interfaces: list[T]) -> list[T]:
            """Validate that 'speed' field is provided in each interface."""
            for interface in interfaces:
                if interface.speed is None:
                    msg = f"{interface} 'speed' field missing in the input"
                    raise ValueError(msg)
            return interfaces

    @AntaTest.anta_test
    def test(self) -> None:
        """Main test function for VerifyInterfacesSpeed."""
        self.result.is_success()
        command_output = self.instance_commands[0].json_output

        # Iterate over all the interfaces
        for interface in self.inputs.interfaces:
            if (interface_detail := get_value(command_output, f"interfaces..{interface.name}", separator="..")) is None:
                self.result.is_failure(f"{interface} - Not found")
                continue

            # Verifies the bandwidth
            if (speed := interface_detail.get("bandwidth")) != interface.speed * BPS_GBPS_CONVERSIONS:
                self.result.is_failure(
                    f"{interface} - Bandwidth mismatch - Expected: {interface.speed}Gbps Actual: {custom_division(speed, BPS_GBPS_CONVERSIONS)}Gbps"
                )

            # Verifies the duplex mode
            if (duplex := interface_detail.get("duplex")) != "duplexFull":
                self.result.is_failure(f"{interface} - Duplex mode mismatch - Expected: duplexFull Actual: {duplex}")

            # Verifies the auto-negotiation as success if specified
            if interface.auto and (auto_negotiation := interface_detail.get("autoNegotiate")) != "success":
                self.result.is_failure(f"{interface} - Auto-negotiation mismatch - Expected: success Actual: {auto_negotiation}")

            # Verifies the communication lanes if specified
            if interface.lanes and (lanes := interface_detail.get("lanes")) != interface.lanes:
                self.result.is_failure(f"{interface} - Data lanes count mismatch - Expected: {interface.lanes} Actual: {lanes}")


class VerifyLACPInterfacesStatus(AntaTest):
    """Verifies the Link Aggregation Control Protocol (LACP) status of the interface.

    This test performs the following checks for each specified interface:

      1. Verifies that the interface is a member of the LACP port channel.
      2. Verifies LACP port states and operational status:
        - Activity: Active LACP mode (initiates)
        - Timeout: Short (Fast Mode), Long (Slow Mode - default)
        - Aggregation: Port aggregable
        - Synchronization: Port in sync with partner
        - Collecting: Incoming frames aggregating
        - Distributing: Outgoing frames aggregating

    Expected Results
    ----------------
    * Success: Interface is bundled and all LACP states match expected values for both actor and partner
    * Failure: If any of the following occur:
        - Interface or port channel is not configured.
        - Interface is not bundled in port channel.
        - Actor or partner port LACP states don't match expected configuration.
        - LACP rate (timeout) mismatch when fast mode is configured.

    Examples
    --------
    ```yaml
    anta.tests.interfaces:
      - VerifyLACPInterfacesStatus:
          interfaces:
            - name: Ethernet1
              portchannel: Port-Channel100
    ```
    """

    categories: ClassVar[list[str]] = ["interfaces"]
    commands: ClassVar[list[AntaCommand | AntaTemplate]] = [AntaCommand(command="show lacp interface detailed", revision=1)]

    class Input(AntaTest.Input):
        """Input model for the VerifyLACPInterfacesStatus test."""

        interfaces: list[InterfaceState]
        """List of interfaces with their expected state."""
        InterfaceState: ClassVar[type[InterfaceState]] = InterfaceState

        @field_validator("interfaces")
        @classmethod
        def validate_interfaces(cls, interfaces: list[T]) -> list[T]:
            """Validate that 'portchannel' field is provided in each interface."""
            for interface in interfaces:
                if interface.portchannel is None:
                    msg = f"{interface} 'portchannel' field missing in the input"
                    raise ValueError(msg)
            return interfaces

    def _verify_interface_churn_state(self, interface_input: InterfaceState, interface_output_data: dict[str, Any]) -> None:
        """Validate the partner and actor churn details for the given interface."""
        partner_churn_state = get_value(interface_output_data, "details.partnerChurnState")
        actor_churn_state = get_value(interface_output_data, "details.actorChurnState")

        # Verify the partner and actor churn state
        if partner_churn_state == "churnDetected" or actor_churn_state == "churnDetected":
            self.result.is_failure(f"{interface_input} - Churn detected (mismatch system ID)")

    def _is_interface_bundled(self, interface_input: InterfaceState, interface_output_data: dict[str, Any]) -> bool:
        """Validate the interface status is bundled."""
        # Verify the interface is bundled in its port-channel
        actor_port_status = interface_output_data.get("actorPortStatus")
        if actor_port_status != "bundled":
            self.result.is_failure(f"{interface_input} - Not bundled - Port Status: {actor_port_status}")
            return False
        return True

    def _verify_interface_actor_partner_states(self, interface_input: InterfaceState, interface_output_data: dict[str, Any]) -> None:
        """Validate the LACP actor, partner port states."""
        # Member port verification parameters
        member_port_details = ["activity", "aggregation", "synchronization", "collecting", "distributing", "timeout"]

        # Collecting actor and partner port details
        actor_port_details = interface_output_data.get("actorPortState", {})
        partner_port_details = interface_output_data.get("partnerPortState", {})

        # Forming expected interface details
        expected_details = {param: param != "timeout" for param in member_port_details}

        # Updating the short LACP timeout, if expected
        if interface_input.lacp_rate_fast:
            expected_details["timeout"] = True

        # Verify the actor port details
        for param, value in expected_details.items():
            if (act_param_value := actor_port_details.get(param)) != value:
                self.result.is_failure(f"{interface_input} - Actor port {param} state mismatch - Expected: {value} Actual: {act_param_value}")

        # Verify the partner port details
        for param, value in expected_details.items():
            if (part_param_value := partner_port_details.get(param)) != value:
                self.result.is_failure(f"{interface_input} - Partner port {param} state mismatch - Expected: {value} Actual: {part_param_value}")

    @AntaTest.anta_test
    def test(self) -> None:
        """Main test function for VerifyLACPInterfacesStatus."""
        self.result.is_success()

        command_output = self.instance_commands[0].json_output

        for interface in self.inputs.interfaces:
            # Verify if a port-channel is configured with the provided interface
            interface_details = get_value(command_output, f"portChannels..{interface.portchannel}..interfaces..{interface.name}", separator="..")

            if interface_details is None:
                self.result.is_failure(f"{interface} - Not configured")
                continue

            if not self._is_interface_bundled(interface, interface_details):
                continue

            # Verify the LACP actor, partner port states
            self._verify_interface_actor_partner_states(interface, interface_details)

            # Verify the actor churn and partner churn states
            if interface.lacp_churn_state:
                self._verify_interface_churn_state(interface, interface_details)


class VerifyInterfaceQueuDropsJericho(AntaTest):
    """Verifies the queue drop counters of interfaces.

    Compatible with EOS operating in `jericho` platform.

    Expected Results
    ----------------
    * Success: The test will pass if interfaces have queue drop counters less than or equal to the defined threshold.
    * Failure: The test will fail if any interface has a queue drop counter exceeding the threshold.

    Examples
    --------
    ```yaml
    anta.tests.interfaces:
      - VerifyInterfaceQueuDropsJericho:
          interfaces:
            - Et1
            - Et2
          traffic_classes:
            - TC0
            - TC3
          ignored_interfaces:
            - Ethernet
            - Port-Channel1
    ```
    """

    categories: ClassVar[list[str]] = ["interfaces"]
    commands: ClassVar[list[AntaCommand | AntaTemplate]] = [AntaCommand(command="show interfaces counters queue drops", revision=1)]

    class Input(AntaTest.Input):
        """Input model for the VerifyInterfaceQueuDropsJericho test."""

        traffic_classes: list[str] | None = None
        """List of traffic classes to be verified. If None, all available traffic classes will be checked."""
        interfaces: list[Interface] | None = None
        """A list of interfaces to be tested. If not provided, all interfaces (excluding any in `ignored_interfaces`) are tested."""
        ignored_interfaces: list[InterfaceType | Interface] | None = None
        """A list of interfaces or interface types like Management which will ignore all Management interfaces."""
        dropped_pckt_threshold: PositiveInteger = 0
        """Threshold for the number of dropped packets."""

    def _verify_traffic_class_details(self, interface: str, traffic_class: str, output: dict[str, Any], threshold: PositiveInteger) -> str | None:
        """Verify Egress & Ingress dropped packets for an input interface and traffic class."""
        if (class_detail := get_value(output["trafficClasses"], traffic_class)) is None:
            return f"Interface: {interface} Traffic Class: {traffic_class} - Not found"

        egress_drop = class_detail["egressQueueCounters"]["countersSum"]["droppedPackets"]
        ingress_drop = class_detail["ingressVoqCounters"]["countersSum"]["droppedPackets"]

        if egress_drop > threshold or ingress_drop > threshold:
            return f"Interface: {interface} Traffic Class: {traffic_class} - Queue drops exceeds the threshold - Egress: {egress_drop}, Ingress: {ingress_drop}"

        return None

    @skip_on_platforms(["cEOSLab", "vEOS-lab", "cEOSCloudLab", "vEOS"])
    @AntaTest.anta_test
    def test(self) -> None:
        """Main test function for VerifyInterfaceQueuDropsJericho."""
        self.result.is_success()
        command_output = self.instance_commands[0].json_output["interfaces"]

        interface_details = self.inputs.interfaces if self.inputs.interfaces else command_output.keys()

        for interface in interface_details:
            # Verification is skipped if the interface is in the ignored interfaces list.
            if is_interface_ignored(interface, self.inputs.ignored_interfaces):
                continue

            if (intf_detail := get_value(command_output, interface)) is None:
                self.result.is_failure(f"Interface: {interface} - Not found")
                continue

            traffic_class_details = self.inputs.traffic_classes if self.inputs.traffic_classes else intf_detail["trafficClasses"].keys()

            for traffic_class in traffic_class_details:
                failure_msg = self._verify_traffic_class_details(interface, traffic_class, intf_detail, self.inputs.dropped_pckt_threshold)
                if failure_msg:
                    self.result.is_failure(failure_msg)
