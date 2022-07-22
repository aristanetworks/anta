"""
BGP test functions
"""
from jsonrpclib import jsonrpc
from anta.inventory.models import InventoryDevice
from anta.result_manager.models import TestResult


def verify_bgp_ipv4_unicast_state(device: InventoryDevice) -> TestResult:
    """
    Verifies all IPv4 unicast BGP sessions are established (for all VRF)
    and all BGP messages queues for these sessions are empty (for all VRF).

    Args:
        device (InventoryDevice): InventoryDevice instance containing all devices information.

    Returns:
        TestResult instance with
        * result = "unset" if test has not been executed
        * result = "success" if all IPv4 unicast BGP sessions are established (for all VRF)
                             and all BGP messages queues for these sessions are empty (for all VRF).
        * result = "failure" otherwise.
        * result = "error" if any exception is caught
    """
    result = TestResult(host=str(device.host), test="verify_bgp_ipv4_unicast_state")

    try:
        response = device.session.runCmds(
            1, ["show bgp ipv4 unicast summary vrf all"], "json"
        )

        if len(response[0]["vrfs"]) == 0:
            # No VRF
            result.result = "unset"
            result.messages.append("No BGP VRF")

        state_issue = {}
        for vrf in response[0]["vrfs"]:
            for peer in response[0]["vrfs"][vrf]["peers"]:
                if (
                    (
                        response[0]["vrfs"][vrf]["peers"][peer]["peerState"]
                        != "Established"
                    )
                    or (response[0]["vrfs"][vrf]["peers"][peer]["inMsgQueue"] != 0)
                    or (response[0]["vrfs"][vrf]["peers"][peer]["outMsgQueue"] != 0)
                ):
                    vrf_dict = state_issue.setdefault(vrf, {})
                    vrf_dict.update(
                        {
                            peer: {
                                "peerState": response[0]["vrfs"][vrf]["peers"][peer][
                                    "peerState"
                                ],
                                "inMsgQueue": response[0]["vrfs"][vrf]["peers"][peer][
                                    "inMsgQueue"
                                ],
                                "outMsgQueue": response[0]["vrfs"][vrf]["peers"][peer][
                                    "outMsgQueue"
                                ],
                            }
                        }
                    )

        if len(state_issue) == 0:
            result.result = "success"
        else:
            result.result = "failure"
            result.messages.append(
                f"Some IPv4 Unicast BGP Peer are not up: {state_issue}"
            )

    except (jsonrpc.AppError, KeyError) as e:
        result.messages.append(str(e))
        result.result = "error"

    return result


def verify_bgp_ipv4_unicast_count(
    device: InventoryDevice, number: int, vrf: str = "default"
) -> TestResult:
    """
    Verifies all IPv4 unicast BGP sessions are established
    and all BGP messages queues for these sessions are empty
    and the actual number of BGP IPv4 unicast neighbors is the one we expect.

    Args:
        device (InventoryDevice): InventoryDevice instance containing all devices information.
        number (int): Expected number of BGP IPv4 unicast neighbors
        vrf(str): VRF to verify. default is "default".

    Returns:
        TestResult instance with
        * result = "unset" if test has not been executed
        * result = "success" if all IPv4 unicast BGP sessions are established
                             and if all BGP messages queues for these sessions are empty
                             and if the actual number of BGP IPv4 unicast neighbors is the one we expect.
        * result = "failure" otherwise.
        * result = "error" if any exception is caught
    """
    result = TestResult(host=str(device.host), test="verify_bgp_ipv4_unicast_count")

    if not number or not vrf:
        result.result = "unset"
        result.messages.append(
            "verify_bgp_ipv4_unicast_count could not run because number of vrf was not supplied"
        )
        return result

    count = 0

    try:
        response = device.session.runCmds(1, [f"show bgp ipv4 unicast summary vrf {vrf}"], "json")

        for peer in response[0]["vrfs"][vrf]["peers"]:
            if (
                (response[0]["vrfs"][vrf]["peers"][peer]["peerState"] != "Established")
                or (response[0]["vrfs"][vrf]["peers"][peer]["inMsgQueue"] != 0)
                or (response[0]["vrfs"][vrf]["peers"][peer]["outMsgQueue"] != 0)
            ):
                return False
            count = count + 1
        if count == number:
            return True
        return False
    except (jsonrpc.AppError, KeyError) as e:
        result.messages.append(str(e))
        result.result = "error"

    return result


