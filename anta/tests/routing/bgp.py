# Copyright (c) 2023-2024 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""
BGP test functions
"""
# Mypy does not understand AntaTest.Input typing
# mypy: disable-error-code=attr-defined
from __future__ import annotations

from ipaddress import IPv4Address, IPv4Network, IPv6Address
from typing import Any, List, Optional, Union, cast

from pydantic import BaseModel, Field, PositiveInt, model_validator, utils
from pydantic_extra_types.mac_address import MacAddress

from anta.custom_types import Afi, MultiProtocolCaps, Safi, Vni
from anta.models import AntaCommand, AntaTemplate, AntaTest
from anta.tools.get_item import get_item
from anta.tools.get_value import get_value

# Need to keep List for pydantic in python 3.8


def _add_bgp_failures(failures: dict[tuple[str, Union[str, None]], dict[str, Any]], afi: Afi, safi: Optional[Safi], vrf: str, issue: Any) -> None:
    """
    Add a BGP failure entry to the given `failures` dictionary.

    Note: This function modifies `failures` in-place.

    Parameters:
        failures (dict): The dictionary to which the failure will be added.
        afi (Afi): The address family identifier.
        vrf (str): The VRF name.
        safi (Safi, optional): The subsequent address family identifier.
        issue (Any): A description of the issue. Can be of any type.

    The `failures` dictionnary will have the following structure:
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
    """
    key = (afi, safi)

    if safi:
        failure_entry = failures.setdefault(key, {"afi": afi, "safi": safi, "vrfs": {}})
    else:
        failure_entry = failures.setdefault(key, {"afi": afi, "vrfs": {}})

    failure_entry["vrfs"][vrf] = issue


def _check_peer_issues(peer_data: Optional[dict[str, Any]]) -> dict[str, Any]:
    """
    Check for issues in BGP peer data.

    Parameters:
        peer_data (dict, optional): The BGP peer data dictionary nested in the `show bgp <afi> <safi> summary` command.

    Returns:
        dict: Dictionary with keys indicating issues or an empty dictionary if no issues.

    Example:
        {"peerNotFound": True}
        {"peerState": "Idle", "inMsgQueue": 2, "outMsgQueue": 0}
        {}

    Raises:
        ValueError: If any of the required keys ("peerState", "inMsgQueue", "outMsgQueue") are missing in `peer_data`, i.e. invalid BGP peer data.
    """
    if peer_data is None:
        return {"peerNotFound": True}

    if any(key not in peer_data for key in ["peerState", "inMsgQueue", "outMsgQueue"]):
        raise ValueError("Provided BGP peer data is invalid.")

    if peer_data["peerState"] != "Established" or peer_data["inMsgQueue"] != 0 or peer_data["outMsgQueue"] != 0:
        return {"peerState": peer_data["peerState"], "inMsgQueue": peer_data["inMsgQueue"], "outMsgQueue": peer_data["outMsgQueue"]}

    return {}


def _add_bgp_routes_failure(
    bgp_routes: list[str], bgp_output: dict[str, Any], peer: str, vrf: str, route_type: str = "advertised_routes"
) -> dict[str, dict[str, dict[str, dict[str, list[str]]]]]:
    """
    Identifies missing BGP routes and invalid or inactive route entries.

    This function checks the BGP output from the device against the expected routes.
    It identifies any missing routes as well as any routes that are invalid or inactive. The results are returned in a dictionary.

    Parameters:
        bgp_routes (list[str]): The list of expected routes.
        bgp_output (dict[str, Any]): The BGP output from the device.
        peer (str): The IP address of the BGP peer.
        vrf (str): The name of the VRF for which the routes need to be verified.
        route_type (str, optional): The type of BGP routes. Defaults to 'advertised_routes'.

    Returns:
        dict[str, dict[str, dict[str, dict[str, list[str]]]]]: A dictionary containing the missing routes and invalid or inactive routes.
    """

    # Prepare the failure routes dictionary
    failure_routes: dict[str, dict[str, Any]] = {}

    # Iterate over the expected BGP routes
    for route in bgp_routes:
        route = str(route)
        failure = {"bgp_peers": {peer: {vrf: {route_type: {route: Any}}}}}

        # Check if the route is missing in the BGP output
        if route not in bgp_output:
            # If missing, add it to the failure routes dictionary
            failure["bgp_peers"][peer][vrf][route_type][route] = "Not found"
            failure_routes = utils.deep_update(failure_routes, failure)
            continue

        # Check if the route is active and valid
        is_active = bgp_output[route]["bgpRoutePaths"][0]["routeType"]["valid"]
        is_valid = bgp_output[route]["bgpRoutePaths"][0]["routeType"]["active"]

        # If the route is either inactive or invalid, add it to the failure routes dictionary
        if not is_active or not is_valid:
            failure["bgp_peers"][peer][vrf][route_type][route] = {"valid": is_valid, "active": is_active}
            failure_routes = utils.deep_update(failure_routes, failure)

    return failure_routes


class VerifyBGPPeerCount(AntaTest):
    """
    This test verifies the count of BGP peers for a given address family.

    It supports multiple types of address families (AFI) and subsequent service families (SAFI).
    Please refer to the Input class attributes below for details.

    Expected Results:
        * success: If the count of BGP peers matches the expected count for each address family and VRF.
        * failure: If the count of BGP peers does not match the expected count, or if BGP is not configured for an expected VRF or address family.
    """

    name = "VerifyBGPPeerCount"
    description = "Verifies the count of BGP peers."
    categories = ["bgp"]
    commands = [
        AntaTemplate(template="show bgp {afi} {safi} summary vrf {vrf}"),
        AntaTemplate(template="show bgp {afi} summary"),
    ]

    class Input(AntaTest.Input):  # pylint: disable=missing-class-docstring
        address_families: List[BgpAfi]
        """
        List of BGP address families (BgpAfi)
        """

        class BgpAfi(BaseModel):  # pylint: disable=missing-class-docstring
            afi: Afi
            """BGP address family (AFI)"""
            safi: Optional[Safi] = None
            """Optional BGP subsequent service family (SAFI).

            If the input `afi` is `ipv4` or `ipv6`, a valid `safi` must be provided.
            """
            vrf: str = "default"
            """
            Optional VRF for IPv4 and IPv6. If not provided, it defaults to `default`.

            If the input `afi` is not `ipv4` or `ipv6`, e.g. `evpn`, `vrf` must be `default`.
            """
            num_peers: PositiveInt
            """Number of expected BGP peer(s)"""

            @model_validator(mode="after")
            def validate_inputs(self: BaseModel) -> BaseModel:
                """
                Validate the inputs provided to the BgpAfi class.

                If afi is either ipv4 or ipv6, safi must be provided.

                If afi is not ipv4 or ipv6, safi must not be provided and vrf must be default.
                """
                if self.afi in ["ipv4", "ipv6"]:
                    if self.safi is None:
                        raise ValueError("'safi' must be provided when afi is ipv4 or ipv6")
                elif self.safi is not None:
                    raise ValueError("'safi' must not be provided when afi is not ipv4 or ipv6")
                elif self.vrf != "default":
                    raise ValueError("'vrf' must be default when afi is not ipv4 or ipv6")
                return self

    def render(self, template: AntaTemplate) -> list[AntaCommand]:
        commands = []
        for afi in self.inputs.address_families:
            if template == VerifyBGPPeerCount.commands[0] and afi.afi in ["ipv4", "ipv6"]:
                commands.append(template.render(afi=afi.afi, safi=afi.safi, vrf=afi.vrf, num_peers=afi.num_peers))
            elif template == VerifyBGPPeerCount.commands[1] and afi.afi not in ["ipv4", "ipv6"]:
                commands.append(template.render(afi=afi.afi, vrf=afi.vrf, num_peers=afi.num_peers))
        return commands

    @AntaTest.anta_test
    def test(self) -> None:
        self.result.is_success()

        failures: dict[tuple[str, Any], dict[str, Any]] = {}

        for command in self.instance_commands:
            peer_count = 0
            command_output = command.json_output

            afi = cast(Afi, command.params.get("afi"))
            safi = cast(Optional[Safi], command.params.get("safi"))
            afi_vrf = cast(str, command.params.get("vrf"))
            num_peers = cast(PositiveInt, command.params.get("num_peers"))

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
    """
    This test verifies the health of BGP peers.

    It will validate that all BGP sessions are established and all message queues for these BGP sessions are empty for a given address family.

    It supports multiple types of address families (AFI) and subsequent service families (SAFI).
    Please refer to the Input class attributes below for details.

    Expected Results:
        * success: If all BGP sessions are established and all messages queues are empty for each address family and VRF.
        * failure: If there are issues with any of the BGP sessions, or if BGP is not configured for an expected VRF or address family.
    """

    name = "VerifyBGPPeersHealth"
    description = "Verifies the health of BGP peers"
    categories = ["bgp"]
    commands = [
        AntaTemplate(template="show bgp {afi} {safi} summary vrf {vrf}"),
        AntaTemplate(template="show bgp {afi} summary"),
    ]

    class Input(AntaTest.Input):  # pylint: disable=missing-class-docstring
        address_families: List[BgpAfi]
        """
        List of BGP address families (BgpAfi)
        """

        class BgpAfi(BaseModel):  # pylint: disable=missing-class-docstring
            afi: Afi
            """BGP address family (AFI)"""
            safi: Optional[Safi] = None
            """Optional BGP subsequent service family (SAFI).

            If the input `afi` is `ipv4` or `ipv6`, a valid `safi` must be provided.
            """
            vrf: str = "default"
            """
            Optional VRF for IPv4 and IPv6. If not provided, it defaults to `default`.

            If the input `afi` is not `ipv4` or `ipv6`, e.g. `evpn`, `vrf` must be `default`.
            """

            @model_validator(mode="after")
            def validate_inputs(self: BaseModel) -> BaseModel:
                """
                Validate the inputs provided to the BgpAfi class.

                If afi is either ipv4 or ipv6, safi must be provided.

                If afi is not ipv4 or ipv6, safi must not be provided and vrf must be default.
                """
                if self.afi in ["ipv4", "ipv6"]:
                    if self.safi is None:
                        raise ValueError("'safi' must be provided when afi is ipv4 or ipv6")
                elif self.safi is not None:
                    raise ValueError("'safi' must not be provided when afi is not ipv4 or ipv6")
                elif self.vrf != "default":
                    raise ValueError("'vrf' must be default when afi is not ipv4 or ipv6")
                return self

    def render(self, template: AntaTemplate) -> list[AntaCommand]:
        commands = []
        for afi in self.inputs.address_families:
            if template == VerifyBGPPeersHealth.commands[0] and afi.afi in ["ipv4", "ipv6"]:
                commands.append(template.render(afi=afi.afi, safi=afi.safi, vrf=afi.vrf))
            elif template == VerifyBGPPeersHealth.commands[1] and afi.afi not in ["ipv4", "ipv6"]:
                commands.append(template.render(afi=afi.afi, vrf=afi.vrf))
        return commands

    @AntaTest.anta_test
    def test(self) -> None:
        self.result.is_success()

        failures: dict[tuple[str, Any], dict[str, Any]] = {}

        for command in self.instance_commands:
            command_output = command.json_output

            afi = cast(Afi, command.params.get("afi"))
            safi = cast(Optional[Safi], command.params.get("safi"))
            afi_vrf = cast(str, command.params.get("vrf"))

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
    """
    This test verifies the health of specific BGP peer(s).

    It will validate that the BGP session is established and all message queues for this BGP session are empty for the given peer(s).

    It supports multiple types of address families (AFI) and subsequent service families (SAFI).
    Please refer to the Input class attributes below for details.

    Expected Results:
        * success: If the BGP session is established and all messages queues are empty for each given peer.
        * failure: If the BGP session has issues or is not configured, or if BGP is not configured for an expected VRF or address family.
    """

    name = "VerifyBGPSpecificPeers"
    description = "Verifies the health of specific BGP peer(s)."
    categories = ["bgp"]
    commands = [
        AntaTemplate(template="show bgp {afi} {safi} summary vrf {vrf}"),
        AntaTemplate(template="show bgp {afi} summary"),
    ]

    class Input(AntaTest.Input):  # pylint: disable=missing-class-docstring
        address_families: List[BgpAfi]
        """
        List of BGP address families (BgpAfi)
        """

        class BgpAfi(BaseModel):  # pylint: disable=missing-class-docstring
            afi: Afi
            """BGP address family (AFI)"""
            safi: Optional[Safi] = None
            """Optional BGP subsequent service family (SAFI).

            If the input `afi` is `ipv4` or `ipv6`, a valid `safi` must be provided.
            """
            vrf: str = "default"
            """
            Optional VRF for IPv4 and IPv6. If not provided, it defaults to `default`.

            `all` is NOT supported.

            If the input `afi` is not `ipv4` or `ipv6`, e.g. `evpn`, `vrf` must be `default`.
            """
            peers: List[Union[IPv4Address, IPv6Address]]
            """List of BGP IPv4 or IPv6 peer"""

            @model_validator(mode="after")
            def validate_inputs(self: BaseModel) -> BaseModel:
                """
                Validate the inputs provided to the BgpAfi class.

                If afi is either ipv4 or ipv6, safi must be provided and vrf must NOT be all.

                If afi is not ipv4 or ipv6, safi must not be provided and vrf must be default.
                """
                if self.afi in ["ipv4", "ipv6"]:
                    if self.safi is None:
                        raise ValueError("'safi' must be provided when afi is ipv4 or ipv6")
                    if self.vrf == "all":
                        raise ValueError("'all' is not supported in this test. Use VerifyBGPPeersHealth test instead.")
                elif self.safi is not None:
                    raise ValueError("'safi' must not be provided when afi is not ipv4 or ipv6")
                elif self.vrf != "default":
                    raise ValueError("'vrf' must be default when afi is not ipv4 or ipv6")
                return self

    def render(self, template: AntaTemplate) -> list[AntaCommand]:
        commands = []
        for afi in self.inputs.address_families:
            if template == VerifyBGPSpecificPeers.commands[0] and afi.afi in ["ipv4", "ipv6"]:
                commands.append(template.render(afi=afi.afi, safi=afi.safi, vrf=afi.vrf, peers=afi.peers))
            elif template == VerifyBGPSpecificPeers.commands[1] and afi.afi not in ["ipv4", "ipv6"]:
                commands.append(template.render(afi=afi.afi, vrf=afi.vrf, peers=afi.peers))
        return commands

    @AntaTest.anta_test
    def test(self) -> None:
        self.result.is_success()

        failures: dict[tuple[str, Any], dict[str, Any]] = {}

        for command in self.instance_commands:
            command_output = command.json_output

            afi = cast(Afi, command.params.get("afi"))
            safi = cast(Optional[Safi], command.params.get("safi"))
            afi_vrf = cast(str, command.params.get("vrf"))
            afi_peers = cast(List[Union[IPv4Address, IPv6Address]], command.params.get("peers", []))

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
    """
    Verifies if the BGP peers have correctly advertised and received routes.
    The route type should be 'valid' and 'active' for a specified VRF.

    Expected results:
        * success: If the BGP peers have correctly advertised and received routes of type 'valid' and 'active' for a specified VRF.
        * failure: If a BGP peer is not found, the expected advertised/received routes are not found, or the routes are not 'valid' or 'active'.
    """

    name = "VerifyBGPExchangedRoutes"
    description = "Verifies if BGP peers have correctly advertised/received routes with type as valid and active for a specified VRF."
    categories = ["bgp"]
    commands = [
        AntaTemplate(template="show bgp neighbors {peer} advertised-routes vrf {vrf}"),
        AntaTemplate(template="show bgp neighbors {peer} routes vrf {vrf}"),
    ]

    class Input(AntaTest.Input):
        """
        Input parameters of the testcase.
        """

        bgp_peers: List[BgpNeighbors]
        """List of BGP peers"""

        class BgpNeighbors(BaseModel):
            """
            This class defines the details of a BGP peer.
            """

            peer_address: IPv4Address
            """IPv4 address of a BGP peer"""
            vrf: str = "default"
            """Optional VRF for BGP peer. If not provided, it defaults to `default`."""
            advertised_routes: List[IPv4Network]
            """List of advertised routes of a BGP peer."""
            received_routes: List[IPv4Network]
            """List of received routes of a BGP peer."""

    def render(self, template: AntaTemplate) -> list[AntaCommand]:
        """Renders the template with the provided inputs. Returns a list of commands to be executed."""

        return [
            template.render(peer=bgp_peer.peer_address, vrf=bgp_peer.vrf, advertised_routes=bgp_peer.advertised_routes, received_routes=bgp_peer.received_routes)
            for bgp_peer in self.inputs.bgp_peers
        ]

    @AntaTest.anta_test
    def test(self) -> None:
        failures: dict[str, dict[str, Any]] = {"bgp_peers": {}}

        # Iterating over command output for different peers
        for command in self.instance_commands:
            peer = str(command.params["peer"])
            vrf = command.params["vrf"]
            advertised_routes = command.params["advertised_routes"]
            received_routes = command.params["received_routes"]
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
            failures = utils.deep_update(failures, failure_routes)

        if not failures["bgp_peers"]:
            self.result.is_success()
        else:
            self.result.is_failure(f"Following BGP peers are not found or routes are not exchanged properly:\n{failures}")


class VerifyBGPPeerMPCaps(AntaTest):
    """
    Verifies the multiprotocol capabilities of a BGP peer in a specified VRF.
    Expected results:
        * success: The test will pass if the BGP peer's multiprotocol capabilities are advertised, received, and enabled in the specified VRF.
        * failure: The test will fail if BGP peers are not found or multiprotocol capabilities are not advertised, received, and enabled in the specified VRF.
    """

    name = "VerifyBGPPeerMPCaps"
    description = "Verifies the multiprotocol capabilities of a BGP peer in a specified VRF"
    categories = ["bgp"]
    commands = [AntaCommand(command="show bgp neighbors vrf all")]

    class Input(AntaTest.Input):
        """
        Input parameters of the testcase.
        """

        bgp_peers: List[BgpPeers]
        """List of BGP peers"""

        class BgpPeers(BaseModel):
            """
            This class defines the details of a BGP peer.
            """

            peer_address: IPv4Address
            """IPv4 address of a BGP peer"""
            vrf: str = "default"
            """Optional VRF for BGP peer. If not provided, it defaults to `default`."""
            capabilities: List[MultiProtocolCaps]
            """Multiprotocol capabilities"""

    @AntaTest.anta_test
    def test(self) -> None:
        failures: dict[str, Any] = {"bgp_peers": {}}

        # Iterate over each bgp peer
        for bgp_peer in self.inputs.bgp_peers:
            peer = str(bgp_peer.peer_address)
            vrf = bgp_peer.vrf
            capabilities = bgp_peer.capabilities
            failure: dict[str, dict[str, dict[str, Any]]] = {"bgp_peers": {peer: {vrf: {}}}}

            # Check if BGP output exists
            if (
                not (bgp_output := get_value(self.instance_commands[0].json_output, f"vrfs.{vrf}.peerList"))
                or (bgp_output := get_item(bgp_output, "peerAddress", peer)) is None
            ):
                failure["bgp_peers"][peer][vrf] = {"status": "Not configured"}
                failures = utils.deep_update(failures, failure)
                continue

            # Check each capability
            bgp_output = get_value(bgp_output, "neighborCapabilities.multiprotocolCaps")
            for capability in capabilities:
                capability_output = bgp_output.get(capability)

                # Check if capabilities are missing
                if not capability_output:
                    failure["bgp_peers"][peer][vrf][capability] = "not found"
                    failures = utils.deep_update(failures, failure)

                # Check if capabilities are not advertised, received, or enabled
                elif not all(capability_output.get(prop, False) for prop in ["advertised", "received", "enabled"]):
                    failure["bgp_peers"][peer][vrf][capability] = capability_output
                    failures = utils.deep_update(failures, failure)

        # Check if there are any failures
        if not failures["bgp_peers"]:
            self.result.is_success()
        else:
            self.result.is_failure(f"Following BGP peer multiprotocol capabilities are not found or not ok:\n{failures}")


class VerifyBGPPeerASNCap(AntaTest):
    """
    Verifies the four octet asn capabilities of a BGP peer in a specified VRF.
    Expected results:
        * success: The test will pass if BGP peer's four octet asn capabilities are advertised, received, and enabled in the specified VRF.
        * failure: The test will fail if BGP peers are not found or four octet asn capabilities are not advertised, received, and enabled in the specified VRF.
    """

    name = "VerifyBGPPeerASNCap"
    description = "Verifies the four octet asn capabilities of a BGP peer in a specified VRF."
    categories = ["bgp"]
    commands = [AntaCommand(command="show bgp neighbors vrf all")]

    class Input(AntaTest.Input):
        """
        Input parameters of the testcase.
        """

        bgp_peers: List[BgpPeers]
        """List of BGP peers"""

        class BgpPeers(BaseModel):
            """
            This class defines the details of a BGP peer.
            """

            peer_address: IPv4Address
            """IPv4 address of a BGP peer"""
            vrf: str = "default"
            """Optional VRF for BGP peer. If not provided, it defaults to `default`."""

    @AntaTest.anta_test
    def test(self) -> None:
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
                failures = utils.deep_update(failures, failure)
                continue

            bgp_output = get_value(bgp_output, "neighborCapabilities.fourOctetAsnCap")

            # Check if  four octet asn capabilities are found
            if not bgp_output:
                failure["bgp_peers"][peer][vrf] = {"fourOctetAsnCap": "not found"}
                failures = utils.deep_update(failures, failure)

            # Check if capabilities are not advertised, received, or enabled
            elif not all(bgp_output.get(prop, False) for prop in ["advertised", "received", "enabled"]):
                failure["bgp_peers"][peer][vrf] = {"fourOctetAsnCap": bgp_output}
                failures = utils.deep_update(failures, failure)

        # Check if there are any failures
        if not failures["bgp_peers"]:
            self.result.is_success()
        else:
            self.result.is_failure(f"Following BGP peer four octet asn capabilities are not found or not ok:\n{failures}")


class VerifyBGPPeerRouteRefreshCap(AntaTest):
    """
    Verifies the route refresh capabilities of a BGP peer in a specified VRF.
    Expected results:
        * success: The test will pass if the BGP peer's route refresh capabilities are advertised, received, and enabled in the specified VRF.
        * failure: The test will fail if BGP peers are not found or route refresh capabilities are not advertised, received, and enabled in the specified VRF.
    """

    name = "VerifyBGPPeerRouteRefreshCap"
    description = "Verifies the route refresh capabilities of a BGP peer in a specified VRF."
    categories = ["bgp"]
    commands = [AntaCommand(command="show bgp neighbors vrf all")]

    class Input(AntaTest.Input):
        """
        Input parameters of the testcase.
        """

        bgp_peers: List[BgpPeers]
        """List of BGP peers"""

        class BgpPeers(BaseModel):
            """
            This class defines the details of a BGP peer.
            """

            peer_address: IPv4Address
            """IPv4 address of a BGP peer"""
            vrf: str = "default"
            """Optional VRF for BGP peer. If not provided, it defaults to `default`."""

    @AntaTest.anta_test
    def test(self) -> None:
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
                failures = utils.deep_update(failures, failure)
                continue

            bgp_output = get_value(bgp_output, "neighborCapabilities.routeRefreshCap")

            # Check if route refresh capabilities are found
            if not bgp_output:
                failure["bgp_peers"][peer][vrf] = {"routeRefreshCap": "not found"}
                failures = utils.deep_update(failures, failure)

            # Check if capabilities are not advertised, received, or enabled
            elif not all(bgp_output.get(prop, False) for prop in ["advertised", "received", "enabled"]):
                failure["bgp_peers"][peer][vrf] = {"routeRefreshCap": bgp_output}
                failures = utils.deep_update(failures, failure)

        # Check if there are any failures
        if not failures["bgp_peers"]:
            self.result.is_success()
        else:
            self.result.is_failure(f"Following BGP peer route refresh capabilities are not found or not ok:\n{failures}")


class VerifyBGPPeerMD5Auth(AntaTest):
    """
    Verifies the MD5 authentication and state of IPv4 BGP peers in a specified VRF.
    Expected results:
        * success: The test will pass if IPv4 BGP peers are configured with MD5 authentication and state as established in the specified VRF.
        * failure: The test will fail if IPv4 BGP peers are not found, state is not as established or MD5 authentication is not enabled in the specified VRF.
    """

    name = "VerifyBGPPeerMD5Auth"
    description = "Verifies the MD5 authentication and state of IPv4 BGP peers in a specified VRF"
    categories = ["routing", "bgp"]
    commands = [AntaCommand(command="show bgp neighbors vrf all")]

    class Input(AntaTest.Input):
        """
        Input parameters of the test case.
        """

        bgp_peers: List[BgpPeers]
        """List of IPv4 BGP peers"""

        class BgpPeers(BaseModel):
            """
            This class defines the details of an IPv4 BGP peer.
            """

            peer_address: IPv4Address
            """IPv4 address of BGP peer."""
            vrf: str = "default"
            """Optional VRF for BGP peer. If not provided, it defaults to `default`."""

    @AntaTest.anta_test
    def test(self) -> None:
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
                failures = utils.deep_update(failures, failure)
                continue

            # Check if BGP peer state and authentication
            state = bgp_output.get("state")
            md5_auth_enabled = bgp_output.get("md5AuthEnabled")
            if state != "Established" or not md5_auth_enabled:
                failure["bgp_peers"][peer][vrf] = {"state": state, "md5_auth_enabled": md5_auth_enabled}
                failures = utils.deep_update(failures, failure)

        # Check if there are any failures
        if not failures["bgp_peers"]:
            self.result.is_success()
        else:
            self.result.is_failure(f"Following BGP peers are not configured, not established or MD5 authentication is not enabled:\n{failures}")


class VerifyEVPNType2Route(AntaTest):
    """
    This test verifies the EVPN Type-2 routes for a given IPv4 or MAC address and VNI.

    Expected Results:
        * success: If all provided VXLAN endpoints have at least one valid and active path to their EVPN Type-2 routes.
        * failure: If any of the provided VXLAN endpoints do not have at least one valid and active path to their EVPN Type-2 routes.
    """

    name = "VerifyEVPNType2Route"
    description = "Verifies the EVPN Type-2 routes for a given IPv4 or MAC address and VNI."
    categories = ["routing", "bgp"]
    commands = [AntaTemplate(template="show bgp evpn route-type mac-ip {address} vni {vni}")]

    class Input(AntaTest.Input):
        """Inputs for the VerifyEVPNType2Route test."""

        vxlan_endpoints: List[VxlanEndpoint]
        """List of VXLAN endpoints to verify"""

        class VxlanEndpoint(BaseModel):
            """VXLAN endpoint input model."""

            address: Union[IPv4Address, MacAddress]
            """IPv4 or MAC address of the VXLAN endpoint"""
            vni: Vni
            """VNI of the VXLAN endpoint"""

    def render(self, template: AntaTemplate) -> list[AntaCommand]:
        return [template.render(address=endpoint.address, vni=endpoint.vni) for endpoint in self.inputs.vxlan_endpoints]

    @AntaTest.anta_test
    def test(self) -> None:
        self.result.is_success()
        no_evpn_routes = []
        bad_evpn_routes = []

        for command in self.instance_commands:
            address = str(command.params["address"])
            vni = command.params["vni"]
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
    """
    Verifies if the advertised communities of BGP peers are standard, extended, and large in the specified VRF.
    Expected results:
        * success: The test will pass if the advertised communities of BGP peers are standard, extended, and large in the specified VRF.
        * failure: The test will fail if the advertised communities of BGP peers are not standard, extended, and large in the specified VRF.
    """

    name = "VerifyBGPAdvCommunities"
    description = "Verifies if the advertised communities of BGP peers are standard, extended, and large in the specified VRF."
    categories = ["routing", "bgp"]
    commands = [AntaCommand(command="show bgp neighbors vrf all")]

    class Input(AntaTest.Input):
        """
        Input parameters for the test.
        """

        bgp_peers: List[BgpPeers]
        """List of BGP peers"""

        class BgpPeers(BaseModel):
            """
            This class defines the details of a BGP peer.
            """

            peer_address: IPv4Address
            """IPv4 address of a BGP peer."""
            vrf: str = "default"
            """Optional VRF for BGP peer. If not provided, it defaults to `default`."""

    @AntaTest.anta_test
    def test(self) -> None:
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
                failures = utils.deep_update(failures, failure)
                continue

            # Verify BGP peer's advertised communities
            bgp_output = bgp_output.get("advertisedCommunities")
            if not bgp_output["standard"] or not bgp_output["extended"] or not bgp_output["large"]:
                failure["bgp_peers"][peer][vrf] = {"advertised_communities": bgp_output}
                failures = utils.deep_update(failures, failure)

        if not failures["bgp_peers"]:
            self.result.is_success()
        else:
            self.result.is_failure(f"Following BGP peers are not configured or advertised communities are not standard, extended, and large:\n{failures}")


class VerifyBGPTimers(AntaTest):
    """
    Verifies if the BGP peers are configured with the correct hold and keep-alive timers in the specified VRF.
    Expected results:
        * success: The test will pass if the hold and keep-alive timers are correct for BGP peers in the specified VRF.
        * failure: The test will fail if BGP peers are not found or hold and keep-alive timers are not correct in the specified VRF.
    """

    name = "VerifyBGPTimers"
    description = "Verifies if the BGP peers are configured with the correct hold and keep alive timers in the specified VRF."
    categories = ["routing", "bgp"]
    commands = [AntaCommand(command="show bgp neighbors vrf all")]

    class Input(AntaTest.Input):
        """
        Input parameters for the test.
        """

        bgp_peers: List[BgpPeers]
        """List of BGP peers"""

        class BgpPeers(BaseModel):
            """
            This class defines the details of a BGP peer.
            """

            peer_address: IPv4Address
            """IPv4 address of a BGP peer"""
            vrf: str = "default"
            """Optional VRF for BGP peer. If not provided, it defaults to `default`."""
            hold_time: int = Field(ge=3, le=7200)
            """BGP hold time in seconds"""
            keep_alive_time: int = Field(ge=0, le=3600)
            """BGP keep-alive time in seconds"""

    @AntaTest.anta_test
    def test(self) -> None:
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
