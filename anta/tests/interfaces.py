"""
Test functions related to the device interfaces
"""
from typing import Dict, Any
from jsonrpclib import jsonrpc
from anta.inventory.models import InventoryDevice
from anta.result_manager.models import TestResult

# pylint: disable=W0511


def verify_interface_utilization(device: InventoryDevice) -> TestResult:

    """
    Verifies interfaces utilization is below 75%.

    Args:
        device (InventoryDevice): InventoryDevice instance containing all devices information.

    Returns:
        TestResult instance with
        * result = "unset" if the test has not been executed
        * result = "success" if interfaces utilization is below 75%
        * result = "failure" otherwise.
        * result = "error" if any exception is caught

    """
    result = TestResult(host=str(device.host), test="verify_interface_utilization")
    try:
        # TODO make it JSON - bad news it seems percentages are not in the json payload
        response = device.session.runCmds(1, ["show interfaces counters rates"], "text")

        wrong_interfaces = {}
        for line in response[0]["output"].split("\n")[1:]:
            if len(line) > 0:
                if line.split()[-5] == "-" or line.split()[-2] == "-":
                    pass
                elif float(line.split()[-5].replace("%", "")) > 75.0:
                    wrong_interfaces[line.split()[0]] = line.split()[-5]
                elif float(line.split()[-2].replace("%", "")) > 75.0:
                    wrong_interfaces[line.split()[0]] = line.split()[-2]

        if len(wrong_interfaces) == 0:
            result.is_success()
        else:
            result.is_failure(
                f"The following interfaces have a usage > 75%: {wrong_interfaces}"
            )

    except (jsonrpc.AppError, KeyError) as e:
        result.is_error(str(e))

    return result


def verify_interface_errors(device: InventoryDevice) -> TestResult:

    """
    Verifies interfaces error counters are equal to zero.

    Args:
        device (InventoryDevice): InventoryDevice instance containing all devices information.

    Returns:
        TestResult instance with
        * result = "unset" if the test has not been executed
        * result = "success" if interfaces error counters are equal to zero.
        * result = "failure" otherwise.
        * result = "error" if any exception is caught

    """
    result = TestResult(host=str(device.host), test="verify_interface_errors")

    try:
        response = device.session.runCmds(
            1, ["show interfaces counters errors"], "json"
        )

        wrong_interfaces = {
            interface: {counter: value for counter, value in outer_v.items if value > 0}
            for interface, outer_v in response[0]["interfaceErrorCounters"]
        }
        if len(wrong_interfaces) == 0:
            result.is_success()
        else:
            result.is_failure(
                f"The following interfaces have non 0 error counter(s): {wrong_interfaces}"
            )

    except (jsonrpc.AppError, KeyError) as e:
        result.is_error(str(e))

    return result


def verify_interface_discards(device: InventoryDevice) -> TestResult:

    """
    Verifies interfaces packet discard counters are equal to zero.

    Args:
        device (InventoryDevice): InventoryDevice instance containing all devices information.

    Returns:
        TestResult instance with
        * result = "unset" if the test has not been executed
        * result = "success" if interfaces discard counters are equal to zero.
        * result = "failure" otherwise.
        * result = "error" if any exception is caught

    """
    result = TestResult(host=str(device.host), test="verify_interface_discards")

    try:
        response = device.session.runCmds(
            1, ["show interfaces counters discards"], "json"
        )

        wrong_interfaces = {
            interface: {counter: value for counter, value in outer_v.items if value > 0}
            for interface, outer_v in response[0]["interfaces"]
        }
        if len(wrong_interfaces) == 0:
            result.is_success()
        else:
            result.is_failure(
                f"The following interfaces have non 0 discard counter(s): {wrong_interfaces}"
            )

    except (jsonrpc.AppError, KeyError) as e:
        result.is_error(str(e))

    return result


def verify_interface_errdisabled(device: InventoryDevice) -> TestResult:

    """
    Verifies there is no interface in error disable state.

    Args:
        device (InventoryDevice): InventoryDevice instance containing all devices information.

    Returns:
        TestResult instance with
        * result = "unset" if the test has not been executed
        * result = "success" if no interface is in error disable state.
        * result = "failure" otherwise.
        * result = "error" if any exception is caught

    """
    result = TestResult(host=str(device.host), test="verify_interface_errdisabled")

    try:
        response = device.session.runCmds(1, ["show interfaces status"], "json")

        errdisabled_interfaces = [
            interface
            for interface, value in response[0]["interfaceStatuses"].items()
            if value["linkStatus"] == "errdisabled"
        ]

        if len(errdisabled_interfaces) == 0:
            result.is_success()
        else:
            result.is_failure(
                f"The following interfaces are in error disabled state: {errdisabled_interfaces}"
            )

    except (jsonrpc.AppError, KeyError) as e:
        result.is_error(str(e))

    return result


