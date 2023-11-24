# Copyright (c) 2023 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""
Tests for anta.tools.misc
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING
from unittest.mock import patch

import pytest

from anta.tools.misc import anta_log_exception, exc_to_str, tb_to_str

if TYPE_CHECKING:
    from pytest import LogCaptureFixture


def my_raising_function(exception: Exception) -> None:
    """
    dummy function to raise Exception
    """
    raise exception


@pytest.mark.parametrize(
    "exception, message, calling_logger, __DEBUG__value, expected_message",
    [
        pytest.param(ValueError("exception message"), None, None, False, "ValueError (exception message)", id="exception only"),
        pytest.param(ValueError("exception message"), "custom message", None, False, "custom message\nValueError (exception message)", id="custom message"),
        pytest.param(
            ValueError("exception message"),
            "custom logger",
            logging.getLogger("custom"),
            False,
            "custom logger\nValueError (exception message)",
            id="custom logger",
        ),
        pytest.param(ValueError("exception message"), "Use with custom message", None, True, "Use with custom message", id="__DEBUG__ on"),
    ],
)
def test_anta_log_exception(
    caplog: LogCaptureFixture,
    exception: Exception,
    message: str | None,
    calling_logger: logging.Logger | None,
    __DEBUG__value: bool,
    expected_message: str,
) -> None:
    """
    Test anta_log_exception
    """

    if calling_logger is not None:
        # https://github.com/pytest-dev/pytest/issues/3697
        calling_logger.propagate = True
        caplog.set_level(logging.ERROR, logger=calling_logger.name)
    else:
        caplog.set_level(logging.ERROR)
    # Need to raise to trigger nice stacktrace for __DEBUG__ == True
    try:
        my_raising_function(exception)
    except ValueError as e:
        with patch("anta.tools.misc.__DEBUG__", __DEBUG__value):
            anta_log_exception(e, message=message, calling_logger=calling_logger)

    # One log captured
    assert len(caplog.record_tuples) == 1
    logger, level, message = caplog.record_tuples[0]

    if calling_logger is not None:
        assert calling_logger.name == logger
    else:
        assert logger == "anta.tools.misc"

    if __DEBUG__value:
        assert level == logging.ERROR
    else:
        assert level == logging.CRITICAL
    assert message == expected_message
    # the only place where we can see the stracktrace is in the capture.text
    if __DEBUG__value is True:
        assert "Traceback" in caplog.text


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
