# Copyright (c) 2023 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""
Configure logging for ANTA
"""
from __future__ import annotations

import logging
from pathlib import Path

from rich.logging import RichHandler

from anta import __DEBUG__

logger = logging.getLogger(__name__)


def setup_logging(level: str = logging.getLevelName(logging.INFO), file: Path | None = None) -> None:
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
    richHandler = RichHandler(markup=True, rich_tracebacks=True, tracebacks_show_locals=True)
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
