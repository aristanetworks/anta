# Copyright (c) 2023-2025 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Module related to the EOS software tests."""

# Pyright does not understand AntaTest.Input typing
# pyright: reportAttributeAccessIssue=false
from __future__ import annotations

from typing import TYPE_CHECKING, ClassVar

from anta.models import AntaCommand, AntaTest

if TYPE_CHECKING:
    from anta.models import AntaTemplate


class VerifyEOSVersion(AntaTest):
    """Verifies the EOS version of the device.

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
        self.result.is_success()
        if command_output["version"] not in self.inputs.versions:
            self.result.is_failure(f"EOS version mismatch - Actual: {command_output['version']} not in Expected: {', '.join(self.inputs.versions)}")


class VerifyTerminAttrVersion(AntaTest):
    """Verifies the TerminAttr version of the device.

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
        self.result.is_success()
        command_output_data = command_output["details"]["packages"]["TerminAttr-core"]["version"]
        if command_output_data not in self.inputs.versions:
            self.result.is_failure(f"TerminAttr version mismatch - Actual: {command_output_data} not in Expected: {', '.join(self.inputs.versions)}")


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

    categories: ClassVar[list[str]] = ["software"]
    commands: ClassVar[list[AntaCommand | AntaTemplate]] = [
        AntaCommand(command="show extensions", revision=2),
        AntaCommand(command="show boot-extensions", revision=1),
    ]

    @AntaTest.anta_test
    def test(self) -> None:
        """Main test function for VerifyEOSExtensions."""
        boot_extensions = []
        self.result.is_success()
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
        if installed_extensions != boot_extensions:
            str_installed_extensions = ", ".join(installed_extensions) if installed_extensions else "Not found"
            str_boot_extensions = ", ".join(boot_extensions) if boot_extensions else "Not found"
            self.result.is_failure(f"EOS extensions mismatch - Installed: {str_installed_extensions} Configured: {str_boot_extensions}")