def verify_bgp_ipv6_unicast_state(device: InventoryDevice) -> TestResult:
    """
    Verifies all IPv6 unicast BGP sessions are established (for all VRF)
    and all BGP messages queues for these sessions are empty (for all VRF).

    Args:
        device (jsonrpclib.jsonrpc.ServerProxy): Instance of the class jsonrpclib.jsonrpc.ServerProxy with the uri f'https://{username}:{password}@{ip}/command-api'.
        enable_password (str): Enable password.

    Returns:
        bool: `True` if all IPv6 unicast BGP sessions are established (for all VRF)
        and all BGP messages queues for these sessions are empty (for all VRF).
        `False` otherwise.

    """
    try:
        response = device.session.runCmds(
            1, ["show bgp ipv6 unicast summary vrf all"], "json"
        )
    except jsonrpc.AppError:
        return None
    try:
        if len(response[0]["vrfs"]) == 0:
            return None
        for vrf in response[0]["vrfs"]:
            for peer in response[0]["vrfs"][vrf]["peers"]:
                if (
                    (
                        response[0]["vrfs"][vrf]["peers"][peer]["peerState"]
                        != "Established"
                    )
                    or (response[0]["vrfs"][vrf]["peers"][peer]["inMsgQueue"] != 0)
                    or (response[0]["vrfs"][vrf]["peers"][peer]["outMsgQueue"] != 0)
                ):
                    return False
        return True
    except KeyError:
        return None


def verify_bgp_evpn_state(device: InventoryDevice) -> TestResult:

    """
    Verifies all EVPN BGP sessions are established (default VRF).

    Args:
        device (jsonrpclib.jsonrpc.ServerProxy): Instance of the class jsonrpclib.jsonrpc.ServerProxy with the uri f'https://{username}:{password}@{ip}/command-api'.
        enable_password (str): Enable password.

    Returns:
        bool: `True` if all EVPN BGP sessions are established.
        `False` otherwise.

    """
    try:
        response = device.session.runCmds(1, ["show bgp evpn summary"], "json")
    except jsonrpc.AppError:
        return None
    try:
        if len(response[0]["vrfs"]["default"]["peers"]) == 0:
            return None
        for peer in response[0]["vrfs"]["default"]["peers"]:
            if (
                response[0]["vrfs"]["default"]["peers"][peer]["peerState"]
                != "Established"
            ):
                return False
        return True
    except KeyError:
        return None


def verify_bgp_evpn_count(
    device: InventoryDevice, enable_password, number
) -> TestResult:
    """
    Verifies all EVPN BGP sessions are established (default VRF)
    and the actual number of BGP EVPN neighbors is the one we expect (default VRF).

    Args:
        device (jsonrpclib.jsonrpc.ServerProxy): Instance of the class jsonrpclib.jsonrpc.ServerProxy with the uri f'https://{username}:{password}@{ip}/command-api'.
        enable_password (str): Enable password.
        number (int): The expected number of BGP EVPN neighbors in the default VRF.

    Returns:
        bool: `True` if all EVPN BGP sessions are established
        and if the actual number of BGP EVPN neighbors is the one we expect.
        `False` otherwise.

    """
    if not number:
        return None
    try:
        response = device.session.runCmds(1, ["show bgp evpn summary"], "json")
    except jsonrpc.AppError:
        return None
    count = 0
    try:
        for peer in response[0]["vrfs"]["default"]["peers"]:
            if (
                response[0]["vrfs"]["default"]["peers"][peer]["peerState"]
                != "Established"
            ):
                return False
            count = count + 1
        if count == number:
            return True
        return False
    except KeyError:
        return None


def verify_bgp_rtc_state(device: InventoryDevice) -> TestResult:

    """
    Verifies all RTC BGP sessions are established (default VRF).

    Args:
        device (jsonrpclib.jsonrpc.ServerProxy): Instance of the class jsonrpclib.jsonrpc.ServerProxy with the uri f'https://{username}:{password}@{ip}/command-api'.
        enable_password (str): Enable password.

    Returns:
        bool: `True` if all RTC BGP sessions are established.
        `False` otherwise.

    """
    try:
        response = device.session.runCmds(1, ["show bgp rt-membership summary"], "json")
    except jsonrpc.AppError:
        return None
    try:
        if len(response[0]["vrfs"]["default"]["peers"]) == 0:
            return None
        for peer in response[0]["vrfs"]["default"]["peers"]:
            if (
                response[0]["vrfs"]["default"]["peers"][peer]["peerState"]
                != "Established"
            ):
                return False
        return True
    except KeyError:
        return None


def verify_bgp_rtc_count(
    device: InventoryDevice, enable_password, number
) -> TestResult:
    """
    Verifies all RTC BGP sessions are established (default VRF)
    and the actual number of BGP RTC neighbors is the one we expect (default VRF).

    Args:
        device (jsonrpclib.jsonrpc.ServerProxy): Instance of the class jsonrpclib.jsonrpc.ServerProxy with the uri f'https://{username}:{password}@{ip}/command-api'.
        enable_password (str): Enable password.
        number (int): The expected number of BGP RTC neighbors (default VRF).

    Returns:
        bool: `True` if all RTC BGP sessions are established
        and if the actual number of BGP RTC neighbors is the one we expect.
        `False` otherwise.

    """
    if not number:
        return None
    try:
        response = device.session.runCmds(1, ["show bgp rt-membership summary"], "json")
    except jsonrpc.AppError:
        return None
    count = 0
    try:
        for peer in response[0]["vrfs"]["default"]["peers"]:
            if (
                response[0]["vrfs"]["default"]["peers"][peer]["peerState"]
                != "Established"
            ):
                return False
            count = count + 1
        if count == number:
            return True
        return False
    except KeyError:
        return None
