# Copyright (c) 2026 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Data models for ANTA security advisories."""

from __future__ import annotations

from datetime import date
from enum import Enum
from typing import Annotated

from pydantic import BaseModel, ConfigDict, StringConstraints, field_validator

_NonEmptyString = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]


class _AdvisoryVulnerabilitySeverity(str, Enum):
    """Normalized severity levels for advisory vulnerabilities."""

    UNKNOWN = "unknown"
    NONE = "none"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


_ADVISORY_VULNERABILITY_SEVERITY_RANK = {
    _AdvisoryVulnerabilitySeverity.UNKNOWN: 0,
    _AdvisoryVulnerabilitySeverity.NONE: 1,
    _AdvisoryVulnerabilitySeverity.LOW: 2,
    _AdvisoryVulnerabilitySeverity.MEDIUM: 3,
    _AdvisoryVulnerabilitySeverity.HIGH: 4,
    _AdvisoryVulnerabilitySeverity.CRITICAL: 5,
}


class _AdvisoryModel(BaseModel):
    """Base model for immutable advisory metadata."""

    model_config = ConfigDict(extra="forbid", frozen=True)


class _AdvisoryVulnerability(_AdvisoryModel):
    """A vulnerability associated with a security advisory."""

    id: _NonEmptyString
    description: _NonEmptyString
    severity: _AdvisoryVulnerabilitySeverity = _AdvisoryVulnerabilitySeverity.UNKNOWN


class _AdvisoryMetadata(_AdvisoryModel):
    """Metadata associated with a security advisory test."""

    sa_number: str
    title: str
    last_updated: date
    vulnerabilities: tuple[_AdvisoryVulnerability, ...]
    url: str
    description: str

    @field_validator("vulnerabilities")
    @classmethod
    def vulnerability_ids_are_unique(cls, vulnerabilities: tuple[_AdvisoryVulnerability, ...]) -> tuple[_AdvisoryVulnerability, ...]:
        """Ensure vulnerability IDs are unique within the advisory."""
        if len({vulnerability.id.casefold() for vulnerability in vulnerabilities}) != len(vulnerabilities):
            msg = "Advisory vulnerability IDs must be unique"
            raise ValueError(msg)
        return vulnerabilities
