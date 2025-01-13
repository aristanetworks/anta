# Copyright (c) 2023-2025 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Tests for anta.cli._main."""

from __future__ import annotations

import sys
from importlib import reload
from typing import TYPE_CHECKING, Any
from unittest.mock import patch

import pytest

import anta.cli

if TYPE_CHECKING:
    from types import ModuleType

builtins_import = __import__


# Tried to achieve this with mock
# http://materials-scientist.com/blog/2021/02/11/mocking-failing-module-import-python/
def import_mock(name: str, *args: Any) -> ModuleType:  # noqa: ANN401
    """Mock."""
    if name == "click":
        msg = "No module named 'click'"
        raise ModuleNotFoundError(msg)
    return builtins_import(name, *args)


def test_cli_error_missing(capsys: pytest.CaptureFixture[Any]) -> None:
    """Test ANTA errors out when anta[cli] was not installed."""
    with patch.dict(sys.modules) as sys_modules, patch("builtins.__import__", import_mock):
        del sys_modules["anta.cli._main"]
        reload(anta.cli)

        with pytest.raises(SystemExit) as e_info:
            anta.cli.cli()

        captured = capsys.readouterr()
        assert "The ANTA command line client could not run because the required dependencies were not installed." in captured.out
        assert "Make sure you've installed everything with: pip install 'anta[cli]'" in captured.out
        assert e_info.value.code == 1

        # setting ANTA_DEBUG
        with pytest.raises(SystemExit) as e_info, patch("anta.cli.__DEBUG__", new=True):
            anta.cli.cli()

        captured = capsys.readouterr()
        assert "The ANTA command line client could not run because the required dependencies were not installed." in captured.out
        assert "Make sure you've installed everything with: pip install 'anta[cli]'" in captured.out
        assert "The caught exception was:" in captured.out
        assert e_info.value.code == 1
