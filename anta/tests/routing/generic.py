"""
Generic routing test functions
"""
import logging

from anta.inventory.models import InventoryDevice
from anta.result_manager.models import TestResult
from anta.tests import anta_test

logger = logging.getLogger(__name__)


@anta_test
async def verify_routing_protocol_model(
    device: InventoryDevice, result: TestResult, model: str = "multi-agent"
) -> TestResult:

    """
    Verifies the configured routing protocol model is the one we expect.
    And if there is no mismatch between the configured and operating routing protocol model.

    Args:
        device (InventoryDevice): InventoryDevice instance containing all devices information.
        model(str): Expected routing protocol model (multi-agent or ribd). Default is multi-agent

    Returns:
        TestResult instance with
        * result = "unset" if the test has not been executed
        * result = "skipped" if the test `model` parameter is missing
        * result = "success" if routing model is well configured
        * result = "failure" otherwise.
        * result = "error" if any exception is caught
    """
    if not model:
        result.is_skipped(
            "verify_routing_protocol_model was not run as no model was given"
        )
        return result

    response = await device.session.cli(
        command={"cmd": "show ip route summary", "revision": 3}, ofmt="json"
    )
    logger.debug(f"query result is: {response}")
    configured_model = response["protoModelStatus"]["configuredProtoModel"]
    operating_model = response["protoModelStatus"]["operatingProtoModel"]
    if configured_model == operating_model == model:
        result.is_success()
    else:
        result.is_failure(
            f"routing model is misconfigured: configured:{configured_model} - "
            f"operating:{operating_model} - expected:{model} "
        )

    return result


@anta_test
async def verify_routing_table_size(
    device: InventoryDevice, result: TestResult, minimum: int, maximum: int
) -> TestResult:
    """
    Verifies the size of the IP routing table (default VRF).
    Should be between the two provided thresholds.

    Args:
        device (InventoryDevice): InventoryDevice instance containing all devices information.
        minimum(int): Expected minimum routing table (default VRF) size.
        maximum(int): Expected maximum routing table (default VRF) size.

    Returns:
        TestResult instance with
        * result = "unset" if the test has not been executed
        * result = "skipped" if the test `minimum` or `maximum` parameters are missing
        * result = "success" if routing-table size is correct
        * result = "failure" otherwise.
        * result = "error" if any exception is caught
    """
    if not minimum or not maximum:
        result.is_skipped(
            "verify_routing_table_size was not run as no "
            "minimum or maximum were given"
        )
        return result
    response = await device.session.cli(
        command={"cmd": "show ip route summary", "revision": 3}, ofmt="json"
    )
    logger.debug(f"query result is: {response}")
    total_routes = int(response["vrfs"]["default"]["totalRoutes"])
    if minimum <= total_routes <= maximum:
        result.is_success()
    else:
        result.is_failure(
            f"routing-table has {total_routes} routes and not between min ({minimum}) and maximum ({maximum})"
        )

    return result


@anta_test
async def verify_bfd(device: InventoryDevice, result: TestResult) -> TestResult:
    """
    Verifies there is no BFD peer in down state (all VRF, IPv4 neighbors).

    Args:
        device (InventoryDevice): InventoryDevice instance containing all devices information.

    Returns:
        TestResult instance with
        * result = "unset" if the test has not been executed
        * result = "success" if routing-table size is OK
        * result = "failure" otherwise.
        * result = "error" if any exception is caught
    """
    response = await device.session.cli(command="show bfd peers", ofmt="json")
    logger.debug(f"query result is: {response}")
    has_failed: bool = False
    for vrf in response["vrfs"]:
        for neighbor in response["vrfs"][vrf]["ipv4Neighbors"]:
            for interface in response["vrfs"][vrf]["ipv4Neighbors"][neighbor][
                "peerStats"
            ]:
                if (
                    response["vrfs"][vrf]["ipv4Neighbors"][neighbor]["peerStats"][
                        interface
                    ]["status"]
                    != "up"
                ):
                    intf_state = response["vrfs"][vrf]["ipv4Neighbors"][neighbor][
                        "peerStats"
                    ][interface]["status"]
                    intf_name = response["vrfs"][vrf]["ipv4Neighbors"][neighbor][
                        "peerStats"
                    ][interface]
                    has_failed = True
                    result.is_failure(
                        f"bfd state on interface {intf_name} is {intf_state} (expected up)"
                    )
    if has_failed is False:
        result.is_success()

    return result
