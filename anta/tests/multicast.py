"""
Test functions related to multicast
"""

from typing import List, Optional

from anta.models import AntaCommand, AntaTest


class VerifyIGMPSnoopingVlans(AntaTest):
    """
    Verifies the IGMP snooping configuration for some VLANs.

    Args:
        vlans (List[str]): A list of VLANs
        configuration (str): Expected IGMP snooping configuration (enabled or disabled) for these VLANs.
    """

    name = "VerifyIGMPSnoopingVlans"
    description = "Verifies the IGMP snooping configuration for some VLANs."
    categories = ["multicast", "igmp"]
    commands = [AntaCommand(command="show ip igmp snooping")]

    @AntaTest.anta_test
    def test(self, vlans: Optional[List[str]] = None, configuration: Optional[str] = None) -> None:
        """
        Run VerifyIGMPSnoopingVlans validation

        Args:
            vlans: List of VLANs.
            configuration: Expected IGMP configuration (enabled or disabled) for these VLANs.
        """

        if not vlans or not configuration:
            self.result.is_skipped("VerifyIGMPSnoopingVlans was not run as no vlans or configuration was given")
            return
        if configuration not in ["enabled", "disabled"]:
            self.result.is_error(f"VerifyIGMPSnoopingVlans was not run as 'configuration': {configuration} is not in the allowed values: ['enabled', 'disabled'])")
            return

        command_output = self.instance_commands[0].json_output

        self.result.is_success()
        for vlan in vlans:
            if vlan not in command_output["vlans"]:
                self.result.is_failure(f"Supplied vlan {vlan} is not present on the device.")
                continue

            igmp_state = command_output["vlans"][str(vlan)]["igmpSnoopingState"]
            if igmp_state != configuration:
                self.result.is_failure(f"IGMP state for vlan {vlan} is {igmp_state}")


class VerifyIGMPSnoopingGlobal(AntaTest):
    """
    Verifies the IGMP snooping global configuration.

    Args:
        configuration (str): Expected global IGMP snooping configuration (enabled or disabled).
    """

    name = "VerifyIGMPSnoopingGlobal"
    description = "Verifies the IGMP snooping global configuration."
    categories = ["multicast", "igmp"]
    commands = [AntaCommand(command="show ip igmp snooping")]

    @AntaTest.anta_test
    def test(self, configuration: Optional[str] = None) -> None:
        """
        Run VerifyIGMPSnoopingGlobal validation

        Args:
            configuration: Expected global IGMP configuration (enabled or disabled).
        """

        if not configuration:
            self.result.is_skipped("VerifyIGMPSnoopingGlobal was not run as no configuration was given")
            return

        if configuration not in ["enabled", "disabled"]:
            self.result.is_error(f"VerifyIGMPSnoopingGlobal was not run as 'configuration': {configuration} is not in the allowed values: ['enabled', 'disabled'])")
            return

        command_output = self.instance_commands[0].json_output

        self.result.is_success()
        if (igmp_state := command_output["igmpSnoopingState"]) != configuration:
            self.result.is_failure(f"IGMP state is not valid: {igmp_state}")
