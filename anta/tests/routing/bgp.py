"""
BGP test functions
"""
from typing import Dict, Any
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
        * result = "unset" if the test has not been executed
        * result = "skipped" if no BGP vrf are returned by the device
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

        bgp_vrfs = response[0]["vrfs"]

        if len(bgp_vrfs) == 0:
            # No VRF
            result.is_skipped("No BGP VRF")

        state_issue: Dict[str, Any] = {}
        for vrf in bgp_vrfs:
            for peer in bgp_vrfs[vrf]["peers"]:
                if (
                    (bgp_vrfs[vrf]["peers"][peer]["peerState"] != "Established")
                    or (bgp_vrfs[vrf]["peers"][peer]["inMsgQueue"] != 0)
                    or (bgp_vrfs[vrf]["peers"][peer]["outMsgQueue"] != 0)
                ):
                    vrf_dict = state_issue.setdefault(vrf, {})
                    vrf_dict.update(
                        {
                            peer: {
                                "peerState": bgp_vrfs[vrf]["peers"][peer]["peerState"],
                                "inMsgQueue": bgp_vrfs[vrf]["peers"][peer][
                                    "inMsgQueue"
                                ],
                                "outMsgQueue": bgp_vrfs[vrf]["peers"][peer][
                                    "outMsgQueue"
                                ],
                            }
                        }
                    )

        if len(state_issue) == 0:
            result.is_success()
        else:
            result.is_failure(f"Some IPv4 Unicast BGP Peer are not up: {state_issue}")

    except (jsonrpc.AppError, KeyError) as e:
        result.is_error(str(e))

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
        * result = "unset" if the test has not been executed
        * result = "skipped" if the `number` or `vrf` parameter is missing
        * result = "success" if all IPv4 unicast BGP sessions are established
                             and if all BGP messages queues for these sessions are empty
                             and if the actual number of BGP IPv4 unicast neighbors is equal to `number.
        * result = "failure" otherwise.
        * result = "error" if any exception is caught
    """
    result = TestResult(host=str(device.host), test="verify_bgp_ipv4_unicast_count")

    if not number or not vrf:
        result.is_skipped(
            "verify_bgp_ipv4_unicast_count could not run because number of vrf was not supplied"
        )
        return result

    try:
        response = device.session.runCmds(
            1, [f"show bgp ipv4 unicast summary vrf {vrf}"], "json"
        )

        bgp_vrfs = response[0]["vrfs"]
        peer_state_issue = {}
        peer_number = len(bgp_vrfs[vrf]["peers"])

        for peer in bgp_vrfs[vrf]["peers"]:
            if (
                (bgp_vrfs[vrf]["peers"][peer]["peerState"] != "Established")
                or (bgp_vrfs[vrf]["peers"][peer]["inMsgQueue"] != 0)
                or (bgp_vrfs[vrf]["peers"][peer]["outMsgQueue"] != 0)
            ):
                peer_state_issue[peer] = {
                    "peerState": bgp_vrfs[vrf]["peers"][peer]["peerState"],
                    "inMsgQueue": bgp_vrfs[vrf]["peers"][peer]["inMsgQueue"],
                    "outMsgQueue": bgp_vrfs[vrf]["peers"][peer]["outMsgQueue"],
                }

        if len(peer_state_issue) == 0 and peer_number == number:
            result.is_success()
        else:
            result.is_failure()
            if len(peer_state_issue) > 0:
                result.is_failure(
                    f"Some IPv4 Unicast BGP Peer in VRF {vrf} are not up: {peer_state_issue}"
                )
            if peer_number != number:
                result.is_failure(
                    f"Expecting {number} BGP peer in vrf {vrf} and got {peer_number}"
                )

    except (jsonrpc.AppError, KeyError) as e:
        result.is_error(str(e))

    return result


def verify_bgp_ipv6_unicast_state(device: InventoryDevice) -> TestResult:
    """
    Verifies all IPv6 unicast BGP sessions are established (for all VRF)
    and all BGP messages queues for these sessions are empty (for all VRF).

    Args:
        device (InventoryDevice): InventoryDevice instance containing all devices information.

    Returns:
        TestResult instance with
        * result = "unset" if the test has not been executed
        * result = "skipped" if no BGP vrf are returned by the device
        * result = "success" if all IPv6 unicast BGP sessions are established (for all VRF)
                             and all BGP messages queues for these sessions are empty (for all VRF).
        * result = "failure" otherwise.
        * result = "error" if any exception is caught
    """
    result = TestResult(host=str(device.host), test="verify_bgp_ipv6_unicast_count")

    try:
        response = device.session.runCmds(
            1, ["show bgp ipv6 unicast summary vrf all"], "json"
        )

        bgp_vrfs = response[0]["vrfs"]

        if len(bgp_vrfs) == 0:
            # No VRF
            result.is_skipped("No IPv6 BGP VRF")
            return result

        state_issue: Dict[str, Any] = {}
        for vrf in bgp_vrfs:
            for peer in bgp_vrfs[vrf]["peers"]:
                if (
                    (bgp_vrfs[vrf]["peers"][peer]["peerState"] != "Established")
                    or (bgp_vrfs[vrf]["peers"][peer]["inMsgQueue"] != 0)
                    or (bgp_vrfs[vrf]["peers"][peer]["outMsgQueue"] != 0)
                ):
                    vrf_dict = state_issue.setdefault(vrf, {})
                    vrf_dict.update(
                        {
                            peer: {
                                "peerState": bgp_vrfs[vrf]["peers"][peer]["peerState"],
                                "inMsgQueue": bgp_vrfs[vrf]["peers"][peer][
                                    "inMsgQueue"
                                ],
                                "outMsgQueue": bgp_vrfs[vrf]["peers"][peer][
                                    "outMsgQueue"
                                ],
                            }
                        }
                    )

        if len(state_issue) == 0:
            result.is_success()
        else:
            result.is_failure(f"Some IPv6 Unicast BGP Peer are not up: {state_issue}")

    except (jsonrpc.AppError, KeyError) as e:
        result.is_error(str(e))

    return result


def verify_bgp_evpn_state(device: InventoryDevice) -> TestResult:

    """
    Verifies all EVPN BGP sessions are established (default VRF).

    Args:
        device (InventoryDevice): InventoryDevice instance containing all devices information.

    Returns:
        TestResult instance with
        * result = "unset" if the test has not been executed
        * result = "skipped" if no BGP EVPN peers are returned by the device
        * result = "success" if all EVPN BGP sessions are established.
        * result = "failure" otherwise.
        * result = "error" if any exception is caught

    """
    result = TestResult(host=str(device.host), test="verify_bgp_evpn_state")

    try:
        response = device.session.runCmds(1, ["show bgp evpn summary"], "json")

        bgp_vrfs = response[0]["vrfs"]

        if len(bgp_vrfs["default"]["peers"]) == 0:
            # No peers
            result.is_skipped("No EVPN peer")
            return result

        peers = bgp_vrfs["default"]["peers"]
        non_established_peers = [
            peer for peer, peer_dict in peers if peer_dict["peerState"] != "Established"
        ]

        if len(non_established_peers) == 0:
            result.is_success()
        else:
            result.is_failure(
                f"The following EVPN peers are not established: {non_established_peers}"
            )

    except (jsonrpc.AppError, KeyError) as e:
        result.is_error(str(e))

    return result


def verify_bgp_evpn_count(device: InventoryDevice, number: int) -> TestResult:
    """
    Verifies all EVPN BGP sessions are established (default VRF)
    and the actual number of BGP EVPN neighbors is the one we expect (default VRF).

    Args:
        device (InventoryDevice): InventoryDevice instance containing all devices information.
        number (int): The expected number of BGP EVPN neighbors in the default VRF.

    Returns:
        TestResult instance with
        * result = "unset" if the test has not been executed
        * result = "skipped" if the `number` parameter is missing
        * result = "success" if all EVPN BGP sessions are Established and if the actual
                             number of BGP EVPN neighbors is the one we expect.
        * result = "failure" otherwise.
        * result = "error" if any exception is caught

    """
    result = TestResult(host=str(device.host), test="verify_bgp_evpn_count")

    if not number:
        result.is_skipped(
            "verify_bgp_evpn_count could not run because number was not supplied."
        )
        return result

    try:
        response = device.session.runCmds(1, ["show bgp evpn summary"], "json")

        peers = response[0]["vrfs"]["default"]["peers"]
        non_established_peers = [
            peer for peer, peer_dict in peers if peer_dict["peerState"] != "Established"
        ]

        if len(non_established_peers) == 0 and len(peers) == number:
            result.is_success()
        else:
            result.is_failure()
            if len(non_established_peers) > 0:
                result.messages.append(
                    f"The following EVPN peers are not established: {non_established_peers}"
                )
            if len(peers) != number:
                result.messages.append(
                    f"Expecting {number} BGP EVPN peers and got {len(peers)}"
                )

    except (jsonrpc.AppError, KeyError) as e:
        result.is_error(str(e))

    return result


def verify_bgp_rtc_state(device: InventoryDevice) -> TestResult:
    """
    Verifies all RTC BGP sessions are established (default VRF).

    Args:
        device (InventoryDevice): InventoryDevice instance containing all devices information.

    Returns:
        TestResult instance with
        * result = "unset" if the test has not been executed
        * result = "skipped" if no BGP RTC peers are returned by the device
        * result = "success" if all RTC BGP sessions are Established.
        * result = "failure" otherwise.
        * result = "error" if any exception is caught

    """
    result = TestResult(host=str(device.host), test="verify_bgp_rtc_state")

    try:
        response = device.session.runCmds(1, ["show bgp rt-membership summary"], "json")

        if len(response[0]["vrfs"]["default"]["peers"]) == 0:
            # No peers
            result.is_skipped("No RTC peer")
            return result

        peers = response[0]["vrfs"]["default"]["peers"]
        non_established_peers = [
            peer for peer, peer_dict in peers if peer_dict["peerState"] != "Established"
        ]

        if len(non_established_peers) == 0:
            result.is_success()
        else:
            result.is_failure(
                f"The following RTC peers are not established: {non_established_peers}"
            )

    except (jsonrpc.AppError, KeyError) as e:
        result.is_error(str(e))

    return result


def verify_bgp_rtc_count(device: InventoryDevice, number: int) -> TestResult:
    """
    Verifies all RTC BGP sessions are established (default VRF)
    and the actual number of BGP RTC neighbors is the one we expect (default VRF).

    Args:
        device (InventoryDevice): InventoryDevice instance containing all devices information.
        number (int): The expected number of BGP RTC neighbors (default VRF).

    Returns:
        TestResult instance with
        * result = "unset" if the test has not been executed
        * result = "skipped" if the `number` parameter is missing
        * result = "success" if all RTC BGP sessions are established
                             and if the actual number of BGP RTC neighbors is the one we expect.
        * result = "failure" otherwise.
        * result = "error" if any exception is caught

    """
    result = TestResult(host=str(device.host), test="verify_bgp_rtc_count")

    if not number:
        result.is_skipped(
            "verify_bgp_rtc_count could not run because number was not supplied"
        )
        return result

    try:
        response = device.session.runCmds(1, ["show bgp rt-membership summary"], "json")

        peers = response[0]["vrfs"]["default"]["peers"]
        non_established_peers = [
            peer for peer, peer_dict in peers if peer_dict["peerState"] != "Established"
        ]

        if len(non_established_peers) == 0 and len(peers) == number:
            result.is_success()
        else:
            result.is_failure()
            if len(non_established_peers) > 0:
                result.is_failure(
                    f"The following RTC peers are not established: {non_established_peers}"
                )
            if len(peers) != number:
                result.is_failure(
                    f"Expecting {number} BGP RTC peers and got {len(peers)}"
                )

    except (jsonrpc.AppError, KeyError) as e:
        result.is_error(str(e))

    return result
