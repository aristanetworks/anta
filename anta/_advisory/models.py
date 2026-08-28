# Copyright (c) 2026 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Data models for ANTA security advisories."""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, ConfigDict, field_validator


class _AdvisoryCVESeverity(str, Enum):
    """Severity levels for security advisories and CVEs."""

    UNKNOWN = "unknown"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


_ADVISORY_CVE_SEVERITY_RANK = {
    _AdvisoryCVESeverity.UNKNOWN: 0,
    _AdvisoryCVESeverity.LOW: 1,
    _AdvisoryCVESeverity.MEDIUM: 2,
    _AdvisoryCVESeverity.HIGH: 3,
    _AdvisoryCVESeverity.CRITICAL: 4,
}


class _AdvisoryModel(BaseModel):
    """Base model for immutable advisory metadata."""

    model_config = ConfigDict(extra="forbid", frozen=True)


class _AdvisoryCVE(_AdvisoryModel):
    """A CVE associated with a security advisory."""

    cve_id: str
    severity: _AdvisoryCVESeverity
    description: str


class _AdvisoryMetadata(_AdvisoryModel):
    """Metadata associated with a security advisory test."""

    sa_number: str
    title: str
    cves: tuple[_AdvisoryCVE, ...]
    url: str
    description: str

    @field_validator("cves")
    @classmethod
    def cve_ids_are_unique(cls, cves: tuple[_AdvisoryCVE, ...]) -> tuple[_AdvisoryCVE, ...]:
        """Ensure CVE IDs are unique within the advisory."""
        if len({cve.cve_id for cve in cves}) != len(cves):
            msg = "Advisory CVE IDs must be unique"
            raise ValueError(msg)
        return cves
