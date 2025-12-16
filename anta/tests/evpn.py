# Copyright (c) 2023-2025 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Module related to EVPN tests."""

# Pyright does not understand AntaTest.Input typing
# pyright: reportAttributeAccessIssue=false
from __future__ import annotations

from typing import Any, ClassVar

from anta.input_models.evpn import EVPNPath, EVPNRoute, EVPNType5Prefix
from anta.models import AntaCommand, AntaTemplate, AntaTest


class VerifyEVPNType5Routes(AntaTest):
    """Verifies EVPN Type-5 routes for given IP prefixes and VNIs.

    It supports multiple levels of verification based on the provided input:

    1.  **Prefix/VNI only:** Verifies there is at least one 'active' and 'valid' path across all
        Route Distinguishers (RDs) learning the given prefix and VNI.
    2.  **Specific Routes (RD/Domain):** Verifies that routes matching the specified RDs and domains
        exist for the prefix/VNI. For each specified route, it checks if at least one of its paths
        is 'active' and 'valid'.
    3.  **Specific Paths (Nexthop/Route Targets):** Verifies that specific paths exist within a
        specified route (RD/Domain). For each specified path criteria (nexthop and optional route targets),
        it finds all matching paths received from the peer and checks if at least one of these
        matching paths is 'active' and 'valid'. The route targets check ensures all specified RTs
        are present in the path's extended communities (subset check).

    Expected Results
    ----------------
    * Success:
        - If only prefix/VNI is provided: The prefix/VNI exists in the EVPN table
          and has at least one active and valid path across all RDs.
        - If specific routes are provided: All specified routes (by RD/Domain) are found,
          and each has at least one active and valid path (if paths are not specified for the route).
        - If specific paths are provided: All specified routes are found, and for each specified path criteria (nexthop/RTs),
          at least one matching path exists and is active and valid.
    * Failure:
        - No EVPN Type-5 routes are found for the given prefix/VNI.
        - A specified route (RD/Domain) is not found.
        - No active and valid path is found when required (either globally for the prefix, per specified route, or per specified path criteria).
        - A specified path criteria (nexthop/RTs) does not match any received paths for the route.

    Examples
    --------
    ```yaml
    anta.tests.evpn:
      - VerifyEVPNType5Routes:
          prefixes:
            # At least one active/valid path across all RDs
            - address: 192.168.10.0/24
              vni: 10
            # Specific routes each has at least one active/valid path
            - address: 192.168.20.0/24
              vni: 20
              routes:
                - rd: "10.0.0.1:20"
                  domain: local
                - rd: "10.0.0.2:20"
                  domain: remote
            # At least one active/valid path matching the nexthop
            - address: 192.168.30.0/24
              vni: 30
              routes:
                - rd: "10.0.0.1:30"
                  domain: local
                  paths:
                    - nexthop: 10.1.1.1
            # At least one active/valid path matching nexthop and specific RTs
            - address: 192.168.40.0/24
              vni: 40
              routes:
                - rd: "10.0.0.1:40"
                  domain: local
                  paths:
                    - nexthop: 10.1.1.1
                      route_targets:
                        - "40:40"
    ```
    """

    categories: ClassVar[list[str]] = ["bgp"]
    commands: ClassVar[list[AntaCommand | AntaTemplate]] = [AntaTemplate(template="show bgp evpn route-type ip-prefix {address} vni {vni}", revision=2)]

    class Input(AntaTest.Input):
        """Input model for the VerifyEVPNType5Routes test."""

        prefixes: list[EVPNType5Prefix]
        """List of EVPN Type-5 prefixes to verify."""

    def render(self, template: AntaTemplate) -> list[AntaCommand]:
        """Render the template for each EVPN Type-5 prefix in the input list."""
        return [template.render(address=str(prefix.address), vni=prefix.vni) for prefix in self.inputs.prefixes]

    # NOTE: The following static methods can be moved at the module level if needed for other EVPN tests
    @staticmethod
    def _get_all_paths(evpn_routes_data: dict[str, Any]) -> list[dict[str, Any]]:
        """Extract all 'evpnRoutePaths' from the entire 'evpnRoutes' dictionary."""
        all_paths = []
        for route_data in evpn_routes_data.values():
            all_paths.extend(route_data["evpnRoutePaths"])
        return all_paths

    @staticmethod
    def _find_route(evpn_routes_data: dict[str, Any], rd_to_find: str, domain_to_find: str) -> dict[str, Any] | None:
        """Find the specific route block for a given RD and domain."""
        for route_data in evpn_routes_data.values():
            if route_data["routeKeyDetail"].get("rd") == rd_to_find and route_data["routeKeyDetail"].get("domain") == domain_to_find:
                return route_data
        return None

    @staticmethod
    def _find_paths(paths: list[dict[str, Any]], nexthop: str, route_targets: list[str] | None = None) -> list[dict[str, Any]]:
        """Find all matching paths for a given nexthop and RTs."""
        route_targets = [f"Route-Target-AS:{rt}" for rt in route_targets] if route_targets is not None else []
        return [path for path in paths if path["nextHop"] == nexthop and set(route_targets).issubset(set(path["routeDetail"]["extCommunities"]))]

    @staticmethod
    def _has_active_valid_path(paths: list[dict[str, Any]]) -> bool:
        """Check if any path in the list is active and valid."""
        return any(path["routeType"]["active"] and path["routeType"]["valid"] for path in paths)

    @AntaTest.anta_test
    def test(self) -> None:
        """Main test function for VerifyEVPNType5Routes."""
        self.result.is_success()

        for command, prefix_input in zip(self.instance_commands, self.inputs.prefixes, strict=False):
            # Verify that the prefix is in the BGP EVPN table
            evpn_routes_data = command.json_output.get("evpnRoutes")
            if not evpn_routes_data:
                self.result.is_failure(f"{prefix_input} - No EVPN Type-5 routes found")
                continue

            # Delegate verification logic for this prefix
            self._verify_routes_for_prefix(prefix_input, evpn_routes_data)

    def _verify_routes_for_prefix(self, prefix_input: EVPNType5Prefix, evpn_routes_data: dict[str, Any]) -> None:
        """Verify EVPN routes for an input prefix."""
        # Case: routes not provided for the prefix, check that at least one EVPN Type-5 route
        # has at least one active and valid path across all learned routes from all RDs combined
        if prefix_input.routes is None:
            all_paths = self._get_all_paths(evpn_routes_data)
            if not self._has_active_valid_path(all_paths):
                self.result.is_failure(f"{prefix_input} - No active and valid path found across all RDs")
            return

        # Case: routes *is* provided, check each specified route
        for route_input in prefix_input.routes:
            # Try to find a route with matching RD and domain
            route_data = self._find_route(evpn_routes_data, route_input.rd, route_input.domain)
            if route_data is None:
                self.result.is_failure(f"{prefix_input} {route_input} - Route not found")
                continue

            # Route found, now check its paths based on route_input criteria
            self._verify_paths_for_route(prefix_input, route_input, route_data)

    def _verify_paths_for_route(self, prefix_input: EVPNType5Prefix, route_input: EVPNRoute, route_data: dict[str, Any]) -> None:
        """Verify paths for a specific EVPN route (route_data) based on route_input criteria."""
        route_paths = route_data["evpnRoutePaths"]

        # Case: paths not provided for the route, check that at least one path is active/valid
        if route_input.paths is None:
            if not self._has_active_valid_path(route_paths):
                self.result.is_failure(f"{prefix_input} {route_input} - No active and valid path found")
            return

        # Case: paths *is* provided, check each specified path criteria
        for path_input in route_input.paths:
            self._verify_single_path(prefix_input, route_input, path_input, route_paths)

    def _verify_single_path(self, prefix_input: EVPNType5Prefix, route_input: EVPNRoute, path_input: EVPNPath, available_paths: list[dict[str, Any]]) -> None:
        """Verify if at least one active/valid path exists among available_paths matching the path_input criteria."""
        # Try to find all paths matching nexthop and RTs criteria from the available paths for this route
        matching_paths = self._find_paths(available_paths, path_input.nexthop, path_input.route_targets)
        if not matching_paths:
            self.result.is_failure(f"{prefix_input} {route_input} {path_input} - Path not found")
            return

        # Check that at least one matching path is active/valid
        if not self._has_active_valid_path(matching_paths):
            self.result.is_failure(f"{prefix_input} {route_input} {path_input} - No active and valid path found")
