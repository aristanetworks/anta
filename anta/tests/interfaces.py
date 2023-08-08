"""
Test functions related to the device interfaces
"""

import re
from typing import Any, Dict, List, Optional

from anta.decorators import skip_on_platforms
from anta.models import AntaCommand, AntaTemplate, AntaTest


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
        """Run VerifyInterfaceUtilization validation"""

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
        """
        Run VerifyInterfaceErrors validation
        """
        command_output = self.instance_commands[0].json_output

        wrong_interfaces: List[Dict[str, Dict[str, int]]] = []
        for interface, counters in command_output["interfaceErrorCounters"].items():
            if any(value > 0 for value in counters.values()) and not any(interface in wrong_interface for wrong_interface in wrong_interfaces):
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
        """Run VerifyInterfaceDiscards validation"""

        command_output = self.instance_commands[0].json_output

        wrong_interfaces: List[Dict[str, Dict[str, int]]] = []

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
        """Run VerifyInterfaceErrDisabled validation"""

        command_output = self.instance_commands[0].json_output

        errdisabled_interfaces = [interface for interface, value in command_output["interfaceStatuses"].items() if value["linkStatus"] == "errdisabled"]

        if errdisabled_interfaces:
            self.result.is_failure(f"The following interfaces are in error disabled state: {errdisabled_interfaces}")
        else:
            self.result.is_success()


