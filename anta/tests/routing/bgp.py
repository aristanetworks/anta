# Copyright (c) 2023 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""
BGP test functions
"""
# Mypy does not understand AntaTest.Input typing
# mypy: disable-error-code=attr-defined
from __future__ import annotations

from ipaddress import IPv4Address
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Union

from pydantic import model_validator

from anta.decorators import check_bgp_family_enable
from anta.models import AntaCommand, AntaTemplate, AntaTest

if TYPE_CHECKING:
    from pydantic import BaseModel


def _check_bgp_vrfs(bgp_vrfs: dict[str, Any], peer_filter: Optional[Union[str, list[str]]] = None) -> dict[str, Any]:
    """
    Parse the output of the `show bgp <address family> unicast summary vrf <vrf>` 'vrfs' key
    and returns a dictionary with the following structure:

    {
        <vrf>: {
            <peer>:
                {
                    "peerState": <state>,
                    "inMsgQueue": <count>,
                    "outMsgQueue": <count>,
                }
        }
    }

    Args:
        bgp_vrfs: Output of the `show bgp <address family> unicast summary vrf <vrf>` 'vrfs' key
        peer_filter: Optional peer or list of peers to verify; defaults to verifying all peers
    """
    state_issue: dict[str, Any] = {}

    if isinstance(peer_filter, str):
        peer_filter = [peer_filter]

    for vrf in bgp_vrfs:
        for peer in bgp_vrfs[vrf]["peers"]:
            if peer_filter is not None and peer not in peer_filter:
                continue

            peer_info = bgp_vrfs[vrf]["peers"][peer]

            if (peer_info["peerState"] != "Established") or (peer_info["inMsgQueue"] != 0) or (peer_info["outMsgQueue"] != 0):
                vrf_dict = state_issue.setdefault(vrf, {})
                vrf_dict.update(
                    {
                        peer: {
                            "peerState": peer_info["peerState"],
                            "inMsgQueue": peer_info["inMsgQueue"],
                            "outMsgQueue": peer_info["outMsgQueue"],
                        }
                    }
                )

    return state_issue


class VerifyBGPIPv4UnicastState(AntaTest):
    """
    Verifies all IPv4 unicast BGP sessions are established (for all VRF)
    and all BGP messages queues for these sessions are empty (for all VRF).

    * self.result = "skipped" if no BGP vrf are returned by the device
    * self.result = "success" if all IPv4 unicast BGP sessions are established (for all VRF)
                         and all BGP messages queues for these sessions are empty (for all VRF).
    * self.result = "failure" otherwise.
    """

    name = "VerifyBGPIPv4UnicastState"
    description = "Verifies all IPv4 unicast BGP sessions are established (for all VRF) and all BGP messages queues for these sessions are empty (for all VRF)."
    categories = ["routing", "bgp"]
    commands = [AntaCommand(command="show bgp ipv4 unicast summary vrf all")]

    @check_bgp_family_enable("ipv4")
    @AntaTest.anta_test
    def test(self) -> None:
        command_output = self.instance_commands[0].json_output
        state_issue = _check_bgp_vrfs(command_output["vrfs"])
        if not state_issue:
            self.result.is_success()
        else:
            self.result.is_failure(f"Some IPv4 Unicast BGP Peer are not up: {state_issue}")


class VerifyBGPIPv4UnicastPeers(AntaTest):
    """
    This test class performs verification of BGP IPv4 unicast peers for specific VRFs.

    !!! warning
        The name of this test has been updated from `VerifyBGPIPv4UnicastCount` for better representation.

    The `count_only` input attribute modifies the behavior of this test as follows:

    If set to True (default):\n
    1. Verifies that the specified VRFs are configured.
    2. Validates the actual count of BGP IPv4 unicast neighbors against the expected count for each specified VRF.
    3. Verifies that all IPv4 unicast BGP sessions in the specified VRFs are established and all message queues for these BGP sessions are empty.

    If set to False:\n
    1. Verifies that the specified VRFs are configured.
    2. Checks that each specified BGP IPv4 unicast peer is present in the corresponding VRF.
    3. Verifies that the BGP session for the specified peers are established and all message queues for these BGP sessions are empty.

    Expected Results:
        * success:
            - All specified VRFs are configured,
            - The actual count of BGP IPv4 unicast neighbors matches the expected count for each specified VRF
              or all specified BGP IPv4 unicast peers are present in the corresponding VRFs
            - There are no issues with the BGP sessions
        * failure:
            - Any of the specified VRFs is not configured.
            - The actual count of BGP IPv4 unicast neighbors doesn't match the expected count for any specified VRF
              or any specified BGP IPv4 unicast peer is not found in the corresponding VRF
            - There are issues with the BGP sessions
    """

    name = "VerifyBGPIPv4UnicastPeers"
    description = "Verifies the BGP IPv4 unicast peers for specific VRFs"
    categories = ["routing", "bgp"]
    commands = [AntaTemplate(template="show bgp ipv4 unicast summary vrf {vrf}")]

    class Input(AntaTest.Input):  # pylint: disable=missing-class-docstring
        vrfs: Dict[str, Union[List[IPv4Address], int]]
        """
        Dictionary mapping VRF names to either:\n
        - A list of expected IPv4 addresses for the BGP peers, or
        - An expected integer count of BGP peers

        The VRF name cannot be 'all'
        """
        count_only: bool = True
        """
        Flag to indicate whether to only validate the count of BGP peers.
        If set to True, the test will only check the count of peers and not the specific peer IPs.
        """

        @model_validator(mode="after")  # type: ignore
        def check_count_only(self: BaseModel) -> BaseModel:  # type: ignore
            """Pydantic model_validator to validate the VRFs"""
            for vrf, value in self.vrfs.items():
                if vrf == "all":
                    raise ValueError("'all' is not supported in this test. Use VerifyBGPIPv4UnicastState test instead.")
                if self.count_only and not isinstance(value, int):
                    raise ValueError(f"Expected integer count for VRF {vrf} when count_only is set to True")
                if not self.count_only and not isinstance(value, list):
                    raise ValueError(f"Expected list of peers for VRF {vrf} when count_only is set to False")

            return self

    def render(self, template: AntaTemplate) -> list[AntaCommand]:
        return [template.render(vrf=vrf) for vrf in self.inputs.vrfs]

    @check_bgp_family_enable(family="ipv4")
    @AntaTest.anta_test
    def test(self) -> None:  # pylint: disable=too-many-branches
        self.result.is_success()

        failures: dict[str, Any] = {"VRF(s) not configured": [], "Wrong number of peers": {}, "Peer(s) issues": [], "Peer(s) not configured": {}}

        for command in self.instance_commands:
            if command.params and "vrf" in command.params:
                vrf = command.params["vrf"]

                if vrf not in command.json_output["vrfs"]:
                    failures["VRF(s) not configured"].append(vrf)
                    continue

                output_peers = command.json_output["vrfs"][vrf]["peers"]

                if self.inputs.count_only:
                    vrf_peer_count = self.inputs.vrfs[vrf]
                    state_issue = _check_bgp_vrfs(bgp_vrfs=command.json_output["vrfs"])

                    if len(output_peers) != vrf_peer_count:
                        failures["Wrong number of peers"].setdefault(vrf, len(output_peers))

                    if state_issue:
                        failures["Peer(s) issues"].append(state_issue)
                else:
                    input_peers = self.inputs.vrfs[vrf]
                    for peer in input_peers:
                        peer = str(peer)
                        if peer not in output_peers:
                            failures["Peer(s) not configured"].setdefault(vrf, []).append(peer)
                            continue

                        state_issue = _check_bgp_vrfs(bgp_vrfs=command.json_output["vrfs"], peer_filter=peer)
                        if state_issue:
                            failures["Peer(s) issues"].append(state_issue)

        for failure in list(failures.keys()):
            if not failures[failure]:
                failures.pop(failure)

        if failures:
            self.result.is_failure(f"The following failure(s) occured: {failures}")


class VerifyBGPIPv6UnicastState(AntaTest):
    """
    Verifies all IPv6 unicast BGP sessions are established (for all VRF)
    and all BGP messages queues for these sessions are empty (for all VRF).

    * self.result = "skipped" if no BGP vrf are returned by the device
    * self.result = "success" if all IPv6 unicast BGP sessions are established (for all VRF)
                         and all BGP messages queues for these sessions are empty (for all VRF).
    * self.result = "failure" otherwise.
    """

    name = "VerifyBGPIPv6UnicastState"
    description = "Verifies all IPv6 unicast BGP sessions are established (for all VRF) and all BGP messages queues for these sessions are empty (for all VRF)."
    categories = ["routing", "bgp"]
    commands = [AntaCommand(command="show bgp ipv6 unicast summary vrf all")]

    @check_bgp_family_enable("ipv6")
    @AntaTest.anta_test
    def test(self) -> None:
        command_output = self.instance_commands[0].json_output
        state_issue = _check_bgp_vrfs(command_output["vrfs"])
        if not state_issue:
            self.result.is_success()
        else:
            self.result.is_failure(f"Some IPv4 Unicast BGP Peer are not up: {state_issue}")


class VerifyBGPEVPNState(AntaTest):
    """
    Verifies all EVPN BGP sessions are established (default VRF).

    * self.result = "skipped" if no BGP EVPN peers are returned by the device
    * self.result = "success" if all EVPN BGP sessions are established.
    * self.result = "failure" otherwise.
    """

    name = "VerifyBGPEVPNState"
    description = "Verifies all EVPN BGP sessions are established (default VRF)."
    categories = ["routing", "bgp"]
    commands = [AntaCommand(command="show bgp evpn summary")]

    @check_bgp_family_enable("evpn")
    @AntaTest.anta_test
    def test(self) -> None:
        command_output = self.instance_commands[0].json_output
        bgp_vrfs = command_output["vrfs"]
        peers = bgp_vrfs["default"]["peers"]
        non_established_peers = [peer for peer, peer_dict in peers.items() if peer_dict["peerState"] != "Established"]
        if not non_established_peers:
            self.result.is_success()
        else:
            self.result.is_failure(f"The following EVPN peers are not established: {non_established_peers}")


class VerifyBGPEVPNCount(AntaTest):
    """
    Verifies all EVPN BGP sessions are established (default VRF)
    and the actual number of BGP EVPN neighbors is the one we expect (default VRF).

    * self.result = "success" if all EVPN BGP sessions are Established and if the actual
                         number of BGP EVPN neighbors is the one we expect.
    * self.result = "failure" otherwise.
    """

    name = "VerifyBGPEVPNCount"
    description = "Verifies all EVPN BGP sessions are established (default VRF) and the actual number of BGP EVPN neighbors is the one we expect (default VRF)."
    categories = ["routing", "bgp"]
    commands = [AntaCommand(command="show bgp evpn summary")]

    class Input(AntaTest.Input):  # pylint: disable=missing-class-docstring
        number: int
        """The expected number of BGP EVPN neighbors in the default VRF"""

    @check_bgp_family_enable("evpn")
    @AntaTest.anta_test
    def test(self) -> None:
        command_output = self.instance_commands[0].json_output
        peers = command_output["vrfs"]["default"]["peers"]
        non_established_peers = [peer for peer, peer_dict in peers.items() if peer_dict["peerState"] != "Established"]
        if not non_established_peers and len(peers) == self.inputs.number:
            self.result.is_success()
        else:
            self.result.is_failure()
            if len(peers) != self.inputs.number:
                self.result.is_failure(f"Expecting {self.inputs.number} BGP EVPN peers and got {len(peers)}")
            if non_established_peers:
                self.result.is_failure(f"The following EVPN peers are not established: {non_established_peers}")


class VerifyBGPRTCState(AntaTest):
    """
    Verifies all RTC BGP sessions are established (default VRF).

    * self.result = "skipped" if no BGP RTC peers are returned by the device
    * self.result = "success" if all RTC BGP sessions are established.
    * self.result = "failure" otherwise.
    """

    name = "VerifyBGPRTCState"
    description = "Verifies all RTC BGP sessions are established (default VRF)."
    categories = ["routing", "bgp"]
    commands = [AntaCommand(command="show bgp rt-membership summary")]

    @check_bgp_family_enable("rtc")
    @AntaTest.anta_test
    def test(self) -> None:
        command_output = self.instance_commands[0].json_output
        bgp_vrfs = command_output["vrfs"]
        peers = bgp_vrfs["default"]["peers"]
        non_established_peers = [peer for peer, peer_dict in peers.items() if peer_dict["peerState"] != "Established"]
        if not non_established_peers:
            self.result.is_success()
        else:
            self.result.is_failure(f"The following RTC peers are not established: {non_established_peers}")


class VerifyBGPRTCCount(AntaTest):
    """
    Verifies all RTC BGP sessions are established (default VRF)
    and the actual number of BGP RTC neighbors is the one we expect (default VRF).

    * self.result = "success" if all RTC BGP sessions are Established and if the actual
                         number of BGP RTC neighbors is the one we expect.
    * self.result = "failure" otherwise.
    """

    name = "VerifyBGPRTCCount"
    description = "Verifies all RTC BGP sessions are established (default VRF) and the actual number of BGP RTC neighbors is the one we expect (default VRF)."
    categories = ["routing", "bgp"]
    commands = [AntaCommand(command="show bgp rt-membership summary")]

    class Input(AntaTest.Input):  # pylint: disable=missing-class-docstring
        number: int
        """The expected number of BGP RTC neighbors in the default VRF"""

    @check_bgp_family_enable("rtc")
    @AntaTest.anta_test
    def test(self) -> None:
        command_output = self.instance_commands[0].json_output
        peers = command_output["vrfs"]["default"]["peers"]
        non_established_peers = [peer for peer, peer_dict in peers.items() if peer_dict["peerState"] != "Established"]
        if not non_established_peers and len(peers) == self.inputs.number:
            self.result.is_success()
        else:
            self.result.is_failure()
            if len(peers) != self.inputs.number:
                self.result.is_failure(f"Expecting {self.inputs.number} BGP RTC peers and got {len(peers)}")
            if non_established_peers:
                self.result.is_failure(f"The following RTC peers are not established: {non_established_peers}")
