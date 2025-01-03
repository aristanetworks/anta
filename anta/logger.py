# Copyright (c) 2023-2025 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""Configure logging for ANTA."""

from __future__ import annotations

import logging
import traceback
from datetime import timedelta
from enum import Enum
from pathlib import Path
from typing import Literal

from rich.logging import RichHandler

from anta import __DEBUG__

logger = logging.getLogger(__name__)


class Log(str, Enum):
    """Represent log levels from logging module as immutable strings."""

    CRITICAL = logging.getLevelName(logging.CRITICAL)
    ERROR = logging.getLevelName(logging.ERROR)
    WARNING = logging.getLevelName(logging.WARNING)
    INFO = logging.getLevelName(logging.INFO)
    DEBUG = logging.getLevelName(logging.DEBUG)


LogLevel = Literal[Log.CRITICAL, Log.ERROR, Log.WARNING, Log.INFO, Log.DEBUG]


def setup_logging(level: LogLevel = Log.INFO, file: Path | None = None) -> None:
    """Configure logging for ANTA.

    By default, the logging level is INFO for all loggers except for httpx and asyncssh which are too verbose:
    their logging level is WARNING.

    If logging level DEBUG is selected, all loggers will be configured with this level.

    In ANTA Debug Mode (environment variable `ANTA_DEBUG=true`), Python tracebacks are logged and logging level is
    overwritten to be DEBUG.

    If a file is provided, logs will also be sent to the file in addition to stdout.
    If a file is provided and logging level is DEBUG, only the logging level INFO and higher will
    be logged to stdout while all levels will be logged in the file.

    Parameters
    ----------
    level
        ANTA logging level
    file
        Send logs to a file

    """
    # Init root logger
    root = logging.getLogger()
    # In ANTA debug mode, level is overridden to DEBUG
    loglevel = logging.DEBUG if __DEBUG__ else getattr(logging, level.upper())
    root.setLevel(loglevel)
    # Silence the logging of chatty Python modules when level is INFO
    if loglevel == logging.INFO:
        # asyncssh is really chatty
        logging.getLogger("asyncssh").setLevel(logging.WARNING)
        # httpx as well
        logging.getLogger("httpx").setLevel(logging.WARNING)

    # Add RichHandler for stdout if not already present
    _maybe_add_rich_handler(loglevel, root)

    # Add FileHandler if file is provided and same File Handler is not already present
    if file and not _get_file_handler(root, file):
        file_handler = logging.FileHandler(file)
        formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
        file_handler.setFormatter(formatter)
        root.addHandler(file_handler)
        # If level is DEBUG and file is provided, do not send DEBUG level to stdout
        if loglevel == logging.DEBUG and (rich_handler := _get_rich_handler(root)) is not None:
            rich_handler.setLevel(logging.INFO)

    if __DEBUG__:
        logger.debug("ANTA Debug Mode enabled")


def _get_file_handler(logger_instance: logging.Logger, file: Path) -> logging.FileHandler | None:
    """Return the FileHandler if present."""
    return (
        next(
            (
                handler
                for handler in logger_instance.handlers
                if isinstance(handler, logging.FileHandler) and str(Path(handler.baseFilename).resolve()) == str(file.resolve())
            ),
            None,
        )
        if logger_instance.hasHandlers()
        else None
    )


def _get_rich_handler(logger_instance: logging.Logger) -> logging.Handler | None:
    """Return the ANTA Rich Handler."""
    return next((handler for handler in logger_instance.handlers if handler.get_name() == "ANTA_RICH_HANDLER"), None) if logger_instance.hasHandlers() else None


def _maybe_add_rich_handler(loglevel: int, logger_instance: logging.Logger) -> None:
    """Add RichHandler for stdout if not already present."""
    if _get_rich_handler(logger_instance) is not None:
        # Nothing to do.
        return

    anta_rich_handler = RichHandler(markup=True, rich_tracebacks=True, tracebacks_show_locals=False)
    anta_rich_handler.set_name("ANTA_RICH_HANDLER")
    # Show Python module in stdout at DEBUG level
    fmt_string = "[grey58]\\[%(name)s][/grey58] %(message)s" if loglevel == logging.DEBUG else "%(message)s"
    formatter = logging.Formatter(fmt=fmt_string, datefmt="[%X]")
    anta_rich_handler.setFormatter(formatter)
    logger_instance.addHandler(anta_rich_handler)


def format_td(seconds: float, digits: int = 3) -> str:
    """Return a formatted string from a float number representing seconds and a number of digits."""
    isec, fsec = divmod(round(seconds * 10**digits), 10**digits)
    return f"{timedelta(seconds=isec)}.{fsec:0{digits}.0f}"


def exc_to_str(exception: BaseException) -> str:
    """Return a human readable string from an BaseException object."""
    return f"{type(exception).__name__}{f': {exception}' if str(exception) else ''}"


def anta_log_exception(exception: BaseException, message: str | None = None, calling_logger: logging.Logger | None = None) -> None:
    """Log exception.

    If `anta.__DEBUG__` is True then the `logger.exception` method is called to get the traceback, otherwise `logger.error` is called.

    Parameters
    ----------
    exception
        The Exception being logged.
    message
        An optional message.
    calling_logger
        A logger to which the exception should be logged. If not present, the logger in this file is used.

    """
    if calling_logger is None:
        calling_logger = logger
    calling_logger.critical(f"{message}\n{exc_to_str(exception)}" if message else exc_to_str(exception))
    if __DEBUG__:
        msg = f"[ANTA Debug Mode]{f' {message}' if message else ''}"
        calling_logger.exception(msg, exc_info=exception)


def tb_to_str(exception: BaseException) -> str:
    """Return a traceback string from an BaseException object."""
    return "Traceback (most recent call last):\n" + "".join(traceback.format_tb(exception.__traceback__))
