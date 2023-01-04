"""
BGP test functions
"""
import logging
from typing import Any, Dict

from anta.decorators import check_bgp_family_enable
from anta.inventory.models import InventoryDevice
from anta.result_manager.models import TestResult
from anta.tests import anta_test

logger = logging.getLogger(__name__)


@anta_test
@check_bgp_family_enable("ipv4")
async def verify_bgp_ipv4_unicast_state(
    device: InventoryDevice, result: TestResult
) -> TestResult:
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
    response = await device.session.cli(
        command="show bgp ipv4 unicast summary vrf all", ofmt="json"
    )
    logger.debug(f"query result is: {response}")

    bgp_vrfs = response["vrfs"]

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
                            "inMsgQueue": bgp_vrfs[vrf]["peers"][peer]["inMsgQueue"],
                            "outMsgQueue": bgp_vrfs[vrf]["peers"][peer]["outMsgQueue"],
                        }
                    }
                )

    if not state_issue:
        result.is_success()
    else:
        result.is_failure(f"Some IPv4 Unicast BGP Peer are not up: {state_issue}")

    return result


@anta_test
@check_bgp_family_enable("ipv4")
async def verify_bgp_ipv4_unicast_count(
    device: InventoryDevice, result: TestResult, number: int, vrf: str = "default"
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
    if not number or not vrf:
        result.is_skipped(
            "verify_bgp_ipv4_unicast_count could not run because number of vrf was not supplied"
        )
        return result

    response = await device.session.cli(
        command=f"show bgp ipv4 unicast summary vrf {vrf}", ofmt="json"
    )
    logger.debug(f"query result is: {response}")

    bgp_vrfs = response["vrfs"]

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

    if peer_number == number:
        result.is_success()
    else:
        result.is_failure()
        if peer_number != number:
            result.is_failure(
                f"Expecting {number} BGP peer in vrf {vrf} and got {peer_number}"
            )

    return result


@anta_test
@check_bgp_family_enable("ipv6")
async def verify_bgp_ipv6_unicast_state(
    device: InventoryDevice, result: TestResult
) -> TestResult:
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
    response = await device.session.cli(
        command="show bgp ipv6 unicast summary vrf all", ofmt="json"
    )

    logger.debug(f"query result is: {response}")
    bgp_vrfs = response["vrfs"]

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
                            "inMsgQueue": bgp_vrfs[vrf]["peers"][peer]["inMsgQueue"],
                            "outMsgQueue": bgp_vrfs[vrf]["peers"][peer]["outMsgQueue"],
                        }
                    }
                )

    if not state_issue:
        result.is_success()
    else:
        result.is_failure(f"Some IPv6 Unicast BGP Peer are not up: {state_issue}")

    return result


@anta_test
@check_bgp_family_enable("evpn")
async def verify_bgp_evpn_state(device: InventoryDevice, result: TestResult) -> TestResult:

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
    response = await device.session.cli(command="show bgp evpn summary", ofmt="json")
    logger.debug(f"query result is: {response}")

    bgp_vrfs = response["vrfs"]

    peers = bgp_vrfs["default"]["peers"]
    non_established_peers = [
        peer
        for peer, peer_dict in peers.items()
        if peer_dict["peerState"] != "Established"
    ]

    if not non_established_peers:
        result.is_success()
    else:
        result.is_failure(
            f"The following EVPN peers are not established: {non_established_peers}"
        )

    return result


@anta_test
@check_bgp_family_enable("evpn")
async def verify_bgp_evpn_count(
    device: InventoryDevice, result: TestResult, number: int
) -> TestResult:
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
    if not number:
        result.is_skipped(
            "verify_bgp_evpn_count could not run because number was not supplied."
        )
        return result

    response = await device.session.cli(command="show bgp evpn summary", ofmt="json")
    logger.debug(f"query result is: {response}")

    peers = response["vrfs"]["default"]["peers"]

    if len(peers) == number:
        result.is_success()
    else:
        result.is_failure()
        if len(peers) != number:
            result.messages.append(
                f"Expecting {number} BGP EVPN peers and got {len(peers)}"
            )

    return result


@anta_test
@check_bgp_family_enable("rtc")
async def verify_bgp_rtc_state(device: InventoryDevice, result: TestResult) -> TestResult:
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
    response = await device.session.cli(command="show bgp rt-membership summary", ofmt="json")
    logger.debug(f"query result is: {response}")

    peers = response["vrfs"]["default"]["peers"]
    non_established_peers = [
        peer
        for peer, peer_dict in peers.items()
        if peer_dict["peerState"] != "Established"
    ]

    if not non_established_peers:
        result.is_success()
    else:
        result.is_failure(
            f"The following RTC peers are not established: {non_established_peers}"
        )

    return result


@anta_test
@check_bgp_family_enable("rtc")
async def verify_bgp_rtc_count(
    device: InventoryDevice, result: TestResult, number: int
) -> TestResult:
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
    if not number:
        result.is_skipped(
            "verify_bgp_rtc_count could not run because number was not supplied"
        )
        return result

    response = await device.session.cli(command="show bgp rt-membership summary", ofmt="json")
    logger.debug(f"query result is: {response}")

    peers = response["vrfs"]["default"]["peers"]
    non_established_peers = [
        peer
        for peer, peer_dict in peers.items()
        if peer_dict["peerState"] != "Established"
    ]

    if not non_established_peers and len(peers) == number:
        result.is_success()
    else:
        result.is_failure()
        if len(peers) != number:
            result.is_failure(f"Expecting {number} BGP RTC peers and got {len(peers)}")

    return result
