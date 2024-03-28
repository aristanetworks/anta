# Copyright (c) 2023-2024 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Module related to the EOS software tests."""

# Mypy does not understand AntaTest.Input typing
# mypy: disable-error-code=attr-defined
from __future__ import annotations

from typing import TYPE_CHECKING, ClassVar

from anta.models import AntaCommand, AntaTest

if TYPE_CHECKING:
    from anta.models import AntaTemplate


class VerifyEOSVersion(AntaTest):
    """Verifies that the device is running one of the allowed EOS version.

    Expected Results
    ----------------
    * Success: The test will pass if the device is running one of the allowed EOS version.
    * Failure: The test will fail if the device is not running one of the allowed EOS version.

    Examples
    --------
    ```yaml
    anta.tests.software:
      - VerifyEOSVersion:
          versions:
            - 4.25.4M
            - 4.26.1F
    ```
    """

    name = "VerifyEOSVersion"
    description = "Verifies the EOS version of the device."
    categories: ClassVar[list[str]] = ["software"]
    commands: ClassVar[list[AntaCommand | AntaTemplate]] = [AntaCommand(command="show version", revision=1)]

    class Input(AntaTest.Input):
        """Input model for the VerifyEOSVersion test."""

        versions: list[str]
        """List of allowed EOS versions."""

    @AntaTest.anta_test
    def test(self) -> None:
        """Main test function for VerifyEOSVersion."""
        command_output = self.instance_commands[0].json_output
        if command_output["version"] in self.inputs.versions:
            self.result.is_success()
        else:
            self.result.is_failure(f'device is running version "{command_output["version"]}" not in expected versions: {self.inputs.versions}')


class VerifyTerminAttrVersion(AntaTest):
    """Verifies that he device is running one of the allowed TerminAttr version.

    Expected Results
    ----------------
    * Success: The test will pass if the device is running one of the allowed TerminAttr version.
    * Failure: The test will fail if the device is not running one of the allowed TerminAttr version.

    Examples
    --------
    ```yaml
    anta.tests.software:
      - VerifyTerminAttrVersion:
          versions:
            - v1.13.6
            - v1.8.0
    ```
    """

    name = "VerifyTerminAttrVersion"
    description = "Verifies the TerminAttr version of the device."
    categories: ClassVar[list[str]] = ["software"]
    commands: ClassVar[list[AntaCommand | AntaTemplate]] = [AntaCommand(command="show version detail", revision=1)]

    class Input(AntaTest.Input):
        """Input model for the VerifyTerminAttrVersion test."""

        versions: list[str]
        """List of allowed TerminAttr versions."""

    @AntaTest.anta_test
    def test(self) -> None:
        """Main test function for VerifyTerminAttrVersion."""
        command_output = self.instance_commands[0].json_output
        command_output_data = command_output["details"]["packages"]["TerminAttr-core"]["version"]
        if command_output_data in self.inputs.versions:
            self.result.is_success()
        else:
            self.result.is_failure(f"device is running TerminAttr version {command_output_data} and is not in the allowed list: {self.inputs.versions}")


class VerifyEOSExtensions(AntaTest):
    """Verifies that all EOS extensions installed on the device are enabled for boot persistence.

    Expected Results
    ----------------
    * Success: The test will pass if all EOS extensions installed on the device are enabled for boot persistence.
    * Failure: The test will fail if some EOS extensions installed on the device are not enabled for boot persistence.

    Examples
    --------
    ```yaml
    anta.tests.software:
      - VerifyEOSExtensions:
    ```
    """

    name = "VerifyEOSExtensions"
    description = "Verifies that all EOS extensions installed on the device are enabled for boot persistence."
    categories: ClassVar[list[str]] = ["software"]
    commands: ClassVar[list[AntaCommand | AntaTemplate]] = [
        AntaCommand(command="show extensions", revision=2),
        AntaCommand(command="show boot-extensions", revision=1),
    ]

    @AntaTest.anta_test
    def test(self) -> None:
        """Main test function for VerifyEOSExtensions."""
        boot_extensions = []
        show_extensions_command_output = self.instance_commands[0].json_output
        show_boot_extensions_command_output = self.instance_commands[1].json_output
        installed_extensions = [
            extension for extension, extension_data in show_extensions_command_output["extensions"].items() if extension_data["status"] == "installed"
        ]
        for extension in show_boot_extensions_command_output["extensions"]:
            formatted_extension = extension.strip("\n")
            if formatted_extension != "":
                boot_extensions.append(formatted_extension)
        installed_extensions.sort()
        boot_extensions.sort()
        if installed_extensions == boot_extensions:
            self.result.is_success()
        else:
            self.result.is_failure(f"Missing EOS extensions: installed {installed_extensions} / configured: {boot_extensions}")
