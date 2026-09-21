# Copyright (c) 2026 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Tests for the documentation snippet generator."""

from __future__ import annotations

import argparse
import io
from typing import TYPE_CHECKING

import pytest
from rich.console import Console
from rich.progress import Progress

from anta.result_manager import ResultManager
from anta.result_manager.models import TestResult as AntaTestResult
from docs.scripts.generate_snippet import (
    custom_progress_bar,
    finalize_console_output,
    format_omitted_results,
    limit_result_manager,
    normalize_svg_whitespace,
    parse_args,
    positive_integer,
)

if TYPE_CHECKING:
    from pathlib import Path


@pytest.mark.parametrize(
    ("args", "expected_format", "expected_max_results", "expected_max_lines"),
    [
        (["anta", "--help"], "svg", None, None),
        (["--format", "txt", "--max-results", "10", "--max-lines", "20", "anta", "--help"], "txt", 10, 20),
    ],
)
def test_parse_args(args: list[str], expected_format: str, expected_max_results: int | None, expected_max_lines: int | None) -> None:
    """Verify the default and explicit output formats."""
    command, output_format, max_results, max_lines = parse_args(args)

    assert command == ["anta", "--help"]
    assert output_format == expected_format
    assert max_results == expected_max_results
    assert max_lines == expected_max_lines


def test_parse_args_requires_command() -> None:
    """Verify an ANTA command is required."""
    with pytest.raises(SystemExit):
        parse_args(["--format", "svg"])


@pytest.mark.parametrize("value", ["0", "-1"])
def test_positive_integer_rejects_non_positive_values(value: str) -> None:
    """Verify the result limit must be greater than zero."""
    with pytest.raises(argparse.ArgumentTypeError):
        positive_integer(value)


def test_limit_result_manager() -> None:
    """Verify result managers are truncated without mutating the original."""
    result_count = 3
    manager = ResultManager()
    manager.results = [AntaTestResult(name=f"device-{index}", test="VerifyTest", categories=[], description="Test") for index in range(result_count)]

    limited_manager, omitted_results = limit_result_manager(manager, 2)

    assert [result.name for result in limited_manager.results] == ["device-0", "device-1"]
    assert omitted_results == 1
    assert len(manager) == result_count


@pytest.mark.parametrize(("count", "expected"), [(1, "... 1 result omitted ..."), (2, "... 2 results omitted ...")])
def test_format_omitted_results(count: int, expected: str) -> None:
    """Verify the omission message handles singular and plural results."""
    assert format_omitted_results(count) == expected


def test_normalize_svg_whitespace(tmp_path: Path) -> None:
    """Verify SVG normalization removes trailing whitespace and preserves line endings."""
    svg_path = tmp_path / "capture.svg"
    svg_path.write_text("<svg>  \n  <text>output</text>\t\n</svg>\n", encoding="utf-8")

    normalize_svg_whitespace(svg_path)

    assert svg_path.read_text(encoding="utf-8") == "<svg>\n  <text>output</text>\n</svg>\n"


def test_finalize_console_output(monkeypatch: pytest.MonkeyPatch) -> None:
    """Verify truncation preserves the final status line before result-omission metadata."""
    test_console = Console(file=io.StringIO(), record=True)
    monkeypatch.setattr("docs.scripts.generate_snippet.console", test_console)
    test_console.print("first\nsecond\nthird")

    finalize_console_output(max_lines=2, omitted_results=2)

    assert test_console.export_text(clear=True) == "first\n\n... 1 line omitted ...\n\nthird\n\n... 2 results omitted ...\n"


def test_custom_progress_bar_forwards_spinner_name(monkeypatch: pytest.MonkeyPatch) -> None:
    """Verify the capture progress bar preserves the command-specific spinner."""
    progress = Progress()
    requested_spinners = []

    def progress_factory(spinner_name: str) -> Progress:
        requested_spinners.append(spinner_name)
        return progress

    monkeypatch.setattr("docs.scripts.generate_snippet.anta_progress_bar", progress_factory)

    assert custom_progress_bar("security") is progress
    assert requested_spinners == ["security"]
    assert progress.live.auto_refresh is False
