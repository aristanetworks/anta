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
    Verifies the state of all paths under router path-selection as ipsecEstablished.

    Expected Results
    ----------------
    * Success: The test will pass if all the paths under router path-selection are ipsecEstablished.
    * Failure: The test will fail if router path-selection is not configured or any path's state is not ipsecEstablished.

    Examples
    --------
    ```yaml
    anta.tests.path_selection:
      - VerifyRouterPathsHealth:
    ```
    """

    name = "VerifyRouterPathsHealth"
    description = "Verifies the state of all paths under router path-selection as ipsecEstablished."
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
        failed_log = ""
        for peer, peer_data in command_output.items():
            for group, group_data in peer_data["dpsGroups"].items():
                for path_data in group_data["dpsPaths"].values():
                    state = path_data["state"]

                    # If the state of any path is not 'ipsecEstablished', the test fails
                    if state != "ipsecEstablished":
                        failed_log += f"\nPeer {peer} in group {group} is `{state}`."
        if failed_log:
            self.result.is_failure(f"State of following peers is not `ipsecEstablished`:{failed_log}")


class VerifySpecificRouterPath(AntaTest):
    """
    Verifies the state of a specific path under router path-selection for an IPv4 peer as ipsecEstablished.

    Expected Results
    ----------------
    * Success: The test will pass if the input path under router path-selection is ipsecEstablished.
    * Failure: The test will fail if the input path is not found or its state is not ipsecEstablished.

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
    description = "Verifies the state of a specific path under router path-selection for an IPv4 peer as ipsecEstablished."
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
            command_output = command.json_output["dpsPeers"]

            # If the peer is not configured for the path group, the test fails
            if not command_output:
                self.result.is_failure(f"Peer `{peer}` is not configured for path group `{path_group}`.")
                continue

            # Extract the state of the path
            path_output = get_value(command_output, f"{peer}..dpsGroups..{path_group}..dpsPaths", separator="..")
            state = next(iter(path_output.values())).get("state")

            # If the state of the path is not 'ipsecEstablished', the test fails
            if state != "ipsecEstablished":
                self.result.is_failure(f"Peer {peer} in group {path_group} is `{state}`.")
