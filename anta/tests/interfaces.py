# Copyright (c) 2023-2024 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Module related to the device interfaces tests."""

# Mypy does not understand AntaTest.Input typing
# mypy: disable-error-code=attr-defined
from __future__ import annotations

import re
from ipaddress import IPv4Network
from typing import Any, ClassVar, Literal

from pydantic import BaseModel, Field
from pydantic_extra_types.mac_address import MacAddress

from anta import GITHUB_SUGGESTION
from anta.custom_types import EthernetInterface, Interface, Percent, PortChannelInterface, PositiveInteger
from anta.decorators import skip_on_platforms
from anta.models import AntaCommand, AntaTemplate, AntaTest
from anta.tools import custom_division, get_failed_logs, get_item, get_value

BPS_GBPS_CONVERSIONS = 1000000000


class VerifyInterfaceUtilization(AntaTest):
    """Verifies that the utilization of interfaces is below a certain threshold.

    Load interval (default to 5 minutes) is defined in device configuration.
    This test has been implemented for full-duplex interfaces only.

    Expected Results
    ----------------
    * Success: The test will pass if all interfaces have a usage below the threshold.
    * Failure: The test will fail if one or more interfaces have a usage above the threshold.
    * Error: The test will error out if the device has at least one non full-duplex interface.

    Examples
    --------
    ```yaml
    anta.tests.interfaces:
      - VerifyInterfaceUtilization:
          threshold: 70.0
    ```
    """

    name = "VerifyInterfaceUtilization"
    description = "Verifies that the utilization of interfaces is below a certain threshold."
    categories: ClassVar[list[str]] = ["interfaces"]
    commands: ClassVar[list[AntaCommand | AntaTemplate]] = [
        AntaCommand(command="show interfaces counters rates", revision=1),
        AntaCommand(command="show interfaces", revision=1),
    ]

    class Input(AntaTest.Input):
        """Input model for the VerifyInterfaceUtilization test."""

        threshold: Percent = 75.0
        """Interface utilization threshold above which the test will fail. Defaults to 75%."""

    @AntaTest.anta_test
    def test(self) -> None:
        """Main test function for VerifyInterfaceUtilization."""
        duplex_full = "duplexFull"
        failed_interfaces: dict[str, dict[str, float]] = {}
        rates = self.instance_commands[0].json_output
        interfaces = self.instance_commands[1].json_output

        for intf, rate in rates["interfaces"].items():
            # The utilization logic has been implemented for full-duplex interfaces only
            if ((duplex := (interface := interfaces["interfaces"][intf]).get("duplex", None)) is not None and duplex != duplex_full) or (
                (members := interface.get("memberInterfaces", None)) is not None and any(stats["duplex"] != duplex_full for stats in members.values())
            ):
                self.result.is_failure(f"Interface {intf} or one of its member interfaces is not Full-Duplex. VerifyInterfaceUtilization has not been implemented.")
                return

            if (bandwidth := interfaces["interfaces"][intf]["bandwidth"]) == 0:
                self.logger.debug("Interface %s has been ignored due to null bandwidth value", intf)
                continue

            for bps_rate in ("inBpsRate", "outBpsRate"):
                usage = rate[bps_rate] / bandwidth * 100
                if usage > self.inputs.threshold:
                    failed_interfaces.setdefault(intf, {})[bps_rate] = usage

        if not failed_interfaces:
            self.result.is_success()
        else:
            self.result.is_failure(f"The following interfaces have a usage > {self.inputs.threshold}%: {failed_interfaces}")


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

    name = "VerifyInterfaceErrors"
    description = "Verifies there are no interface error counters."
    categories: ClassVar[list[str]] = ["interfaces"]
    commands: ClassVar[list[AntaCommand | AntaTemplate]] = [AntaCommand(command="show interfaces counters errors", revision=1)]

    @AntaTest.anta_test
    def test(self) -> None:
        """Main test function for VerifyInterfaceErrors."""
        command_output = self.instance_commands[0].json_output
        wrong_interfaces: list[dict[str, dict[str, int]]] = []
        for interface, counters in command_output["interfaceErrorCounters"].items():
            if any(value > 0 for value in counters.values()) and all(interface not in wrong_interface for wrong_interface in wrong_interfaces):
                wrong_interfaces.append({interface: counters})
        if not wrong_interfaces:
            self.result.is_success()
        else:
            self.result.is_failure(f"The following interface(s) have non-zero error counters: {wrong_interfaces}")


