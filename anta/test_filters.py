"""
Filters to be used with AntaTestFilter
"""
from typing import List

from anta.inventory.models import InventoryDevice
from anta.models import AntaTestFilter
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

    def should_skip(self, device: InventoryDevice, result: TestResult) -> bool:
        if device.hw_model in self.platforms_to_skip:
            result.is_skipped(f"{result.test} test is not supported on {device.hw_model}.")
            return True
        return False
