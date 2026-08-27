# Copyright (c) 2026 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Data models for ANTA security advisories."""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class AdvisorySeverity(str, Enum):
    """Severity levels for security advisories and CVEs."""

    UNKNOWN = "unknown"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


_ADVISORY_SEVERITY_RANK = {
    AdvisorySeverity.UNKNOWN: 0,
    AdvisorySeverity.LOW: 1,
    AdvisorySeverity.MEDIUM: 2,
    AdvisorySeverity.HIGH: 3,
    AdvisorySeverity.CRITICAL: 4,
}


class AdvisoryModel(BaseModel):
    """Base model for immutable advisory metadata."""

    model_config = ConfigDict(extra="forbid", frozen=True)


class AdvisoryCVSSScore(AdvisoryModel):
    """A versioned CVSS base score and vector."""

    version: str
    score: float = Field(ge=0, le=10)
    vector: str


class AdvisoryCVE(AdvisoryModel):
    """A CVE associated with a security advisory."""

    cve_id: str
    severity: AdvisorySeverity
    cvss_scores: tuple[AdvisoryCVSSScore, ...] = ()


class AdvisoryMitigation(AdvisoryModel):
    """A temporary mitigation or workaround for a security advisory."""

    name: str
    details: str
    url: str | None = None


class AdvisoryResolution(AdvisoryModel):
    """A resolution for a security advisory."""

    name: str
    details: str
    url: str | None = None


class AdvisoryMetadata(AdvisoryModel):
    """Metadata associated with a security advisory test."""

    sa_number: str
    title: str
    severity: AdvisorySeverity
    cves: tuple[AdvisoryCVE, ...]
    url: str
    description: str
    resolutions: tuple[AdvisoryResolution, ...]
    mitigations: tuple[AdvisoryMitigation, ...] = ()

    @field_validator("cves")
    @classmethod
    def cve_ids_are_unique(cls, cves: tuple[AdvisoryCVE, ...]) -> tuple[AdvisoryCVE, ...]:
        """Ensure CVE IDs are unique within the advisory."""
        if len({cve.cve_id for cve in cves}) != len(cves):
            msg = "Advisory CVE IDs must be unique"
            raise ValueError(msg)
        return cves

    @model_validator(mode="after")
    def advisory_severity_is_not_below_cve_severity(self) -> AdvisoryMetadata:
        """Ensure the advisory severity is at least as high as every included CVE."""
        if not self.cves:
            return self

        highest_cve = max(self.cves, key=lambda cve: _ADVISORY_SEVERITY_RANK[cve.severity])
        if _ADVISORY_SEVERITY_RANK[self.severity] < _ADVISORY_SEVERITY_RANK[highest_cve.severity]:
            msg = f"Advisory severity '{self.severity.value}' cannot be below CVE '{highest_cve.cve_id}' severity '{highest_cve.severity.value}'"
            raise ValueError(msg)
        return self
