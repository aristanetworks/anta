# Copyright (c) 2026 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Unit tests for advisory optional-command handling."""

from __future__ import annotations

import logging
from typing import ClassVar

import pytest

from anta._advisory.optional_commands import OptionalAntaCommand, OptionalCommandsMixin, is_unsupported_optional_command
from anta.device import AntaDevice, AsyncEOSDevice
from anta.models import AntaCommand, AntaTemplate, AntaTest
from anta.result_manager.models import AntaTestStatus
from asynceapi import EapiCommandError

UNSUPPORTED_ERROR = "Incomplete command (at token 1: 'module')"


class NoOpAntaDevice(AntaDevice):
    """Device retaining pre-populated command outcomes during collection."""

    @property
    def _keys(self) -> tuple[str]:
        return (self.name,)

    async def _collect(self, command: AntaCommand, *, collection_id: str | None = None) -> None:
        """Retain the command's pre-populated output or errors."""

    async def refresh(self) -> None:
        """Mark the test device available."""
        self.is_online = True
        self.established = True


class HandlesUnsupportedOptionalCommand(OptionalCommandsMixin, AntaTest):
    """Probe that handles an unsupported optional command in its test body."""

    categories: ClassVar[list[str]] = []
    commands: ClassVar[list[AntaCommand | AntaTemplate]] = [OptionalAntaCommand(command="show module", errors=[UNSUPPORTED_ERROR])]

    @AntaTest.anta_test
    def test(self) -> None:
        """Confirm the unsupported state remains available to the test."""
        if is_unsupported_optional_command(self.instance_commands[0]):
            self.result.is_success()
        else:
            self.result.is_failure()


class RequiredUnsupportedCommand(AntaTest):
    """Probe retaining ANTA's default handling for a required command."""

    categories: ClassVar[list[str]] = []
    commands: ClassVar[list[AntaCommand | AntaTemplate]] = [AntaCommand(command="show module", errors=[UNSUPPORTED_ERROR])]

    @AntaTest.anta_test
    def test(self) -> None:
        """Fail if the wrapper incorrectly executes this body."""
        self.result.is_failure("Required unsupported command was ignored.")


class MixedOptionalCommandFailure(OptionalCommandsMixin, AntaTest):
    """Probe ensuring unsupported markers do not conceal other failures."""

    categories: ClassVar[list[str]] = []
    commands: ClassVar[list[AntaCommand | AntaTemplate]] = [
        OptionalAntaCommand(command="show module", errors=[UNSUPPORTED_ERROR, "unexpected transport failure"]),
    ]

    @AntaTest.anta_test
    def test(self) -> None:
        """Fail if the wrapper incorrectly executes this body."""
        self.result.is_failure("Mixed optional-command errors were ignored.")


class HandlesDeferredOptionalCommandError(OptionalCommandsMixin, AntaTest):
    """Probe that handles a deliberately deferred optional-command error."""

    categories: ClassVar[list[str]] = []
    commands: ClassVar[list[AntaCommand | AntaTemplate]] = [
        OptionalAntaCommand(command="show agent Example", errors=["Agent 'Example' is not running"], defer_errors=True),
    ]

    @AntaTest.anta_test
    def test(self) -> None:
        """Confirm the command error remains available to the test."""
        if self.instance_commands[0].errors == ["Agent 'Example' is not running"]:
            self.result.is_success()
        else:
            self.result.is_failure()


@pytest.mark.asyncio
async def test_unsupported_optional_command_reaches_test_body() -> None:
    """Verify a solely unsupported optional command remains non-terminal."""
    test_instance = HandlesUnsupportedOptionalCommand(device=NoOpAntaDevice("unit-test"))

    await test_instance.test()

    assert test_instance.result.result is AntaTestStatus.SUCCESS
    assert test_instance.instance_commands[0].errors == [UNSUPPORTED_ERROR]


@pytest.mark.asyncio
async def test_required_unsupported_command_keeps_default_skip() -> None:
    """Verify required unsupported commands retain core ANTA behavior."""
    test_instance = RequiredUnsupportedCommand(device=NoOpAntaDevice("unit-test"))

    await test_instance.test()

    assert test_instance.result.result is AntaTestStatus.SKIPPED


@pytest.mark.asyncio
async def test_mixed_optional_command_errors_are_not_hidden() -> None:
    """Verify a real failure accompanying an unsupported marker remains terminal."""
    test_instance = MixedOptionalCommandFailure(device=NoOpAntaDevice("unit-test"))

    await test_instance.test()

    assert test_instance.result.result is AntaTestStatus.ERROR
    assert "unexpected transport failure" in test_instance.result.messages[0]


@pytest.mark.asyncio
async def test_deferred_optional_command_error_reaches_test_body() -> None:
    """Verify an opted-in command error is retained for test interpretation."""
    test_instance = HandlesDeferredOptionalCommandError(device=NoOpAntaDevice("unit-test"))

    await test_instance.test()

    assert test_instance.result.result is AntaTestStatus.SUCCESS
    assert test_instance.instance_commands[0].errors == ["Agent 'Example' is not running"]


def test_optional_command_preserves_anta_command_contract() -> None:
    """Verify the marker remains a copyable ANTA command with string content."""
    command = OptionalAntaCommand(command="show module")

    assert isinstance(command, AntaCommand)
    assert isinstance(command.command, str)
    assert isinstance(command.model_copy(), OptionalAntaCommand)
    assert command.defer_errors is False


@pytest.mark.parametrize(
    ("error", "defer_errors"),
    [("Invalid input (at token 2: 'Gnpsi')", True), (UNSUPPORTED_ERROR, False)],
)
def test_deferred_optional_command_error_is_not_logged_as_error(
    async_device: AsyncEOSDevice, caplog: pytest.LogCaptureFixture, error: str, *, defer_errors: bool
) -> None:
    """Verify collection does not report consumer-handled command errors as errors."""
    command = OptionalAntaCommand(command="show trace Gnpsi | grep Auth", defer_errors=defer_errors)
    exception = EapiCommandError(
        passed=[],
        failed=command.command,
        errors=[error],
        errmsg="Invalid command",
        not_exec=[],
    )
    caplog.set_level(logging.DEBUG)

    async_device._handle_eapi_command_error(command, exception)

    assert command.errors == [error]
    assert not any(record.levelno >= logging.ERROR for record in caplog.records)
    assert "returned an error deferred to the test" in caplog.text
