"""
Loader that parses a YAML test catalog and imports corresponding Python functions
"""
import importlib
from typing import Callable, List, Tuple, Dict, Any
import sys
import logging

from anta.result_manager.models import TestResult

logger = logging.getLogger(__name__)


def parse_catalog(
    test_catalog: Dict[Any, Any], package: str = "anta.tests"
) -> List[Tuple[Callable[..., TestResult], Dict[Any, Any]]]:
    """
    Function to pase the catalog and return a list of tests
    """
    tests = []
    for key, value in test_catalog.items():
        try:
            module = importlib.import_module(f"{package}.{key}")
        except ModuleNotFoundError:
            logger.error(f"No test module named '{key}' in package '{package}'")
            sys.exit(1)
        if isinstance(value, list):
            # This is a list of tests
            for test in value:
                for func_name, args in test.items():
                    try:
                        func = getattr(module, func_name)
                    except AttributeError:
                        logger.error(
                            f"Wrong test function name '{func_name}' in '{module.__name__}'"
                        )
                        sys.exit(1)
                    if not callable(func):
                        logger.error(
                            f"'{func.__module__}.{func.__name__}' is not a function"
                        )
                        sys.exit(1)
                    tests.append((func, args if args is not None else {}))
        if isinstance(value, dict):
            # This is an inner Python module
            tests.extend(parse_catalog(value, package=module.__name__))
    return tests
