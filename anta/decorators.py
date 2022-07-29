"""
decorators for tests
"""
from functools import wraps
from typing import List, Callable, Any, Dict
from anta.result_manager.models import TestResult


def skip_on_platforms(platforms: List[str]) -> Callable[..., Callable[..., TestResult]]:
    """
    Decorator factory to skip a test on a list of platforms

    Args:
    * platforms (List[str]): the list of platforms on which the decorated test should be skipped.

    """

    def decorator(function: Callable[..., TestResult]) -> Callable[..., TestResult]:
        """
        Decorator to skip a test ona list of platform
        * func (Callable): the test to be decorated
        """

        @wraps(function)
        def wrapper(*args: List[Any], **kwargs: Dict[str, Any]) -> TestResult:
            """
            wrapper for func
            """
            device = args[0]
            if device.hw_model in platforms:  # type:ignore
                result = TestResult(host=str(device.host), test=function.__name__)  # type: ignore
                result.is_skipped(
                    f"{wrapper.__name__} test is not supported on {device.hw_model}."  # type: ignore
                )
                return result

            return function(*args, **kwargs)

        return wrapper

    return decorator
