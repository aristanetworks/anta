class VerifyISISSegmentRoutingTunnels(AntaTest):
    """
    Verify ISIS-SR tunnels computed by device.

    Expected Results
    ----------------
    * Success: The test will pass if all listed tunnels are computed on device.
    * Failure: The test will fail if one of the listed tunnels is missing.
    * Skipped: The test will be skipped if ISIS-SR is not configured.

    Examples
    --------
    ```yaml
    anta.tests.routing:
    isis:
        - VerifyISISSegmentRoutingTunnels:
            entries:
              # Check only endpoint
              - endpoint: 1.0.0.122/32
              # Check endpoint and via TI-LFA
              - endpoint: 1.0.0.13/32
                vias:
                  - type: tunnel
                    tunnel_id: ti-lfa
              # Check endpoint and via IP routers
              - endpoint: 1.0.0.14/32
                vias:
                  - type: ip
                    nexthop: 1.1.1.1
    ```
    """

    name = "VerifyISISSegmentRoutingTunnels"
    description = "Verify ISIS-SR tunnels computed by device"
    categories: ClassVar[list[str]] = ["isis", "segment-routing"]
    commands: ClassVar[list[AntaCommand | AntaTemplate]] = [AntaCommand(command="show isis segment-routing tunnel", ofmt="json")]

    class Input(AntaTest.Input):
        """Input model for the VerifyISISSegmentRoutingTunnels test."""

        entries: list[Entry]
        """List of tunnels to check on device."""

        class Entry(BaseModel):
            """Definition of a tunnel entry."""

            endpoint: IPv4Network
            """Endpoint IP of the tunnel."""
            vias: list[Vias] | None = None
            """Optional list of path to reach endpoint."""

            class Vias(BaseModel):
                """Definition of a tunnel path."""

                nexthop: IPv4Address | None = None
                """Nexthop of the tunnel. If None, then it is not tested. Default: None"""
                type: Literal["ip", "tunnel"] | None = None
                """Type of the tunnel. If None, then it is not tested. Default: None"""
                interface: Interface | None = None
                """Interface of the tunnel. If None, then it is not tested. Default: None"""
                tunnel_id: Literal["TI-LFA", "ti-lfa", "unset"] | None = None
                """Computation method of the tunnel. If None, then it is not tested. Default: None"""

    def _eos_entry_lookup(self, search_value: IPv4Network, entries: dict[str, Any], search_key: str = "endpoint") -> dict[str, Any] | None:
        return next(
            (entry_value for entry_id, entry_value in entries.items() if str(entry_value[search_key]) == str(search_value)),
            None,
        )

    @AntaTest.anta_test
    def test(self) -> None:
        """Main test function for VerifyISISSegmentRoutingTunnels.

        This method performs the main test logic for verifying ISIS Segment Routing tunnels.
        It checks the command output, initiates defaults, and performs various checks on the tunnels.
        """
        command_output = self.instance_commands[0].json_output
        self.result.is_success()

        # initiate defaults
        failure_message = []

        if len(command_output["entries"]) == 0:
            self.result.is_skipped("IS-IS-SR is not running on device.")
            return

        for input_entry in self.inputs.entries:
            eos_entry = self._eos_entry_lookup(search_value=input_entry.endpoint, entries=command_output["entries"])
            if eos_entry is None:
                failure_message.append(f"Tunnel to {input_entry.endpoint!s} is not found.")
            elif input_entry.vias is not None:
                for via_input in input_entry.vias:
                    via_search_result = any(self._via_matches(via_input, eos_via) for eos_via in eos_entry["vias"])
                    if not via_search_result:
                        failure_message.append(f"Tunnel to {input_entry.endpoint!s} is incorrect.")
                        if "pytest" not in sys.modules:
                            failure_message.append(f"Expected: {via_input} - Found: {eos_entry['vias']}.")

        if failure_message:
            self.result.is_failure("\n".join(failure_message))

    def _via_matches(self, via_input: VerifyISISSegmentRoutingTunnels.Input.Entry.Vias, eos_via: dict[str, Any]) -> bool:
        """
        Check if the via input matches the eos via.

        Parameters
        ----------
        via_input : VerifyISISSegmentRoutingTunnels.Input.Entry.Vias
            The input via to check.
        eos_via : dict[str, Any]
            The EOS via to compare against.

        Returns
        -------
        bool
            True if the via input matches the eos via, False otherwise.
        """
        return (
            (via_input.type is None or via_input.type == eos_via.get("type"))
            and (via_input.nexthop is None or str(via_input.nexthop) == eos_via.get("nexthop"))
            and (via_input.interface is None or via_input.interface == eos_via.get("interface"))
            and (via_input.tunnel_id is None or via_input.tunnel_id.upper() == eos_via.get("tunnelId", {}).get("type", "").upper())
        )
