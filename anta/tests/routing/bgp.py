# Copyright (c) 2023-2024 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Module related to BGP tests."""

# Mypy does not understand AntaTest.Input typing
# mypy: disable-error-code=attr-defined
from __future__ import annotations

from ipaddress import IPv4Address, IPv4Network, IPv6Address
from typing import TYPE_CHECKING, Any, ClassVar

from pydantic import BaseModel, Field, PositiveInt, model_validator
from pydantic.v1.utils import deep_update
from pydantic_extra_types.mac_address import MacAddress

from anta.custom_types import Afi, BgpDropStats, BgpUpdateError, MultiProtocolCaps, Safi, Vni
from anta.models import AntaCommand, AntaTemplate, AntaTest
from anta.tools import get_item, get_value

if TYPE_CHECKING:
    import sys

    if sys.version_info >= (3, 11):
        from typing import Self
    else:
        from typing_extensions import Self


def _add_bgp_failures(failures: dict[tuple[str, str | None], dict[str, Any]], afi: Afi, safi: Safi | None, vrf: str, issue: str | dict[str, Any]) -> None:
    """Add a BGP failure entry to the given `failures` dictionary.

    Note: This function modifies `failures` in-place.

    Parameters
    ----------
    failures
        The dictionary to which the failure will be added.
    afi
        The address family identifier.
    vrf
        The VRF name.
    safi
        The subsequent address family identifier.
    issue
        A description of the issue. Can be of any type.

    Example
    -------
    The `failures` dictionary will have the following structure:
    ```
    {
        ('afi1', 'safi1'): {
            'afi': 'afi1',
            'safi': 'safi1',
            'vrfs': {
                'vrf1': issue1,
                'vrf2': issue2
            }
        },
        ('afi2', None): {
            'afi': 'afi2',
            'vrfs': {
                'vrf1': issue3
            }
        }
    }
    ```

    """
    key = (afi, safi)

    failure_entry = failures.setdefault(key, {"afi": afi, "safi": safi, "vrfs": {}}) if safi else failures.setdefault(key, {"afi": afi, "vrfs": {}})

    failure_entry["vrfs"][vrf] = issue


def _check_peer_issues(peer_data: dict[str, Any] | None) -> dict[str, Any]:
    """Check for issues in BGP peer data.

    Parameters
    ----------
    peer_data
        The BGP peer data dictionary nested in the `show bgp <afi> <safi> summary` command.

    Returns
    -------
    dict
        Dictionary with keys indicating issues or an empty dictionary if no issues.

    Raises
    ------
    ValueError
        If any of the required keys ("peerState", "inMsgQueue", "outMsgQueue") are missing in `peer_data`, i.e. invalid BGP peer data.

    Example
    -------
    This can for instance return
    ```
    {"peerNotFound": True}
    {"peerState": "Idle", "inMsgQueue": 2, "outMsgQueue": 0}
    {}
    ```

    """
    if peer_data is None:
        return {"peerNotFound": True}

    if any(key not in peer_data for key in ["peerState", "inMsgQueue", "outMsgQueue"]):
        msg = "Provided BGP peer data is invalid."
        raise ValueError(msg)

    if peer_data["peerState"] != "Established" or peer_data["inMsgQueue"] != 0 or peer_data["outMsgQueue"] != 0:
        return {"peerState": peer_data["peerState"], "inMsgQueue": peer_data["inMsgQueue"], "outMsgQueue": peer_data["outMsgQueue"]}

    return {}


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


