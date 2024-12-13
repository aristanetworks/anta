# Copyright (c) 2023-2025 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Test functions related to various router path-selection settings."""

# Mypy does not understand AntaTest.Input typing
# mypy: disable-error-code=attr-defined
from __future__ import annotations

from typing import ClassVar

from anta.decorators import skip_on_platforms
from anta.input_models.path_selection import RouterPath
from anta.models import AntaCommand, AntaTemplate, AntaTest
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
            self.result.is_failure("No path configured for router path-selection.")
            return

        # Check the state of each path
        for peer, peer_data in command_output.items():
            for group, group_data in peer_data["dpsGroups"].items():
                for path_data in group_data["dpsPaths"].values():
                    path_state = path_data["state"]
                    session = path_data["dpsSessions"]["0"]["active"]

                    # If the path state of any path is not 'ipsecEstablished' or 'routeResolved', the test fails
                    if path_state not in ["ipsecEstablished", "routeResolved"]:
                        self.result.is_failure(f"Path state for peer {peer} in path-group {group} is `{path_state}`.")

                    # If the telemetry state of any path is inactive, the test fails
                    elif not session:
                        self.result.is_failure(f"Telemetry state for peer {peer} in path-group {group} is `inactive`.")


class VerifySpecificPath(AntaTest):
    """Verifies the path and telemetry state of a specific path for an IPv4 peer.

    This test performs the following checks for each specified routerpath:
        1. Verifies that the specified peer is configured.
        2. Verifies that the specified path group is found.
        3. Verifies that the expected source and destination address match the path group.
        4. Verifies that the state of the path is `ipsecEstablished` or `routeResolved`.
        5. Verifies that the telemetry state is `active`.

    Expected Results
    ----------------
    * Success: The test will pass if the path state under router path selection is either 'IPsecEstablished' or 'Resolved'
               and telemetry state as 'active'.
    * Failure: The test will fail if router path selection is not configured, the path state is not 'IPsec established' or 'Resolved',
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

    class Input(AntaTest.Input):
        """Input model for the VerifySpecificPath test."""

        paths: list[RouterPath]
        """List of router paths to verify."""
        RouterPath: ClassVar[type[RouterPath]] = RouterPath

    @skip_on_platforms(["cEOSLab", "vEOS-lab"])
    @AntaTest.anta_test
    def test(self) -> None:
        """Main test function for VerifySpecificPath."""
        self.result.is_success()

        command_output = self.instance_commands[0].json_output

        # If the dpsPeers details are not found in the command output, the test fails.
        if not (dps_peers_details := get_value(command_output, "dpsPeers")):
            self.result.is_failure("Router path not configured")
            return

        # Iterating on each router path mentioned in the inputs.
        for router_path in self.inputs.paths:
            peer = str(router_path.peer)
            path_group = router_path.path_group
            source = str(router_path.source_address)
            destination = str(router_path.destination_address)
            peer_details = dps_peers_details.get(peer, {})

            # If the peer is not configured for the path group, the test fails
            if not peer_details:
                self.result.is_failure(f"{router_path} - Peer not found")
                continue

            path_group_details = get_value(peer_details, f"dpsGroups..{path_group}..dpsPaths", separator="..")
            # If the expected pathgroup is not found for the peer, the test fails.
            if not path_group_details:
                self.result.is_failure(f"{router_path} - Path-group not found")
                continue

            path_data = next((path for path in path_group_details.values() if (path.get("source") == source and path.get("destination") == destination)), None)
            # If the expected and actual source and destion address of the pathgroup are not matched, test fails.
            if not path_data:
                self.result.is_failure(f"{router_path} - Source and/or Destination address not found")
                continue

            path_state = path_data.get("state")
            session = get_value(path_data, "dpsSessions.0.active")
            expected_state = ["ipsecEstablished", "routeResolved"]
            # If the state of the path is not 'ipsecEstablished' or 'routeResolved', or the telemetry state is 'inactive', the test fails
            if path_state not in expected_state:
                self.result.is_failure(f"{router_path} - Incorrect path state - Expected: {' or '.join(expected_state)} Actual: {path_state}")
            elif not session:
                self.result.is_failure(f"{router_path} - Incorrect telemetry state - Expected: active Actual: inactive")
