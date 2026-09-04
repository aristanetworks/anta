# Copyright (c) 2026 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Fact definitions derived from EOS device and command data."""

from __future__ import annotations

from typing import TYPE_CHECKING

from anta._advisory.facts.models import (
    CommandsFactDefinition,
    Fact,
    FactDefinition,
    FactProblemKind,
    FactSource,
    FactSourceKind,
    FeatureName,
    FeatureState,
    FeatureValue,
)
from anta._eos.version import EOSVersion, parse_eos_version
from anta.models import AntaCommand

if TYPE_CHECKING:
    from anta.device import AntaDevice


class EosVersionFact(FactDefinition[EOSVersion]):
    """Derive the normalized EOS version from refreshed device metadata."""

    key = "eos.version"
    label = "EOS version"

    @classmethod
    def derive(cls, device: AntaDevice, commands: tuple[AntaCommand, ...] = ()) -> Fact[EOSVersion]:
        """Normalize the device version into an EOS version fact."""
        _ = commands
        source = FactSource("device metadata", FactSourceKind.DEVICE_METADATA)
        device_version = device.version
        if device_version is None:
            return cls.unavailable(FactProblemKind.MISSING, source)
        version = device_version if isinstance(device_version, EOSVersion) else parse_eos_version(str(device_version))
        if version is None:
            return cls.unavailable(FactProblemKind.INVALID, source)
        return cls.available(version, source)


class SecureBootFact(CommandsFactDefinition[FeatureValue]):
    """Derive Secure Boot support and state from structured ``show boot`` output."""

    key = "feature.secure_boot"
    label = "Secure Boot feature state"
    commands = (AntaCommand(command="show boot", revision=1),)

    @classmethod
    def parse(cls, commands: tuple[AntaCommand, ...]) -> Fact[FeatureValue]:
        """Normalize the collected command output into a Secure Boot fact.

        The structured fields prove the platform-support and configuration prerequisites
        together. Empty structured output is the established unsupported-feature shape and
        therefore proves absence. A false prerequisite is otherwise sufficient to establish
        a safe state.
        """
        (command,) = commands
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
