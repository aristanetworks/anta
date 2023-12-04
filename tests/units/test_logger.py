# Copyright (c) 2023 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""
Tests for anta.logger
"""
from __future__ import annotations

import logging
from typing import TYPE_CHECKING
from unittest.mock import patch

import pytest

from anta.logger import anta_log_exception

if TYPE_CHECKING:
    from pytest import LogCaptureFixture


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
        pytest.param(
            ValueError("exception message"), "Use with custom message", None, True, "Use with custom message\nValueError (exception message)", id="__DEBUG__ on"
        ),
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
        raise exception
    except ValueError as e:
        with patch("anta.logger.__DEBUG__", __DEBUG__value):
            anta_log_exception(e, message=message, calling_logger=calling_logger)

    # Two log captured
    if __DEBUG__value:
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
    if __DEBUG__value is True:
        assert "Traceback" in caplog.text