class VerifyInterfacesStatus(AntaTest):
    """
    Verifies the number of Ethernet interfaces up/up on the device is higher or equal than a value.
    """

    name = "VerifyInterfacesStatus"
    description = "Verifies the number of Ethernet interfaces up/up on the device is higher or equal than a value."
    categories = ["interfaces"]
    commands = [AntaCommand(command="show interfaces description")]

    @AntaTest.anta_test
    def test(self, minimum: Optional[int] = None) -> None:
        """
        Run VerifyInterfacesStatus validation

        Args:
            minimum: Expected minimum number of Ethernet interfaces up/up.
        """

        if minimum is None or minimum < 0:
            self.result.is_skipped(f"VerifyInterfacesStatus was not run as an invalid minimum value was given {minimum}.")
            return

        command_output = self.instance_commands[0].json_output

        count_up_up = 0
        other_ethernet_interfaces = []

        for interface in command_output["interfaceDescriptions"]:
            interface_dict = command_output["interfaceDescriptions"][interface]
            if "Ethernet" in interface:
                if re.match(r"connected|up", interface_dict["lineProtocolStatus"]) and re.match(r"connected|up", interface_dict["interfaceStatus"]):
                    count_up_up += 1
                else:
                    other_ethernet_interfaces.append(interface)

        if count_up_up >= minimum:
            self.result.is_success()
        else:
            self.result.is_failure(f"Only {count_up_up}, less than {minimum} Ethernet interfaces are UP/UP")
            self.result.messages.append(f"The following Ethernet interfaces are not UP/UP: {other_ethernet_interfaces}")


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
        """Run VerifyStormControlDrops validation"""

        command_output = self.instance_commands[0].json_output

        storm_controlled_interfaces: Dict[str, Dict[str, Any]] = {}
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
        """Run VerifyPortChannels validation"""

        command_output = self.instance_commands[0].json_output

        po_with_invactive_ports: List[Dict[str, str]] = []
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
        """Run VerifyIllegalLACP validation"""

        command_output = self.instance_commands[0].json_output

        po_with_illegal_lacp: List[Dict[str, Dict[str, int]]] = []
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

    @AntaTest.anta_test
    def test(self, number: Optional[int] = None) -> None:
        """
        Run VerifyLoopbackCount validation

        Args:
            number: Number of loopback interfaces expected to be present.
        """

        if number is None:
            self.result.is_skipped("VerifyLoopbackCount was not run as no number value was given.")
            return

        command_output = self.instance_commands[0].json_output

        loopback_count = 0
        down_loopback_interfaces = []

        for interface in command_output["interfaces"]:
            interface_dict = command_output["interfaces"][interface]
            if "Loopback" in interface:
                loopback_count += 1
                if not (interface_dict["lineProtocolStatus"] == "up" and interface_dict["interfaceStatus"] == "connected"):
                    down_loopback_interfaces.append(interface)

        if loopback_count == number and len(down_loopback_interfaces) == 0:
            self.result.is_success()
        else:
            self.result.is_failure()
            if loopback_count != number:
                self.result.is_failure(f"Found {loopback_count} Loopbacks when expecting {number}")
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
        """Run VerifySVI validation"""

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

    Default ignored interfaces: ["Management", "Loopback", "Vxlan", "Tunnel"]

    Expected Results:
        * success: The test will pass if all layer 3 interfaces have the proper MTU configured.
        * failure: The test will fail if one or many layer 3 interfaces have the wrong MTU configured.
        * skipped: The test will be skipped if the MTU value is not provided.
    """

    name = "VerifyL3MTU"
    description = "Verifies the global layer 3 Maximum Transfer Unit (MTU) for all layer 3 interfaces."
    categories = ["interfaces"]
    commands = [AntaCommand(command="show interfaces")]

    NOT_SUPPORTED_INTERFACES: List[str] = ["Management", "Loopback", "Vxlan", "Tunnel"]

    @AntaTest.anta_test
    def test(self, mtu: int = 1500, ignored_interfaces: Optional[List[str]] = None, specific_mtu: Optional[List[Dict[str, int]]] = None) -> None:
        """
        Verifies the global L3 Maximum Transfer Unit (MTU) for interfaces.

        Test that L3 interfaces are configured with the correct MTU. It supports Ethernet, Port Channel and VLAN interfaces.
        You can define a global MTU to check and also an MTU per interface and also ignored some interfaces.

        Args:
            mtu (int, optional): Default MTU we should have configured on all non-excluded interfaces. Defaults to 1500.
            ignored_interfaces (List[str]): A list of L3 interfaces to ignore. It will replace the built-in exclusion.
            specific_mtu (Optional[List[Dict[str, int]]]): A list of dictionary of L3 interfaces with their specific MTU configured.
        """
        if not mtu:
            self.result.is_skipped(f"{self.__class__.name} did not run because mtu was not supplied")
            return

        if ignored_interfaces is None:
            ignored_interfaces = self.NOT_SUPPORTED_INTERFACES

        # Parameter to save incorrect interface settings
        wrong_l3mtu_intf: List[Dict[str, int]] = []

        command_output = self.instance_commands[0].json_output

        # Set list of interfaces with specific settings
        specific_interfaces: List[str] = []
        if specific_mtu is not None:
            for d in specific_mtu:
                specific_interfaces.extend(d)
        # Set default value if there is no specific settings.
        else:
            specific_mtu = []

        for interface, values in command_output["interfaces"].items():
            if re.findall(r"[a-z]+", interface, re.IGNORECASE)[0] not in ignored_interfaces and values["forwardingModel"] == "routed":
                if interface in specific_interfaces:
                    wrong_l3mtu_intf.extend({interface: values["mtu"]} for custom_data in specific_mtu if values["mtu"] != custom_data[interface])
                # Comparison with generic setting
                elif values["mtu"] != mtu:
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
        * error: The test will give an error if a list of interface(s) is not provided as template_params.

    """

    name = "VerifyIPProxyARP"
    description = "Verifies if Proxy-ARP is enabled for the provided list of interface(s)."
    categories = ["interfaces"]
    template = AntaTemplate(template="show ip interface {intf}")

    @AntaTest.anta_test
    def test(self) -> None:
        """
        Run VerifyIPProxyARP validation.
        """

        disabled_intf = []
        for command in self.instance_commands:
            if command.params and "intf" in command.params:
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

    Default ignored interfaces: ["Management", "Loopback", "Tunnel", "Vxlan"]

    Expected Results:
        * success: The test will pass if all layer 2 interfaces have the proper MTU configured.
        * failure: The test will fail if one or many layer 2 interfaces have the wrong MTU configured.
        * skipped: The test will be skipped if the MTU value is not provided.
    """

    name = "VerifyL2MTU"
    description = "Verifies the global layer 2 Maximum Transfer Unit (MTU) for all layer 2 interfaces."
    categories = ["interfaces"]
    commands = [AntaCommand(command="show interfaces")]

    NOT_SUPPORTED_INTERFACES: List[str] = ["Management", "Loopback", "Tunnel", "Vxlan"]

    @AntaTest.anta_test
    def test(self, mtu: int = 9214, ignored_interfaces: Optional[List[str]] = None, specific_mtu: Optional[List[Dict[str, int]]] = None) -> None:
        """
        Verifies the global L2 Maximum Transfer Unit (MTU) for interfaces.

        Test that L2 interfaces are configured with the correct MTU. It supports Ethernet, Port Channel and VLAN interfaces.
        You can define a global MTU to check and also an MTU per interface and also ignored some interfaces.

        Args:
            mtu (int, optional): Default MTU we should have configured on all non-excluded interfaces. Defaults to 9214.
            ignored_interfaces (List[str]): A list of L2 interfaces to ignore. It will replace the built-in exclusion.
            specific_mtu (Optional[List[Dict[str, int]]]): A list of dictionary of L2 interfaces with their specific MTU configured.
        """
        if not mtu:
            self.result.is_skipped(f"{self.__class__.name} did not run because mtu was not supplied")
            return

        if ignored_interfaces is None:
            ignored_interfaces = self.NOT_SUPPORTED_INTERFACES

        # Parameter to save incorrect interface settings
        wrong_l2mtu_intf: List[Dict[str, int]] = []

        command_output = self.instance_commands[0].json_output

        # Set list of interfaces with specific settings
        specific_interfaces: List[str] = []
        if specific_mtu is not None:
            for d in specific_mtu:
                specific_interfaces.extend(d)
        # Set default value if there is no specific settings.
        else:
            specific_mtu = []

        for interface, values in command_output["interfaces"].items():
            if re.findall(r"[a-z]+", interface, re.IGNORECASE)[0] not in ignored_interfaces and values["forwardingModel"] == "bridged":
                if interface in specific_interfaces:
                    wrong_l2mtu_intf.extend({interface: values["mtu"]} for custom_data in specific_mtu if values["mtu"] != custom_data[interface])
                # Comparison with generic setting
                elif values["mtu"] != mtu:
                    wrong_l2mtu_intf.append({interface: values["mtu"]})

        if wrong_l2mtu_intf:
            self.result.is_failure(f"Some L2 interfaces do not have correct MTU configured:\n{wrong_l2mtu_intf}")
        else:
            self.result.is_success()
