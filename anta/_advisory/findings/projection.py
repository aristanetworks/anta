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
    ComponentVersionAssessment,
    EosReleaseAssessment,
    ErrorResult,
    FindingEvidence,
    InconclusiveResult,
    MitigatedResult,
    NotAffectedResult,
    PlatformAssessment,
    VulnerabilityResult,
    VulnerabilityStatus,
)
from anta.result_manager.models import AntaTestStatus

if TYPE_CHECKING:
    from anta._advisory.facts.models import AvailableFact, UnavailableFact
    from anta._advisory.results import _AdvisoryAtomicTestResult, _AdvisoryTestResult
PAIR_COUNT = 2


_VULNERABILITY_STATUS_TO_ANTA_STATUS = {
    VulnerabilityStatus.NOT_AFFECTED: AntaTestStatus.SUCCESS,
    VulnerabilityStatus.MITIGATED: AntaTestStatus.SUCCESS,
    VulnerabilityStatus.INCONCLUSIVE: AntaTestStatus.FAILURE,
    VulnerabilityStatus.AFFECTED: AntaTestStatus.FAILURE,
    VulnerabilityStatus.ERROR: AntaTestStatus.ERROR,
}


def _get_anta_status(finding: VulnerabilityResult) -> AntaTestStatus:
    """Return the generic ANTA status for a vulnerability finding."""
    return _VULNERABILITY_STATUS_TO_ANTA_STATUS[finding.status]


def _render_evidence(evidence: FindingEvidence) -> str:
    """Render one typed piece of finding evidence as a factual clause."""
    if isinstance(evidence, (EosReleaseAssessment, ComponentVersionAssessment)):
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
        elif problem.problem is FactProblemKind.UNSUPPORTED:
            reason = f"{command} is not supported"
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


def _render_result(result: VulnerabilityResult) -> str:
    """Render one structured finding as an assessment message."""
    if isinstance(result, NotAffectedResult):
        evidence = _join_clauses(tuple(_render_evidence(item) for item in result.decisive))
        return f"The device is not affected because {evidence}."
    if isinstance(result, AffectedResult):
        evidence = _join_clauses(tuple(_render_evidence(item) for item in (*result.context, *result.conditions)))
        return f"The device is affected because {evidence}."
    if isinstance(result, MitigatedResult):
        mitigated_conditions = tuple(
            _join_clauses(
                (
                    _render_evidence(item.condition),
                    *(_render_mitigation(mitigation) for mitigation in item.mitigations),
                )
            )
            for item in result.mitigated_conditions
        )
        evidence = _join_clauses(
            (
                *(_render_evidence(item) for item in result.context),
                *mitigated_conditions,
            )
        )
        return f"The device is affected but mitigated because {evidence}."
    if isinstance(result, InconclusiveResult):
        indications = _join_clauses(tuple(_render_evidence(item) for item in result.indications))
        unresolved = _join_clauses(tuple(f"{item.subject} is {item.kind.value}" for item in result.unresolved))
        return f"The assessment is inconclusive and the device may be affected. Indications: {indications}. Unresolved: {unresolved}."
    if isinstance(result, ErrorResult):
        return " ".join(_render_problem(problem) for problem in result.problems)
    return assert_never(result)


def project_vulnerability_result(result: _AdvisoryTestResult, finding: VulnerabilityResult) -> _AdvisoryAtomicTestResult:
    """Render one vulnerability finding and add its atomic result."""
    status = _get_anta_status(finding)
    message = _render_result(finding)
    atomic_result = result.add(
        f"Verify {finding.vulnerability_id}.",
        status,
        [message],
        vulnerability_id=finding.vulnerability_id,
    )
    atomic_result.set_finding(finding)
    return atomic_result
