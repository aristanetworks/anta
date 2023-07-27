"""
Loader that parses a YAML test catalog and imports corresponding Python functions
"""
import importlib
import logging
import sys
from typing import Any, Callable, Dict, List, Optional, Tuple

from rich.logging import RichHandler

from anta import __DEBUG__
from anta.result_manager.models import TestResult

logger = logging.getLogger(__name__)


def setup_logging(level: str = logging.getLevelName(logging.INFO)) -> None:
    """
    Configure logging

    Args:
        level (str, optional): level name to configure.
    """
    root = logging.getLogger()
    loglevel = getattr(logging, level.upper())
    handler = RichHandler(markup=True, rich_tracebacks=True, tracebacks_show_locals=True)
    if __DEBUG__:
        fmt_string = r"[grey58]\[%(name)s][/grey58] %(message)s"
    else:
        fmt_string = "%(message)s"
    formatter = logging.Formatter(fmt=fmt_string, datefmt="[%X]")
    handler.setFormatter(formatter)
    root.addHandler(handler)
    root.setLevel(loglevel)

    if __DEBUG__:
        if loglevel != logging.DEBUG:
            root.setLevel(logging.DEBUG)
            logger.debug(f"Override current logging level {level.upper()} with DEBUG")
        logger.debug("ANTA Debug Mode enabled")
    else:
        if loglevel == logging.INFO:
            # asyncssh is really chatty
            logging.getLogger("asyncssh").setLevel(logging.WARNING)
            # httpx as well
            logging.getLogger("httpx").setLevel(logging.WARNING)


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
