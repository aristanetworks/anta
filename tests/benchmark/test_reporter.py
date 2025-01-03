# Copyright (c) 2023-2025 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Benchmark tests for anta.reporter."""

import json
import logging
from pathlib import Path

import pytest

from anta.reporter import ReportJinja, ReportTable
from anta.reporter.csv_reporter import ReportCsv
from anta.reporter.md_reporter import MDReportGenerator
from anta.result_manager import ResultManager

logger = logging.getLogger(__name__)

DATA_DIR: Path = Path(__file__).parents[1].resolve() / "data"


@pytest.mark.benchmark
@pytest.mark.dependency(depends=["anta_benchmark"], scope="package")
def test_table_all(results: ResultManager) -> None:
    """Benchmark ReportTable.report_all()."""
    reporter = ReportTable()
    reporter.report(results)


@pytest.mark.benchmark
@pytest.mark.dependency(depends=["anta_benchmark"], scope="package")
def test_table_devices(results: ResultManager) -> None:
    """Benchmark ReportTable.report_summary_devices()."""
    reporter = ReportTable()
    reporter.report_summary_devices(results)


@pytest.mark.benchmark
@pytest.mark.dependency(depends=["anta_benchmark"], scope="package")
def test_table_tests(results: ResultManager) -> None:
    """Benchmark ReportTable.report_summary_tests()."""
    reporter = ReportTable()
    reporter.report_summary_tests(results)


@pytest.mark.benchmark
@pytest.mark.dependency(depends=["anta_benchmark"], scope="package")
def test_json(results: ResultManager) -> None:
    """Benchmark JSON report."""
    assert isinstance(results.json, str)


@pytest.mark.benchmark
@pytest.mark.dependency(depends=["anta_benchmark"], scope="package")
def test_jinja(results: ResultManager) -> None:
    """Benchmark ReportJinja."""
    assert isinstance(ReportJinja(template_path=DATA_DIR / "template.j2").render(json.loads(results.json)), str)


@pytest.mark.benchmark
@pytest.mark.dependency(depends=["anta_benchmark"], scope="package")
def test_csv(results: ResultManager, tmp_path: Path) -> None:
    """Benchmark ReportCsv.generate()."""
    ReportCsv.generate(results=results, csv_filename=tmp_path / "report.csv")


@pytest.mark.benchmark
@pytest.mark.dependency(depends=["anta_benchmark"], scope="package")
def test_markdown(results: ResultManager, tmp_path: Path) -> None:
    """Benchmark MDReportGenerator.generate()."""
    MDReportGenerator.generate(results=results, md_filename=tmp_path / "report.md")
