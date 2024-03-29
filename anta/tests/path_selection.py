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

from anta.models import AntaCommand, AntaTemplate, AntaTest
from anta.tools.get_value import get_value


class VerifyRouterPathsHealth(AntaTest):
    """
    Verifies the route and telemetry state of all paths under router path-selection.

    The expected states are 'IPsec established', 'Resolved' for route and 'active' for telemetry.

    Expected Results
    ----------------
    * Success: The test will pass if all paths under router path-selection have their route state as either 'IPsec established' or 'Resolved'
               and their telemetry state as 'active'.
    * Failure: The test will fail if router path-selection is not configured, any path's route state is not 'IPsec established' or 'Resolved',
               or the telemetry state is 'inactive'.

    Examples
    --------
    ```yaml
    anta.tests.path_selection:
      - VerifyRouterPathsHealth:
    ```
    """

    name = "VerifyRouterPathsHealth"
    description = "Verifies the route and telemetry state of all paths under router path-selection."
    categories: ClassVar[list[str]] = ["path-selection"]
    commands: ClassVar[list[AntaCommand | AntaTemplate]] = [AntaCommand(command="show path-selection paths")]

    @AntaTest.anta_test
    def test(self) -> None:
        """Main test function for VerifyRouterPathsHealth."""
        self.result.is_success()

        command_output = self.instance_commands[0].json_output["dpsPeers"]

        # If no paths are configured for router path-selection, the test fails
        if not command_output:
            self.result.is_failure("No paths are configured for router path-selection.")
            return

        # Check the state of each path
        for peer, peer_data in command_output.items():
            for group, group_data in peer_data["dpsGroups"].items():
                for path_data in group_data["dpsPaths"].values():
                    route_state = path_data["state"]
                    session = path_data["dpsSessions"]["0"]["active"]

                    # If the route state of any path is not 'ipsecEstablished' or 'routeResolved', the test fails
                    if route_state not in ["ipsecEstablished", "routeResolved"]:
                        self.result.is_failure(f"Route state for peer {peer} in group {group} is `{route_state}`.")

                    # If the telemetry state of any path is inactive, the test fails
                    elif not session:
                        self.result.is_failure(f"Telemetry state for peer {peer} in group {group} is `inactive`.")


class VerifySpecificRouterPath(AntaTest):
    """
    Verifies the route and telemetry state of a specific path for an IPv4 peer under router path-selection.

    The expected states are 'IPsec established', 'Resolved' for route and 'active' for telemetry.

    Expected Results
    ----------------
    * Success: The test will pass if the path under router path-selection has its route state as either 'IPsec established' or 'Resolved'
               and telemetry state as 'active'.
    * Failure: The test will fail if router path-selection is not configured, the path's route state is not 'IPsec established' or 'Resolved',
               or the telemetry state is 'inactive'.

    Examples
    --------
    ```yaml
    anta.tests.path_selection:
      - VerifySpecificRouterPath:
          paths:
            - peer: 10.255.0.1
              path_groups:
                - internet
                - mpls
    ```
    """

    name = "VerifySpecificRouterPath"
    description = "Verifies the route and telemetry state of a specific path under router path-selection."
    categories: ClassVar[list[str]] = ["path-selection"]
    commands: ClassVar[list[AntaCommand | AntaTemplate]] = [AntaTemplate(template="show path-selection paths peer {peer} path-group {group}")]

    class Input(AntaTest.Input):
        """Input model for the VerifySpecificRouterPath test."""

        paths: list[RouterPath]
        """List of router paths to verify."""

        class RouterPath(BaseModel):
            """Detail of a router path."""

            peer: IPv4Address
            """Static peer IPv4 address."""

            path_groups: list[str]
            """Router path group names."""

    def render(self, template: AntaTemplate) -> list[AntaCommand]:
        """Render the template for each router path."""
        return [template.render(peer=path.peer, group=path_group) for path in self.inputs.paths for path_group in path.path_groups]

    @AntaTest.anta_test
    def test(self) -> None:
        """Main test function for VerifySpecificRouterPath."""
        self.result.is_success()

        # Check the state of each path
        for command in self.instance_commands:
            peer = str(command.params["peer"])
            path_group = command.params["group"]
            command_output = command.json_output.get("dpsPeers", [])

            # If the peer is not configured for the path group, the test fails
            if not command_output:
                self.result.is_failure(f"Peer `{peer}` is not configured for path group `{path_group}`.")
                continue

            # Extract the state of the path
            path_output = get_value(command_output, f"{peer}..dpsGroups..{path_group}..dpsPaths", separator="..")
            state = next(iter(path_output.values())).get("state")
            session = get_value(next(iter(path_output.values())), "dpsSessions.0.active")

            # If the state of the path is not 'ipsecEstablished' or 'routeResolved', or the telemetry state is 'inactive', the test fails
            if state not in ["ipsecEstablished", "routeResolved"]:
                self.result.is_failure(f"Route state for peer {peer} in group {path_group} is `{state}`.")
            elif not session:
                self.result.is_failure(f"Telemetry state for peer {peer} in group {path_group} is `inactive`.")
