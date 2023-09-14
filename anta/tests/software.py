# Copyright (c) 2023 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""
Test functions related to the EOS software
"""
# Mypy does not understand AntaTest.Input typing
# mypy: disable-error-code=attr-defined
from __future__ import annotations

# Need to keep List for pydantic in python 3.8
from typing import List

from anta.models import AntaCommand, AntaTest


class VerifyEOSVersion(AntaTest):
    """
    Verifies the device is running one of the allowed EOS version.
    """

    name = "VerifyEOSVersion"
    description = "Verifies the device is running one of the allowed EOS version."
    categories = ["software"]
    commands = [AntaCommand(command="show version")]

    class Input(AntaTest.Input):  # pylint: disable=missing-class-docstring
        versions: List[str]
        """List of allowed EOS versions"""

    @AntaTest.anta_test
    def test(self) -> None:
        command_output = self.instance_commands[0].json_output
        if command_output["version"] in self.inputs.versions:
            self.result.is_success()
        else:
            self.result.is_failure(f'device is running version {command_output["version"]} not in expected versions: {self.inputs.versions}')


class VerifyTerminAttrVersion(AntaTest):
    """
    Verifies the device is running one of the allowed TerminAttr version.
    """

    name = "VerifyTerminAttrVersion"
    description = "Verifies the device is running one of the allowed TerminAttr version."
    categories = ["software"]
    commands = [AntaCommand(command="show version detail")]

    class Input(AntaTest.Input):  # pylint: disable=missing-class-docstring
        versions: List[str]
        """List of allowed TerminAttr versions"""

    @AntaTest.anta_test
    def test(self) -> None:
        command_output = self.instance_commands[0].json_output
        command_output_data = command_output["details"]["packages"]["TerminAttr-core"]["version"]
        if command_output_data in self.inputs.versions:
            self.result.is_success()
        else:
            self.result.is_failure(f"device is running TerminAttr version {command_output_data} and is not in the allowed list: {self.inputs.versions}")


class VerifyEOSExtensions(AntaTest):
    """
    Verifies all EOS extensions installed on the device are enabled for boot persistence.
    """

    name = "VerifyEOSExtensions"
    description = "Verifies all EOS extensions installed on the device are enabled for boot persistence."
    categories = ["software"]
    commands = [AntaCommand(command="show extensions"), AntaCommand(command="show boot-extensions")]

    @AntaTest.anta_test
    def test(self) -> None:
        boot_extensions = []
        show_extensions_command_output = self.instance_commands[0].json_output
        show_boot_extensions_command_output = self.instance_commands[1].json_output
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
