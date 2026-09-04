# Copyright (c) 2026 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Structured vulnerability-finding result models."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import TYPE_CHECKING, Any, TypeAlias

from anta._advisory.facts.models import (
    AvailableFact,
    ComponentSoftwareVersion,
    ConfigurationState,
    ConfigurationValue,
    FeatureState,
    FeatureValue,
    MitigationState,
    MitigationValue,
    UnavailableFact,
)

if TYPE_CHECKING:
    from anta._advisory.remediation import RemediationPlan
    from anta._eos.platform import PlatformIdentity
    from anta.device import DeviceVersion


class VersionRelation(str, Enum):
    """Relationship between an observed version and an advisory's affected scope."""

    AFFECTED = "affected"
    CONDITIONAL_FIXED = "conditionally fixed"
    FIXED = "fixed"
    OUTSIDE_SCOPE = "outside the affected releases"


@dataclass(frozen=True, slots=True)
class EosReleaseAssessment:
    """Advisory-specific interpretation of an observed EOS release."""

    fact: AvailableFact[DeviceVersion]
    relation: VersionRelation


@dataclass(frozen=True, slots=True)
class AffectedEosRelease(EosReleaseAssessment):
    """An observed EOS release confirmed to be affected."""

    relation: VersionRelation = field(default=VersionRelation.AFFECTED, init=False)


@dataclass(frozen=True, slots=True)
class ComponentVersionAssessment:
    """Advisory-specific interpretation of an observed EOS component version."""

    fact: AvailableFact[ComponentSoftwareVersion]
    relation: VersionRelation


@dataclass(frozen=True, slots=True)
class AffectedComponentVersion(ComponentVersionAssessment):
    """An observed EOS component version confirmed to be affected."""

    relation: VersionRelation = field(default=VersionRelation.AFFECTED, init=False)


class PlatformRelation(str, Enum):
    """Relationship between observed platform identity and advisory scope."""

    AFFECTED = "within the affected platform scope"
    OUTSIDE_SCOPE = "outside the affected platform scope"


@dataclass(frozen=True, slots=True)
class PlatformAssessment:
    """Advisory-specific interpretation of observed platform identity."""

    fact: AvailableFact[PlatformIdentity]
    relation: PlatformRelation


ExposureFact: TypeAlias = AvailableFact[FeatureValue] | AvailableFact[ConfigurationValue]
MitigatableCondition: TypeAlias = AffectedEosRelease | AffectedComponentVersion | ExposureFact
AffectedCondition: TypeAlias = MitigatableCondition | AvailableFact[MitigationValue]
VersionAssessment: TypeAlias = EosReleaseAssessment | ComponentVersionAssessment
FindingEvidence: TypeAlias = VersionAssessment | PlatformAssessment | ExposureFact | AvailableFact[MitigationValue]


def _is_affected_condition(value: object) -> bool:
    """Return whether a runtime value has one of the affected-condition shapes."""
    if isinstance(value, AvailableFact) and isinstance(value.value, MitigationValue):
        return value.value.state is MitigationState.INEFFECTIVE
    return _is_mitigatable_condition(value)


def _is_mitigatable_condition(value: object) -> bool:
    """Return whether a runtime value is an exposure that a mitigation can cover."""
    if isinstance(value, (AffectedEosRelease, AffectedComponentVersion)):
        return True
    if not isinstance(value, AvailableFact):
        return False
    if isinstance(value.value, FeatureValue):
        return value.value.state is FeatureState.ENABLED
    if isinstance(value.value, ConfigurationValue):
        return value.value.state is ConfigurationState.CONFIGURED
    return False


@dataclass(frozen=True, slots=True)
class MitigatedCondition:
    """One confirmed affected condition paired with the mitigations that cover it."""

    condition: MitigatableCondition
    mitigations: tuple[AvailableFact[MitigationValue], ...]

    def __post_init__(self) -> None:
        if not _is_mitigatable_condition(self.condition):
            msg = "Mitigated conditions require a confirmed affected condition"
            raise ValueError(msg)
        if not self.mitigations:
            msg = "Mitigated conditions must include at least one mitigation fact"
            raise ValueError(msg)
        if any(mitigation.value.state is not MitigationState.EFFECTIVE for mitigation in self.mitigations):
            msg = "Mitigated conditions may only include effective mitigation facts"
            raise ValueError(msg)


