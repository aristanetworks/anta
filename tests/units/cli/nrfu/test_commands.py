# Copyright (c) 2023 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""
Tests for anta.cli.nrfu.commands
"""
from __future__ import annotations
import json
import re

from pathlib import Path

from click.testing import CliRunner

from anta.cli import anta
from anta.cli.utils import ExitCode

DATA_DIR: Path = Path(__file__).parent.parent.parent.parent.resolve() / "data"


def test_anta_nrfu_table(click_runner: CliRunner) -> None:
    """
    Test anta nrfu, catalog is given via env
    """
    result = click_runner.invoke(anta, ["nrfu", "table"])
    assert result.exit_code == ExitCode.OK
    assert "dummy  │ VerifyEOSVersion │ success" in result.output


def test_anta_nrfu_text(click_runner: CliRunner) -> None:
    """
    Test anta nrfu, catalog is given via env
    """
    result = click_runner.invoke(anta, ["nrfu", "text"])
    assert result.exit_code == ExitCode.OK
    assert "dummy :: VerifyEOSVersion :: SUCCESS" in result.output


def test_anta_nrfu_json(click_runner: CliRunner) -> None:
    """
    Test anta nrfu, catalog is given via env
    """
    result = click_runner.invoke(anta, ["nrfu", "json"])
    assert result.exit_code == ExitCode.OK
    assert "JSON results of all tests" in result.output
    m = re.search(r'\[\n  {[\s\S]+  }\n\]', result.output)
    assert m is not None
    result_list = json.loads(m.group())
    for r in result_list:
        if r['name'] == 'dummy':
            assert r['test'] == 'VerifyEOSVersion'
            assert r['result'] == 'success'


def test_anta_nrfu_template(click_runner: CliRunner) -> None:
    """
    Test anta nrfu, catalog is given via env
    """
    result = click_runner.invoke(anta, ["nrfu", "tpl-report", "--template", str(DATA_DIR / "template.j2")])
    assert result.exit_code == ExitCode.OK
    assert "* VerifyEOSVersion is SUCCESS for dummy" in result.output
