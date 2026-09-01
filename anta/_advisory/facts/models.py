# Copyright (c) 2026 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Typed normalized facts used by security-advisory assessments."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from inspect import isabstract
from typing import TYPE_CHECKING, ClassVar, Generic, TypeAlias, TypeVar

if TYPE_CHECKING:
    from anta.device import AntaDevice
    from anta.models import AntaCommand

T = TypeVar("T")
MIN_CONTRADICTORY_OBSERVATIONS = 2


class FactProblemKind(str, Enum):
    """Reason a requested fact is unavailable."""

    COLLECTION_FAILED = "collection failed"
    MISSING = "missing"
    MALFORMED = "malformed"
    INVALID = "invalid"
    UNSUPPORTED = "unsupported"
    CONTRADICTORY = "contradictory"


class FactSourceKind(str, Enum):
    """Kind of source from which a fact is derived."""

    DEVICE_METADATA = "device metadata"
    COMMAND = "command"


@dataclass(frozen=True, slots=True)
class FactSource:
    """Stable description of where a normalized fact originated."""

    name: str
    kind: FactSourceKind

    def __post_init__(self) -> None:
        if not self.name or "\n" in self.name:
            msg = "Fact source names must be non-empty and single-line"
            raise ValueError(msg)


class FactDefinition(ABC, Generic[T]):
    """Typed identity, display label, and derivation contract for one fact."""

    key: ClassVar[str]
    label: ClassVar[str]

    def __init_subclass__(cls) -> None:
        """Validate the identity declared by each concrete fact class."""
        super().__init_subclass__()
        if not isabstract(cls) and (not getattr(cls, "key", "") or not getattr(cls, "label", "") or "\n" in cls.key or "\n" in cls.label):
            msg = "Fact keys and labels must be non-empty and single-line"
            raise ValueError(msg)

    @classmethod
    def available(cls, value: T, source: FactSource) -> AvailableFact[T]:
        """Create an available observation of this fact."""
        return AvailableFact(definition=cls, value=value, source=source)

    @classmethod
    def unavailable(cls, problem: FactProblemKind, source: FactSource, *, observations: tuple[T, ...] = ()) -> UnavailableFact[T]:
        """Create an unavailable observation of this fact."""
        return UnavailableFact(definition=cls, problem=problem, source=source, observations=observations)

    @classmethod
    @abstractmethod
    def derive(cls, device: AntaDevice, commands: tuple[AntaCommand, ...] = ()) -> Fact[T]:
        """Derive this fact from its declared source."""

    @classmethod
    def required_commands(cls) -> tuple[AntaCommand, ...]:
        """Return the ANTA commands required to derive this fact."""
        return ()


@dataclass(frozen=True, slots=True)
class AvailableFact(Generic[T]):
    """A typed fact whose normalized value is known."""

    definition: type[FactDefinition[T]]
    value: T
    source: FactSource


@dataclass(frozen=True, slots=True)
class UnavailableFact(Generic[T]):
    """A requested typed fact whose normalized value cannot be established."""

    definition: type[FactDefinition[T]]
    problem: FactProblemKind
    source: FactSource
    observations: tuple[T, ...] = ()

    def __post_init__(self) -> None:
        if self.problem is FactProblemKind.CONTRADICTORY and len(self.observations) < MIN_CONTRADICTORY_OBSERVATIONS:
            msg = "Contradictory facts must retain at least two observations"
            raise ValueError(msg)
        if self.problem is not FactProblemKind.CONTRADICTORY and self.observations:
            msg = "Only contradictory facts may retain observations"
            raise ValueError(msg)


Fact: TypeAlias = AvailableFact[T] | UnavailableFact[T]


