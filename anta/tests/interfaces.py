# Copyright (c) 2023 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""
Test functions related to the device interfaces
"""
# Mypy does not understand AntaTest.Input typing
# mypy: disable-error-code=attr-defined
from __future__ import annotations

import re

# Need to keep Dict and List for pydantic in python 3.8
from typing import Any, Dict, List, Literal

from pydantic import BaseModel, conint

from anta.custom_types import Interface
from anta.decorators import skip_on_platforms
from anta.models import AntaCommand, AntaTemplate, AntaTest
from anta.tools.get_value import get_value


class VerifyInterfaceUtilization(AntaTest):
    """
    Verifies interfaces utilization is below 75%.
    """

    name = "VerifyInterfaceUtilization"
    description = "Verifies interfaces utilization is below 75%."
    categories = ["interfaces"]
    # TODO - move from text to json if possible
    commands = [AntaCommand(command="show interfaces counters rates", ofmt="text")]

    @AntaTest.anta_test
    def test(self) -> None:
        command_output = self.instance_commands[0].text_output
        wrong_interfaces = {}
        for line in command_output.split("\n")[1:]:
            if len(line) > 0:
                if line.split()[-5] == "-" or line.split()[-2] == "-":
                    pass
                elif float(line.split()[-5].replace("%", "")) > 75.0:
                    wrong_interfaces[line.split()[0]] = line.split()[-5]
                elif float(line.split()[-2].replace("%", "")) > 75.0:
                    wrong_interfaces[line.split()[0]] = line.split()[-2]
        if not wrong_interfaces:
            self.result.is_success()
        else:
            self.result.is_failure(f"The following interfaces have a usage > 75%: {wrong_interfaces}")


class VerifyInterfaceErrors(AntaTest):
    """
    This test verifies that interfaces error counters are equal to zero.

    Expected Results:
        * success: The test will pass if all interfaces have error counters equal to zero.
        * failure: The test will fail if one or more interfaces have non-zero error counters.
    """

    name = "VerifyInterfaceErrors"
    description = "Verifies that interfaces error counters are equal to zero."
    categories = ["interfaces"]
    commands = [AntaCommand(command="show interfaces counters errors")]

    @AntaTest.anta_test
    def test(self) -> None:
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
    """
    Verifies interfaces packet discard counters are equal to zero.
    """

    name = "VerifyInterfaceDiscards"
    description = "Verifies interfaces packet discard counters are equal to zero."
    categories = ["interfaces"]
    commands = [AntaCommand(command="show interfaces counters discards")]

    @AntaTest.anta_test
    def test(self) -> None:
        command_output = self.instance_commands[0].json_output
        wrong_interfaces: list[dict[str, dict[str, int]]] = []
        for interface, outer_v in command_output["interfaces"].items():
            wrong_interfaces.extend({interface: outer_v} for counter, value in outer_v.items() if value > 0)
        if not wrong_interfaces:
            self.result.is_success()
        else:
            self.result.is_failure(f"The following interfaces have non 0 discard counter(s): {wrong_interfaces}")


class VerifyInterfaceErrDisabled(AntaTest):
    """
    Verifies there is no interface in error disable state.
    """

    name = "VerifyInterfaceErrDisabled"
    description = "Verifies there is no interface in error disable state."
    categories = ["interfaces"]
    commands = [AntaCommand(command="show interfaces status")]

    @AntaTest.anta_test
    def test(self) -> None:
        command_output = self.instance_commands[0].json_output
        errdisabled_interfaces = [interface for interface, value in command_output["interfaceStatuses"].items() if value["linkStatus"] == "errdisabled"]
        if errdisabled_interfaces:
            self.result.is_failure(f"The following interfaces are in error disabled state: {errdisabled_interfaces}")
        else:
            self.result.is_success()


class VerifyInterfacesStatus(AntaTest):
    """
    This test verifies if the provided list of interfaces are all in the expected state.

    Expected Results:
        * success: The test will pass if the provided interfaces are all in the expected state.
        * failure: The test will fail if any interface is not in the expected state.
    """

    name = "VerifyInterfacesStatus"
    description = "Verifies if the provided list of interfaces are all in the expected state."
    categories = ["interfaces"]
    commands = [AntaCommand(command="show interfaces description")]

    class Input(AntaTest.Input):  # pylint: disable=missing-class-docstring
        interfaces: List[InterfaceStatus]
        """List of interfaces to validate with the expected state"""

        class InterfaceStatus(BaseModel):  # pylint: disable=missing-class-docstring
            interface: Interface
            state: Literal["up", "adminDown"]
            protocol_status: Literal["up", "down"] = "up"

    @AntaTest.anta_test
    def test(self) -> None:
        command_output = self.instance_commands[0].json_output

        self.result.is_success()

        intf_not_configured = []
        intf_wrong_state = []

        for interface_status in self.inputs.interfaces:
            intf_status = get_value(command_output["interfaceDescriptions"], interface_status.interface, separator=";")
            if intf_status is None:
                intf_not_configured.append(interface_status.interface)
                continue

            proto = intf_status["lineProtocolStatus"]
            status = intf_status["interfaceStatus"]

            if interface_status.state == "up" and not (re.match(r"connected|up", proto) and re.match(r"connected|up", status)):
                intf_wrong_state.append(f"{interface_status.interface} is {proto}/{status} expected {interface_status.protocol_status}/{interface_status.state}")
            elif interface_status.state == "adminDown":
                if interface_status.protocol_status == "up" and not (re.match(r"up", proto) and re.match(r"adminDown", status)):
                    intf_wrong_state.append(f"{interface_status.interface} is {proto}/{status} expected {interface_status.protocol_status}/{interface_status.state}")
                elif interface_status.protocol_status == "down" and not (re.match(r"down", proto) and re.match(r"adminDown", status)):
                    intf_wrong_state.append(f"{interface_status.interface} is {proto}/{status} expected {interface_status.protocol_status}/{interface_status.state}")

        if intf_not_configured:
            self.result.is_failure(f"The following interface(s) are not configured: {intf_not_configured}")

        if intf_wrong_state:
            self.result.is_failure(f"The following interface(s) are not in the expected state: {intf_wrong_state}")


class VerifyStormControlDrops(AntaTest):
    """
    Verifies the device did not drop packets due its to storm-control configuration.
    """

    name = "VerifyStormControlDrops"
    description = "Verifies the device did not drop packets due its to storm-control configuration."
    categories = ["interfaces"]
    commands = [AntaCommand(command="show storm-control")]

    @skip_on_platforms(["cEOSLab", "vEOS-lab"])
    @AntaTest.anta_test
    def test(self) -> None:
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
    """
    Verifies there is no inactive port in port channels.
    """

    name = "VerifyPortChannels"
    description = "Verifies there is no inactive port in port channels."
    categories = ["interfaces"]
    commands = [AntaCommand(command="show port-channel")]

    @skip_on_platforms(["cEOSLab", "vEOS-lab"])
    @AntaTest.anta_test
    def test(self) -> None:
        command_output = self.instance_commands[0].json_output
        po_with_invactive_ports: list[dict[str, str]] = []
        for portchannel, portchannel_dict in command_output["portChannels"].items():
            if len(portchannel_dict["inactivePorts"]) != 0:
                po_with_invactive_ports.extend({portchannel: portchannel_dict["inactivePorts"]})
        if not po_with_invactive_ports:
            self.result.is_success()
        else:
            self.result.is_failure(f"The following port-channels have inactive port(s): {po_with_invactive_ports}")


class VerifyIllegalLACP(AntaTest):
    """
    Verifies there is no illegal LACP packets received.
    """

    name = "VerifyIllegalLACP"
    description = "Verifies there is no illegal LACP packets received."
    categories = ["interfaces"]
    commands = [AntaCommand(command="show lacp counters all-ports")]

    @AntaTest.anta_test
    def test(self) -> None:
        command_output = self.instance_commands[0].json_output
        po_with_illegal_lacp: list[dict[str, dict[str, int]]] = []
        for portchannel, portchannel_dict in command_output["portChannels"].items():
            po_with_illegal_lacp.extend(
                {portchannel: interface} for interface, interface_dict in portchannel_dict["interfaces"].items() if interface_dict["illegalRxCount"] != 0
            )
        if not po_with_illegal_lacp:
            self.result.is_success()
        else:
            self.result.is_failure("The following port-channels have recieved illegal lacp packets on the " f"following ports: {po_with_illegal_lacp}")


class VerifyLoopbackCount(AntaTest):
    """
    Verifies the number of loopback interfaces on the device is the one we expect and if none of the loopback is down.
    """

    name = "VerifyLoopbackCount"
    description = "Verifies the number of loopback interfaces on the device is the one we expect and if none of the loopback is down."
    categories = ["interfaces"]
    commands = [AntaCommand(command="show ip interface brief")]

    class Input(AntaTest.Input):  # pylint: disable=missing-class-docstring
        number: conint(ge=0)  # type: ignore
        """Number of loopback interfaces expected to be present"""

    @AntaTest.anta_test
    def test(self) -> None:
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
            elif len(down_loopback_interfaces) != 0:
                self.result.is_failure(f"The following Loopbacks are not up: {down_loopback_interfaces}")


class VerifySVI(AntaTest):
    """
    Verifies there is no interface vlan down.
    """

    name = "VerifySVI"
    description = "Verifies there is no interface vlan down."
    categories = ["interfaces"]
    commands = [AntaCommand(command="show ip interface brief")]

    @AntaTest.anta_test
    def test(self) -> None:
        command_output = self.instance_commands[0].json_output
        down_svis = []
        for interface in command_output["interfaces"]:
            interface_dict = command_output["interfaces"][interface]
            if "Vlan" in interface:
                if not (interface_dict["lineProtocolStatus"] == "up" and interface_dict["interfaceStatus"] == "connected"):
                    down_svis.append(interface)
        if len(down_svis) == 0:
            self.result.is_success()
        else:
            self.result.is_failure(f"The following SVIs are not up: {down_svis}")


class VerifyL3MTU(AntaTest):
    """
    Verifies the global layer 3 Maximum Transfer Unit (MTU) for all L3 interfaces.

    Test that L3 interfaces are configured with the correct MTU. It supports Ethernet, Port Channel and VLAN interfaces.
    You can define a global MTU to check and also an MTU per interface and also ignored some interfaces.

    Expected Results:
        * success: The test will pass if all layer 3 interfaces have the proper MTU configured.
        * failure: The test will fail if one or many layer 3 interfaces have the wrong MTU configured.
    """

    name = "VerifyL3MTU"
    description = "Verifies the global layer 3 Maximum Transfer Unit (MTU) for all layer 3 interfaces."
    categories = ["interfaces"]
    commands = [AntaCommand(command="show interfaces")]

    class Input(AntaTest.Input):  # pylint: disable=missing-class-docstring
        mtu: int = 1500
        """Default MTU we should have configured on all non-excluded interfaces"""
        ignored_interfaces: List[str] = ["Management", "Loopback", "Vxlan", "Tunnel"]
        """A list of L3 interfaces to ignore"""
        specific_mtu: List[Dict[str, int]] = []
        """A list of dictionary of L3 interfaces with their specific MTU configured"""

    @AntaTest.anta_test
    def test(self) -> None:
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
    """
    Verifies if Proxy-ARP is enabled for the provided list of interface(s).

    Expected Results:
        * success: The test will pass if Proxy-ARP is enabled on the specified interface(s).
        * failure: The test will fail if Proxy-ARP is disabled on the specified interface(s).
    """

    name = "VerifyIPProxyARP"
    description = "Verifies if Proxy-ARP is enabled for the provided list of interface(s)."
    categories = ["interfaces"]
    commands = [AntaTemplate(template="show ip interface {intf}")]

    class Input(AntaTest.Input):  # pylint: disable=missing-class-docstring
        interfaces: List[str]
        """list of interfaces to be tested"""

    def render(self, template: AntaTemplate) -> list[AntaCommand]:
        return [template.render(intf=intf) for intf in self.inputs.interfaces]

    @AntaTest.anta_test
    def test(self) -> None:
        disabled_intf = []
        for command in self.instance_commands:
            if "intf" in command.params:
                intf = command.params["intf"]
            if not command.json_output["interfaces"][intf]["proxyArp"]:
                disabled_intf.append(intf)
        if disabled_intf:
            self.result.is_failure(f"The following interface(s) have Proxy-ARP disabled: {disabled_intf}")
        else:
            self.result.is_success()


class VerifyL2MTU(AntaTest):
    """
    Verifies the global layer 2 Maximum Transfer Unit (MTU) for all L2 interfaces.

    Test that L2 interfaces are configured with the correct MTU. It supports Ethernet, Port Channel and VLAN interfaces.
    You can define a global MTU to check and also an MTU per interface and also ignored some interfaces.

    Expected Results:
        * success: The test will pass if all layer 2 interfaces have the proper MTU configured.
        * failure: The test will fail if one or many layer 2 interfaces have the wrong MTU configured.
    """

    name = "VerifyL2MTU"
    description = "Verifies the global layer 2 Maximum Transfer Unit (MTU) for all layer 2 interfaces."
    categories = ["interfaces"]
    commands = [AntaCommand(command="show interfaces")]

    class Input(AntaTest.Input):  # pylint: disable=missing-class-docstring
        mtu: int = 9214
        """Default MTU we should have configured on all non-excluded interfaces"""
        ignored_interfaces: List[str] = ["Management", "Loopback", "Vxlan", "Tunnel"]
        """A list of L2 interfaces to ignore"""
        specific_mtu: List[Dict[str, int]] = []
        """A list of dictionary of L2 interfaces with their specific MTU configured"""

    @AntaTest.anta_test
    def test(self) -> None:
        # Parameter to save incorrect interface settings
        wrong_l2mtu_intf: list[dict[str, int]] = []
        command_output = self.instance_commands[0].json_output
        # Set list of interfaces with specific settings
        specific_interfaces: list[str] = []
        if self.inputs.specific_mtu:
            for d in self.inputs.specific_mtu:
                specific_interfaces.extend(d)
        for interface, values in command_output["interfaces"].items():
            if re.findall(r"[a-z]+", interface, re.IGNORECASE)[0] not in self.inputs.ignored_interfaces and values["forwardingModel"] == "bridged":
                if interface in specific_interfaces:
                    wrong_l2mtu_intf.extend({interface: values["mtu"]} for custom_data in self.inputs.specific_mtu if values["mtu"] != custom_data[interface])
                # Comparison with generic setting
                elif values["mtu"] != self.inputs.mtu:
                    wrong_l2mtu_intf.append({interface: values["mtu"]})
        if wrong_l2mtu_intf:
            self.result.is_failure(f"Some L2 interfaces do not have correct MTU configured:\n{wrong_l2mtu_intf}")
        else:
            self.result.is_success()
