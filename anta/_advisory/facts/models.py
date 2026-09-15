# Copyright (c) 2026 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Typed normalized facts and their declarative advisory containers."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field, fields
from enum import Enum
from inspect import isabstract
from types import MappingProxyType
from typing import TYPE_CHECKING, Any, ClassVar, Generic, TypeAlias, TypeVar, cast

from typing_extensions import dataclass_transform

if TYPE_CHECKING:
    from collections.abc import Mapping

    from typing_extensions import Self

    from anta._advisory.base import _AntaAdvisoryTest
    from anta.device import AntaDevice
    from anta.models import AntaCommand

T = TypeVar("T")
T_co = TypeVar("T_co", covariant=True)
FactsT = TypeVar("FactsT")
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


def _validate_definitions(facts_type: type[FactsBase]) -> Mapping[str, type[FactDefinition[Any]]]:
    """Validate one concrete fact container and return its immutable definitions.

    The generic field-to-definition relationship is enforced statically by the
    signature of ``fact_field``. Runtime validation deliberately avoids resolving
    type annotations: it only checks that every dataclass field has exactly the
    expected metadata naming a ``FactDefinition``, participates in the generated
    initializer, and uses a unique definition.

    A structurally valid metadata mapping can be constructed without calling
    ``fact_field``, so runtime validation does not prove that the helper was used.
    It also cannot recheck the erased generic relationship. Callers rely on the
    type checker for that relationship.
    """
    definitions: dict[str, type[FactDefinition[Any]]] = {}
    definition_fields: dict[type[FactDefinition[Any]], str] = {}
    for declared_field in fields(facts_type):
        if set(declared_field.metadata) != {"definition"}:
            msg = f"Class {facts_type.__module__}.{facts_type.__qualname__} field '{declared_field.name}' must use fact_field(...)"
            raise TypeError(msg)
        definition = declared_field.metadata["definition"]
        if not isinstance(definition, type) or not issubclass(definition, FactDefinition):
            msg = f"Class {facts_type.__module__}.{facts_type.__qualname__} field '{declared_field.name}' must use fact_field(...)"
            raise TypeError(msg)
        if not declared_field.init:
            msg = f"Class {facts_type.__module__}.{facts_type.__qualname__} field '{declared_field.name}' must be included in the generated initializer"
            raise TypeError(msg)
        if previous_field := definition_fields.get(definition):
            msg = (
                f"Class {facts_type.__module__}.{facts_type.__qualname__} fields '{previous_field}' and '{declared_field.name}' "
                f"must not use the same fact definition '{definition.__name__}'"
            )
            raise TypeError(msg)
        definitions[declared_field.name] = definition
        definition_fields[definition] = declared_field.name
    if not definitions:
        msg = f"Class {facts_type.__module__}.{facts_type.__qualname__} must declare one or more fact fields"
        raise TypeError(msg)
    return MappingProxyType(definitions)


def fact_field(definition: type[FactDefinition[T]]) -> Fact[T]:
    """Declare a required field populated from one typed fact definition.

    This helper has deliberately different static and runtime representations.
    Its ``Fact[T]`` return annotation lets a type checker verify that the field's
    annotation and ``FactDefinition[T]`` agree. At runtime it returns a standard
    ``dataclasses.Field`` with no default, making the collected value a required
    constructor argument, and retains ``definition`` in the field metadata used
    for runtime collection.

    ``facts_dataclass`` registers this helper as a PEP 681 field specifier so the
    generated constructor is understood correctly by supporting type checkers.
    Runtime validation checks the metadata shape and definition value but does
    not inspect the field annotation or its generic type.
    """
    return cast("Fact[T]", field(metadata={"definition": definition}))  # pylint: disable=invalid-field-call


@dataclass_transform(field_specifiers=(fact_field,), frozen_default=True)
def facts_dataclass(cls: type[FactsT]) -> type[FactsT]:
    """Create and validate a frozen, slotted container of collected facts.

    Fact containers must use this decorator rather than applying ``dataclass``
    directly. Besides performing the runtime dataclass transformation, it tells
    type checkers that ``fact_field`` declares required instance fields whose
    values have the helper's annotated ``Fact[T]`` type. Once dataclass fields
    are available, the decorator validates their runtime declarations and
    populates the concrete class's immutable definition cache.
    """
    facts_type = dataclass(frozen=True, slots=True)(cls)
    if not issubclass(facts_type, FactsBase):
        msg = f"Class {facts_type.__module__}.{facts_type.__qualname__} decorated with facts_dataclass must inherit FactsBase"
        raise TypeError(msg)
    facts_type._definitions = _validate_definitions(facts_type)  # noqa: SLF001
    return facts_type


