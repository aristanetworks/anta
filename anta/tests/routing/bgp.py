# Copyright (c) 2023-2025 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Module related to BGP tests."""

# Mypy does not understand AntaTest.Input typing
# mypy: disable-error-code=attr-defined
from __future__ import annotations

from typing import ClassVar, TypeVar

from pydantic import field_validator

from anta.input_models.routing.bgp import BgpAddressFamily, BgpAfi, BgpNeighbor, BgpPeer, VxlanEndpoint
from anta.models import AntaCommand, AntaTemplate, AntaTest
from anta.tools import format_data, get_item, get_value

# Using a TypeVar for the BgpPeer model since mypy thinks it's a ClassVar and not a valid type when used in field validators
T = TypeVar("T", bound=BgpPeer)


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


class VerifyBGPPeerSession(AntaTest):
    """Verifies the session state of BGP IPv4 peer(s).

    This test performs the following checks for each specified peer:

      1. Verifies that the peer is found in its VRF in the BGP configuration.
      2. Checks that the BGP session is in the `Established` state.
      3. Ensures that both input and output TCP message queues are empty.
      Can be disabled by setting `check_tcp_queues` global flag to `False`.

    Expected Results
    ----------------
    * Success: If all of the following conditions are met:
        - All specified peers are found in the BGP configuration.
        - All peers sessions state are `Established`.
        - All peers have empty TCP message queues if `check_tcp_queues` is `True` (default).
    * Failure: If any of the following occur:
        - A specified peer is not found in the BGP configuration.
        - A peer's session state is not `Established`.
        - A peer has non-empty TCP message queues (input or output) when `check_tcp_queues` is `True`.

    Examples
    --------
    ```yaml
    anta.tests.routing:
      bgp:
        - VerifyBGPPeerSession:
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
    ```
    """

    categories: ClassVar[list[str]] = ["bgp"]
    commands: ClassVar[list[AntaCommand | AntaTemplate]] = [AntaCommand(command="show bgp neighbors vrf all", revision=3)]

    class Input(AntaTest.Input):
        """Input model for the VerifyBGPPeerSession test."""

        check_tcp_queues: bool = True
        """Flag to check if the TCP session queues are empty for all BGP peers. Defaults to `True`."""
        bgp_peers: list[BgpPeer]
        """List of BGP IPv4 peers."""

    @AntaTest.anta_test
    def test(self) -> None:
        """Main test function for VerifyBGPPeerSession."""
        self.result.is_success()

        output = self.instance_commands[0].json_output

        for peer in self.inputs.bgp_peers:
            peer_ip = str(peer.peer_address)
            peer_list = get_value(output, f"vrfs.{peer.vrf}.peerList", default=[])

            # Check if the peer is found
            if (peer_data := get_item(peer_list, "peerAddress", peer_ip)) is None:
                self.result.is_failure(f"{peer} - Not found")
                continue

            # Check if the BGP session is established
            if peer_data["state"] != "Established":
                self.result.is_failure(f"{peer} - Session state is not established - State: {peer_data['state']}")
                continue

            # Check the TCP session message queues
            if self.inputs.check_tcp_queues:
                inq = peer_data["peerTcpInfo"]["inputQueueLength"]
                outq = peer_data["peerTcpInfo"]["outputQueueLength"]
                if inq != 0 or outq != 0:
                    self.result.is_failure(f"{peer} - Session has non-empty message queues - InQ: {inq}, OutQ: {outq}")


