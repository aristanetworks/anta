"""
Filters to be used with AntaTestFilter
"""
from typing import Any, Dict, List, cast

from anta.inventory.models import InventoryDevice
from anta.models import AntaTestCommand, AntaTestFilter
from anta.result_manager.models import TestResult


class SkipPlatformsFilter(AntaTestFilter):
    """
    Skip the test for specific platforms.
    """

    # pylint: disable=too-few-public-methods
    def __init__(self, platforms_to_skip: List[str]) -> None:
        """
        Class initialization with a list of platform to skip.
        """
        self.platforms_to_skip = platforms_to_skip

    def sync_should_skip(self, device: InventoryDevice, result: TestResult) -> bool:
        if device.hw_model in self.platforms_to_skip:
            result.is_skipped(f"{result.test} test is not supported on {device.hw_model}.")
            return True
        return False

    async def async_should_skip(self, device: InventoryDevice, result: TestResult) -> bool:
        if device.hw_model in self.platforms_to_skip:
            result.is_skipped(f"{result.test} test is not supported on {device.hw_model}.")
            return True
        return False


class SkipBGPFilter(AntaTestFilter):
    """
    Skip the test if an address family is not configured or has no peer.
    """

    # pylint: disable=too-few-public-methods
    def __init__(self, family: str) -> None:
        """
        Class initialization with the BGP address family to verify.
        """
        self.family = family

    def sync_should_skip(self, device: InventoryDevice, result: TestResult) -> bool:
        if self.family == "ipv4":
            command = AntaTestCommand(command="show bgp ipv4 unicast summary vrf all")
        elif self.family == "ipv6":
            command = AntaTestCommand(command="show bgp ipv6 unicast summary vrf all")
        elif self.family == "evpn":
            command = AntaTestCommand(command="show bgp evpn summary")
        elif self.family == "rtc":
            command = AntaTestCommand(command="show bgp rt-membership summary")
        else:
            result.is_error(f"Wrong address family initialized with {self.__class__.__name__} : {self.family}.")
            return True

        device.sync_collect(command=command)

        command_output = cast(Dict[str, Any], command.output)

        if "vrfs" not in command_output:
            result.is_skipped(f"No BGP configuration for {self.family} on this device")
            return True
        if len(bgp_vrfs := command_output["vrfs"]) == 0 or len(bgp_vrfs["default"]["peers"]) == 0:
            # No VRF
            result.is_skipped(f"No {self.family} peer on this device.")
            return True
        return False

    async def async_should_skip(self, device: InventoryDevice, result: TestResult) -> bool:
        if self.family == "ipv4":
            command = AntaTestCommand(command="show bgp ipv4 unicast summary vrf all")
        elif self.family == "ipv6":
            command = AntaTestCommand(command="show bgp ipv6 unicast summary vrf all")
        elif self.family == "evpn":
            command = AntaTestCommand(command="show bgp evpn summary")
        elif self.family == "rtc":
            command = AntaTestCommand(command="show bgp rt-membership summary")
        else:
            result.is_error(f"Wrong address family initialized with {self.__class__.__name__} : {self.family}.")
            return True

        await device.async_collect(command=command)

        command_output = cast(Dict[str, Any], command.output)

        if "vrfs" not in command_output:
            result.is_skipped(f"No BGP configuration for {self.family} on this device")
            return True
        if len(bgp_vrfs := command_output["vrfs"]) == 0 or len(bgp_vrfs["default"]["peers"]) == 0:
            # No VRF
            result.is_skipped(f"No {self.family} peer on this device.")
            return True
        return False
