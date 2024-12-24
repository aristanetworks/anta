# Copyright (c) 2023-2024 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Module related to BGP tests."""

# Mypy does not understand AntaTest.Input typing
# mypy: disable-error-code=attr-defined
from __future__ import annotations

from ipaddress import IPv4Address, IPv4Network
from typing import TYPE_CHECKING, Any, ClassVar

from pydantic import BaseModel, Field, field_validator, model_validator
from pydantic.v1.utils import deep_update
from pydantic_extra_types.mac_address import MacAddress

from anta.custom_types import BgpDropStats, BgpUpdateError, MultiProtocolCaps, Vni
from anta.input_models.routing.bgp import BgpAddressFamily, BgpAfi
from anta.models import AntaCommand, AntaTemplate, AntaTest
from anta.tools import format_data, get_item, get_value

if TYPE_CHECKING:
    import sys

    if sys.version_info >= (3, 11):
        from typing import Self
    else:
        from typing_extensions import Self


def _add_bgp_routes_failure(
    bgp_routes: list[str], bgp_output: dict[str, Any], peer: str, vrf: str, route_type: str = "advertised_routes"
) -> dict[str, dict[str, dict[str, dict[str, list[str]]]]]:
    """Identify missing BGP routes and invalid or inactive route entries.

    This function checks the BGP output from the device against the expected routes.

    It identifies any missing routes as well as any routes that are invalid or inactive. The results are returned in a dictionary.

    Parameters
    ----------
    bgp_routes
        The list of expected routes.
    bgp_output
        The BGP output from the device.
    peer
        The IP address of the BGP peer.
    vrf
        The name of the VRF for which the routes need to be verified.
    route_type
        The type of BGP routes. Defaults to 'advertised_routes'.

    Returns
    -------
    dict[str, dict[str, dict[str, dict[str, list[str]]]]]
        A dictionary containing the missing routes and invalid or inactive routes.

    """
    # Prepare the failure routes dictionary
    failure_routes: dict[str, dict[str, Any]] = {}

    # Iterate over the expected BGP routes
    for route in bgp_routes:
        str_route = str(route)
        failure: dict[str, Any] = {"bgp_peers": {peer: {vrf: {route_type: {}}}}}

        # Check if the route is missing in the BGP output
        if str_route not in bgp_output:
            # If missing, add it to the failure routes dictionary
            failure["bgp_peers"][peer][vrf][route_type][str_route] = "Not found"
            failure_routes = deep_update(failure_routes, failure)
            continue

        # Check if the route is active and valid
        is_active = bgp_output[str_route]["bgpRoutePaths"][0]["routeType"]["valid"]
        is_valid = bgp_output[str_route]["bgpRoutePaths"][0]["routeType"]["active"]

        # If the route is either inactive or invalid, add it to the failure routes dictionary
        if not is_active or not is_valid:
            failure["bgp_peers"][peer][vrf][route_type][str_route] = {"valid": is_valid, "active": is_active}
            failure_routes = deep_update(failure_routes, failure)

    return failure_routes


def _check_bgp_neighbor_capability(capability_status: dict[str, bool]) -> bool:
    """Check if a BGP neighbor capability is advertised, received, and enabled.

    Parameters
    ----------
    capability_status
        A dictionary containing the capability status.

    Returns
    -------
    bool
        True if the capability is advertised, received, and enabled, False otherwise.

    Example
    -------
    >>> _check_bgp_neighbor_capability({"advertised": True, "received": True, "enabled": True})
    True
    """
    return all(capability_status.get(state, False) for state in ("advertised", "received", "enabled"))


class VerifyBGPPeerCount(AntaTest):
    """Verifies the count of BGP peers for given address families.

    This test performs the following checks for each specified address family:

      1. Confirms that the specified VRF is configured.
      2. Counts the number of peers that are:
        - If `check_peer_state` is set to True, Counts the number of BGP peers that are in the `Established` state and
        have successfully negotiated the specified AFI/SAFI
        - If `check_peer_state` is set to False, skips validation of the `Established` state and AFI/SAFI negotiation.

    Expected Results
    ----------------
    * Success: If the count of BGP peers matches the expected count with `check_peer_state` enabled/disabled.
    * Failure: If any of the following occur:
        - The specified VRF is not configured.
        - The BGP peer count does not match expected value with `check_peer_state` enabled/disabled."

    Examples
    --------
    ```yaml
    anta.tests.routing:
      bgp:
        - VerifyBGPPeerCount:
            address_families:
              - afi: "evpn"
                num_peers: 2
              - afi: "ipv4"
                safi: "unicast"
                vrf: "PROD"
                num_peers: 2
              - afi: "ipv4"
                safi: "unicast"
                vrf: "default"
                num_peers: 3
              - afi: "ipv4"
                safi: "multicast"
                vrf: "DEV"
                num_peers: 3
    ```
    """

    categories: ClassVar[list[str]] = ["bgp"]
    commands: ClassVar[list[AntaCommand | AntaTemplate]] = [AntaCommand(command="show bgp summary vrf all", revision=1)]

    class Input(AntaTest.Input):
        """Input model for the VerifyBGPPeerCount test."""

        address_families: list[BgpAddressFamily]
        """List of BGP address families."""
        BgpAfi: ClassVar[type[BgpAfi]] = BgpAfi

        @field_validator("address_families")
        @classmethod
        def validate_address_families(cls, address_families: list[BgpAddressFamily]) -> list[BgpAddressFamily]:
            """Validate that 'num_peers' field is provided in each address family."""
            for af in address_families:
                if af.num_peers is None:
                    msg = f"{af} 'num_peers' field missing in the input"
                    raise ValueError(msg)
            return address_families

    @AntaTest.anta_test
    def test(self) -> None:
        """Main test function for VerifyBGPPeerCount."""
        self.result.is_success()

        output = self.instance_commands[0].json_output

        for address_family in self.inputs.address_families:
            # Check if the VRF is configured
            if (vrf_output := get_value(output, f"vrfs.{address_family.vrf}")) is None:
                self.result.is_failure(f"{address_family} - VRF not configured")
                continue

            peers_data = vrf_output.get("peers", {}).values()
            if not address_family.check_peer_state:
                # Count the number of peers without considering the state and negotiated AFI/SAFI check if the count matches the expected count
                peer_count = sum(1 for peer_data in peers_data if address_family.eos_key in peer_data)
            else:
                # Count the number of established peers with negotiated AFI/SAFI
                peer_count = sum(
                    1
                    for peer_data in peers_data
                    if peer_data.get("peerState") == "Established" and get_value(peer_data, f"{address_family.eos_key}.afiSafiState") == "negotiated"
                )

            # Check if the count matches the expected count
            if address_family.num_peers != peer_count:
                self.result.is_failure(f"{address_family} - Expected: {address_family.num_peers}, Actual: {peer_count}")


