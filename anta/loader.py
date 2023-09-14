# Copyright (c) 2023 Arista Networks, Inc.
# Use of this source code is governed by the Apache License 2.0
# that can be found in the LICENSE file.
"""
Loader that parses a YAML test catalog and imports corresponding Python functions
"""
from __future__ import annotations

import importlib
import logging
import sys
from pathlib import Path
from typing import Any

from rich.logging import RichHandler

from anta import __DEBUG__
from anta.models import AntaTest

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


def parse_catalog(test_catalog: dict[str, Any], package: str | None = None) -> list[tuple[AntaTest, dict[str, Any] | None]]:
    """
    Function to parse the catalog and return a list of tests with their inputs

    A valid test catalog must follow the following structure:
        <Python module>:
            - <AntaTest subclass>:
                <AntaTest.Input compliant dictionary>

    Example:
        anta.tests.connectivity:
            - VerifyReachability:
                hosts:
                    - dst: 8.8.8.8
                      src: 172.16.0.1
                    - dst: 1.1.1.1
                      src: 172.16.0.1
                result_overwrite:
                    categories:
                        - "Overwritten category 1"
                    description: "Test with overwritten description"
                    custom_field: "Test run by John Doe"

    Also supports nesting for Python module definition:
        anta.tests:
            connectivity:
                - VerifyReachability:
                    hosts:
                        - dst: 8.8.8.8
                          src: 172.16.0.1
                        - dst: 1.1.1.1
                          src: 172.16.0.1
                    result_overwrite:
                        categories:
                            - "Overwritten category 1"
                        description: "Test with overwritten description"
                        custom_field: "Test run by John Doe"

    Args:
        test_catalog: Python dictionary representing the test catalog YAML file

    Returns:
        tests: List of tuples (test, inputs) where test is a reference of an AntaTest subclass
              and inputs is a dictionary
    """
    tests: list[tuple[AntaTest, dict[str, Any] | None]] = []
    if not test_catalog:
        return tests
    for key, value in test_catalog.items():
        # Required to manage iteration within a tests module
        if package is not None:
            key = ".".join([package, key])
        try:
            module = importlib.import_module(f"{key}")
        except ModuleNotFoundError:
            logger.critical(f"No test module named '{key}'")
            sys.exit(1)
        if isinstance(value, list):
            # This is a list of tests
            for test in value:
                for test_name, inputs in test.items():
                    # A test must be a subclass of AntaTest as defined in the Python module
                    try:
                        test = getattr(module, test_name)
                    except AttributeError:
                        logger.critical(f"Wrong test name '{test_name}' in '{module.__name__}'")
                        sys.exit(1)
                    if not issubclass(test, AntaTest):
                        logger.critical(f"'{test.__module__}.{test.__name__}' is not an AntaTest subclass")
                        sys.exit(1)
                    # Test inputs can be either None or a dictionary
                    if inputs is None or isinstance(inputs, dict):
                        tests.append((test, inputs))
                    else:
                        logger.critical(f"'{test.__module__}.{test.__name__}' inputs must be a dictionary")
                        sys.exit(1)
        if isinstance(value, dict):
            # This is an inner Python module
            tests.extend(parse_catalog(value, package=module.__name__))
    return tests