@dataclass(frozen=True, slots=True, kw_only=True)
class VulnerabilityResultBase:
    """Common identity for one vulnerability conclusion."""

    vulnerability_id: str

    def __post_init__(self) -> None:
        if not self.vulnerability_id:
            msg = "Vulnerability results require a vulnerability ID"
            raise ValueError(msg)


@dataclass(frozen=True, slots=True, kw_only=True)
class NotAffectedResult(VulnerabilityResultBase):
    """Every exposure path is closed by decisive available evidence."""

    decisive: tuple[FindingEvidence, ...]

    def __post_init__(self) -> None:
        VulnerabilityResultBase.__post_init__(self)
        if not self.decisive:
            msg = "Not-affected results require decisive evidence"
            raise ValueError(msg)


@dataclass(frozen=True, slots=True, kw_only=True)
class AffectedResult(VulnerabilityResultBase):
    """At least one confirmed affected condition is not mitigated."""

    conditions: tuple[AffectedCondition, ...]
    remediation: RemediationPlan
    context: tuple[EosReleaseAssessment | ComponentVersionAssessment | PlatformAssessment, ...] = ()

    def __post_init__(self) -> None:
        VulnerabilityResultBase.__post_init__(self)
        if not self.conditions:
            msg = "Affected results require affected conditions"
            raise ValueError(msg)
        if any(not _is_affected_condition(condition) for condition in self.conditions):
            msg = "Affected results require confirmed affected conditions"
            raise ValueError(msg)


@dataclass(frozen=True, slots=True, kw_only=True)
class MitigatedResult(VulnerabilityResultBase):
    """Every confirmed affected condition is paired with an effective mitigation."""

    mitigated_conditions: tuple[MitigatedCondition, ...]
    remediation: RemediationPlan
    context: tuple[EosReleaseAssessment | ComponentVersionAssessment | PlatformAssessment, ...] = ()

    def __post_init__(self) -> None:
        VulnerabilityResultBase.__post_init__(self)
        if not self.mitigated_conditions:
            msg = "Mitigated results require mitigated conditions and remediation"
            raise ValueError(msg)


@dataclass(frozen=True, slots=True, kw_only=True)
class InconclusiveResult(VulnerabilityResultBase):
    """Known indications remain dependent on an inherently unresolved condition."""

    indications: tuple[FindingEvidence, ...]
    unresolved: tuple[Unobservable, ...]
    remediation: RemediationPlan

    def __post_init__(self) -> None:
        VulnerabilityResultBase.__post_init__(self)
        if not self.indications or not self.unresolved:
            msg = "Inconclusive results require indications, unresolved conditions, and remediation"
            raise ValueError(msg)


@dataclass(frozen=True, slots=True, kw_only=True)
class ErrorResult(VulnerabilityResultBase):
    """Required observable evidence is unavailable."""

    problems: tuple[UnavailableFact[Any], ...]

    def __post_init__(self) -> None:
        VulnerabilityResultBase.__post_init__(self)
        if not self.problems:
            msg = "Error results require unavailable facts"
            raise ValueError(msg)


VulnerabilityResult: TypeAlias = NotAffectedResult | AffectedResult | MitigatedResult | InconclusiveResult | ErrorResult


class UnobservableKind(str, Enum):
    """Kind of condition that device evidence inherently cannot establish."""

    DEVICE_STATE_NOT_EXPOSED = "device state not exposed"
    EXTERNAL_STATE = "external state"
    HISTORICAL_STATE = "historical state"
    INCOMPLETE_PLATFORM_IDENTITY = "incomplete platform identity"
    OPERATOR_ACTION = "operator action"


@dataclass(frozen=True, slots=True)
class Unobservable:
    """One inherently unresolved condition used by an inconclusive result."""

    kind: UnobservableKind
    subject: str

    def __post_init__(self) -> None:
        if not self.subject or "\n" in self.subject:
            msg = "Unobservable subjects must be non-empty and single-line"
            raise ValueError(msg)
