# Copyright (c) 2026 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Render and project structured vulnerability findings onto ANTA results."""

from __future__ import annotations

from typing import TYPE_CHECKING

from typing_extensions import assert_never

from anta._advisory.facts.models import ComponentSoftwareVersion, ConfigurationValue, FactProblemKind, FactSourceKind, FeatureName, MitigationValue, SubFeature
from anta._advisory.findings.models import (
    AffectedResult,
    ErrorResult,
    FindingEvidence,
    InconclusiveResult,
    MitigatedResult,
    NotAffectedResult,
    PlatformAssessment,
    SoftwareAssessment,
    VulnerabilityResult,
)
from anta._advisory.results import _AdvisoryAtomicTestResult, _get_atomic_vulnerability_ids
from anta._advisory.status import AdvisoryStatus, project_advisory_status

if TYPE_CHECKING:
    from anta._advisory.facts.models import AvailableFact, UnavailableFact

PAIR_COUNT = 2


def _render_evidence(evidence: FindingEvidence) -> str:
    """Render one typed piece of finding evidence as a factual clause."""
    if isinstance(evidence, SoftwareAssessment):
        value = evidence.fact.value
        if isinstance(value, ComponentSoftwareVersion):
            return f"{value.component} '{value.version}' is {evidence.relation.value}"
        return f"{evidence.fact.definition.label} '{value}' is {evidence.relation.value}"
    if isinstance(evidence, PlatformAssessment):
        return f"platform '{evidence.fact.value.model}' is {evidence.relation.value}"
    if isinstance(evidence.value, MitigationValue):
        return f"{evidence.definition.label} is {evidence.value.state.value}"
    feature = evidence.value.feature
    feature_name = f"{feature.parent.value} {feature.name}" if isinstance(feature, SubFeature) else feature.value
    if isinstance(evidence.value, ConfigurationValue):
        return f"the {feature_name} configuration is {evidence.value.state.value}"
    suffix = " feature" if isinstance(feature, FeatureName) else ""
    return f"the {feature_name}{suffix} is {evidence.value.state.value}"


def _render_problem(problem: UnavailableFact[object]) -> str:
    """Explain why the test could not determine one required fact."""
    subject = problem.definition.label
    if problem.source.kind is FactSourceKind.COMMAND:
        command = f"'{problem.source.name}'"
        if problem.problem is FactProblemKind.COLLECTION_FAILED:
            reason = f"{command} could not be collected"
        elif problem.problem is FactProblemKind.MISSING:
            reason = f"the {command} output is incomplete"
        else:
            reason = f"the {command} output is invalid"
    elif problem.problem is FactProblemKind.MISSING:
        reason = f"it is missing from {problem.source.name}"
    else:
        reason = f"{problem.source.name} is invalid"
    return f"The test could not determine the {subject} because {reason}."


def _join_clauses(clauses: tuple[str, ...]) -> str:
    """Join factual clauses with deterministic conjunctions."""
    if len(clauses) == 1:
        return clauses[0]
    if len(clauses) == PAIR_COUNT:
        return f"{clauses[0]} and {clauses[1]}"
    return f"{', '.join(clauses[:-1])}, and {clauses[-1]}"


def _render_mitigation(mitigation: AvailableFact[MitigationValue]) -> str:
    """Render one observed mitigation as a factual clause."""
    return f"{mitigation.definition.label} is {mitigation.value.state.value}"


def _render_result(result: VulnerabilityResult) -> tuple[AdvisoryStatus, str, str]:
    """Render one structured finding into the current advisory projection contract."""
    if isinstance(result, NotAffectedResult):
        evidence = _join_clauses(tuple(_render_evidence(item) for item in result.decisive))
        return AdvisoryStatus.NOT_AFFECTED, f"The device is not affected because {evidence}.", ""
    if isinstance(result, AffectedResult):
        evidence = _join_clauses(tuple(_render_evidence(item) for item in (*result.context, *result.exposure)))
        return AdvisoryStatus.AFFECTED, f"The device is affected because {evidence}.", result.remediation
    if isinstance(result, MitigatedResult):
        mitigated_exposures = tuple(
            _join_clauses(
                (
                    _render_evidence(item.exposure),
                    *(_render_mitigation(mitigation) for mitigation in item.mitigations),
                )
            )
            for item in result.mitigated_exposures
        )
        evidence = _join_clauses(
            (
                *(_render_evidence(item) for item in result.context),
                *mitigated_exposures,
            )
        )
        return AdvisoryStatus.MITIGATED, f"The device is affected but mitigated because {evidence}.", result.remediation
    if isinstance(result, InconclusiveResult):
        indications = _join_clauses(tuple(_render_evidence(item) for item in result.indications))
        unresolved = _join_clauses(tuple(f"{item.subject} is {item.kind.value}" for item in result.unresolved))
        message = f"The assessment is inconclusive and the device may be affected. Indications: {indications}. Unresolved: {unresolved}."
        return AdvisoryStatus.INCONCLUSIVE, message, result.remediation
    if isinstance(result, ErrorResult):
        return AdvisoryStatus.ERROR, " ".join(_render_problem(problem) for problem in result.problems), ""
    return assert_never(result)


def project_vulnerability_result(result: _AdvisoryAtomicTestResult, finding: VulnerabilityResult) -> None:
    """Validate, render, and project one vulnerability finding onto an atomic result."""
    if _get_atomic_vulnerability_ids(result) != (finding.vulnerability_id,):
        msg = "The structured finding must match the atomic result's single vulnerability association"
        raise ValueError(msg)
    status, message, remediation = _render_result(finding)
    project_advisory_status(result, status, message, remediation)
