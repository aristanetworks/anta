# Copyright (c) 2023-2025 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Tests for anta.cli._main."""

from __future__ import annotations

import sys
from typing import TYPE_CHECKING, Any, Callable
from unittest.mock import patch

import pytest

if TYPE_CHECKING:
    from types import ModuleType

builtins_import = __import__


# http://materials-scientist.com/blog/2021/02/11/mocking-failing-module-import-python/
def import_mock(delete_name: str) -> Callable[..., ModuleType]:
    """Mock missing the package 'delete_name' when importing."""

    def wrapper(name: str, *args: Any) -> ModuleType:  # noqa: ANN401
        """Mock."""
        if name == delete_name:
            msg = f"No module named '{delete_name}'"
            raise ModuleNotFoundError(msg, name=delete_name)
        return builtins_import(name, *args)

    return wrapper


def test_cli_error_missing_click(capsys: pytest.CaptureFixture[Any]) -> None:
    # def test_cli_error_missing_click() -> None:
    """Test ANTA errors out when anta[cli] was not installed."""
    with patch.dict(sys.modules) as sys_modules, patch("builtins.__import__", import_mock("click")):
        for k in list(sys_modules.keys()):
            if k.startswith("anta."):  # and k != "anta.cli":
                del sys_modules[k]
        import anta.cli

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


def test_cli_error_missing_other() -> None:
    """Test ANTA errors out when anta[cli] was not installed."""
    with patch.dict(sys.modules) as sys_modules, patch("builtins.__import__", import_mock("httpx")):
        # Need to clean up from previous runs a path that will trigger reimporting httpx
        for k in list(sys_modules.keys()):
            if k.startswith("anta."):  # and k != "anta.cli":
                del sys_modules[k]
        import anta.cli

        with pytest.raises(ImportError, match="httpx"):
            anta.cli.cli()