class VerifyBGPPeersHealth(AntaTest):
    """Verifies the health of BGP peers for given address families.

    This test performs the following checks for each specified address family:

      1. Validates that the VRF is configured.
      2. Checks if there are any peers for the given AFI/SAFI.
      3. For each relevant peer:
        - Verifies that the BGP session is in the `Established` state.
        - Confirms that the AFI/SAFI state is `negotiated`.
        - Checks that both input and output TCP message queues are empty.
          Can be disabled by setting `check_tcp_queues` to `False`.

    Expected Results
    ----------------
    * Success: If all checks pass for all specified address families and their peers.
    * Failure: If any of the following occur:
        - The specified VRF is not configured.
        - No peers are found for a given AFI/SAFI.
        - Any BGP session is not in the `Established` state.
        - The AFI/SAFI state is not 'negotiated' for any peer.
        - Any TCP message queue (input or output) is not empty when `check_tcp_queues` is `True` (default).

    Examples
    --------
    ```yaml
    anta.tests.routing:
      bgp:
        - VerifyBGPPeersHealth:
            address_families:
              - afi: "evpn"
              - afi: "ipv4"
                safi: "unicast"
                vrf: "default"
              - afi: "ipv6"
                safi: "unicast"
                vrf: "DEV"
                check_tcp_queues: false
    ```
    """

    categories: ClassVar[list[str]] = ["bgp"]
    commands: ClassVar[list[AntaCommand | AntaTemplate]] = [AntaCommand(command="show bgp neighbors vrf all", revision=3)]

    class Input(AntaTest.Input):
        """Input model for the VerifyBGPPeersHealth test."""

        address_families: list[BgpAddressFamily]
        """List of BGP address families."""
        BgpAfi: ClassVar[type[BgpAfi]] = BgpAfi

    @AntaTest.anta_test
    def test(self) -> None:
        """Main test function for VerifyBGPPeersHealth."""
        self.result.is_success()

        output = self.instance_commands[0].json_output

        for address_family in self.inputs.address_families:
            # Check if the VRF is configured
            if (vrf_output := get_value(output, f"vrfs.{address_family.vrf}")) is None:
                self.result.is_failure(f"{address_family} - VRF not configured")
                continue

            # Check if any peers are found for this AFI/SAFI
            relevant_peers = [
                peer for peer in vrf_output.get("peerList", []) if get_value(peer, f"neighborCapabilities.multiprotocolCaps.{address_family.eos_key}") is not None
            ]

            if not relevant_peers:
                self.result.is_failure(f"{address_family} - No peers found")
                continue

            for peer in relevant_peers:
                # Check if the BGP session is established
                if peer["state"] != "Established":
                    self.result.is_failure(f"{address_family} Peer: {peer['peerAddress']} - Session state is not established - State: {peer['state']}")
                    continue

                # Check if the AFI/SAFI state is negotiated
                capability_status = get_value(peer, f"neighborCapabilities.multiprotocolCaps.{address_family.eos_key}")
                if not _check_bgp_neighbor_capability(capability_status):
                    self.result.is_failure(f"{address_family} Peer: {peer['peerAddress']} - AFI/SAFI state is not negotiated - {format_data(capability_status)}")

                # Check the TCP session message queues
                if address_family.check_tcp_queues:
                    inq = peer["peerTcpInfo"]["inputQueueLength"]
                    outq = peer["peerTcpInfo"]["outputQueueLength"]
                    if inq != 0 or outq != 0:
                        self.result.is_failure(f"{address_family} Peer: {peer['peerAddress']} - Session has non-empty message queues - InQ: {inq}, OutQ: {outq}")


class VerifyBGPSpecificPeers(AntaTest):
    """Verifies the health of specific BGP peer(s) for given address families.

    This test performs the following checks for each specified address family and peer:

      1. Confirms that the specified VRF is configured.
      2. For each specified peer:
        - Verifies that the peer is found in the BGP configuration.
        - Checks that the BGP session is in the `Established` state.
        - Confirms that the AFI/SAFI state is `negotiated`.
        - Ensures that both input and output TCP message queues are empty.
          Can be disabled by setting `check_tcp_queues` to `False`.

    Expected Results
    ----------------
    * Success: If all checks pass for all specified peers in all address families.
    * Failure: If any of the following occur:
        - The specified VRF is not configured.
        - A specified peer is not found in the BGP configuration.
        - The BGP session for a peer is not in the `Established` state.
        - The AFI/SAFI state is not `negotiated` for a peer.
        - Any TCP message queue (input or output) is not empty for a peer when `check_tcp_queues` is `True` (default).

    Examples
    --------
    ```yaml
    anta.tests.routing:
      bgp:
        - VerifyBGPSpecificPeers:
            address_families:
              - afi: "evpn"
                peers:
                  - 10.1.0.1
                  - 10.1.0.2
              - afi: "ipv4"
                safi: "unicast"
                peers:
                  - 10.1.254.1
                  - 10.1.255.0
                  - 10.1.255.2
                  - 10.1.255.4
    ```
    """

    categories: ClassVar[list[str]] = ["bgp"]
    commands: ClassVar[list[AntaCommand | AntaTemplate]] = [AntaCommand(command="show bgp neighbors vrf all", revision=3)]

    class Input(AntaTest.Input):
        """Input model for the VerifyBGPSpecificPeers test."""

        address_families: list[BgpAddressFamily]
        """List of BGP address families."""
        BgpAfi: ClassVar[type[BgpAfi]] = BgpAfi

        @field_validator("address_families")
        @classmethod
        def validate_address_families(cls, address_families: list[BgpAddressFamily]) -> list[BgpAddressFamily]:
            """Validate that 'peers' field is provided in each address family."""
            for af in address_families:
                if af.peers is None:
                    msg = f"{af} 'peers' field missing in the input"
                    raise ValueError(msg)
            return address_families

    @AntaTest.anta_test
    def test(self) -> None:
        """Main test function for VerifyBGPSpecificPeers."""
        self.result.is_success()

        output = self.instance_commands[0].json_output

        for address_family in self.inputs.address_families:
            # Check if the VRF is configured
            if (vrf_output := get_value(output, f"vrfs.{address_family.vrf}")) is None:
                self.result.is_failure(f"{address_family} - VRF not configured")
                continue

            for peer in address_family.peers:
                peer_ip = str(peer)

                # Check if the peer is found
                if (peer_data := get_item(vrf_output["peerList"], "peerAddress", peer_ip)) is None:
                    self.result.is_failure(f"{address_family} Peer: {peer_ip} - Not configured")
                    continue

                # Check if the BGP session is established
                if peer_data["state"] != "Established":
                    self.result.is_failure(f"{address_family} Peer: {peer_ip} - Session state is not established - State: {peer_data['state']}")
                    continue

                # Check if the AFI/SAFI state is negotiated
                capability_status = get_value(peer_data, f"neighborCapabilities.multiprotocolCaps.{address_family.eos_key}")
                if not capability_status:
                    self.result.is_failure(f"{address_family} Peer: {peer_ip} - AFI/SAFI state is not negotiated")

                if capability_status and not _check_bgp_neighbor_capability(capability_status):
                    self.result.is_failure(f"{address_family} Peer: {peer_ip} - AFI/SAFI state is not negotiated - {format_data(capability_status)}")

                # Check the TCP session message queues
                if address_family.check_tcp_queues:
                    inq = peer_data["peerTcpInfo"]["inputQueueLength"]
                    outq = peer_data["peerTcpInfo"]["outputQueueLength"]
                    if inq != 0 or outq != 0:
                        self.result.is_failure(f"{address_family} Peer: {peer_ip} - Session has non-empty message queues - InQ: {inq}, OutQ: {outq}")


