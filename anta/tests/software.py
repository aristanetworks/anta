"""
Test functions related to the EOS software
"""
import logging
from typing import Any, Dict, List, Optional, cast

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
        """
        Run VerifyEOSVersion validation

        Args:
            versions: List of allowed EOS versions.
        """
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

        Args:
            versions: List of allowed TerminAttr versions.
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
