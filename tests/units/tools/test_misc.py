# Copyright (c) 2023-2024 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""
Tests for anta.tools.misc
"""
from __future__ import annotations

import pytest

from anta.tools.misc import exc_to_str, tb_to_str


def my_raising_function(exception: Exception) -> None:
    """
    dummy function to raise Exception
    """
    raise exception


@pytest.mark.parametrize("exception, expected_output", [(ValueError("test"), "ValueError (test)"), (ValueError(), "ValueError")])
def test_exc_to_str(exception: Exception, expected_output: str) -> None:
    """
    Test exc_to_str
    """
    assert exc_to_str(exception) == expected_output


def test_tb_to_str() -> None:
    """
    Test tb_to_str
    """
    try:
        my_raising_function(ValueError("test"))
    except ValueError as e:
        output = tb_to_str(e)
        assert "Traceback" in output
        assert 'my_raising_function(ValueError("test"))' in output
