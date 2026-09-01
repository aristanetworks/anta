# Copyright (c) 2026 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Fact definitions derived from EOS device and command data."""

from __future__ import annotations

from typing import TYPE_CHECKING

from anta._advisory.facts.models import (
    CommandFactDefinition,
    Fact,
    FactDefinition,
    FactProblemKind,
    FactSource,
    FactSourceKind,
    FeatureName,
    FeatureState,
    FeatureValue,
)
from anta.device import DeviceVersion
from anta.models import AntaCommand

if TYPE_CHECKING:
    from anta.device import AntaDevice


class EosVersionFact(FactDefinition[DeviceVersion]):
    """Derive the normalized EOS version from refreshed device metadata."""

    key = "eos.version"
    label = "EOS version"

    @classmethod
    def derive(cls, device: AntaDevice, commands: tuple[AntaCommand, ...] = ()) -> Fact[DeviceVersion]:
        """Return the device version or a missing fact when it is unavailable."""
        _ = commands
        source = FactSource("device metadata", FactSourceKind.DEVICE_METADATA)
        if device.version is None:
            return cls.unavailable(FactProblemKind.MISSING, source)
        return cls.available(device.version, source)


class SecureBootFact(CommandFactDefinition[FeatureValue]):
    """Derive Secure Boot support and state from structured ``show boot`` output."""

    key = "feature.secure_boot"
    label = "Secure Boot feature state"
    command = AntaCommand(command="show boot", revision=1)

    @classmethod
    def parse(cls, command: AntaCommand) -> Fact[FeatureValue]:
        """Normalize the collected command output into a Secure Boot fact.

        The structured fields prove the platform-support and configuration prerequisites
        together. Empty structured output is the established unsupported-feature shape and
        therefore proves absence. A false prerequisite is otherwise sufficient to establish
        a safe state.
        """
        boot_output = command.json_output
        source = FactSource(command.command, FactSourceKind.COMMAND)
        if not boot_output:
            return cls.available(FeatureValue(FeatureName.SECURE_BOOT, FeatureState.UNSUPPORTED), source)

        supported = boot_output.get("securebootSupported")
        enabled = boot_output.get("securebootEnabled")

        if supported is False and enabled is True:
            return cls.unavailable(
                FactProblemKind.CONTRADICTORY,
                source,
                observations=(
                    FeatureValue(FeatureName.SECURE_BOOT, FeatureState.UNSUPPORTED),
                    FeatureValue(FeatureName.SECURE_BOOT, FeatureState.ENABLED),
                ),
            )
        if supported is False:
            return cls.available(FeatureValue(FeatureName.SECURE_BOOT, FeatureState.UNSUPPORTED), source)
        if enabled is False:
            return cls.available(FeatureValue(FeatureName.SECURE_BOOT, FeatureState.DISABLED), source)
        if supported is True and enabled is True:
            return cls.available(FeatureValue(FeatureName.SECURE_BOOT, FeatureState.ENABLED), source)

        values = (supported, enabled)
        problem = FactProblemKind.MISSING if any(value is None for value in values) else FactProblemKind.MALFORMED
        return cls.unavailable(problem, source)