class VerifyInterfaceDiscards(AntaTest):
    """Verifies that the interfaces packet discard counters are equal to zero.

    Expected Results
    ----------------
    * Success: The test will pass if all interfaces have discard counters equal to zero.
    * Failure: The test will fail if one or more interfaces have non-zero discard counters.

    Examples
    --------
    ```yaml
    anta.tests.interfaces:
      - VerifyInterfaceDiscards:
    ```
    """

    name = "VerifyInterfaceDiscards"
    description = "Verifies there are no interface discard counters."
    categories: ClassVar[list[str]] = ["interfaces"]
    commands: ClassVar[list[AntaCommand | AntaTemplate]] = [AntaCommand(command="show interfaces counters discards", revision=1)]

    @AntaTest.anta_test
    def test(self) -> None:
        """Main test function for VerifyInterfaceDiscards."""
        command_output = self.instance_commands[0].json_output
        wrong_interfaces: list[dict[str, dict[str, int]]] = []
        for interface, outer_v in command_output["interfaces"].items():
            wrong_interfaces.extend({interface: outer_v} for value in outer_v.values() if value > 0)
        if not wrong_interfaces:
            self.result.is_success()
        else:
            self.result.is_failure(f"The following interfaces have non 0 discard counter(s): {wrong_interfaces}")


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

    name = "VerifyInterfaceErrDisabled"
    description = "Verifies there are no interfaces in the errdisabled state."
    categories: ClassVar[list[str]] = ["interfaces"]
    commands: ClassVar[list[AntaCommand | AntaTemplate]] = [AntaCommand(command="show interfaces status", revision=1)]

    @AntaTest.anta_test
    def test(self) -> None:
        """Main test function for VerifyInterfaceErrDisabled."""
        command_output = self.instance_commands[0].json_output
        errdisabled_interfaces = [interface for interface, value in command_output["interfaceStatuses"].items() if value["linkStatus"] == "errdisabled"]
        if errdisabled_interfaces:
            self.result.is_failure(f"The following interfaces are in error disabled state: {errdisabled_interfaces}")
        else:
            self.result.is_success()


