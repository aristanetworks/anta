# Copyright (c) 2026 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Typed normalized facts used by security-advisory assessments."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, fields
from enum import Enum
from inspect import isabstract
from types import MappingProxyType
from typing import TYPE_CHECKING, Any, ClassVar, Generic, TypeAlias, TypeVar

if TYPE_CHECKING:
    from collections.abc import Mapping

    from typing_extensions import Self

    from anta._advisory.base import _AntaAdvisoryTest
    from anta.device import AntaDevice
    from anta.models import AntaCommand

T = TypeVar("T")
T_co = TypeVar("T_co", covariant=True)
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
        """Create an available observation of this fact.

        TODO: Once all fact values are nominal, move available-observation construction onto the fact instance to avoid passing an instance of `cls`.
        """
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
class AvailableFact(Generic[T_co]):
    """A typed fact whose normalized value is known."""

    definition: type[FactDefinition[T_co]]
    value: T_co
    source: FactSource


@dataclass(frozen=True, slots=True)
class UnavailableFact(Generic[T_co]):
    """A requested typed fact whose normalized value cannot be established."""

    definition: type[FactDefinition[T_co]]
    problem: FactProblemKind
    source: FactSource
    observations: tuple[T_co, ...] = ()

    def __post_init__(self) -> None:
        if self.problem is FactProblemKind.CONTRADICTORY and len(self.observations) < MIN_CONTRADICTORY_OBSERVATIONS:
            msg = "Contradictory facts must retain at least two observations"
            raise ValueError(msg)
        if self.problem is not FactProblemKind.CONTRADICTORY and self.observations:
            msg = "Only contradictory facts may retain observations"
            raise ValueError(msg)


Fact: TypeAlias = AvailableFact[T] | UnavailableFact[T]


@dataclass(frozen=True, slots=True)
class _FactFactory(Generic[T]):
    """Callable declaration connecting one dataclass field to its fact definition.

    Dataclasses require ``default_factory`` to be a zero-argument callable returning
    the annotated field type. Exposing ``Fact[T]`` from this callable lets the type
    checker verify that ``FactDefinition[T]`` matches the field's ``Fact[T]``.

    The callable is retained on ``dataclasses.Field.default_factory`` so
    ``FactsBase`` can discover the definition without resolving type annotations.
    It is a declaration marker and must never create an uncollected field value.
    """

    definition: type[FactDefinition[T]]

    def __call__(self) -> Fact[T]:
        """Reject dataclass construction that omitted an explicitly collected value.

        Calling ``collect`` on the concrete ``FactsBase`` subclass supplies every
        field as a constructor argument, so a valid collection never invokes this
        default factory. Calling the generated dataclass constructor without those
        values would invoke the factory and expose a container whose annotations
        incorrectly claim its facts are collected, so fail immediately instead.
        """
        msg = "Fact fields must be populated using collect() on a FactsBase subclass"
        raise RuntimeError(msg)


def fact_field(definition: type[FactDefinition[T]]) -> _FactFactory[T]:
    """Declare the definition collected into a typed dataclass fact field.

    Use this helper only as ``field(default_factory=fact_field(Definition))``.
    Keeping ``T`` in both the argument and return type makes mismatched field and
    definition types a static error, while the returned callable retains the
    definition needed for runtime command derivation and collection.
    """
    return _FactFactory(definition)


