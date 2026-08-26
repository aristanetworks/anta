# Copyright (c) 2026 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Data models for ANTA security advisories."""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, ConfigDict, Field


class AdvisorySeverity(str, Enum):
    """Severity levels for security advisories and CVEs."""

    UNKNOWN = "unknown"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


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
