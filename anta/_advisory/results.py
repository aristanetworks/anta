# Copyright (c) 2026 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Private result models for ANTA security advisory tests."""

from __future__ import annotations

from pydantic import Field

from anta._advisory.models import _AdvisoryMetadata  # noqa: TC001  # Pydantic resolves this annotation at runtime.
from anta.result_manager.models import AntaTestStatus, AtomicTestResult, TestResult


class _AdvisoryAtomicTestResult(AtomicTestResult):
    """Atomic advisory result with optional vulnerability associations and remediations."""

    vulnerability_ids: tuple[str, ...] | None = Field(default=None, exclude=True)
    remediations: list[str] = Field(default_factory=list, exclude=True)


class _AdvisoryTestResult(TestResult):
    """Test result carrying private security advisory metadata and optional remediations."""

    advisory: _AdvisoryMetadata = Field(exclude=True)
    remediations: list[str] = Field(default_factory=list, exclude=True)

    def add(
        self,
        description: str,
        status: AntaTestStatus = AntaTestStatus.UNSET,
        messages: list[str] | None = None,
        *,
        vulnerability_ids: tuple[str, ...] | None = None,
        remediations: list[str] | None = None,
    ) -> _AdvisoryAtomicTestResult:
        """Create an atomic advisory result with optional vulnerability associations and remediations."""
        if vulnerability_ids is not None:
            if not vulnerability_ids:
                msg = "vulnerability_ids must contain at least one vulnerability ID when provided"
                raise ValueError(msg)
            if len(vulnerability_ids) != len(set(vulnerability_ids)):
                msg = "vulnerability_ids must not contain duplicate vulnerability IDs"
                raise ValueError(msg)
            requested_vulnerabilities = set(vulnerability_ids)
            advisory_vulnerability_ids = {vulnerability.id for vulnerability in self.advisory.vulnerabilities}
            if unknown_vulnerabilities := requested_vulnerabilities - advisory_vulnerability_ids:
                msg = f"Unknown vulnerability IDs for advisory {self.advisory.sa_number}: {', '.join(sorted(unknown_vulnerabilities))}"
                raise ValueError(msg)
            vulnerability_ids = tuple(vulnerability.id for vulnerability in self.advisory.vulnerabilities if vulnerability.id in requested_vulnerabilities)

        result = _AdvisoryAtomicTestResult(
            description=description,
            parent=self,
            result=status,
            messages=messages or [],
            vulnerability_ids=vulnerability_ids,
            remediations=remediations or [],
        )
        self.atomic_results.append(result)
        return result


def _get_advisory_metadata(result: TestResult) -> _AdvisoryMetadata | None:
    """Return advisory metadata from an advisory result, otherwise None."""
    return result.advisory if isinstance(result, _AdvisoryTestResult) else None


def _get_atomic_vulnerability_ids(result: AtomicTestResult) -> tuple[str, ...] | None:
    """Return explicitly associated vulnerability IDs from an advisory atomic result."""
    return result.vulnerability_ids if isinstance(result, _AdvisoryAtomicTestResult) else None
