# Copyright (c) 2023-2024 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Tests for anta.cli._main."""

from __future__ import annotations

import builtins
import sys
from typing import TYPE_CHECKING, Any
from unittest.mock import patch

import pytest

if TYPE_CHECKING:
    from types import ModuleType

builtins_import = __import__


# Tried to achieve this with mock
# http://materials-scientist.com/blog/2021/02/11/mocking-failing-module-import-python/
def import_mock(name: str, *args: Any) -> ModuleType:  # noqa: ANN401
    """mock."""
    if name == "_main":
        raise ImportError
    return builtins_import(name, *args)


def test_cli_error_missing(capsys: pytest.CaptureFixture) -> None:
    """Test ANTA errors out when anta[cli] was not installed."""
    # TODO: this works but it is breaking subsequent tests because we are messing up with imports
    with patch.dict(sys.modules), patch.object(builtins, "__import__", import_mock):
        del sys.modules["anta.cli"]

        # Import outside toplevel
        from anta.cli import cli  # pylint: disable=C0415

        with pytest.raises(SystemExit) as e_info:
            cli()

        captured = capsys.readouterr()
        assert "The ANTA command line client could not run because the required dependencies were not installed." in captured.out
        assert "Make sure you've installed everything with: pip install 'anta[cli]'" in captured.out
        assert e_info.value.code == 1

        # setting ANTA_DEBUG
        with pytest.raises(SystemExit) as e_info, patch("anta.cli.__DEBUG__", new=True):
            cli()

        captured = capsys.readouterr()
        assert "The ANTA command line client could not run because the required dependencies were not installed." in captured.out
        assert "Make sure you've installed everything with: pip install 'anta[cli]'" in captured.out
        assert "The caught exception was:" in captured.out
        assert e_info.value.code == 1

    # TODO: this does not work
    for key in list(sys.modules.keys()):
        if key.startswith(("anta", "test")):
            del sys.modules[key]