class VerifyBGPExchangedRoutes(AntaTest):
    """Verifies the advertised and received routes of BGP peers.

    The route type should be 'valid' and 'active' for a specified VRF.

    Expected Results
    ----------------
    * Success: If the BGP peers have correctly advertised and received routes of type 'valid' and 'active' for a specified VRF.
    * Failure: If a BGP peer is not found, the expected advertised/received routes are not found, or the routes are not 'valid' or 'active'.

    Examples
    --------
    ```yaml
    anta.tests.routing:
      bgp:
        - VerifyBGPExchangedRoutes:
            bgp_peers:
              - peer_address: 172.30.255.5
                vrf: default
                advertised_routes:
                  - 192.0.254.5/32
                received_routes:
                  - 192.0.255.4/32
              - peer_address: 172.30.255.1
                vrf: default
                advertised_routes:
                  - 192.0.255.1/32
                  - 192.0.254.5/32
                received_routes:
                  - 192.0.254.3/32
    ```
    """

    categories: ClassVar[list[str]] = ["bgp"]
    commands: ClassVar[list[AntaCommand | AntaTemplate]] = [
        AntaTemplate(template="show bgp neighbors {peer} advertised-routes vrf {vrf}", revision=3),
        AntaTemplate(template="show bgp neighbors {peer} routes vrf {vrf}", revision=3),
    ]

    class Input(AntaTest.Input):
        """Input model for the VerifyBGPExchangedRoutes test."""

        bgp_peers: list[BgpNeighbor]
        """List of BGP neighbors."""

        class BgpNeighbor(BaseModel):
            """Model for a BGP neighbor."""

            peer_address: IPv4Address
            """IPv4 address of a BGP peer."""
            vrf: str = "default"
            """Optional VRF for BGP peer. If not provided, it defaults to `default`."""
            advertised_routes: list[IPv4Network]
            """List of advertised routes in CIDR format."""
            received_routes: list[IPv4Network]
            """List of received routes in CIDR format."""

    def render(self, template: AntaTemplate) -> list[AntaCommand]:
        """Render the template for each BGP neighbor in the input list."""
        return [template.render(peer=str(bgp_peer.peer_address), vrf=bgp_peer.vrf) for bgp_peer in self.inputs.bgp_peers]

    @AntaTest.anta_test
    def test(self) -> None:
        """Main test function for VerifyBGPExchangedRoutes."""
        failures: dict[str, dict[str, Any]] = {"bgp_peers": {}}

        # Iterating over command output for different peers
        for command in self.instance_commands:
            peer = command.params.peer
            vrf = command.params.vrf
            for input_entry in self.inputs.bgp_peers:
                if str(input_entry.peer_address) == peer and input_entry.vrf == vrf:
                    advertised_routes = input_entry.advertised_routes
                    received_routes = input_entry.received_routes
                    break
            failure = {vrf: ""}

            # Verify if a BGP peer is configured with the provided vrf
            if not (bgp_routes := get_value(command.json_output, f"vrfs.{vrf}.bgpRouteEntries")):
                failure[vrf] = "Not configured"
                failures["bgp_peers"][peer] = failure
                continue

            # Validate advertised routes
            if "advertised-routes" in command.command:
                failure_routes = _add_bgp_routes_failure(advertised_routes, bgp_routes, peer, vrf)

            # Validate received routes
            else:
                failure_routes = _add_bgp_routes_failure(received_routes, bgp_routes, peer, vrf, route_type="received_routes")
            failures = deep_update(failures, failure_routes)

        if not failures["bgp_peers"]:
            self.result.is_success()
        else:
            self.result.is_failure(f"Following BGP peers are not found or routes are not exchanged properly:\n{failures}")


