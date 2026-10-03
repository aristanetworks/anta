# Copyright (c) 2023-2026 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Pydantic models for the Arista AlertBase bug database."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class BugTagCondition(BaseModel):
    """A single tag condition in a conjunction clause."""

    model_config = ConfigDict(frozen=True)

    tag: str


class Bug(BaseModel):
    """A bug entry from AlertBase-CVP.json."""

    model_config = ConfigDict(populate_by_name=True)

    bug_id: int = Field(alias="bugId")
    severity: str
    security_advisory_url: str = Field(alias="securityAdvisoryURL", default="")
    cve: str = ""
    alert_summary: str = Field(alias="alertSummary")
    alert_note: str = Field(alias="alertNote", default="")
    product: str
    version_introduced: list[str] = Field(alias="versionIntroduced")
    version_fixed: list[str] = Field(alias="versionFixed")
    bites: int = 0
    last_bite_time: int = Field(alias="lastBiteTime", default=0)
    exported_time: int = Field(alias="exportedTime", default=0)
    release_note: str = Field(alias="releaseNote", default="")
    conjunction: list[list[BugTagCondition]] = []
    hotfix_ids: list[int] = Field(alias="hotfixIds", default_factory=list)


class QueryRule(BaseModel):
    """A query rule mapping a tag to a SysDB query."""

    model_config = ConfigDict(populate_by_name=True)

    id: int
    query: str
    tag: str
    revision: int = 1
    description: str = ""
    path_filters: list[str] = Field(alias="pathFilters", default_factory=list)


class Release(BaseModel):
    """An EOS release entry."""

    release: str
    type: str
    product: str


class AlertBaseDatabase(BaseModel):
    """Top-level model for the AlertBase-CVP.json file."""

    model_config = ConfigDict(populate_by_name=True, extra="ignore")

    gen_id: str = Field(alias="genId", default="")
    release_date: str = Field(alias="releaseDate", default="")
    bugs: list[Bug]
    tag_implication: list[list[str]] = Field(alias="tagImplication", default_factory=list)
    release_graph: list[list[str]] = Field(alias="releaseGraph", default_factory=list)
    releases: list[Release] = Field(default_factory=list)
    query_rules: list[QueryRule] = Field(alias="queryRules", default_factory=list)
    query_rules_rev: list[QueryRule] = Field(alias="queryRulesRev", default_factory=list)


class BugMatch(BaseModel):
    """A bug that matched a device."""

    bug: Bug
    matched_by: str


class DeviceBugReport(BaseModel):
    """Result of bug analysis for a single device."""

    device_name: str
    hw_model: str
    eos_version: str
    terminattr_version: str = ""
    resolved_tags: set[str] = Field(default_factory=set)
    matching_bugs: list[BugMatch] = Field(default_factory=list)
