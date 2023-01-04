"""
Test functions related to the EOS software
"""
import logging
from typing import List, Optional

from anta.decorators import skip_on_platforms
from anta.inventory.models import InventoryDevice
from anta.result_manager.models import TestResult
from anta.tests import anta_test

logger = logging.getLogger(__name__)


@anta_test
async def verify_eos_version(device: InventoryDevice, result: TestResult, versions: Optional[List[str]] = None) -> TestResult:
    """
    Verifies the device is running one of the allowed EOS version.

    Args:
        device (InventoryDevice): InventoryDevice instance containing all devices information.
        versions (list): List of allowed EOS versions.

    Returns:
        TestResult instance with
        * result = "unset" if the test has not been executed
        * result = "skipped" if the `version` parameter is missing
        * result = "success" if EOS version is valid against versions
        * result = "failure" otherwise.
        * result = "error" if any exception is caught

    """
    if not versions:
        result.is_skipped("verify_eos_version was not run as no versions were given")
        return result

    response = await device.session.cli(command="show version", ofmt="json")
    logger.debug(f"query result is: {response}")

    if response["version"] in versions:
        result.is_success()
    else:
        result.is_failure(
            f'device is running version {response["version"]} not in expected versions: {versions}'
        )

    return result


@anta_test
async def verify_terminattr_version(
    device: InventoryDevice, result: TestResult, versions: Optional[List[str]] = None
) -> TestResult:
    """
    Verifies the device is running one of the allowed TerminAttr version.

    Args:
        device (InventoryDevice): InventoryDevice instance containing all devices information.
        versions (list): List of allowed TerminAttr versions.

    Returns:
        TestResult instance with
        * result = "unset" if the test has not been executed
        * result = "skipped" if the `versions` parameter is missing
        * result = "success" if TerminAttr version is valid against versions
        * result = "failure" otherwise.
        * result = "error" if any exception is caught

    """
    if not versions:
        result.is_skipped(
            "verify_terminattr_version was not run as no versions were given"
        )
        return result

    response = await device.session.cli(command="show version detail", ofmt="json")
    logger.debug(f"query result is: {response}")

    response_data = response["details"]["packages"]["TerminAttr-core"]["version"]
    if response_data in versions:
        result.is_success()
    else:
        result.is_failure(
            f"device is running TerminAttr version {response_data} and is not in the allowed list: {versions}"
        )

    return result


@anta_test
async def verify_eos_extensions(device: InventoryDevice, result: TestResult) -> TestResult:
    """
    Verifies all EOS extensions installed on the device are enabled for boot persistence.

    Args:
        device (InventoryDevice): InventoryDevice instance containing all devices information.

    Returns:
        TestResult instance with
        * result = "unset" if the test has not been executed
        * result = "success" if the device has all installed its EOS extensions enabled for boot persistence.
        * result = "failure" otherwise.
        * result = "error" if any exception is caught

    """
    response = await device.session.cli(commands=["show extensions", "show boot-extensions"], ofmt="json")
    logger.debug(f"query result is: {response}")

    installed_extensions = []
    boot_extensions = []
    for extension in response[0]["extensions"]:
        if response[0]["extensions"][extension]["status"] == "installed":
            installed_extensions.append(extension)
    for extension in response[1]["extensions"]:
        extension = extension.strip("\n")
        if extension == "":
            pass
        else:
            boot_extensions.append(extension)
    installed_extensions.sort()
    boot_extensions.sort()
    if installed_extensions == boot_extensions:
        result.is_success()
    else:
        result.is_failure(
            f"Missing EOS extensions: installed {installed_extensions} / configured: {boot_extensions}"
        )

    return result


@skip_on_platforms(["cEOSLab"])
@anta_test
async def verify_field_notice_44_resolution(
    device: InventoryDevice, result: TestResult
) -> TestResult:
    """
    Verifies the device is using an Aboot version that fix the bug discussed
    in the field notice 44 (Aboot manages system settings prior to EOS initialization).

    https://www.arista.com/en/support/advisories-notices/field-notice/8756-field-notice-44

    Args:
        device (InventoryDevice): InventoryDevice instance containing all devices information.

    Returns:
        TestResult instance with
        * result = "unset" if the test has not been executed
        * result = "success" if aboot is running valid version
        * result = "failure" otherwise.
        * result = "error" if any exception is caught
    """
    response = await device.session.cli(command="show version detail", ofmt="json")
    logger.debug(f"query result is: {response}")

    devices = [
        "DCS-7010T-48",
        "DCS-7010T-48-DC",
        "DCS-7050TX-48",
        "DCS-7050TX-64",
        "DCS-7050TX-72",
        "DCS-7050TX-72Q",
        "DCS-7050TX-96",
        "DCS-7050TX2-128",
        "DCS-7050SX-64",
        "DCS-7050SX-72",
        "DCS-7050SX-72Q",
        "DCS-7050SX2-72Q",
        "DCS-7050SX-96",
        "DCS-7050SX2-128",
        "DCS-7050QX-32S",
        "DCS-7050QX2-32S",
        "DCS-7050SX3-48YC12",
        "DCS-7050CX3-32S",
        "DCS-7060CX-32S",
        "DCS-7060CX2-32S",
        "DCS-7060SX2-48YC6",
        "DCS-7160-48YC6",
        "DCS-7160-48TC6",
        "DCS-7160-32CQ",
        "DCS-7280SE-64",
        "DCS-7280SE-68",
        "DCS-7280SE-72",
        "DCS-7150SC-24-CLD",
        "DCS-7150SC-64-CLD",
        "DCS-7020TR-48",
        "DCS-7020TRA-48",
        "DCS-7020SR-24C2",
        "DCS-7020SRG-24C2",
        "DCS-7280TR-48C6",
        "DCS-7280TRA-48C6",
        "DCS-7280SR-48C6",
        "DCS-7280SRA-48C6",
        "DCS-7280SRAM-48C6",
        "DCS-7280SR2K-48C6-M",
        "DCS-7280SR2-48YC6",
        "DCS-7280SR2A-48YC6",
        "DCS-7280SRM-40CX2",
        "DCS-7280QR-C36",
        "DCS-7280QRA-C36S",
    ]
    variants = ["-SSD-F", "-SSD-R", "-M-F", "-M-R", "-F", "-R"]

    model = response["modelName"]
    for variant in variants:
        model = model.replace(variant, "")
    if model not in devices:
        result.is_skipped("device is not impacted by FN044")
        return result

    for component in response["details"]["components"]:
        if component["name"] == "Aboot":
            aboot_version = component["version"].split("-")[2]
    result.is_success()
    if aboot_version.startswith("4.0.") and int(aboot_version.split(".")[2]) < 7:
        result.is_failure(
            f"device is running incorrect version of aboot ({aboot_version})"
        )
    elif aboot_version.startswith("4.1.") and int(aboot_version.split(".")[2]) < 1:
        result.is_failure(
            f"device is running incorrect version of aboot ({aboot_version})"
        )
    elif aboot_version.startswith("6.0.") and int(aboot_version.split(".")[2]) < 9:
        result.is_failure(
            f"device is running incorrect version of aboot ({aboot_version})"
        )
    elif aboot_version.startswith("6.1.") and int(aboot_version.split(".")[2]) < 7:
        result.is_failure(
            f"device is running incorrect version of aboot ({aboot_version})"
        )

    return result