class VerifyBGPPeerCount(AntaTest):
    """Verifies the count of BGP peers for a given address family.

    It supports multiple types of Address Families Identifiers (AFI) and Subsequent Address Family Identifiers (SAFI).

    For SR-TE SAFI, the EOS command supports sr-te first then ipv4/ipv6 (AFI) which is handled automatically in this test.

    Please refer to the Input class attributes below for details.

    Expected Results
    ----------------
    * Success: If the count of BGP peers matches the expected count for each address family and VRF.
    * Failure: If the count of BGP peers does not match the expected count, or if BGP is not configured for an expected VRF or address family.

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

    name = "VerifyBGPPeerCount"
    description = "Verifies the count of BGP peers."
    categories: ClassVar[list[str]] = ["bgp"]
    commands: ClassVar[list[AntaCommand | AntaTemplate]] = [
        AntaTemplate(template="show bgp {afi} {safi} summary vrf {vrf}", revision=3),
        AntaTemplate(template="show bgp {afi} summary", revision=3),
    ]

    class Input(AntaTest.Input):
        """Input model for the VerifyBGPPeerCount test."""

        address_families: list[BgpAfi]
        """List of BGP address families (BgpAfi)."""

        class BgpAfi(BaseModel):
            """Model for a BGP address family (AFI) and subsequent address family (SAFI)."""

            afi: Afi
            """BGP address family (AFI)."""
            safi: Safi | None = None
            """Optional BGP subsequent service family (SAFI).

            If the input `afi` is `ipv4` or `ipv6`, a valid `safi` must be provided.
            """
            vrf: str = "default"
            """
            Optional VRF for IPv4 and IPv6. If not provided, it defaults to `default`.

            If the input `afi` is not `ipv4` or `ipv6`, e.g. `evpn`, `vrf` must be `default`.
            """
            num_peers: PositiveInt
            """Number of expected BGP peer(s)."""

            @model_validator(mode="after")
            def validate_inputs(self) -> Self:
                """Validate the inputs provided to the BgpAfi class.

                If afi is either ipv4 or ipv6, safi must be provided.

                If afi is not ipv4 or ipv6, safi must not be provided and vrf must be default.
                """
                if self.afi in ["ipv4", "ipv6"]:
                    if self.safi is None:
                        msg = "'safi' must be provided when afi is ipv4 or ipv6"
                        raise ValueError(msg)
                elif self.safi is not None:
                    msg = "'safi' must not be provided when afi is not ipv4 or ipv6"
                    raise ValueError(msg)
                elif self.vrf != "default":
                    msg = "'vrf' must be default when afi is not ipv4 or ipv6"
                    raise ValueError(msg)
                return self

    def render(self, template: AntaTemplate) -> list[AntaCommand]:
        """Render the template for each BGP address family in the input list."""
        commands = []
        for afi in self.inputs.address_families:
            if template == VerifyBGPPeerCount.commands[0] and afi.afi in ["ipv4", "ipv6"] and afi.safi != "sr-te":
                commands.append(template.render(afi=afi.afi, safi=afi.safi, vrf=afi.vrf))

            # For SR-TE SAFI, the EOS command supports sr-te first then ipv4/ipv6
            elif template == VerifyBGPPeerCount.commands[0] and afi.afi in ["ipv4", "ipv6"] and afi.safi == "sr-te":
                commands.append(template.render(afi=afi.safi, safi=afi.afi, vrf=afi.vrf))
            elif template == VerifyBGPPeerCount.commands[1] and afi.afi not in ["ipv4", "ipv6"]:
                commands.append(template.render(afi=afi.afi))
        return commands

    @AntaTest.anta_test
    def test(self) -> None:
        """Main test function for VerifyBGPPeerCount."""
        self.result.is_success()

        failures: dict[tuple[str, Any], dict[str, Any]] = {}

        for command in self.instance_commands:
            num_peers = None
            peer_count = 0
            command_output = command.json_output

            afi = command.params.afi
            safi = command.params.safi if hasattr(command.params, "safi") else None
            afi_vrf = command.params.vrf if hasattr(command.params, "vrf") else "default"

            # Swapping AFI and SAFI in case of SR-TE
            if afi == "sr-te":
                afi, safi = safi, afi

            for input_entry in self.inputs.address_families:
                if input_entry.afi == afi and input_entry.safi == safi and input_entry.vrf == afi_vrf:
                    num_peers = input_entry.num_peers
                    break

            if not (vrfs := command_output.get("vrfs")):
                _add_bgp_failures(failures=failures, afi=afi, safi=safi, vrf=afi_vrf, issue="Not Configured")
                continue

            if afi_vrf == "all":
                for vrf_data in vrfs.values():
                    peer_count += len(vrf_data["peers"])
            else:
                peer_count += len(command_output["vrfs"][afi_vrf]["peers"])

            if peer_count != num_peers:
                _add_bgp_failures(failures=failures, afi=afi, safi=safi, vrf=afi_vrf, issue=f"Expected: {num_peers}, Actual: {peer_count}")

        if failures:
            self.result.is_failure(f"Failures: {list(failures.values())}")


class VerifyBGPPeersHealth(AntaTest):
    """Verifies the health of BGP peers.

    It will validate that all BGP sessions are established and all message queues for these BGP sessions are empty for a given address family.

    It supports multiple types of Address Families Identifiers (AFI) and Subsequent Address Family Identifiers (SAFI).

    For SR-TE SAFI, the EOS command supports sr-te first then ipv4/ipv6 (AFI) which is handled automatically in this test.

    Please refer to the Input class attributes below for details.

    Expected Results
    ----------------
    * Success: If all BGP sessions are established and all messages queues are empty for each address family and VRF.
    * Failure: If there are issues with any of the BGP sessions, or if BGP is not configured for an expected VRF or address family.

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
    ```
    """

    name = "VerifyBGPPeersHealth"
    description = "Verifies the health of BGP peers"
    categories: ClassVar[list[str]] = ["bgp"]
    commands: ClassVar[list[AntaCommand | AntaTemplate]] = [
        AntaTemplate(template="show bgp {afi} {safi} summary vrf {vrf}", revision=3),
        AntaTemplate(template="show bgp {afi} summary", revision=3),
    ]

    class Input(AntaTest.Input):
        """Input model for the VerifyBGPPeersHealth test."""

        address_families: list[BgpAfi]
        """List of BGP address families (BgpAfi)."""

        class BgpAfi(BaseModel):
            """Model for a BGP address family (AFI) and subsequent address family (SAFI)."""

            afi: Afi
            """BGP address family (AFI)."""
            safi: Safi | None = None
            """Optional BGP subsequent service family (SAFI).

            If the input `afi` is `ipv4` or `ipv6`, a valid `safi` must be provided.
            """
            vrf: str = "default"
            """
            Optional VRF for IPv4 and IPv6. If not provided, it defaults to `default`.

            If the input `afi` is not `ipv4` or `ipv6`, e.g. `evpn`, `vrf` must be `default`.
            """

            @model_validator(mode="after")
            def validate_inputs(self) -> Self:
                """Validate the inputs provided to the BgpAfi class.

                If afi is either ipv4 or ipv6, safi must be provided.

                If afi is not ipv4 or ipv6, safi must not be provided and vrf must be default.
                """
                if self.afi in ["ipv4", "ipv6"]:
                    if self.safi is None:
                        msg = "'safi' must be provided when afi is ipv4 or ipv6"
                        raise ValueError(msg)
                elif self.safi is not None:
                    msg = "'safi' must not be provided when afi is not ipv4 or ipv6"
                    raise ValueError(msg)
                elif self.vrf != "default":
                    msg = "'vrf' must be default when afi is not ipv4 or ipv6"
                    raise ValueError(msg)
                return self

    def render(self, template: AntaTemplate) -> list[AntaCommand]:
        """Render the template for each BGP address family in the input list."""
        commands = []
        for afi in self.inputs.address_families:
            if template == VerifyBGPPeersHealth.commands[0] and afi.afi in ["ipv4", "ipv6"] and afi.safi != "sr-te":
                commands.append(template.render(afi=afi.afi, safi=afi.safi, vrf=afi.vrf))

            # For SR-TE SAFI, the EOS command supports sr-te first then ipv4/ipv6
            elif template == VerifyBGPPeersHealth.commands[0] and afi.afi in ["ipv4", "ipv6"] and afi.safi == "sr-te":
                commands.append(template.render(afi=afi.safi, safi=afi.afi, vrf=afi.vrf))
            elif template == VerifyBGPPeersHealth.commands[1] and afi.afi not in ["ipv4", "ipv6"]:
                commands.append(template.render(afi=afi.afi))
        return commands

    @AntaTest.anta_test
    def test(self) -> None:
        """Main test function for VerifyBGPPeersHealth."""
        self.result.is_success()

        failures: dict[tuple[str, Any], dict[str, Any]] = {}

        for command in self.instance_commands:
            command_output = command.json_output

            afi = command.params.afi
            safi = command.params.safi if hasattr(command.params, "safi") else None
            afi_vrf = command.params.vrf if hasattr(command.params, "vrf") else "default"

            # Swapping AFI and SAFI in case of SR-TE
            if afi == "sr-te":
                afi, safi = safi, afi

            if not (vrfs := command_output.get("vrfs")):
                _add_bgp_failures(failures=failures, afi=afi, safi=safi, vrf=afi_vrf, issue="Not Configured")
                continue

            for vrf, vrf_data in vrfs.items():
                if not (peers := vrf_data.get("peers")):
                    _add_bgp_failures(failures=failures, afi=afi, safi=safi, vrf=afi_vrf, issue="No Peers")
                    continue

                peer_issues = {}
                for peer, peer_data in peers.items():
                    issues = _check_peer_issues(peer_data)

                    if issues:
                        peer_issues[peer] = issues

                if peer_issues:
                    _add_bgp_failures(failures=failures, afi=afi, safi=safi, vrf=vrf, issue=peer_issues)

        if failures:
            self.result.is_failure(f"Failures: {list(failures.values())}")


class VerifyBGPSpecificPeers(AntaTest):
    """Verifies the health of specific BGP peer(s).

    It will validate that the BGP session is established and all message queues for this BGP session are empty for the given peer(s).

    It supports multiple types of Address Families Identifiers (AFI) and Subsequent Address Family Identifiers (SAFI).

    For SR-TE SAFI, the EOS command supports sr-te first then ipv4/ipv6 (AFI) which is handled automatically in this test.

    Please refer to the Input class attributes below for details.

    Expected Results
    ----------------
    * Success: If the BGP session is established and all messages queues are empty for each given peer.
    * Failure: If the BGP session has issues or is not configured, or if BGP is not configured for an expected VRF or address family.

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

    name = "VerifyBGPSpecificPeers"
    description = "Verifies the health of specific BGP peer(s)."
    categories: ClassVar[list[str]] = ["bgp"]
    commands: ClassVar[list[AntaCommand | AntaTemplate]] = [
        AntaTemplate(template="show bgp {afi} {safi} summary vrf {vrf}", revision=3),
        AntaTemplate(template="show bgp {afi} summary", revision=3),
    ]

    class Input(AntaTest.Input):
        """Input model for the VerifyBGPSpecificPeers test."""

        address_families: list[BgpAfi]
        """List of BGP address families (BgpAfi)."""

        class BgpAfi(BaseModel):
            """Model for a BGP address family (AFI) and subsequent address family (SAFI)."""

            afi: Afi
            """BGP address family (AFI)."""
            safi: Safi | None = None
            """Optional BGP subsequent service family (SAFI).

            If the input `afi` is `ipv4` or `ipv6`, a valid `safi` must be provided.
            """
            vrf: str = "default"
            """
            Optional VRF for IPv4 and IPv6. If not provided, it defaults to `default`.

            `all` is NOT supported.

            If the input `afi` is not `ipv4` or `ipv6`, e.g. `evpn`, `vrf` must be `default`.
            """
            peers: list[IPv4Address | IPv6Address]
            """List of BGP IPv4 or IPv6 peer."""

            @model_validator(mode="after")
            def validate_inputs(self) -> Self:
                """Validate the inputs provided to the BgpAfi class.

                If afi is either ipv4 or ipv6, safi must be provided and vrf must NOT be all.

                If afi is not ipv4 or ipv6, safi must not be provided and vrf must be default.
                """
                if self.afi in ["ipv4", "ipv6"]:
                    if self.safi is None:
                        msg = "'safi' must be provided when afi is ipv4 or ipv6"
                        raise ValueError(msg)
                    if self.vrf == "all":
                        msg = "'all' is not supported in this test. Use VerifyBGPPeersHealth test instead."
                        raise ValueError(msg)
                elif self.safi is not None:
                    msg = "'safi' must not be provided when afi is not ipv4 or ipv6"
                    raise ValueError(msg)
                elif self.vrf != "default":
                    msg = "'vrf' must be default when afi is not ipv4 or ipv6"
                    raise ValueError(msg)
                return self

    def render(self, template: AntaTemplate) -> list[AntaCommand]:
        """Render the template for each BGP address family in the input list."""
        commands = []

        for afi in self.inputs.address_families:
            if template == VerifyBGPSpecificPeers.commands[0] and afi.afi in ["ipv4", "ipv6"] and afi.safi != "sr-te":
                commands.append(template.render(afi=afi.afi, safi=afi.safi, vrf=afi.vrf))

            # For SR-TE SAFI, the EOS command supports sr-te first then ipv4/ipv6
            elif template == VerifyBGPSpecificPeers.commands[0] and afi.afi in ["ipv4", "ipv6"] and afi.safi == "sr-te":
                commands.append(template.render(afi=afi.safi, safi=afi.afi, vrf=afi.vrf))
            elif template == VerifyBGPSpecificPeers.commands[1] and afi.afi not in ["ipv4", "ipv6"]:
                commands.append(template.render(afi=afi.afi))
        return commands

    @AntaTest.anta_test
    def test(self) -> None:
        """Main test function for VerifyBGPSpecificPeers."""
        self.result.is_success()

        failures: dict[tuple[str, Any], dict[str, Any]] = {}

        for command in self.instance_commands:
            command_output = command.json_output

            afi = command.params.afi
            safi = command.params.safi if hasattr(command.params, "safi") else None
            afi_vrf = command.params.vrf if hasattr(command.params, "vrf") else "default"

            # Swapping AFI and SAFI in case of SR-TE
            if afi == "sr-te":
                afi, safi = safi, afi

            for input_entry in self.inputs.address_families:
                if input_entry.afi == afi and input_entry.safi == safi and input_entry.vrf == afi_vrf:
                    afi_peers = input_entry.peers
                    break

            if not (vrfs := command_output.get("vrfs")):
                _add_bgp_failures(failures=failures, afi=afi, safi=safi, vrf=afi_vrf, issue="Not Configured")
                continue

            peer_issues = {}
            for peer in afi_peers:
                peer_ip = str(peer)
                peer_data = get_value(dictionary=vrfs, key=f"{afi_vrf}_peers_{peer_ip}", separator="_")
                issues = _check_peer_issues(peer_data)
                if issues:
                    peer_issues[peer_ip] = issues

            if peer_issues:
                _add_bgp_failures(failures=failures, afi=afi, safi=safi, vrf=afi_vrf, issue=peer_issues)

        if failures:
            self.result.is_failure(f"Failures: {list(failures.values())}")


class VerifyBGPExchangedRoutes(AntaTest):
    """Verifies if the BGP peers have correctly advertised and received routes.

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

    name = "VerifyBGPExchangedRoutes"
    description = "Verifies the advertised and received routes of BGP peers."
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

    name = "VerifyBGPPeerMPCaps"
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

    name = "VerifyBGPPeerASNCap"
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

    name = "VerifyBGPPeerRouteRefreshCap"
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

    name = "VerifyBGPPeerMD5Auth"
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

    name = "VerifyEVPNType2Route"
    description = "Verifies the EVPN Type-2 routes for a given IPv4 or MAC address and VNI."
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
            # Verify that each EVPN route has at least one valid and active path
            for route, route_data in evpn_routes.items():
                has_active_path = False
                for path in route_data["evpnRoutePaths"]:
                    if path["routeType"]["valid"] is True and path["routeType"]["active"] is True:
                        # At least one path is valid and active, no need to check the other paths
                        has_active_path = True
                        break
                if not has_active_path:
                    bad_evpn_routes.append(route)

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

    name = "VerifyBGPAdvCommunities"
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

    name = "VerifyBGPTimers"
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

    name = "VerifyBGPPeerDropStats"
    description = "Verifies the NLRI drop statistics of a BGP IPv4 peer(s)."
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

    name = "VerifyBGPPeerUpdateErrors"
    description = "Verifies the update error counters of a BGP IPv4 peer."
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

    name = "VerifyBgpRouteMaps"
    description = "Verifies BGP inbound and outbound route-maps of BGP IPv4 peer(s)."
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

    name = "VerifyBGPPeerRouteLimit"
    description = "Verifies maximum routes and maximum routes warning limit for the provided BGP IPv4 peer(s)."
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
