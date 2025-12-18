# Copyright (c) 2023-2025 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Module related to the device interfaces tests."""

# TODO: https://github.com/aristanetworks/anta/issues/1260
# pylint: disable=too-many-lines, duplicate-code

# Pyright does not understand AntaTest.Input typing
# pyright: reportAttributeAccessIssue=false
from __future__ import annotations

import re
from typing import TYPE_CHECKING, Any, ClassVar, Literal, TypeVar

from pydantic import Field, field_validator, model_validator
from pydantic_extra_types.mac_address import MacAddress

from anta.custom_types import DropPrecedence, EthernetInterface, Interface, InterfaceType, ManagementInterface, Percent, PortChannelInterface, PositiveInteger
from anta.decorators import skip_on_platforms
from anta.input_models.interfaces import InterfaceDetail, InterfaceState
from anta.models import AntaCommand, AntaTemplate, AntaTest
from anta.result_manager.models import AntaTestStatus
from anta.tools import custom_division, get_item, get_value, get_value_by_range_key, is_interface_ignored, time_ago

if TYPE_CHECKING:
    import sys

    if sys.version_info >= (3, 11):
        from typing import Self
    else:
        from typing_extensions import Self

BPS_GBPS_CONVERSIONS = 1000000000
NO_LIGHT_DBM = -30.0

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

            if (intf_bandwidth := intf_status["bandwidth"]) == 0:
                if test_has_input_interfaces:
                    # Test fails on user-provided interfaces
                    self.result.is_failure(f"Interface: {intf} - Cannot get interface utilization due to null bandwidth value")
                else:
                    self.logger.debug("Interface %s has been ignored due to null bandwidth value", intf)
                continue

            # The utilization logic has been implemented for full-duplex interfaces only
            if (intf_duplex := intf_status["duplex"]) != "duplexFull":
                self.result.is_failure(f"Interface: {intf} - Test not implemented for non-full-duplex interfaces - Expected: duplexFull Actual: {intf_duplex}")
                continue

            # If one or more interfaces have a usage above the threshold, test fails
            for bps_rate in ("inBpsRate", "outBpsRate"):
                usage = intf_counters[bps_rate] / intf_bandwidth * 100
                if usage > self.inputs.threshold:
                    self.result.is_failure(
                        f"Interface: {intf} BPS Rate: {bps_rate} - Usage above threshold - Expected: <= {self.inputs.threshold}% Actual: {usage}%"
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
          interfaces:
            - Ethernet1/1
          ignored_interfaces:
            - Ethernet1/5
            - Ethernet1/6
    ```
    """

    categories: ClassVar[list[str]] = ["interfaces"]
    commands: ClassVar[list[AntaCommand | AntaTemplate]] = [AntaCommand(command="show interfaces counters errors", revision=1)]
    _atomic_support: ClassVar[bool] = True

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

            # Atomic result
            result = self.result.add(description=f"Interface: {interface}", status=AntaTestStatus.SUCCESS)

            # If specified interface is not configured, test fails
            if (intf_counters := get_value(command_output, f"interfaceErrorCounters..{interface}", separator="..")) is None:
                result.is_failure("Not found")
                continue

            counters_data = [f"{counter}: {value}" for counter, value in intf_counters.items() if value > 0]
            if counters_data:
                result.is_failure(f"Non-zero error counter(s) - {', '.join(counters_data)}")


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
            - Ethernet1
            - Port-Channel1
          ignored_interfaces:
            - Vxlan1
            - Loopback0
    ```
    """

    categories: ClassVar[list[str]] = ["interfaces"]
    commands: ClassVar[list[AntaCommand | AntaTemplate]] = [AntaCommand(command="show interfaces counters discards", revision=1)]
    _atomic_support: ClassVar[bool] = True

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

            # Atomic result
            result = self.result.add(description=f"Interface: {interface}", status=AntaTestStatus.SUCCESS)

            # If specified interface is not configured, test fails
            if (intf_details := get_value(command_output, f"interfaces..{interface}", separator="..")) is None:
                result.is_failure("Not found")
                continue

            counters_data = [f"{counter}: {value}" for counter, value in intf_details.items() if value > 0]
            if counters_data:
                result.is_failure(f"Non-zero discard counter(s): {', '.join(counters_data)}")


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
          interfaces:
            - Ethernet1/1
          ignored_interfaces:
            - Ethernet1/5
            - Ethernet1/6
    ```
    """

    categories: ClassVar[list[str]] = ["interfaces"]
    commands: ClassVar[list[AntaCommand | AntaTemplate]] = [AntaCommand(command="show interfaces status errdisabled", revision=1)]
    _atomic_support: ClassVar[bool] = True

    class Input(AntaTest.Input):
        """Input model for the VerifyInterfaceErrDisabled test."""

        interfaces: list[Interface] | None = None
        """A list of interfaces to be tested. If not provided, all interfaces (excluding any in `ignored_interfaces`) are tested."""
        ignored_interfaces: list[InterfaceType | Interface] | None = None
        """A list of interfaces or interface types like Management which will ignore all Management interfaces."""

    @AntaTest.anta_test
    def test(self) -> None:
        """Main test function for VerifyInterfaceErrDisabled."""
        self.result.is_success()
        command_output = self.instance_commands[0].json_output
        interfaces = self.inputs.interfaces if self.inputs.interfaces else command_output["interfaceStatuses"].keys()

        for interface in interfaces:
            # Verification is skipped if the interface is in the ignored interfaces list.
            if is_interface_ignored(interface, self.inputs.ignored_interfaces):
                continue

            # atomic results
            result = self.result.add(description=f"Interface: {interface}")
            result.is_success()

            if not (intf_details := get_value(command_output["interfaceStatuses"], interface, separator="..")):
                continue

            if causes := intf_details.get("causes"):
                msg = f"Error disabled - Causes: {', '.join(causes)}"
                result.is_failure(msg)
                continue

            result.is_failure("Error disabled")


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
    _atomic_support: ClassVar[bool] = True

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
        command_output = self.instance_commands[0].json_output
        for interface in self.inputs.interfaces:
            # atomic result
            result = self.result.add(str(interface))
            result.is_success()

            if (intf_status := get_value(command_output["interfaceDescriptions"], interface.name, separator="..")) is None:
                result.is_failure("Not configured")
                continue

            status = "up" if intf_status["interfaceStatus"] in {"up", "connected"} else intf_status["interfaceStatus"]
            proto = "up" if intf_status["lineProtocolStatus"] in {"up", "connected"} else intf_status["lineProtocolStatus"]

            # If line protocol status is provided, prioritize checking against both status and line protocol status
            if interface.line_protocol_status:
                if any([interface.status != status, interface.line_protocol_status != proto]):
                    actual_state = f"Expected: {interface.status}/{interface.line_protocol_status}, Actual: {status}/{proto}"
                    result.is_failure(f"Status mismatch - {actual_state}")

            # If line protocol status is not provided and interface status is "up", expect both status and proto to be "up"
            # If interface status is not "up", check only the interface status without considering line protocol status
            elif all([interface.status == "up", status != "up" or proto != "up"]):
                result.is_failure(f"Status mismatch - Expected: up/up, Actual: {status}/{proto}")
            elif interface.status != status:
                result.is_failure(f"Status mismatch - Expected: {interface.status}, Actual: {status}")


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
    _atomic_support: ClassVar[bool] = True

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

            # Atomic result
            result = self.result.add(description=f"Interface: {interface}", status=AntaTestStatus.SUCCESS)

            # If specified interface is not configured, test fails
            if (intf_details := get_value(command_output, f"interfaces..{interface}", separator="..")) is None:
                result.is_failure("Not found")
                continue

            for traffic_type, traffic_type_dict in intf_details["trafficTypes"].items():
                if "drop" in traffic_type_dict and traffic_type_dict["drop"] != 0:
                    storm_controlled_interfaces = f"{traffic_type}: {traffic_type_dict['drop']}"
                    result.is_failure(f"Non-zero storm-control drop counter(s) - {storm_controlled_interfaces}")


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
    _atomic_support: ClassVar[bool] = True

    class Input(AntaTest.Input):
        """Input model for the VerifyPortChannels test."""

        interfaces: list[PortChannelInterface] | None = None
        """A list of port-channel interfaces to be tested. If not provided, all port-channel interfaces (excluding any in `ignored_interfaces`) are tested."""
        ignored_interfaces: list[PortChannelInterface] | None = None
        """A list of port-channel interfaces to ignore."""

    @AntaTest.anta_test
    def test(self) -> None:
        """Main test function for VerifyPortChannels."""
        command_output = self.instance_commands[0].json_output
        port_channels = self.inputs.interfaces if self.inputs.interfaces else command_output["portChannels"].keys()

        for port_channel in port_channels:
            # Verification is skipped if the interface is in the ignored interfaces list.
            if is_interface_ignored(port_channel, self.inputs.ignored_interfaces):
                continue

            # atomic results
            result = self.result.add(description=f"Interface: {port_channel}")
            result.is_success()

            # If specified interface is not configured, test fails
            if (port_channel_details := get_value(command_output, f"portChannels..{port_channel}", separator="..")) is None:
                result.is_failure("Not found")
                continue

            # Verify that the no inactive ports in all port channels.
            if inactive_ports := port_channel_details["inactivePorts"]:
                result.is_failure(f"Inactive port(s) - {', '.join(inactive_ports.keys())}")


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
    _atomic_support: ClassVar[bool] = True

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

            # Atomic result
            result = self.result.add(description=f"Interface: {port_channel}", status=AntaTestStatus.SUCCESS)

            # If specified port-channel is not configured, test fails
            if (port_channel_details := get_value(command_output, f"portChannels..{port_channel}", separator="..")) is None:
                result.is_failure("Not found")
                continue

            for interface, interface_details in port_channel_details["interfaces"].items():
                # Verify that the no illegal LACP packets in all port channels.
                if interface_details["illegalRxCount"] != 0:
                    result.is_failure(f"Illegal LACP packets detected on member interface {interface}")


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


class VerifyInterfacesVoqAndEgressQueueDrops(AntaTest):
    """Verifies interface ingress VOQ and egress queue drop counters.

    Compatible with Arista 7280R, 7500R, 7800R and 7700R series platforms supporting Virtual Output Queues (VOQ).

    Expected Results
    ----------------
    * Success: The test will pass if all VOQ and egress queue drops are within the defined threshold.
    * Failure: The test will fail if any VOQ or egress queue drop exceeds the defined threshold.

    Examples
    --------
    ```yaml
    anta.tests.interfaces:
      - VerifyInterfacesVoqAndEgressQueueDrops:
          interfaces:
            - Et1
            - Et2
          traffic_classes:
            - TC0
            - TC3
    ```
    """

    categories: ClassVar[list[str]] = ["interfaces"]
    commands: ClassVar[list[AntaCommand | AntaTemplate]] = [AntaCommand(command="show interfaces counters queue drops", revision=1)]

    class Input(AntaTest.Input):
        """Input model for the VerifyInterfacesVoqAndEgressQueueDrops test."""

        interfaces: list[Interface] | None = None
        """A list of interfaces to be tested. If not provided, all interfaces are tested."""
        traffic_classes: list[str] | None = None
        """List of traffic classes to be verified - TC0, TC1, etc. If None, all available traffic classes will be checked."""
        packet_drop_threshold: PositiveInteger = 0
        """Threshold for the number of dropped packets."""

    def _get_traffic_classes_to_check(self, interface: Interface, output: dict[str, Any]) -> dict[str, Any]:
        """Retrieve the traffic class and details to check based on the provided input traffic classes."""
        # Prepare the dictionary of traffic classes to check
        traffic_classes_to_check: dict[str, Any] = {}
        if self.inputs.traffic_classes:
            for tc_name in self.inputs.traffic_classes:
                if (tc_detail := get_value_by_range_key(output["trafficClasses"], tc_name)) is None:
                    self.result.is_failure(f"Interface: {interface} Traffic Class: {tc_name} - Not found")
                    continue
                traffic_classes_to_check[tc_name] = tc_detail
        else:
            # If no specific traffic classes are given, use all from the current interface
            traffic_classes_to_check = output["trafficClasses"]

        return traffic_classes_to_check

    @skip_on_platforms(["cEOSLab", "vEOS-lab", "cEOSCloudLab", "vEOS"])
    @AntaTest.anta_test
    def test(self) -> None:
        """Main test function for VerifyInterfacesVoqAndEgressQueueDrops."""
        self.result.is_success()
        command_output = self.instance_commands[0].json_output

        # Prepare the dictionary of interfaces to check
        interfaces_to_check: dict[str, Any] = {}
        if self.inputs.interfaces:
            for intf_name in self.inputs.interfaces:
                if (intf_detail := get_value(command_output["interfaces"], intf_name, separator="..")) is None:
                    self.result.is_failure(f"Interface: {intf_name} - Not found")
                    continue
                interfaces_to_check[intf_name] = intf_detail
        else:
            # If no specific interfaces are given, use all interfaces
            interfaces_to_check = command_output["interfaces"]

        for interface, details in interfaces_to_check.items():
            # Prepare the dictionary of traffic classes to check
            traffic_classes_to_check = self._get_traffic_classes_to_check(interface, details)
            for traffic_class, class_detail in traffic_classes_to_check.items():
                egress_drop = class_detail["egressQueueCounters"]["countersSum"]["droppedPackets"]
                ingress_drop = class_detail["ingressVoqCounters"]["countersSum"]["droppedPackets"]

                if egress_drop > self.inputs.packet_drop_threshold or ingress_drop > self.inputs.packet_drop_threshold:
                    self.result.is_failure(
                        f"Interface: {interface} Traffic Class: {traffic_class} - Queue drops above threshold - "
                        f"Expected: <= {self.inputs.packet_drop_threshold} Actual VOQ: {ingress_drop} Actual Egress: {egress_drop}"
                    )


class VerifyInterfacesTridentCounters(AntaTest):
    """Verifies the Trident debug counters of all interfaces.

    Compatible with Arista 7358X, 7300X, 7050X, 7010TX, 750XP, 720 and 710 series platforms featuring the Trident series chip.

    Expected Results
    ----------------
    * Success: The test will pass if all interfaces have drop and error counter values below the defined threshold.
    * Failure: The test will fail if any interface has drop or error counter values above the defined threshold.

    Examples
    --------
    ```yaml
    anta.tests.hardware:
      - VerifyInterfacesTridentCounters:
          ignored_counters:
            - nonCongestionDiscard
            - rxFpDrop
            - rxVlanDrop
          packet_drop_threshold: 0
    ```
    """

    categories: ClassVar[list[str]] = ["hardware"]
    commands: ClassVar[list[AntaCommand | AntaTemplate]] = [AntaCommand(command="show platform trident counters", revision=1)]

    class Input(AntaTest.Input):
        """Input model for the VerifyInterfacesTridentCounters test."""

        packet_drop_threshold: PositiveInteger = 0
        """Threshold for the number of dropped packets."""
        ignored_counters: list[str] | None = None
        """A list of interface counters to ignore. If None, all available counters will be checked."""

    @skip_on_platforms(["cEOSLab", "vEOS-lab", "cEOSCloudLab", "vEOS"])
    @AntaTest.anta_test
    def test(self) -> None:
        """Main test function for VerifyInterfacesTridentCounters."""
        self.result.is_success()
        command_output = self.instance_commands[0].json_output

        for interface, hw_counters in command_output["ethernet"].items():
            for counter_type in ["drop", "error"]:
                for counter_name, counter_value in hw_counters["count"][counter_type].items():
                    if self.inputs.ignored_counters and counter_name in self.inputs.ignored_counters:
                        continue

                    # Verify actual counter threshold
                    if counter_value > self.inputs.packet_drop_threshold:
                        self.result.is_failure(
                            f"Interface: {interface} - {counter_type.capitalize()} counter {counter_name} above threshold - "
                            f"Expected: <= {self.inputs.packet_drop_threshold} Actual: {counter_value}"
                        )


class VerifyInterfacesCounterDetails(AntaTest):
    """Verifies the interfaces counter details.

    !!! note
        This test specifically applies to **physical interfaces** (e.g., Ethernet and Management interfaces).

        It offers a more granular check of interface counters, including link status changes, compared to
        `VerifyInterfaceDiscards` and `VerifyInterfaceErrors` tests.


    Expected Results
    ----------------
    * Success: The test will pass if all tested interfaces have counters and link status changes at or below the defined thresholds.
    * Failure: The test will fail if any tested interface has one or more counters or a link status changes count that exceeds its defined threshold.

    Examples
    --------
    ```yaml
    anta.tests.interfaces:
      - VerifyInterfacesCounterDetails:
          interfaces:  # Optionally target specific interfaces
            - Ethernet1/1
            - Ethernet2/1
          ignored_interfaces:  # OR ignore specific interfaces
            - Management0
          counters_threshold: 10
          link_status_changes_threshold: 100
    ```
    """

    categories: ClassVar[list[str]] = ["interfaces"]
    commands: ClassVar[list[AntaCommand | AntaTemplate]] = [AntaCommand(command="show interfaces", revision=1)]

    class Input(AntaTest.Input):
        """Input model for the VerifyInterfacesCounterDetails test."""

        interfaces: list[EthernetInterface | ManagementInterface] | None = None
        """A list of Ethernet or Management interfaces to be tested.
        If not provided, all Ethernet or Management interfaces (excluding any in `ignored_interfaces`) are tested."""
        ignored_interfaces: list[EthernetInterface | ManagementInterface] | None = None
        """A list of Ethernet or Management interfaces to ignore."""
        counters_threshold: PositiveInteger = 0
        """The maximum acceptable value for each verified counter."""
        link_status_changes_threshold: PositiveInteger = 100
        """The maximum acceptable number of link status changes."""

        @model_validator(mode="after")
        def validate_duplicate_interfaces(self) -> Self:
            """Validate that no interface exists in both interfaces and ignored_interfaces simultaneously."""
            redundant_interfaces = []
            if self.interfaces and self.ignored_interfaces:
                redundant_interfaces = list(set(self.interfaces) & set(self.ignored_interfaces))
            if redundant_interfaces:
                msg = f"Interface(s) {', '.join(redundant_interfaces)} are present in both 'interfaces' and 'ignored_interfaces' lists"
                raise ValueError(msg)
            return self

    @AntaTest.anta_test
    def test(self) -> None:
        """Main test function for VerifyInterfacesCounterDetails."""
        self.result.is_success()
        command_output = self.instance_commands[0].json_output
        interfaces_to_check = self._get_interfaces_to_check(command_output)

        for interface, intf_details in interfaces_to_check.items():
            # Verification is skipped if the interface is in the ignored interfaces list
            if is_interface_ignored(interface, self.inputs.ignored_interfaces):
                continue

            # Verification is skipped if the interface is a subinterface or is not an EthernetX or ManagementX interface
            if re.fullmatch(r"^(Ethernet|Management)\d+(?:/\d+){0,2}$", interface) is None:
                continue

            # Verification is skipped if interface counters are not found
            if not (interface_counters := intf_details.get("interfaceCounters", {})):
                self.logger.debug("Interface: %s has been ignored as interface counters not found", interface)
                continue

            # Retrieve the interface failure message summary
            interface_failure_message_summary = self._generate_interface_failure_message_summary(interface, intf_details)

            # Verify the link status changes
            if (act_link_status_changes := interface_counters["linkStatusChanges"]) > self.inputs.link_status_changes_threshold:
                self.result.is_failure(
                    f"{interface_failure_message_summary} - Link status changes above threshold - "
                    f"Expected: <= {self.inputs.link_status_changes_threshold} Actual: {act_link_status_changes}"
                )

            # Verify interface counters
            self._verify_interface_counters(interface_counters, interface_failure_message_summary)

    def _get_interfaces_to_check(self, intf_details: dict[str, Any]) -> dict[str, Any]:
        """Get the interfaces to check and their corresponding details based on the provided input interfaces."""
        # Prepare the dictionary of interfaces to check
        interfaces_to_check: dict[str, Any] = {}
        if self.inputs.interfaces:
            for intf_name in self.inputs.interfaces:
                if (intf_detail := get_value(intf_details["interfaces"], intf_name, separator="..")) is None:
                    self.result.is_failure(f"Interface: {intf_name} - Not found")
                    continue
                interfaces_to_check[intf_name] = intf_detail
        else:
            # If no specific interfaces are given, use all interfaces
            interfaces_to_check = intf_details["interfaces"]
        return interfaces_to_check

    def _generate_interface_failure_message_summary(self, interface: str, intf_details: dict[str, Any]) -> str:
        """Generate an interface failure message summary from the provided interface details."""
        interface_summary = f"Interface: {interface}"
        interface_is_up = intf_details["lineProtocolStatus"] == "up" and intf_details["interfaceStatus"] == "connected"
        if intf_description := intf_details.get("description"):
            interface_summary += f" Description: {intf_description}"
        if (intf_timestamp := intf_details.get("lastStatusChangeTimestamp")) is not None:
            last_status_change = time_ago(intf_timestamp)
            uptime_or_downtime = " Uptime" if interface_is_up else " Downtime"
            interface_summary += f"{uptime_or_downtime}: {last_status_change}"
        return interface_summary

    def _verify_interface_counters(self, interface_counters: dict[str, Any], interface_failure_message_summary: str) -> None:
        """Verify counters of an interface."""
        counters_to_verify = [
            {"counter_key": "inDiscards", "counter_name": "Input discards"},
            {"counter_key": "outDiscards", "counter_name": "Output discards"},
            {"counter_key": "totalInErrors", "counter_name": "Input errors"},
            {"counter_key": "totalOutErrors", "counter_name": "Output errors"},
            {"counter_key": "inputErrorsDetail.runtFrames", "counter_name": "Runt frames"},
            {"counter_key": "inputErrorsDetail.giantFrames", "counter_name": "Giant frames"},
            {"counter_key": "inputErrorsDetail.fcsErrors", "counter_name": "CRC errors"},
            {"counter_key": "inputErrorsDetail.alignmentErrors", "counter_name": "Alignment errors"},
            {"counter_key": "inputErrorsDetail.symbolErrors", "counter_name": "Symbol errors"},
            {"counter_key": "outputErrorsDetail.collisions", "counter_name": "Collisions"},
            {"counter_key": "outputErrorsDetail.lateCollisions", "counter_name": "Late collisions"},
            {"counter_key": "outputErrorsDetail.deferredTransmissions", "counter_name": "Deferred transmissions"},
        ]
        for counter in counters_to_verify:
            counter_value = get_value(interface_counters, counter["counter_key"])
            if counter_value > self.inputs.counters_threshold:
                failure_msg = f"Expected: <= {self.inputs.counters_threshold} Actual: {counter_value}"
                self.result.is_failure(f"{interface_failure_message_summary} - {counter['counter_name']} above threshold - {failure_msg}")


class VerifyInterfacesBER(AntaTest):
    """Verifies interfaces pre-FEC bit error rate (BER) and FEC uncorrected codewords.

    Expected Results
    ----------------
    * Success: The test will pass if all tested interfaces have a pre-FEC BER below the specified maximum threshold and have zero uncorrected FEC codewords.
    * Failure: The test will fail if any tested interface has a BER exceeding the maximum threshold or reports any uncorrected FEC codewords.

    Examples
    --------
    ```yaml
    anta.tests.interfaces:
      - VerifyInterfacesBER:
          interfaces:
            - Ethernet1/1
            - Ethernet2/1
          max_ber_threshold: 1e-6
    ```
    """

    categories: ClassVar[list[str]] = ["interfaces"]
    commands: ClassVar[list[AntaCommand | AntaTemplate]] = [
        AntaCommand(command="show interfaces phy detail", revision=2),
        AntaCommand(command="show interfaces description", revision=1),
    ]

    class Input(AntaTest.Input):
        """Input model for the VerifyInterfacesBER test."""

        interfaces: list[EthernetInterface] | None = None
        """A list of Ethernet interfaces to be tested.
        If not provided, all Ethernet interfaces (excluding any in `ignored_interfaces`) with PHY details are tested."""
        ignored_interfaces: list[EthernetInterface] | None = None
        """A list of Ethernet interfaces to ignore."""
        max_ber_threshold: float = 1e-7
        """The maximum acceptable Pre-FEC BER."""
        fail_on_uncorrected_codewords: bool = True
        """If True, the test will fail if any uncorrected FEC codewords are detected."""

        @model_validator(mode="after")
        def validate_duplicate_interfaces(self) -> Self:
            """Validate that no interface exists in both interfaces and ignored_interfaces simultaneously."""
            redundant_interfaces = []
            if self.interfaces and self.ignored_interfaces:
                redundant_interfaces = list(set(self.interfaces) & set(self.ignored_interfaces))
            if redundant_interfaces:
                msg = f"Interface(s) {', '.join(redundant_interfaces)} are present in both 'interfaces' and 'ignored_interfaces' lists"
                raise ValueError(msg)
            return self

    def _get_interfaces_to_check(self, intf_details: dict[str, Any]) -> dict[str, Any]:
        """Get the interfaces to check and their corresponding details based on the provided input interfaces."""
        # Prepare the dictionary of interfaces to check
        interfaces_to_check: dict[str, Any] = {}
        if self.inputs.interfaces:
            for intf_name in self.inputs.interfaces:
                if (intf_detail := get_value(intf_details["interfacePhyStatuses"], intf_name, separator="..")) is None:
                    self.result.is_failure(f"Interface: {intf_name} - Not found")
                    continue
                interfaces_to_check[intf_name] = intf_detail
        else:
            # If no specific interfaces are given, use all interfaces
            interfaces_to_check = intf_details["interfacePhyStatuses"]
        return interfaces_to_check

    @skip_on_platforms(["cEOSLab", "vEOS-lab", "cEOSCloudLab", "vEOS"])
    @AntaTest.anta_test
    def test(self) -> None:
        """Main test function for VerifyInterfacesBER."""
        self.result.is_success()
        intf_phy_details = self.instance_commands[0].json_output
        intf_descriptions = self.instance_commands[1].json_output["interfaceDescriptions"]

        interfaces_to_check = self._get_interfaces_to_check(intf_phy_details)
        for interface, data in interfaces_to_check.items():
            # Verification is skipped if the interface is in the ignored interfaces list
            if is_interface_ignored(interface, self.inputs.ignored_interfaces):
                continue

            # Collect interface description
            intf_description = get_value(intf_descriptions, f"{interface}..description", separator="..")
            description_str = f" Description: {intf_description}" if intf_description else ""
            for phy_status in data.get("phyStatuses", []):
                actual_ber_value = get_value(phy_status, "preFecBer.value")
                fec_corrected_value = get_value(phy_status, "fec.correctedCodewords.value")
                fec_uncorrected_value = get_value(phy_status, "fec.uncorrectedCodewords.value")

                # Skip interfaces that don't have 'preFecBer', 'fec.correctedCodewords' or 'fec.uncorrectedCodewords' values
                if any(x is None for x in [actual_ber_value, fec_corrected_value, fec_uncorrected_value]):
                    self.logger.debug("Interface %s: Skipped - pre-FEC BER or FEC details are not found", interface)
                    continue

                if self.inputs.fail_on_uncorrected_codewords and fec_uncorrected_value > 0:
                    self.result.is_failure(
                        f"Interface: {interface}{description_str} - Uncorrected FEC codewords detected - Expected: 0 Actual: {fec_uncorrected_value}"
                    )

                # Verify if BER exceeds the maximum allowed threshold
                if actual_ber_value > self.inputs.max_ber_threshold:
                    self.result.is_failure(
                        f"Interface: {interface}{description_str} FEC Corrected: {fec_corrected_value} FEC Uncorrected: {fec_uncorrected_value} - "
                        f"BER above threshold - Expected: <= {self.inputs.max_ber_threshold:.2e} Actual: {actual_ber_value:.2e}"
                    )


class VerifyInterfacesOpticsReceivePower(AntaTest):
    """Verifies that the receive power levels of optical interface transceivers are within acceptable limits.

    !!! info
        This test only applies to interface transceivers that support Digital Optical Monitoring (DOM).

        Unless otherwise stated, DOM capabilities are supported on all Arista AOCs and optical transceivers.

    Expected Results
    ----------------
    * Success: The test will pass if all tested interfaces have their installed transceiver receive power levels
                above their low-alarm threshold, considering the defined tolerance.
    * Failure: The test will fail if any interface reports a receive power level from its transceiver that,
                after subtracting the tolerance, falls below its low-alarm threshold.

    Examples
    --------
    ```yaml
    anta.tests.interfaces:
      - VerifyInterfacesOpticsReceivePower:
          interfaces:  # Optionally target specific interfaces
            - Ethernet1/1
            - Ethernet2/1
          ignored_interfaces:  # OR ignore specific interfaces
            - Ethernet3/1
          failure_margin: 2
    ```
    """

    categories: ClassVar[list[str]] = ["interfaces"]
    commands: ClassVar[list[AntaCommand | AntaTemplate]] = [
        AntaCommand(command="show interfaces transceiver dom thresholds", revision=1),
        AntaCommand(command="show interfaces description", revision=1),
    ]

    class Input(AntaTest.Input):
        """Input model for the VerifyInterfacesOpticsReceivePower test."""

        interfaces: list[EthernetInterface] | None = None
        """A list of Ethernet interfaces to be tested.
        If not provided, all Ethernet interfaces (excluding any in `ignored_interfaces`) with DOM support are tested."""
        ignored_interfaces: list[EthernetInterface] | None = None
        """A list of Ethernet interfaces to ignore."""
        failure_margin: PositiveInteger = Field(default=2)
        """Proactive failure margin in dB. The test will fail if the receive power is weaker than the low-alarm threshold plus this margin."""

        @model_validator(mode="after")
        def validate_duplicate_interfaces(self) -> Self:
            """Validate that no interface exists in both interfaces and ignored_interfaces simultaneously."""
            redundant_interfaces = []
            if self.interfaces and self.ignored_interfaces:
                redundant_interfaces = list(set(self.interfaces) & set(self.ignored_interfaces))
            if redundant_interfaces:
                msg = f"Interface(s) {', '.join(redundant_interfaces)} are present in both 'interfaces' and 'ignored_interfaces' lists"
                raise ValueError(msg)
            return self

    def _get_interfaces_to_check(self, intf_details: dict[str, Any]) -> dict[str, Any]:
        """Get the interfaces to check and their corresponding details based on the provided input interfaces."""
        # Prepare the dictionary of interfaces to check
        interfaces_to_check: dict[str, Any] = {}
        if self.inputs.interfaces:
            for intf_name in self.inputs.interfaces:
                if (intf_detail := get_value(intf_details["interfaces"], intf_name, separator="..")) is None:
                    self.result.is_failure(f"Interface: {intf_name} - Optic not found")
                    continue
                interfaces_to_check[intf_name] = intf_detail
        else:
            # If no specific interfaces are given, use all interfaces
            interfaces_to_check = intf_details["interfaces"]
        return interfaces_to_check

    @skip_on_platforms(["cEOSLab", "vEOS-lab", "cEOSCloudLab", "vEOS"])
    @AntaTest.anta_test
    def test(self) -> None:
        """Main test function for VerifyInterfacesOpticsReceivePower."""
        self.result.is_success()
        int_transceiver_details = self.instance_commands[0].json_output
        int_descriptions = self.instance_commands[1].json_output["interfaceDescriptions"]

        interfaces_to_check = self._get_interfaces_to_check(int_transceiver_details)
        for interface, int_data in interfaces_to_check.items():
            # Verification is skipped if the interface is in the ignored interfaces list
            if is_interface_ignored(interface, self.inputs.ignored_interfaces):
                continue

            # Verify receive power details
            if (rx_power_details := get_value(int_data, "parameters.rxPower")) is None:
                message = f"Interface: {interface} - Receive power details are not found (DOM not supported)"
                if self.inputs.interfaces:
                    self.result.is_failure(message)
                else:
                    self.logger.debug(message)
                continue

            # Collect interface description
            intf_description = get_value(int_descriptions, f"{interface}.description", separator="..")
            description_str = f" Description: {intf_description}" if intf_description else ""

            for channel, rx_power_value in rx_power_details["channels"].items():
                low_alarm_threshold = rx_power_details["threshold"]["lowAlarm"]
                effective_threshold = low_alarm_threshold + self.inputs.failure_margin
                is_receiving_light = rx_power_value != NO_LIGHT_DBM
                if is_receiving_light and (rx_power_value < effective_threshold):
                    self.result.is_failure(
                        f"Interface: {interface}{description_str} Status: {int_descriptions[interface]['interfaceStatus']} "
                        f"Channel: {channel} Optic: {int_data.get('mediaType')} - "
                        f"Low receive power detected - "
                        f"Expected: >= {effective_threshold:.2f}dBm (Alarm: {low_alarm_threshold:.2f}dBm + Margin: {self.inputs.failure_margin}dBm) "
                        f"Actual: {rx_power_value:.2f}dBm"
                    )


class VerifyInterfacesEgressQueueDrops(AntaTest):
    """Verifies interface egress queue drop counters.

    Expected Results
    ----------------
    * Success: The test will pass if all egress queue drop counters are within the defined threshold.
    * Failure: The test will fail if any egress queue drop counters exceeds the defined threshold.

    Examples
    --------
    ```yaml
    anta.tests.interfaces:
      - VerifyInterfacesEgressQueueDrops:
          interfaces:
            - Et1
            - Et2
          traffic_classes:
            - TC0
            - TC3
          drop_precedences:
            - DP0
    ```
    """

    categories: ClassVar[list[str]] = ["interfaces"]
    commands: ClassVar[list[AntaCommand | AntaTemplate]] = [AntaCommand(command="show interfaces counters queue detail", revision=1)]

    class Input(AntaTest.Input):
        """Input model for the VerifyInterfacesEgressQueueDrops test."""

        interfaces: list[EthernetInterface] | None = None
        """A list of interfaces to be tested. If not provided, all interfaces are tested."""
        ignored_interfaces: list[EthernetInterface] | None = None
        """A list of Ethernet interfaces to ignore."""
        traffic_classes: list[str] | None = None
        """List of traffic classes to be verified - TC0, TC1, etc. If None, all available traffic classes will be checked."""
        queue_types: list[Literal["unicast", "multicast"]] = Field(default=["unicast", "multicast"])
        """List of queue types to be verified. If None, unicast and multicast queue types will be checked."""
        drop_precedences: list[DropPrecedence] = Field(default=["DP0"])
        """List of drop precedences to be verified - DP0, DP1, etc. If None, only DP0 will be checked."""
        packet_drop_threshold: PositiveInteger = 0
        """Threshold for the number of dropped packets."""

        @model_validator(mode="after")
        def validate_duplicate_interfaces(self) -> Self:
            """Validate that no interface exists in both interfaces and ignored_interfaces simultaneously."""
            redundant_interfaces = []
            if self.interfaces and self.ignored_interfaces:
                redundant_interfaces = list(set(self.interfaces) & set(self.ignored_interfaces))
            if redundant_interfaces:
                msg = f"Interface(s) {', '.join(redundant_interfaces)} are present in both 'interfaces' and 'ignored_interfaces' lists"
                raise ValueError(msg)
            return self

    def _verify_traffic_class_details(self, interface: Interface, queue_type: str, traffic_classes_to_check: dict[str, Any]) -> None:
        """Verify if egress dropped packet counts for given traffic classes and drop precedences exceed the threshold."""
        for traffic_class, tc_detail in traffic_classes_to_check.items():
            for drop_precedence in self.inputs.drop_precedences:
                if (drop_precedence_details := get_value_by_range_key(tc_detail["dropPrecedences"], drop_precedence)) is None:
                    self.result.is_failure(
                        f"Interface: {interface} Traffic Class: {traffic_class} Queue Type: {queue_type} Drop Precedence: {drop_precedence} - Not found"
                    )
                    continue

                dropped_packets = drop_precedence_details["droppedPackets"]
                if dropped_packets > self.inputs.packet_drop_threshold:
                    message = f"Queue drops above threshold - Expected: <= {self.inputs.packet_drop_threshold} Actual: {dropped_packets}"
                    self.result.is_failure(
                        f"Interface: {interface} Traffic Class: {traffic_class} Queue Type: {queue_type} Drop Precedence: {drop_precedence} - {message}"
                    )

    def _get_traffic_classes_to_check(self, interface: Interface, queue_type: str, traffic_classes_output: dict[str, Any]) -> dict[str, Any]:
        """Retrieve the traffic classes and details to check based on the provided input traffic classes."""
        # Prepare the dictionary of traffic classes to check
        traffic_classes_to_check: dict[str, Any] = {}
        if self.inputs.traffic_classes:
            for tc_name in self.inputs.traffic_classes:
                if (tc_detail := get_value_by_range_key(traffic_classes_output, tc_name)) is None:
                    self.result.is_failure(f"Interface: {interface} Queue Type: {queue_type} Traffic Class: {tc_name} - Not found")
                    continue
                traffic_classes_to_check[tc_name] = tc_detail
        else:
            # If no specific traffic classes are given, use all from the current interface
            traffic_classes_to_check = traffic_classes_output

        return traffic_classes_to_check

    @skip_on_platforms(["cEOSLab", "vEOS-lab"])
    @AntaTest.anta_test
    def test(self) -> None:
        """Main test function for VerifyInterfacesEgressQueueDrops."""
        self.result.is_success()
        command_output = self.instance_commands[0].json_output

        # Prepare the dictionary of interfaces to check
        interfaces_to_check: dict[str, Any] = {}
        if self.inputs.interfaces:
            for intf_name in self.inputs.interfaces:
                if (intf_detail := get_value(command_output["egressQueueCounters"]["interfaces"], intf_name, separator="..")) is None:
                    self.result.is_failure(f"Interface: {intf_name} - Not found")
                    continue
                interfaces_to_check[intf_name] = intf_detail
        else:
            # If no specific interfaces are given, use all interfaces
            interfaces_to_check = command_output["egressQueueCounters"]["interfaces"]

        for interface, details in interfaces_to_check.items():
            # Verification is skipped if the interface is in the ignored interfaces list
            if is_interface_ignored(interface, self.inputs.ignored_interfaces):
                continue

            for queue_type in self.inputs.queue_types:
                type_to_lookup = "ucastQueues" if queue_type == "unicast" else "mcastQueues"
                traffic_classes_output = get_value(details, f"{type_to_lookup}.trafficClasses", default={})
                traffic_classes_to_check = self._get_traffic_classes_to_check(interface, queue_type, traffic_classes_output)
                self._verify_traffic_class_details(interface, queue_type, traffic_classes_to_check)


class VerifyInterfacesOpticsTemperature(AntaTest):
    """Verifies that the temperature of optical interface transceivers is within acceptable limits.

    !!! info
        This test only applies to interface transceivers that support Digital Optical Monitoring (DOM).

        Unless otherwise stated, DOM capabilities are supported on all Arista AOCs and optical transceivers.

    Expected Results
    ----------------
    * Success: The test will pass if the temperature of all tested transceivers is within the defined threshold.
    * Failure: The test will fail if any transceiver reports a temperature that exceeds the defined threshold.

    Examples
    --------
    ```yaml
    anta.tests.interfaces:
      - VerifyInterfacesOpticsTemperature:
          interfaces:  # Optionally target specific interfaces
            - Ethernet1/1
            - Ethernet2/1
          ignored_interfaces:  # OR ignore specific interfaces
            - Ethernet3/1
          max_transceiver_temperature: 68
    ```
    """

    categories: ClassVar[list[str]] = ["interfaces"]
    commands: ClassVar[list[AntaCommand | AntaTemplate]] = [AntaCommand(command="show interfaces transceiver dom thresholds", revision=1)]

    class Input(AntaTest.Input):
        """Input model for the VerifyInterfacesOpticsTemperature test."""

        interfaces: list[EthernetInterface] | None = None
        """A list of Ethernet interfaces to be tested.
        If not provided, all Ethernet interfaces (excluding any in `ignored_interfaces`) with DOM support are tested."""
        ignored_interfaces: list[EthernetInterface] | None = None
        """A list of Ethernet interfaces to ignore."""
        max_transceiver_temperature: float = 68.00
        """The temperature threshold in degrees Celsius (°C)."""

        @model_validator(mode="after")
        def validate_duplicate_interfaces(self) -> Self:
            """Validate that no interface exists in both interfaces and ignored_interfaces simultaneously."""
            redundant_interfaces = []
            if self.interfaces and self.ignored_interfaces:
                redundant_interfaces = list(set(self.interfaces) & set(self.ignored_interfaces))
            if redundant_interfaces:
                msg = f"Interface(s) {', '.join(redundant_interfaces)} are present in both 'interfaces' and 'ignored_interfaces' lists"
                raise ValueError(msg)
            return self

    def _get_interfaces_to_check(self, intf_details: dict[str, Any]) -> dict[str, Any]:
        """Get the interfaces to check and their corresponding details based on the provided input interfaces."""
        # Prepare the dictionary of interfaces to check
        interfaces_to_check: dict[str, Any] = {}
        if self.inputs.interfaces:
            for intf_name in self.inputs.interfaces:
                if not (intf_detail := get_value(intf_details["interfaces"], intf_name, separator="..")):
                    self.result.is_failure(f"Interface: {intf_name} - Optic not found")
                    continue
                interfaces_to_check[intf_name] = intf_detail
        else:
            # If no specific interfaces are given, use all interfaces
            interfaces_to_check = intf_details["interfaces"]
        return interfaces_to_check

    @skip_on_platforms(["cEOSLab", "vEOS-lab", "cEOSCloudLab", "vEOS"])
    @AntaTest.anta_test
    def test(self) -> None:
        """Main test function for VerifyInterfacesOpticsTemperature."""
        self.result.is_success()
        command_output = self.instance_commands[0].json_output

        # Prepare the dictionary of interfaces to check
        interfaces_to_check = self._get_interfaces_to_check(command_output)

        for interface, interface_detail in interfaces_to_check.items():
            # Verification is skipped if the interface is in the ignored interfaces list
            if is_interface_ignored(interface, self.inputs.ignored_interfaces):
                continue

            # Verify temperature details
            if (temp_details := get_value(interface_detail, "parameters.temperature")) is None:
                message = f"Interface: {interface} - Temperature details are not found (DOM not supported)"
                if self.inputs.interfaces:
                    self.result.is_failure(message)
                else:
                    self.logger.debug(message)
                continue

            # '-' for the channel indicates a channel independent parameter
            actual_temp = get_value(temp_details, "channels.-", default=0.0)
            if actual_temp > self.inputs.max_transceiver_temperature:
                values = f"Expected: <= {self.inputs.max_transceiver_temperature}°C Actual: {actual_temp:.2f}°C"
                self.result.is_failure(f"Interface: {interface} - High transceiver temperature detected - {values}")


class VerifyInterfacesPFCCounters(AntaTest):
    """Verifies the interfaces PFC frame send and receive counters.

    Expected Results
    ----------------
    * Success: The test will pass if both the sent and received PFC frame counts on all tested interfaces are below the defined threshold.
    * Failure: The test will fail if either the sent or received PFC frame count on any tested interface exceeds the defined threshold.

    Examples
    --------
    ```yaml
    anta.tests.interfaces:
      - VerifyInterfacesPFCCounters:
          interfaces:  # Optionally target specific interfaces
            - Ethernet1/1
            - Ethernet2/1
          ignored_interfaces:  # OR ignore specific interfaces
            - Management0
          counters_threshold: 0
    ```
    """

    categories: ClassVar[list[str]] = ["interfaces"]
    commands: ClassVar[list[AntaCommand | AntaTemplate]] = [AntaCommand(command="show priority-flow-control counters", revision=3)]

    class Input(AntaTest.Input):
        """Input model for the VerifyInterfacesPFCCounters test."""

        interfaces: list[EthernetInterface | ManagementInterface] | None = None
        """A list of Ethernet or Management interfaces to be tested.

        If not provided, all Ethernet or Management interfaces (excluding any in `ignored_interfaces`) are tested."""
        ignored_interfaces: list[EthernetInterface | ManagementInterface] | None = None
        """A list of Ethernet or Management interfaces to ignore."""
        counters_threshold: PositiveInteger = 0
        """The maximum acceptable value for PFC sent and received frame."""

        @model_validator(mode="after")
        def validate_duplicate_interfaces(self) -> Self:
            """Validate that no interface exists in both interfaces and ignored_interfaces simultaneously."""
            redundant_interfaces = []
            if self.interfaces and self.ignored_interfaces:
                redundant_interfaces = list(set(self.interfaces) & set(self.ignored_interfaces))
            if redundant_interfaces:
                msg = f"Interface(s) {', '.join(redundant_interfaces)} are present in both 'interfaces' and 'ignored_interfaces' lists"
                raise ValueError(msg)
            return self

    def _get_interfaces_to_check(self, intf_details: dict[str, Any]) -> dict[str, Any]:
        """Get the interfaces to check and their corresponding details based on the provided input interfaces."""
        # Prepare the dictionary of interfaces to check
        interfaces_to_check: dict[str, Any] = {}
        if self.inputs.interfaces:
            for intf_name in self.inputs.interfaces:
                if (intf_detail := get_value(intf_details["interfaceCounters"], intf_name, separator="..")) is None:
                    self.result.is_failure(f"Interface: {intf_name} - Not found")
                    continue
                interfaces_to_check[intf_name] = intf_detail
        else:
            # If no specific interfaces are given, use all interfaces
            interfaces_to_check = intf_details["interfaceCounters"]
        return interfaces_to_check

    @skip_on_platforms(["cEOSLab", "vEOS-lab", "cEOSCloudLab", "vEOS"])
    @AntaTest.anta_test
    def test(self) -> None:
        """Main test function for VerifyInterfacesPFCCounters."""
        self.result.is_success()
        command_output = self.instance_commands[0].json_output

        # Prepare the dictionary of interfaces to check
        interfaces_to_check = self._get_interfaces_to_check(command_output)

        for interface, interface_detail in interfaces_to_check.items():
            # Verification is skipped if the interface is in the ignored interfaces list
            if is_interface_ignored(interface, self.inputs.ignored_interfaces):
                continue

            rx_frames = get_value(interface_detail, "rxFrames", 0)
            tx_frames = get_value(interface_detail, "txFrames", 0)

            if rx_frames > self.inputs.counters_threshold or tx_frames > self.inputs.counters_threshold:
                self.result.is_failure(
                    f"Interface: {interface} - Counters above threshold - "
                    f"Expected: <= {self.inputs.counters_threshold} Actual RX PFC: {rx_frames} Actual TX PFC: {tx_frames}"
                )


class VerifyInterfacesECNCounters(AntaTest):
    """Verifies the interfaces ECN counters for all queues.

    Expected Results
    ----------------
    * Success: The test will pass if all tested interfaces have ECN counters below the defined threshold.
    * Failure: The test will fail if any tested interface ECN counter exceeds the defined threshold.

    Examples
    --------
    ```yaml
    anta.tests.interfaces:
      - VerifyInterfacesECNCounters:
          interfaces:  # Optionally target specific interfaces
            - Ethernet1/1
            - Ethernet2/1
          ignored_interfaces:  # OR ignore specific interfaces
            - Management0
          counters_threshold: 0
    ```
    """

    categories: ClassVar[list[str]] = ["interfaces"]
    commands: ClassVar[list[AntaCommand | AntaTemplate]] = [AntaCommand(command="show qos interfaces ecn counters queue", revision=1)]

    class Input(AntaTest.Input):
        """Input model for the VerifyInterfacesECNCounters test."""

        interfaces: list[EthernetInterface | ManagementInterface] | None = None
        """A list of Ethernet or Management interfaces to be tested.

        If not provided, all Ethernet or Management interfaces (excluding any in `ignored_interfaces`) are tested."""
        ignored_interfaces: list[EthernetInterface | ManagementInterface] | None = None
        """A list of Ethernet or Management interfaces to ignore."""
        counters_threshold: PositiveInteger = 0
        """The maximum acceptable number of ECN-marked packets."""

        @model_validator(mode="after")
        def validate_duplicate_interfaces(self) -> Self:
            """Validate that no interface exists in both interfaces and ignored_interfaces simultaneously."""
            redundant_interfaces = []
            if self.interfaces and self.ignored_interfaces:
                redundant_interfaces = list(set(self.interfaces) & set(self.ignored_interfaces))
            if redundant_interfaces:
                msg = f"Interface(s) {', '.join(redundant_interfaces)} are present in both 'interfaces' and 'ignored_interfaces' lists"
                raise ValueError(msg)
            return self

    def _get_interfaces_to_check(self, intf_details: dict[str, Any]) -> dict[str, Any]:
        """Get the interfaces to check and their corresponding details based on the provided input interfaces."""
        # Prepare the dictionary of interfaces to check
        interfaces_to_check: dict[str, Any] = {}
        if self.inputs.interfaces:
            for intf_name in self.inputs.interfaces:
                if (intf_detail := get_value(intf_details["intfQueueCounters"], intf_name, separator="..")) is None:
                    self.result.is_failure(f"Interface: {intf_name} - Not found")
                    continue
                interfaces_to_check[intf_name] = intf_detail
        else:
            # If no specific interfaces are given, use all interfaces
            interfaces_to_check = intf_details["intfQueueCounters"]
        return interfaces_to_check

    @skip_on_platforms(["cEOSLab", "vEOS-lab", "cEOSCloudLab", "vEOS"])
    @AntaTest.anta_test
    def test(self) -> None:
        """Main test function for VerifyInterfacesECNCounters."""
        self.result.is_success()
        command_output = self.instance_commands[0].json_output

        # Prepare the dictionary of interfaces to check
        interfaces_to_check = self._get_interfaces_to_check(command_output)

        for interface, interface_detail in interfaces_to_check.items():
            # Verification is skipped if the interface is in the ignored interfaces list
            if is_interface_ignored(interface, self.inputs.ignored_interfaces):
                continue

            for queue, counter_value in interface_detail["queueCounters"].items():
                if counter_value == "-":
                    # ECN not configured for this queue
                    continue

                if int(counter_value) > self.inputs.counters_threshold:
                    self.result.is_failure(
                        f"Interface: {interface} Queue: {queue} - Counters above threshold - Expected: <= {self.inputs.counters_threshold} Actual: {counter_value}"
                    )
