# Copyright (c) 2026 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Tests for the README animation capture helpers."""

from __future__ import annotations

import io
import json
import subprocess
import sys
from pathlib import Path

import yaml
from rich.console import Console

from anta.reporter.table_reporter import ReportTable
from anta.result_manager import ResultManager
from anta.result_manager.models import AntaTestStatus
from anta.result_manager.models import TestResult as AntaTestResult

REPOSITORY_ROOT = Path(__file__).parents[2]
ASCIINEMA_DIRECTORY = REPOSITORY_ROOT / ".github" / "asciinema"
FILTER_CAST = ASCIINEMA_DIRECTORY / "filter_cast.py"
PREPARE_NRFU_CATALOG = ASCIINEMA_DIRECTORY / "prepare_nrfu_catalog.py"
EXPECTED_DEMO_CATALOG_ENTRIES = 41
EXPECTED_PROGRESS_DURATION = 4


def run_script(script: Path, *args: Path | str) -> subprocess.CompletedProcess[str]:
    """Run an asciinema helper with the current Python interpreter."""
    return subprocess.run(  # noqa: S603
        [sys.executable, str(script), *(str(argument) for argument in args)],
        check=False,
        capture_output=True,
        text=True,
    )


def write_cast(path: Path, events: list[dict[str, object] | list[object]]) -> None:
    """Write asciicast v3 events as newline-delimited JSON."""
    path.write_text("".join(f"{json.dumps(event)}\n" for event in events), encoding="utf-8")


def cast_header() -> dict[str, object]:
    """Return the minimal header accepted by the cast filter."""
    return {"version": 3, "term": {"cols": 120, "rows": 22}, "command": "private command"}


def test_filter_cast_supports_current_nrfu_table(tmp_path: Path) -> None:
    """Verify the filter recognizes the title, borders, and statuses emitted by Rich."""
    manager = ResultManager()
    manager.results = [
        AntaTestResult(
            name="leaf1",
            test="VerifySuccess",
            categories=["system"],
            description="Successful test",
            result=AntaTestStatus.SUCCESS,
        ),
        AntaTestResult(
            name="leaf1",
            test="VerifyFailure",
            categories=["system"],
            description="Failed test",
            result=AntaTestStatus.FAILURE,
            messages=["Expected failure"],
        ),
    ]
    rendered_table = io.StringIO()
    console = Console(file=rendered_table, force_terminal=True, color_system="truecolor", width=120)
    console.print(ReportTable().generate(manager))

    source = tmp_path / "raw.cast"
    destination = tmp_path / "filtered.cast"
    write_cast(
        source,
        [
            cast_header(),
            [0.25, "o", "Running Tests ... 25%"],
            [0.75, "o", "Running Tests ... 100%"],
            [0.1, "o", rendered_table.getvalue()],
        ],
    )

    completed = run_script(FILTER_CAST, source, destination, "nrfu")

    assert completed.returncode == 0, completed.stderr
    filtered_events = [json.loads(line) for line in destination.read_text(encoding="utf-8").splitlines()]
    assert filtered_events[0]["command"] == "anta nrfu"
    progress_duration = sum(event[0] for event in filtered_events if isinstance(event, list) and "Running Tests" in event[2])
    assert progress_duration == EXPECTED_PROGRESS_DURATION
    output = "".join(event[2] for event in filtered_events[1:] if event[1] == "o")
    assert "All tests results" in output
    assert "success" in output
    assert "failure" in output
    assert "\x1b[1A" in output


def test_filter_cast_accepts_successful_psirt_recording(tmp_path: Path) -> None:
    """Verify a successful PSIRT recording is normalized and written."""
    source = tmp_path / "raw.cast"
    destination = tmp_path / "filtered.cast"
    write_cast(source, [cast_header(), [0.1, "o", "Security advisory Markdown report saved to psirt.md\r\n"]])

    completed = run_script(FILTER_CAST, source, destination, "psirt")

    assert completed.returncode == 0, completed.stderr
    header = json.loads(destination.read_text(encoding="utf-8").splitlines()[0])
    assert header["command"] == "anta psirt md-report --md-output psirt.md"


def test_filter_cast_rejects_unsuccessful_psirt_recording(tmp_path: Path) -> None:
    """Verify an incomplete PSIRT capture cannot replace the committed cast."""
    source = tmp_path / "raw.cast"
    destination = tmp_path / "filtered.cast"
    write_cast(source, [cast_header(), [0.1, "o", "PSIRT run failed\r\n"]])

    completed = run_script(FILTER_CAST, source, destination, "psirt")

    assert completed.returncode != 0
    assert "PSIRT Markdown report success message was not found" in completed.stderr
    assert not destination.exists()


def test_prepare_nrfu_catalog_selects_all_demo_tests(tmp_path: Path) -> None:
    """Verify the current example catalog satisfies the complete demo allowlist."""
    source = REPOSITORY_ROOT / "examples" / "tests.yaml"
    destination = tmp_path / "demo-catalog.yaml"
    original_source = source.read_bytes()

    completed = run_script(PREPARE_NRFU_CATALOG, source, destination)

    assert completed.returncode == 0, completed.stderr
    catalog = yaml.safe_load(destination.read_text(encoding="utf-8"))
    selected_tests = [next(iter(test)) for tests in catalog.values() for test in tests]
    assert len(selected_tests) == EXPECTED_DEMO_CATALOG_ENTRIES
    assert source.read_bytes() == original_source


def test_prepare_nrfu_catalog_rejects_missing_demo_tests(tmp_path: Path) -> None:
    """Verify removed allowlisted tests fail before a partial catalog is written."""
    source = tmp_path / "incomplete-catalog.yaml"
    destination = tmp_path / "demo-catalog.yaml"
    source.write_text("anta.tests.system:\n  - VerifyUptime:\n", encoding="utf-8")

    completed = run_script(PREPARE_NRFU_CATALOG, source, destination)

    assert completed.returncode != 0
    assert "Demo tests not found" in completed.stderr
    assert not destination.exists()
