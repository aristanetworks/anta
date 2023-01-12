"""
Test functions related to the device interfaces
"""
import re
from typing import Any, Dict, List, Optional

from anta.decorators import skip_on_platforms
from anta.inventory.models import InventoryDevice
from anta.result_manager.models import TestResult
from anta.tests import anta_test

# pylint: disable=W0511


@anta_test
async def verify_interface_utilization(
    device: InventoryDevice, result: TestResult
) -> TestResult:

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
    # TODO make it JSON - bad news it seems percentages are not in the json payload
    response = await device.session.cli(command="show interfaces counters rates", ofmt="text")

    wrong_interfaces = {}
    for line in response.split("\n")[1:]:
        if len(line) > 0:
            if line.split()[-5] == "-" or line.split()[-2] == "-":
                pass
            elif float(line.split()[-5].replace("%", "")) > 75.0:
                wrong_interfaces[line.split()[0]] = line.split()[-5]
            elif float(line.split()[-2].replace("%", "")) > 75.0:
                wrong_interfaces[line.split()[0]] = line.split()[-2]

    if not wrong_interfaces:
        result.is_success()
    else:
        result.is_failure(
            f"The following interfaces have a usage > 75%: {wrong_interfaces}"
        )

    return result


@anta_test
async def verify_interface_errors(device: InventoryDevice, result: TestResult) -> TestResult:

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
    response = await device.session.cli(command="show interfaces counters errors", ofmt="json")

    wrong_interfaces: List[Dict[str, Dict[str, int]]] = []
    for interface, outer_v in response["interfaceErrorCounters"].items():
        wrong_interfaces.extend(
            {interface: outer_v}
            for counter, value in outer_v.items()
            if value > 0
        )
    if not wrong_interfaces:
        result.is_success()
    else:
        result.is_failure(
            f"The following interfaces have non 0 error counter(s): {wrong_interfaces}"
        )

    return result


@anta_test
async def verify_interface_discards(
    device: InventoryDevice, result: TestResult
) -> TestResult:

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
    response = await device.session.cli(command="show interfaces counters discards", ofmt="json")

    wrong_interfaces: List[Dict[str, Dict[str, int]]] = []
    for interface, outer_v in response["interfaces"].items():
        wrong_interfaces.extend(
            {interface: outer_v}
            for counter, value in outer_v.items()
            if value > 0
        )
    if not wrong_interfaces:
        result.is_success()
    else:
        result.is_failure(
            f"The following interfaces have non 0 discard counter(s): {wrong_interfaces}"
        )

    return result


@anta_test
async def verify_interface_errdisabled(
    device: InventoryDevice, result: TestResult
) -> TestResult:

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
    response = await device.session.cli(command="show interfaces status", ofmt="json")

    errdisabled_interfaces = [
        interface
        for interface, value in response["interfaceStatuses"].items()
        if value["linkStatus"] == "errdisabled"
    ]

    if not errdisabled_interfaces:
        result.is_success()
    else:
        result.is_failure(
            f"The following interfaces are in error disabled state: {errdisabled_interfaces}"
        )

    return result


@anta_test
async def verify_interfaces_status(
    device: InventoryDevice, result: TestResult, minimum: Optional[int] = None
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
    if not minimum:
        result.result = "skipped"
        result.messages.append(
            "verify_interfaces_status was not run as no minimum value was given."
        )
        return result

    response = await device.session.cli(command="show interfaces description", ofmt="json")

    count_up_up = 0
    other_ethernet_interfaces = []

    for interface in response["interfaceDescriptions"]:
        interface_dict = response["interfaceDescriptions"][interface]
        if "Ethernet" in interface:
            if (
                re.match(r"connected|up", interface_dict["lineProtocolStatus"])
                and re.match(r"connected|up", interface_dict["interfaceStatus"])
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

    return result


@skip_on_platforms(["cEOSLab", "VEOS-LAB"])
@anta_test
async def verify_storm_control_drops(
    device: InventoryDevice, result: TestResult
) -> TestResult:
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
    response = await device.session.cli(command="show storm-control", ofmt="json")

    storm_controlled_interfaces: Dict[str, Dict[str, Any]] = {}
    for interface, interface_dict in response["interfaces"].items():
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

    return result


@anta_test
async def verify_portchannels(device: InventoryDevice, result: TestResult) -> TestResult:

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
    response = await device.session.cli(command="show port-channel", ofmt="json")

    po_with_invactive_ports: List[Dict[str, str]] = []
    for portchannel, portchannel_dict in response["portChannels"].items():
        if len(portchannel_dict["inactivePorts"]) != 0:
            po_with_invactive_ports.extend(
                {portchannel: portchannel_dict["inactivePorts"]}
            )

    if not po_with_invactive_ports:
        result.is_success()
    else:
        result.is_failure(
            f"The following port-channels have inactive port(s): {po_with_invactive_ports}"
        )

    return result


@anta_test
async def verify_illegal_lacp(device: InventoryDevice, result: TestResult) -> TestResult:

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
    response = await device.session.cli(command="show lacp counters all-ports", ofmt="json")

    po_with_illegal_lacp: List[Dict[str, Dict[str, int]]] = []
    for portchannel, portchannel_dict in response["portChannels"].items():
        po_with_illegal_lacp.extend(
            {portchannel: interface}
            for interface, interface_dict in portchannel_dict["interfaces"].items()
            if interface_dict["illegalRxCount"] != 0
        )

    if not po_with_illegal_lacp:
        result.is_success()
    else:
        result.is_failure(
            "The following port-channels have recieved illegal lacp packets on the "
            f"following ports: {po_with_illegal_lacp}"
        )

    return result


@anta_test
async def verify_loopback_count(
    device: InventoryDevice, result: TestResult, number: Optional[int] = None
) -> TestResult:
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
    if not number:
        result.is_skipped(
            "verify_loopback_count was not run as no number value was given."
        )
        return result

    response = await device.session.cli(command="show ip interface brief ", ofmt="json")

    loopback_count = 0
    down_loopback_interfaces = []

    for interface in response["interfaces"]:
        interface_dict = response["interfaces"][interface]
        if "Loopback" in interface:
            loopback_count += 1
            if not (
                interface_dict["lineProtocolStatus"] == "up"
                and interface_dict["interfaceStatus"] == "connected"
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

    return result


@anta_test
async def verify_svi(device: InventoryDevice, result: TestResult) -> TestResult:
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
    response = await device.session.cli(command="show ip interface brief", ofmt="json")

    down_svis = []

    for interface in response["interfaces"]:
        interface_dict = response["interfaces"][interface]
        if "Vlan" in interface:
            if not (
                interface_dict["lineProtocolStatus"] == "up"
                and interface_dict["interfaceStatus"] == "connected"
            ):
                down_svis.append(interface)

    if len(down_svis) == 0:
        result.is_success()
    else:
        result.is_failure(f"The following SVIs are not up: {down_svis}")

    return result


@anta_test
async def verify_spanning_tree_blocked_ports(
    device: InventoryDevice, result: TestResult
) -> TestResult:

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
    response = await device.session.cli(command="show spanning-tree blockedports", ofmt="json")

    if len(response["spanningTreeInstances"]) == 0:
        result.is_success()
    else:
        result.is_failure()
        # TODO: a bit lazy would need a real output for this
        result.messages.append(
            f"The following ports are spanning-tree blocked {response['spanningTreeInstances']}"
        )

    return result
