"""
Test functions related to Multi-Chassis LAG
"""
import logging

from anta.inventory.models import InventoryDevice
from anta.result_manager.models import TestResult
from anta.tests import anta_test

logger = logging.getLogger(__name__)


@anta_test
async def verify_mlag_status(device: InventoryDevice, result: TestResult) -> TestResult:
    """
    Verifies the MLAG status:
    state is active, negotiation status is connected, local int is up, peer link is up.

    Args:
        device (InventoryDevice): InventoryDevice instance containing all devices information.

    Returns:
        TestResult instance with
        * result = "unset" if the test has not been executed
        * result = "success" if the MLAG status is OK
        * result = "failure" otherwise.
        * result = "error" if any exception is caught

    """
    response = await device.session.cli(command="show mlag", ofmt="json")

    if response["state"] == "disabled":
        result.is_skipped("MLAG is disabled")
    elif (
        response["state"] != "active"
        or response["negStatus"] != "connected"
        or response["localIntfStatus"] != "up"
        or response["peerLinkStatus"] != "up"
    ):
        result.is_failure(f"MLAG status is not OK: {response}")
    else:
        result.is_success()

    return result


@anta_test
async def verify_mlag_interfaces(device: InventoryDevice, result: TestResult) -> TestResult:
    """
    Verifies there is no inactive or active-partial MLAG interfaces.

    Args:
        device (InventoryDevice): InventoryDevice instance containing all devices information.

    Returns:
        TestResult instance with
        * result = "unset" if the test has not been executed
        * result = "success" if there is no inactive or active-partial MLAG interfaces.
        * result = "failure" otherwise.
        * result = "error" if any exception is caught

    """
    response = await device.session.cli(command="show mlag", ofmt="json")

    if response["state"] == "disabled":
        result.is_skipped("MLAG is disabled")
    elif (
        response["mlagPorts"]["Inactive"] != 0
        or response["mlagPorts"]["Active-partial"] != 0
    ):
        result.is_failure(f"MLAG status is not OK: {response['mlagPorts']}")
    else:
        result.is_success()

    return result


@anta_test
async def verify_mlag_config_sanity(
    device: InventoryDevice, result: TestResult
) -> TestResult:
    """
    Verifies there is no MLAG config-sanity inconsistencies.

    Args:
        device (InventoryDevice): InventoryDevice instance containing all devices information.

    Returns:
        TestResult instance with
        * result = "unset" if the test has not been executed
        * result = "success" if there is no MLAG config-sanity inconsistencies
        * result = "failure" otherwise.
        * result = "error" if any exception is caught

    """
    response = await device.session.cli(command="show mlag config-sanity", ofmt="json")

    if "mlagActive" not in response.keys():
        result.is_error("incorrect JSON response")
    elif response["mlagActive"] is False:
        # MLAG is not running
        result.is_skipped("MLAG is disabled")
    elif (
        len(response["globalConfiguration"]) > 0
        or len(response["interfaceConfiguration"]) > 0
    ):
        result.is_failure()
        if len(response["globalConfiguration"]) > 0:
            result.is_failure(
                "MLAG config-sanity returned some Global inconsistencies: "
                f"{response['response']['globalConfiguration']}"
            )
        if len(response["interfaceConfiguration"]) > 0:
            result.is_failure(
                "MLAG config-sanity returned some Interface inconsistencies: "
                f"{response['response']['interfaceConfiguration']}"
            )
    else:
        result.is_success()

    return result
