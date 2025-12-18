# Copyright (c) 2023-2025 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Test functions related to various router path-selection settings."""

# Pyright does not understand AntaTest.Input typing
# pyright: reportAttributeAccessIssue=false
from __future__ import annotations

from typing import ClassVar

from anta.decorators import skip_on_platforms
from anta.input_models.path_selection import DpsPath
from anta.models import AntaCommand, AntaTemplate, AntaTest
from anta.result_manager.models import AntaTestStatus
from anta.tools import get_value


class VerifyPathsHealth(AntaTest):
    """Verifies the path and telemetry state of all paths under router path-selection.

    The expected states are 'IPsec established', 'Resolved' for path and 'active' for telemetry.

    Expected Results
    ----------------
    * Success: The test will pass if all path states under router path-selection are either 'IPsec established' or 'Resolved'
               and their telemetry state as 'active'.
    * Failure: The test will fail if router path-selection is not configured or if any path state is not 'IPsec established' or 'Resolved',
               or the telemetry state is 'inactive'.

    Examples
    --------
    ```yaml
    anta.tests.path_selection:
      - VerifyPathsHealth:
    ```
    """

    categories: ClassVar[list[str]] = ["path-selection"]
    commands: ClassVar[list[AntaCommand | AntaTemplate]] = [AntaCommand(command="show path-selection paths", revision=1)]

    @skip_on_platforms(["cEOSLab", "vEOS-lab"])
    @AntaTest.anta_test
    def test(self) -> None:
        """Main test function for VerifyPathsHealth."""
        self.result.is_success()

        command_output = self.instance_commands[0].json_output["dpsPeers"]

        # If no paths are configured for router path-selection, the test fails
        if not command_output:
            self.result.is_failure("No path configured for router path-selection")
            return

        # Check the state of each path
        for peer, peer_data in command_output.items():
            for group, group_data in peer_data["dpsGroups"].items():
                for path_data in group_data["dpsPaths"].values():
                    path_state = path_data["state"]
                    session = path_data["dpsSessions"]["0"]["active"]

                    # If the path state of any path is not 'ipsecEstablished' or 'routeResolved', the test fails
                    expected_state = ["ipsecEstablished", "routeResolved"]
                    if path_state not in expected_state:
                        self.result.is_failure(f"Peer: {peer} Path Group: {group} - Invalid path state - Expected: {', '.join(expected_state)} Actual: {path_state}")

                    # If the telemetry state of any path is inactive, the test fails
                    elif not session:
                        self.result.is_failure(f"Peer: {peer} Path Group {group} - Telemetry state inactive")


class VerifySpecificPath(AntaTest):
    """Verifies the DPS path and telemetry state of an IPv4 peer.

    This test performs the following checks:

      1. Verifies that the specified peer is configured.
      2. Verifies that the specified path group is found.
      3. For each specified DPS path:
         - Verifies that the expected source and destination address matches the expected.
         - Verifies that the state is `ipsecEstablished` or `routeResolved`.
         - Verifies that the telemetry state is `active`.

    Expected Results
    ----------------
    * Success: The test will pass if the path state under router path-selection is either 'IPsecEstablished' or 'Resolved'
               and telemetry state as 'active'.
    * Failure: The test will fail if router path selection or the peer is not configured or if the path state is not 'IPsec established' or 'Resolved',
               or the telemetry state is 'inactive'.

    Examples
    --------
    ```yaml
    anta.tests.path_selection:
      - VerifySpecificPath:
          paths:
            - peer: 10.255.0.1
              path_group: internet
              source_address: 100.64.3.2
              destination_address: 100.64.1.2
    ```
    """

    categories: ClassVar[list[str]] = ["path-selection"]
    commands: ClassVar[list[AntaCommand | AntaTemplate]] = [AntaCommand(command="show path-selection paths", revision=1)]
    _atomic_support: ClassVar[bool] = True

    class Input(AntaTest.Input):
        """Input model for the VerifySpecificPath test."""

        paths: list[DpsPath]
        """List of router paths to verify."""
        RouterPath: ClassVar[type[DpsPath]] = DpsPath
        """To maintain backward compatibility."""

    @skip_on_platforms(["cEOSLab", "vEOS-lab"])
    @AntaTest.anta_test
    def test(self) -> None:
        """Main test function for VerifySpecificPath."""
        self.result.is_success()

        command_output = self.instance_commands[0].json_output

        # If the dpsPeers details are not found in the command output, the test fails.
        if not (dps_peers_details := get_value(command_output, "dpsPeers")):
            self.result.is_failure("Router path-selection not configured")
            return

        # Iterating on each DPS peer mentioned in the inputs.
        for dps_path in self.inputs.paths:
            peer = str(dps_path.peer)
            peer_details = dps_peers_details.get(peer, {})

            # Atomic result
            result = self.result.add(description=str(dps_path), status=AntaTestStatus.SUCCESS)

            # If the peer is not configured for the path group, the test fails
            if not peer_details:
                result.is_failure("Peer not found")
                continue

            path_group = dps_path.path_group
            source = str(dps_path.source_address)
            destination = str(dps_path.destination_address)
            path_group_details = get_value(peer_details, f"dpsGroups..{path_group}..dpsPaths", separator="..")
            # If the expected path group is not found for the peer, the test fails.
            if not path_group_details:
                result.is_failure("No DPS path found for this peer and path group")
                continue

            path_data = next((path for path in path_group_details.values() if (path.get("source") == source and path.get("destination") == destination)), None)
            #  Source and destination address do not match, the test fails.
            if not path_data:
                result.is_failure("No path matching the source and destination found")
                continue

            path_state = path_data.get("state")
            session = get_value(path_data, "dpsSessions.0.active")

            # If the state of the path is not 'ipsecEstablished' or 'routeResolved', or the telemetry state is 'inactive', the test fails
            if path_state not in ["ipsecEstablished", "routeResolved"]:
                result.is_failure(f"Invalid state path - Expected: ipsecEstablished, routeResolved Actual: {path_state}")
            elif not session:
                result.is_failure("Telemetry state inactive for this path")