def verify_interfaces_status(
    device: InventoryDevice, minimum: int = None
) -> TestResult:
    """
    Verifies the number of Ethernet interfaces up/up on the device is higher or equal than a value.

    Args:
        device (InventoryDevice): InventoryDevice instance containing all devices information.
        minimum (int): Expected minimum number of Ethernet interfaces up/up

    Returns:
        TestResult instance with
        * result = "unset" if the test has not been executed
        * result = "skipped" if the `minimum` parameter is missing
        * result = "success" if the number of Ethernet interface up/up is >= minimum
        * result = "failure" otherwise.
        * result = "error" if any exception is caught

    """
    result = TestResult(host=str(device.host), test="verify_interfaces_status")
    if not minimum:
        result.result = "skipped"
        result.messages.append(
            "verify_interfaces_status was not run as no minimum value was given."
        )
        return result
    try:
        response = device.session.runCmds(1, ["show interfaces description"], "json")

        count_up_up = 0
        other_ethernet_interfaces = []

        for interface in response[0]["interfaceDescriptions"]:
            interface_dict = response[0]["interfaceDescriptions"][interface]
            if "Ethernet" in interface:
                if (
                    interface_dict["lineProtocolStatus"] == "up"
                    and interface_dict["interfaceStatus"] == "up"
                ):
                    count_up_up += 1
                else:
                    other_ethernet_interfaces.append(interface)

        if count_up_up >= minimum:
            result.is_success()
        else:
            result.is_failure(
                f"Only {count_up_up}, less than {minimum} Ethernet interfaces are UP/UP"
            )
            result.messages.append(
                f"The following Ethernet interfaces are not UP/UP: {other_ethernet_interfaces}"
            )

    except (jsonrpc.AppError, KeyError) as e:
        result.is_error(str(e))

    return result


def verify_storm_control_drops(device: InventoryDevice) -> TestResult:
    """
    Verifies the device did not drop packets due its to storm-control configuration.

    Args:
        device (InventoryDevice): InventoryDevice instance containing all devices information.

    Returns:
        TestResult instance with
        * result = "unset" if the test has not been executed
        * result = "success" if the device did not drop packet due to its storm-control configuration.
        * result = "failure" otherwise.
        * result = "error" if any exception is caught

    """
    result = TestResult(host=str(device.host), test="verify_storm_control_drops")

    try:
        response = device.session.runCmds(1, ["show storm-control"], "json")

        storm_controlled_interfaces: Dict[str, Dict[str, Any]] = {}
        for interface, interface_dict in response[0]["interfaces"].items():
            for traffic_type, traffic_type_dict in interface_dict["trafficTypes"]:
                if "drop" in traffic_type_dict and traffic_type_dict["drop"] != 0:
                    storm_controlled_interface_dict = (
                        storm_controlled_interfaces.setdefault(interface, {})
                    )
                    storm_controlled_interface_dict.update(
                        {traffic_type: traffic_type_dict["drop"]}
                    )

        if len(storm_controlled_interfaces) == 0:
            result.is_success()
        else:
            result.is_failure(
                f"The following interfaces have none 0 storm-control drop counters {storm_controlled_interfaces}"
            )

    except (jsonrpc.AppError, KeyError) as e:
        result.is_error(str(e))

    return result


def verify_portchannels(device: InventoryDevice) -> TestResult:

    """
    Verifies there is no inactive port in port channels.

    Args:
        device (InventoryDevice): InventoryDevice instance containing all devices information.

    Returns:
        TestResult instance with
        * result = "unset" if the test has not been executed
        * result = "success" if there is no inactive ports in port-channels
                             in particular "success" if there is no port-channel
        * result = "failure" otherwise.
        * result = "error" if any exception is caught

    """
    result = TestResult(host=str(device.host), test="verify_portchannels")

    try:
        response = device.session.runCmds(1, ["show port-channel"], "json")

        po_with_invactive_ports = {
            portchannel: {"inactivePorts": portchannel_dict["inactivePorts"]}
            for portchannel, portchannel_dict in response[0]["portChannels"].items()
            if len(portchannel_dict["inactivePorts"]) != 0
        }

        if len(po_with_invactive_ports) == 0:
            result.is_success()
        else:
            result.is_failure(
                f"The following port-channels have inactive port(s): {po_with_invactive_ports}"
            )

    except (jsonrpc.AppError, KeyError) as e:
        result.is_error(str(e))

    return result


