# Copyright (c) 2023-2026 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Tests for anta.bugdb.models."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from anta.bugdb.models import AlertBaseDatabase, Bug, BugMatch, BugTagCondition, DeviceBugReport, QueryRule


class TestBugTagCondition:
    """Tests for BugTagCondition."""

    def test_creation(self) -> None:
        """Test basic creation."""
        cond = BugTagCondition(tag="bgpEnabled")
        assert cond.tag == "bgpEnabled"

    def test_frozen(self) -> None:
        """Test that the model is frozen."""
        cond = BugTagCondition(tag="bgpEnabled")
        with pytest.raises(Exception):  # noqa: B017, PT011
            cond.tag = "other"  # type: ignore[misc]


class TestBug:
    """Tests for Bug model."""

    def test_from_json(self) -> None:
        """Test parsing a bug entry from JSON-style dict."""
        data = {
            "bugId": 68683,
            "severity": "sev2",
            "securityAdvisoryURL": "",
            "cve": "",
            "alertSummary": "MAC flaps causing issues",
            "alertNote": "Details here",
            "product": "eos",
            "versionIntroduced": ["4.14.0"],
            "versionFixed": ["4.21.10", "4.22.4", "4.23.3", "4.24.0"],
            "bites": 16,
            "lastBiteTime": 1732241052,
            "exportedTime": 1672531200,
            "releaseNote": "Release note text",
            "conjunction": [[{"tag": "Sand"}, {"tag": "vxlanEnabled"}]],
        }
        bug = Bug.model_validate(data)
        assert bug.bug_id == 68683
        assert bug.severity == "sev2"
        assert bug.product == "eos"
        assert len(bug.version_introduced) == 1
        assert len(bug.version_fixed) == 4
        assert len(bug.conjunction) == 1
        assert len(bug.conjunction[0]) == 2
        assert bug.conjunction[0][0].tag == "Sand"
        assert bug.conjunction[0][1].tag == "vxlanEnabled"
        assert bug.bites == 16

    def test_no_conjunction(self) -> None:
        """Test a bug without conjunction field."""
        data = {
            "bugId": 12345,
            "severity": "sev1",
            "alertSummary": "Critical bug",
            "product": "eos",
            "versionIntroduced": ["4.20.0"],
            "versionFixed": ["4.20.5"],
        }
        bug = Bug.model_validate(data)
        assert bug.conjunction == []

    def test_multiple_conjunction_clauses(self) -> None:
        """Test OR of AND clauses."""
        data = {
            "bugId": 99999,
            "severity": "sev3",
            "alertSummary": "Test bug",
            "product": "eos",
            "versionIntroduced": ["4.20.0"],
            "versionFixed": ["4.25.0"],
            "conjunction": [
                [{"tag": "Sand"}, {"tag": "bgpEnabled"}],
                [{"tag": "Trident3"}],
            ],
        }
        bug = Bug.model_validate(data)
        assert len(bug.conjunction) == 2
        assert len(bug.conjunction[0]) == 2
        assert len(bug.conjunction[1]) == 1


class TestQueryRule:
    """Tests for QueryRule model."""

    def test_from_json(self) -> None:
        """Test parsing a queryRule entry."""
        data = {
            "id": 517,
            "query": 'let data = merge(`{_d}:/Sysdb/routing/bgp/config`)\ndata["asNumber"]["value"] != 0',
            "tag": "bgpEnabled",
            "revision": 1,
            "description": "BGP enabled rule",
            "pathFilters": ["/Sysdb/routing/bgp/config"],
        }
        rule = QueryRule.model_validate(data)
        assert rule.id == 517
        assert rule.tag == "bgpEnabled"
        assert rule.revision == 1
        assert rule.path_filters == ["/Sysdb/routing/bgp/config"]


class TestAlertBaseDatabase:
    """Tests for AlertBaseDatabase model."""

    def test_minimal(self) -> None:
        """Test minimal valid database."""
        data = {"bugs": []}
        db = AlertBaseDatabase.model_validate(data)
        assert db.bugs == []
        assert db.tag_implication == []
        assert db.query_rules == []

    def test_extra_fields_ignored(self) -> None:
        """Test that unknown top-level fields are ignored."""
        data = {
            "bugs": [],
            "genId": "abc",
            "releaseDate": "2024-01-01",
            "unknownField": "should be ignored",
            "anotherUnknown": 42,
        }
        db = AlertBaseDatabase.model_validate(data)
        assert db.gen_id == "abc"
        assert db.release_date == "2024-01-01"

    @pytest.mark.parametrize("filename", ["AlertBase-CVP.json"])
    def test_parse_real_file(self, filename: str) -> None:
        """Test parsing the real AlertBase-CVP.json file if available."""
        path = Path(filename)
        if not path.exists():
            pytest.skip(f"{filename} not found")
        with path.open() as f:
            data = json.load(f)
        db = AlertBaseDatabase.model_validate(data)
        assert len(db.bugs) > 0
        assert len(db.tag_implication) > 0


class TestDeviceBugReport:
    """Tests for DeviceBugReport model."""

    def test_creation(self) -> None:
        """Test creating a report."""
        report = DeviceBugReport(
            device_name="spine1",
            hw_model="DCS-7280SR3-48YC8-F",
            eos_version="4.30.1F",
            resolved_tags={"Sand", "bgpEnabled"},
            matching_bugs=[],
        )
        assert report.device_name == "spine1"
        assert "Sand" in report.resolved_tags
        assert report.matching_bugs == []

    def test_with_matches(self) -> None:
        """Test a report with matching bugs."""
        bug = Bug.model_validate(
            {
                "bugId": 12345,
                "severity": "sev2",
                "alertSummary": "Test",
                "product": "eos",
                "versionIntroduced": ["4.20.0"],
                "versionFixed": ["4.25.0"],
            }
        )
        match = BugMatch(bug=bug, matched_by="version-only")
        report = DeviceBugReport(
            device_name="leaf1",
            hw_model="DCS-7050SX3",
            eos_version="4.22.0F",
            matching_bugs=[match],
        )
        assert len(report.matching_bugs) == 1
        assert report.matching_bugs[0].matched_by == "version-only"
