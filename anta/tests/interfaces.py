"""
Test functions related to the device interfaces
"""
import re
from typing import Any, Dict, List, cast

from anta.decorators import skip_on_platforms
from anta.models import AntaTest, AntaTestCommand

# pylint: disable=W0511


class VerifyInterfaceUtilization(AntaTest):
    """
    Verifies interfaces utilization is below 75%.
    """

    name = "verify_interface_utilization"
    description = "Verifies interfaces utilization is below 75%."
    categories = ["interfaces"]
    # TODO - move from text to json if possible
    commands = [AntaTestCommand(command="show interfaces counters rates", ofmt="text")]

    @AntaTest.anta_test
    def test(self) -> None:
        """Run VerifyInterfaceUtilization validation"""
        self.logger.debug(f"self.instance_commands is: {self.instance_commands}")
        command_output = cast(str, self.instance_commands[0].output)
        self.logger.debug(f"dataset is: {command_output}")

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
    Verifies interfaces error counters are equal to zero.
    """

    name = "verify_interface_errors"
    description = "Verifies interfaces error counters are equal to zero."
    categories = ["interfaces"]
    commands = [AntaTestCommand(command="show interfaces counters errors")]

    @AntaTest.anta_test
    def test(self) -> None:
        """Run VerifyInterfaceUtilization validation"""
        self.logger.debug(f"self.instance_commands is: {self.instance_commands}")
        command_output = cast(Dict[str, Dict[str, Any]], self.instance_commands[0].output)
        self.logger.debug(f"dataset is: {command_output}")

        wrong_interfaces: List[Dict[str, Dict[str, int]]] = []
        for interface, outer_v in command_output["interfaceErrorCounters"].items():
            wrong_interfaces.extend({interface: outer_v} for counter, value in outer_v.items() if value > 0)
        if not wrong_interfaces:
            self.result.is_success()
        else:
            self.result.is_failure(f"The following interfaces have non 0 error counter(s): {wrong_interfaces}")


class VerifyInterfaceDiscards(AntaTest):
    """
    Verifies interfaces packet discard counters are equal to zero.
    """

    name = "VerifyInterfaceDiscards"
    description = "Verifies interfaces packet discard counters are equal to zero."
    categories = ["interfaces"]
    commands = [AntaTestCommand(command="show interfaces counters discards")]

    @AntaTest.anta_test
    def test(self) -> None:
        """Run VerifyInterfaceDiscards validation"""

        command_output = cast(Dict[str, Dict[Any, Any]], self.instance_commands[0].output)

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
    commands = [AntaTestCommand(command="show interfaces status")]

    @AntaTest.anta_test
    def test(self) -> None:
        """Run VerifyInterfaceErrDisabled validation"""

        command_output = cast(Dict[str, Dict[Any, Any]], self.instance_commands[0].output)

        errdisabled_interfaces = [interface for interface, value in command_output["interfaceStatuses"].items() if value["linkStatus"] == "errdisabled"]

        if not errdisabled_interfaces:
            self.result.is_failure(f"The following interfaces are in error disabled state: {errdisabled_interfaces}")


class VerifyInterfacesStatus(AntaTest):
    """
    Verifies the number of Ethernet interfaces up/up on the device is higher or equal than a value.
    """

    name = "VerifyInterfacesStatus"
    description = "Verifies the number of Ethernet interfaces up/up on the device is higher or equal than a value."
    categories = ["interfaces"]
    commands = [AntaTestCommand(command="show interfaces description")]

    @AntaTest.anta_test
    def test(self, minimum: int = -1) -> None:  # type: ignore[override]
        """Run VerifyInterfacesStatus validation"""

        if minimum < 0:
            self.result.is_skipped(f"VerifyInterfacesStatus was not run as an invalid minimum value was given {minimum}.")
            return

        command_output = cast(Dict[str, Dict[Any, Any]], self.instance_commands[0].output)

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
    commands = [AntaTestCommand(command="show storm-control")]

    @skip_on_platforms(["cEOSLab", "vEOS-lab"])
    @AntaTest.anta_test
    def test(self) -> None:
        """Run VerifyStormControlDrops validation"""

        command_output = cast(Dict[str, Dict[Any, Any]], self.instance_commands[0].output)

        storm_controlled_interfaces: Dict[str, Dict[str, Any]] = {}
        for interface, interface_dict in command_output["interfaces"].items():
            for traffic_type, traffic_type_dict in interface_dict["trafficTypes"]:
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
    commands = [AntaTestCommand(command="show port-channel")]

    @skip_on_platforms(["cEOSLab", "vEOS-lab"])
    @AntaTest.anta_test
    def test(self) -> None:
        """Run VerifyPortChannels validation"""

        command_output = cast(Dict[str, Dict[Any, Any]], self.instance_commands[0].output)

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
    commands = [AntaTestCommand(command="show lacp counters all-ports")]

    @AntaTest.anta_test
    def test(self) -> None:
        """Run VerifyIllegalLACP validation"""

        command_output = cast(Dict[str, Dict[Any, Any]], self.instance_commands[0].output)

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
    commands = [AntaTestCommand(command="show ip interface brief")]

    @AntaTest.anta_test
    def test(self, number: int = -1) -> None:
        """Run VerifyLoopbackCount validation"""

        if number < 0:
            self.result.is_skipped("VerifyLoopbackCount was not run as no number value was given.")
            return

        command_output = cast(Dict[str, Dict[Any, Any]], self.instance_commands[0].output)

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
    commands = [AntaTestCommand(command="show ip interface brief")]

    @AntaTest.anta_test
    def test(self) -> None:
        """Run VerifySVI validation"""

        command_output = cast(Dict[str, Dict[Any, Any]], self.instance_commands[0].output)

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


class VerifySpanningTreeBlockedPorts(AntaTest):
    """
    Verifies there is no spanning-tree blocked ports.
    """

    name = "VerifySpanningTreeBlockedPorts"
    description = "Verifies there is no spanning-tree blocked ports."
    categories = ["interfaces"]
    commands = [AntaTestCommand(command="show spanning-tree blockedports")]

    @AntaTest.anta_test
    def test(self) -> None:
        """Run VerifySpanningTreeBlockedPorts validation"""

        command_output = cast(Dict[str, Dict[Any, Any]], self.instance_commands[0].output)

        if len(command_output["spanningTreeInstances"]) == 0:
            self.result.is_success()
        else:
            self.result.is_failure()
            # TODO: a bit lazy would need a real output for this
            self.result.messages.append(f"The following ports are spanning-tree blocked {command_output['spanningTreeInstances']}")