class VerifyBGPPeerMPCaps(AntaTest):
    """Verifies the multiprotocol capabilities of a BGP peer in a specified VRF.

    Supports `strict: True` to verify that only the specified capabilities are configured, requiring an exact match.

    Expected Results
    ----------------
    * Success: The test will pass if the BGP peer's multiprotocol capabilities are advertised, received, and enabled in the specified VRF.
    * Failure: The test will fail if BGP peers are not found or multiprotocol capabilities are not advertised, received, and enabled in the specified VRF.

    Examples
    --------
    ```yaml
    anta.tests.routing:
      bgp:
        - VerifyBGPPeerMPCaps:
            bgp_peers:
              - peer_address: 172.30.11.1
                vrf: default
                strict: False
                capabilities:
                  - ipv4Unicast
    ```
    """

    description = "Verifies the multiprotocol capabilities of a BGP peer."
    categories: ClassVar[list[str]] = ["bgp"]
    commands: ClassVar[list[AntaCommand | AntaTemplate]] = [AntaCommand(command="show bgp neighbors vrf all", revision=3)]

    class Input(AntaTest.Input):
        """Input model for the VerifyBGPPeerMPCaps test."""

        bgp_peers: list[BgpPeer]
        """List of BGP peers"""

        class BgpPeer(BaseModel):
            """Model for a BGP peer."""

            peer_address: IPv4Address
            """IPv4 address of a BGP peer."""
            vrf: str = "default"
            """Optional VRF for BGP peer. If not provided, it defaults to `default`."""
            strict: bool = False
            """If True, requires exact matching of provided capabilities. Defaults to False."""
            capabilities: list[MultiProtocolCaps]
            """List of multiprotocol capabilities to be verified."""

    @AntaTest.anta_test
    def test(self) -> None:
        """Main test function for VerifyBGPPeerMPCaps."""
        failures: dict[str, Any] = {"bgp_peers": {}}

        # Iterate over each bgp peer.
        for bgp_peer in self.inputs.bgp_peers:
            peer = str(bgp_peer.peer_address)
            vrf = bgp_peer.vrf
            capabilities = bgp_peer.capabilities
            failure: dict[str, dict[str, dict[str, Any]]] = {"bgp_peers": {peer: {vrf: {}}}}

            # Check if BGP output exists.
            if (
                not (bgp_output := get_value(self.instance_commands[0].json_output, f"vrfs.{vrf}.peerList"))
                or (bgp_output := get_item(bgp_output, "peerAddress", peer)) is None
            ):
                failure["bgp_peers"][peer][vrf] = {"status": "Not configured"}
                failures = deep_update(failures, failure)
                continue

            # Fetching the capabilities output.
            bgp_output = get_value(bgp_output, "neighborCapabilities.multiprotocolCaps")

            if bgp_peer.strict and sorted(capabilities) != sorted(bgp_output):
                failure["bgp_peers"][peer][vrf] = {
                    "status": f"Expected only `{', '.join(capabilities)}` capabilities should be listed but found `{', '.join(bgp_output)}` instead."
                }
                failures = deep_update(failures, failure)
                continue

            # Check each capability
            for capability in capabilities:
                capability_output = bgp_output.get(capability)

                # Check if capabilities are missing
                if not capability_output:
                    failure["bgp_peers"][peer][vrf][capability] = "not found"
                    failures = deep_update(failures, failure)

                # Check if capabilities are not advertised, received, or enabled
                elif not all(capability_output.get(prop, False) for prop in ["advertised", "received", "enabled"]):
                    failure["bgp_peers"][peer][vrf][capability] = capability_output
                    failures = deep_update(failures, failure)

        # Check if there are any failures
        if not failures["bgp_peers"]:
            self.result.is_success()
        else:
            self.result.is_failure(f"Following BGP peer multiprotocol capabilities are not found or not ok:\n{failures}")


class VerifyBGPPeerASNCap(AntaTest):
    """Verifies the four octet asn capabilities of a BGP peer in a specified VRF.

    Expected Results
    ----------------
    * Success: The test will pass if BGP peer's four octet asn capabilities are advertised, received, and enabled in the specified VRF.
    * Failure: The test will fail if BGP peers are not found or four octet asn capabilities are not advertised, received, and enabled in the specified VRF.

    Examples
    --------
    ```yaml
    anta.tests.routing:
      bgp:
        - VerifyBGPPeerASNCap:
            bgp_peers:
              - peer_address: 172.30.11.1
                vrf: default
    ```
    """

    description = "Verifies the four octet asn capabilities of a BGP peer."
    categories: ClassVar[list[str]] = ["bgp"]
    commands: ClassVar[list[AntaCommand | AntaTemplate]] = [AntaCommand(command="show bgp neighbors vrf all", revision=3)]

    class Input(AntaTest.Input):
        """Input model for the VerifyBGPPeerASNCap test."""

        bgp_peers: list[BgpPeer]
        """List of BGP peers."""

        class BgpPeer(BaseModel):
            """Model for a BGP peer."""

            peer_address: IPv4Address
            """IPv4 address of a BGP peer."""
            vrf: str = "default"
            """Optional VRF for BGP peer. If not provided, it defaults to `default`."""

    @AntaTest.anta_test
    def test(self) -> None:
        """Main test function for VerifyBGPPeerASNCap."""
        failures: dict[str, Any] = {"bgp_peers": {}}

        # Iterate over each bgp peer
        for bgp_peer in self.inputs.bgp_peers:
            peer = str(bgp_peer.peer_address)
            vrf = bgp_peer.vrf
            failure: dict[str, dict[str, dict[str, Any]]] = {"bgp_peers": {peer: {vrf: {}}}}

            # Check if BGP output exists
            if (
                not (bgp_output := get_value(self.instance_commands[0].json_output, f"vrfs.{vrf}.peerList"))
                or (bgp_output := get_item(bgp_output, "peerAddress", peer)) is None
            ):
                failure["bgp_peers"][peer][vrf] = {"status": "Not configured"}
                failures = deep_update(failures, failure)
                continue

            bgp_output = get_value(bgp_output, "neighborCapabilities.fourOctetAsnCap")

            # Check if  four octet asn capabilities are found
            if not bgp_output:
                failure["bgp_peers"][peer][vrf] = {"fourOctetAsnCap": "not found"}
                failures = deep_update(failures, failure)

            # Check if capabilities are not advertised, received, or enabled
            elif not all(bgp_output.get(prop, False) for prop in ["advertised", "received", "enabled"]):
                failure["bgp_peers"][peer][vrf] = {"fourOctetAsnCap": bgp_output}
                failures = deep_update(failures, failure)

        # Check if there are any failures
        if not failures["bgp_peers"]:
            self.result.is_success()
        else:
            self.result.is_failure(f"Following BGP peer four octet asn capabilities are not found or not ok:\n{failures}")


class VerifyBGPPeerRouteRefreshCap(AntaTest):
    """Verifies the route refresh capabilities of a BGP peer in a specified VRF.

    Expected Results
    ----------------
    * Success: The test will pass if the BGP peer's route refresh capabilities are advertised, received, and enabled in the specified VRF.
    * Failure: The test will fail if BGP peers are not found or route refresh capabilities are not advertised, received, and enabled in the specified VRF.

    Examples
    --------
    ```yaml
    anta.tests.routing:
      bgp:
        - VerifyBGPPeerRouteRefreshCap:
            bgp_peers:
              - peer_address: 172.30.11.1
                vrf: default
    ```
    """

    description = "Verifies the route refresh capabilities of a BGP peer."
    categories: ClassVar[list[str]] = ["bgp"]
    commands: ClassVar[list[AntaCommand | AntaTemplate]] = [AntaCommand(command="show bgp neighbors vrf all", revision=3)]

    class Input(AntaTest.Input):
        """Input model for the VerifyBGPPeerRouteRefreshCap test."""

        bgp_peers: list[BgpPeer]
        """List of BGP peers"""

        class BgpPeer(BaseModel):
            """Model for a BGP peer."""

            peer_address: IPv4Address
            """IPv4 address of a BGP peer."""
            vrf: str = "default"
            """Optional VRF for BGP peer. If not provided, it defaults to `default`."""

    @AntaTest.anta_test
    def test(self) -> None:
        """Main test function for VerifyBGPPeerRouteRefreshCap."""
        failures: dict[str, Any] = {"bgp_peers": {}}

        # Iterate over each bgp peer
        for bgp_peer in self.inputs.bgp_peers:
            peer = str(bgp_peer.peer_address)
            vrf = bgp_peer.vrf
            failure: dict[str, dict[str, dict[str, Any]]] = {"bgp_peers": {peer: {vrf: {}}}}

            # Check if BGP output exists
            if (
                not (bgp_output := get_value(self.instance_commands[0].json_output, f"vrfs.{vrf}.peerList"))
                or (bgp_output := get_item(bgp_output, "peerAddress", peer)) is None
            ):
                failure["bgp_peers"][peer][vrf] = {"status": "Not configured"}
                failures = deep_update(failures, failure)
                continue

            bgp_output = get_value(bgp_output, "neighborCapabilities.routeRefreshCap")

            # Check if route refresh capabilities are found
            if not bgp_output:
                failure["bgp_peers"][peer][vrf] = {"routeRefreshCap": "not found"}
                failures = deep_update(failures, failure)

            # Check if capabilities are not advertised, received, or enabled
            elif not all(bgp_output.get(prop, False) for prop in ["advertised", "received", "enabled"]):
                failure["bgp_peers"][peer][vrf] = {"routeRefreshCap": bgp_output}
                failures = deep_update(failures, failure)

        # Check if there are any failures
        if not failures["bgp_peers"]:
            self.result.is_success()
        else:
            self.result.is_failure(f"Following BGP peer route refresh capabilities are not found or not ok:\n{failures}")