def verify_illegal_lacp(device: InventoryDevice) -> TestResult:

    """
    Verifies there is no illegal LACP packets received.

    Args:
        device (InventoryDevice): InventoryDevice instance containing all devices information.

    Returns:
        TestResult instance with
        * result = "unset" if the test has not been executed
        * result = "success" if there is no illegal LACP packets received.
                             in particular "success" if there is no port-channel
        * result = "failure" otherwise.
        * result = "error" if any exception is caught

    """
    result = TestResult(host=str(device.host), test="verify_illegal_lacp")

    try:
        response = device.session.runCmds(1, ["show lacp counters all-ports"], "json")

        po_with_illegal_lacp = {
            portchannel: [
                interface
                for interface, interface_dict in portchannel_dict["interfaces"].items()
                if interface_dict["illegalRxCount"] != 0
            ]
            for portchannel, portchannel_dict in response[0]["portChannels"].items()
        }

        if len(po_with_illegal_lacp) == 0:
            result.is_success()
        else:
            result.is_failure(
                "The following port-channels have recieved illegal lacp packets on the "
                f"following ports: {po_with_illegal_lacp}"
            )

    except (jsonrpc.AppError, KeyError) as e:
        result.is_error(str(e))

    return result


def verify_loopback_count(device: InventoryDevice, number: int = None) -> TestResult:
    """
    Verifies the number of loopback interfaces on the device is the one we expect.
    And if none of the loopback is down.

    Args:
        device (InventoryDevice): InventoryDevice instance containing all devices information.
        number (int): Expected number of loopback interfaces.

    Returns:
        TestResult instance with
        * result = "unset" if the test has not been executed
        * result = "success" if the number of loopback is equal to `number` and if
                             none of the loopback is down
        * result = "failure" otherwise.
        * result = "error" if any exception is caught

    """
    result = TestResult(host=str(device.host), test="verify_loopback_count")

    if not number:
        result.is_skipped(
            "verify_loopback_count was not run as no number value was given."
        )
        return result

    try:
        response = device.session.runCmds(1, ["show ip interface brief "], "json")

        loopback_count = 0
        down_loopback_interfaces = []

        for interface in response[0]["interfaceDescriptions"]:
            interface_dict = response[0]["interfaceDescriptions"][interface]
            if "Loopback" in interface:
                loopback_count += 1
                if not (
                    interface_dict["lineProtocolStatus"] == "up"
                    and interface_dict["interfaceStatus"] == "up"
                ):
                    down_loopback_interfaces.append(interface)

        if loopback_count == number and len(down_loopback_interfaces) == 0:
            result.is_success()
        else:
            result.is_failure()
            if loopback_count != number:
                result.is_failure(
                    f"Found {loopback_count} Loopbacks when expecting {number}"
                )
            elif len(down_loopback_interfaces) != 0:
                result.is_failure(
                    f"The following Loopbacks are not up: {down_loopback_interfaces}"
                )

    except (jsonrpc.AppError, KeyError) as e:
        result.is_error(str(e))

    return result


def verify_svi(device: InventoryDevice) -> TestResult:
    """
    Verifies there is no interface vlan down.

    Args:
        device (InventoryDevice): InventoryDevice instance containing all devices information.

    Returns:
        TestResult instance with
        * result = "unset" if the test has not been executed
        * result = "success" if no SVI is down
        * result = "failure" otherwise.
        * result = "error" if any exception is caught

    """
    result = TestResult(host=str(device.host), test="verify_svi")

    try:
        response = device.session.runCmds(1, ["show ip interface brief"], "json")

        down_svis = []

        for interface in response[0]["interfaceDescriptions"]:
            interface_dict = response[0]["interfaceDescriptions"][interface]
            if "Vlan" in interface:
                if not (
                    interface_dict["lineProtocolStatus"] == "up"
                    and interface_dict["interfaceStatus"] == "up"
                ):
                    down_svis.append(interface)

        if len(down_svis) == 0:
            result.is_success()
        else:
            result.is_failure(f"The following SVIs are not up: {down_svis}")

    except (jsonrpc.AppError, KeyError) as e:
        result.is_error(str(e))

    return result


def verify_spanning_tree_blocked_ports(device: InventoryDevice) -> TestResult:

    """
    Verifies there is no spanning-tree blocked ports.

    Args:
        device (InventoryDevice): InventoryDevice instance containing all devices information.

    Returns:
        TestResult instance with
        * result = "unset" if the test has not been executed
        * result = "success" if there is no spanning-tree blocked ports
        * result = "failure" otherwise.
        * result = "error" if any exception is caught

    """
    result = TestResult(
        host=str(device.host), test="verify_spanning_tree_blocked_ports"
    )

    try:
        response = device.session.runCmds(
            1, ["show spanning-tree blockedports"], "json"
        )

        if len(response[0]["spanningTreeInstances"]) == 0:
            result.is_success()
        else:
            result.is_failure()
            # TODO: a bit lazy would need a real output for this
            result.messages.append(
                f"The following ports are spanning-tree blocked {response[0]['spanningTreeInstances']}"
            )

    except (jsonrpc.AppError, KeyError) as e:
        result.is_error(str(e))

    return result