class VerifyBGPExchangedRoutes(AntaTest):
    """Verifies the advertised and received routes of BGP IPv4 peer(s).

    This test performs the following checks for each specified peer:

      For each advertised and received route:
        - Confirms that the route exists in the BGP route table.
        - Verifies that the route is in an 'active' and 'valid' state.

    Expected Results
    ----------------
    * Success: If all of the following conditions are met:
        - All specified advertised/received routes are found in the BGP route table.
        - All routes are in both 'active' and 'valid' states.
    * Failure: If any of the following occur:
        - An advertised/received route is not found in the BGP route table.
        - Any route is not in an 'active' or 'valid' state.

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

        bgp_peers: list[BgpPeer]
        """List of BGP IPv4 peers."""
        BgpNeighbor: ClassVar[type[BgpNeighbor]] = BgpNeighbor

        @field_validator("bgp_peers")
        @classmethod
        def validate_bgp_peers(cls, bgp_peers: list[BgpPeer]) -> list[BgpPeer]:
            """Validate that 'advertised_routes' or 'received_routes' field is provided in each BGP peer."""
            for peer in bgp_peers:
                if peer.advertised_routes is None or peer.received_routes is None:
                    msg = f"{peer} 'advertised_routes' or 'received_routes' field missing in the input"
                    raise ValueError(msg)
            return bgp_peers

    def render(self, template: AntaTemplate) -> list[AntaCommand]:
        """Render the template for each BGP peer in the input list."""
        return [template.render(peer=str(bgp_peer.peer_address), vrf=bgp_peer.vrf) for bgp_peer in self.inputs.bgp_peers]

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
            for route_type, routes in zip(["Advertised", "Received"], [peer.advertised_routes, peer.received_routes]):
                entries = command_output[route_type]
                for route in routes:
                    # Check if the route is found
                    if str(route) not in entries:
                        self.result.is_failure(f"{peer} {route_type} route: {route} - Not found")
                        continue

                    # Check if the route is active and valid
                    route_paths = entries[str(route)]["bgpRoutePaths"][0]["routeType"]
                    is_active = route_paths["active"]
                    is_valid = route_paths["valid"]
                    if not is_active or not is_valid:
                        self.result.is_failure(f"{peer} {route_type} route: {route} - Valid: {is_valid}, Active: {is_active}")


class VerifyBGPPeerMPCaps(AntaTest):
    """Verifies the multiprotocol capabilities of BGP IPv4 peer(s).

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
                  - ipv4Unicast
    ```
    """

    categories: ClassVar[list[str]] = ["bgp"]
    commands: ClassVar[list[AntaCommand | AntaTemplate]] = [AntaCommand(command="show bgp neighbors vrf all", revision=3)]

    class Input(AntaTest.Input):
        """Input model for the VerifyBGPPeerMPCaps test."""

        bgp_peers: list[BgpPeer]
        """List of BGP IPv4 peers."""
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
            peer_ip = str(peer.peer_address)
            peer_list = get_value(output, f"vrfs.{peer.vrf}.peerList", default=[])

            # Check if the peer is found
            if (peer_data := get_item(peer_list, "peerAddress", peer_ip)) is None:
                self.result.is_failure(f"{peer} - Not found")
                continue

            # Fetching the multiprotocol capabilities
            act_mp_caps = get_value(peer_data, "neighborCapabilities.multiprotocolCaps")

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
    """Verifies the four octet ASN capability of BGP IPv4 peer(s).

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
    ```
    """

    categories: ClassVar[list[str]] = ["bgp"]
    commands: ClassVar[list[AntaCommand | AntaTemplate]] = [AntaCommand(command="show bgp neighbors vrf all", revision=3)]

    class Input(AntaTest.Input):
        """Input model for the VerifyBGPPeerASNCap test."""

        bgp_peers: list[BgpPeer]
        """List of BGP IPv4 peers."""
        BgpPeer: ClassVar[type[BgpPeer]] = BgpPeer

    @AntaTest.anta_test
    def test(self) -> None:
        """Main test function for VerifyBGPPeerASNCap."""
        self.result.is_success()

        output = self.instance_commands[0].json_output

        for peer in self.inputs.bgp_peers:
            peer_ip = str(peer.peer_address)
            peer_list = get_value(output, f"vrfs.{peer.vrf}.peerList", default=[])

            # Check if the peer is found
            if (peer_data := get_item(peer_list, "peerAddress", peer_ip)) is None:
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
    """Verifies the route refresh capabilities of IPv4 BGP peer(s) in a specified VRF.

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
    ```
    """

    categories: ClassVar[list[str]] = ["bgp"]
    commands: ClassVar[list[AntaCommand | AntaTemplate]] = [AntaCommand(command="show bgp neighbors vrf all", revision=3)]

    class Input(AntaTest.Input):
        """Input model for the VerifyBGPPeerRouteRefreshCap test."""

        bgp_peers: list[BgpPeer]
        """List of BGP IPv4 peers."""
        BgpPeer: ClassVar[type[BgpPeer]] = BgpPeer

    @AntaTest.anta_test
    def test(self) -> None:
        """Main test function for VerifyBGPPeerRouteRefreshCap."""
        self.result.is_success()

        output = self.instance_commands[0].json_output

        for peer in self.inputs.bgp_peers:
            peer_ip = str(peer.peer_address)
            peer_list = get_value(output, f"vrfs.{peer.vrf}.peerList", default=[])

            # Check if the peer is found
            if (peer_data := get_item(peer_list, "peerAddress", peer_ip)) is None:
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
    """Verifies the MD5 authentication and state of IPv4 BGP peer(s) in a specified VRF.

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
    ```
    """

    categories: ClassVar[list[str]] = ["bgp"]
    commands: ClassVar[list[AntaCommand | AntaTemplate]] = [AntaCommand(command="show bgp neighbors vrf all", revision=3)]

    class Input(AntaTest.Input):
        """Input model for the VerifyBGPPeerMD5Auth test."""

        bgp_peers: list[BgpPeer]
        """List of IPv4 BGP peers."""
        BgpPeer: ClassVar[type[BgpPeer]] = BgpPeer

    @AntaTest.anta_test
    def test(self) -> None:
        """Main test function for VerifyBGPPeerMD5Auth."""
        self.result.is_success()

        output = self.instance_commands[0].json_output

        for peer in self.inputs.bgp_peers:
            peer_ip = str(peer.peer_address)
            peer_list = get_value(output, f"vrfs.{peer.vrf}.peerList", default=[])

            # Check if the peer is found
            if (peer_data := get_item(peer_list, "peerAddress", peer_ip)) is None:
                self.result.is_failure(f"{peer} - Not found")
                continue

            # Check BGP peer state and MD5 authentication
            state = peer_data.get("state")
            md5_auth_enabled = peer_data.get("md5AuthEnabled")
            if state != "Established":
                self.result.is_failure(f"{peer} - Session state is not established - State: {state}")
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

        for command, endpoint in zip(self.instance_commands, self.inputs.vxlan_endpoints):
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
    """Verifies that advertised communities are standard, extended and large for BGP IPv4 peer(s).

    This test performs the following checks for each specified peer:

      1. Verifies that the peer is found in its VRF in the BGP configuration.
      2. Validates that all required community types are advertised:
        - Standard communities
        - Extended communities
        - Large communities

    Expected Results
    ----------------
    * Success: If all of the following conditions are met:
        - All specified peers are found in the BGP configuration.
        - Each peer advertises standard, extended and large communities.
    * Failure: If any of the following occur:
        - A specified peer is not found in the BGP configuration.
        - A peer does not advertise standard, extended or large communities.

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

    categories: ClassVar[list[str]] = ["bgp"]
    commands: ClassVar[list[AntaCommand | AntaTemplate]] = [AntaCommand(command="show bgp neighbors vrf all", revision=3)]

    class Input(AntaTest.Input):
        """Input model for the VerifyBGPAdvCommunities test."""

        bgp_peers: list[BgpPeer]
        """List of BGP IPv4 peers."""
        BgpPeer: ClassVar[type[BgpPeer]] = BgpPeer

    @AntaTest.anta_test
    def test(self) -> None:
        """Main test function for VerifyBGPAdvCommunities."""
        self.result.is_success()

        output = self.instance_commands[0].json_output

        for peer in self.inputs.bgp_peers:
            peer_ip = str(peer.peer_address)
            peer_list = get_value(output, f"vrfs.{peer.vrf}.peerList", default=[])

            # Check if the peer is found
            if (peer_data := get_item(peer_list, "peerAddress", peer_ip)) is None:
                self.result.is_failure(f"{peer} - Not found")
                continue

            # Check BGP peer advertised communities
            if not all(get_value(peer_data, f"advertisedCommunities.{community}") is True for community in ["standard", "extended", "large"]):
                self.result.is_failure(f"{peer} - {format_data(peer_data['advertisedCommunities'])}")