class VerifyInterfacesStatus(AntaTest):
    """Verifies if the provided list of interfaces are all in the expected state.

    - If line protocol status is provided, prioritize checking against both status and line protocol status
    - If line protocol status is not provided and interface status is "up", expect both status and line protocol to be "up"
    - If interface status is not "up", check only the interface status without considering line protocol status

    Expected Results
    ----------------
    * Success: The test will pass if the provided interfaces are all in the expected state.
    * Failure: The test will fail if any interface is not in the expected state.

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

    name = "VerifyInterfacesStatus"
    description = "Verifies the status of the provided interfaces."
    categories: ClassVar[list[str]] = ["interfaces"]
    commands: ClassVar[list[AntaCommand | AntaTemplate]] = [AntaCommand(command="show interfaces description", revision=1)]

    class Input(AntaTest.Input):
        """Input model for the VerifyInterfacesStatus test."""

        interfaces: list[InterfaceState]
        """List of interfaces with their expected state."""

        class InterfaceState(BaseModel):
            """Model for an interface state."""

            name: Interface
            """Interface to validate."""
            status: Literal["up", "down", "adminDown"]
            """Expected status of the interface."""
            line_protocol_status: Literal["up", "down", "testing", "unknown", "dormant", "notPresent", "lowerLayerDown"] | None = None
            """Expected line protocol status of the interface."""

    @AntaTest.anta_test
    def test(self) -> None:
        """Main test function for VerifyInterfacesStatus."""
        command_output = self.instance_commands[0].json_output

        self.result.is_success()

        intf_not_configured = []
        intf_wrong_state = []

        for interface in self.inputs.interfaces:
            if (intf_status := get_value(command_output["interfaceDescriptions"], interface.name, separator="..")) is None:
                intf_not_configured.append(interface.name)
                continue

            status = "up" if intf_status["interfaceStatus"] in {"up", "connected"} else intf_status["interfaceStatus"]
            proto = "up" if intf_status["lineProtocolStatus"] in {"up", "connected"} else intf_status["lineProtocolStatus"]

            # If line protocol status is provided, prioritize checking against both status and line protocol status
            if interface.line_protocol_status:
                if interface.status != status or interface.line_protocol_status != proto:
                    intf_wrong_state.append(f"{interface.name} is {status}/{proto}")

            # If line protocol status is not provided and interface status is "up", expect both status and proto to be "up"
            # If interface status is not "up", check only the interface status without considering line protocol status
            elif (interface.status == "up" and (status != "up" or proto != "up")) or (interface.status != status):
                intf_wrong_state.append(f"{interface.name} is {status}/{proto}")

        if intf_not_configured:
            self.result.is_failure(f"The following interface(s) are not configured: {intf_not_configured}")

        if intf_wrong_state:
            self.result.is_failure(f"The following interface(s) are not in the expected state: {intf_wrong_state}")


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
    ```
    """

    name = "VerifyStormControlDrops"
    description = "Verifies there are no interface storm-control drop counters."
    categories: ClassVar[list[str]] = ["interfaces"]
    commands: ClassVar[list[AntaCommand | AntaTemplate]] = [AntaCommand(command="show storm-control", revision=1)]

    @skip_on_platforms(["cEOSLab", "vEOS-lab", "cEOSCloudLab"])
    @AntaTest.anta_test
    def test(self) -> None:
        """Main test function for VerifyStormControlDrops."""
        command_output = self.instance_commands[0].json_output
        storm_controlled_interfaces: dict[str, dict[str, Any]] = {}
        for interface, interface_dict in command_output["interfaces"].items():
            for traffic_type, traffic_type_dict in interface_dict["trafficTypes"].items():
                if "drop" in traffic_type_dict and traffic_type_dict["drop"] != 0:
                    storm_controlled_interface_dict = storm_controlled_interfaces.setdefault(interface, {})
                    storm_controlled_interface_dict.update({traffic_type: traffic_type_dict["drop"]})
        if not storm_controlled_interfaces:
            self.result.is_success()
        else:
            self.result.is_failure(f"The following interfaces have none 0 storm-control drop counters {storm_controlled_interfaces}")


class VerifyPortChannels(AntaTest):
    """Verifies there are no inactive ports in all port channels.

    Expected Results
    ----------------
    * Success: The test will pass if there are no inactive ports in all port channels.
    * Failure: The test will fail if there is at least one inactive port in a port channel.

    Examples
    --------
    ```yaml
    anta.tests.interfaces:
      - VerifyPortChannels:
    ```
    """

    name = "VerifyPortChannels"
    description = "Verifies there are no inactive ports in all port channels."
    categories: ClassVar[list[str]] = ["interfaces"]
    commands: ClassVar[list[AntaCommand | AntaTemplate]] = [AntaCommand(command="show port-channel", revision=1)]

    @AntaTest.anta_test
    def test(self) -> None:
        """Main test function for VerifyPortChannels."""
        command_output = self.instance_commands[0].json_output
        po_with_inactive_ports: list[dict[str, str]] = []
        for portchannel, portchannel_dict in command_output["portChannels"].items():
            if len(portchannel_dict["inactivePorts"]) != 0:
                po_with_inactive_ports.extend({portchannel: portchannel_dict["inactivePorts"]})
        if not po_with_inactive_ports:
            self.result.is_success()
        else:
            self.result.is_failure(f"The following port-channels have inactive port(s): {po_with_inactive_ports}")


