# Copyright (c) 2026 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Fact definitions derived from EOS device and command data."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, ClassVar

from anta._advisory.facts.models import (
    CommandsFactDefinition,
    Fact,
    FactDefinition,
    FactProblemKind,
    FactSource,
    FactSourceKind,
    FeatureFact,
    FeatureName,
    FeatureRef,
    FeatureState,
)
from anta._eos.version import EOSVersion, parse_eos_version
from anta.models import AntaCommand

if TYPE_CHECKING:
    from anta.device import AntaDevice


@dataclass(frozen=True, eq=False)
class EosVersionFact(EOSVersion, FactDefinition["EosVersionFact"]):
    """Derive the normalized EOS version from refreshed device metadata."""

    key: ClassVar[str] = "eos.version"
    label: ClassVar[str] = "EOS version"

    @classmethod
    def from_version(cls, version: EOSVersion) -> EosVersionFact:
        """Create the nominal fact value from an already normalized EOS version."""
        return cls(version.major, version.minor, version.patch, version.suffix, version.hotfix)

    def __eq__(self, other: object) -> bool:
        """Compare release components with any normalized EOS version.

        ``EOSVersion`` is a dataclass whose generated equality otherwise rejects
        subclasses. A nominal fact remains an EOS version and is passed to
        remediation/version APIs, so equality must preserve that value contract.
        """
        if not isinstance(other, EOSVersion):
            return NotImplemented
        return (self.major, self.minor, self.patch, self.hotfix, self.suffix) == (
            other.major,
            other.minor,
            other.patch,
            other.hotfix,
            other.suffix,
        )

    def __hash__(self) -> int:
        """Hash the same release components used by equality."""
        # Match the field order used by the generated ``EOSVersion.__hash__`` so
        # equal base and nominal values remain interchangeable as mapping keys.
        return hash((self.major, self.minor, self.patch, self.suffix, self.hotfix))

    @classmethod
    def derive(cls, device: AntaDevice, commands: tuple[AntaCommand, ...] = ()) -> Fact[EosVersionFact]:
        """Normalize the device version into an EOS version fact."""
        _ = commands
        source = FactSource("device metadata", FactSourceKind.DEVICE_METADATA)
        device_version = device.version
        if device_version is None:
            return cls.unavailable(FactProblemKind.MISSING, source)
        version = device_version if isinstance(device_version, EOSVersion) else parse_eos_version(str(device_version)).unwrap_or_none()
        if version is None:
            return cls.unavailable(FactProblemKind.INVALID, source)
        return cls.from_version(version).available(source)


@dataclass(frozen=True, slots=True)
class SecureBootFact(FeatureFact, CommandsFactDefinition["SecureBootFact"]):
    """Derive Secure Boot support and state from structured ``show boot`` output."""

    feature: ClassVar[FeatureRef] = FeatureName.SECURE_BOOT
    key: ClassVar[str] = "feature.secure_boot"
    label: ClassVar[str] = "Secure Boot feature state"
    commands: ClassVar[tuple[AntaCommand, ...]] = (AntaCommand(command="show boot", revision=1),)

    @classmethod
    def parse(cls, commands: tuple[AntaCommand, ...]) -> Fact[SecureBootFact]:
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
            return cls(FeatureState.UNSUPPORTED).available(source)

        supported = boot_output.get("securebootSupported")
        enabled = boot_output.get("securebootEnabled")

        if supported is False and enabled is True:
            return cls.unavailable(
                FactProblemKind.CONTRADICTORY,
                source,
                observations=(
                    cls(FeatureState.UNSUPPORTED),
                    cls(FeatureState.ENABLED),
                ),
            )
        if supported is False:
            return cls(FeatureState.UNSUPPORTED).available(source)
        if enabled is False:
            return cls(FeatureState.DISABLED).available(source)
        if supported is True and enabled is True:
            return cls(FeatureState.ENABLED).available(source)

        values = (supported, enabled)
        problem = FactProblemKind.MISSING if any(value is None for value in values) else FactProblemKind.MALFORMED
        return cls.unavailable(problem, source)