class VerifyBGPTimers(AntaTest):
    """Verifies the timers of BGP IPv4 peer(s).

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
    ```
    """

    categories: ClassVar[list[str]] = ["bgp"]
    commands: ClassVar[list[AntaCommand | AntaTemplate]] = [AntaCommand(command="show bgp neighbors vrf all", revision=3)]

    class Input(AntaTest.Input):
        """Input model for the VerifyBGPTimers test."""

        bgp_peers: list[BgpPeer]
        """List of BGP IPv4 peers."""
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
            peer_ip = str(peer.peer_address)
            peer_list = get_value(output, f"vrfs.{peer.vrf}.peerList", default=[])

            # Check if the peer is found
            if (peer_data := get_item(peer_list, "peerAddress", peer_ip)) is None:
                self.result.is_failure(f"{peer} - Not found")
                continue

            # Check BGP peer timers
            if peer_data["holdTime"] != peer.hold_time:
                self.result.is_failure(f"{peer} - Hold time mismatch - Expected: {peer.hold_time}, Actual: {peer_data['holdTime']}")
            if peer_data["keepaliveTime"] != peer.keep_alive_time:
                self.result.is_failure(f"{peer} - Keepalive time mismatch - Expected: {peer.keep_alive_time}, Actual: {peer_data['keepaliveTime']}")


