# Copyright (c) 2023-2025 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Tests for anta.cli._main."""

from __future__ import annotations

import sys
from typing import Any
from unittest.mock import patch

import pytest


# https://github.com/python/cpython/issues/88852
@pytest.mark.skipif(sys.version_info <= (3, 11), reason="Unreliable behavior patching sys.modules before 3.11")
def test_cli_error_missing_click(capsys: pytest.CaptureFixture[Any]) -> None:
    """Test ANTA errors out when anta[cli] was not installed."""
    with patch.dict(sys.modules, {"click": None}) as sys_modules:
        for k in list(sys_modules.keys()):
            if k.startswith("anta."):
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


# https://github.com/python/cpython/issues/88852
@pytest.mark.skipif(sys.version_info <= (3, 11), reason="Unreliable behavior patching sys.modules before 3.11")
def test_cli_error_missing_other() -> None:
    """Test ANTA errors out when anta[cli] was not installed."""
    with patch.dict(sys.modules, {"httpx": None}) as sys_modules:
        # Need to clean up from previous runs a path that will trigger reimporting httpx
        for k in list(sys_modules.keys()):
            if k.startswith("anta."):
                del sys_modules[k]
        import anta.cli

        with pytest.raises(ImportError, match="httpx"):
            anta.cli.cli()
