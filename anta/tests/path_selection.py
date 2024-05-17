# Copyright (c) 2023-2024 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Test functions related to various router path-selection settings."""

# Mypy does not understand AntaTest.Input typing
# mypy: disable-error-code=attr-defined
from __future__ import annotations

from ipaddress import IPv4Address
from typing import ClassVar

from pydantic import BaseModel

from anta.decorators import skip_on_platforms
from anta.models import AntaCommand, AntaTemplate, AntaTest
from anta.tools import get_value


class VerifyPathsHealth(AntaTest):
    """
    Verifies the path and telemetry state of all paths under router path-selection.

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

    name = "VerifyPathsHealth"
    description = "Verifies the path and telemetry state of all paths under router path-selection."
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
    """
    Verifies the path and telemetry state of a specific path for an IPv4 peer under router path-selection.

    The expected states are 'IPsec established', 'Resolved' for path and 'active' for telemetry.

    Expected Results
    ----------------
    * Success: The test will pass if the path state under router path-selection is either 'IPsec established' or 'Resolved'
               and telemetry state as 'active'.
    * Failure: The test will fail if router path-selection is not configured or if the path state is not 'IPsec established' or 'Resolved',
               or if the telemetry state is 'inactive'.

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

    name = "VerifySpecificPath"
    description = "Verifies the path and telemetry state of a specific path under router path-selection."
    categories: ClassVar[list[str]] = ["path-selection"]
    commands: ClassVar[list[AntaCommand | AntaTemplate]] = [
        AntaTemplate(template="show path-selection paths peer {peer} path-group {group} source {source} destination {destination}", revision=1)
    ]

    class Input(AntaTest.Input):
        """Input model for the VerifySpecificPath test."""

        paths: list[RouterPath]
        """List of router paths to verify."""

        class RouterPath(BaseModel):
            """Detail of a router path."""

            peer: IPv4Address
            """Static peer IPv4 address."""

            path_group: str
            """Router path group name."""

            source_address: IPv4Address
            """Source IPv4 address of path."""

            destination_address: IPv4Address
            """Destination IPv4 address of path."""

    def render(self, template: AntaTemplate) -> list[AntaCommand]:
        """Render the template for each router path."""
        return [
            template.render(peer=path.peer, group=path.path_group, source=path.source_address, destination=path.destination_address) for path in self.inputs.paths
        ]

    @skip_on_platforms(["cEOSLab", "vEOS-lab"])
    @AntaTest.anta_test
    def test(self) -> None:
        """Main test function for VerifySpecificPath."""
        self.result.is_success()

        # Check the state of each path
        for command in self.instance_commands:
            peer = command.params.peer
            path_group = command.params.group
            source = command.params.source
            destination = command.params.destination
            command_output = command.json_output.get("dpsPeers", [])

            # If the peer is not configured for the path group, the test fails
            if not command_output:
                self.result.is_failure(f"Path `peer: {peer} source: {source} destination: {destination}` is not configured for path-group `{path_group}`.")
                continue

            # Extract the state of the path
            path_output = get_value(command_output, f"{peer}..dpsGroups..{path_group}..dpsPaths", separator="..")
            path_state = next(iter(path_output.values())).get("state")
            session = get_value(next(iter(path_output.values())), "dpsSessions.0.active")

            # If the state of the path is not 'ipsecEstablished' or 'routeResolved', or the telemetry state is 'inactive', the test fails
            if path_state not in ["ipsecEstablished", "routeResolved"]:
                self.result.is_failure(f"Path state for `peer: {peer} source: {source} destination: {destination}` in path-group {path_group} is `{path_state}`.")
            elif not session:
                self.result.is_failure(
                    f"Telemetry state for path `peer: {peer} source: {source} destination: {destination}` in path-group {path_group} is `inactive`."
                )
