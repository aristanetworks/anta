# Copyright (c) 2026 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Read-only recognition of configured management receive-queue boot controls."""

from __future__ import annotations

import shlex
from collections.abc import Mapping
from dataclasses import dataclass
from typing import TYPE_CHECKING, ClassVar, cast

from anta._advisory.facts.models import (
    CommandsFactDefinition,
    Fact,
    FactProblemKind,
    FactSource,
    FactSourceKind,
    FeatureFact,
    FeatureName,
    FeatureRef,
    FeatureState,
    SubFeature,
)
from anta._advisory.optional_commands import OptionalAntaCommand, is_unsupported_optional_command

if TYPE_CHECKING:
    from anta.models import AntaCommand

# Recognition signature for action text returned by show event-handler.
# This string is never declared as a device command or executed by the test.
SINGLE_QUEUE_BOOT_ACTION = (
    "sudo ip -all netns exec bash -c 'for i in /sys/class/net/ma*; do "
    'ethtool -L "$(basename "$i")" rx 1; ethtool -L "$(basename "$i")" combined 1; done\' &> /dev/null'
)
BOOT_COMMAND = OptionalAntaCommand(command="show event-handler", revision=1, defer_errors=True)


def _command_problem(command: AntaCommand, expected: type) -> FactProblemKind | None:
    """Retain unsupported, collection, missing, and serialization failures."""
    if is_unsupported_optional_command(command):
        return FactProblemKind.UNSUPPORTED
    if command.errors:
        return FactProblemKind.COLLECTION_FAILED
    if command.output is None:
        return FactProblemKind.MISSING
    if not isinstance(command.output, expected):
        return FactProblemKind.MALFORMED
    return None


def _other_boot_control(record: Mapping[str, object]) -> bool:
    """Identify a disabled action or a decisively different execution/trigger kind."""
    kind = record.get("actionKind")
    trigger = record.get("trigger")
    trigger_type = trigger.get("triggerType") if isinstance(trigger, Mapping) else None
    return (
        record.get("disabledManually") is True
        or record.get("builtinHandlerDisabled") is True
        or (isinstance(kind, str) and bool(kind) and kind != "bash")
        or (isinstance(trigger_type, str) and bool(trigger_type) and trigger_type != "onBoot")
    )


def _boot_properties(record: Mapping[str, object]) -> bool | FactProblemKind:
    """Validate the fields required by a matching boot-control action."""
    for key, expected in (("actionKind", str), ("trigger", Mapping), ("disabledManually", bool), ("builtinHandlerDisabled", bool)):
        if key not in record:
            return FactProblemKind.MISSING
        if not isinstance(record[key], expected):
            return FactProblemKind.MALFORMED
    trigger = cast("Mapping[str, object]", record["trigger"])
    if "triggerType" not in trigger:
        return FactProblemKind.MISSING
    trigger_type = trigger["triggerType"]
    if not isinstance(trigger_type, str):
        return FactProblemKind.MALFORMED
    return FactProblemKind.INVALID if not record["actionKind"] or not trigger_type else True


def _boot_action(record: object) -> bool | FactProblemKind:
    """Recognize the canonical all-namespace management-channel boot action."""
    if not isinstance(record, Mapping):
        return FactProblemKind.MALFORMED
    if _other_boot_control(record):
        return False
    action = record.get("action")
    if not isinstance(action, str):
        return FactProblemKind.MISSING if action is None else FactProblemKind.MALFORMED
    try:
        matches = shlex.split(action) == shlex.split(SINGLE_QUEUE_BOOT_ACTION)
    except ValueError:
        return FactProblemKind.MALFORMED
    return _boot_properties(record) if matches else False


@dataclass(frozen=True, slots=True)
class ManagementSingleQueueBootFact(FeatureFact, CommandsFactDefinition["ManagementSingleQueueBootFact"]):
    """An enabled on-boot action setting management receive channels to one."""

    feature: ClassVar[FeatureRef] = SubFeature(FeatureName.INTERFACE, "management single-receive-queue boot control")
    key: ClassVar[str] = "management.single_receive_queue.boot_action"
    label: ClassVar[str] = "single-receive-queue boot action"
    commands: ClassVar[tuple[AntaCommand, ...]] = (BOOT_COMMAND,)

    @classmethod
    def parse(cls, commands: tuple[AntaCommand, ...]) -> Fact[ManagementSingleQueueBootFact]:
        """One complete matching action is sufficient despite unrelated bad records."""
        (command,) = commands
        source = FactSource(command.command, FactSourceKind.COMMAND)
        if problem := _command_problem(command, Mapping):
            return cls.unavailable(problem, source)
        handlers = command.json_output.get("eventHandlers")
        if not isinstance(handlers, Mapping):
            return cls.unavailable(FactProblemKind.MISSING if handlers is None else FactProblemKind.MALFORMED, source)
        results = tuple(_boot_action(record) if isinstance(name, str) and name else FactProblemKind.MALFORMED for name, record in handlers.items())
        if any(result is True for result in results):
            return cls(FeatureState.ENABLED).available(source)
        problems = tuple(result for result in results if isinstance(result, FactProblemKind))
        if problems:
            return cls.unavailable(problems[0], source)
        return cls(FeatureState.DISABLED).available(source)
