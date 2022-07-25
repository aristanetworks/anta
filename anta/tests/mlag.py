"""
Test functions related to Multi-Chassis LAG
"""
from jsonrpclib import jsonrpc
from anta.inventory.models import InventoryDevice
from anta.result_manager.models import TestResult


def verify_mlag_status(device: InventoryDevice) -> TestResult:
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
    result = TestResult(host=str(device.host), test="verify_mlag_status")

    try:
        response = device.session.runCmds(1, ["show mlag"], "json")

        if response[0]["state"] == "disabled":
            result.is_skipped("MLAG is disabled")
        elif (
            response[0]["state"] != "active"
            or response[0]["negStatus"] != "connected"
            or response[0]["localIntfStatus"] != "up"
            or response[0]["peerLinkStatus"] != "up"
        ):
            result.is_failure(f"MLAG status is not OK: {response[0]}")
        else:
            result.is_success()

    except (jsonrpc.AppError, KeyError) as e:
        result.is_error(str(e))

    return result


def verify_mlag_interfaces(device: InventoryDevice) -> TestResult:
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
    result = TestResult(host=str(device.host), test="verify_mlag_interfaces")

    try:
        response = device.session.runCmds(1, ["show mlag"], "json")

        if response[0]["state"] == "disabled":
            result.is_skipped("MLAG is disabled")
        elif (
            response[0]["mlagPorts"]["Inactive"] != 0
            or response[0]["mlagPorts"]["Active-partial"] != 0
        ):
            result.is_failure(f"MLAG status is not OK: {response[0]['mlagPorts']}")
        else:
            result.is_success()

    except (jsonrpc.AppError, KeyError) as e:
        result.is_error(str(e))

    return result


def verify_mlag_config_sanity(device: InventoryDevice) -> TestResult:
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
    result = TestResult(host=str(device.host), test="verify_mlag_config_sanity")

    try:
        response = device.session.runCmds(1, ["show mlag config-sanity"], "json")

        if response[0]["response"]["mlagActive"] is False:
            # MLAG is not running
            result.is_skipped("MLAG is disabled")
        elif (
            len(response[0]["response"]["globalConfiguration"]) > 0
            or len(response[0]["response"]["interfaceConfiguration"]) > 0
        ):
            result.is_failure()
            if len(response[0]["response"]["globalConfiguration"]) > 0:
                result.is_failure(
                    "MLAG config-sanity returned some Global inconsistencies: "
                    f"{response[0]['response']['globalConfiguration']}"
                )
            if len(response[0]["response"]["interfaceConfiguration"]) > 0:
                result.is_failure(
                    "MLAG config-sanity returned some Interface inconsistencies: "
                    f"{response[0]['response']['interfaceConfiguration']}"
                )
        else:
            result.is_success()

    except (jsonrpc.AppError, KeyError) as e:
        result.is_error(str(e))

    return result