class VerifyBGPPeerMD5Auth(AntaTest):
    """Verifies the MD5 authentication and state of IPv4 BGP peers in a specified VRF.

    Expected Results
    ----------------
    * Success: The test will pass if IPv4 BGP peers are configured with MD5 authentication and state as established in the specified VRF.
    * Failure: The test will fail if IPv4 BGP peers are not found, state is not as established or MD5 authentication is not enabled in the specified VRF.

    Examples
    --------
    ```yaml
    anta.tests.routing:
      bgp:
        - VerifyBGPPeerMD5Auth:
            bgp_peers:
              - peer_address: 172.30.11.1
                vrf: default
              - peer_address: 172.30.11.5
                vrf: default
    ```
    """

    description = "Verifies the MD5 authentication and state of a BGP peer."
    categories: ClassVar[list[str]] = ["bgp"]
    commands: ClassVar[list[AntaCommand | AntaTemplate]] = [AntaCommand(command="show bgp neighbors vrf all", revision=3)]

    class Input(AntaTest.Input):
        """Input model for the VerifyBGPPeerMD5Auth test."""

        bgp_peers: list[BgpPeer]
        """List of IPv4 BGP peers."""

        class BgpPeer(BaseModel):
            """Model for a BGP peer."""

            peer_address: IPv4Address
            """IPv4 address of BGP peer."""
            vrf: str = "default"
            """Optional VRF for BGP peer. If not provided, it defaults to `default`."""

    @AntaTest.anta_test
    def test(self) -> None:
        """Main test function for VerifyBGPPeerMD5Auth."""
        failures: dict[str, Any] = {"bgp_peers": {}}

        # Iterate over each command
        for bgp_peer in self.inputs.bgp_peers:
            peer = str(bgp_peer.peer_address)
            vrf = bgp_peer.vrf
            failure: dict[str, dict[str, dict[str, Any]]] = {"bgp_peers": {peer: {vrf: {}}}}

            # Check if BGP output exists
            if (
                not (bgp_output := get_value(self.instance_commands[0].json_output, f"vrfs.{vrf}.peerList"))
                or (bgp_output := get_item(bgp_output, "peerAddress", peer)) is None
            ):
                failure["bgp_peers"][peer][vrf] = {"status": "Not configured"}
                failures = deep_update(failures, failure)
                continue

            # Check if BGP peer state and authentication
            state = bgp_output.get("state")
            md5_auth_enabled = bgp_output.get("md5AuthEnabled")
            if state != "Established" or not md5_auth_enabled:
                failure["bgp_peers"][peer][vrf] = {"state": state, "md5_auth_enabled": md5_auth_enabled}
                failures = deep_update(failures, failure)

        # Check if there are any failures
        if not failures["bgp_peers"]:
            self.result.is_success()
        else:
            self.result.is_failure(f"Following BGP peers are not configured, not established or MD5 authentication is not enabled:\n{failures}")


class VerifyEVPNType2Route(AntaTest):
    """Verifies the EVPN Type-2 routes for a given IPv4 or MAC address and VNI.

    Expected Results
    ----------------
    * Success: If all provided VXLAN endpoints have at least one valid and active path to their EVPN Type-2 routes.
    * Failure: If any of the provided VXLAN endpoints do not have at least one valid and active path to their EVPN Type-2 routes.

    Examples
    --------
    ```yaml
    anta.tests.routing:
      bgp:
        - VerifyEVPNType2Route:
            vxlan_endpoints:
              - address: 192.168.20.102
                vni: 10020
              - address: aac1.ab5d.b41e
                vni: 10010
    ```
    """

    categories: ClassVar[list[str]] = ["bgp"]
    commands: ClassVar[list[AntaCommand | AntaTemplate]] = [AntaTemplate(template="show bgp evpn route-type mac-ip {address} vni {vni}", revision=2)]

    class Input(AntaTest.Input):
        """Input model for the VerifyEVPNType2Route test."""

        vxlan_endpoints: list[VxlanEndpoint]
        """List of VXLAN endpoints to verify."""

        class VxlanEndpoint(BaseModel):
            """Model for a VXLAN endpoint."""

            address: IPv4Address | MacAddress
            """IPv4 or MAC address of the VXLAN endpoint."""
            vni: Vni
            """VNI of the VXLAN endpoint."""

    def render(self, template: AntaTemplate) -> list[AntaCommand]:
        """Render the template for each VXLAN endpoint in the input list."""
        return [template.render(address=str(endpoint.address), vni=endpoint.vni) for endpoint in self.inputs.vxlan_endpoints]

    @AntaTest.anta_test
    def test(self) -> None:
        """Main test function for VerifyEVPNType2Route."""
        self.result.is_success()
        no_evpn_routes = []
        bad_evpn_routes = []

        for command in self.instance_commands:
            address = command.params.address
            vni = command.params.vni
            # Verify that the VXLAN endpoint is in the BGP EVPN table
            evpn_routes = command.json_output["evpnRoutes"]
            if not evpn_routes:
                no_evpn_routes.append((address, vni))
                continue

            # Verify that at least one EVPN route has at least one active/valid path across all learned routes from all RDs combined
            has_active_path = False
            for route_data in evpn_routes.values():
                for path in route_data.get("evpnRoutePaths", []):
                    route_type = path.get("routeType", {})
                    if route_type.get("active") and route_type.get("valid"):
                        has_active_path = True
                        break
            if not has_active_path:
                bad_evpn_routes.extend(list(evpn_routes))

        if no_evpn_routes:
            self.result.is_failure(f"The following VXLAN endpoint do not have any EVPN Type-2 route: {no_evpn_routes}")
        if bad_evpn_routes:
            self.result.is_failure(f"The following EVPN Type-2 routes do not have at least one valid and active path: {bad_evpn_routes}")


