# Copyright (c) 2023-2026 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Test anta.cli.utils."""

from __future__ import annotations

import click
import pytest

from anta.cli.utils import ExitCode, exit_with_code
from anta.result_manager import ResultManager
from anta.result_manager.models import AntaTestStatus


def test_exit_with_code_inconclusive() -> None:
    """Test an inconclusive result uses the existing tests-failed exit code."""
    result_manager = ResultManager()
    result_manager.status = AntaTestStatus.INCONCLUSIVE
    ctx = click.Context(click.Command("test"), obj={"result_manager": result_manager})

    with pytest.raises(click.exceptions.Exit) as exc_info:
        exit_with_code(ctx)

    assert exc_info.value.exit_code == ExitCode.TESTS_FAILED
