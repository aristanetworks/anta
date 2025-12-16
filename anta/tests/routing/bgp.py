# Copyright (c) 2023-2025 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Module related to BGP tests."""

# pylint: disable=too-many-lines

# Pyright does not understand AntaTest.Input typing
# pyright: reportAttributeAccessIssue=false
from __future__ import annotations

from typing import Any, ClassVar, TypeVar

from pydantic import PositiveInt, field_validator

from anta.input_models.routing.bgp import BgpAddressFamily, BgpAfi, BgpNeighbor, BgpPeer, BgpRoute, BgpVrf, VxlanEndpoint
from anta.models import AntaCommand, AntaTemplate, AntaTest
from anta.tools import format_data, get_item, get_value

T = TypeVar("T", bound=BgpPeer)

# TODO: Refactor to reduce the number of lines in this module later


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


def _get_bgp_peer_data(peer: BgpPeer, command_output: dict[str, Any]) -> dict[str, Any] | None:
    """Retrieve BGP peer data for the given peer from the command output.

    Parameters
    ----------
    peer
        The BgpPeer object to look up.
    command_output
        Parsed output of the command.

    Returns
    -------
    dict | None
        The peer data dictionary if found, otherwise None.
    """
    if peer.interface is not None:
        # RFC5549
        identity = peer.interface
        lookup_key = "ifName"
    else:
        identity = str(peer.peer_address)
        lookup_key = "peerAddress"

    peer_list = get_value(command_output, f"vrfs.{peer.vrf}.peerList", default=[])

    return get_item(peer_list, lookup_key, identity)


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
                self.result.is_failure(f"{address_family} - Peer count mismatch - Expected: {address_family.num_peers} Actual: {peer_count}")


