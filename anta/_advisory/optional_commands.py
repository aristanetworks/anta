# Copyright (c) 2026 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""ANTA extensions for advisory tests with non-terminal optional commands."""
# pylint: disable=too-few-public-methods

from __future__ import annotations

from typing import cast

from anta._eos.errors import is_unsupported_platform_error
from anta.models import AntaCommand, AntaTest


class OptionalAntaCommand(AntaCommand):
    """Mark a command whose unsupported status is evaluated by the test body."""


def _has_only_unsupported_platform_errors(command: AntaCommand) -> bool:
    """Return whether every command error is an ANTA unsupported-platform error."""
    return bool(command.errors) and all(is_unsupported_platform_error(error) for error in command.errors)


def is_unsupported_optional_command(command: AntaCommand) -> bool:
    """Return whether a marked optional command is unsupported on the platform."""
    return isinstance(command, OptionalAntaCommand) and _has_only_unsupported_platform_errors(command)


class OptionalCommandsMixin:
    """Allow tests to handle unsupported optional commands in their test body.

    This mixin must precede ``AntaTest`` in the test class's base classes so its
    ``failed_commands`` property is used by the ANTA test wrapper.
    """

    instance_commands: list[AntaCommand]

    @property
    def failed_commands(self) -> list[AntaCommand]:
        """Return terminal command failures while retaining optional-command errors."""
        return [command for command in self.instance_commands if command.error and not is_unsupported_optional_command(command)]

    def _handle_failed_commands(self) -> None:
        """Prevent a mixed optional-command failure from being reported as unsupported."""
        test = cast("AntaTest", self)
        mixed_optional_failures = [
            command
            for command in self.instance_commands
            if isinstance(command, OptionalAntaCommand) and command.error and not _has_only_unsupported_platform_errors(command) and not command.supported
        ]
        if mixed_optional_failures:
            test.result.is_error(message="\n".join(f"{command.command} has failed: {', '.join(command.errors)}" for command in mixed_optional_failures))
            return

        AntaTest._handle_failed_commands(test)  # noqa: SLF001 - Delegate unchanged failures to ANTA's core wrapper.
