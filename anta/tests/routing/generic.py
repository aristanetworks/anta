"""
Generic routing test functions
"""
from jsonrpclib import jsonrpc
from anta.inventory.models import InventoryDevice
from anta.result_manager.models import TestResult


def verify_routing_protocol_model(
    device: InventoryDevice, model: str = "multi-agent"
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
    result = TestResult(host=str(device.host), test="verify_routing_protocol_model")
    if not model:
        result.is_skipped(
            "verify_routing_protocol_model was not run as no model was given"
        )
        return result
    try:
        response = device.session.runCmds(
            1, [{"cmd": "show ip route summary", "revision": 3}], "json"
        )
        configured_model = response[0]["protoModelStatus"]["configuredProtoModel"]
        operating_model = response[0]["protoModelStatus"]["operatingProtoModel"]
        if configured_model == operating_model == model:
            result.is_success()
        else:
            result.is_failure(
                f"routing model is misconfigured: configured:{configured_model} - "
                f"operating:{operating_model} - expected:{model} "
            )
    except (jsonrpc.AppError, KeyError) as e:
        result.is_error(str(e))
    return result


def verify_routing_table_size(
    device: InventoryDevice, minimum: int, maximum: int
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
    result = TestResult(host=str(device.host), test="verify_routing_table_size")
    if not minimum or not maximum:
        result.is_skipped(
            "verify_routing_table_size was not run as no "
            "minimum or maximum were given"
        )
        return result
    try:
        response = device.session.runCmds(
            1, [{"cmd": "show ip route summary", "revision": 3}], "json"
        )
        total_routes = int(response[0]["vrfs"]["default"]["totalRoutes"])
        if minimum <= total_routes <= maximum:
            result.is_success()
        else:
            result.is_failure(
                f"routing-table has {total_routes} routes and not between min ({minimum}) and maximum ({maximum})"
            )
    except (jsonrpc.AppError, KeyError) as e:
        result.is_error(str(e))
    return result


def verify_bfd(device: InventoryDevice) -> TestResult:
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
    result = TestResult(host=str(device.host), test="verify_bfd")
    try:
        response = device.session.runCmds(1, ["show bfd peers"], "json")
        has_failed: bool = False
        for vrf in response[0]["vrfs"]:
            for neighbor in response[0]["vrfs"][vrf]["ipv4Neighbors"]:
                for interface in response[0]["vrfs"][vrf]["ipv4Neighbors"][neighbor][
                    "peerStats"
                ]:
                    if (
                        response[0]["vrfs"][vrf]["ipv4Neighbors"][neighbor][
                            "peerStats"
                        ][interface]["status"]
                        != "up"
                    ):
                        intf_state = response[0]["vrfs"][vrf]["ipv4Neighbors"][
                            neighbor
                        ]["peerStats"][interface]["status"]
                        intf_name = response[0]["vrfs"][vrf]["ipv4Neighbors"][neighbor][
                            "peerStats"
                        ][interface]
                        has_failed = True
                        result.is_failure(
                            f"bfd state on interface {intf_name} is {intf_state} (expected up)"
                        )
        if has_failed is not False:
            result.is_success()
    except (jsonrpc.AppError, KeyError) as e:
        result.is_error(str(e))
    return result
