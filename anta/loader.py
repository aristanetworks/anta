"""
Loader that parses a YAML test catalog and imports corresponding Python functions
"""
from __future__ import annotations

import importlib
import logging
import sys
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple

from rich.logging import RichHandler

from anta import __DEBUG__
from anta.result_manager.models import TestResult

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
    loglevel = getattr(logging, level.upper()) if not __DEBUG__ else logging.DEBUG
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


def parse_catalog(test_catalog: Dict[Any, Any], package: Optional[str] = None) -> List[Tuple[Callable[..., TestResult], Dict[Any, Any]]]:
    """
    Function to parse the catalog and return a list of tests

    Args:
        test_catalog (Dict[Any, Any]): List of tests defined in catalog YAML file

    Returns:
        List[Tuple[Callable[..., TestResult], Dict[Any, Any]]]: List of python function tests to run.
    """
    tests: List[Tuple[Callable[..., TestResult], Dict[Any, Any]]] = []
    if not test_catalog:
        return tests
    for key, value in test_catalog.items():
        # Required to manage iteration within a tests module
        if package is not None:
            key = ".".join([package, key])
        try:
            module = importlib.import_module(f"{key}")
        except ModuleNotFoundError:
            logger.error(f"No test module named '{key}'")
            sys.exit(1)
        if isinstance(value, list):
            # This is a list of tests
            for test in value:
                for func_name, args in test.items():
                    try:
                        func = getattr(module, func_name)
                    except AttributeError:
                        logger.error(f"Wrong test function name '{func_name}' in '{module.__name__}'")
                        sys.exit(1)
                    if not callable(func):
                        logger.error(f"'{func.__module__}.{func.__name__}' is not a function")
                        sys.exit(1)
                    tests.append((func, args if args is not None else {}))
        if isinstance(value, dict):
            # This is an inner Python module
            tests.extend(parse_catalog(value, package=module.__name__))
    return tests
