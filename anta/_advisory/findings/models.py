# Copyright (c) 2026 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Structured vulnerability-finding result models."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import TYPE_CHECKING, Any, TypeAlias

from anta._advisory.facts.models import AvailableFact, FeatureValue, MitigationState, MitigationValue, UnavailableFact

if TYPE_CHECKING:
    from anta.device import DeviceVersion


class SoftwareRelation(str, Enum):
    """Relationship between observed software and an advisory's affected scope."""

    AFFECTED = "affected"
    FIXED = "fixed"
    OUTSIDE_SCOPE = "outside the affected releases"


@dataclass(frozen=True, slots=True)
class SoftwareAssessment:
    """Advisory-specific interpretation of an observed EOS version fact."""

    fact: AvailableFact[DeviceVersion]
    relation: SoftwareRelation


ExposureFact: TypeAlias = AvailableFact[FeatureValue]
FindingEvidence: TypeAlias = SoftwareAssessment | ExposureFact


@dataclass(frozen=True, slots=True)
class MitigatedExposure:
    """One exposure paired with the observed mitigations that cover it."""

    exposure: ExposureFact
    mitigations: tuple[AvailableFact[MitigationValue], ...]

    def __post_init__(self) -> None:
        if not self.mitigations:
            msg = "Mitigated exposures must include at least one mitigation fact"
            raise ValueError(msg)
        if any(mitigation.value.state is not MitigationState.EFFECTIVE for mitigation in self.mitigations):
            msg = "Mitigated exposures may only include effective mitigation facts"
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
    """At least one active exposure is not mitigated."""

    exposure: tuple[ExposureFact, ...]
    remediation: str
    context: tuple[SoftwareAssessment, ...] = ()

    def __post_init__(self) -> None:
        VulnerabilityResultBase.__post_init__(self)
        if not self.exposure or not self.remediation:
            msg = "Affected results require exposure evidence and remediation"
            raise ValueError(msg)


@dataclass(frozen=True, slots=True, kw_only=True)
class MitigatedResult(VulnerabilityResultBase):
    """Every active exposure is paired with an effective mitigation."""

    mitigated_exposures: tuple[MitigatedExposure, ...]
    remediation: str
    context: tuple[SoftwareAssessment, ...] = ()

    def __post_init__(self) -> None:
        VulnerabilityResultBase.__post_init__(self)
        if not self.mitigated_exposures or not self.remediation:
            msg = "Mitigated results require mitigated exposures and remediation"
            raise ValueError(msg)


@dataclass(frozen=True, slots=True, kw_only=True)
class InconclusiveResult(VulnerabilityResultBase):
    """Known indications remain dependent on an inherently unresolved condition."""

    indications: tuple[FindingEvidence, ...]
    unresolved: tuple[Unobservable, ...]
    remediation: str

    def __post_init__(self) -> None:
        VulnerabilityResultBase.__post_init__(self)
        if not self.indications or not self.unresolved or not self.remediation:
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