class VerifyBGPAdvCommunities(AntaTest):
    """Verifies if the advertised communities of BGP peers are standard, extended, and large in the specified VRF.

    Expected Results
    ----------------
    * Success: The test will pass if the advertised communities of BGP peers are standard, extended, and large in the specified VRF.
    * Failure: The test will fail if the advertised communities of BGP peers are not standard, extended, and large in the specified VRF.

    Examples
    --------
    ```yaml
    anta.tests.routing:
      bgp:
        - VerifyBGPAdvCommunities:
            bgp_peers:
              - peer_address: 172.30.11.17
                vrf: default
              - peer_address: 172.30.11.21
                vrf: default
    ```
    """

    description = "Verifies the advertised communities of a BGP peer."
    categories: ClassVar[list[str]] = ["bgp"]
    commands: ClassVar[list[AntaCommand | AntaTemplate]] = [AntaCommand(command="show bgp neighbors vrf all", revision=3)]

    class Input(AntaTest.Input):
        """Input model for the VerifyBGPAdvCommunities test."""

        bgp_peers: list[BgpPeer]
        """List of BGP peers."""

        class BgpPeer(BaseModel):
            """Model for a BGP peer."""

            peer_address: IPv4Address
            """IPv4 address of a BGP peer."""
            vrf: str = "default"
            """Optional VRF for BGP peer. If not provided, it defaults to `default`."""

    @AntaTest.anta_test
    def test(self) -> None:
        """Main test function for VerifyBGPAdvCommunities."""
        failures: dict[str, Any] = {"bgp_peers": {}}

        # Iterate over each bgp peer
        for bgp_peer in self.inputs.bgp_peers:
            peer = str(bgp_peer.peer_address)
            vrf = bgp_peer.vrf
            failure: dict[str, dict[str, dict[str, Any]]] = {"bgp_peers": {peer: {vrf: {}}}}

            # Verify BGP peer
            if (
                not (bgp_output := get_value(self.instance_commands[0].json_output, f"vrfs.{vrf}.peerList"))
                or (bgp_output := get_item(bgp_output, "peerAddress", peer)) is None
            ):
                failure["bgp_peers"][peer][vrf] = {"status": "Not configured"}
                failures = deep_update(failures, failure)
                continue

            # Verify BGP peer's advertised communities
            bgp_output = bgp_output.get("advertisedCommunities")
            if not bgp_output["standard"] or not bgp_output["extended"] or not bgp_output["large"]:
                failure["bgp_peers"][peer][vrf] = {"advertised_communities": bgp_output}
                failures = deep_update(failures, failure)

        if not failures["bgp_peers"]:
            self.result.is_success()
        else:
            self.result.is_failure(f"Following BGP peers are not configured or advertised communities are not standard, extended, and large:\n{failures}")


class VerifyBGPTimers(AntaTest):
    """Verifies if the BGP peers are configured with the correct hold and keep-alive timers in the specified VRF.

    Expected Results
    ----------------
    * Success: The test will pass if the hold and keep-alive timers are correct for BGP peers in the specified VRF.
    * Failure: The test will fail if BGP peers are not found or hold and keep-alive timers are not correct in the specified VRF.

    Examples
    --------
    ```yaml
    anta.tests.routing:
      bgp:
        - VerifyBGPTimers:
            bgp_peers:
              - peer_address: 172.30.11.1
                vrf: default
                hold_time: 180
                keep_alive_time: 60
              - peer_address: 172.30.11.5
                vrf: default
                hold_time: 180
                keep_alive_time: 60
    ```
    """

    description = "Verifies the timers of a BGP peer."
    categories: ClassVar[list[str]] = ["bgp"]
    commands: ClassVar[list[AntaCommand | AntaTemplate]] = [AntaCommand(command="show bgp neighbors vrf all", revision=3)]

    class Input(AntaTest.Input):
        """Input model for the VerifyBGPTimers test."""

        bgp_peers: list[BgpPeer]
        """List of BGP peers"""

        class BgpPeer(BaseModel):
            """Model for a BGP peer."""

            peer_address: IPv4Address
            """IPv4 address of a BGP peer."""
            vrf: str = "default"
            """Optional VRF for BGP peer. If not provided, it defaults to `default`."""
            hold_time: int = Field(ge=3, le=7200)
            """BGP hold time in seconds."""
            keep_alive_time: int = Field(ge=0, le=3600)
            """BGP keep-alive time in seconds."""

    @AntaTest.anta_test
    def test(self) -> None:
        """Main test function for VerifyBGPTimers."""
        failures: dict[str, Any] = {}

        # Iterate over each bgp peer
        for bgp_peer in self.inputs.bgp_peers:
            peer_address = str(bgp_peer.peer_address)
            vrf = bgp_peer.vrf
            hold_time = bgp_peer.hold_time
            keep_alive_time = bgp_peer.keep_alive_time

            # Verify BGP peer
            if (
                not (bgp_output := get_value(self.instance_commands[0].json_output, f"vrfs.{vrf}.peerList"))
                or (bgp_output := get_item(bgp_output, "peerAddress", peer_address)) is None
            ):
                failures[peer_address] = {vrf: "Not configured"}
                continue

            # Verify BGP peer's hold and keep alive timers
            if bgp_output.get("holdTime") != hold_time or bgp_output.get("keepaliveTime") != keep_alive_time:
                failures[peer_address] = {vrf: {"hold_time": bgp_output.get("holdTime"), "keep_alive_time": bgp_output.get("keepaliveTime")}}

        if not failures:
            self.result.is_success()
        else:
            self.result.is_failure(f"Following BGP peers are not configured or hold and keep-alive timers are not correct:\n{failures}")