@dataclass(frozen=True, slots=True)
class FactsBase:
    """Base for immutable containers of collected advisory facts.

    Concrete dataclasses declare each fact with ``fact_field``. Definitions are
    validated and cached once when the advisory class consumes ``definitions``;
    subsequent device collections reuse that immutable cache.
    """

    _definitions: ClassVar[Mapping[str, type[FactDefinition[Any]]]]

    @classmethod
    def definitions(cls) -> Mapping[str, type[FactDefinition[Any]]]:
        """Return definitions from the concrete class's one-time validated cache.

        Looking directly in ``cls.__dict__`` prevents a subclass from accidentally
        reusing a cache created for another fact-container class.
        """
        if "_definitions" not in cls.__dict__:
            cls._validate_definitions()
        return cls._definitions

    @classmethod
    def _validate_definitions(cls) -> None:
        """Validate declaration markers and populate the immutable class cache.

        The generic field-to-definition relationship is enforced statically by
        ``fact_field``. Runtime validation only needs to ensure every author-defined
        dataclass field uses that marker and can receive the value supplied by
        ``collect``.
        """
        definitions: dict[str, type[FactDefinition[Any]]] = {}
        for declared_field in fields(cls):
            factory = declared_field.default_factory
            if not isinstance(factory, _FactFactory):
                msg = f"Class {cls.__module__}.{cls.__qualname__} field '{declared_field.name}' must use field(default_factory=fact_field(...))"
                raise TypeError(msg)
            if not declared_field.init:
                msg = f"Class {cls.__module__}.{cls.__qualname__} field '{declared_field.name}' must be included in the generated initializer"
                raise TypeError(msg)
            definitions[declared_field.name] = factory.definition
        if not definitions:
            msg = f"Class {cls.__module__}.{cls.__qualname__} must declare one or more fact fields"
            raise TypeError(msg)
        cls._definitions = MappingProxyType(definitions)

    @classmethod
    def collect(cls, collector: _AntaAdvisoryTest) -> Self:
        """Collect every cached definition and construct the concrete container.

        Every field is passed explicitly, preventing dataclasses from invoking the
        raising declaration factories. Returning ``Self`` preserves the concrete
        nested ``Facts`` type and its precisely typed fields at the call site.
        """
        facts = {}
        for name, definition in cls.definitions().items():
            facts[name] = collector.fact(definition)
        return cls(**facts)


class CommandsFactDefinition(FactDefinition[T], ABC):
    """Fact definition derived from one or more declared ANTA commands."""

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

    AAA = "AAA"
    ACL = "ACL"
    AGENT_TRACING = "agent tracing"
    BFD = "BFD"
    DHCP = "DHCP"
    DOT1X = "802.1X"
    GNMI = "gNMI"
    GNPSI = "gNPSI"
    GNSI = "gNSI"
    GRIBI = "gRIBI"
    ISIS = "IS-IS"
    MLAG = "MLAG"
    NETCONF = "NETCONF"
    NEXT_HOP_REDIRECTION = "next-hop redirection"
    OSPFV2 = "OSPFv2"
    OSPFV3 = "OSPFv3"
    P4_RUNTIME = "P4Runtime"
    PIM = "PIM"
    RADIUS_PROXY = "RADIUS proxy"
    RESTCONF = "RESTCONF"
    SECURE_BOOT = "Secure Boot"
    SNMP = "SNMP"
    SNMPV3 = "SNMPv3"
    SSH = "SSH"
    TERMINATTR = "TerminAttr"
    TRACE = "OpenConfig tracing"
    URPF = "uRPF"
    VRRP = "VRRP"


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
class FeatureFact:
    """Common state and class-level identity for a nominal feature fact."""

    feature: ClassVar[FeatureRef]
    state: FeatureState


@dataclass(frozen=True, slots=True)
class FeatureValue:
    """Legacy non-nominal state of one EOS feature."""

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


class CredentialSyntaxState(str, Enum):
    """Observed syntax used to store configured credentials."""

    NOT_CONFIGURED = "not configured"
    LEGACY = "legacy"
    ENCRYPTED = "encrypted"
    MIXED = "mixed legacy and encrypted"


@dataclass(frozen=True, slots=True)
class CredentialSyntaxValue:
    """Normalized credential-syntax state for a feature or subfeature."""

    feature: FeatureRef
    state: CredentialSyntaxState


@dataclass(frozen=True, slots=True)
class ComponentSoftwareVersion:
    """Normalized version of an EOS software component."""

    component: str
    version: str


class MitigationState(str, Enum):
    """Observed effectiveness of a possible mitigation."""

    EFFECTIVE = "effective"
    INEFFECTIVE = "ineffective"


@dataclass(frozen=True, slots=True)
class MitigationValue:
    """Normalized effectiveness of a mitigation fact."""

    state: MitigationState


class IndicatorState(str, Enum):
    """Observed state of an advisory-relevant indicator."""

    PRESENT = "present"
    ABSENT = "absent"


@dataclass(frozen=True, slots=True)
class IndicatorValue:
    """Normalized state of one advisory-relevant indicator."""

    indicator: str
    state: IndicatorState