class VerifyIllegalLACP(AntaTest):
    """Verifies there are no illegal LACP packets in all port channels.

    Expected Results
    ----------------
    * Success: The test will pass if there are no illegal LACP packets received.
    * Failure: The test will fail if there is at least one illegal LACP packet received.

    Examples
    --------
    ```yaml
    anta.tests.interfaces:
      - VerifyIllegalLACP:
    ```
    """

    name = "VerifyIllegalLACP"
    description = "Verifies there are no illegal LACP packets in all port channels."
    categories: ClassVar[list[str]] = ["interfaces"]
    commands: ClassVar[list[AntaCommand | AntaTemplate]] = [AntaCommand(command="show lacp counters all-ports", revision=1)]

    @AntaTest.anta_test
    def test(self) -> None:
        """Main test function for VerifyIllegalLACP."""
        command_output = self.instance_commands[0].json_output
        po_with_illegal_lacp: list[dict[str, dict[str, int]]] = []
        for portchannel, portchannel_dict in command_output["portChannels"].items():
            po_with_illegal_lacp.extend(
                {portchannel: interface} for interface, interface_dict in portchannel_dict["interfaces"].items() if interface_dict["illegalRxCount"] != 0
            )
        if not po_with_illegal_lacp:
            self.result.is_success()
        else:
            self.result.is_failure(f"The following port-channels have received illegal LACP packets on the following ports: {po_with_illegal_lacp}")


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

    name = "VerifyLoopbackCount"
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
        command_output = self.instance_commands[0].json_output
        loopback_count = 0
        down_loopback_interfaces = []
        for interface in command_output["interfaces"]:
            interface_dict = command_output["interfaces"][interface]
            if "Loopback" in interface:
                loopback_count += 1
                if not (interface_dict["lineProtocolStatus"] == "up" and interface_dict["interfaceStatus"] == "connected"):
                    down_loopback_interfaces.append(interface)
        if loopback_count == self.inputs.number and len(down_loopback_interfaces) == 0:
            self.result.is_success()
        else:
            self.result.is_failure()
            if loopback_count != self.inputs.number:
                self.result.is_failure(f"Found {loopback_count} Loopbacks when expecting {self.inputs.number}")
            elif len(down_loopback_interfaces) != 0:  # pragma: no branch
                self.result.is_failure(f"The following Loopbacks are not up: {down_loopback_interfaces}")


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

    name = "VerifySVI"
    description = "Verifies the status of all SVIs."
    categories: ClassVar[list[str]] = ["interfaces"]
    commands: ClassVar[list[AntaCommand | AntaTemplate]] = [AntaCommand(command="show ip interface brief", revision=1)]

    @AntaTest.anta_test
    def test(self) -> None:
        """Main test function for VerifySVI."""
        command_output = self.instance_commands[0].json_output
        down_svis = []
        for interface in command_output["interfaces"]:
            interface_dict = command_output["interfaces"][interface]
            if "Vlan" in interface and not (interface_dict["lineProtocolStatus"] == "up" and interface_dict["interfaceStatus"] == "connected"):
                down_svis.append(interface)
        if len(down_svis) == 0:
            self.result.is_success()
        else:
            self.result.is_failure(f"The following SVIs are not up: {down_svis}")


class VerifyL3MTU(AntaTest):
    """Verifies the global layer 3 Maximum Transfer Unit (MTU) for all L3 interfaces.

    Test that L3 interfaces are configured with the correct MTU. It supports Ethernet, Port Channel and VLAN interfaces.

    You can define a global MTU to check, or an MTU per interface and you can also ignored some interfaces.

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
              - Vxlan1
          specific_mtu:
              - Ethernet1: 2500
    ```
    """

    name = "VerifyL3MTU"
    description = "Verifies the global L3 MTU of all L3 interfaces."
    categories: ClassVar[list[str]] = ["interfaces"]
    commands: ClassVar[list[AntaCommand | AntaTemplate]] = [AntaCommand(command="show interfaces", revision=1)]

    class Input(AntaTest.Input):
        """Input model for the VerifyL3MTU test."""

        mtu: int = 1500
        """Default MTU we should have configured on all non-excluded interfaces. Defaults to 1500."""
        ignored_interfaces: list[str] = Field(default=["Management", "Loopback", "Vxlan", "Tunnel"])
        """A list of L3 interfaces to ignore"""
        specific_mtu: list[dict[str, int]] = Field(default=[])
        """A list of dictionary of L3 interfaces with their specific MTU configured"""

    @AntaTest.anta_test
    def test(self) -> None:
        """Main test function for VerifyL3MTU."""
        # Parameter to save incorrect interface settings
        wrong_l3mtu_intf: list[dict[str, int]] = []
        command_output = self.instance_commands[0].json_output
        # Set list of interfaces with specific settings
        specific_interfaces: list[str] = []
        if self.inputs.specific_mtu:
            for d in self.inputs.specific_mtu:
                specific_interfaces.extend(d)
        for interface, values in command_output["interfaces"].items():
            if re.findall(r"[a-z]+", interface, re.IGNORECASE)[0] not in self.inputs.ignored_interfaces and values["forwardingModel"] == "routed":
                if interface in specific_interfaces:
                    wrong_l3mtu_intf.extend({interface: values["mtu"]} for custom_data in self.inputs.specific_mtu if values["mtu"] != custom_data[interface])
                # Comparison with generic setting
                elif values["mtu"] != self.inputs.mtu:
                    wrong_l3mtu_intf.append({interface: values["mtu"]})
        if wrong_l3mtu_intf:
            self.result.is_failure(f"Some interfaces do not have correct MTU configured:\n{wrong_l3mtu_intf}")
        else:
            self.result.is_success()