class VerifyBGPPeerDropStats(AntaTest):
    """Verifies BGP NLRI drop statistics for the provided BGP IPv4 peer(s).

    By default, all drop statistics counters will be checked for any non-zero values.
    An optional list of specific drop statistics can be provided for granular testing.

    Expected Results
    ----------------
    * Success: The test will pass if the BGP peer's drop statistic(s) are zero.
    * Failure: The test will fail if the BGP peer's drop statistic(s) are non-zero/Not Found or peer is not configured.

    Examples
    --------
    ```yaml
    anta.tests.routing:
      bgp:
        - VerifyBGPPeerDropStats:
            bgp_peers:
              - peer_address: 172.30.11.1
                vrf: default
                drop_stats:
                  - inDropAsloop
                  - prefixEvpnDroppedUnsupportedRouteType
    ```
    """

    categories: ClassVar[list[str]] = ["bgp"]
    commands: ClassVar[list[AntaCommand | AntaTemplate]] = [AntaTemplate(template="show bgp neighbors {peer} vrf {vrf}", revision=3)]

    class Input(AntaTest.Input):
        """Input model for the VerifyBGPPeerDropStats test."""

        bgp_peers: list[BgpPeer]
        """List of BGP peers"""

        class BgpPeer(BaseModel):
            """Model for a BGP peer."""

            peer_address: IPv4Address
            """IPv4 address of a BGP peer."""
            vrf: str = "default"
            """Optional VRF for BGP peer. If not provided, it defaults to `default`."""
            drop_stats: list[BgpDropStats] | None = None
            """Optional list of drop statistics to be verified. If not provided, test will verifies all the drop statistics."""

    def render(self, template: AntaTemplate) -> list[AntaCommand]:
        """Render the template for each BGP peer in the input list."""
        return [template.render(peer=str(bgp_peer.peer_address), vrf=bgp_peer.vrf) for bgp_peer in self.inputs.bgp_peers]

    @AntaTest.anta_test
    def test(self) -> None:
        """Main test function for VerifyBGPPeerDropStats."""
        failures: dict[Any, Any] = {}

        for command, input_entry in zip(self.instance_commands, self.inputs.bgp_peers):
            peer = command.params.peer
            vrf = command.params.vrf
            drop_statistics = input_entry.drop_stats

            # Verify BGP peer
            if not (peer_list := get_value(command.json_output, f"vrfs.{vrf}.peerList")) or (peer_detail := get_item(peer_list, "peerAddress", peer)) is None:
                failures[peer] = {vrf: "Not configured"}
                continue

            # Verify BGP peer's drop stats
            drop_stats_output = peer_detail.get("dropStats", {})

            # In case drop stats not provided, It will check all drop statistics
            if not drop_statistics:
                drop_statistics = drop_stats_output

            # Verify BGP peer's drop stats
            drop_stats_not_ok = {
                drop_stat: drop_stats_output.get(drop_stat, "Not Found") for drop_stat in drop_statistics if drop_stats_output.get(drop_stat, "Not Found")
            }
            if any(drop_stats_not_ok):
                failures[peer] = {vrf: drop_stats_not_ok}

        # Check if any failures
        if not failures:
            self.result.is_success()
        else:
            self.result.is_failure(f"The following BGP peers are not configured or have non-zero NLRI drop statistics counters:\n{failures}")


class VerifyBGPPeerUpdateErrors(AntaTest):
    """Verifies BGP update error counters for the provided BGP IPv4 peer(s).

    By default, all update error counters will be checked for any non-zero values.
    An optional list of specific update error counters can be provided for granular testing.

    Note: For "disabledAfiSafi" error counter field, checking that it's not "None" versus 0.

    Expected Results
    ----------------
    * Success: The test will pass if the BGP peer's update error counter(s) are zero/None.
    * Failure: The test will fail if the BGP peer's update error counter(s) are non-zero/not None/Not Found or
    peer is not configured.

    Examples
    --------
    ```yaml
    anta.tests.routing:
      bgp:
        - VerifyBGPPeerUpdateErrors:
            bgp_peers:
              - peer_address: 172.30.11.1
                vrf: default
                update_error_filter:
                  - inUpdErrWithdraw
    ```
    """

    categories: ClassVar[list[str]] = ["bgp"]
    commands: ClassVar[list[AntaCommand | AntaTemplate]] = [AntaTemplate(template="show bgp neighbors {peer} vrf {vrf}", revision=3)]

    class Input(AntaTest.Input):
        """Input model for the VerifyBGPPeerUpdateErrors test."""

        bgp_peers: list[BgpPeer]
        """List of BGP peers"""

        class BgpPeer(BaseModel):
            """Model for a BGP peer."""

            peer_address: IPv4Address
            """IPv4 address of a BGP peer."""
            vrf: str = "default"
            """Optional VRF for BGP peer. If not provided, it defaults to `default`."""
            update_errors: list[BgpUpdateError] | None = None
            """Optional list of update error counters to be verified. If not provided, test will verifies all the update error counters."""

    def render(self, template: AntaTemplate) -> list[AntaCommand]:
        """Render the template for each BGP peer in the input list."""
        return [template.render(peer=str(bgp_peer.peer_address), vrf=bgp_peer.vrf) for bgp_peer in self.inputs.bgp_peers]

    @AntaTest.anta_test
    def test(self) -> None:
        """Main test function for VerifyBGPPeerUpdateErrors."""
        failures: dict[Any, Any] = {}

        for command, input_entry in zip(self.instance_commands, self.inputs.bgp_peers):
            peer = command.params.peer
            vrf = command.params.vrf
            update_error_counters = input_entry.update_errors

            # Verify BGP peer.
            if not (peer_list := get_value(command.json_output, f"vrfs.{vrf}.peerList")) or (peer_detail := get_item(peer_list, "peerAddress", peer)) is None:
                failures[peer] = {vrf: "Not configured"}
                continue

            # Getting the BGP peer's error counters output.
            error_counters_output = peer_detail.get("peerInUpdateErrors", {})

            # In case update error counters not provided, It will check all the update error counters.
            if not update_error_counters:
                update_error_counters = error_counters_output

            # verifying the error counters.
            error_counters_not_ok = {
                ("disabledAfiSafi" if error_counter == "disabledAfiSafi" else error_counter): value
                for error_counter in update_error_counters
                if (value := error_counters_output.get(error_counter, "Not Found")) != "None" and value != 0
            }
            if error_counters_not_ok:
                failures[peer] = {vrf: error_counters_not_ok}

        # Check if any failures
        if not failures:
            self.result.is_success()
        else:
            self.result.is_failure(f"The following BGP peers are not configured or have non-zero update error counters:\n{failures}")