class VerifyBGPPeerDropStats(AntaTest):
    """Verifies BGP NLRI drop statistics for the provided BGP IPv4 peer(s).

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
    ```
    """

    categories: ClassVar[list[str]] = ["bgp"]
    commands: ClassVar[list[AntaCommand | AntaTemplate]] = [AntaCommand(command="show bgp neighbors vrf all", revision=3)]

    class Input(AntaTest.Input):
        """Input model for the VerifyBGPPeerDropStats test."""

        bgp_peers: list[BgpPeer]
        """List of BGP IPv4 peers."""
        BgpPeer: ClassVar[type[BgpPeer]] = BgpPeer

    @AntaTest.anta_test
    def test(self) -> None:
        """Main test function for VerifyBGPPeerDropStats."""
        self.result.is_success()

        output = self.instance_commands[0].json_output

        for peer in self.inputs.bgp_peers:
            peer_ip = str(peer.peer_address)
            drop_stats_input = peer.drop_stats
            peer_list = get_value(output, f"vrfs.{peer.vrf}.peerList", default=[])

            # Check if the peer is found
            if (peer_data := get_item(peer_list, "peerAddress", peer_ip)) is None:
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
    """Verifies BGP update error counters for the provided BGP IPv4 peer(s).

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
    ```
    """

    categories: ClassVar[list[str]] = ["bgp"]
    commands: ClassVar[list[AntaCommand | AntaTemplate]] = [AntaCommand(command="show bgp neighbors vrf all", revision=3)]

    class Input(AntaTest.Input):
        """Input model for the VerifyBGPPeerUpdateErrors test."""

        bgp_peers: list[BgpPeer]
        """List of BGP IPv4 peers."""
        BgpPeer: ClassVar[type[BgpPeer]] = BgpPeer

    @AntaTest.anta_test
    def test(self) -> None:
        """Main test function for VerifyBGPPeerUpdateErrors."""
        self.result.is_success()

        output = self.instance_commands[0].json_output

        for peer in self.inputs.bgp_peers:
            peer_ip = str(peer.peer_address)
            update_errors_input = peer.update_errors
            peer_list = get_value(output, f"vrfs.{peer.vrf}.peerList", default=[])

            # Check if the peer is found
            if (peer_data := get_item(peer_list, "peerAddress", peer_ip)) is None:
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
    """Verifies BGP inbound and outbound route-maps of BGP IPv4 peer(s).

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
    ```
    """

    categories: ClassVar[list[str]] = ["bgp"]
    commands: ClassVar[list[AntaCommand | AntaTemplate]] = [AntaCommand(command="show bgp neighbors vrf all", revision=3)]

    class Input(AntaTest.Input):
        """Input model for the VerifyBgpRouteMaps test."""

        bgp_peers: list[BgpPeer]
        """List of BGP IPv4 peers."""
        BgpPeer: ClassVar[type[BgpPeer]] = BgpPeer

        @field_validator("bgp_peers")
        @classmethod
        def validate_bgp_peers(cls, bgp_peers: list[T]) -> list[T]:
            """Validate that 'inbound_route_map' or 'outbound_route_map' field is provided in each BGP peer."""
            for peer in bgp_peers:
                if not (peer.inbound_route_map or peer.outbound_route_map):
                    msg = f"{peer}; At least one of 'inbound_route_map' or 'outbound_route_map' must be provided."
                    raise ValueError(msg)
            return bgp_peers

    @AntaTest.anta_test
    def test(self) -> None:
        """Main test function for VerifyBgpRouteMaps."""
        self.result.is_success()

        output = self.instance_commands[0].json_output

        for peer in self.inputs.bgp_peers:
            peer_ip = str(peer.peer_address)
            inbound_route_map = peer.inbound_route_map
            outbound_route_map = peer.outbound_route_map
            peer_list = get_value(output, f"vrfs.{peer.vrf}.peerList", default=[])

            # Check if the peer is found
            if (peer_data := get_item(peer_list, "peerAddress", peer_ip)) is None:
                self.result.is_failure(f"{peer} - Not found")
                continue

            # Verify Inbound route-map
            if inbound_route_map and (inbound_map := peer_data.get("routeMapInbound", "Not Configured")) != inbound_route_map:
                self.result.is_failure(f"{peer} - Inbound route-map mismatch - Expected: {inbound_route_map}, Actual: {inbound_map}")

            # Verify Outbound route-map
            if outbound_route_map and (outbound_map := peer_data.get("routeMapOutbound", "Not Configured")) != outbound_route_map:
                self.result.is_failure(f"{peer} - Outbound route-map mismatch - Expected: {outbound_route_map}, Actual: {outbound_map}")