class CommandFactDefinition(FactDefinition[T], ABC):
    """Fact definition derived from one declared ANTA command."""

    command: ClassVar[AntaCommand]

    @classmethod
    def required_commands(cls) -> tuple[AntaCommand, ...]:
        """Return the command declared by this fact class."""
        return (cls.command,)

    @classmethod
    def derive(cls, device: AntaDevice, commands: tuple[AntaCommand, ...] = ()) -> Fact[T]:
        """Validate the collected command and normalize its output."""
        _ = device
        source = FactSource(cls.command.command, FactSourceKind.COMMAND)
        if not commands:
            return cls.unavailable(FactProblemKind.COLLECTION_FAILED, source)
        command = commands[0]
        if command.uid != cls.command.uid:
            msg = f"Fact '{cls.key}' cannot be derived from command '{command.command}'"
            raise ValueError(msg)
        return cls.parse(command)

    @classmethod
    @abstractmethod
    def parse(cls, command: AntaCommand) -> Fact[T]:
        """Normalize the collected output for this fact."""


class MultiCommandFactDefinition(FactDefinition[T], ABC):
    """Fact definition derived from multiple declared ANTA commands."""

    commands: ClassVar[tuple[AntaCommand, ...]]

    @classmethod
    def required_commands(cls) -> tuple[AntaCommand, ...]:
        """Return the commands declared by this fact class."""
        return cls.commands

    @classmethod
    def derive(cls, device: AntaDevice, commands: tuple[AntaCommand, ...] = ()) -> Fact[T]:
        """Validate the collected commands and normalize their output."""
        _ = device
        if len(commands) != len(cls.commands) or any(command.uid != declared.uid for command, declared in zip(commands, cls.commands, strict=True)):
            source = FactSource(", ".join(command.command for command in cls.commands), FactSourceKind.COMMAND)
            return cls.unavailable(FactProblemKind.COLLECTION_FAILED, source)
        return cls.parse(commands)

    @classmethod
    @abstractmethod
    def parse(cls, commands: tuple[AntaCommand, ...]) -> Fact[T]:
        """Normalize the collected outputs for this fact."""


class FeatureName(str, Enum):
    """Normalized EOS features currently used by structured findings."""

    GNMI = "gNMI"
    GRIBI = "gRIBI"
    NEXT_HOP_REDIRECTION = "next-hop redirection"
    SECURE_BOOT = "Secure Boot"
    SSH = "SSH"
    TERMINATTR = "TerminAttr"
    TRACE = "OpenConfig tracing"


@dataclass(frozen=True, slots=True)
class SubFeature:
    """Advisory-relevant feature below one stable parent feature."""

    parent: FeatureName
    name: str


FeatureRef: TypeAlias = FeatureName | SubFeature


class FeatureState(str, Enum):
    """Observed lifecycle state of an EOS feature."""

    ENABLED = "enabled"
    DISABLED = "disabled"
    UNSUPPORTED = "not supported"


@dataclass(frozen=True, slots=True)
class FeatureValue:
    """Normalized state of one EOS feature."""

    feature: FeatureRef
    state: FeatureState


class ConfigurationState(str, Enum):
    """Observed configuration state."""

    CONFIGURED = "configured"
    NOT_CONFIGURED = "not configured"


@dataclass(frozen=True, slots=True)
class ConfigurationValue:
    """Normalized configuration state for a feature or subfeature."""

    feature: FeatureRef
    state: ConfigurationState


@dataclass(frozen=True, slots=True)
class ComponentSoftwareVersion:
    """Normalized version of an EOS software component."""

    component: str
    version: str


@dataclass(frozen=True, slots=True)
class PlatformIdentity:
    """Normalized platform identity placeholder for future platform facts."""

    model: str


class MitigationState(str, Enum):
    """Observed effectiveness of a possible mitigation."""

    EFFECTIVE = "effective"
    INEFFECTIVE = "ineffective"


@dataclass(frozen=True, slots=True)
class MitigationValue:
    """Normalized mitigation placeholder for mitigated findings."""

    name: str
    state: MitigationState