class VerifyBgpRouteMaps(AntaTest):
    """Verifies BGP inbound and outbound route-maps of BGP IPv4 peer(s).

    Expected Results
    ----------------
    * Success: The test will pass if the correct route maps are applied in the correct direction (inbound or outbound) for IPv4 BGP peers in the specified VRF.
    * Failure: The test will fail if BGP peers are not configured or any neighbor has an incorrect or missing route map in either the inbound or outbound direction.

    Examples
    --------
    ```yaml
    anta.tests.routing:
      bgp:
        - VerifyBgpRouteMaps:
            bgp_peers:
              - peer_address: 172.30.11.1
                vrf: default
                inbound_route_map: RM-MLAG-PEER-IN
                outbound_route_map: RM-MLAG-PEER-OUT
    ```
    """

    categories: ClassVar[list[str]] = ["bgp"]
    commands: ClassVar[list[AntaCommand | AntaTemplate]] = [AntaTemplate(template="show bgp neighbors {peer} vrf {vrf}", revision=3)]

    class Input(AntaTest.Input):
        """Input model for the VerifyBgpRouteMaps test."""

        bgp_peers: list[BgpPeer]
        """List of BGP peers"""

        class BgpPeer(BaseModel):
            """Model for a BGP peer."""

            peer_address: IPv4Address
            """IPv4 address of a BGP peer."""
            vrf: str = "default"
            """Optional VRF for BGP peer. If not provided, it defaults to `default`."""
            inbound_route_map: str | None = None
            """Inbound route map applied, defaults to None."""
            outbound_route_map: str | None = None
            """Outbound route map applied, defaults to None."""

            @model_validator(mode="after")
            def validate_inputs(self) -> Self:
                """Validate the inputs provided to the BgpPeer class.

                At least one of 'inbound' or 'outbound' route-map must be provided.
                """
                if not (self.inbound_route_map or self.outbound_route_map):
                    msg = "At least one of 'inbound_route_map' or 'outbound_route_map' must be provided."
                    raise ValueError(msg)
                return self

    def render(self, template: AntaTemplate) -> list[AntaCommand]:
        """Render the template for each BGP peer in the input list."""
        return [template.render(peer=str(bgp_peer.peer_address), vrf=bgp_peer.vrf) for bgp_peer in self.inputs.bgp_peers]

    @AntaTest.anta_test
    def test(self) -> None:
        """Main test function for VerifyBgpRouteMaps."""
        failures: dict[Any, Any] = {}

        for command, input_entry in zip(self.instance_commands, self.inputs.bgp_peers):
            peer = str(input_entry.peer_address)
            vrf = input_entry.vrf
            inbound_route_map = input_entry.inbound_route_map
            outbound_route_map = input_entry.outbound_route_map
            failure: dict[Any, Any] = {vrf: {}}

            # Verify BGP peer.
            if not (peer_list := get_value(command.json_output, f"vrfs.{vrf}.peerList")) or (peer_detail := get_item(peer_list, "peerAddress", peer)) is None:
                failures[peer] = {vrf: "Not configured"}
                continue

            # Verify Inbound route-map
            if inbound_route_map and (inbound_map := peer_detail.get("routeMapInbound", "Not Configured")) != inbound_route_map:
                failure[vrf].update({"Inbound route-map": inbound_map})

            # Verify Outbound route-map
            if outbound_route_map and (outbound_map := peer_detail.get("routeMapOutbound", "Not Configured")) != outbound_route_map:
                failure[vrf].update({"Outbound route-map": outbound_map})

            if failure[vrf]:
                failures[peer] = failure

        # Check if any failures
        if not failures:
            self.result.is_success()
        else:
            self.result.is_failure(
                f"The following BGP peers are not configured or has an incorrect or missing route map in either the inbound or outbound direction:\n{failures}"
            )


class VerifyBGPPeerRouteLimit(AntaTest):
    """Verifies the maximum routes and optionally verifies the maximum routes warning limit for the provided BGP IPv4 peer(s).

    Expected Results
    ----------------
    * Success: The test will pass if the BGP peer's maximum routes and, if provided, the maximum routes warning limit are equal to the given limits.
    * Failure: The test will fail if the BGP peer's maximum routes do not match the given limit, or if the maximum routes warning limit is provided
    and does not match the given limit, or if the peer is not configured.

    Examples
    --------
    ```yaml
    anta.tests.routing:
      bgp:
        - VerifyBGPPeerRouteLimit:
            bgp_peers:
              - peer_address: 172.30.11.1
                vrf: default
                maximum_routes: 12000
                warning_limit: 10000
    ```
    """

    categories: ClassVar[list[str]] = ["bgp"]
    commands: ClassVar[list[AntaCommand | AntaTemplate]] = [AntaTemplate(template="show bgp neighbors {peer} vrf {vrf}", revision=3)]

    class Input(AntaTest.Input):
        """Input model for the VerifyBGPPeerRouteLimit test."""

        bgp_peers: list[BgpPeer]
        """List of BGP peers"""

        class BgpPeer(BaseModel):
            """Model for a BGP peer."""

            peer_address: IPv4Address
            """IPv4 address of a BGP peer."""
            vrf: str = "default"
            """Optional VRF for BGP peer. If not provided, it defaults to `default`."""
            maximum_routes: int = Field(ge=0, le=4294967294)
            """The maximum allowable number of BGP routes, `0` means unlimited."""
            warning_limit: int = Field(default=0, ge=0, le=4294967294)
            """Optional maximum routes warning limit. If not provided, it defaults to `0` meaning no warning limit."""

    def render(self, template: AntaTemplate) -> list[AntaCommand]:
        """Render the template for each BGP peer in the input list."""
        return [template.render(peer=str(bgp_peer.peer_address), vrf=bgp_peer.vrf) for bgp_peer in self.inputs.bgp_peers]

    @AntaTest.anta_test
    def test(self) -> None:
        """Main test function for VerifyBGPPeerRouteLimit."""
        failures: dict[Any, Any] = {}

        for command, input_entry in zip(self.instance_commands, self.inputs.bgp_peers):
            peer = str(input_entry.peer_address)
            vrf = input_entry.vrf
            maximum_routes = input_entry.maximum_routes
            warning_limit = input_entry.warning_limit
            failure: dict[Any, Any] = {}

            # Verify BGP peer.
            if not (peer_list := get_value(command.json_output, f"vrfs.{vrf}.peerList")) or (peer_detail := get_item(peer_list, "peerAddress", peer)) is None:
                failures[peer] = {vrf: "Not configured"}
                continue

            # Verify maximum routes configured.
            if (actual_routes := peer_detail.get("maxTotalRoutes", "Not Found")) != maximum_routes:
                failure["Maximum total routes"] = actual_routes

            # Verify warning limit if given.
            if warning_limit and (actual_warning_limit := peer_detail.get("totalRoutesWarnLimit", "Not Found")) != warning_limit:
                failure["Warning limit"] = actual_warning_limit

            # Updated failures if any.
            if failure:
                failures[peer] = {vrf: failure}

        # Check if any failures
        if not failures:
            self.result.is_success()
        else:
            self.result.is_failure(f"The following BGP peer(s) are not configured or maximum routes and maximum routes warning limit is not correct:\n{failures}")