class VerifyBGPPeerRouteLimit(AntaTest):
    """Verifies maximum routes and warning limit for BGP IPv4 peer(s).

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
    ```
    """

    categories: ClassVar[list[str]] = ["bgp"]
    commands: ClassVar[list[AntaCommand | AntaTemplate]] = [AntaCommand(command="show bgp neighbors vrf all", revision=3)]

    class Input(AntaTest.Input):
        """Input model for the VerifyBGPPeerRouteLimit test."""

        bgp_peers: list[BgpPeer]
        """List of BGP IPv4 peers."""
        BgpPeer: ClassVar[type[BgpPeer]] = BgpPeer

        @field_validator("bgp_peers")
        @classmethod
        def validate_bgp_peers(cls, bgp_peers: list[T]) -> list[T]:
            """Validate that 'maximum_routes' field is provided in each BGP peer."""
            for peer in bgp_peers:
                if peer.maximum_routes is None:
                    msg = f"{peer}; 'maximum_routes' field missing in the input"
                    raise ValueError(msg)
            return bgp_peers

    @AntaTest.anta_test
    def test(self) -> None:
        """Main test function for VerifyBGPPeerRouteLimit."""
        self.result.is_success()

        output = self.instance_commands[0].json_output

        for peer in self.inputs.bgp_peers:
            peer_ip = str(peer.peer_address)
            maximum_routes = peer.maximum_routes
            warning_limit = peer.warning_limit
            peer_list = get_value(output, f"vrfs.{peer.vrf}.peerList", default=[])

            # Check if the peer is found
            if (peer_data := get_item(peer_list, "peerAddress", peer_ip)) is None:
                self.result.is_failure(f"{peer} - Not found")
                continue

            # Verify maximum routes
            if (actual_maximum_routes := peer_data.get("maxTotalRoutes", "Not Found")) != maximum_routes:
                self.result.is_failure(f"{peer} - Maximum routes mismatch - Expected: {maximum_routes}, Actual: {actual_maximum_routes}")

            # Verify warning limit if provided. By default, EOS does not have a warning limit and `totalRoutesWarnLimit` is not present in the output.
            if warning_limit is not None and (actual_warning_limit := peer_data.get("totalRoutesWarnLimit", 0)) != warning_limit:
                self.result.is_failure(f"{peer} - Maximum routes warning limit mismatch - Expected: {warning_limit}, Actual: {actual_warning_limit}")