class VerifyBGPPeersHealth(AntaTest):
    """Verifies the health of BGP peers for given address families.

    This test performs the following checks for each specified address family:

      1. Validates that the VRF is configured.
      2. Checks if there are any peers for the given AFI/SAFI.
      3. For each relevant peer:
        - Verifies that the BGP session is `Established` and, if specified, has remained established for at least the duration given by `minimum_established_time`.
        - Confirms that the AFI/SAFI state is `negotiated`.
        - Checks that both input and output TCP message queues are empty.
          Can be disabled by setting `check_tcp_queues` to `False`.

    Expected Results
    ----------------
    * Success: If all checks pass for all specified address families and their peers.
    * Failure: If any of the following occur:
        - The specified VRF is not configured.
        - No peers are found for a given AFI/SAFI.
        - A peer's session state is not `Established` or if specified, has not remained established for at least the duration specified by
        the `minimum_established_time`.
        - The AFI/SAFI state is not 'negotiated' for any peer.
        - Any TCP message queue (input or output) is not empty when `check_tcp_queues` is `True` (default).

    Examples
    --------
    ```yaml
    anta.tests.routing:
      bgp:
        - VerifyBGPPeersHealth:
            minimum_established_time: 10000
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

        minimum_established_time: PositiveInt | None = None
        """Minimum established time (seconds) for all the BGP sessions."""
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
                    self.result.is_failure(f"{address_family} Peer: {peer['peerAddress']} - Incorrect session state - Expected: Established Actual: {peer['state']}")
                    continue

                if self.inputs.minimum_established_time and (act_time := peer["establishedTime"]) < self.inputs.minimum_established_time:
                    msg = f"BGP session not established for the minimum required duration - Expected: {self.inputs.minimum_established_time}s Actual: {act_time}s"
                    self.result.is_failure(f"{address_family} Peer: {peer['peerAddress']} - {msg}")

                # Check if the AFI/SAFI state is negotiated
                capability_status = get_value(peer, f"neighborCapabilities.multiprotocolCaps.{address_family.eos_key}")
                if not _check_bgp_neighbor_capability(capability_status):
                    self.result.is_failure(f"{address_family} Peer: {peer['peerAddress']} - AFI/SAFI state is not negotiated - {format_data(capability_status)}")

                # Check the TCP session message queues
                if address_family.check_tcp_queues:
                    inq = peer["peerTcpInfo"]["inputQueueLength"]
                    outq = peer["peerTcpInfo"]["outputQueueLength"]
                    if inq != 0 or outq != 0:
                        self.result.is_failure(f"{address_family} Peer: {peer['peerAddress']} - Session has non-empty message queues - InQ: {inq} OutQ: {outq}")


class VerifyBGPSpecificPeers(AntaTest):
    """Verifies the health of specific BGP peer(s) for given address families.

    This test performs the following checks for each specified address family and peer:

      1. Confirms that the specified VRF is configured.
      2. For each specified peer:
        - Verifies that the peer is found in the BGP configuration.
        - Verifies that the BGP session is `Established` and, if specified, has remained established for at least the duration given by `minimum_established_time`.
        - Confirms that the AFI/SAFI state is `negotiated`.
        - Ensures that both input and output TCP message queues are empty.
          Can be disabled by setting `check_tcp_queues` to `False`.

    Expected Results
    ----------------
    * Success: If all checks pass for all specified peers in all address families.
    * Failure: If any of the following occur:
        - The specified VRF is not configured.
        - A specified peer is not found in the BGP configuration.
        - A peer's session state is not `Established` or if specified, has not remained established for at least the duration specified by
        the `minimum_established_time`.
        - The AFI/SAFI state is not `negotiated` for a peer.
        - Any TCP message queue (input or output) is not empty for a peer when `check_tcp_queues` is `True` (default).

    Examples
    --------
    ```yaml
    anta.tests.routing:
      bgp:
        - VerifyBGPSpecificPeers:
            minimum_established_time: 10000
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

        minimum_established_time: PositiveInt | None = None
        """Minimum established time (seconds) for all the BGP sessions."""
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
                    self.result.is_failure(f"{address_family} Peer: {peer_ip} - Incorrect session state - Expected: Established Actual: {peer_data['state']}")
                    continue

                if self.inputs.minimum_established_time and (act_time := peer_data["establishedTime"]) < self.inputs.minimum_established_time:
                    msg = f"BGP session not established for the minimum required duration - Expected: {self.inputs.minimum_established_time}s Actual: {act_time}s"
                    self.result.is_failure(f"{address_family} Peer: {peer_ip} - {msg}")

                # Check if the AFI/SAFI state is negotiated
                capability_status = get_value(peer_data, f"neighborCapabilities.multiprotocolCaps.{address_family.eos_key}")
                if not capability_status:
                    self.result.is_failure(f"{address_family} Peer: {peer_ip} - AFI/SAFI state is not negotiated")

                if capability_status and not _check_bgp_neighbor_capability(capability_status):
                    self.result.is_failure(f"{address_family} Peer: {peer_ip} - AFI/SAFI state is not negotiated - {format_data(capability_status)}")

                # Check the TCP session message queues
                inq = peer_data["peerTcpInfo"]["inputQueueLength"]
                outq = peer_data["peerTcpInfo"]["outputQueueLength"]
                if address_family.check_tcp_queues and (inq != 0 or outq != 0):
                    self.result.is_failure(f"{address_family} Peer: {peer_ip} - Session has non-empty message queues - InQ: {inq} OutQ: {outq}")


class VerifyBGPPeerSession(AntaTest):
    """Verifies the session state of BGP peers.

    This test performs the following checks for each specified peer:

      1. Verifies that the peer is found in its VRF in the BGP configuration.
      2. Verifies that the BGP session is `Established` and, if specified, has remained established for at least the duration given by `minimum_established_time`.
      3. Ensures that both input and output TCP message queues are empty.
      Can be disabled by setting `check_tcp_queues` input flag to `False`.

    Expected Results
    ----------------
    * Success: If all of the following conditions are met:
        - All specified peers are found in the BGP configuration.
        - All peers sessions state are `Established` and, if specified, has remained established for at least the duration given by `minimum_established_time`.
        - All peers have empty TCP message queues if `check_tcp_queues` is `True` (default).
        - All peers are established for specified minimum duration.
    * Failure: If any of the following occur:
        - A specified peer is not found in the BGP configuration.
        - A peer's session state is not `Established` or if specified, has not remained established for at least the duration specified by
        the `minimum_established_time`.
        - A peer has non-empty TCP message queues (input or output) when `check_tcp_queues` is `True`.

    Examples
    --------
    ```yaml
    anta.tests.routing:
      bgp:
        - VerifyBGPPeerSession:
            minimum_established_time: 10000
            check_tcp_queues: false
            bgp_peers:
              - peer_address: 10.1.0.1
                vrf: default
              - peer_address: 10.1.0.2
                vrf: default
              - peer_address: 10.1.255.2
                vrf: DEV
              - peer_address: 10.1.255.4
                vrf: DEV
              - peer_address: fd00:dc:1::1
                vrf: default
              # RFC5549
              - interface: Ethernet1
                vrf: default
              - interface: Vlan3499
                vrf: PROD
    ```
    """

    categories: ClassVar[list[str]] = ["bgp"]
    commands: ClassVar[list[AntaCommand | AntaTemplate]] = [AntaCommand(command="show bgp neighbors vrf all", revision=3)]
    _atomic_support: ClassVar[bool] = True

    class Input(AntaTest.Input):
        """Input model for the VerifyBGPPeerSession test."""

        minimum_established_time: PositiveInt | None = None
        """Minimum established time (seconds) for all BGP sessions."""
        check_tcp_queues: bool = True
        """Flag to check if the TCP session queues are empty for all BGP peers."""
        bgp_peers: list[BgpPeer]
        """List of BGP peers."""

    @AntaTest.anta_test
    def test(self) -> None:
        """Main test function for VerifyBGPPeerSession."""
        output = self.instance_commands[0].json_output

        for peer in self.inputs.bgp_peers:
            # atomic result
            result = self.result.add(description=str(peer))
            result.is_success()

            # Check if the peer is found
            if (peer_data := _get_bgp_peer_data(peer, output)) is None:
                result.is_failure("Not found")
                continue

            # Check if the BGP session is established
            if peer_data["state"] != "Established":
                result.is_failure(f"Incorrect session state - Expected: Established Actual: {peer_data['state']}")
                continue

            if self.inputs.minimum_established_time and (act_time := peer_data["establishedTime"]) < self.inputs.minimum_established_time:
                result.is_failure(
                    f"BGP session not established for the minimum required duration - Expected: {self.inputs.minimum_established_time}s Actual: {act_time}s"
                )

            # Check the TCP session message queues
            if self.inputs.check_tcp_queues:
                inq = peer_data["peerTcpInfo"]["inputQueueLength"]
                outq = peer_data["peerTcpInfo"]["outputQueueLength"]
                if inq != 0 or outq != 0:
                    result.is_failure(f"Session has non-empty message queues - InQ: {inq} OutQ: {outq}")


class VerifyBGPExchangedRoutes(AntaTest):
    """Verifies the advertised and received routes of BGP IPv4 peer(s).

    This test performs the following checks for each advertised and received route for each peer:

      - Confirms that the route exists in the BGP route table.
      - If `check_active` input flag is True, verifies that the route is 'valid' and 'active'.
      - If `check_active` input flag is False, verifies that the route is 'valid'.

    Expected Results
    ----------------
    * Success: If all of the following conditions are met:
        - All specified advertised/received routes are found in the BGP route table.
        - All routes are 'active' and 'valid' or 'valid' only per the `check_active` input flag.
    * Failure: If any of the following occur:
        - An advertised/received route is not found in the BGP route table.
        - Any route is not 'active' and 'valid' or 'valid' only per `check_active` input flag.

    Examples
    --------
    ```yaml
    anta.tests.routing:
      bgp:
        - VerifyBGPExchangedRoutes:
            check_active: True
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
    ```
    """

    categories: ClassVar[list[str]] = ["bgp"]
    commands: ClassVar[list[AntaCommand | AntaTemplate]] = [
        AntaTemplate(template="show bgp neighbors {peer} advertised-routes vrf {vrf}", revision=3),
        AntaTemplate(template="show bgp neighbors {peer} routes vrf {vrf}", revision=3),
    ]

    class Input(AntaTest.Input):
        """Input model for the VerifyBGPExchangedRoutes test."""

        check_active: bool = True
        """Flag to check if the provided prefixes must be active and valid. If False, checks if the prefixes are valid only. """
        bgp_peers: list[BgpPeer]
        """List of BGP peers."""
        BgpNeighbor: ClassVar[type[BgpNeighbor]] = BgpNeighbor

        @field_validator("bgp_peers")
        @classmethod
        def validate_bgp_peers(cls, bgp_peers: list[BgpPeer]) -> list[BgpPeer]:
            """Validate that 'advertised_routes' or 'received_routes' field is provided in each BGP peer."""
            for peer in bgp_peers:
                if peer.advertised_routes is None and peer.received_routes is None:
                    msg = f"{peer} 'advertised_routes' or 'received_routes' field missing in the input"
                    raise ValueError(msg)
            return bgp_peers

    def render(self, template: AntaTemplate) -> list[AntaCommand]:
        """Render the template for each BGP peer in the input list."""
        return [template.render(peer=str(bgp_peer.peer_address), vrf=bgp_peer.vrf) for bgp_peer in self.inputs.bgp_peers]

    def _validate_bgp_route_paths(self, peer: str, route_type: str, route: str, entries: dict[str, Any], *, active_flag: bool = True) -> str | None:
        """Validate the BGP route paths."""
        # Check if the route is found
        if route in entries:
            # Check if the route is active and valid
            route_paths = entries[route]["bgpRoutePaths"][0]["routeType"]
            is_active = route_paths["active"]
            is_valid = route_paths["valid"]
            if active_flag:
                if not is_active or not is_valid:
                    return f"{peer} {route_type} route: {route} - Valid: {is_valid} Active: {is_active}"
            elif not is_valid:
                return f"{peer} {route_type} route: {route} - Valid: {is_valid}"
            return None

        return f"{peer} {route_type} route: {route} - Not found"

    @AntaTest.anta_test
    def test(self) -> None:
        """Main test function for VerifyBGPExchangedRoutes."""
        self.result.is_success()

        num_peers = len(self.inputs.bgp_peers)

        # Process each peer and its corresponding command pair
        for peer_idx, peer in enumerate(self.inputs.bgp_peers):
            # For n peers, advertised routes are at indices 0 to n-1, and received routes are at indices n to 2n-1
            advertised_routes_cmd = self.instance_commands[peer_idx]
            received_routes_cmd = self.instance_commands[peer_idx + num_peers]

            # Get the BGP route entries of each command
            command_output = {
                "Advertised": get_value(advertised_routes_cmd.json_output, f"vrfs.{peer.vrf}.bgpRouteEntries", default={}),
                "Received": get_value(received_routes_cmd.json_output, f"vrfs.{peer.vrf}.bgpRouteEntries", default={}),
            }

            # Validate both advertised and received routes
            for route_type, routes in zip(["Advertised", "Received"], [peer.advertised_routes, peer.received_routes], strict=False):
                # Skipping the validation for routes if user input is None
                if not routes:
                    continue

                entries = command_output[route_type]
                for route in routes:
                    # Check if the route is found. If yes then checks the route is active/valid
                    failure_msg = self._validate_bgp_route_paths(str(peer), route_type, str(route), entries, active_flag=self.inputs.check_active)
                    if failure_msg:
                        self.result.is_failure(failure_msg)


class VerifyBGPPeerMPCaps(AntaTest):
    """Verifies the multiprotocol capabilities of BGP peers.

    This test performs the following checks for each specified peer:

      1. Verifies that the peer is found in its VRF in the BGP configuration.
      2. For each specified capability:
        - Validates that the capability is present in the peer configuration.
        - Confirms that the capability is advertised, received, and enabled.
      3. When strict mode is enabled (`strict: true`):
        - Verifies that only the specified capabilities are configured.
        - Ensures an exact match between configured and expected capabilities.

    Expected Results
    ----------------
    * Success: If all of the following conditions are met:
        - All specified peers are found in the BGP configuration.
        - All specified capabilities are present and properly negotiated.
        - In strict mode, only the specified capabilities are configured.
    * Failure: If any of the following occur:
        - A specified peer is not found in the BGP configuration.
        - A specified capability is not found.
        - A capability is not properly negotiated (not advertised, received, or enabled).
        - In strict mode, additional or missing capabilities are detected.

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
                  - ipv4 labeled-Unicast
                  - ipv4MplsVpn
              - peer_address: fd00:dc:1::1
                vrf: default
                strict: False
                capabilities:
                  - ipv4 labeled-Unicast
                  - ipv4MplsVpn
              # RFC5549
              - interface: Ethernet1
                vrf: default
                strict: False
                capabilities:
                  - ipv4 labeled-Unicast
                  - ipv4MplsVpn
    ```
    """

    categories: ClassVar[list[str]] = ["bgp"]
    commands: ClassVar[list[AntaCommand | AntaTemplate]] = [AntaCommand(command="show bgp neighbors vrf all", revision=3)]

    class Input(AntaTest.Input):
        """Input model for the VerifyBGPPeerMPCaps test."""

        bgp_peers: list[BgpPeer]
        """List of BGP peers."""
        BgpPeer: ClassVar[type[BgpPeer]] = BgpPeer

        @field_validator("bgp_peers")
        @classmethod
        def validate_bgp_peers(cls, bgp_peers: list[T]) -> list[T]:
            """Validate that 'capabilities' field is provided in each BGP peer."""
            for peer in bgp_peers:
                if peer.capabilities is None:
                    msg = f"{peer} 'capabilities' field missing in the input"
                    raise ValueError(msg)
            return bgp_peers

    @AntaTest.anta_test
    def test(self) -> None:
        """Main test function for VerifyBGPPeerMPCaps."""
        self.result.is_success()

        output = self.instance_commands[0].json_output

        for peer in self.inputs.bgp_peers:
            # Check if the peer is found
            if (peer_data := _get_bgp_peer_data(peer, output)) is None:
                self.result.is_failure(f"{peer} - Not found")
                continue

            # Check if the multiprotocol capabilities are found
            if (act_mp_caps := get_value(peer_data, "neighborCapabilities.multiprotocolCaps")) is None:
                self.result.is_failure(f"{peer} - Multiprotocol capabilities not found")
                continue

            # If strict is True, check if only the specified capabilities are configured
            if peer.strict and sorted(peer.capabilities) != sorted(act_mp_caps):
                self.result.is_failure(f"{peer} - Mismatch - Expected: {', '.join(peer.capabilities)} Actual: {', '.join(act_mp_caps)}")
                continue

            # Check each capability
            for capability in peer.capabilities:
                # Check if the capability is found
                if (capability_status := get_value(act_mp_caps, capability)) is None:
                    self.result.is_failure(f"{peer} - {capability} not found")

                # Check if the capability is advertised, received, and enabled
                elif not _check_bgp_neighbor_capability(capability_status):
                    self.result.is_failure(f"{peer} - {capability} not negotiated - {format_data(capability_status)}")


class VerifyBGPPeerASNCap(AntaTest):
    """Verifies the four octet ASN capability of BGP peers.

    This test performs the following checks for each specified peer:

      1. Verifies that the peer is found in its VRF in the BGP configuration.
      2. Validates that the capability is present in the peer configuration.
      3. Confirms that the capability is advertised, received, and enabled.

    Expected Results
    ----------------
    * Success: If all of the following conditions are met:
        - All specified peers are found in the BGP configuration.
        - The four octet ASN capability is present in each peer configuration.
        - The capability is properly negotiated (advertised, received, and enabled) for all peers.
    * Failure: If any of the following occur:
        - A specified peer is not found in the BGP configuration.
        - The four octet ASN capability is not present for a peer.
        - The capability is not properly negotiated (not advertised, received, or enabled) for any peer.

    Examples
    --------
    ```yaml
    anta.tests.routing:
      bgp:
        - VerifyBGPPeerASNCap:
            bgp_peers:
              - peer_address: 172.30.11.1
                vrf: default
              - peer_address: fd00:dc:1::1
                vrf: default
              # RFC5549
              - interface: Ethernet1
                vrf: MGMT
    ```
    """

    categories: ClassVar[list[str]] = ["bgp"]
    commands: ClassVar[list[AntaCommand | AntaTemplate]] = [AntaCommand(command="show bgp neighbors vrf all", revision=3)]

    class Input(AntaTest.Input):
        """Input model for the VerifyBGPPeerASNCap test."""

        bgp_peers: list[BgpPeer]
        """List of BGP peers."""
        BgpPeer: ClassVar[type[BgpPeer]] = BgpPeer

    @AntaTest.anta_test
    def test(self) -> None:
        """Main test function for VerifyBGPPeerASNCap."""
        self.result.is_success()

        output = self.instance_commands[0].json_output

        for peer in self.inputs.bgp_peers:
            # Check if the peer is found
            if (peer_data := _get_bgp_peer_data(peer, output)) is None:
                self.result.is_failure(f"{peer} - Not found")
                continue

            # Check if the 4-octet ASN capability is found
            if (capablity_status := get_value(peer_data, "neighborCapabilities.fourOctetAsnCap")) is None:
                self.result.is_failure(f"{peer} - 4-octet ASN capability not found")
                continue

            # Check if the 4-octet ASN capability is advertised, received, and enabled
            if not _check_bgp_neighbor_capability(capablity_status):
                self.result.is_failure(f"{peer} - 4-octet ASN capability not negotiated - {format_data(capablity_status)}")


class VerifyBGPPeerRouteRefreshCap(AntaTest):
    """Verifies the route refresh capabilities of BGP peers.

    This test performs the following checks for each specified peer:

      1. Verifies that the peer is found in its VRF in the BGP configuration.
      2. Validates that the route refresh capability is present in the peer configuration.
      3. Confirms that the capability is advertised, received, and enabled.

    Expected Results
    ----------------
    * Success: If all of the following conditions are met:
        - All specified peers are found in the BGP configuration.
        - The route refresh capability is present in each peer configuration.
        - The capability is properly negotiated (advertised, received, and enabled) for all peers.
    * Failure: If any of the following occur:
        - A specified peer is not found in the BGP configuration.
        - The route refresh capability is not present for a peer.
        - The capability is not properly negotiated (not advertised, received, or enabled) for any peer.

    Examples
    --------
    ```yaml
    anta.tests.routing:
      bgp:
        - VerifyBGPPeerRouteRefreshCap:
            bgp_peers:
              - peer_address: 172.30.11.1
                vrf: default
              - peer_address: fd00:dc:1::1
                vrf: default
              # RFC5549
              - interface: Ethernet1
                vrf: MGMT
    ```
    """

    categories: ClassVar[list[str]] = ["bgp"]
    commands: ClassVar[list[AntaCommand | AntaTemplate]] = [AntaCommand(command="show bgp neighbors vrf all", revision=3)]

    class Input(AntaTest.Input):
        """Input model for the VerifyBGPPeerRouteRefreshCap test."""

        bgp_peers: list[BgpPeer]
        """List of BGP peers."""
        BgpPeer: ClassVar[type[BgpPeer]] = BgpPeer

    @AntaTest.anta_test
    def test(self) -> None:
        """Main test function for VerifyBGPPeerRouteRefreshCap."""
        self.result.is_success()

        output = self.instance_commands[0].json_output

        for peer in self.inputs.bgp_peers:
            # Check if the peer is found
            if (peer_data := _get_bgp_peer_data(peer, output)) is None:
                self.result.is_failure(f"{peer} - Not found")
                continue

            # Check if the route refresh capability is found
            if (capablity_status := get_value(peer_data, "neighborCapabilities.routeRefreshCap")) is None:
                self.result.is_failure(f"{peer} - Route refresh capability not found")
                continue

            # Check if the route refresh capability is advertised, received, and enabled
            if not _check_bgp_neighbor_capability(capablity_status):
                self.result.is_failure(f"{peer} - Route refresh capability not negotiated - {format_data(capablity_status)}")


class VerifyBGPPeerMD5Auth(AntaTest):
    """Verifies the MD5 authentication and state of BGP peers.

    This test performs the following checks for each specified peer:

      1. Verifies that the peer is found in its VRF in the BGP configuration.
      2. Validates that the BGP session is in `Established` state.
      3. Confirms that MD5 authentication is enabled for the peer.

    Expected Results
    ----------------
    * Success: If all of the following conditions are met:
        - All specified peers are found in the BGP configuration.
        - All peers are in `Established` state.
        - MD5 authentication is enabled for all peers.
    * Failure: If any of the following occur:
        - A specified peer is not found in the BGP configuration.
        - A peer's session state is not `Established`.
        - MD5 authentication is not enabled for a peer.

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
              - peer_address: fd00:dc:1::1
                vrf: default
              # RFC5549
              - interface: Ethernet1
                vrf: default
    ```
    """

    categories: ClassVar[list[str]] = ["bgp"]
    commands: ClassVar[list[AntaCommand | AntaTemplate]] = [AntaCommand(command="show bgp neighbors vrf all", revision=3)]

    class Input(AntaTest.Input):
        """Input model for the VerifyBGPPeerMD5Auth test."""

        bgp_peers: list[BgpPeer]
        """List of BGP peers."""
        BgpPeer: ClassVar[type[BgpPeer]] = BgpPeer

    @AntaTest.anta_test
    def test(self) -> None:
        """Main test function for VerifyBGPPeerMD5Auth."""
        self.result.is_success()

        output = self.instance_commands[0].json_output

        for peer in self.inputs.bgp_peers:
            # Check if the peer is found
            if (peer_data := _get_bgp_peer_data(peer, output)) is None:
                self.result.is_failure(f"{peer} - Not found")
                continue

            # Check BGP peer state and MD5 authentication
            state = peer_data.get("state")
            md5_auth_enabled = peer_data.get("md5AuthEnabled")
            if state != "Established":
                self.result.is_failure(f"{peer} - Incorrect session state - Expected: Established Actual: {state}")
            if not md5_auth_enabled:
                self.result.is_failure(f"{peer} - Session does not have MD5 authentication enabled")


class VerifyEVPNType2Route(AntaTest):
    """Verifies the EVPN Type-2 routes for a given IPv4 or MAC address and VNI.

    This test performs the following checks for each specified VXLAN endpoint:

      1. Verifies that the endpoint exists in the BGP EVPN table.
      2. Confirms that at least one EVPN Type-2 route with a valid and active path exists.

    Expected Results
    ----------------
    * Success: If all of the following conditions are met:
        - All specified VXLAN endpoints are found in the BGP EVPN table.
        - Each endpoint has at least one EVPN Type-2 route with a valid and active path.
    * Failure: If any of the following occur:
        - A VXLAN endpoint is not found in the BGP EVPN table.
        - No EVPN Type-2 route with a valid and active path exists for an endpoint.

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
        VxlanEndpoint: ClassVar[type[VxlanEndpoint]] = VxlanEndpoint

    def render(self, template: AntaTemplate) -> list[AntaCommand]:
        """Render the template for each VXLAN endpoint in the input list."""
        return [template.render(address=str(endpoint.address), vni=endpoint.vni) for endpoint in self.inputs.vxlan_endpoints]

    @AntaTest.anta_test
    def test(self) -> None:
        """Main test function for VerifyEVPNType2Route."""
        self.result.is_success()

        for command, endpoint in zip(self.instance_commands, self.inputs.vxlan_endpoints, strict=False):
            # Verify that the VXLAN endpoint is in the BGP EVPN table
            evpn_routes = command.json_output["evpnRoutes"]
            if not evpn_routes:
                self.result.is_failure(f"{endpoint} - No EVPN Type-2 route")
                continue

            # Verify that at least one EVPN Type-2 route has at least one active and valid path across all learned routes from all RDs combined
            has_active_path = False
            for route_data in evpn_routes.values():
                for path in route_data.get("evpnRoutePaths", []):
                    route_type = path.get("routeType", {})
                    if route_type.get("active") and route_type.get("valid"):
                        has_active_path = True
                        break
            if not has_active_path:
                self.result.is_failure(f"{endpoint} - No valid and active path")


class VerifyBGPAdvCommunities(AntaTest):
    """Verifies the advertised communities of BGP peers.

    This test performs the following checks for each specified peer:

      1. Verifies that the peer is found in its VRF in the BGP configuration.
      2. Validates that given community types are advertised. If not provided, validates that all communities (standard, extended, large) are advertised.

    Expected Results
    ----------------
    * Success: If all of the following conditions are met:
        - All specified peers are found in the BGP configuration.
        - Each peer advertises the given community types.
    * Failure: If any of the following occur:
        - A specified peer is not found in the BGP configuration.
        - A peer does not advertise any of the given community types.

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
                vrf: MGMT
                advertised_communities: ["standard", "extended"]
              - peer_address: fd00:dc:1::1
                vrf: default
              # RFC5549
              - interface: Ethernet1
                vrf: default
                advertised_communities: ["standard", "extended"]
    ```
    """

    categories: ClassVar[list[str]] = ["bgp"]
    commands: ClassVar[list[AntaCommand | AntaTemplate]] = [AntaCommand(command="show bgp neighbors vrf all", revision=3)]

    class Input(AntaTest.Input):
        """Input model for the VerifyBGPAdvCommunities test."""

        bgp_peers: list[BgpPeer]
        """List of BGP peers."""
        BgpPeer: ClassVar[type[BgpPeer]] = BgpPeer

    @AntaTest.anta_test
    def test(self) -> None:
        """Main test function for VerifyBGPAdvCommunities."""
        self.result.is_success()

        output = self.instance_commands[0].json_output

        for peer in self.inputs.bgp_peers:
            # Check if the peer is found
            if (peer_data := _get_bgp_peer_data(peer, output)) is None:
                self.result.is_failure(f"{peer} - Not found")
                continue

            # Check BGP peer advertised communities
            if not all(get_value(peer_data, f"advertisedCommunities.{community}") is True for community in peer.advertised_communities):
                self.result.is_failure(f"{peer} - {format_data(peer_data['advertisedCommunities'])}")


class VerifyBGPTimers(AntaTest):
    """Verifies the timers of BGP peers.

    This test performs the following checks for each specified peer:

      1. Verifies that the peer is found in its VRF in the BGP configuration.
      2. Confirms the BGP session hold time/keepalive timers match the expected value.

    Expected Results
    ----------------
    * Success: If all of the following conditions are met:
        - All specified peers are found in the BGP configuration.
        - The hold time/keepalive timers match the expected value for each peer.
    * Failure: If any of the following occur:
        - A specified peer is not found in the BGP configuration.
        - The hold time/keepalive timers do not match the expected value for a peer.

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
              - peer_address: fd00:dc:1::1
                vrf: default
                hold_time: 180
                keep_alive_time: 60
              # RFC5549
              - interface: Ethernet1
                vrf: MGMT
                hold_time: 180
                keep_alive_time: 60
    ```
    """

    categories: ClassVar[list[str]] = ["bgp"]
    commands: ClassVar[list[AntaCommand | AntaTemplate]] = [AntaCommand(command="show bgp neighbors vrf all", revision=3)]

    class Input(AntaTest.Input):
        """Input model for the VerifyBGPTimers test."""

        bgp_peers: list[BgpPeer]
        """List of BGP peers."""
        BgpPeer: ClassVar[type[BgpPeer]] = BgpPeer

        @field_validator("bgp_peers")
        @classmethod
        def validate_bgp_peers(cls, bgp_peers: list[T]) -> list[T]:
            """Validate that 'hold_time' or 'keep_alive_time'  field is provided in each BGP peer."""
            for peer in bgp_peers:
                if peer.hold_time is None or peer.keep_alive_time is None:
                    msg = f"{peer} 'hold_time' or 'keep_alive_time' field missing in the input"
                    raise ValueError(msg)
            return bgp_peers

    @AntaTest.anta_test
    def test(self) -> None:
        """Main test function for VerifyBGPTimers."""
        self.result.is_success()

        output = self.instance_commands[0].json_output

        for peer in self.inputs.bgp_peers:
            # Check if the peer is found
            if (peer_data := _get_bgp_peer_data(peer, output)) is None:
                self.result.is_failure(f"{peer} - Not found")
                continue

            # Check BGP peer timers
            if peer_data["holdTime"] != peer.hold_time:
                self.result.is_failure(f"{peer} - Hold time mismatch - Expected: {peer.hold_time} Actual: {peer_data['holdTime']}")
            if peer_data["keepaliveTime"] != peer.keep_alive_time:
                self.result.is_failure(f"{peer} - Keepalive time mismatch - Expected: {peer.keep_alive_time} Actual: {peer_data['keepaliveTime']}")


class VerifyBGPPeerDropStats(AntaTest):
    """Verifies BGP NLRI drop statistics of BGP peers.

    This test performs the following checks for each specified peer:

      1. Verifies that the peer is found in its VRF in the BGP configuration.
      2. Validates the BGP drop statistics:
        - If specific drop statistics are provided, checks only those counters.
        - If no specific drop statistics are provided, checks all available counters.
        - Confirms that all checked counters have a value of zero.

    Expected Results
    ----------------
    * Success: If all of the following conditions are met:
        - All specified peers are found in the BGP configuration.
        - All specified drop statistics counters (or all counters if none specified) are zero.
    * Failure: If any of the following occur:
        - A specified peer is not found in the BGP configuration.
        - Any checked drop statistics counter has a non-zero value.
        - A specified drop statistics counter does not exist.

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
              - peer_address: fd00:dc:1::1
                vrf: default
                drop_stats:
                  - inDropAsloop
                  - prefixEvpnDroppedUnsupportedRouteType
              # RFC5549
              - interface: Ethernet1
                vrf: MGMT
                drop_stats:
                  - inDropAsloop
                  - prefixEvpnDroppedUnsupportedRouteType
    ```
    """

    categories: ClassVar[list[str]] = ["bgp"]
    commands: ClassVar[list[AntaCommand | AntaTemplate]] = [AntaCommand(command="show bgp neighbors vrf all", revision=3)]

    class Input(AntaTest.Input):
        """Input model for the VerifyBGPPeerDropStats test."""

        bgp_peers: list[BgpPeer]
        """List of BGP peers."""
        BgpPeer: ClassVar[type[BgpPeer]] = BgpPeer

    @AntaTest.anta_test
    def test(self) -> None:
        """Main test function for VerifyBGPPeerDropStats."""
        self.result.is_success()

        output = self.instance_commands[0].json_output

        for peer in self.inputs.bgp_peers:
            drop_stats_input = peer.drop_stats
            # Check if the peer is found
            if (peer_data := _get_bgp_peer_data(peer, output)) is None:
                self.result.is_failure(f"{peer} - Not found")
                continue

            # Verify BGP peers' drop stats
            drop_stats_output = peer_data["dropStats"]

            # In case drop stats not provided, It will check all drop statistics
            if not drop_stats_input:
                drop_stats_input = drop_stats_output

            # Verify BGP peer's drop stats
            for drop_stat in drop_stats_input:
                if (stat_value := drop_stats_output.get(drop_stat, 0)) != 0:
                    self.result.is_failure(f"{peer} - Non-zero NLRI drop statistics counter - {drop_stat}: {stat_value}")


class VerifyBGPPeerUpdateErrors(AntaTest):
    """Verifies BGP update error counters of BGP peers.

    This test performs the following checks for each specified peer:

      1. Verifies that the peer is found in its VRF in the BGP configuration.
      2. Validates the BGP update error counters:
        - If specific update error counters are provided, checks only those counters.
        - If no update error counters are provided, checks all available counters.
        - Confirms that all checked counters have a value of zero.

    Note: For "disabledAfiSafi" error counter field, checking that it's not "None" versus 0.

    Expected Results
    ----------------
    * Success: If all of the following conditions are met:
        - All specified peers are found in the BGP configuration.
        - All specified update error counters (or all counters if none specified) are zero.
    * Failure: If any of the following occur:
        - A specified peer is not found in the BGP configuration.
        - Any checked update error counters has a non-zero value.
        - A specified update error counters does not exist.

    Examples
    --------
    ```yaml
    anta.tests.routing:
      bgp:
        - VerifyBGPPeerUpdateErrors:
            bgp_peers:
              - peer_address: 172.30.11.1
                vrf: default
                update_errors:
                  - inUpdErrWithdraw
              - peer_address: fd00:dc:1::1
                vrf: default
                update_errors:
                  - inUpdErrWithdraw
              # RFC5549
              - interface: Ethernet1
                vrf: MGMT
                update_errors:
                  - inUpdErrWithdraw
    ```
    """

    categories: ClassVar[list[str]] = ["bgp"]
    commands: ClassVar[list[AntaCommand | AntaTemplate]] = [AntaCommand(command="show bgp neighbors vrf all", revision=3)]

    class Input(AntaTest.Input):
        """Input model for the VerifyBGPPeerUpdateErrors test."""

        bgp_peers: list[BgpPeer]
        """List of BGP peers."""
        BgpPeer: ClassVar[type[BgpPeer]] = BgpPeer

    @AntaTest.anta_test
    def test(self) -> None:
        """Main test function for VerifyBGPPeerUpdateErrors."""
        self.result.is_success()

        output = self.instance_commands[0].json_output

        for peer in self.inputs.bgp_peers:
            update_errors_input = peer.update_errors
            # Check if the peer is found
            if (peer_data := _get_bgp_peer_data(peer, output)) is None:
                self.result.is_failure(f"{peer} - Not found")
                continue

            # Getting the BGP peer's error counters output.
            error_counters_output = peer_data.get("peerInUpdateErrors", {})

            # In case update error counters not provided, It will check all the update error counters.
            if not update_errors_input:
                update_errors_input = error_counters_output

            # Verify BGP peer's update error counters
            for error_counter in update_errors_input:
                if (stat_value := error_counters_output.get(error_counter, "Not Found")) != 0 and stat_value != "None":
                    self.result.is_failure(f"{peer} - Non-zero update error counter - {error_counter}: {stat_value}")


class VerifyBgpRouteMaps(AntaTest):
    """Verifies BGP inbound and outbound route-maps of BGP peers.

    This test performs the following checks for each specified peer:

      1. Verifies that the peer is found in its VRF in the BGP configuration.
      2. Validates the correct BGP route maps are applied in the correct direction (inbound or outbound).

    Expected Results
    ----------------
    * Success: If all of the following conditions are met:
        - All specified peers are found in the BGP configuration.
        - All specified peers has correct BGP route maps are applied in the correct direction (inbound or outbound).
    * Failure: If any of the following occur:
        - A specified peer is not found in the BGP configuration.
        - A incorrect or missing route map in either the inbound or outbound direction.

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
              - peer_address: fd00:dc:1::1
                vrf: default
                inbound_route_map: RM-MLAG-PEER-IN
                outbound_route_map: RM-MLAG-PEER-OUT
              # RFC5549
              - interface: Ethernet1
                vrf: MGMT
                inbound_route_map: RM-MLAG-PEER-IN
                outbound_route_map: RM-MLAG-PEER-OUT
    ```
    """

    categories: ClassVar[list[str]] = ["bgp"]
    commands: ClassVar[list[AntaCommand | AntaTemplate]] = [AntaCommand(command="show bgp neighbors vrf all", revision=3)]

    class Input(AntaTest.Input):
        """Input model for the VerifyBgpRouteMaps test."""

        bgp_peers: list[BgpPeer]
        """List of BGP peers."""
        BgpPeer: ClassVar[type[BgpPeer]] = BgpPeer

        @field_validator("bgp_peers")
        @classmethod
        def validate_bgp_peers(cls, bgp_peers: list[T]) -> list[T]:
            """Validate that 'inbound_route_map' or 'outbound_route_map' field is provided in each BGP peer."""
            for peer in bgp_peers:
                if not (peer.inbound_route_map or peer.outbound_route_map):
                    msg = f"{peer} 'inbound_route_map' or 'outbound_route_map' field missing in the input"
                    raise ValueError(msg)
            return bgp_peers

    @AntaTest.anta_test
    def test(self) -> None:
        """Main test function for VerifyBgpRouteMaps."""
        self.result.is_success()

        output = self.instance_commands[0].json_output

        for peer in self.inputs.bgp_peers:
            inbound_route_map = peer.inbound_route_map
            outbound_route_map = peer.outbound_route_map

            # Check if the peer is found
            if (peer_data := _get_bgp_peer_data(peer, output)) is None:
                self.result.is_failure(f"{peer} - Not found")
                continue

            # Verify Inbound route-map
            if inbound_route_map and (inbound_map := peer_data.get("routeMapInbound", "Not Configured")) != inbound_route_map:
                self.result.is_failure(f"{peer} - Inbound route-map mismatch - Expected: {inbound_route_map} Actual: {inbound_map}")

            # Verify Outbound route-map
            if outbound_route_map and (outbound_map := peer_data.get("routeMapOutbound", "Not Configured")) != outbound_route_map:
                self.result.is_failure(f"{peer} - Outbound route-map mismatch - Expected: {outbound_route_map} Actual: {outbound_map}")


class VerifyBGPPeerRouteLimit(AntaTest):
    """Verifies maximum routes and warning limit for BGP peers.

    This test performs the following checks for each specified peer:

      1. Verifies that the peer is found in its VRF in the BGP configuration.
      2. Confirms the maximum routes and maximum routes warning limit, if provided, match the expected value.

    Expected Results
    ----------------
    * Success: If all of the following conditions are met:
        - All specified peers are found in the BGP configuration.
        - The maximum routes/maximum routes warning limit match the expected value for a peer.
    * Failure: If any of the following occur:
        - A specified peer is not found in the BGP configuration.
        - The maximum routes/maximum routes warning limit do not match the expected value for a peer.

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
              - peer_address: fd00:dc:1::1
                vrf: default
                maximum_routes: 12000
                warning_limit: 10000
              # RFC5549
              - interface: Ethernet1
                vrf: MGMT
                maximum_routes: 12000
                warning_limit: 10000
    ```
    """

    categories: ClassVar[list[str]] = ["bgp"]
    commands: ClassVar[list[AntaCommand | AntaTemplate]] = [AntaCommand(command="show bgp neighbors vrf all", revision=3)]

    class Input(AntaTest.Input):
        """Input model for the VerifyBGPPeerRouteLimit test."""

        bgp_peers: list[BgpPeer]
        """List of BGP peers."""
        BgpPeer: ClassVar[type[BgpPeer]] = BgpPeer

        @field_validator("bgp_peers")
        @classmethod
        def validate_bgp_peers(cls, bgp_peers: list[T]) -> list[T]:
            """Validate that 'maximum_routes' field is provided in each BGP peer."""
            for peer in bgp_peers:
                if peer.maximum_routes is None:
                    msg = f"{peer} 'maximum_routes' field missing in the input"
                    raise ValueError(msg)
            return bgp_peers

    @AntaTest.anta_test
    def test(self) -> None:
        """Main test function for VerifyBGPPeerRouteLimit."""
        self.result.is_success()

        output = self.instance_commands[0].json_output

        for peer in self.inputs.bgp_peers:
            maximum_routes = peer.maximum_routes
            warning_limit = peer.warning_limit

            # Check if the peer is found
            if (peer_data := _get_bgp_peer_data(peer, output)) is None:
                self.result.is_failure(f"{peer} - Not found")
                continue

            # Verify maximum routes
            if (actual_maximum_routes := peer_data.get("maxTotalRoutes", "Not Found")) != maximum_routes:
                self.result.is_failure(f"{peer} - Maximum routes mismatch - Expected: {maximum_routes} Actual: {actual_maximum_routes}")

            # Verify warning limit if provided. By default, EOS does not have a warning limit and `totalRoutesWarnLimit` is not present in the output.
            if warning_limit is not None and (actual_warning_limit := peer_data.get("totalRoutesWarnLimit", 0)) != warning_limit:
                self.result.is_failure(f"{peer} - Maximum routes warning limit mismatch - Expected: {warning_limit} Actual: {actual_warning_limit}")


class VerifyBGPPeerGroup(AntaTest):
    """Verifies BGP peer group of BGP peers.

    This test performs the following checks for each specified peer:

      1. Verifies that the peer is found in its VRF in the BGP configuration.
      2. Confirms the peer group is correctly assigned to the specified BGP peer.

    Expected Results
    ----------------
    * Success: If all of the following conditions are met:
        - All specified peers are found in the BGP configuration.
        - The peer group is correctly assigned to the specified BGP peer.
    * Failure: If any of the following occur:
        - A specified peer is not found in the BGP configuration.
        - The peer group is not correctly assigned to the specified BGP peer.

    Examples
    --------
    ```yaml
    anta.tests.routing:
      bgp:
        - VerifyBGPPeerGroup:
            bgp_peers:
              - peer_address: 172.30.11.1
                vrf: default
                peer_group: IPv4-UNDERLAY-PEERS
              - peer_address: fd00:dc:1::1
                vrf: default
                peer_group: IPv4-UNDERLAY-PEERS
              # RFC5549
              - interface: Ethernet1
                vrf: MGMT
                peer_group: IPv4-UNDERLAY-PEERS
    ```
    """

    categories: ClassVar[list[str]] = ["bgp"]
    commands: ClassVar[list[AntaCommand | AntaTemplate]] = [AntaCommand(command="show bgp neighbors vrf all", revision=3)]

    class Input(AntaTest.Input):
        """Input model for the VerifyBGPPeerGroup test."""

        bgp_peers: list[BgpPeer]
        """List of BGP peers."""

        @field_validator("bgp_peers")
        @classmethod
        def validate_bgp_peers(cls, bgp_peers: list[BgpPeer]) -> list[BgpPeer]:
            """Validate that 'peer_group' field is provided in each BGP peer."""
            for peer in bgp_peers:
                if peer.peer_group is None:
                    msg = f"{peer} 'peer_group' field missing in the input"
                    raise ValueError(msg)
            return bgp_peers

    @AntaTest.anta_test
    def test(self) -> None:
        """Main test function for VerifyBGPPeerGroup."""
        self.result.is_success()

        output = self.instance_commands[0].json_output

        for peer in self.inputs.bgp_peers:
            # Check if the peer is found
            if (peer_data := _get_bgp_peer_data(peer, output)) is None:
                self.result.is_failure(f"{peer} - Not found")
                continue

            if (actual_peer_group := peer_data.get("peerGroupName", "Not Found")) != peer.peer_group:
                self.result.is_failure(f"{peer} - Incorrect peer group configured - Expected: {peer.peer_group} Actual: {actual_peer_group}")


class VerifyBGPPeerSessionRibd(AntaTest):
    """Verifies the session state of BGP peers.

    Compatible with EOS operating in `ribd` routing protocol model.

    This test performs the following checks for each specified peer:

      1. Verifies that the peer is found in its VRF in the BGP configuration.
      2. Verifies that the BGP session is `Established` and, if specified, has remained established for at least the duration given by `minimum_established_time`.
      3. Ensures that both input and output TCP message queues are empty.
      Can be disabled by setting `check_tcp_queues` input flag to `False`.

    Expected Results
    ----------------
    * Success: If all of the following conditions are met:
        - All specified peers are found in the BGP configuration.
        - All peers sessions state are `Established` and, if specified, has remained established for at least the duration given by `minimum_established_time`.
        - All peers have empty TCP message queues if `check_tcp_queues` is `True` (default).
        - All peers are established for specified minimum duration.
    * Failure: If any of the following occur:
        - A specified peer is not found in the BGP configuration.
        - A peer's session state is not `Established` or if specified, has not remained established for at least the duration specified by
        the `minimum_established_time`.
        - A peer has non-empty TCP message queues (input or output) when `check_tcp_queues` is `True`.

    Examples
    --------
    ```yaml
    anta.tests.routing:
      bgp:
        - VerifyBGPPeerSessionRibd:
            minimum_established_time: 10000
            check_tcp_queues: false
            bgp_peers:
              - peer_address: 10.1.0.1
                vrf: default
              - peer_address: 10.1.255.4
                vrf: DEV
              - peer_address: fd00:dc:1::1
                vrf: default
              # RFC5549
              - interface: Ethernet1
                vrf: MGMT
    ```
    """

    categories: ClassVar[list[str]] = ["bgp"]
    commands: ClassVar[list[AntaCommand | AntaTemplate]] = [AntaCommand(command="show ip bgp neighbors vrf all", revision=2)]

    class Input(AntaTest.Input):
        """Input model for the VerifyBGPPeerSessionRibd test."""

        minimum_established_time: PositiveInt | None = None
        """Minimum established time (seconds) for all the BGP sessions."""
        check_tcp_queues: bool = True
        """Flag to check if the TCP session queues are empty for all BGP peers. Defaults to `True`."""
        bgp_peers: list[BgpPeer]
        """List of BGP peers."""

    @AntaTest.anta_test
    def test(self) -> None:
        """Main test function for VerifyBGPPeerSessionRibd."""
        self.result.is_success()

        output = self.instance_commands[0].json_output

        for peer in self.inputs.bgp_peers:
            # Check if the peer is found
            if (peer_data := _get_bgp_peer_data(peer, output)) is None:
                self.result.is_failure(f"{peer} - Not found")
                continue

            # Check if the BGP session is established
            if peer_data["state"] != "Established":
                self.result.is_failure(f"{peer} - Incorrect session state - Expected: Established Actual: {peer_data['state']}")
                continue

            if self.inputs.minimum_established_time and (act_time := peer_data["establishedTime"]) < self.inputs.minimum_established_time:
                self.result.is_failure(
                    f"{peer} - BGP session not established for the minimum required duration - Expected: {self.inputs.minimum_established_time}s Actual: {act_time}s"
                )

            # Check the TCP session message queues
            if self.inputs.check_tcp_queues:
                inq_stat = peer_data["peerTcpInfo"]["inputQueueLength"]
                outq_stat = peer_data["peerTcpInfo"]["outputQueueLength"]
                if inq_stat != 0 or outq_stat != 0:
                    self.result.is_failure(f"{peer} - Session has non-empty message queues - InQ: {inq_stat} OutQ: {outq_stat}")


class VerifyBGPPeersHealthRibd(AntaTest):
    """Verifies the health of all the BGP peers.

    Compatible with EOS operating in `ribd` routing protocol model.

    This test performs the following checks for all BGP IPv4 peers:

      1. Verifies that the BGP session is in the `Established` state.
      2. Checks that both input and output TCP message queues are empty.
      Can be disabled by setting `check_tcp_queues` input flag to `False`.

    Expected Results
    ----------------
    * Success: If all checks pass for all BGP IPv4 peers.
    * Failure: If any of the following occur:
        - Any BGP session is not in the `Established` state.
        - Any TCP message queue (input or output) is not empty when `check_tcp_queues` is `True` (default).

    Examples
    --------
    ```yaml
    anta.tests.routing:
      bgp:
        - VerifyBGPPeersHealthRibd:
            check_tcp_queues: True
    ```
    """

    categories: ClassVar[list[str]] = ["bgp"]
    commands: ClassVar[list[AntaCommand | AntaTemplate]] = [AntaCommand(command="show ip bgp neighbors vrf all", revision=2)]

    class Input(AntaTest.Input):
        """Input model for the VerifyBGPPeersHealthRibd test."""

        check_tcp_queues: bool = True
        """Flag to check if the TCP session queues are empty for all BGP peers. Defaults to `True`."""

    @AntaTest.anta_test
    def test(self) -> None:
        """Main test function for VerifyBGPPeersHealthRibd."""
        self.result.is_success()

        output = self.instance_commands[0].json_output

        for vrf, vrf_data in output["vrfs"].items():
            peer_list = vrf_data.get("peerList", [])

            for peer in peer_list:
                # Check if the BGP session is established
                if peer["state"] != "Established":
                    self.result.is_failure(f"Peer: {peer['peerAddress']} VRF: {vrf} - Incorrect session state - Expected: Established Actual: {peer['state']}")
                    continue

                # Check the TCP session message queues
                inq = peer["peerTcpInfo"]["inputQueueLength"]
                outq = peer["peerTcpInfo"]["outputQueueLength"]
                if self.inputs.check_tcp_queues and (inq != 0 or outq != 0):
                    self.result.is_failure(f"Peer: {peer['peerAddress']} VRF: {vrf} - Session has non-empty message queues - InQ: {inq} OutQ: {outq}")


class VerifyBGPNlriAcceptance(AntaTest):
    """Verifies that all received NLRI are accepted for all AFI/SAFI configured for BGP peers.

    This test performs the following checks for each specified peer:

      1. Verifies that the peer is found in its VRF in the BGP configuration.
      2. Verifies that all received NLRI were accepted by comparing `nlrisReceived` with `nlrisAccepted`.

    Expected Results
    ----------------
    * Success: If `nlrisReceived` equals `nlrisAccepted`, indicating all NLRI were accepted.
    * Failure: If any of the following occur:
        - The specified VRF is not configured.
        - `nlrisReceived` does not equal `nlrisAccepted`, indicating some NLRI were rejected or filtered.

    Examples
    --------
    ```yaml
    anta.tests.routing:
      bgp:
        - VerifyBGPNlriAcceptance:
            bgp_peers:
              - peer_address: 10.100.0.128
                vrf: default
                capabilities:
                  - ipv4Unicast
              - peer_address: 2001:db8:1::2
                vrf: default
                capabilities:
                  - ipv6Unicast
              - peer_address: fe80::2%Et1
                vrf: default
                capabilities:
                  - ipv6Unicast
              # RFC 5549
              - peer_address: fe80::2%Et1
                vrf: default
                capabilities:
                  - ipv6Unicast
    ```
    """

    categories: ClassVar[list[str]] = ["bgp"]
    commands: ClassVar[list[AntaCommand | AntaTemplate]] = [
        AntaCommand(command="show bgp summary vrf all", revision=1),
        AntaCommand(command="show bgp neighbors vrf all", revision=3),
    ]

    class Input(AntaTest.Input):
        """Input model for the VerifyBGPNlriAcceptance test."""

        bgp_peers: list[BgpPeer]
        """List of BGP IPv4 peers."""

        @field_validator("bgp_peers")
        @classmethod
        def validate_bgp_peers(cls, bgp_peers: list[T]) -> list[T]:
            """Validate that 'capabilities' field is provided in each BGP peer."""
            for peer in bgp_peers:
                if peer.capabilities is None:
                    msg = f"{peer} 'capabilities' field missing in the input"
                    raise ValueError(msg)
            return bgp_peers

    @staticmethod
    def _get_peer_address(peer: BgpPeer, command_output: dict[str, Any]) -> str | None:
        """Retrieve the peer address for the given BGP peer data.

        If an interface is specified, the address is extracted from the command output;
        otherwise, it is retrieved directly from the peer object.

        Parameters
        ----------
        peer
            The BGP peer object to look up.
        command_output
            Parsed output from the relevant command.

        Returns
        -------
        str | None
            The peer address if found, otherwise None.
        """
        if peer.interface is not None:
            # RFC5549
            interface = str(peer.interface)
            lookup_key = "ifName"

            peer_list = get_value(command_output, f"vrfs.{peer.vrf}.peerList", default=[])
            # Check if the peer is found
            if (peer_details := get_item(peer_list, lookup_key, interface)) is not None:
                return str(peer_details.get("peerAddress"))
            return None

        return str(peer.peer_address)

    @AntaTest.anta_test
    def test(self) -> None:
        """Main test function for VerifyBGPNlriAcceptance."""
        self.result.is_success()

        output = self.instance_commands[0].json_output
        peer_output = self.instance_commands[1].json_output

        for peer in self.inputs.bgp_peers:
            identity = self._get_peer_address(peer, peer_output)
            # Check if the peer is found
            if not (peer_data := get_value(output, f"vrfs..{peer.vrf}..peers..{identity}", separator="..")):
                self.result.is_failure(f"{peer} - Not found")
                continue

            # Fetching the multiprotocol capabilities
            for capability in peer.capabilities:
                # Check if the capability is found
                if (capability_status := get_value(peer_data, capability)) is None:
                    self.result.is_failure(f"{peer} - {capability} not found")
                    continue

                if capability_status["afiSafiState"] != "negotiated":
                    self.result.is_failure(f"{peer} - {capability} not negotiated")

                if (received := capability_status.get("nlrisReceived")) != (accepted := capability_status.get("nlrisAccepted")):
                    self.result.is_failure(f"{peer} AFI/SAFI: {capability} - Some NLRI were filtered or rejected - Accepted: {accepted} Received: {received}")


class VerifyBGPRoutePaths(AntaTest):
    """Verifies BGP IPv4 route paths.

    This test performs the following checks for each specified BGP route entry:

      1. Verifies the specified BGP route exists in the routing table.
      2. For each expected paths:
          - Verifies a path with matching next-hop exists.
          - Verifies the path's origin attribute matches the expected value.

    Expected Results
    ----------------
    * Success: The test will pass if all specified routes exist with paths matching the expected next-hops and origin attributes.
    * Failure: The test will fail if:
        - A specified BGP route is not found.
        - A path with specified next-hop is not found.
        - A path's origin attribute doesn't match the expected value.

    Examples
    --------
    ```yaml
    anta.tests.routing:
      bgp:
        - VerifyBGPRoutePaths:
            route_entries:
                - prefix: 10.100.0.128/31
                  vrf: default
                  paths:
                    - nexthop: 10.100.0.10
                      origin: Igp
                    - nexthop: 10.100.4.5
                      origin: Incomplete
    ```
    """

    categories: ClassVar[list[str]] = ["bgp"]
    commands: ClassVar[list[AntaCommand | AntaTemplate]] = [AntaCommand(command="show ip bgp vrf all", revision=3)]

    class Input(AntaTest.Input):
        """Input model for the VerifyBGPRoutePaths test."""

        route_entries: list[BgpRoute]
        """List of BGP IPv4 route(s)."""

        @field_validator("route_entries")
        @classmethod
        def validate_route_entries(cls, route_entries: list[BgpRoute]) -> list[BgpRoute]:
            """Validate that 'paths' field is provided in each BGP route."""
            for route in route_entries:
                if route.paths is None:
                    msg = f"{route} 'paths' field missing in the input"
                    raise ValueError(msg)
            return route_entries

    @AntaTest.anta_test
    def test(self) -> None:
        """Main test function for VerifyBGPRoutePaths."""
        self.result.is_success()

        for route in self.inputs.route_entries:
            # Verify if the prefix exists in BGP table
            if not (bgp_routes := get_value(self.instance_commands[0].json_output, f"vrfs..{route.vrf}..bgpRouteEntries..{route.prefix}", separator="..")):
                self.result.is_failure(f"{route} - Prefix not found")
                continue

            # Iterating over each path.
            for path in route.paths:
                nexthop = str(path.nexthop)
                origin = path.origin
                if not (route_path := get_item(bgp_routes["bgpRoutePaths"], "nextHop", nexthop)):
                    self.result.is_failure(f"{route} {path} - Path not found")
                    continue

                if (actual_origin := get_value(route_path, "routeType.origin")) != origin:
                    self.result.is_failure(f"{route} {path} - Origin mismatch - Actual: {actual_origin}")


class VerifyBGPRouteECMP(AntaTest):
    """Verifies BGP IPv4 route ECMP paths.

    This test performs the following checks for each specified BGP route entry:

      1. Route exists in BGP table.
      2. First path is a valid and active ECMP head.
      3. Correct number of valid ECMP contributors follow the head path.
      4. Route is installed in RIB with same amount of next-hops.

    Expected Results
    ----------------
    * Success: The test will pass if all specified routes exist in both BGP and RIB tables with correct amount of ECMP paths.
    * Failure: The test will fail if:
        - A specified route is not found in BGP table.
        - A valid and active ECMP head is not found.
        - ECMP contributors count does not match the expected value.
        - Route is not installed in RIB table.
        - BGP and RIB nexthops count do not match.

    Examples
    --------
    ```yaml
    anta.tests.routing:
      bgp:
        - VerifyBGPRouteECMP:
            route_entries:
                - prefix: 10.100.0.128/31
                  vrf: default
                  ecmp_count: 2
    ```
    """

    categories: ClassVar[list[str]] = ["bgp"]
    commands: ClassVar[list[AntaCommand | AntaTemplate]] = [
        AntaCommand(command="show ip bgp vrf all", revision=3),
        AntaCommand(command="show ip route vrf all bgp", revision=4),
    ]

    class Input(AntaTest.Input):
        """Input model for the VerifyBGPRouteECMP test."""

        route_entries: list[BgpRoute]
        """List of BGP IPv4 route(s)."""

        @field_validator("route_entries")
        @classmethod
        def validate_route_entries(cls, route_entries: list[BgpRoute]) -> list[BgpRoute]:
            """Validate that 'ecmp_count' field is provided in each BGP route."""
            for route in route_entries:
                if route.ecmp_count is None:
                    msg = f"{route} 'ecmp_count' field missing in the input"
                    raise ValueError(msg)
            return route_entries

    @AntaTest.anta_test
    def test(self) -> None:
        """Main test function for VerifyBGPRouteECMP."""
        self.result.is_success()

        for route in self.inputs.route_entries:
            # Verify if the prefix exists in BGP table.
            if not (bgp_route_entry := get_value(self.instance_commands[0].json_output, f"vrfs..{route.vrf}..bgpRouteEntries..{route.prefix}", separator="..")):
                self.result.is_failure(f"{route} - Prefix not found in BGP table")
                continue

            route_paths = iter(bgp_route_entry["bgpRoutePaths"])
            head = next(route_paths, None)
            # Verify if the active ECMP head exists.
            if head is None or not all(head["routeType"][key] for key in ["valid", "active", "ecmpHead"]):
                self.result.is_failure(f"{route} - Valid and active ECMP head not found")
                continue

            bgp_nexthops = {head["nextHop"]}
            bgp_nexthops.update([path["nextHop"] for path in route_paths if all(path["routeType"][key] for key in ["valid", "ecmp", "ecmpContributor"])])

            # Verify ECMP count is correct.
            if len(bgp_nexthops) != route.ecmp_count:
                self.result.is_failure(f"{route} - ECMP count mismatch - Expected: {route.ecmp_count} Actual: {len(bgp_nexthops)}")
                continue

            # Verify if the prefix exists in routing table.
            if not (route_entry := get_value(self.instance_commands[1].json_output, f"vrfs..{route.vrf}..routes..{route.prefix}", separator="..")):
                self.result.is_failure(f"{route} - Prefix not found in routing table")
                continue

            # Verify BGP and RIB nexthops are same.
            if len(bgp_nexthops) != len(route_entry["vias"]):
                self.result.is_failure(f"{route} - Nexthops count mismatch - BGP: {len(bgp_nexthops)} RIB: {len(route_entry['vias'])}")


class VerifyBGPRedistribution(AntaTest):
    """Verifies BGP redistribution.

    This test performs the following checks for each specified VRF in the BGP instance:

      1. Ensures that the expected address-family is configured on the device.
      2. Confirms that the redistributed route protocol, include leaked and route map match the expected values.


    Expected Results
    ----------------
    * Success: If all of the following conditions are met:
        - The expected address-family is configured on the device.
        - The redistributed route protocol, include leaked and route map align with the expected values for the route.
    * Failure: If any of the following occur:
        - The expected address-family is not configured on device.
        - The redistributed route protocol, include leaked or route map does not match the expected values.

    Examples
    --------
    ```yaml
    anta.tests.routing:
      bgp:
        - VerifyBGPRedistribution:
            vrfs:
              - vrf: default
                address_families:
                  - afi_safi: ipv4multicast
                    redistributed_routes:
                      - proto: Connected
                        include_leaked: True
                        route_map: RM-CONN-2-BGP
                      - proto: IS-IS
                        include_leaked: True
                        route_map: RM-CONN-2-BGP
                  - afi_safi: IPv6 Unicast
                    redistributed_routes:
                      - proto: User # Converted to EOS SDK
                        route_map: RM-CONN-2-BGP
                      - proto: Static
                        include_leaked: True
                        route_map: RM-CONN-2-BGP
    ```
    """

    categories: ClassVar[list[str]] = ["bgp"]
    commands: ClassVar[list[AntaCommand | AntaTemplate]] = [AntaCommand(command="show bgp instance vrf all", revision=4)]

    class Input(AntaTest.Input):
        """Input model for the VerifyBGPRedistribution test."""

        vrfs: list[BgpVrf]
        """List of VRFs in the BGP instance."""

    def _validate_redistribute_route(self, vrf_data: str, addr_family: str, afi_safi_configs: list[dict[str, Any]], route_info: dict[str, Any]) -> list[Any]:
        """Validate the redstributed route details for a given address family."""
        failure_msg = []
        # If the redistributed route protocol does not match the expected value, test fails.
        if not (actual_route := get_item(afi_safi_configs.get("redistributedRoutes"), "proto", route_info.proto)):
            failure_msg.append(f"{vrf_data}, {addr_family}, Proto: {route_info.proto} - Not configured")
            return failure_msg

        # If includes leaked field applicable, and it does not matches the expected value, test fails.
        if (act_include_leaked := actual_route.get("includeLeaked", False)) != route_info.include_leaked:
            failure_msg.append(f"{vrf_data}, {addr_family}, {route_info} - Include leaked mismatch - Actual: {act_include_leaked}")

        # If route map is required and it is not matching the expected value, test fails.
        if all([route_info.route_map, (act_route_map := actual_route.get("routeMap", "Not Found")) != route_info.route_map]):
            failure_msg.append(f"{vrf_data}, {addr_family}, {route_info} - Route map mismatch - Actual: {act_route_map}")
        return failure_msg

    @AntaTest.anta_test
    def test(self) -> None:
        """Main test function for VerifyBGPRedistribution."""
        self.result.is_success()
        command_output = self.instance_commands[0].json_output

        for vrf_data in self.inputs.vrfs:
            # If the specified VRF details are not found, test fails.
            if not (instance_details := get_value(command_output, f"vrfs.{vrf_data.vrf}")):
                self.result.is_failure(f"{vrf_data} - Not configured")
                continue
            for address_family in vrf_data.address_families:
                # If the AFI-SAFI configuration details are not found, test fails.
                if not (afi_safi_configs := get_value(instance_details, f"afiSafiConfig.{address_family.afi_safi}")):
                    self.result.is_failure(f"{vrf_data}, {address_family} - Not redistributed")
                    continue

                for route_info in address_family.redistributed_routes:
                    failure_msg = self._validate_redistribute_route(str(vrf_data), str(address_family), afi_safi_configs, route_info)
                    for msg in failure_msg:
                        self.result.is_failure(msg)


class VerifyBGPPeerTtlMultiHops(AntaTest):
    """Verifies BGP TTL and max-ttl-hops count for BGP peers.

    This test performs the following checks for each specified BGP peer:

      1. Verifies the specified BGP peer exists in the BGP configuration.
      2. Verifies the TTL and max-ttl-hops attribute matches the expected value.

    Expected Results
    ----------------
    * Success: The test will pass if all specified peers exist with TTL and max-ttl-hops attributes matching the expected values.
    * Failure: If any of the following occur:
        - A specified BGP peer is not found.
        - A TTL or max-ttl-hops attribute doesn't match the expected value for any peer.

    Examples
    --------
    ```yaml
    anta.tests.routing:
      bgp:
        - VerifyBGPPeerTtlMultiHops:
            bgp_peers:
                - peer_address: 172.30.11.1
                  vrf: default
                  ttl: 3
                  max_ttl_hops: 3
                - peer_address: 172.30.11.2
                  vrf: test
                  ttl: 30
                  max_ttl_hops: 30
                - peer_address: fd00:dc:1::1
                  vrf: default
                  ttl: 30
                  max_ttl_hops: 30
                # RFC5549
                - interface: Ethernet1
                  vrf: MGMT
                  ttl: 30
                  max_ttl_hops: 30
    ```
    """

    categories: ClassVar[list[str]] = ["bgp"]
    commands: ClassVar[list[AntaCommand | AntaTemplate]] = [AntaCommand(command="show ip bgp neighbors vrf all", revision=2)]

    class Input(AntaTest.Input):
        """Input model for the VerifyBGPPeerTtlMultiHops test."""

        bgp_peers: list[BgpPeer]
        """List of peer(s)."""

        @field_validator("bgp_peers")
        @classmethod
        def validate_bgp_peers(cls, bgp_peers: list[BgpPeer]) -> list[BgpPeer]:
            """Validate that 'ttl' and 'max_ttl_hops' field is provided in each BGP peer."""
            for peer in bgp_peers:
                if peer.ttl is None:
                    msg = f"{peer} 'ttl' field missing in the input"
                    raise ValueError(msg)
                if peer.max_ttl_hops is None:
                    msg = f"{peer} 'max_ttl_hops' field missing in the input"
                    raise ValueError(msg)

            return bgp_peers

    @AntaTest.anta_test
    def test(self) -> None:
        """Main test function for VerifyBGPPeerTtlMultiHops."""
        self.result.is_success()
        command_output = self.instance_commands[0].json_output

        for peer in self.inputs.bgp_peers:
            # Check if the peer is found
            if (peer_details := _get_bgp_peer_data(peer, command_output)) is None:
                self.result.is_failure(f"{peer} - Not found")
                continue

            # Verify if the TTL duration matches the expected value.
            if peer_details.get("ttl") != peer.ttl:
                self.result.is_failure(f"{peer} - TTL mismatch - Expected: {peer.ttl} Actual: {peer_details.get('ttl')}")

            # Verify if the max-ttl-hops time matches the expected value.
            if peer_details.get("maxTtlHops") != peer.max_ttl_hops:
                self.result.is_failure(f"{peer} - Max TTL Hops mismatch - Expected: {peer.max_ttl_hops} Actual: {peer_details.get('maxTtlHops')}")
