"""
Test functions related to ASIC profiles
"""
import logging

from anta.decorators import skip_on_platforms
from anta.inventory.models import InventoryDevice
from anta.result_manager.models import TestResult
from anta.tests import anta_test

logger = logging.getLogger(__name__)


@skip_on_platforms(["cEOSLab", "VEOS-LAB"])
@anta_test
async def verify_unified_forwarding_table_mode(
    device: InventoryDevice, result: TestResult, mode: str
) -> TestResult:

    """
    Verifies the device is using the expected Unified Forwarding Table mode.

    Args:
        device (InventoryDevice): InventoryDevice instance containing all devices information.
        mode (str): The expected Unified Forwarding Table mode.

    Returns:
        TestResult instance with
        * result = "unset" if the test has not been executed
        * result = "mode" if the `mode` parameter is missing
        * result = "success" if UFT mode is correct
        * result = "failure" otherwise.
        * result = "error" if any exception is caught
    """
    if not mode:
        result.is_skipped(
            "verify_unified_forwarding_table_mode was not run as no mode was given"
        )
        return result

    response = await device.session.cli(command="show platform trident forwarding-table partition", ofmt="json")
    logger.debug(f"query result is: {response}")
    response_data = response["uftMode"]
    if response_data == mode:
        result.is_success()
    else:
        result.is_failure(
            f"device is not running correct UFT mode (expected: {mode} / running: {response_data})"
        )

    return result


@skip_on_platforms(["cEOSLab", "VEOS-LAB"])
@anta_test
async def verify_tcam_profile(
    device: InventoryDevice, result: TestResult, profile: str
) -> TestResult:

    """
    Verifies the configured TCAM profile is the expected one.

    Args:
        device (InventoryDevice): InventoryDevice instance containing all devices information.
        profile (str): The expected TCAM profile.0

    Returns:
        TestResult instance with
        * result = "unset" if the test has not been executed
        * result = "mode" if the `profile` parameter is missing
        * result = "success" if TCAM profile is correct
        * result = "failure" otherwise.
        * result = "error" if any exception is caught
    """
    if not profile:
        result.is_skipped("verify_tcam_profile was not run as no profile was given")
        return result

    response = await device.session.cli(command="show hardware tcam profile", ofmt="json")
    logger.debug(f"query result is: {response}")
    if (
        response["pmfProfiles"]["FixedSystem"]["status"]
        == response["pmfProfiles"]["FixedSystem"]["config"]
    ) and (response["pmfProfiles"]["FixedSystem"]["status"] == profile):
        result.is_success()
    else:
        result.is_failure(
            f'Incorrect profile configured on device: {response["pmfProfiles"]["FixedSystem"]["status"]}'
        )

    return result
