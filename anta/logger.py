# Copyright (c) 2023 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""
Configure logging for ANTA
"""
from __future__ import annotations

import logging
from enum import Enum
from pathlib import Path
from typing import Literal, Optional

from rich.logging import RichHandler

from anta import __DEBUG__
from anta.tools.misc import exc_to_str

logger = logging.getLogger(__name__)


class Log(str, Enum):
    """Represent log levels from logging module as immutable strings"""

    CRITICAL = logging.getLevelName(logging.CRITICAL)
    ERROR = logging.getLevelName(logging.ERROR)
    WARNING = logging.getLevelName(logging.WARNING)
    INFO = logging.getLevelName(logging.INFO)
    DEBUG = logging.getLevelName(logging.DEBUG)


LogLevel = Literal[Log.CRITICAL, Log.ERROR, Log.WARNING, Log.INFO, Log.DEBUG]


def setup_logging(level: LogLevel = Log.INFO, file: Path | None = None) -> None:
    """
    Configure logging for ANTA.
    By default, the logging level is INFO for all loggers except for httpx and asyncssh which are too verbose:
    their logging level is WARNING.

    If logging level DEBUG is selected, all loggers will be configured with this level.

    In ANTA Debug Mode (environment variable `ANTA_DEBUG=true`), Python tracebacks are logged and logging level is
    overwritten to be DEBUG.

    If a file is provided, logs will also be sent to the file in addition to stdout.
    If a file is provided and logging level is DEBUG, only the logging level INFO and higher will
    be logged to stdout while all levels will be logged in the file.

    Args:
        level: ANTA logging level
        file: Send logs to a file
    """
    # Init root logger
    root = logging.getLogger()
    # In ANTA debug mode, level is overriden to DEBUG
    loglevel = logging.DEBUG if __DEBUG__ else getattr(logging, level.upper())
    root.setLevel(loglevel)
    # Silence the logging of chatty Python modules when level is INFO
    if loglevel == logging.INFO:
        # asyncssh is really chatty
        logging.getLogger("asyncssh").setLevel(logging.WARNING)
        # httpx as well
        logging.getLogger("httpx").setLevel(logging.WARNING)

    # Add RichHandler for stdout
    richHandler = RichHandler(markup=True, rich_tracebacks=True, tracebacks_show_locals=False)
    # In ANTA debug mode, show Python module in stdout
    if __DEBUG__:
        fmt_string = r"[grey58]\[%(name)s][/grey58] %(message)s"
    else:
        fmt_string = "%(message)s"
    formatter = logging.Formatter(fmt=fmt_string, datefmt="[%X]")
    richHandler.setFormatter(formatter)
    root.addHandler(richHandler)
    # Add FileHandler if file is provided
    if file:
        fileHandler = logging.FileHandler(file)
        formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
        fileHandler.setFormatter(formatter)
        root.addHandler(fileHandler)
        # If level is DEBUG and file is provided, do not send DEBUG level to stdout
        if loglevel == logging.DEBUG:
            richHandler.setLevel(logging.INFO)

    if __DEBUG__:
        logger.debug("ANTA Debug Mode enabled")


def anta_log_exception(exception: BaseException, message: Optional[str] = None, calling_logger: Optional[logging.Logger] = None) -> None:
    """
    Helper function to help log exceptions:
    * if anta.__DEBUG__ is True then the logger.exception method is called to get the traceback
    * otherwise logger.error is called

    Args:
        exception (BAseException): The Exception being logged
        message (str): An optional message
        calling_logger (logging.Logger): A logger to which the exception should be logged
                                         if not present, the logger in this file is used.

    """
    if calling_logger is None:
        calling_logger = logger
    calling_logger.critical(f"{message}\n{exc_to_str(exception)}" if message else exc_to_str(exception))
    if __DEBUG__:
        calling_logger.exception(f"[ANTA Debug Mode]{f' {message}' if message else ''}", exc_info=exception)
