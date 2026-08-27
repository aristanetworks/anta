# Copyright (c) 2026 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Unit tests for security advisory Markdown reporting."""

from __future__ import annotations

from pathlib import Path

import pytest

from anta._advisory.reporting import SecurityAdvisoryReport, generate_security_advisory_md_report
from anta.result_manager import ResultManager
from anta.result_manager.models import AntaTestStatus
from tests.units._advisory.conftest import ADVISORY
from tests.units._advisory.reporting_data import build_security_advisory_result, build_security_advisory_result_manager


def test_security_advisory_markdown_report(tmp_path: Path) -> None:
    """Verify a realistic fleet report is clean, grouped, and deterministic."""
    report = SecurityAdvisoryReport.from_result_manager(build_security_advisory_result_manager())
    output = tmp_path / "advisories.md"

    generate_security_advisory_md_report(report, output)

    expected = (Path(__file__).parents[2] / "data" / "test_security_advisory_md_report.md").read_text(encoding="utf-8")
    assert output.read_text(encoding="utf-8") == expected


def test_security_advisory_report_rejects_conflicting_metadata() -> None:
    """Verify one advisory number cannot be rendered with conflicting metadata."""
    manager = ResultManager()
    manager.add(build_security_advisory_result("leaf1", AntaTestStatus.SUCCESS, "No exposure detected.", ADVISORY))
    manager.add(
        build_security_advisory_result(
            "leaf2",
            AntaTestStatus.FAILURE,
            "Exposure detected.",
            advisory=ADVISORY.model_copy(update={"title": "Conflicting title"}),
        )
    )

    with pytest.raises(ValueError, match="Conflicting metadata"):
        SecurityAdvisoryReport.from_result_manager(manager)


def test_security_advisory_markdown_optional_content(tmp_path: Path) -> None:
    """Verify the report handles advisories without scores or published guidance."""
    advisory = ADVISORY.model_copy(
        update={
            "sa_number": "0002",
            "cves": (ADVISORY.cves[0].model_copy(update={"cvss_scores": ()}),),
            "mitigations": (ADVISORY.mitigations[0].model_copy(update={"url": None}),),
            "resolutions": (),
        }
    )
    manager = ResultManager()
    manager.add(build_security_advisory_result("leaf1", AntaTestStatus.SUCCESS, "No exposure detected.", advisory))
    manager.add(build_security_advisory_result("leaf2", AntaTestStatus.SUCCESS, "No exposure detected.", advisory.model_copy(update={"sa_number": "0001"})))
    report = SecurityAdvisoryReport.from_result_manager(manager)
    output = tmp_path / "advisories.md"

    generate_security_advisory_md_report(report, output)

    content = output.read_text(encoding="utf-8")
    assert "[SA0001: Test advisory](#sa-0001)" in content
    assert "| CVE-2026-0001 | Medium | - | - | - |" in content
    assert "- **Workaround:** Apply the temporary workaround." in content
    assert "[Reference]" not in content
    assert "*No resolutions are published for this advisory.*" in content
