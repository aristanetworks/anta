# Copyright (c) 2023-2025 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Tests for anta.logger."""

from __future__ import annotations

import logging
from unittest.mock import patch

import pytest

from anta.logger import anta_log_exception, exc_to_str, tb_to_str


@pytest.mark.parametrize(
    ("exception", "message", "calling_logger", "debug_value", "expected_message"),
    [
        pytest.param(
            ValueError("exception message"),
            None,
            None,
            False,
            "ValueError: exception message",
            id="exception only",
        ),
        pytest.param(
            ValueError("exception message"),
            "custom message",
            None,
            False,
            "custom message\nValueError: exception message",
            id="custom message",
        ),
        pytest.param(
            ValueError("exception message"),
            "custom logger",
            logging.getLogger("custom"),
            False,
            "custom logger\nValueError: exception message",
            id="custom logger",
        ),
        pytest.param(
            ValueError("exception message"),
            "Use with custom message",
            None,
            True,
            "Use with custom message\nValueError: exception message",
            id="__DEBUG__ on",
        ),
    ],
)
def test_anta_log_exception(
    caplog: pytest.LogCaptureFixture,
    exception: Exception,
    message: str | None,
    calling_logger: logging.Logger | None,
    debug_value: bool,
    expected_message: str,
) -> None:
    """Test anta_log_exception."""
    if calling_logger is not None:
        # https://github.com/pytest-dev/pytest/issues/3697
        calling_logger.propagate = True
        caplog.set_level(logging.ERROR, logger=calling_logger.name)
    else:
        caplog.set_level(logging.ERROR)
    # Need to raise to trigger nice stacktrace for __DEBUG__ == True
    try:
        raise exception
    except ValueError as exc:
        with patch("anta.logger.__DEBUG__", new=debug_value):
            anta_log_exception(exc, message=message, calling_logger=calling_logger)

    # Two log captured
    if debug_value:
        assert len(caplog.record_tuples) == 2
    else:
        assert len(caplog.record_tuples) == 1
    logger, level, message = caplog.record_tuples[0]

    if calling_logger is not None:
        assert calling_logger.name == logger
    else:
        assert logger == "anta.logger"

    assert level == logging.CRITICAL
    assert message == expected_message
    # the only place where we can see the stracktrace is in the capture.text
    if debug_value:
        assert "Traceback" in caplog.text


def my_raising_function(exception: Exception) -> None:
    """Raise Exception."""
    raise exception


@pytest.mark.parametrize(
    ("exception", "expected_output"),
    [(ValueError("test"), "ValueError: test"), (ValueError(), "ValueError")],
)
def test_exc_to_str(exception: Exception, expected_output: str) -> None:
    """Test exc_to_str."""
    assert exc_to_str(exception) == expected_output


def test_tb_to_str() -> None:
    """Test tb_to_str."""
    try:
        my_raising_function(ValueError("test"))
    except ValueError as exc:
        output = tb_to_str(exc)
        assert "Traceback" in output
        assert 'my_raising_function(ValueError("test"))' in output