class VerifyIPProxyARP(AntaTest):
    """Verifies if Proxy-ARP is enabled for the provided list of interface(s).

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

    name = "VerifyIPProxyARP"
    description = "Verifies if Proxy ARP is enabled."
    categories: ClassVar[list[str]] = ["interfaces"]
    commands: ClassVar[list[AntaCommand | AntaTemplate]] = [AntaTemplate(template="show ip interface {intf}", revision=2)]

    class Input(AntaTest.Input):
        """Input model for the VerifyIPProxyARP test."""

        interfaces: list[str]
        """List of interfaces to be tested."""

    def render(self, template: AntaTemplate) -> list[AntaCommand]:
        """Render the template for each interface in the input list."""
        return [template.render(intf=intf) for intf in self.inputs.interfaces]

    @AntaTest.anta_test
    def test(self) -> None:
        """Main test function for VerifyIPProxyARP."""
        disabled_intf = []
        for command in self.instance_commands:
            intf = command.params.intf
            if not command.json_output["interfaces"][intf]["proxyArp"]:
                disabled_intf.append(intf)
        if disabled_intf:
            self.result.is_failure(f"The following interface(s) have Proxy-ARP disabled: {disabled_intf}")
        else:
            self.result.is_success()


class VerifyL2MTU(AntaTest):
    """Verifies the global layer 2 Maximum Transfer Unit (MTU) for all L2 interfaces.

    Test that L2 interfaces are configured with the correct MTU. It supports Ethernet, Port Channel and VLAN interfaces.
    You can define a global MTU to check and also an MTU per interface and also ignored some interfaces.

    Expected Results
    ----------------
    * Success: The test will pass if all layer 2 interfaces have the proper MTU configured.
    * Failure: The test will fail if one or many layer 2 interfaces have the wrong MTU configured.

    Examples
    --------
    ```yaml
    anta.tests.interfaces:
      - VerifyL2MTU:
          mtu: 1500
          ignored_interfaces:
            - Management1
            - Vxlan1
          specific_mtu:
            - Ethernet1/1: 1500
    ```
    """

    name = "VerifyL2MTU"
    description = "Verifies the global L2 MTU of all L2 interfaces."
    categories: ClassVar[list[str]] = ["interfaces"]
    commands: ClassVar[list[AntaCommand | AntaTemplate]] = [AntaCommand(command="show interfaces", revision=1)]

    class Input(AntaTest.Input):
        """Input model for the VerifyL2MTU test."""

        mtu: int = 9214
        """Default MTU we should have configured on all non-excluded interfaces. Defaults to 9214."""
        ignored_interfaces: list[str] = Field(default=["Management", "Loopback", "Vxlan", "Tunnel"])
        """A list of L2 interfaces to ignore. Defaults to ["Management", "Loopback", "Vxlan", "Tunnel"]"""
        specific_mtu: list[dict[str, int]] = Field(default=[])
        """A list of dictionary of L2 interfaces with their specific MTU configured"""

    @AntaTest.anta_test
    def test(self) -> None:
        """Main test function for VerifyL2MTU."""
        # Parameter to save incorrect interface settings
        wrong_l2mtu_intf: list[dict[str, int]] = []
        command_output = self.instance_commands[0].json_output
        # Set list of interfaces with specific settings
        specific_interfaces: list[str] = []
        if self.inputs.specific_mtu:
            for d in self.inputs.specific_mtu:
                specific_interfaces.extend(d)
        for interface, values in command_output["interfaces"].items():
            catch_interface = re.findall(r"^[e,p][a-zA-Z]+[-,a-zA-Z]*\d+\/*\d*", interface, re.IGNORECASE)
            if len(catch_interface) and catch_interface[0] not in self.inputs.ignored_interfaces and values["forwardingModel"] == "bridged":
                if interface in specific_interfaces:
                    wrong_l2mtu_intf.extend({interface: values["mtu"]} for custom_data in self.inputs.specific_mtu if values["mtu"] != custom_data[interface])
                # Comparison with generic setting
                elif values["mtu"] != self.inputs.mtu:
                    wrong_l2mtu_intf.append({interface: values["mtu"]})
        if wrong_l2mtu_intf:
            self.result.is_failure(f"Some L2 interfaces do not have correct MTU configured:\n{wrong_l2mtu_intf}")
        else:
            self.result.is_success()


class VerifyInterfaceIPv4(AntaTest):
    """Verifies if an interface is configured with a correct primary and list of optional secondary IPv4 addresses.

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
              primary_ip: 172.30.11.0/31
              secondary_ips:
                - 10.10.10.0/31
                - 10.10.10.10/31
    ```
    """

    name = "VerifyInterfaceIPv4"
    description = "Verifies the interface IPv4 addresses."
    categories: ClassVar[list[str]] = ["interfaces"]
    commands: ClassVar[list[AntaCommand | AntaTemplate]] = [AntaTemplate(template="show ip interface {interface}", revision=2)]

    class Input(AntaTest.Input):
        """Input model for the VerifyInterfaceIPv4 test."""

        interfaces: list[InterfaceDetail]
        """List of interfaces with their details."""

        class InterfaceDetail(BaseModel):
            """Model for an interface detail."""

            name: Interface
            """Name of the interface."""
            primary_ip: IPv4Network
            """Primary IPv4 address in CIDR notation."""
            secondary_ips: list[IPv4Network] | None = None
            """Optional list of secondary IPv4 addresses in CIDR notation."""

    def render(self, template: AntaTemplate) -> list[AntaCommand]:
        """Render the template for each interface in the input list."""
        return [template.render(interface=interface.name) for interface in self.inputs.interfaces]

    @AntaTest.anta_test
    def test(self) -> None:
        """Main test function for VerifyInterfaceIPv4."""
        self.result.is_success()
        for command in self.instance_commands:
            intf = command.params.interface
            for interface in self.inputs.interfaces:
                if interface.name == intf:
                    input_interface_detail = interface
                    break
            else:
                self.result.is_failure(f"Could not find `{intf}` in the input interfaces. {GITHUB_SUGGESTION}")
                continue

            input_primary_ip = str(input_interface_detail.primary_ip)
            failed_messages = []

            # Check if the interface has an IP address configured
            if not (interface_output := get_value(command.json_output, f"interfaces.{intf}.interfaceAddress")):
                self.result.is_failure(f"For interface `{intf}`, IP address is not configured.")
                continue

            primary_ip = get_value(interface_output, "primaryIp")

            # Combine IP address and subnet for primary IP
            actual_primary_ip = f"{primary_ip['address']}/{primary_ip['maskLen']}"

            # Check if the primary IP address matches the input
            if actual_primary_ip != input_primary_ip:
                failed_messages.append(f"The expected primary IP address is `{input_primary_ip}`, but the actual primary IP address is `{actual_primary_ip}`.")

            if (param_secondary_ips := input_interface_detail.secondary_ips) is not None:
                input_secondary_ips = sorted([str(network) for network in param_secondary_ips])
                secondary_ips = get_value(interface_output, "secondaryIpsOrderedList")

                # Combine IP address and subnet for secondary IPs
                actual_secondary_ips = sorted([f"{secondary_ip['address']}/{secondary_ip['maskLen']}" for secondary_ip in secondary_ips])

                # Check if the secondary IP address is configured
                if not actual_secondary_ips:
                    failed_messages.append(
                        f"The expected secondary IP addresses are `{input_secondary_ips}`, but the actual secondary IP address is not configured."
                    )

                # Check if the secondary IP addresses match the input
                elif actual_secondary_ips != input_secondary_ips:
                    failed_messages.append(
                        f"The expected secondary IP addresses are `{input_secondary_ips}`, but the actual secondary IP addresses are `{actual_secondary_ips}`."
                    )

            if failed_messages:
                self.result.is_failure(f"For interface `{intf}`, " + " ".join(failed_messages))


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

    name = "VerifyIpVirtualRouterMac"
    description = "Verifies the IP virtual router MAC address."
    categories: ClassVar[list[str]] = ["interfaces"]
    commands: ClassVar[list[AntaCommand | AntaTemplate]] = [AntaCommand(command="show ip virtual-router", revision=2)]

    class Input(AntaTest.Input):
        """Input model for the VerifyIpVirtualRouterMac test."""

        mac_address: MacAddress
        """IP virtual router MAC address."""

    @AntaTest.anta_test
    def test(self) -> None:
        """Main test function for VerifyIpVirtualRouterMac."""
        command_output = self.instance_commands[0].json_output["virtualMacs"]
        mac_address_found = get_item(command_output, "macAddress", self.inputs.mac_address)

        if mac_address_found is None:
            self.result.is_failure(f"IP virtual router MAC address `{self.inputs.mac_address}` is not configured.")
        else:
            self.result.is_success()


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

    name = "VerifyInterfacesSpeed"
    description = "Verifies the speed, lanes, auto-negotiation status, and mode as full duplex for interfaces."
    categories: ClassVar[list[str]] = ["interfaces"]
    commands: ClassVar[list[AntaCommand | AntaTemplate]] = [AntaCommand(command="show interfaces")]

    class Input(AntaTest.Input):
        """Inputs for the VerifyInterfacesSpeed test."""

        interfaces: list[InterfaceDetail]
        """List of interfaces to be tested"""

        class InterfaceDetail(BaseModel):
            """Detail of an interface."""

            name: EthernetInterface
            """The name of the interface."""
            auto: bool
            """The auto-negotiation status of the interface."""
            speed: float = Field(ge=1, le=1000)
            """The speed of the interface in Gigabits per second. Valid range is 1 to 1000."""
            lanes: None | int = Field(None, ge=1, le=8)
            """The number of lanes in the interface. Valid range is 1 to 8. This field is optional."""

    @AntaTest.anta_test
    def test(self) -> None:
        """Main test function for VerifyInterfacesSpeed."""
        self.result.is_success()
        command_output = self.instance_commands[0].json_output

        # Iterate over all the interfaces
        for interface in self.inputs.interfaces:
            intf = interface.name

            # Check if interface exists
            if not (interface_output := get_value(command_output, f"interfaces.{intf}")):
                self.result.is_failure(f"Interface `{intf}` is not found.")
                continue

            auto_negotiation = interface_output.get("autoNegotiate")
            actual_lanes = interface_output.get("lanes")

            # Collecting actual interface details
            actual_interface_output = {
                "auto negotiation": auto_negotiation if interface.auto is True else None,
                "duplex mode": interface_output.get("duplex"),
                "speed": interface_output.get("bandwidth"),
                "lanes": actual_lanes if interface.lanes is not None else None,
            }

            # Forming expected interface details
            expected_interface_output = {
                "auto negotiation": "success" if interface.auto is True else None,
                "duplex mode": "duplexFull",
                "speed": interface.speed * BPS_GBPS_CONVERSIONS,
                "lanes": interface.lanes,
            }

            # Forming failure message
            if actual_interface_output != expected_interface_output:
                for output in [actual_interface_output, expected_interface_output]:
                    # Convert speed to Gbps for readability
                    if output["speed"] is not None:
                        output["speed"] = f"{custom_division(output['speed'], BPS_GBPS_CONVERSIONS)}Gbps"
                failed_log = get_failed_logs(expected_interface_output, actual_interface_output)
                self.result.is_failure(f"For interface {intf}:{failed_log}\n")


class VerifyLACPInterfacesStatus(AntaTest):
    """Verifies the Link Aggregation Control Protocol (LACP) status of the provided interfaces.

    - Verifies that the interface is a member of the LACP port channel.
    - Ensures that the synchronization is established.
    - Ensures the interfaces are in the correct state for collecting and distributing traffic.
    - Validates that LACP settings, such as timeouts, are correctly configured. (i.e The long timeout mode, also known as "slow" mode, is the default setting.)

    Expected Results
    ----------------
    * Success: The test will pass if the provided interfaces are bundled in port channel and all specified parameters are correct.
    * Failure: The test will fail if any interface is not bundled in port channel or any of specified parameter is not correct.

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

    name = "VerifyLACPInterfacesStatus"
    description = "Verifies the Link Aggregation Control Protocol(LACP) status of the provided interfaces."
    categories: ClassVar[list[str]] = ["interfaces"]
    commands: ClassVar[list[AntaCommand | AntaTemplate]] = [AntaTemplate(template="show lacp interface {interface}", revision=1)]

    class Input(AntaTest.Input):
        """Input model for the VerifyLACPInterfacesStatus test."""

        interfaces: list[LACPInterface]
        """List of LACP member interface."""

        class LACPInterface(BaseModel):
            """Model for an LACP member interface."""

            name: EthernetInterface
            """Ethernet interface to validate."""
            portchannel: PortChannelInterface
            """Port Channel in which the interface is bundled."""

    def render(self, template: AntaTemplate) -> list[AntaCommand]:
        """Render the template for each interface in the input list."""
        return [template.render(interface=interface.name) for interface in self.inputs.interfaces]

    @AntaTest.anta_test
    def test(self) -> None:
        """Main test function for VerifyLACPInterfacesStatus."""
        self.result.is_success()

        # Member port verification parameters.
        member_port_details = ["activity", "aggregation", "synchronization", "collecting", "distributing", "timeout"]

        # Iterating over command output for different interfaces
        for command, input_entry in zip(self.instance_commands, self.inputs.interfaces):
            interface = input_entry.name
            portchannel = input_entry.portchannel

            # Verify if a PortChannel is configured with the provided interface
            if not (interface_details := get_value(command.json_output, f"portChannels.{portchannel}.interfaces.{interface}")):
                self.result.is_failure(f"Interface '{interface}' is not configured to be a member of LACP '{portchannel}'.")
                continue

            # Verify the interface is bundled in port channel.
            actor_port_status = interface_details.get("actorPortStatus")
            if actor_port_status != "bundled":
                message = f"For Interface {interface}:\nExpected `bundled` as the local port status, but found `{actor_port_status}` instead.\n"
                self.result.is_failure(message)
                continue

            # Collecting actor and partner port details
            actor_port_details = interface_details.get("actorPortState", {})
            partner_port_details = interface_details.get("partnerPortState", {})

            # Collecting actual interface details
            actual_interface_output = {
                "actor_port_details": {param: actor_port_details.get(param, "NotFound") for param in member_port_details},
                "partner_port_details": {param: partner_port_details.get(param, "NotFound") for param in member_port_details},
            }

            # Forming expected interface details
            expected_details = {param: param != "timeout" for param in member_port_details}
            expected_interface_output = {"actor_port_details": expected_details, "partner_port_details": expected_details}

            # Forming failure message
            if actual_interface_output != expected_interface_output:
                message = f"For Interface {interface}:\n"
                actor_port_failed_log = get_failed_logs(
                    expected_interface_output.get("actor_port_details", {}), actual_interface_output.get("actor_port_details", {})
                )
                partner_port_failed_log = get_failed_logs(
                    expected_interface_output.get("partner_port_details", {}), actual_interface_output.get("partner_port_details", {})
                )

                if actor_port_failed_log:
                    message += f"Actor port details:{actor_port_failed_log}\n"
                if partner_port_failed_log:
                    message += f"Partner port details:{partner_port_failed_log}\n"

                self.result.is_failure(message)
