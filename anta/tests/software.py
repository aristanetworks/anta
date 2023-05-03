"""
Test functions related to the EOS software
"""
import logging
from typing import Any, Dict, List, Optional, cast

from anta.decorators import skip_on_platforms
from anta.models import AntaTest, AntaTestCommand

logger = logging.getLogger(__name__)


class VerifyEOSVersion(AntaTest):
    """
    Verifies the device is running one of the allowed EOS version.
    """

    name = "VerifyEOSVersion"
    description = "Verifies the device is running one of the allowed EOS version."
    categories = ["software"]
    commands = [AntaTestCommand(command="show version")]

    @AntaTest.anta_test
    def test(self, versions: Optional[List[str]] = None) -> None:
        """Run VerifyEOSVersion validation
        versions (list): List of allowed EOS versions."""
        if not versions:
            self.result.is_skipped("VerifyEOSVersion was not run as no versions were given")
            return

        command_output = cast(Dict[str, Dict[Any, Any]], self.instance_commands[0].output)

        if command_output["version"] in versions:
            self.result.is_success()
        else:
            self.result.is_failure(f'device is running version {command_output["version"]} not in expected versions: {versions}')


class VerifyTerminAttrVersion(AntaTest):
    """
    Verifies the device is running one of the allowed TerminAttr version.
    """

    name = "VerifyTerminAttrVersion"
    description = "Verifies the device is running one of the allowed TerminAttr version."
    categories = ["software"]
    commands = [AntaTestCommand(command="show version detail")]

    @AntaTest.anta_test
    def test(self, versions: Optional[List[str]] = None) -> None:
        """
        Run VerifyTerminAttrVersion validation
                versions (list): List of allowed TerminAttr versions.
        """

        if not versions:
            self.result.is_skipped("VerifyTerminAttrVersion was not run as no versions were given")
            return

        command_output = cast(Dict[str, Dict[Any, Any]], self.instance_commands[0].output)

        command_output_data = command_output["details"]["packages"]["TerminAttr-core"]["version"]
        if command_output_data in versions:
            self.result.is_success()
        else:
            self.result.is_failure(f"device is running TerminAttr version {command_output_data} and is not in the allowed list: {versions}")


class VerifyEOSExtensions(AntaTest):
    """
    Verifies all EOS extensions installed on the device are enabled for boot persistence.
    """

    name = "VerifyEOSExtensions"
    description = "Verifies all EOS extensions installed on the device are enabled for boot persistence."
    categories = ["software"]
    commands = [AntaTestCommand(command="show extensions"), AntaTestCommand(command="show boot-extensions")]

    @AntaTest.anta_test
    def test(self) -> None:
        """Run VerifyEOSExtensions validation"""

        boot_extensions = []

        show_extensions_command_output = cast(Dict[str, Dict[Any, Any]], self.instance_commands[0].output)
        show_boot_extensions_command_output = cast(Dict[str, Dict[Any, Any]], self.instance_commands[1].output)

        installed_extensions = [
            extension for extension, extension_data in show_extensions_command_output["extensions"].items() if extension_data["status"] == "installed"
        ]

        for extension in show_boot_extensions_command_output["extensions"]:
            extension = extension.strip("\n")
            if extension != "":
                boot_extensions.append(extension)

        installed_extensions.sort()
        boot_extensions.sort()
        if installed_extensions == boot_extensions:
            self.result.is_success()
        else:
            self.result.is_failure(f"Missing EOS extensions: installed {installed_extensions} / configured: {boot_extensions}")


class VerifyFieldNotice44Resolution(AntaTest):
    """
    Verifies the device is using an Aboot version that fix the bug discussed
    in the field notice 44 (Aboot manages system settings prior to EOS initialization).

    https://www.arista.com/en/support/advisories-notices/field-notice/8756-field-notice-44
    """

    name = "VerifyFieldNotice44Resolution"
    description = (
        "Verifies the device is using an Aboot version that fix the bug discussed in the field notice 44 (Aboot manages system settings prior to EOS initialization)"
    )
    categories = ["software"]
    commands = [AntaTestCommand(command="show version detail")]

    # TODO maybe implement ONLY ON PLATFORMS instead
    @skip_on_platforms(["cEOSLab"])
    @AntaTest.anta_test
    def test(self) -> None:  # type: ignore[override]
        """Run VerifyFieldNotice44Resolution validation"""

        command_output = cast(Dict[str, Dict[Any, Any]], self.instance_commands[0].output)

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

        model = cast(str, command_output["modelName"])
        # TODO this list could be a regex
        for variant in variants:
            model = model.replace(variant, "")
        if model not in devices:
            self.result.is_skipped("device is not impacted by FN044")
            return

        for component in command_output["details"]["components"]:
            if component["name"] == "Aboot":
                aboot_version = component["version"].split("-")[2]
        self.result.is_success()
        if aboot_version.startswith("4.0.") and int(aboot_version.split(".")[2]) < 7:
            self.result.is_failure(f"device is running incorrect version of aboot ({aboot_version})")
        elif aboot_version.startswith("4.1.") and int(aboot_version.split(".")[2]) < 1:
            self.result.is_failure(f"device is running incorrect version of aboot ({aboot_version})")
        elif aboot_version.startswith("6.0.") and int(aboot_version.split(".")[2]) < 9:
            self.result.is_failure(f"device is running incorrect version of aboot ({aboot_version})")
        elif aboot_version.startswith("6.1.") and int(aboot_version.split(".")[2]) < 7:
            self.result.is_failure(f"device is running incorrect version of aboot ({aboot_version})")
