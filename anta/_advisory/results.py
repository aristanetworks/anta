# Copyright (c) 2026 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Private result models for ANTA security advisory tests."""

from __future__ import annotations

from pydantic import Field

from anta._advisory.models import _AdvisoryMetadata  # noqa: TC001  # Pydantic resolves this annotation at runtime.
from anta.result_manager.models import AntaTestStatus, AtomicTestResult, TestResult


class _AdvisoryAtomicTestResult(AtomicTestResult):
    """Atomic advisory result with optional CVE associations and remediations."""

    cve_ids: tuple[str, ...] | None = Field(default=None, exclude=True)
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
        cve_ids: tuple[str, ...] | None = None,
        remediations: list[str] | None = None,
    ) -> _AdvisoryAtomicTestResult:
        """Create an atomic advisory result with optional CVE associations and remediations."""
        if cve_ids is not None:
            if not cve_ids:
                msg = "cve_ids must contain at least one CVE ID when provided"
                raise ValueError(msg)
            if len(cve_ids) != len(set(cve_ids)):
                msg = "cve_ids must not contain duplicate CVE IDs"
                raise ValueError(msg)
            requested_cves = set(cve_ids)
            advisory_cves = {cve.cve_id for cve in self.advisory.cves}
            if unknown_cves := requested_cves - advisory_cves:
                msg = f"Unknown CVE IDs for advisory {self.advisory.sa_number}: {', '.join(sorted(unknown_cves))}"
                raise ValueError(msg)
            cve_ids = tuple(cve.cve_id for cve in self.advisory.cves if cve.cve_id in requested_cves)

        result = _AdvisoryAtomicTestResult(
            description=description,
            parent=self,
            result=status,
            messages=messages or [],
            cve_ids=cve_ids,
            remediations=remediations or [],
        )
        self.atomic_results.append(result)
        return result


def _get_advisory_metadata(result: TestResult) -> _AdvisoryMetadata | None:
    """Return advisory metadata from an advisory result, otherwise None."""
    return result.advisory if isinstance(result, _AdvisoryTestResult) else None


def _get_atomic_cve_ids(result: AtomicTestResult) -> tuple[str, ...] | None:
    """Return explicitly associated CVE IDs from an advisory atomic result."""
    return result.cve_ids if isinstance(result, _AdvisoryAtomicTestResult) else None