@dataclass(frozen=True, slots=True)
class FactsBase:
    """Common collection behavior for immutable typed fact containers.

    A concrete container is decorated with ``facts_dataclass`` and declares each
    required value with ``fact_field``. The field annotations preserve precise
    fact types for advisory assessment code. The field metadata supplies the
    corresponding runtime definitions used to derive commands and collect facts.

    ``facts_dataclass`` validates definitions once, immediately after transforming
    each concrete subclass, and stores an immutable cache. Advisory class creation
    and subsequent device collections only read that cache.
    """

    _definitions: ClassVar[Mapping[str, type[FactDefinition[Any]]]]

    @classmethod
    def definitions(cls) -> Mapping[str, type[FactDefinition[Any]]]:
        """Return definitions cached when the concrete class was decorated.

        Looking directly in ``cls.__dict__`` prevents an undecorated subclass from
        accidentally reusing another fact-container class's validated cache.
        """
        if "_definitions" not in cls.__dict__:
            msg = f"Class {cls.__module__}.{cls.__qualname__} must use @facts_dataclass"
            raise TypeError(msg)
        return cls._definitions

    @classmethod
    def collect(cls, collector: _AntaAdvisoryTest) -> Self:
        """Collect every cached definition and construct the concrete container.

        The validated field-name mapping ensures every required constructor value
        is supplied explicitly. The dynamic loop cannot preserve each field's
        distinct generic parameter internally, so this boundary relies on the
        validated declaration and the type-checker contract of ``fact_field``.
        Returning ``Self`` preserves the concrete nested ``Facts`` type and its
        precisely typed fields at the call site.
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

    def __init_subclass__(cls) -> None:
        """Require every feature-fact subclass to expose a valid identity."""
        # ``dataclass(slots=True)`` returns a replacement class, so zero-argument
        # ``super()`` can retain the pre-transformation class on older Python versions.
        super(FeatureFact, cls).__init_subclass__()
        if not isinstance(getattr(cls, "feature", None), (FeatureName, SubFeature)):
            msg = f"Class {cls.__module__}.{cls.__qualname__} must define 'feature' as a FeatureName or SubFeature"
            raise TypeError(msg)


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
class ConfigurationFact:
    """Common state and class-level identity for a nominal configuration fact."""

    feature: ClassVar[FeatureRef]
    state: ConfigurationState

    def __init_subclass__(cls) -> None:
        """Require every configuration-fact subclass to expose a valid identity."""
        # See ``FeatureFact.__init_subclass__`` for why this form of ``super`` is required.
        super(ConfigurationFact, cls).__init_subclass__()
        if not isinstance(getattr(cls, "feature", None), (FeatureName, SubFeature)):
            msg = f"Class {cls.__module__}.{cls.__qualname__} must define 'feature' as a FeatureName or SubFeature"
            raise TypeError(msg)


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
class CredentialSyntaxFact:
    """Common state and class-level identity for a nominal credential-syntax fact."""

    feature: ClassVar[FeatureRef]
    state: CredentialSyntaxState

    def __init_subclass__(cls) -> None:
        """Require every credential-syntax fact subclass to expose a valid identity."""
        # See ``FeatureFact.__init_subclass__`` for why this form of ``super`` is required.
        super(CredentialSyntaxFact, cls).__init_subclass__()
        if not isinstance(getattr(cls, "feature", None), (FeatureName, SubFeature)):
            msg = f"Class {cls.__module__}.{cls.__qualname__} must define 'feature' as a FeatureName or SubFeature"
            raise TypeError(msg)


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


@dataclass(frozen=True, slots=True)
class ComponentSoftwareFact:
    """Common version and class-level component identity for a nominal software fact."""

    component: ClassVar[str]
    version: str


class MitigationState(str, Enum):
    """Observed effectiveness of a possible mitigation."""

    EFFECTIVE = "effective"
    INEFFECTIVE = "ineffective"


@dataclass(frozen=True, slots=True)
class MitigationFact:
    """Common effectiveness state for a nominal mitigation fact."""

    state: MitigationState


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
