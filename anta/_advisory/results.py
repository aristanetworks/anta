# Copyright (c) 2026 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Private result models for ANTA security advisory tests."""

from __future__ import annotations

from typing import TYPE_CHECKING

from pydantic import Field
from typing_extensions import assert_never

from anta._advisory.findings.models import AffectedResult, ErrorResult, InconclusiveResult, MitigatedResult, NotAffectedResult, VulnerabilityResult
from anta._advisory.models import _AdvisoryMetadata  # noqa: TC001  # Pydantic resolves this annotation at runtime.
from anta.result_manager.models import AntaTestStatus, AtomicTestResult, TestResult

if TYPE_CHECKING:
    from anta._advisory.remediation import RemediationPlan


class _AdvisoryAtomicTestResult(AtomicTestResult):
    """Atomic advisory result with an optional structured vulnerability finding."""

    vulnerability_id: str | None = Field(default=None, exclude=True)
    if TYPE_CHECKING:
        finding: VulnerabilityResult | None = None
    else:
        # Findings are immutable domain objects retained in memory. Keep Pydantic from
        # recursively validating or serializing their full object graph.
        finding: object | None = Field(default=None, exclude=True, repr=False)

    @property
    def remediation(self) -> RemediationPlan | None:
        """Return the remediation carried by the structured finding, when applicable."""
        if isinstance(self.finding, (AffectedResult, MitigatedResult, InconclusiveResult)):
            return self.finding.remediation
        if self.finding is None or isinstance(self.finding, (NotAffectedResult, ErrorResult)):
            return None
        return assert_never(self.finding)

    def set_finding(self, finding: VulnerabilityResult) -> None:
        """Retain the single structured finding produced for this atomic result."""
        if self.finding is not None:
            msg = "An advisory atomic result may only retain one structured finding"
            raise ValueError(msg)
        self.finding = finding


class _AdvisoryTestResult(TestResult):
    """Test result carrying private security advisory metadata."""

    advisory: _AdvisoryMetadata = Field(exclude=True)

    @property
    def findings(self) -> tuple[VulnerabilityResult, ...]:
        """Return structured findings from advisory atomics in insertion order."""
        return tuple(atomic.finding for atomic in self.atomic_results if isinstance(atomic, _AdvisoryAtomicTestResult) and atomic.finding is not None)

    def add(
        self,
        description: str,
        status: AntaTestStatus = AntaTestStatus.UNSET,
        messages: list[str] | None = None,
        *,
        vulnerability_id: str | None = None,
    ) -> _AdvisoryAtomicTestResult:
        """Create an atomic advisory result with an optional vulnerability association."""
        if vulnerability_id is not None:
            advisory_vulnerability_ids = {vulnerability.id for vulnerability in self.advisory.vulnerabilities}
            if vulnerability_id not in advisory_vulnerability_ids:
                msg = f"Unknown vulnerability ID for advisory {self.advisory.sa_number}: {vulnerability_id}"
                raise ValueError(msg)

        result = _AdvisoryAtomicTestResult(
            description=description,
            parent=self,
            result=status,
            messages=messages or [],
            vulnerability_id=vulnerability_id,
        )
        self.atomic_results.append(result)
        return result


def _get_advisory_metadata(result: TestResult) -> _AdvisoryMetadata | None:
    """Return advisory metadata from an advisory result, otherwise None."""
    return result.advisory if isinstance(result, _AdvisoryTestResult) else None


def _get_atomic_vulnerability_id(result: AtomicTestResult) -> str | None:
    """Return the explicitly associated vulnerability ID from an advisory atomic result."""
    return result.vulnerability_id if isinstance(result, _AdvisoryAtomicTestResult) else None
